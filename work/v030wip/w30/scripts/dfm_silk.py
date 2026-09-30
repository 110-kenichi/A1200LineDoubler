# JLC DFM follow-up, step 3 (pcbnew): re-place reference texts that come within 0.15 mm of a pad or a drilled hole
# (JLC DFM "Silkscreen to pad" / "Silkscreen to hole"). Same rules as r10_silk.py plus holes as hard obstacles;
# texts that are already clear stay where they are.
import sys,os,math,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
import pcbnew as p;from pcbk7 import V,finish
from shapely.geometry import box,Polygon,LineString,Point
from shapely.strtree import STRtree
mm=p.ToMM;b=p.LoadBoard(sys.argv[1]);CLR=0.15
def pad_poly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
def tbox(t):bb=t.GetBoundingBox();return box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
hard=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.IsOnLayer(p.F_Cu) or q.IsOnLayer(p.F_Mask):hard.append(pad_poly(q).buffer(CLR))
        if q.GetDrillSize().x>0:hard.append(Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(mm(max(q.GetDrillSize().x,q.GetDrillSize().y))/2+CLR))
    for g in f.GraphicalItems():
        if g.GetLayer()==p.F_SilkS and not isinstance(g,p.FP_TEXT):
            hard.append(LineString([(mm(g.GetStart().x),mm(g.GetStart().y)),(mm(g.GetEnd().x),mm(g.GetEnd().y))]).buffer(mm(g.GetWidth())/2+0.1) if g.GetShape()==p.SHAPE_T_SEGMENT else box(*[mm(v) for v in (g.GetBoundingBox().GetX(),g.GetBoundingBox().GetY(),g.GetBoundingBox().GetRight(),g.GetBoundingBox().GetBottom())]).buffer(0.1))
for v in b.GetTracks():
    if isinstance(v,p.PCB_VIA):hard.append(Point(mm(v.GetPosition().x),mm(v.GetPosition().y)).buffer(mm(v.GetDrill())/2+CLR))
hard+= [box(0,26.1,9.2,57.9),box(85.8,26.1,95,57.9)]   # J1/J2 bodies
Th=STRtree(hard);edge=box(0.6,0.6,94.4,94.4)
bad=lambda g:any(hard[i].intersects(g) for i in Th.query(g))
texts={}
for f in b.GetFootprints():
    if f.Reference().IsVisible():texts[f.GetReference()]=tbox(f.Reference())
for d in b.GetDrawings():
    if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS:texts['#'+d.GetText()]=tbox(d)
move=[r for r,g in texts.items() if not r.startswith('#') and bad(g)]
soft=[(f.GetReference(),box(*[mm(v) for v in (f.GetCourtyard(p.F_CrtYd).BBox().GetX(),f.GetCourtyard(p.F_CrtYd).BBox().GetY(),f.GetCourtyard(p.F_CrtYd).BBox().GetRight(),f.GetCourtyard(p.F_CrtYd).BBox().GetBottom())])) for f in b.GetFootprints() if f.GetCourtyard(p.F_CrtYd).OutlineCount()]
HS=STRtree([g for _,g in soft])
def free(g,tier,own):
    if not edge.contains(g) or bad(g):return False
    if any(x.intersects(g.buffer(0.1)) for k,x in texts.items() if k!=own):return False
    if tier==1 and any(soft[i][1].intersects(g) and soft[i][0]!=own for i in HS.query(g)):return False
    return True
log={'moved':[],'hidden':[]}
for ref in move:
    f=b.FindFootprintByReference(ref);t=f.Reference();cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y);best=None
    for tier in (1,2):
        for ang in (0,90):
            t.SetTextAngleDegrees(ang);t.SetPosition(V(0,0));w=tbox(t).bounds
            for k in range(0,76):
                rr=k*0.1;n=max(1,int(2*math.pi*rr/0.1))
                if best and rr>=best[0]:break
                for i in range(n):
                    a=2*math.pi*i/n;x,y=cx+rr*math.cos(a),cy+rr*math.sin(a);g=box(w[0]+x,w[1]+y,w[2]+x,w[3]+y)
                    if free(g,tier,ref):best=(rr,x,y,ang,g);break
        if best:break
    if best:
        rr,x,y,ang,g=best;t.SetTextAngleDegrees(ang);t.SetPosition(V(x,y));texts[ref]=g;log['moved'].append([ref,round(rr,2)])
    else:
        t.SetPosition(f.GetPosition());t.SetVisible(False);texts.pop(ref,None);log['hidden'].append(ref)
print('checked',len(texts),'moved',len(log['moved']),'hidden',log['hidden'])
json.dump(log,open(sys.argv[2].replace('.kicad_pcb','_silk.json'),'w'),indent=1)
finish(b,sys.argv[2])
