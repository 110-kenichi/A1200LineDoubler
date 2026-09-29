# Issue 6 / step 2 (text): clear U2's top edge and both top corners for the DAC fan-out.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer='F.Cu'):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
# top-left: pin44 3V3 -> C36, C36 vias; pin43 GND -> via (46.6,36.05); C36 GND via
segs('3V3',[(45.8,37.05),(45.8,36.0),(46.8,35.0),(46.775,35.0)]);segs('3V3',[(46.775,35.0),(47.8,35.0),(47.775,35.0)]);b.remove_via('3V3',(47.775,35.0))
segs('GND',[(46.2,37.05),(46.2,36.3),(46.35,36.3),(46.6,36.05)]);b.remove_via('GND',(46.6,36.05))
segs('GND',[(45.225,35.0),(45.2,34.0),(45.225,34.0)]);b.remove_via('GND',(45.225,34.0))
# C40 (bulk 3V3) vias
segs('3V3',[(50.95,35.0),(51.95,35.0)]);b.remove_via('3V3',(51.95,35.0))
segs('GND',[(49.05,35.0),(49.05,33.8)]);b.remove_via('GND',(49.05,33.8))
# top-right: pin23 3V3 -> C35 + via; pin24 GND -> via; pin21 GND via; pin22 1V2 -> C29; C29 GND via
segs('3V3',[(54.2,37.05),(54.3,36.95),(54.3,36.9),(54.35,36.85),(54.35,36.75),(54.4,36.7),(54.4,36.35),(54.45,36.3),(54.45,35.35),(54.8,35.0),(54.775,35.0)])
segs('3V3',[(54.775,35.0),(55.8,35.0),(55.775,35.0)]);b.remove_via('3V3',(55.775,35.0))
segs('GND',[(53.8,37.05),(53.8,36.3),(53.55,36.3),(53.25,36.0),(53.225,36.0)]);segs('GND',[(53.225,35.0),(53.25,36.0)]);b.remove_via('GND',(53.225,36.0))
segs('GND',[(54.95,38.2),(55.95,38.2)]);b.remove_via('GND',(55.95,38.2))
segs('1V2',[(54.95,37.8),(55.05,37.7),(55.1,37.7),(55.15,37.65),(55.25,37.65),(55.3,37.6),(55.65,37.6),(55.7,37.55),(56.7,37.55),(57.0,37.25),(57.0,37.225)])
segs('1V2',[(57.0,37.225),(58.0,37.25),(58.0,37.225)])            # keep via (58,37.225): end of the y=37.225 In2 run
segs('GND',[(57.0,38.775),(58.0,38.8),(58.0,38.775)]);b.remove_via('GND',(58.0,38.775))
b.save(sys.argv[2])
