# JLC DFM (solder mask opening exposing trace, danger 0.05 mm): U1.85 -> ADC_1V9PLL via (27.8,36.0) ran through the
# 0.2 mm gap between U1.84 and U1.85. Step 1 (text): remove the gap-running pieces; step 2 (pcbnew): pad 85 goes
# straight off its tip to the via like pad 84 does. usage: dfm_u1pll.py in.kicad_pcb out.kicad_pcb
import sys,os
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
from pcbedit import Board
N='ADC_1V9PLL'
RM=[((27.5,34.35),(27.6,34.45)),((27.6,34.45),(27.6,34.5)),((27.6,34.5),(27.65,34.55)),((27.65,34.55),(27.65,34.65)),
    ((27.65,34.65),(27.7,34.7)),((27.7,34.7),(27.7,35.05)),((27.7,35.05),(27.75,35.1)),((27.75,35.1),(27.75,35.95)),
    ((27.75,35.95),(27.8,36.0)),((27.5,34.35),(27.8,34.65)),((27.8,34.65),(27.8,34.75)),((27.8,34.75),(28.0,34.95)),
    ((28.0,34.95),(28.0,35.35))]   # the last one only duplicated part of pad 84's own stub
b=Board(sys.argv[1])
for a,z in RM:b.remove_segment(N,a,z,'F.Cu')
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import path,finish
B=p.LoadBoard(tmp)
path(B,N,[(27.5,34.35),(27.5,35.7),(27.8,36.0)],'F.Cu',w=0.15)
finish(B,sys.argv[2])
os.remove(tmp)
