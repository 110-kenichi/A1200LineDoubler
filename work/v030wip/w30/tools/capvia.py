# Place a 2-pad decap (0402) near given points, each pad tied to its plane with a short straight stub + via.
# usage: capvia.py board plan.json NETA,NETB x,y [x,y ...]   (pad1 -> NETA, pad2 -> NETB)
import os
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

import math
CYW,CYH,OFF,PW,PH=0.93,0.47,0.48,0.56,0.62     # C_0402_1005Metric: courtyard half sizes, pad offset/size
CY=[]
for f in b.GetFootprints():
    c=f.GetCourtyard(p.F_CrtYd)
    if c.OutlineCount():bb=c.BBox();CY.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
NA,NB=sys.argv[3].split(',');plan=[]
def padbox(x,y,rot,k):
    s=-1 if k==1 else 1
    if rot in(0,180):
        px=x+s*OFF*(1 if rot==0 else -1);return box(px-PW/2,y-PH/2,px+PW/2,y+PH/2),(px,y)
    py=y-s*OFF*(1 if rot==90 else -1);return box(x-PH/2,py-PW/2,x+PH/2,py+PW/2),(x,py)
def findvia(pc,net,pad,other):
    best=None
    for i in range(-24,25):
        for j in range(-24,25):
            x,y=round(pc[0]+i*0.05,3),round(pc[1]+j*0.05,3);d=math.hypot(x-pc[0],y-pc[1])
            if d>1.2 or (best and d>=best[0]):continue
            v=Point(x,y);vg=v.buffer(VD/2)
            if not edge.contains(v) or not all(clear(L,vg,net) for L in LAY):continue
            if any(o[2]=='pad' and o[1]!=net and o[0].distance(vg)<0.2 for o in [obs['F.Cu'][k] for k in T['F.Cu'].query(vg.buffer(0.3))]):continue
            h=v.buffer(VR)
            if any(holes[k].distance(h)<HOLE-1e-6 for k in TH.query(h.buffer(HOLE))):continue
            if vg.distance(pad)<0.05 or vg.distance(other)<0.2:continue   # no via-in-pad, clear of the cap's other pad
            seg=LineString([pc,(x,y)]).buffer(0.125)
            if not clear('F.Cu',seg,net) or seg.distance(other)<0.2:continue
            best=(d,x,y)
    return best
for arg in sys.argv[4:]:
    tx,ty=map(float,arg.split(','));sol=None
    cands=sorted(((math.hypot(i*0.1,j*0.1),tx+i*0.1,ty+j*0.1) for i in range(-46,47) for j in range(-46,47)),key=lambda c:c[0])
    for d,x,y in cands:
        if d>float(os.environ.get("CAPR","3.0")):break
        for rot in (0,90,180,270):
            cy=box(x-(CYW if rot in(0,180) else CYH),y-(CYH if rot in(0,180) else CYW),x+(CYW if rot in(0,180) else CYH),y+(CYH if rot in(0,180) else CYW))
            if any(c.intersects(cy) and c.intersection(cy).area>1e-6 for c in CY):continue
            ok=True;pads=[]
            for k,net in ((1,NA),(2,NB)):
                pb,pc=padbox(x,y,rot,k);pads.append((pb,pc,net))
                if not clear('F.Cu',pb,net):ok=False;break
            if not ok:continue
            va=findvia(pads[0][1],NA,pads[0][0],pads[1][0]);vb=findvia(pads[1][1],NB,pads[1][0],pads[0][0]) if va else None
            if va and vb and math.hypot(va[1]-vb[1],va[2]-vb[2])>=0.9:
                sol=dict(target=[tx,ty],center=[round(x,3),round(y,3)],rot=rot,pad1=list(pads[0][1]),pad2=list(pads[1][1]),via1=[va[1],va[2]],via2=[vb[1],vb[2]],dist=round(d,2));break
        if sol:break
    print(arg,sol)
    if sol:
        plan.append(sol);CY.append(box(sol['center'][0]-1,sol['center'][1]-1,sol['center'][0]+1,sol['center'][1]+1))
        for pb,pc,net in pads:obs['F.Cu'].append((pb,net,'pad'))
        for v,net in ((sol['via1'],NA),(sol['via2'],NB)):
            g=Point(*v).buffer(VD/2)
            for L in LAY:obs[L].append((g,net,'via'))
            holes.append(Point(*v).buffer(VR))
        for (pb,pc,net),v in zip(pads,(sol['via1'],sol['via2'])):obs['F.Cu'].append((LineString([pc,tuple(v)]).buffer(0.125),net,'trk'))
        TH=STRtree(holes);T={L:STRtree([o[0] for o in obs[L]]) for L in LAY}
json.dump(plan,open(sys.argv[2],'w'),indent=1)
