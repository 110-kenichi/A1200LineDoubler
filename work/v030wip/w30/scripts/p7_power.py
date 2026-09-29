# Issue 7 (pcbnew): connect island power pads to their planes / nets.
# - p7_viastub_plan.json: straight F.Cu stub + plane via per pad (found by tools/viastub.py, sequentially)
# - manual links where no via fits (J1.10, J2.7/8) and the separate supply nets (ADC_3V3A, ADC_1V9PLL, DAC_3V3)
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import path,via,finish
b=p.LoadBoard(sys.argv[1])
here=os.path.dirname(os.path.abspath(__file__))
for sc,ref,pin,net,s,v,ex in json.load(open(os.path.join(here,'p7_viastub_plan.json'))):
    s=tuple(s);v=tuple(v)
    if s!=v:path(b,net,[s,v],w=0.25)
    if not ex:via(b,net,v,0.6)
# J1.10 -> J1.5 around the pad ends (J1.5 has its own via)
path(b,'GND',[(7.3,45.8),(7.95,45.8),(7.95,47.32),(7.3,47.32)],w=0.2)
# J2.8 / J2.7: enclosed by H_OUT/R_OUT on the west and the pin 14/3/2 lines on the east -> via on the pad
via(b,'GND',(87.8,42.76),0.55);via(b,'GND',(89.65,45.04),0.55)   # J2.7: east of R_OUT's pad-1 lead end
# ADC_3V3A: C62.1 onto FB1's via
path(b,'ADC_3V3A',[(13.0,27.3),(13.0,28.412)],w=0.25)
# C63.1 (ADC_3V3A) and C66.1 / C67.1 (ADC_1V9PLL): F.Cu links found by the A* router (0.2mm)
path(b,'ADC_3V3A',[(20.225,26.0),(21.0,26.75),(21.0,29.75),(21.225,30.0)],w=0.2)
path(b,'ADC_1V9PLL',[(30.55,28.5),(30.3,28.75),(30.3,29.95)],w=0.2)
path(b,'ADC_1V9PLL',[(27.725,26.0),(27.75,26.025),(27.75,27.55),(28.675,28.475),(28.675,28.5)],w=0.2)
# DAC_3V3: C68.1 to C47.1; C69.1 via -> In2 DAC_3V3 feed
path(b,'DAC_3V3',[(79.05,49.0),(79.05,51.5)],w=0.3)
path(b,'DAC_3V3',[(75.725,52.5),(74.8,52.5)],w=0.25);via(b,'DAC_3V3',(74.8,52.5),0.6)
path(b,'DAC_3V3',[(74.8,52.5),(74.65,51.05)],'In2.Cu',w=0.4)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
