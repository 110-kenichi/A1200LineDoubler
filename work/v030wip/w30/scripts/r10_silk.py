# Issue 10 (pcbnew): silkscreen clean-up.
# - reference designators: 0.8 mm / 0.15 mm, placed at the nearest spot clear of pad openings, silk graphics,
#   other texts and the board edge (tier 1: also clear of all courtyards; tier 2: may sit under a neighbour's courtyard);
#   hidden when no spot exists within 7.5 mm (still on F.Fab).
# - board texts: stale "PARTIAL ANALOG ROUTING - REVIEW ONLY" -> revision text; texts moved off copper.
import sys,os,math,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,finish
from shapely.geometry import box,Polygon,LineString,Point
from shapely.strtree import STRtree
mm=p.ToMM;b=p.LoadBoard(sys.argv[1]);H,TH=0.8,0.15
def pad_poly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())]).buffer(0.1)
hard=[];soft=[];texts=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.IsOnLayer(p.F_Cu) or q.IsOnLayer(p.F_Mask):hard.append(pad_poly(q))
    for g in f.GraphicalItems():
        if g.GetLayer()==p.F_SilkS and not isinstance(g,p.FP_TEXT):
            bb=g.GetBoundingBox();hard.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())).buffer(0.1) if g.GetShape()!=p.SHAPE_T_SEGMENT else LineString([(mm(g.GetStart().x),mm(g.GetStart().y)),(mm(g.GetEnd().x),mm(g.GetEnd().y))]).buffer(mm(g.GetWidth())/2+0.1))
    c=f.GetCourtyard(p.F_CrtYd)
    if c.OutlineCount():bb=c.BBox();soft.append((f.GetReference(),box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):continue
edge=box(0.6,0.6,94.4,94.4)
# board texts first
REV='REV 0.30  2026-09'
bt=[d for d in b.GetDrawings() if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS]
def text_box(t):bb=t.GetBoundingBox();return box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
Th=STRtree(hard);HS=STRtree([g for _,g in soft])
def free(g,tier,own=None):
    if not edge.contains(g):return False
    if any(hard[i].intersects(g) for i in Th.query(g)):return False
    if any(x.intersects(g.buffer(0.1)) for x in texts):return False
    if tier==1 and any(soft[i][1].intersects(g) and soft[i][0]!=own for i in HS.query(g)):return False
    return True
def place(t,cx,cy,own,rmax=4.5,angles=(0,90)):
    for tier in (1,2):
        best=None
        for ang in angles:
            t.SetTextAngleDegrees(ang);t.SetPosition(V(0,0));g0=text_box(t);w=g0.bounds
            n=int(rmax/0.1)
            for i in range(-n,n+1):
                for j in range(-n,n+1):
                    d=math.hypot(i,j)*0.1
                    if d>rmax or (best and d>=best[0]):continue
                    x,y=cx+i*0.1,cy+j*0.1;g=box(w[0]+x,w[1]+y,w[2]+x,w[3]+y)
                    if free(g,tier,own):best=(d,x,y,ang,g)
        if best:
            d,x,y,ang,g=best;t.SetTextAngleDegrees(ang);t.SetPosition(V(x,y));texts.append(g);return tier,round(d,2)
    return None,None
log={'hidden':[],'tier2':[],'moved':0}
for t in bt:
    if t.GetText().startswith('PARTIAL ANALOG ROUTING'):t.SetText(REV)
    t.SetTextThickness(p.FromMM(0.15))
    c=t.GetPosition();tier,d=place(t,mm(c.x),mm(c.y),None,rmax=8,angles=(0,))
    if tier is None:log['hidden'].append(t.GetText())
# references, biggest parts first
fps=sorted(b.GetFootprints(),key=lambda f:-f.GetBoundingBox(False,False).GetArea())
for f in fps:
    r=f.Reference();r.SetLayer(p.F_SilkS);r.SetTextSize(p.VECTOR2I(p.FromMM(H),p.FromMM(H)));r.SetTextThickness(p.FromMM(TH));r.SetKeepUpright(True)
    c=f.GetPosition();tier,d=place(r,mm(c.x),mm(c.y),f.GetReference())
    if tier is None:tier,d=place(r,mm(c.x),mm(c.y),f.GetReference(),rmax=7.5)   # second pass, wider
    if tier is None:r.SetVisible(False);log['hidden'].append(f.GetReference())
    else:
        r.SetVisible(True);log['moved']+=1
        if tier==2:log['tier2'].append(f.GetReference())
# pin-1 marker circles that sit on a pad opening: slide them away from the part centre until clear
for f in b.GetFootprints():
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
    for g in f.GraphicalItems():
        if g.GetLayer()!=p.F_SilkS or isinstance(g,p.FP_TEXT) or g.GetShape()!=p.SHAPE_T_CIRCLE:continue
        c=g.GetCenter();x,y=mm(c.x),mm(c.y);r=mm(g.GetRadius())+mm(g.GetWidth())/2
        pads=[pad_poly(q) for q in f.Pads()]
        if not any(Point(x,y).buffer(r).intersects(q) for q in pads):continue
        dx,dy=x-cx,y-cy;n=math.hypot(dx,dy);dx,dy=dx/n,dy/n
        for k in range(1,31):
            nx,ny=x+dx*0.05*k,y+dy*0.05*k
            if not any(Point(nx,ny).buffer(r).intersects(q) for q in hard):
                r0=mm(g.GetRadius());g.SetStart(V(nx,ny));g.SetEnd(V(nx+r0,ny));g.SetLocalCoord();log.setdefault('pin1_moved',[]).append([f.GetReference(),round(nx,2),round(ny,2)]);break
json.dump(log,open(sys.argv[2].replace('.kicad_pcb','_silk.json'),'w'),indent=1)
print('placed',log['moved'],'tier2',len(log['tier2']),'hidden',len(log['hidden']),log['hidden'])
finish(b,sys.argv[2],drc=len(sys.argv)<4)
