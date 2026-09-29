# KiCad 7 pcbnew edit helpers
# NOTE: KiCad 7.0.11 python: BOARD.Remove() corrupts SWIG type info; do removals with pcbedit.py (text) first.
import pcbnew as p
mm=p.ToMM; MM=p.FromMM
V=lambda x,y:p.VECTOR2I(MM(x),MM(y))
_C={}
def _tracks(b):
    k=id(b)
    if k not in _C:_C[k]=list(b.GetTracks())
    return _C[k]
def near(a,b,t=1e-3):return abs(mm(a.x)-b[0])<t and abs(mm(a.y)-b[1])<t
def rm_seg(b,net,a,z,layer=None):
    hit=[t for t in _tracks(b) if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net and (layer is None or t.GetLayerName()==layer)
         and ((near(t.GetStart(),a) and near(t.GetEnd(),z)) or (near(t.GetStart(),z) and near(t.GetEnd(),a)))]
    assert len(hit)==1,(net,a,z,len(hit)); _tracks(b).remove(hit[0]);b.Remove(hit[0])
def rm_via(b,net,pt):
    hit=[t for t in _tracks(b) if isinstance(t,p.PCB_VIA) and t.GetNetname()==net and near(t.GetPosition(),pt)]
    assert len(hit)==1,(net,pt,len(hit)); _tracks(b).remove(hit[0]);b.Remove(hit[0])
def seg(b,net,a,z,layer='F.Cu',w=0.15):
    t=p.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetWidth(MM(w));t.SetLayer(b.GetLayerID(layer));t.SetNet(b.FindNet(net));b.Add(t)
def path(b,net,pts,layer='F.Cu',w=0.15):
    for a,z in zip(pts,pts[1:]):seg(b,net,a,z,layer,w)
def via(b,net,pt,d=0.55,dr=0.3):
    v=p.PCB_VIA(b);v.SetPosition(V(*pt));v.SetWidth(MM(d));v.SetDrill(MM(dr));v.SetNet(b.FindNet(net));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);b.Add(v)
def finish(b,dst,drc=True):
    p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(dst,b)
    if drc:p.WriteDRCReport(b,dst.replace('.kicad_pcb','_drc.txt'),p.EDA_UNITS_MILLIMETRES,True)
