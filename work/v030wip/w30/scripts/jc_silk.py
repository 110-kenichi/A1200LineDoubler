# J1/J2 -> HYC06-HDR15B-060, step 4 (pcbnew): re-place the reference texts that the new connector bodies cover
# (J1, J2, R15, C49), using the r10_silk.py rules; every other text stays where it is.
import sys,os,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
import pcbnew as p;from pcbk7 import V,finish
from shapely.geometry import box,Polygon,LineString
from shapely.strtree import STRtree
mm=p.ToMM;b=p.LoadBoard(sys.argv[1]);H,TH=0.8,0.15
MOVE={'J1','J2','R15','C49'}
def pad_poly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())]).buffer(0.1)
def text_box(t):bb=t.GetBoundingBox();return box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
hard=[box(0,26.1,9.2,57.9),box(85.8,26.1,95,57.9)]   # connector bodies on the board (8.9 mm from the edge)
soft=[];texts=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.IsOnLayer(p.F_Cu) or q.IsOnLayer(p.F_Mask):hard.append(pad_poly(q))
    for g in f.GraphicalItems():
        if g.GetLayer()!=p.F_SilkS:continue
        if isinstance(g,p.FP_TEXT):continue
        bb=g.GetBoundingBox();hard.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())).buffer(0.1) if g.GetShape()!=p.SHAPE_T_SEGMENT else LineString([(mm(g.GetStart().x),mm(g.GetStart().y)),(mm(g.GetEnd().x),mm(g.GetEnd().y))]).buffer(mm(g.GetWidth())/2+0.1))
    c=f.GetCourtyard(p.F_CrtYd)
    if c.OutlineCount():bb=c.BBox();soft.append((f.GetReference(),box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))))
    if f.GetReference() not in MOVE and f.Reference().IsVisible():texts.append(text_box(f.Reference()))
for d in b.GetDrawings():
    if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS:texts.append(text_box(d))
edge=box(0.6,0.6,94.4,94.4);Th=STRtree(hard);HS=STRtree([g for _,g in soft])
def free(g,tier,own):
    if not edge.contains(g):return False
    if any(hard[i].intersects(g) for i in Th.query(g)):return False
    if any(x.intersects(g.buffer(0.1)) for x in texts):return False
    if tier==1 and any(soft[i][1].intersects(g) and soft[i][0] not in (own,'J1','J2') for i in HS.query(g)):return False
    return True
def place(t,cx,cy,own,rmax=6.0,angles=(0,90)):
    for tier in (1,2):
        best=None
        for ang in angles:
            t.SetTextAngleDegrees(ang);t.SetPosition(V(0,0));w=text_box(t).bounds;n=int(rmax/0.1)
            for i in range(-n,n+1):
                for j in range(-n,n+1):
                    d=math.hypot(i,j)*0.1
                    if d>rmax or (best and d>=best[0]):continue
                    x,y=cx+i*0.1,cy+j*0.1;g=box(w[0]+x,w[1]+y,w[2]+x,w[3]+y)
                    if free(g,tier,own):best=(d,x,y,ang,g)
        if best:
            d,x,y,ang,g=best;t.SetTextAngleDegrees(ang);t.SetPosition(V(x,y));texts.append(g);return tier,(round(x,2),round(y,2),ang)
    return None,None
# J refs: just off the body ends (J1 north end; J2 south end, clear of the board title)
anchor={'J1':(4.5,25.3),'J2':(91.0,59.0)}
for ref in ('J1','J2','R15','C49'):
    f=b.FindFootprintByReference(ref);r=f.Reference()
    r.SetLayer(p.F_SilkS);r.SetTextSize(p.VECTOR2I(p.FromMM(H),p.FromMM(H)));r.SetTextThickness(p.FromMM(TH));r.SetKeepUpright(True);r.SetVisible(True)
    c=anchor.get(ref,(mm(f.GetPosition().x),mm(f.GetPosition().y)))
    res=place(r,c[0],c[1],ref)
    if res[0] is None:res=place(r,c[0],c[1],ref,rmax=9.0)
    if res[0] is None:r.SetPosition(f.GetPosition());r.SetVisible(False)   # as r10_silk.py: hidden, still on F.Fab
    print(ref,res if res[0] else 'hidden')
finish(b,sys.argv[2],drc=len(sys.argv)<4)
