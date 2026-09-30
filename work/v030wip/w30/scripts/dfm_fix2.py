# JLC DFM follow-up, step 2 (pcbnew, no removals):
#  - C71 (0402): shift +0.40 mm in x so the U2.23 3V3 plane via (54.2,36.1) leaves pad 1; GND via (55.55,36.3) -> (55.55,36.45)
#    so its hole stays out of the shifted pad 2. Tracks follow.
#  - J3: shell slots 0.6 -> 0.8 mm wide, pads 1.0 -> 1.2 mm (footprint Amiga:USB_C_Receptacle_HRO_TYPE-C-31-M-12_Slot0.8).
#  - C29 (0603, 1V2) also shifts +0.40 mm in x so its courtyard stays clear of C71.
#  - (the only 0.5 mm via, GND 17.15,46.45, stays 0.5 mm: 0.55 mm violates clearance to U1.22 / ADC_1V9A)
#  - C15850 group: value "10uF 25V" for C47/C54/C55/C57/C59 (one JLC BOM line).
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
import pcbnew as p;from pcbk7 import finish
mm=p.ToMM;V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
b=p.LoadBoard(sys.argv[1])
def at(q,x,y,t=1e-3):return abs(mm(q.x)-x)<t and abs(mm(q.y)-y)<t
tr=list(b.GetTracks())
def move_point(net,old,new):
    n=0
    for t in tr:
        if t.GetNetname()!=net:continue
        if isinstance(t,p.PCB_VIA):
            if at(t.GetPosition(),*old):t.SetPosition(V(*new));n+=1
        else:
            if at(t.GetStart(),*old):t.SetStart(V(*new));n+=1
            if at(t.GetEnd(),*old):t.SetEnd(V(*new));n+=1
    assert n,(net,old);return n
# C71
f=b.FindFootprintByReference('C71');x,y=mm(f.GetPosition().x),mm(f.GetPosition().y);f.SetPosition(V(x+0.40,y))
move_point('3V3',(54.27,35.905),(54.67,35.905))
move_point('GND',(55.23,35.905),(55.63,35.905))
move_point('GND',(55.55,36.3),(55.55,36.45))
move_point('GND',(55.55,36.225),(55.55,36.3))   # keep the short vertical stub inside the via land
# C29 follows (courtyard)
f=b.FindFootprintByReference('C29');x,y=mm(f.GetPosition().x),mm(f.GetPosition().y);f.SetPosition(V(x+0.40,y))
move_point('1V2',(57.975,36.3),(58.375,36.3))
move_point('GND',(56.425,36.3),(56.825,36.3))
# J3 slots
f=b.FindFootprintByReference('J3');f.SetFPID(p.LIB_ID('Amiga','USB_C_Receptacle_HRO_TYPE-C-31-M-12_Slot0.8'));n=0
for q in f.Pads():
    if q.GetDrillShape()==p.PAD_DRILL_SHAPE_OBLONG:
        d=q.GetDrillSize();s=q.GetSize();o=f.GetOrientationDegrees()
        # footprint at 0 deg: slots are vertical (x = width)
        q.SetDrillSize(p.VECTOR2I(p.FromMM(0.8),d.y));q.SetSize(p.VECTOR2I(p.FromMM(1.2),s.y));n+=1
assert n==4
for r in ('C47','C54','C55','C57','C59'):b.FindFootprintByReference(r).SetValue('10uF 25V')
finish(b,sys.argv[2])
