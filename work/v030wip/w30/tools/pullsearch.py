# Place pull-up/down resistors: signal pad -> short F.Cu -> via on the net's B.Cu run; other pad -> plane via.
# usage: pullsearch.py <board> <refs-to-move> <out.json> [x0,y0,x1,y1] [json order]  (RSIZE=0402|0603)
import pcbnew as p, math, sys, json
from shapely.geometry import Point, LineString, box
from shapely.strtree import STRtree
mm=p.ToMM
b=p.LoadBoard(sys.argv[1]); MOVE=set(sys.argv[2].split(','))
CL=0.2; HOLE=0.25
import os
SZ=os.environ.get('RSIZE','0402')
CYX,CYY,OFF,PX,PY=(0.93,0.47,0.51,0.27,0.32) if SZ=='0402' else (1.48,0.73,0.825,0.45,0.475)
LAY=['F.Cu','In1.Cu','In2.Cu','B.Cu']
class Obs:
    def __init__(s):s.items={L:[] for L in LAY};s.holes=[];s.cy=[];s.dirty=True
    def add(s,L,g,net):s.items[L].append((g,net));s.dirty=True
    def tree(s):
        if s.dirty:s.t={L:STRtree([g for g,n in s.items[L]]) for L in LAY};s.ht=STRtree(s.holes) if s.holes else None;s.ct=STRtree(s.cy) if s.cy else None;s.dirty=False
    def clear(s,L,g,net):
        s.tree()
        for i in s.t[L].query(g.buffer(CL)):
            og,on=s.items[L][i]
            if on==net:continue
            if og.distance(g)<CL-1e-6:return False
        return True
    def hole_ok(s,pt):
        s.tree();h=pt.buffer(0.15)
        return s.ht is None or all(s.holes[i].distance(h)>=HOLE-1e-6 for i in s.ht.query(h.buffer(HOLE)))
    def cy_ok(s,g):
        s.tree();return s.ct is None or not any(s.cy[i].intersects(g) for i in s.ct.query(g))
O=Obs()
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):
        c=Point(mm(t.GetPosition().x),mm(t.GetPosition().y))
        for L in LAY:O.add(L,c.buffer(mm(t.GetWidth())/2),t.GetNetname())
        O.holes.append(c.buffer(mm(t.GetDrill())/2))
    else:
        O.add(t.GetLayerName(),LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2),t.GetNetname())
for f in b.GetFootprints():
    if f.GetReference() in MOVE:continue
    try:bb=f.GetCourtyard(p.F_CrtYd).BBox();O.cy.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
    except Exception:pass
    for q in f.Pads():
        bb=q.GetBoundingBox();g=box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
        for i,L in enumerate(LAY):
            if q.IsOnLayer(b.GetLayerID(L)):O.add(L,g,q.GetNetname())
        if q.GetDrillSize().x>0:O.holes.append(Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(mm(q.GetDrillSize().x)/2))
PLANE={'GND':'In1.Cu','3V3':'In2.Cu'}
PV={'GND':[],'3V3':[]}
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA) and t.GetNetname() in PV:PV[t.GetNetname()].append((mm(t.GetPosition().x),mm(t.GetPosition().y)))
def via_ok(pt,net,d=0.55):
    P=Point(pt);g=P.buffer(d/2)
    return all(O.clear(L,g,net) for L in LAY if PLANE.get(net)!=L) and O.hole_ok(P)
def add_via(pt,net,d=0.55):
    P=Point(pt)
    for L in LAY:O.add(L,P.buffer(d/2),net)
    O.holes.append(P.buffer(0.15))
def add_trk(a,z,net,L='F.Cu',w=0.15):O.add(L,LineString([a,z]).buffer(w/2),net)
def net_bcu_points(net,step=0.05):
    pts=[]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net or t.GetLayerName()!='B.Cu':continue
        a=(mm(t.GetStart().x),mm(t.GetStart().y));z=(mm(t.GetEnd().x),mm(t.GetEnd().y));n=max(1,int(math.dist(a,z)/step))
        pts+=[(round(a[0]+(z[0]-a[0])*k/n,3),round(a[1]+(z[1]-a[1])*k/n,3)) for k in range(n+1)]
    return pts
