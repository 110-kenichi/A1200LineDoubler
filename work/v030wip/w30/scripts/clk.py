import sys;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
b=E.Board(sys.argv[1])
for a,c in [((22.3,50.85),(28.75,44.4)),((28.75,44.4),(41.45,44.4)),((41.45,44.4),(41.9,43.95))]:b.remove_segment('ADC_CLK',a,c)
b.add_path('ADC_CLK',[(22.3,50.85),(28.4,44.75),(41.1,44.75),(41.9,43.95)],layer='B.Cu')
b.save(sys.argv[2])
