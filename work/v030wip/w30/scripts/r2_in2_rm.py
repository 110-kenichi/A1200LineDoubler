# Review #2 (text): In2 ADC_3V3A / ADC_1V9A lines that ran under GIN_1's B.Cu (4.9 mm of reference gap).
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer='In2.Cu'):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
segs('ADC_3V3A',[(15.75,44.05),(15.75,42.4),(17.85,42.4),(18.05,42.2),(18.05,40.05)])
segs('ADC_1V9A',[(15.0,41.775),(14.4,42.375),(13.925,42.85),(13.925,47.5)])
b.save(sys.argv[2])
