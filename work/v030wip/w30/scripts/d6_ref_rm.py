# Issue 6 / step 1 (text): take REF_27M off the B.Cu under U2's top pad row.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
segs('REF_27M',[(39.35,34.0),(42.0,34.0)],'F.Cu');b.remove_via('REF_27M',(42.0,34.0))
segs('REF_27M',[(42.0,34.0),(46.3,38.3),(53.55,38.3),(54.05,38.8)],'B.Cu');b.remove_via('REF_27M',(54.05,38.8))
segs('REF_27M',[(54.05,38.8),(54.05,41.85),(54.4,42.2),(54.95,42.2)],'F.Cu')
b.save(sys.argv[2])
