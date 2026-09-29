# Review #1 (pcbnew): add 100nF 0402 decaps for U2 VCCO pins 12 and 23 (3V3).
#  C70 next to pin12's plane via (55.95,42.0), GND via (58.0,42.05) in the TMS/TCK B.Cu gap.
#  C71 north of pin23's plane via (54.2,36.1), GND pad on C29's GND via (55.55,36.3).
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,path,via,finish
b=p.LoadBoard(sys.argv[1]);mm=p.ToMM
SHEET='/ecfa7323-a425-5fed-9824-71c38a2d27b0/'
NEW={'C70':('a0e1c070-0000-4000-8000-00000000c070',56.95,42.05),'C71':('a0e1c071-0000-4000-8000-00000000c071',54.75,35.905)}
for ref,(uid,x,y) in NEW.items():
    f=p.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0402_1005Metric');f.SetParent(b)
    f.SetReference(ref);f.SetValue('100nF');f.SetPath(p.KIID_PATH(SHEET+uid));f.SetProperty('MPN','100nF');f.SetProperty('LCSC','')
    b.Add(f);f.SetPosition(V(x,y))
    for ang in (0,180):
        f.SetOrientationDegrees(ang);q1=[q for q in f.Pads() if q.GetNumber()=='1'][0]
        if mm(q1.GetPosition().x)<x:break
    for q in f.Pads():q.SetNet(b.FindNet('3V3' if q.GetNumber()=='1' else 'GND'))
    t=f.Reference();t.SetTextSize(p.VECTOR2I(p.FromMM(0.5),p.FromMM(0.5)));t.SetTextThickness(p.FromMM(0.08))
# C70: pad1 -> pin12 via, pad2 -> new GND via
path(b,'3V3',[(56.47,42.05),(56.2,42.05),(55.95,42.0)],w=0.25)
path(b,'GND',[(57.43,42.05),(58.0,42.05)],w=0.25);via(b,'GND',(58.0,42.05),0.6)
# C71: pad1 -> pin23 via, pad2 -> C29's GND via
path(b,'3V3',[(54.27,35.905),(54.2,35.975),(54.2,36.1)],w=0.25)
path(b,'GND',[(55.23,35.905),(55.55,36.225),(55.55,36.3)],w=0.25)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
