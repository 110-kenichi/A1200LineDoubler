# JLC DFM 2026-10-01 (Silkscreen to pad: 36 danger, Silkscreen to hole: 6 danger). pcbnew moves / layer changes /
# additions only (no BOARD.Remove):
#  - footprint silk segments: the parts closer than PADCL (0.16) to a pad (mask opening) or HOLECL (0.2) to a drilled hole (vias,
#    PTH) are cut away; a segment with nothing left (or only pieces shorter than MINLEN) goes to F.Fab. This hits the
#    0402 silk ticks of R37-R40, C42, C70-C73 (0.101 mm from their pads) and outline lines of J1/U5/R2/C68/C71 that ran
#    over via holes.
#  - U2's pin-1 dot sat on the pin-1 1V2 via (55.95,46.75): moved to the nearest free spot by pin 1.
#  - board text "REV 0.30  2026-09" ran over two JTAG vias: moved to the nearest free spot.
# usage: dfm_silk2.py in.kicad_pcb out.kicad_pcb
import sys,os,math,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
import pcbnew as p
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
mm=p.ToMM;V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
PADCL=0.16;HOLECL=0.2;MINLEN=0.15
b=p.LoadBoard(sys.argv[1])
def pp(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
padg=[pp(q) for f in b.GetFootprints() for q in f.Pads() if q.IsOnLayer(p.F_Mask)]
holeg=[Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(min(mm(q.GetDrillSize().x),mm(q.GetDrillSize().y))/2,16)
       for f in b.GetFootprints() for q in f.Pads() if q.GetDrillSize().x>0]
holeg+=[Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetDrill())/2,16) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
PADU=unary_union(padg);HOLEU=unary_union(holeg)
log=[]
for f in b.GetFootprints():
    for it in list(f.GraphicalItems()):
        if it.GetLayer()!=p.F_SilkS or isinstance(it,p.FP_TEXT) or it.GetShape()!=p.SHAPE_T_SEGMENT:continue
        a=(mm(it.GetStart().x),mm(it.GetStart().y));z=(mm(it.GetEnd().x),mm(it.GetEnd().y));w=mm(it.GetWidth())
        ln=LineString([a,z]);keep=ln.buffer(w/2,8)
        if keep.distance(PADU)>=PADCL and keep.distance(HOLEU)>=HOLECL:continue
        cut=PADU.buffer(PADCL+w/2,16).union(HOLEU.buffer(HOLECL+w/2,16))
        rest=ln.difference(cut)
        parts=[g for g in (getattr(rest,'geoms',None) or [rest]) if not g.is_empty and g.length>=MINLEN]
        if not parts:
            it.SetLayer(p.F_Fab);log.append(dict(ref=f.GetReference(),seg=[a,z],to='F.Fab'));continue
        for k,g in enumerate(parts):
            c=list(g.coords);s,e=c[0],c[-1]
            sh=it if k==0 else p.FP_SHAPE(f)
            if k>0:sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetLayer(p.F_SilkS);sh.SetWidth(it.GetWidth());f.Add(sh)
            sh.SetStart(V(round(s[0],4),round(s[1],4)));sh.SetEnd(V(round(e[0],4),round(e[1],4)));sh.SetLocalCoord()
        log.append(dict(ref=f.GetReference(),seg=[a,z],pieces=[[list(g.coords)[0],list(g.coords)[-1]] for g in parts]))
