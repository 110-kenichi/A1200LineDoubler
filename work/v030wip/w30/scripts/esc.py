import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board('/tmp/r/d3.kicad_pcb')
# move C18/C7 GND via west
for a,c in [((16.274999,47.5),(16.25,48.5)),((16.25,48.5),(16.274999,48.5)),((16.274999,49.5),(16.25,48.5))]:
    b.remove_segment('GND',a,c)
E.remove_via(b,'GND',(16.274999,48.5))
b.add_path('GND',[(16.275,47.5),(15.95,47.825),(15.95,49.175),(16.275,49.5)])
b.add_via('GND',(15.95,48.5),size=.6,drill=.3)
b.remove_segment('GND',(17.1,46.3),(17.1,46.55));E.remove_via(b,'GND',(17.1,46.55))
b.add_segment('GND',(17.1,46.3),(17.15,46.45));b.add_via('GND',(17.15,46.45),size=.5,drill=.3)
W=.127
b.add_path('ADC_VS',[(18.35,47.0),(17.0,47.0),(17.0,48.25),(16.75,48.5)],width=W);b.add_via('ADC_VS',(16.75,48.5))
b.add_path('ADC_HS',[(18.35,47.5),(17.33,47.5),(17.33,48.3),(17.5,48.47),(17.5,48.9)],width=W);b.add_via('ADC_HS',(17.5,48.9))
b.save('/tmp/r/d4.kicad_pcb')
