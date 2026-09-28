from pathlib import Path
import pcbnew as p,json,math,heapq
h=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(h/'amiga_scandoubler_analog.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()}
S=.05;clearance=.205;log=[]
def mm(v):return p.ToMM(v)
def xy(item):return (mm(item.GetPosition().x),mm(item.GetPosition().y))
def pt(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
def pad(ref,num):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(num))
def rect(item):
    b=item.GetBoundingBox();return tuple(mm(v) for v in [b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()])
pads=[a for f in fps.values() for a in f.Pads() if a.GetLayerSet().Contains(p.F_Cu)]
pad_boxes=[(q.GetNetCode(),rect(q)) for q in pads]
def distance2(x,y,ax,ay,bx,by):
    dx=bx-ax;dy=by-ay;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return (x-ax-t*dx)**2+(y-ay-t*dy)**2
def find_path(a,z,net,layer=p.F_Cu,width=.15,margin=4):
    x0=max(1,math.floor((min(a[0],z[0])-margin)/S));y0=max(1,math.floor((min(a[1],z[1])-margin)/S))
    x1=min(1880,math.ceil((max(a[0],z[0])+margin)/S));y1=min(1880,math.ceil((max(a[1],z[1])+margin)/S))
    w=x1-x0+1;hh=y1-y0+1;mask=bytearray(w*hh);grow=clearance+width/2
    def box(bounds,shape=None):
        l,t,r,b=bounds;il=max(x0,math.ceil(l/S));ir=min(x1,math.floor(r/S));it=max(y0,math.ceil(t/S));ib=min(y1,math.floor(b/S))
        if il>ir or it>ib:return
        for yy in range(it,ib+1):
            start=(yy-y0)*w
            if shape is None:mask[start+il-x0:start+ir-x0+1]=b'\1'*(ir-il+1)
            else:
                for xx in range(il,ir+1):
                    if shape(xx*S,yy*S):mask[start+xx-x0]=1
    for q in pads:
        if not q.GetLayerSet().Contains(layer) or q.GetNetCode()==net:continue
        l,t,r,b=rect(q);box((l-grow,t-grow,r+grow,b+grow))
    for tr in board.GetTracks():
        if tr.GetNetCode()==net:continue
        if isinstance(tr,p.PCB_VIA):
            xx,yy=xy(tr);rr=mm(tr.GetWidth())/2+grow
            box((xx-rr,yy-rr,xx+rr,yy+rr),lambda x,y:(x-xx)**2+(y-yy)**2<=rr*rr)
        elif tr.GetLayer()==layer:
            ax,ay=mm(tr.GetStart().x),mm(tr.GetStart().y);bx,by=mm(tr.GetEnd().x),mm(tr.GetEnd().y);rr=mm(tr.GetWidth())/2+grow
            box((min(ax,bx)-rr,min(ay,by)-rr,max(ax,bx)+rr,max(ay,by)+rr),lambda x,y:distance2(x,y,ax,ay,bx,by)<=rr*rr)
    start=(round(a[0]/S)-x0,round(a[1]/S)-y0);end=(round(z[0]/S)-x0,round(z[1]/S)-y0)
    def idx(v):return v[1]*w+v[0]
    if mask[idx(start)] or mask[idx(end)]:return None
    def heur(v):dx=abs(v[0]-end[0]);dy=abs(v[1]-end[1]);return max(dx,dy)+.41421356*min(dx,dy)
    queue=[(heur(start),0,start)];cost={start:0};prev={};found=False
    while queue:
        _,g,v=heapq.heappop(queue)
        if g>cost[v]:continue
        if v==end:found=True;break
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
            q=(v[0]+dx,v[1]+dy)
            if not (0<=q[0]<w and 0<=q[1]<hh) or mask[idx(q)]:continue
            if dx and dy and (mask[idx((v[0]+dx,v[1]))] or mask[idx((v[0],v[1]+dy))]):continue
            ng=g+(1.41421356 if dx and dy else 1)
            if ng<cost.get(q,1e99):cost[q]=ng;prev[q]=v;heapq.heappush(queue,(ng+heur(q),ng,q))
    if not found:return None
    path=[end]
    while path[-1]!=start:path.append(prev[path[-1]])
    path.reverse();points=[a];last=None
    for i in range(1,len(path)):
        direction=(path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])
        if last is not None and direction!=last:points.append(((path[i-1][0]+x0)*S,(path[i-1][1]+y0)*S))
        last=direction
    points.extend([((end[0]+x0)*S,(end[1]+y0)*S),z]);return points
def route(points,net,layer=p.F_Cu,width=.15):
    for a,z in zip(points,points[1:]):
        if math.dist(a,z)<1e-6:continue
        t=p.PCB_TRACK(board);t.SetStart(pt(a));t.SetEnd(pt(z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNetCode(net);board.Add(t)

from collections import defaultdict,deque
start=pt((24.725,52.0));end=pt((54.55,72.75))
def key(v):return (v.x,v.y)
adj=defaultdict(list)
for tr in board.GetTracks():
    if not isinstance(tr,p.PCB_VIA) and tr.GetNetname()=='1V9' and tr.GetLayer()==p.In2_Cu:
        a,z=key(tr.GetStart()),key(tr.GetEnd());adj[a].append((z,tr));adj[z].append((a,tr))
todo=deque([key(start)]);prev={key(start):None}
while todo:
    v=todo.popleft()
    if v==key(end):break
    for z,tr in adj[v]:
        if z not in prev:prev[z]=(v,tr);todo.append(z)
assert key(end) in prev
removed=[];v=key(end)
while prev[v]:
    v,tr=prev[v];removed.append(tr)
old_length=sum(mm(t.GetLength()) for t in removed);net=removed[0].GetNetCode()
for tr in removed:board.Remove(tr)
points=find_path((24.725,52.0),(54.55,72.75),net,layer=p.B_Cu,width=.4,margin=8)
assert points,'No back-layer path'
route(points,net,layer=p.B_Cu,width=.4)
new_length=sum(math.dist(a,z) for a,z in zip(points,points[1:]))
assert new_length<old_length
name=h/'amiga_scandoubler_refined.kicad_pcb';board.SetFileName(str(name));p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(name),board)
result={'net':'1V9','endpoints_mm':[[24.725,52.0],[54.55,72.75]],'old_layer':'In2.Cu','new_layer':'B.Cu','width_mm':.4,'old_length_mm':old_length,'new_length_mm':new_length,'removed_segments':len(removed),'new_path_mm':points}
(h/'r34_refinement.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
