# Review #3 follow-up (pcbnew): 3V3-GND decaps (100nF 0402) next to REF_27M layer-change vias (37.75,35.6) and (40.2,34.0).
# Placement from tools/capvia.py -> r4_refdecap_plan.json (pad1 3V3, pad2 GND, each with a short stub + plane via).
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,path,via,finish
b=p.LoadBoard(sys.argv[1]);mm=p.ToMM;here=os.path.dirname(os.path.abspath(__file__))
SHEET='/ecfa7323-a425-5fed-9824-71c38a2d27b0/'
REFS=[('C72','a0e1c072-0000-4000-8000-00000000c072'),('C73','a0e1c073-0000-4000-8000-00000000c073')]
for (ref,uid),s in zip(REFS,json.load(open(os.path.join(here,'r4_refdecap_plan.json')))):
    f=p.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0402_1005Metric');f.SetParent(b)
    f.SetReference(ref);f.SetValue('100nF');f.SetPath(p.KIID_PATH(SHEET+uid));f.SetProperty('MPN','100nF');f.SetProperty('LCSC','')
    b.Add(f);f.SetPosition(V(*s['center']))
    for ang in (0,90,180,270):
        f.SetOrientationDegrees(ang);q1=[q for q in f.Pads() if q.GetNumber()=='1'][0]
        if abs(mm(q1.GetPosition().x)-s['pad1'][0])<1e-3 and abs(mm(q1.GetPosition().y)-s['pad1'][1])<1e-3:break
    else:raise SystemExit(ref+' orientation')
    for q in f.Pads():q.SetNet(b.FindNet('3V3' if q.GetNumber()=='1' else 'GND'))
    t=f.Reference();t.SetTextSize(p.VECTOR2I(p.FromMM(0.5),p.FromMM(0.5)));t.SetTextThickness(p.FromMM(0.08))
    for pad,v,net in ((s['pad1'],s['via1'],'3V3'),(s['pad2'],s['via2'],'GND')):
        path(b,net,[tuple(pad),tuple(v)],w=0.25);via(b,net,tuple(v),0.6)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
