import sys;sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'../tools'))
import pcbnew as p;from pcbk7 import *
b=p.LoadBoard(sys.argv[1])
path(b,'DAC_PSAVE_N',[(46.04,42.1),(46.69,42.75),(52.45,42.75),(55.7,46.0),(59.45,46.0),(63.75,41.7),(63.75,39.8)],'B.Cu')
finish(b,sys.argv[2],drc=False)
