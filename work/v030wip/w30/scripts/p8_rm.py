# Issue 8 (text): open the U1 input pins that are walled in by other routing.
# - ADC_1V9A pin7 -> C14 branch along x=17.1 (C14 stays on the net through its via (15,41.775) and In2)
# - ADC_3V3A pin13/14 -> C16 branch along x=17.1 (C16 stays on the net through its via (15,45.275) and In2)
# - GIN_4 pin96 -> C8 along y=33.3 over the pin 97-99 pad ends (re-routed in p8_add.py)
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer='F.Cu'):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
segs('ADC_1V9A',[(17.75,39.05),(17.3,39.05),(17.3,39.1),(17.1,39.3),(17.1,40.65),(16.95,40.8),(16.95,40.85),(16.1,41.7),(16.05,41.7),(16.0,41.75)])
segs('ADC_1V9A',[(17.8,39.0),(17.75,39.05)])
segs('ADC_3V3A',[(17.3,42.55),(17.3,42.6),(17.1,42.8),(17.1,44.15),(16.95,44.3),(16.95,44.35),(16.1,45.2),(16.05,45.2),(16.0,45.25)])
segs('GIN_4',[(22.0,34.35),(21.95,34.3),(21.95,33.3),(20.1,33.3),(19.1,32.3),(19.05,32.3),(19.0,32.25),(19.0,32.275)])
# GIN_1 B.Cu from the U1 inner via (19.75,36.5) to C49's via: crosses the pin 9-11 escape area (re-routed in p8_add.py)
segs('GIN_1',[(19.75,36.5),(18.75,37.5),(18.75,37.65),(18.7,37.7),(18.7,38.35),(15.8,41.25),(15.8,47.35),(15.6,47.55),(15.6,47.7),(12.8,50.5),(12.775,50.5)],'B.Cu')
# In2 ADC_3V3A diagonal (15.75,42.4)-(18.05,40.05): moved to y=42.4 / x=18.05 in p8_add.py
segs('ADC_3V3A',[(15.75,42.4),(17.9,40.25),(17.9,40.2),(18.05,40.05)],'In2.Cu')
# BIN_3 pin16 -> C6: wraps around C7 (BIN_2) and encloses its pad; re-routed in p8_add.py
segs('BIN_3',[(18.35,43.5),(19.35,43.5),(19.4,43.55),(19.4,48.45),(19.35,48.45),(19.05,48.75),(18.6,48.75),(17.05,50.3),(13.95,50.3),(13.95,49.1),(13.15,48.3),(12.1,48.3),(12.1,45.6),(12.2,45.5),(12.225,45.5)])
# ADC_1V9A B.Cu link (15,41.775)->(13.925,47.5): moved to In2 in p8_add.py so GIN_1 can pass on B.Cu
segs('ADC_1V9A',[(15.0,41.775),(15.0,41.75),(15.0,42.85),(14.35,43.5),(14.35,43.6),(14.2,43.75),(14.2,44.2),(13.9,44.5),(13.925,47.5)],'B.Cu')
b.save(sys.argv[2])