# obstacles for moved silk: pads + PADCL, holes + HOLECL, other silk (text boxes and lines) + 0.1, board edge 0.5
def silk_obst(skip):
    out=[]
    for f in b.GetFootprints():
        for it in f.GraphicalItems():
            if it is skip or it.GetLayer()!=p.F_SilkS:continue
            r=it.GetBoundingBox()
            if isinstance(it,p.FP_TEXT) and not it.IsVisible():continue
            out.append(box(mm(r.GetX()),mm(r.GetY()),mm(r.GetRight()),mm(r.GetBottom())) if isinstance(it,p.FP_TEXT) or it.GetShape()!=p.SHAPE_T_SEGMENT
                       else LineString([(mm(it.GetStart().x),mm(it.GetStart().y)),(mm(it.GetEnd().x),mm(it.GetEnd().y))]).buffer(mm(it.GetWidth())/2))
        for tx in (f.Reference(),f.Value()):
            if tx is not skip and tx.GetLayer()==p.F_SilkS and tx.IsVisible():r=tx.GetBoundingBox();out.append(box(mm(r.GetX()),mm(r.GetY()),mm(r.GetRight()),mm(r.GetBottom())))
    for d in b.GetDrawings():
        if d is not skip and d.GetLayer()==p.F_SilkS:r=d.GetBoundingBox();out.append(box(mm(r.GetX()),mm(r.GetY()),mm(r.GetRight()),mm(r.GetBottom())))
    return unary_union(out)
def free(g,so):return g.distance(PADU)>=PADCL and g.distance(HOLEU)>=HOLECL and g.distance(so)>=0.1 and box(0.5,0.5,94.5,94.5).contains(g)
def search(item,geom_at,x0,y0,R=3.0,step=0.05):
    so=silk_obst(item);best=None
    for k in range(0,int(R/step)+1):
        rr=k*step;n=max(1,int(2*math.pi*rr/step))
        for i in range(n):
            a=2*math.pi*i/n;x,y=x0+rr*math.cos(a),y0+rr*math.sin(a)
            if free(geom_at(x,y),so):return (round(x,3),round(y,3)),rr
    return None,None
# U2 pin-1 dot
u2=[f for f in b.GetFootprints() if f.GetReference()=='U2'][0]
dot=[it for it in u2.GraphicalItems() if it.GetLayer()==p.F_SilkS and not isinstance(it,p.FP_TEXT) and it.GetShape()==p.SHAPE_T_CIRCLE][0]
c0=(mm(dot.GetCenter().x),mm(dot.GetCenter().y));r=mm(dot.GetRadius());w=mm(dot.GetWidth())
pos,rr=search(dot,lambda x,y:Point(x,y).buffer(r+w/2,16),c0[0],c0[1],R=1.2)
assert pos,'no spot for the U2 pin-1 dot'
# set the circle in board coordinates (Move() works in footprint coordinates; U2 is rotated 180 deg)
dot.SetStart(V(*pos));dot.SetEnd(V(pos[0]+r,pos[1]));dot.SetLocalCoord()
assert abs(mm(dot.GetCenter().x)-pos[0])<1e-3 and abs(mm(dot.GetCenter().y)-pos[1])<1e-3,(mm(dot.GetCenter().x),mm(dot.GetCenter().y))
log.append(dict(ref='U2',pin1_dot=[c0,pos],shift=rr))
# board text
tx=[d for d in b.GetDrawings() if isinstance(d,p.PCB_TEXT) and d.GetText().startswith('REV 0.30')][0]
r0=tx.GetBoundingBox();bx=box(mm(r0.GetX()),mm(r0.GetY()),mm(r0.GetRight()),mm(r0.GetBottom()));t0=(mm(tx.GetPosition().x),mm(tx.GetPosition().y))
pos,rr=search(tx,lambda x,y:box(bx.bounds[0]+x-t0[0],bx.bounds[1]+y-t0[1],bx.bounds[2]+x-t0[0],bx.bounds[3]+y-t0[1]),t0[0],t0[1],R=15.0,step=0.25)
assert pos,'no spot for the board text'
tx.SetPosition(V(*pos));log.append(dict(text=tx.GetText(),moved=[t0,pos],shift=rr))
for x in log:print(x)
json.dump(log,open(sys.argv[2].replace('.kicad_pcb','_silk2.json'),'w'),indent=1)
from pcbk7 import finish
finish(b,sys.argv[2])
