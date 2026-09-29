# Review #2 (pcbnew): same In2 links re-drawn so each crosses GIN_1 once, at an angle, instead of running under it.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import path,finish
b=p.LoadBoard(sys.argv[1])
path(b,'ADC_3V3A',[(15.75,44.05),(15.75,42.15),(17.85,42.15),(18.05,41.95),(18.05,40.05)],'In2.Cu',w=0.4)
path(b,'ADC_1V9A',[(15.0,41.775),(13.925,41.775),(13.925,47.5)],'In2.Cu',w=0.4)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
