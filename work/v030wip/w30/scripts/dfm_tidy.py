# Hand tidy-up after dfm_dedup.py / dfm_spur.py (text edit, then refill + DRC):
#  - U1.93/U1.94 -> C27/C28 (ADC_3V3A): U1.93's 0.2 mm lead and the C27 branch joined U1.94's diagonal 0.035 mm off
#    its centre line and looked like a doubled Z. U1.93 now goes 45 deg to U1.94's corner (23.0,33.35); the C27 branch
#    leaves from the existing corner (22.0,32.8), which is on its own 45-degree line.
#  - ADC_1V9PLL on In2: the diagonal (30.95,30.15)-(29.35,31.75) and two pieces along it were what was left of the dead
#    spur removed by dfm_spur.py (they closed a small cycle with the via at (31.0,30.2)).
#  - H_OUT: the diagonal to R22.2 overshot its junction (83.5,46.6) by 0.28 mm.
# usage: dfm_tidy.py in.kicad_pcb out.kicad_pcb
import sys,os
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
from pcbedit import Board
b=Board(sys.argv[1])
A='ADC_3V3A'
for a,z in [((23.1,33.2),(22.8,33.2)),((22.95,33.3),(22.9,33.3)),((22.7,33.1),(22.3,33.1)),((23.5,33.6),(23.1,33.2)),((22.3,33.1),(21.2,32.0))]:
    b.remove_segment(A,a,z,'F.Cu')
b.add_path(A,[(23.5,33.6),(23.25,33.35),(23.0,33.35)],'F.Cu',0.2)
b.add_segment(A,(22.0,32.8),(21.2,32.0),'F.Cu',0.15)
# C28 was reached twice, side by side 0.25 mm apart: from U1.94 along x=21.25 and by a 0.05-grid staircase from the In2
# via (20.225,32.0). Now a tree: via -> C27 (as before), via -> C28 in one 45-degree + vertical run, U1.93/94 -> C27.
for a,z in [((22.0,32.8),(22.0,32.1)),((22.0,32.1),(21.25,31.35)),((21.25,31.35),(21.25,30.05)),((21.25,30.05),(21.2,30.0)),
            ((21.2,30.0),(21.225,30.0)),((21.225,30.0),(21.1,30.1)),((21.1,30.1),(21.1,30.15)),((21.1,30.15),(21.05,30.2)),
            ((21.05,30.2),(21.05,30.3)),((21.05,30.3),(21.0,30.35)),((21.0,30.35),(21.0,30.65)),((21.0,30.65),(20.95,30.7)),
            ((20.95,30.7),(20.95,31.15)),((20.95,31.15),(20.7,31.4)),((20.7,31.4),(20.7,31.5)),((20.7,31.5),(20.2,32.0))]:
    b.remove_segment(A,a,z,'F.Cu')
b.add_path(A,[(20.225,32.0),(21.0,31.225),(21.0,30.225),(21.225,30.0)],'F.Cu',0.15)
P='ADC_1V9PLL'
for a,z in [((30.95,30.15),(29.35,31.75)),((30.6,30.45),(30.8,30.25)),((30.8,30.25),(30.95,30.25))]:
    b.remove_segment(P,a,z,'In2.Cu')
b.remove_segment('H_OUT',(85.1,48.2),(83.3,46.4),'F.Cu');b.add_segment('H_OUT',(85.1,48.2),(83.5,46.6),'F.Cu',0.15)
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp)
