# C34 (U2 3V3 decoupling) relocation for v0.30wip. KiCad 7 pcbnew. usage: python3 c34.py <src.kicad_pcb> <dst.kicad_pcb>
import pcbnew as p, sys
mm=p.ToMM; MM=p.FromMM; V=lambda x,y:p.VECTOR2I(MM(x),MM(y))
src,dst=sys.argv[1],sys.argv[2]
b=p.LoadBoard(src)
c=b.FindFootprintByReference('C34')
cx,cy=45.4,49.15
c.SetPosition(V(cx,cy))
for rot in (90,270):
    c.SetOrientationDegrees(rot)
    pads={q.GetNumber():q for q in c.Pads()}
    if mm(pads['1'].GetPosition().y)<cy: break
print('rot',rot,{n:(round(mm(q.GetPosition().x),3),round(mm(q.GetPosition().y),3)) for n,q in pads.items()})
# move reference text next to part
ref=c.Reference(); ref.SetPosition(V(43.5,50.3)); ref.SetTextAngleDegrees(0)
net=lambda n:b.FindNet(n)
def trk(a,z,n,w=0.25):
    t=p.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*z)); t.SetWidth(MM(w)); t.SetLayer(p.F_Cu); t.SetNet(net(n)); b.Add(t)
def via(pt,n,d,dr):
    v=p.PCB_VIA(b); v.SetPosition(V(*pt)); v.SetWidth(MM(d)); v.SetDrill(MM(dr)); v.SetNet(net(n)); v.SetViaType(p.VIATYPE_THROUGH); v.SetLayerPair(p.F_Cu,p.B_Cu); b.Add(v)
p1=(mm(pads['1'].GetPosition().x),mm(pads['1'].GetPosition().y)); p2=(mm(pads['2'].GetPosition().x),mm(pads['2'].GetPosition().y))
trk(p1,(45.6,47.6),'3V3')          # to existing 3V3 via of U2.67
gv=(p2[0],p2[1]+0.95); trk(p2,gv,'GND'); via(gv,'GND',0.6,0.3)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(dst,b)
p.WriteDRCReport(b,dst.replace('.kicad_pcb','_drc.txt'),p.EDA_UNITS_MILLIMETRES,True)
