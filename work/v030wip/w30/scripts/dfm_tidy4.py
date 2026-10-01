# JLC DFM 2026-10-01 "Solder mask opening exposing trace" (danger 0.07 mm): the ADC_3V3A line In2 via (20.225,32.0) ->
# C28.1 (dfm_tidy.py) cut past the top-left corner of C27.1's opening at 0.071 mm. Now it goes straight up from the via,
# 45 deg, then along y=30.0 into C28.1 - 0.475 mm clear of C27.1. Text edit, then refill + DRC.
# usage: dfm_tidy4.py in.kicad_pcb out.kicad_pcb
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from pcbedit import Board
b=Board(sys.argv[1]);N='ADC_3V3A'
for a,z in [((20.225,32.0),(21.0,31.225)),((21.0,31.225),(21.0,30.225)),((21.0,30.225),(21.225,30.0))]:b.remove_segment(N,a,z,'F.Cu')
b.add_path(N,[(20.225,32.0),(20.225,30.25),(20.475,30.0),(21.225,30.0)],'F.Cu',0.15)
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');b.save(tmp)
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp)
