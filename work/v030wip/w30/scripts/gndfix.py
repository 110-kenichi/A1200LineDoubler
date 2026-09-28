import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board('/tmp/r/d1.kicad_pcb')
for a,c in [((17.1,46.35),(16.25,47.2)),((16.25,47.2),(16.25,47.55)),((17.1,46.3),(17.1,47.85)),((17.1,47.85),(16.95,48.0)),((16.95,48.0),(16.95,48.5))]:
    print(b.remove_segment('GND',a,c))
print(E.remove_via(b,'GND',(16.95,48.5)))
b.add_segment('GND',(17.1,46.3),(17.1,46.55));b.add_via('GND',(17.1,46.55),size=.6,drill=.3)
b.save('/tmp/r/d2.kicad_pcb')
