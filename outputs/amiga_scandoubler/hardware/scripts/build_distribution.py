from pathlib import Path
import pcbnew as p,json,math,heapq
h=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(h/'amiga_scandoubler_routing.kicad_pcb'));fps={f.GetReference():f for f in board.GetFootprints()}
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
manifest=json.loads((h/'circuit_manifest.json').read_text());pairs=[]
adc=[n for n,r in sorted(manifest['parts']['U1']['pins'].items(),key=lambda kv:int(kv[0])) if 'VDD' in r['name']]
pairs += [(('U1',n),(f'C{13+i}',1)) for i,n in enumerate(adc)]
power=json.loads((h/'fpga_pin_assignment.json').read_text())['pins']
fpins=[n for n,r in power.items() if r['function']=='Power']
pairs += [(('U2',n),(f'C{29+i}',1)) for i,n in enumerate(fpins)]
pairs += [(('U3',13),('C44',1)),(('U3',29),('C45',1)),(('U3',30),('C46',1))]
for a,z in pairs:
    aa,zz=pad(*a),pad(*z);assert aa.GetNetCode()==zz.GetNetCode(),(a,z)
    path=find_path(xy(aa),xy(zz),aa.GetNetCode())
    if path:route(path,aa.GetNetCode())
    log.append({'from':a,'to':z,'routed':bool(path),'length_mm':sum(math.dist(a,b) for a,b in zip(path,path[1:])) if path else None})
    print(a,z,'routed' if path else 'NO PATH',flush=True)
def via_free(v,net):
    x,y=v
    if not (1<x<94 and 1<y<94):return False
    for ref in ['U1','U2','U3']:
        bb=fps[ref].GetBoundingBox(False,False)
        if mm(bb.GetX())<=x<=mm(bb.GetRight()) and mm(bb.GetY())<=y<=mm(bb.GetBottom()):return False
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
power_nets={'1V2','1V9','3V3','ADC_1V9A','ADC_3V3A','ADC_1V9PLL','DAC_3V3'}
escaped=[];nodes={};ground=[]
targets=[]
for ref,item in manifest['parts'].items():
    if ref.startswith('C') and 13<=int(ref[1:])<=47:
        for num,rec in item['pins'].items():
            if rec['net'] in power_nets or rec['net']=='GND':targets.append((ref,num))
for ref in ['FB1','FB2','FB3','FB4']:targets.extend([(ref,1),(ref,2)])
targets.extend([('C56',1),('C58',1),('C60',1)])
for endpoint in targets:
    q=pad(*endpoint);v=escape(q)
    escaped.append({'pad':endpoint,'net':q.GetNetname(),'via_mm':v})
    if v:
        if q.GetNetname()=='GND':ground.append(v)
        else:nodes.setdefault(q.GetNetname(),set()).add(v)
    print('via',endpoint,'OK' if v else 'NO ESCAPE',flush=True)
# IC ground pins reach a nearby ground via; exposed pads use a ground lead.
icgrounds=[]
for ref in ['U1','U2','U3']:
    qs=[q for q in fps[ref].Pads() if q.GetNetname()=='GND']
    connected_ground_pads=[];deferred=[]
    for q in sorted(qs,key=lambda q:mm(q.GetSize().x)*mm(q.GetSize().y)):
        if mm(q.GetSize().x)*mm(q.GetSize().y)>10:
            others=sorted(connected_ground_pads,key=lambda a:math.dist(xy(a),xy(q)))
            v=None
            for other in others:
                points=find_path(xy(q),xy(other),q.GetNetCode(),margin=5)
                if points:route(points,q.GetNetCode());v=xy(other);break
        else:v=escape(q)
        icgrounds.append({'pad':[ref,q.GetNumber()],'connected':bool(v)})
        if v:connected_ground_pads.append(q)
        else:deferred.append((q,icgrounds[-1]))
        print('ground',ref,q.GetNumber(),'OK' if v else 'NO ESCAPE',flush=True)
    for q,record in deferred:
        for other in sorted(connected_ground_pads,key=lambda a:math.dist(xy(a),xy(q))):
            points=find_path(xy(q),xy(other),q.GetNetCode(),margin=5)
            if points:
                route(points,q.GetNetCode());record['connected']=True;record['via_ground_pad']=other.GetNumber();connected_ground_pads.append(q);break
# Connect same-net supply vias as a short spanning tree; back layer is fallback.
branches=[]
for net,positions in sorted(nodes.items(),key=lambda item:-len(item[1])):
    todo=set(positions);done={todo.pop()};code=next(q.GetNetCode() for q in pads if q.GetNetname()==net)
    while todo:
        choices=sorted((math.dist(a,z),a,z) for a in done for z in todo)
        found=False
        for dist,a,z in choices[:12]:
            for layer in [p.In2_Cu,p.B_Cu]:
                points=find_path(a,z,code,layer,width=.4,margin=8)
                if points:
                    route(points,code,layer,width=.4);branches.append({'net':net,'from':a,'to':z,'layer':board.GetLayerName(layer)});done.add(z);todo.remove(z);found=True;break
            if found:break
        if not found:break
    print('supply',net,'joined',len(done),'unjoined',len(todo),flush=True)
    if todo:branches.append({'net':net,'unjoined':sorted(todo)})
name=h/'amiga_scandoubler_distribution.kicad_pcb';board.SetFileName(str(name));p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(name),board)
(h/'distribution_progress.json').write_text(json.dumps({'status':'POWER_DISTRIBUTION_IN_PROGRESS','connections':log,'escapes':escaped,'IC_grounds':icgrounds,'branches':branches},indent=2)+'\n')
print('Saved',len(log),'connections',sum(x['routed'] for x in log),'routed')
