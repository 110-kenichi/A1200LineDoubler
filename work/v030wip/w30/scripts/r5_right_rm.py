# Issue 5, step 1 (text edit): clear U2's right side in front of pins 1-12.
# - C37 (pin12 3V3 decap) and C31 (pin1 1V2 decap) connections and their x=58 plane vias
# - pin2 GND via (55.95,45.4)
# - the 1V2 In2 link that runs x 58-58.75 (via field will sit there); re-made at x=55.0 in step 2
import sys,os,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer='F.Cu'):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
# C37 / pin 12
segs('3V3',[(54.95,41.8),(56.45,41.8),(57.0,41.25),(57.0,41.225),(58.0,41.25),(58.0,41.225)])
b.remove_via('3V3',(58.0,41.225))
segs('GND',[(57.0,42.775),(58.0,42.8),(58.0,42.775)]);b.remove_via('GND',(58.0,42.775))
# C31 / pin 1
segs('1V2',[(54.95,46.2),(56.0,46.2),(56.2,46.0),(56.25,46.0),(57.0,45.25),(57.0,45.225),(58.0,45.25),(58.0,45.225)])
b.remove_via('1V2',(58.0,45.225))
segs('GND',[(57.0,46.775),(58.0,46.8),(58.0,46.775)]);b.remove_via('GND',(58.0,46.775))
# pin 2 GND via
segs('GND',[(54.95,45.8),(55.7,45.8),(55.7,45.65),(55.95,45.4)]);b.remove_via('GND',(55.95,45.4))
# 1V2 In2 link x 58-58.75 (keep the y=37.225 run into via (58,37.225))
n=b.nets['1V2'];keep=0;drop=[]
for i,l in enumerate(b.lines):
    m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "In2.Cu"\) \(net (\d+)\)',l)
    if not m or int(m.group(5))!=n:continue
    x1,y1,x2,y2=map(float,m.group(1,2,3,4))
    if min(x1,x2)>=57.9 and max(x1,x2)<=58.8 and min(y1,y2)>=37.24 and max(y1,y2)<=45.3:drop.append(i)
    elif {(x1,y1),(x2,y2)}=={(58.0,45.225),(55.95,47.3)}:drop.append(i)
    elif {(x1,y1),(x2,y2)}=={(58.0,37.25),(58.0,37.225)}:drop.append(i)
for i in reversed(drop):del b.lines[i]
print('In2 1V2 segments removed',len(drop))
b.save(sys.argv[2])
