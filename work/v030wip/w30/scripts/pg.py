import sys;sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'../tools'))
import pcbnew as p;from pcbk7 import *
b=p.LoadBoard(sys.argv[1])
path(b,'POWER_GOOD',[(45.05,44.6),(45.89,44.6),(46.04,44.45)]);via(b,'POWER_GOOD',(46.04,44.45))
path(b,'POWER_GOOD',[(46.04,44.45),(46.25,44.65),(52.7,44.65),(59.075,51.025),(59.075,64.6),(60.175,65.7)],'B.Cu')
finish(b,sys.argv[2])
