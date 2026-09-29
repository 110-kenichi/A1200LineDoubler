# Issue 8 (pcbnew): connect the 7 remaining analog inputs (and re-route the lines opened in p8_rm.py).
# Routes in p8_routes.json were produced by the A* router (router7) in this order:
#   RIN_3, RIN_2, RIN_1 (from vias placed west of pins 9-11), GIN_1 (B.Cu, BIN corridor x15.3-18.7/y43-53 reserved),
#   BIN_2, BIN_1, BIN_3, SOGIN_2, GIN_3, GIN_4.
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import path,via,finish
b=p.LoadBoard(sys.argv[1]);here=os.path.dirname(os.path.abspath(__file__))
# In2 moves (make room for the RIN vias and the GIN_1 B.Cu)
path(b,'ADC_3V3A',[(15.75,42.4),(17.85,42.4),(18.05,42.2),(18.05,40.05)],'In2.Cu',w=0.4)
path(b,'ADC_1V9A',[(15.0,41.775),(14.4,42.375),(13.925,42.85),(13.925,47.5)],'In2.Cu',w=0.4)
# RIN escape vias west of U1 pins 9/10/11
path(b,'RIN_3',[(17.6,40.0),(17.2,40.0),(16.95,39.75)]);via(b,'RIN_3',(16.95,39.75))
path(b,'RIN_2',[(17.6,40.5),(17.05,40.5),(16.95,40.6)]);via(b,'RIN_2',(16.95,40.6))
path(b,'RIN_1',[(17.6,41.0),(17.35,41.0),(16.95,41.4),(16.95,41.45)]);via(b,'RIN_1',(16.95,41.45))
for r in json.load(open(os.path.join(here,'p8_routes.json'))):
    for L,pts in r['segments']:
        pts=[tuple(q) for q in pts]
        if len(pts)>1:path(b,r['net'],pts,L)
    for v in r['vias']:via(b,r['net'],tuple(v))
# In2 3V3 plane: drop isolated fill islands (the new In2 lines cut a few small unconnected pieces)
for z in b.Zones():
    if z.GetNetname()=='3V3':z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
