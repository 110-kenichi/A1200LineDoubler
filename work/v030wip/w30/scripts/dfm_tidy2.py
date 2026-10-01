# Hand tidy-up 2 (text edit, then refill + DRC):
#  - GND between C27 and U1.90-92: U1.90 and U1.91 ran in two 0.2 mm 45-degree lines 0.28 mm apart into a 0.05-grid
#    staircase before the via (24.0,32.95), next to C27.2's line (0.25 mm away). Now U1.91 goes up and 45 deg into the
#    via, U1.90 joins U1.91's corner (24.5,33.35) like U1.93 joins U1.94; C27.2 enters the via centre horizontally.
#  - C21: its 3V3 via (28.35,54.2) sat 0.26 mm from its GND via (27.6,53.9) and looked stacked; moved to (28.6,54.1)
#    (gap 0.47 mm), the 3V3 lead follows.
#  - U4.5 -> C51.1 (3V3): two lines 0.016 mm apart (U4.5 -> C51 at y=59.0, via (19.5,58.775) -> C51 slanted). Now one
#    line at y=59.0, U4.5 -> via (end inside the via land) -> C51.
# usage: dfm_tidy2.py in.kicad_pcb out.kicad_pcb
import sys,os,re
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
from pcbedit import Board
b=Board(sys.argv[1])
G='GND'
for a,z in [((24.0,32.95),(24.1,33.05)),((24.1,33.05),(24.1,33.1)),((24.1,33.1),(24.15,33.15)),((24.5,33.5),(24.15,33.15)),
            ((24.5,34.35),(24.5,33.5)),((24.55,33.15),(24.15,33.15)),((25.0,33.6),(24.55,33.15)),((23.05,32.4),(23.95,33.3))]:
    b.remove_segment(G,a,z,'F.Cu')
b.add_path(G,[(24.5,34.35),(24.5,33.35),(24.1,32.95),(24.0,32.95)],'F.Cu',0.2)
b.add_path(G,[(25.0,33.6),(24.75,33.35),(24.5,33.35)],'F.Cu',0.2)
b.add_path(G,[(23.05,32.4),(23.6,32.95),(24.0,32.95)],'F.Cu',0.15)
P='3V3'
for a,z in [((28.45,51.725),(28.45,53.8)),((28.45,53.8),(28.35,53.9)),((28.35,53.9),(28.35,54.2))]:
    b.remove_segment(P,a,z,'F.Cu')
b.add_path(P,[(28.45,51.725),(28.45,53.95),(28.6,54.1)],'F.Cu',0.15)
for a,z in [((18.1375,59.0),(20.3,59.0)),((20.3,59.0),(20.5,58.8)),((19.5,58.8),(19.5,58.775)),((20.5,58.8),(20.5,58.775)),((20.5,58.775),(19.5,58.8))]:
    b.remove_segment(P,a,z,'F.Cu')
b.add_path(P,[(18.1375,59.0),(19.5,59.0)],'F.Cu',0.15);b.add_path(P,[(19.5,59.0),(20.5,59.0)],'F.Cu',0.15)
n=[i for i,l in enumerate(b.lines) if re.match(r'\s*\(via \(at 28\.35 54\.2\) ',l)];assert len(n)==1
b.lines[n[0]]=b.lines[n[0]].replace('(at 28.35 54.2)','(at 28.6 54.1)')
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp)
