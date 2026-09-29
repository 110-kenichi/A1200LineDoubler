# For island pads of plane nets: find the shortest F.Cu stub (straight, from a point on the pad's axis)
# to a new plane via (or an existing plane-connected via of the same net).
# usage: viastub.py board plan.json REF:PIN[:net] ...   (writes candidates; applied by viastub_apply.py)
import pcbnew as p,sys,json,math
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree
mm=p.ToMM;b=p.LoadBoard(sys.argv[1])
CL=0.2;HOLE=0.25;VD=0.6;VR=0.3;W=0.25;RMAX=3.0;STEP=0.05
LAY=['F.Cu','In1.Cu','In2.Cu','B.Cu']
obs={L:[] for L in LAY};holes=[]
def padpoly(q):
    sh=q.GetEffectivePolygon();o=sh.Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):
        c=Point(mm(t.GetPosition().x),mm(t.GetPosition().y))
        for L in LAY:obs[L].append((c.buffer(mm(t.GetWidth())/2),t.GetNetname(),'via'))
        holes.append(c.buffer(mm(t.GetDrill())/2))
    else:
        g=LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2)
        obs[t.GetLayerName()].append((g,t.GetNetname(),'trk'))
for f in b.GetFootprints():
    for q in f.Pads():
        g=padpoly(q)
        for L in LAY:
            if q.IsOnLayer(b.GetLayerID(L)):obs[L].append((g,q.GetNetname(),'pad'))
        if q.GetDrillSize().x>0:holes.append(Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(mm(q.GetDrillSize().x)/2))
T={L:STRtree([o[0] for o in obs[L]]) for L in LAY};TH=STRtree(holes)
def clear(L,g,net):
    for i in T[L].query(g.buffer(CL)):
        og,on,_=obs[L][i]
        if on!=net and og.distance(g)<CL-1e-6:return False
    return True
edge=box(1.0,1.0,94.0,94.0)
b.BuildConnectivity();con=b.GetConnectivity()
plan=[]
for arg in sys.argv[3:]:
    ref,pin=arg.split(':')[:2]
    q=[q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber()==pin][0];net=q.GetNetname()
    pp=padpoly(q);cx,cy=mm(q.GetPosition().x),mm(q.GetPosition().y)
    # starts: sample the pad's long axis
    bx=pp.bounds;starts=[]
    if bx[2]-bx[0]>bx[3]-bx[1]:starts=[(bx[0]+(bx[2]-bx[0])*k/8,cy) for k in range(1,8)]
    else:starts=[(cx,bx[1]+(bx[3]-bx[1])*k/8) for k in range(1,8)]
    best=None
    # existing same-net vias first (0.3 bonus)
    exist=[(o[0].centroid.x,o[0].centroid.y) for o in obs['F.Cu'] if o[2]=='via' and o[1]==net]
    cand=[(x,y,1) for x,y in exist if math.hypot(x-cx,y-cy)<RMAX+2]
    n=int(RMAX/STEP)
    for i in range(-n,n+1):
        for j in range(-n,n+1):
            x,y=round(cx+i*STEP,3),round(cy+j*STEP,3)
            if math.hypot(x-cx,y-cy)<=RMAX:cand.append((x,y,0))
    for x,y,ex in cand:
        v=Point(x,y)
        if not ex:
            if not edge.contains(v):continue
            vg=v.buffer(VD/2)
            if not all(clear(L,vg,net) for L in LAY):continue
            if any(o[2]=='pad' and o[0].distance(vg)<0.1 for o in [obs['F.Cu'][k] for k in T['F.Cu'].query(vg.buffer(0.1))]):continue
            h=v.buffer(VR)
            if any(holes[k].distance(h)<HOLE-1e-6 for k in TH.query(h.buffer(HOLE))):continue
        for s in starts:
            L=math.hypot(x-s[0],y-s[1]);ang=math.degrees(math.atan2(y-s[1],x-s[0]))%45
            sc=L+(0 if min(ang,45-ang)<0.5 else 0.3)+(0 if ex else 0.4)
            if best and sc>=best[0]:continue
            seg=LineString([s,(x,y)]).buffer(W/2) if L>1e-6 else Point(s).buffer(W/2)
            if not clear('F.Cu',seg,net):continue
            best=(round(sc,3),ref,pin,net,[round(s[0],3),round(s[1],3)],[x,y],bool(ex))
    print(best if best else ('NONE',ref,pin,net));
    if best:
        plan.append(best);s,(x,y)=best[4],best[5];v=Point(x,y)
        obs['F.Cu'].append((LineString([s,(x,y)]).buffer(W/2) if s!=[x,y] else Point(s).buffer(W/2),net,'trk'))
        if not best[6]:
            for L in LAY:obs[L].append((v.buffer(VD/2),net,'via'))
            holes.append(v.buffer(VR));TH=STRtree(holes)
        T={L:STRtree([o[0] for o in obs[L]]) for L in LAY}
json.dump(plan,open(sys.argv[2],'w'),indent=0)