STUB_UP={'I2C_SDA':1.2}
def place(ref,sig,other,region,maxlen=4.0):
    vc=[q for q in net_bcu_points(sig) if via_ok(q,sig)]
    stub={}
    if sig in STUB_UP:
        for w in net_bcu_points(sig,0.1):
            if abs(w[1]-36.8)>1e-3:continue
            for dd in (0.4,0.6,0.8,1.0,1.2):
                q=(w[0],round(w[1]-dd,3));g=LineString([w,q]).buffer(0.075)
                if q not in stub and via_ok(q,sig) and O.clear('B.Cu',g,sig):vc.append(q);stub[q]=w
    best=None
    x0,y0,x1,y1=region
    for rot in (0,90):
        ax=(1,0) if rot==0 else (0,1)
        hw,hh=(CYX,CYY) if rot==0 else (CYY,CYX)
        x=x0
        while x<=x1:
            y=y0
            while y<=y1:
                ctr=box(x-hw,y-hh,x+hw,y+hh)
                if O.cy_ok(ctr):
                    for flip in (1,-1):
                        ps=(x-flip*OFF*ax[0],y-flip*OFF*ax[1]);po=(x+flip*OFF*ax[0],y+flip*OFF*ax[1])
                        pad=lambda c:box(c[0]-PX,c[1]-PY,c[0]+PX,c[1]+PY) if rot==0 else box(c[0]-PY,c[1]-PX,c[0]+PY,c[1]+PX)
                        if not(O.clear('F.Cu',pad(ps),sig) and O.clear('F.Cu',pad(po),other)):continue
                        # signal: straight F.Cu from pad centre to a via candidate
                        sv=None
                        for q in sorted(vc,key=lambda q:math.dist(q,ps)):
                            d=math.dist(q,ps)
                            if d>maxlen:break
                            tr=LineString([ps,q]).buffer(0.075)
                            if pad(ps).distance(Point(q).buffer(0.275))>=0.1 and O.clear('F.Cu',tr,sig) and pad(po).distance(tr)>=CL and pad(po).distance(Point(q).buffer(0.275))>=CL:sv=(q,d);break
                        if not sv:continue
                        # other pad: plane via next to it
                        ov=None
                        for dd in (0.95,1.1,1.3,1.6,2.0):
                            for dv in [(flip*ax[0],flip*ax[1]),(ax[1],ax[0]),(-ax[1],-ax[0]),(0.7071*(flip*ax[0]+ax[1]),0.7071*(flip*ax[1]+ax[0])),(0.7071*(flip*ax[0]-ax[1]),0.7071*(flip*ax[1]-ax[0]))]:
                                q=(round(po[0]+dv[0]*dd,3),round(po[1]+dv[1]*dd,3))
                                tr=LineString([po,q]).buffer(0.125)
                                if via_ok(q,other,0.6) and O.clear('F.Cu',tr,other) and pad(ps).distance(tr)>=CL and math.dist(q,sv[0])>=0.6+0.2 and pad(ps).distance(Point(q).buffer(0.3))>=CL:
                                    ov=(q,dd);break
                            if ov:break
                        if not ov:
                            for q in sorted(PV.get(other,[]),key=lambda q:math.dist(q,po)):
                                d=math.dist(q,po)
                                if d>2.0:break
                                tr=LineString([po,q]).buffer(0.125)
                                if O.clear('F.Cu',tr,other) and pad(ps).distance(tr)>=CL and math.dist(q,sv[0])>=0.8:ov=(q,d+0.5);break
                        if not ov:continue
                        score=sv[1]+0.3*ov[1]
                        if best is None or score<best[0]:best=(score,rot,flip,(round(x,2),round(y,2)),ps,po,sv[0],ov[0])
                y=round(y+0.05,3)
            x=round(x+0.05,3)
    if not best:print(ref,'NO PLACEMENT');return None
    sc,rot,flip,c,ps,po,sv,ov=best
    hw,hh=(CYX,CYY) if rot==0 else (CYY,CYX)
    O.cy.append(box(c[0]-hw,c[1]-hh,c[0]+hw,c[1]+hh))
    for q in (ps,po):O.add('F.Cu',Point(q).buffer(0.4),sig if q==ps else other)
    add_trk(ps,sv,sig);add_via(sv,sig)
    if sv in stub:add_trk(stub[sv],sv,sig,'B.Cu')
    add_trk(po,ov,other,w=0.25)
    shared=ov in PV[other]
    if not shared:add_via(ov,other,0.6);PV[other].append(ov)
    r=dict(ref=ref,rot=rot,flip=flip,center=c,sig_pad=ps,other_pad=po,sig_via=sv,other_via=ov,score=round(sc,3),sig_stub=stub.get(sv),other_via_shared=shared)
    print(json.dumps(r));return r
plan=[]
REG=tuple(map(float,sys.argv[4].split(','))) if len(sys.argv)>4 else (35.5,29.0,44.5,38.6)
ORDER=json.loads(sys.argv[5]) if len(sys.argv)>5 else [('R40','ADC_PWDN','3V3'),('R39','ADC_RESET_N','GND'),('R37','I2C_SCL','3V3'),('R38','I2C_SDA','3V3')]
for ref,sig,other in ORDER:
    r=place(ref,sig,other,REG)
    if r:plan.append(r)
json.dump(plan,open(sys.argv[3],'w'))
