# Issue 6 / step 2 (pcbnew): power pins at U2's top corners re-connected so the DAC fan can pass outside them.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,path,via,finish
b=p.LoadBoard(sys.argv[1])
def place(ref,x,y,rot):f=b.FindFootprintByReference(ref);f.SetPosition(V(x,y));f.SetOrientationDegrees(rot)
PW=0.25
# ---- top-left
path(b,'GND',[(46.2,37.05),(46.2,37.9),(46.75,38.45),(46.75,38.65)])                       # pin43 -> EP corner
place('C36',44.4,35.0,0)                                                     # pad1 3V3 (43.625) / pad2 GND (45.175)? -> fixed below
f=b.FindFootprintByReference('C36');pd={q.GetNumber():q for q in f.Pads()}
p1=(p.ToMM(pd['1'].GetPosition().x),p.ToMM(pd['1'].GetPosition().y))
if p1[0]<44.4:place('C36',44.4,35.0,180)                                     # want pad1 (3V3) east, next to pin44
path(b,'3V3',[(45.8,37.05),(45.8,35.6),(45.175,35.0)],w=0.2)                 # pin44 -> C36.1
path(b,'3V3',[(45.175,35.0),(45.175,34.1)],w=PW);via(b,'3V3',(45.175,34.1),0.6)
path(b,'GND',[(43.625,35.0),(43.625,34.1)],w=PW);via(b,'GND',(43.625,34.1),0.6)
# R0 (pin47): inner via, B.Cu north under the top pad row, up again north of the fan
path(b,'DAC_R0',[(45.05,38.6),(45.69,38.6),(46.04,38.95)]);via(b,'DAC_R0',(46.04,38.95))
path(b,'DAC_R0',[(46.04,38.95),(46.04,29.0)],'B.Cu');via(b,'DAC_R0',(46.04,29.0))
# ---- top-right
path(b,'GND',[(53.8,37.05),(53.8,37.9),(53.35,38.35),(53.35,38.65)])        # pin24 -> EP corner
path(b,'GND',[(54.95,38.2),(54.2,38.2),(53.75,38.65),(53.35,38.65)])        # pin21 -> EP corner
path(b,'1V2',[(54.95,37.8),(55.6,37.8),(55.85,37.55),(55.9,37.55)],w=0.2);via(b,'1V2',(55.9,37.55),0.6)   # pin22 -> In2 1V2
path(b,'3V3',[(54.2,37.05),(54.2,36.1)],w=0.2);via(b,'3V3',(54.2,36.1),0.6)                                # pin23 -> plane
# park caps that sit in the fan; re-placed after the fan is routed
for i,r in enumerate(['C35','C40','C29']):place(r,88.0,20.0+2.5*i,0)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
