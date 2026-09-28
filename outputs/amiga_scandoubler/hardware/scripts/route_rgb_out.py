from pathlib import Path
import pcbnew as p,json,math,heapq
h=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(h/'amiga_scandoubler_pll_top.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()}
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
def via_free(v,net):
    x,y=v
    if not (1<x<94 and 1<y<94):return False
    for code,(l,t,r,b) in pad_boxes:
        grow=.35 if code==net else .48
        if l-grow<x<r+grow and t-grow<y<b+grow:return False
    for tr in board.GetTracks():
        if isinstance(tr,p.PCB_VIA) and math.dist(v,xy(tr))<.61:return False
        if tr.GetNetCode()==net:continue
        rr=.48+mm(tr.GetWidth())/2
        if isinstance(tr,p.PCB_VIA):
            xx,yy=xy(tr)
            if (x-xx)**2+(y-yy)**2<rr*rr:return False
        else:
            if distance2(x,y,mm(tr.GetStart().x),mm(tr.GetStart().y),mm(tr.GetEnd().x),mm(tr.GetEnd().y))<rr*rr:return False
    return True
def addvia(v,net):
    item=p.PCB_VIA(board);item.SetPosition(pt(v));item.SetWidth(p.FromMM(.55));item.SetDrill(p.FromMM(.3));item.SetViaType(p.VIATYPE_THROUGH);item.SetLayerPair(p.F_Cu,p.B_Cu);item.SetNetCode(net);board.Add(item)
def escape(q):
    a=xy(q);net=q.GetNetCode()
    existing=sorted((math.dist(a,xy(v)),xy(v)) for v in board.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetCode()==net and math.dist(a,xy(v))<2.5)
    candidates=[(a[0]+dx*.2,a[1]+dy*.2) for dx in range(-18,19) for dy in range(-18,19)]
    candidates.sort(key=lambda z:math.dist(a,z))
    choices=[(z,False) for dist,z in existing]+[(z,True) for z in candidates if .8<math.dist(a,z)<3.6]
    tested=0
    for z,new in choices:
        if new:
            if not via_free(z,net):continue
            tested+=1
            if tested>120:break
        points=find_path(a,z,net,margin=3)
        if points:
            route(points,net)
            if new:addvia(z,net)
            return z
    return None



held=[];restore=[]
for tr in list(board.GetTracks()):
 if isinstance(tr,p.PCB_VIA) or tr.GetLayer()!=p.F_Cu or tr.GetNetname()!='GND':continue
 a=xy(tr);z=(mm(tr.GetEnd().x),mm(tr.GetEnd().y))
 if min(a[0],z[0])<81 and max(a[0],z[0])>75 and min(a[1],z[1])<45 and max(a[1],z[1])>39:
  restore.append((a,z,tr.GetNetCode(),mm(tr.GetWidth()),'GND',p.F_Cu));held.append(tr);board.Remove(tr)
# Collapse removed segment chains; internal bends need not survive rerouting.
from collections import defaultdict
adj=defaultdict(list)
for i,(a,z,net,width,name,layer) in enumerate(restore):
 adj[(net,layer,a)].append(i);adj[(net,layer,z)].append(i)
anchors=set()
for q in pads:anchors.add((q.GetNetCode(),p.F_Cu,xy(q)))
for tr in board.GetTracks():
 if isinstance(tr,p.PCB_VIA):
  for layer in [p.F_Cu,p.In2_Cu,p.B_Cu]:anchors.add((tr.GetNetCode(),layer,xy(tr)))
 else:
  for v in [tr.GetStart(),tr.GetEnd()]:anchors.add((tr.GetNetCode(),tr.GetLayer(),(mm(v.x),mm(v.y))))
ends={k for k,v in adj.items() if len(v)!=2 or k in anchors};seen=set();merged=[]
for start in ends:
 for index in adj[start]:
  if index in seen:continue
  net,layer,a=start;v=a;width=restore[index][3];name=restore[index][4]
  while True:
   seen.add(index);aa,zz=restore[index][:2];v=zz if aa==v else aa;k=(net,layer,v)
   if k in ends:break
   index=next(i for i in adj[k] if i not in seen)
  if a!=v:merged.append((a,v,net,width,name,layer))
assert len(seen)==len(restore),(len(seen),len(restore))
restore=merged

comp_vias=[xy(t) for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='DAC_COMP'];assert len(comp_vias)==2
for tr in list(board.GetTracks()):
 if not isinstance(tr,p.PCB_VIA) and tr.GetLayer()==p.B_Cu and tr.GetNetname()=='DAC_COMP':held.append(tr);board.Remove(tr)
for n,v in [(33,(75.3,40.8)),(31,(76.9,42.25)),(27,(76.9,44.0))]:
 q=pad('U3',n);assert via_free(v,q.GetNetCode()),('ground via',n)
 points=find_path(xy(q),v,q.GetNetCode(),margin=3);assert points,('ground path',n)
 route(points,q.GetNetCode());addvia(v,q.GetNetCode())
records=[]
for net,number,ref,v in [('G_OUT',32,'R12',(76.2,41.45)),('B_OUT',28,'R13',(76.3,43.25))]:
 q=pad('U3',number);z=pad(ref,1);code=q.GetNetCode()
 points=find_path(xy(q),xy(z),code,margin=5)
 if points:route(points,code);records.append({'net':net,'layer':'F.Cu'});continue
 v=escape(q);assert v,(net,'pin escape')
 vz=escape(z);assert vz,(net,'resistor escape')
 points=find_path(v,vz,code,layer=p.B_Cu,margin=5);assert points,net
 route(points,code,layer=p.B_Cu);records.append({'net':net,'layer':'B.Cu','IC_via_mm':v,'resistor_via_mm':vz})
 print(net,'connected',flush=True)
failed=[]
for a,z,net,width,name,layer in restore:
 points=find_path(a,z,net,width=width,margin=8)
 if points:route(points,net,width=width)
 else:failed.extend([(a,net,width),(z,net,width)])
for endpoint,net,width in failed:
 if (net,p.F_Cu,endpoint) not in anchors:continue
 board.BuildConnectivity();conn=board.GetConnectivity();todo=[v for v in board.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetCode()==net];seen=set();nodes=[]
 while todo:
  item=todo.pop();uid=item.m_Uuid.AsString()
  if uid in seen:continue
  seen.add(uid)
  if isinstance(item,p.PAD) or isinstance(item,p.PCB_VIA):nodes.append(xy(item))
  elif item.GetLayer()==p.F_Cu:nodes.extend([xy(item),(mm(item.GetEnd().x),mm(item.GetEnd().y))])
  todo.extend(list(conn.GetConnectedPads(item))+list(conn.GetConnectedTracks(item)))
 if any(math.dist(endpoint,v)<.001 for v in nodes):continue
 for target in sorted(set(nodes),key=lambda v:math.dist(endpoint,v))[:8]:
  points=find_path(endpoint,target,net,width=width,margin=5)
  if points:route(points,net,width=width);break
 else:
  q=next((q for q in pads if q.GetNetCode()==net and math.dist(xy(q),endpoint)<.001),None)
  assert q and escape(q),('Ground escape',endpoint)
comp_net=pad('U3',35).GetNetCode()
points=find_path(comp_vias[0],comp_vias[1],comp_net,layer=p.B_Cu,margin=8);assert points,'COMP reroute'
route(points,comp_net,layer=p.B_Cu)
name=h/'amiga_scandoubler_rgb_out.kicad_pcb';board.SetFileName(str(name));p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(name),board)
(h/'rgb_out_progress.json').write_text(json.dumps(records,indent=2)+'\n')





