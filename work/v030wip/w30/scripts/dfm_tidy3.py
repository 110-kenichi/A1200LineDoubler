# Hand tidy-up 3, after dfm_planeloop.py / dfm_smooth.py / dfm_dedup.py (text edit, then refill + DRC). Spots the
# smoother cannot reach because a T-junction pins them:
#  - GND U1.77/U1.79 -> via (32.0,32.95): 0.05-grid steps where the two leads met. Now U1.79 runs along y=33.3 to
#    U1.77's corner (31.5,33.3) and U1.77 goes 45 deg into the via.
#  - GND x~26.9, y 43.25-49.6: a vertical line with two 0.05 mm side steps and the branch to (28.0,48.8) landing off its
#    centre. One 45-degree step at the branch point (26.95,48.0) now.
#  - ADC_3V3A U1.13/U1.14: U1.14's line (y=42.5) continued 0.05 mm lower (y=42.55) after U1.13 joined. Now one line at
#    y=42.5 to (15.5,42.5), then 45 deg to (14.75,43.25) as before; two left-over stubs at (17.8,42.5) removed.
#  - DAC_3V3 FB4.2 -> via (78.075,48.3) and on to C47.1: 0.05-grid staircases. Now FB4.2 -> 45 deg -> x=77.55 ->
#    45 deg -> (77.7,48.7); via -> 45 deg -> y=48.5 into C47.1.
#  - GND U2 corner (pins at (53.8,37.05) and (54.95,38.2) -> EP corner (53.35,38.65)): after smoothing the two leads ran
#    as parallel 45-degree lines 0.28 mm apart. Now the right-hand lead runs along y=38.2 to the other lead's corner.
# usage: dfm_tidy3.py in.kicad_pcb out.kicad_pcb
import sys,os
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
from pcbedit import Board
b=Board(sys.argv[1])
def rm(net,pairs,L='F.Cu'):
    for a,z in pairs:b.remove_segment(net,a,z,L,dup_ok=True)
rm('GND',[((31.5,34.35),(31.5,33.35)),((31.5,33.35),(31.7,33.15)),((31.75,33.1),(31.6,33.25)),((31.6,33.25),(31.35,33.25)),
          ((31.35,33.25),(31.3,33.3)),((31.3,33.3),(30.55,33.3)),((31.85,33.05),(31.8,33.1)),((31.9,33.05),(31.85,33.05)),
          ((31.8,33.1),(31.75,33.1)),((31.8,33.15),(32.0,32.95))])
b.add_path('GND',[(31.5,34.35),(31.5,33.3),(31.85,32.95),(32.0,32.95)],'F.Cu',0.2)
b.add_path('GND',[(30.55,33.3),(31.5,33.3)],'F.Cu',0.15)
rm('GND',[((26.85,46.5),(26.9,46.55)),((26.9,46.55),(26.9,47.95)),((26.9,47.95),(26.95,48.0)),((26.85,43.25),(26.85,46.5)),
          ((27.2,48.0),(26.9,48.0))])
b.add_path('GND',[(26.85,43.25),(26.85,47.9),(26.95,48.0)],'F.Cu',0.15)
b.add_path('GND',[(27.2,48.0),(26.95,48.0)],'F.Cu',0.2)
rm('ADC_3V3A',[((18.35,42.5),(16.85,42.5)),((16.85,42.5),(16.8,42.55)),((16.8,42.55),(15.45,42.55)),((15.45,42.55),(14.75,43.25)),
               ((17.85,42.5),(17.8,42.5)),((17.8,42.5),(17.75,42.55))])
b.add_path('ADC_3V3A',[(18.35,42.5),(15.5,42.5),(14.75,43.25)],'F.Cu',0.15)
rm('DAC_3V3',[((77.2875,50.5),(77.4,50.4)),((77.4,50.4),(77.4,50.35)),((77.4,50.35),(77.45,50.3)),((77.45,50.3),(77.45,50.2)),
              ((77.45,50.2),(77.5,50.15)),((77.5,50.15),(77.55,50.1)),((77.55,50.1),(77.55,49.2)),((77.55,49.2),(77.7,49.05)),
              ((77.7,49.05),(77.7,48.7)),((78.3,48.5),(78.1,48.3)),((78.45,48.5),(78.3,48.5)),((78.7,48.75),(78.45,48.5)),
              ((78.75,48.75),(78.7,48.75)),((78.9,48.9),(78.75,48.75))])
b.add_path('DAC_3V3',[(77.2875,50.5),(77.55,50.2375),(77.55,48.85),(77.7,48.7)],'F.Cu',0.15)
b.add_path('DAC_3V3',[(78.1,48.3),(78.3,48.5),(78.9,48.5)],'F.Cu',0.15)
rm('GND',[((54.2,38.2),(53.75,38.65)),((53.75,38.65),(53.35,38.65)),((54.95,38.2),(54.2,38.2))])
b.add_path('GND',[(54.95,38.2),(53.8,38.2)],'F.Cu',0.15)
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp)
