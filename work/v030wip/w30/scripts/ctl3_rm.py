import sys;sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'../tools'))
import pcbedit as E
b=E.Board(sys.argv[1])
for a,z,L in [((41.45,44.4),(41.9,43.95),'B.Cu'),((41.9,43.95),(43.85,43.95),'F.Cu'),((43.85,43.95),(44.3,44.4),'F.Cu'),((44.3,44.4),(44.3,44.8),'F.Cu'),((44.3,44.8),(44.5,45.0),'F.Cu'),((44.5,45.0),(45.05,45.0),'F.Cu')]:b.remove_segment('ADC_CLK',a,z,layer=L)
b.remove_via('ADC_CLK',(41.9,43.95))
for a,z in [((45.05,45.4),(44.3,45.4)),((44.3,45.4),(43.8,44.9)),((43.8,44.9),(43.8,44.45)),((43.8,44.45),(42.2,44.45)),((42.2,44.45),(41.9,44.75)),((41.9,44.75),(41.0,44.75))]:b.remove_segment('3V3',a,z,layer='F.Cu')
b.remove_segment('GND',(46.2,45.8),(50.0,42.0),layer='F.Cu');b.remove_segment('GND',(45.05,45.8),(46.2,45.8),layer='F.Cu')
b.save(sys.argv[2])
