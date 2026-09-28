import sys;sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'../tools'))
import pcbedit as E
b=E.Board(sys.argv[1])
pts=[(46.04,42.1),(47.14,41.0),(52.65,41.0),(55.35,38.3),(55.35,37.95),(56.7,36.6),(60.55,36.6),(63.75,39.8)]
for a,z in zip(pts,pts[1:]):b.remove_segment('DAC_PSAVE_N',a,z,layer='B.Cu')
b.save(sys.argv[2])
