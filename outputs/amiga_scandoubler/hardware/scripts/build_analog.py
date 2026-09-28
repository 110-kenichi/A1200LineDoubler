from pathlib import Path
import pcbnew as p,json,math,heapq
h=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(h/'amiga_scandoubler_distribution.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()}
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
        grow=.35 if code==net else .505
        if l-grow<x<r+grow and t-grow<y<b+grow:return False
    for tr in board.GetTracks():
        if isinstance(tr,p.PCB_VIA) and math.dist(v,xy(tr))<.61:return False
        if tr.GetNetCode()==net:continue
        rr=.505+mm(tr.GetWidth())/2
        if isinstance(tr,p.PCB_VIA):
            xx,yy=xy(tr)
            if (x-xx)**2+(y-yy)**2<rr*rr:return False
        else:
            if distance2(x,y,mm(tr.GetStart().x),mm(tr.GetStart().y),mm(tr.GetEnd().x),mm(tr.GetEnd().y))<rr*rr:return False
    return True
def addvia(v,net):
    item=p.PCB_VIA(board);item.SetPosition(pt(v));item.SetWidth(p.FromMM(.6));item.SetDrill(p.FromMM(.3));item.SetViaType(p.VIATYPE_THROUGH);item.SetLayerPair(p.F_Cu,p.B_Cu);item.SetNetCode(net);board.Add(item)
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
            if tested>40:break
        points=find_path(a,z,net,margin=3)
        if points:
            route(points,net)
            if new:addvia(z,net)
            return z
    return None

# Route only explicitly selected analog networks; retain historical board.
selected=['PLL_F','PLL_FILT1','PLL_RC','PLL_FILT2','DAC_COMP','DAC_VREF','DAC_RSET',
'SOGIN_1','RIN_3','RIN_2','BIN_3','BIN_2','GIN_4','SOGIN_3','GIN_3','SOGIN_2','GIN_2',
'RIN_1','GIN_1','BIN_1','R_IN','G_IN','B_IN','R_OUT','G_OUT','B_OUT']
connections=[];deferred=[]
for netname in selected:
    targets=[q for q in pads if q.GetNetname()==netname]
    done=[targets.pop(0)]
    while targets:
        choices=sorted((math.dist(xy(a),xy(z)),i,j) for i,a in enumerate(done) for j,z in enumerate(targets))
        success=False
        for _,i,j in choices:
            a,z=done[i],targets[j]
            points=find_path(xy(a),xy(z),a.GetNetCode(),margin=8)
            layer=p.F_Cu
            if not points:
                before={t.m_Uuid.AsString() for t in board.GetTracks()}
                va=escape(a);vz=escape(z)
                if va and vz:
                    points=find_path(va,vz,a.GetNetCode(),layer=p.B_Cu,margin=8);layer=p.B_Cu
                if not points:
                    for tr in list(board.GetTracks()):
                        if tr.m_Uuid.AsString() not in before:board.Remove(tr)
            if points:
                route(points,a.GetNetCode(),layer=layer)
                connections.append({'net':netname,'from':[a.GetParent().GetReference(),a.GetNumber()],'to':[z.GetParent().GetReference(),z.GetNumber()],
                    'layer':board.GetLayerName(layer),'length_mm':sum(math.dist(x,y) for x,y in zip(points,points[1:]))})
                done.append(targets.pop(j));success=True;break
        if not success:break
    print(netname,'remaining pads',len(targets),flush=True)
    if targets: deferred.append(netname);print('DEFER',netname,flush=True)
grounds=[]
for ref in [f'C{i}' for i in range(3,13)]+['R10','R11','R12','R13','R15','R16','R17']:
    q=pad(ref,2);v=escape(q)
    if not v: print('DEFER GND',ref,flush=True);continue
    grounds.append([ref,'2']);print('ground',ref,flush=True)
for drawing in board.GetDrawings():
    if isinstance(drawing,p.PCB_TEXT):drawing.SetText(drawing.GetText().replace('PARTIAL POWER ROUTING','PARTIAL ANALOG ROUTING'))
name=h/'amiga_scandoubler_analog.kicad_pcb';board.SetFileName(str(name));p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(name),board)
(h/'analog_progress.json').write_text(json.dumps({'status':'ANALOG_PARTIAL_REVIEW','selected_nets':selected,'connections':connections,'ground_pads':grounds,'deferred_nets':deferred},indent=2)+'\n')
print('Saved',len(connections),'connections',len(grounds),'ground pads')

