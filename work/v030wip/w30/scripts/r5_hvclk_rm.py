# Issue 5 remainder, step 1 (text): drop the H/V_OUT_RAW stubs, vias and B.Cu starts that sit in the future B-bus corridor.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
segs('H_OUT_RAW',[(67.5,47.825),(67.5,48.4),(67.3,48.6),(67.3,48.625)],'F.Cu');b.remove_via('H_OUT_RAW',(67.3,48.625))
segs('H_OUT_RAW',[(67.3,48.6),(67.3,48.625),(67.4,48.7),(67.45,48.7),(67.5,48.75),(67.6,48.75),(67.65,48.8),(68.0,48.8),(68.05,48.85),(69.15,48.85),(69.2,48.9),(70.25,48.9),(72.5,51.15),(72.55,51.15),(72.65,51.25)],'B.Cu')
segs('V_OUT_RAW',[(66.675,50.0),(66.1,50.0),(65.9,49.8),(65.875,49.8)],'F.Cu');b.remove_via('V_OUT_RAW',(65.875,49.8))
segs('V_OUT_RAW',[(65.9,49.8),(65.875,49.8),(67.7,51.6),(67.8,51.6),(70.45,54.25)],'B.Cu')
# C37's old plane stubs/vias (C37 is re-placed later)
b.remove_segment('3V3',(60.525,47.2),(60.525,48.1),layer='F.Cu');b.remove_via('3V3',(60.525,48.1))
b.remove_segment('GND',(62.075,47.2),(62.075,48.1),layer='F.Cu');b.remove_via('GND',(62.075,48.1))
# R41/R42 old pad2 plane stubs and vias (inside the B-bus corridor; resistors are re-placed later)
segs('3V3',[(68.325,50.0),(68.9,50.0),(69.1,49.8),(69.125,49.8)],'F.Cu');b.remove_via('3V3',(69.125,49.8))
segs('3V3',[(67.5,46.175),(67.5,45.6),(67.3,45.4),(67.3,45.375)],'F.Cu');b.remove_via('3V3',(67.3,45.375))
b.save(sys.argv[2])
