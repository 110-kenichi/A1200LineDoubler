import sys;sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'../tools'))
import pcbnew as p;from pcbk7 import *
b=p.LoadBoard(sys.argv[1])
N='DAC_PSAVE_N'
# U2.56 -> inner via -> B.Cu under EP (y=41) -> around the north end of the 1V2 B.Cu wall -> R44.1
path(b,N,[(45.05,42.2),(45.94,42.2),(46.04,42.1)]);via(b,N,(46.04,42.1))
path(b,N,[(46.04,42.1),(47.14,41.0),(52.65,41.0),(55.35,38.3),(55.35,37.95),(56.7,36.6),(60.55,36.6),(63.75,39.8)],'B.Cu')
via(b,N,(63.75,39.8));path(b,N,[(63.75,39.8),(63.95,40.0),(64.675,40.0)])
# R44 -> B.Cu y=39.85 -> via under U3 body -> U3.38 from the inside of the pad ring
path(b,N,[(63.75,39.8),(63.8,39.85),(74.95,39.85),(75.7,39.1)],'B.Cu')
via(b,N,(75.7,39.1));path(b,N,[(75.7,39.1),(75.8,39.1),(76.25,38.65),(76.25,37.837)])
finish(b,sys.argv[2])
