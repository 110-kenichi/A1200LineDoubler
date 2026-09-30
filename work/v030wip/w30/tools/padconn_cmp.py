# Compare pad connections between two boards: for every pad, the widest track (any layer the pad is on) that touches
# it, plus whether a via land overlaps it. Reports pads whose widest touching track got narrower or disappeared.
# usage: padconn_cmp.py before.kicad_pcb after.kicad_pcb
import sys
import pcbnew as p
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
mm=p.ToMM
def scan(fn):
    b=p.LoadBoard(fn);res={}
    tr=[t for t in b.GetTracks()]
    geo=[];meta=[]
    for t in tr:
        if isinstance(t,p.PCB_VIA):
            geo.append(Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetWidth())/2,16));meta.append(('via',t.GetNetCode(),None,mm(t.GetWidth())))
        else:
            geo.append(LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2,8))
            meta.append(('trk',t.GetNetCode(),b.GetLayerName(t.GetLayer()),mm(t.GetWidth())))
    T=STRtree(geo)
    for f in b.GetFootprints():
        for q in f.Pads():
            if not q.GetNetname():continue
            o=q.GetEffectivePolygon().Outline(0);g=Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
            ls={b.GetLayerName(l) for l in q.GetLayerSet().Seq()};w=0;via=False
            for i in T.query(g):
                k,net,L,wd=meta[i]
                if net!=q.GetNetCode() or not geo[i].intersects(g):continue
                if k=='via':via=True
                elif L in ls or q.GetAttribute()==p.PAD_ATTRIB_PTH:w=max(w,wd)
            res[f.GetReference()+'.'+q.GetNumber()]=(round(w,3),via,q.GetNetname())
    return res
a=scan(sys.argv[1]);b=scan(sys.argv[2]);bad=[]
for k,(w0,v0,net) in a.items():
    w1,v1,_=b.get(k,(0,False,net))
    if w1+1e-6<w0 or (v0 and not v1 and w1==0):bad.append((k,net,'track %.3f->%.3f'%(w0,w1),'via %s->%s'%(v0,v1)))
print('pads with a narrower/lost connection:',len(bad))
for x in bad:print('  ',x)
sys.exit(1 if bad else 0)
