# 5V bus under the regulators (y=80, 0.8 mm): the drops from C55/C57/C59 (x=22.45/44.95/66.95) were 0.6 mm, so the
# wider bus stuck out past them at the corners, and the bus ran 0.5 mm beyond the C59 drop to x=67.45 (nothing there).
# Now the drops are 0.8 mm like the bus and the bus ends at x=66.95. Text edit, then refill + DRC.
# Found with tools/cornerscan.py, also fixed here:
#  - GND U3.31: the lead ended 0.008 mm outside the via land (76.9,42.25) and only touched it by copper overlap. Now
#    via centre -> 45 deg -> (77.35,41.8) -> pad; a 0.07 mm left-over piece at (77.4,41.75) removed.
#  - GND U1.15: its vertical (x=19.4) stopped 0.1 mm short of U1.12's line (y=41.45), touching it only by copper.
#    Now it ends on that line.
# usage: dfm_corner.py in.kicad_pcb out.kicad_pcb
import sys,os
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
from pcbedit import Board
b=Board(sys.argv[1]);N='5V'
b.remove_segment(N,(22.45,80.0),(67.45,80.0),'F.Cu');b.add_segment(N,(22.45,80.0),(66.95,80.0),'F.Cu',0.8)
for x in (22.45,44.95,66.95):
    b.remove_segment(N,(x,72.75),(x,80.0),'F.Cu');b.add_segment(N,(x,72.75),(x,80.0),'F.Cu',0.8)
for a,z in [((77.1,42.05),(77.1,41.8)),((77.1,41.8),(78.1,41.8)),((77.4,41.75),(77.35,41.8))]:
    b.remove_segment('GND',a,z,'F.Cu')
b.add_path('GND',[(76.9,42.25),(77.35,41.8),(78.1,41.8)],'F.Cu',0.15)
b.remove_segment('GND',(19.4,42.95),(19.4,41.55),'F.Cu');b.add_segment('GND',(19.4,42.95),(19.4,41.45),'F.Cu',0.15)
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp)
