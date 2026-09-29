# Issue 6 / step 1 (pcbnew): REF_27M via (40.2,34) -> B.Cu under the left pad row -> y=41 channel under the EP -> inner via (53.96,41.9) -> U2.11
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import path,via,finish
b=p.LoadBoard(sys.argv[1]);N='REF_27M'
path(b,N,[(39.325,34.0),(40.2,34.0)]);via(b,N,(40.2,34.0))
path(b,N,[(40.2,34.0),(40.2,34.6),(44.9,39.3),(44.9,40.3),(45.6,41.0),(53.06,41.0),(53.96,41.9)],'B.Cu')
via(b,N,(53.96,41.9));path(b,N,[(53.96,41.9),(54.26,42.2),(54.95,42.2)])
finish(b,sys.argv[2],drc=len(sys.argv)<4)
