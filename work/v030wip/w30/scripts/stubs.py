import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board('/tmp/r/d2.kicad_pcb')
b.add_path('ADC_VS',[(53.4,46.95),(53.4,46.16),(53.2,45.96)]);b.add_via('ADC_VS',(53.2,45.96))
b.add_path('ADC_HS',[(53.0,46.95),(53.0,47.85),(53.2,48.05)]);b.add_via('ADC_HS',(53.2,48.05))
b.save('/tmp/r/d3.kicad_pcb')
