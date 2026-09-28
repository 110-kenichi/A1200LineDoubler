import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,path,via,finish
b=p.LoadBoard(sys.argv[1])
# park parts that sit in the corridors; final positions are chosen after routing
for i,r in enumerate(['R41','R42','R14','C37']):
    f=b.FindFootprintByReference(r);f.SetPosition(V(88.0,6.0+2.5*i));f.SetOrientationDegrees(0)
# DAC_CLK_RAW (pin 3): escape south-east under the JTAGSEL staircase via into the y=46 lane
path(b,'DAC_CLK_RAW',[(54.95,45.4),(55.45,45.4),(56.05,46.0),(57.0,46.0)])
N='DAC_CLK_RAW'
path(b,N,[(57.0,46.0),(60.2,46.0),(60.5,46.3),(60.5,50.9),(63.6,54.0),(65.86,54.0)])   # x=60.5 clears C41's 1V2 via (59.9,50.75)
path(b,N,[(60.5,49.95),(57.0,49.95)])                       # R43 (pull-down) stays at (57,49.5)
N='V_OUT_RAW'
path(b,N,[(54.95,41.4),(59.75,41.4),(61.15,42.8),(61.15,45.6)]);via(b,N,(61.15,45.6))
path(b,N,[(61.15,45.6),(69.8,54.25),(70.45,54.25)],'B.Cu')
N='H_OUT_RAW'
path(b,N,[(54.95,41.0),(61.1,41.0),(61.85,41.75),(61.85,44.9)]);via(b,N,(61.85,44.9))
path(b,N,[(61.85,44.9),(68.2,51.25),(72.65,51.25)],'B.Cu')
# pull resistors R41/R42 near U5 (pullsearch result), R14 in the pocket between the B-bus and G/BLANK corridors, C37 spare 3V3 decap
PL=[{"ref": "R42", "rot": 90, "flip": 1, "center": [78.3, 56.05], "sig_pad": [78.3, 55.224999999999994], "other_pad": [78.3, 56.875], "sig_via": [78.293, 54.393], "other_via": [78.3, 57.825], "score": 1.117, "sig_stub": None, "other_via_shared": False}, {"ref": "R41", "rot": 0, "flip": -1, "center": [76.05, 54.0], "sig_pad": [76.875, 54.0], "other_pad": [75.225, 54.0], "sig_via": [79.936, 52.536], "other_via": [75.225, 54.95], "score": 3.678, "sig_stub": None, "other_via_shared": False}]
for r in PL:
    f=b.FindFootprintByReference(r['ref']);f.SetPosition(V(*r['center']));f.SetOrientationDegrees(r['rot'])
    q1=[q for q in f.Pads() if q.GetNumber()=='1'][0]
    if abs(p.ToMM(q1.GetPosition().x)-r['sig_pad'][0])>1e-3 or abs(p.ToMM(q1.GetPosition().y)-r['sig_pad'][1])>1e-3:f.SetOrientationDegrees(r['rot']+180)
    sig=q1.GetNetname();o=[q for q in f.Pads() if q.GetNumber()=='2'][0].GetNetname()
    path(b,sig,[tuple(r['sig_pad']),tuple(r['sig_via'])]);via(b,sig,tuple(r['sig_via']))
    path(b,o,[tuple(r['other_pad']),tuple(r['other_via'])],w=0.25);via(b,o,tuple(r['other_via']),0.6)
f=b.FindFootprintByReference('R14');f.SetPosition(V(66.3,45.9));f.SetOrientationDegrees(0)
path(b,'GND',[(67.125,45.9),(68.05,45.9)],w=0.25);via(b,'GND',(68.05,45.9),0.6)
f=b.FindFootprintByReference('C37');f.SetPosition(V(70.5,57.6));f.SetOrientationDegrees(0)
path(b,'3V3',[(69.725,57.6),(69.725,58.5)],w=0.25);via(b,'3V3',(69.725,58.5),0.6)
path(b,'GND',[(71.275,57.6),(71.275,58.5)],w=0.25);via(b,'GND',(71.275,58.5),0.6)
finish(b,sys.argv[2])
