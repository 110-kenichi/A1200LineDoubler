# Issue 6 / step 3 (text): clear U3's sides for the DAC fan.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbedit as E
b=E.Board(sys.argv[1])
def segs(net,pts,layer='F.Cu'):
    for a,z in zip(pts,pts[1:]):b.remove_segment(net,a,z,layer=layer)
# PSAVE: F.Cu hop to R44 and its via (B.Cu stays continuous through (63.75,39.8))
segs('DAC_PSAVE_N',[(63.75,39.8),(63.95,40.0),(64.675,40.0)]);b.remove_via('DAC_PSAVE_N',(63.75,39.8))
# R10 (RSET) west part and its GND chain up to the pin39/40 GND via
segs('DAC_RSET',[(76.2,34.85),(76.05,34.7),(74.6,34.7),(73.95,35.35),(73.9,35.35),(73.8,35.45),(73.7,35.45),(73.65,35.5),(73.675,35.5)])
segs('GND',[(75.325,35.5),(75.4,35.6),(75.4,35.65),(75.45,35.7),(75.45,35.8),(75.5,35.85),(75.5,36.15),(75.55,36.2),(75.55,36.65)])
# U3 pins 1/2 GND via on the left (G0's column)
segs('GND',[(69.838,39.25),(68.65,39.25),(68.638,39.25)]);b.remove_via('GND',(68.638,39.25))
segs('GND',[(69.838,39.75),(69.75,39.65),(69.7,39.65),(69.65,39.6),(69.55,39.6),(69.5,39.55),(69.45,39.55),(69.35,39.45),(69.2,39.45),(69.15,39.4),(68.8,39.4),(68.65,39.25)])
# U3 bottom: pin13 -> C44 and via, pins14/15 -> via, C44 GND
segs('DAC_3V3',[(71.25,46.163),(71.15,46.25),(71.15,46.3),(71.1,46.35),(71.1,46.45),(71.05,46.5),(71.05,46.85),(71.0,46.9),(71.0,47.7),(70.2,48.5),(70.225,48.5)])
segs('DAC_3V3',[(70.225,48.5),(69.6,48.5),(69.4,48.3),(69.425,48.3)]);b.remove_via('DAC_3V3',(69.425,48.3))
segs('GND',[(71.75,46.163),(71.85,46.25),(71.85,46.3),(71.9,46.35),(71.9,46.45),(71.95,46.5),(71.95,46.85),(72.0,46.9),(72.0,47.7),(72.6,48.3)])
segs('GND',[(72.25,46.163),(72.25,47.95),(72.6,48.3)]);segs('GND',[(72.6,48.3),(72.575,48.3)]);segs('GND',[(71.775,48.5),(72.4,48.5),(72.6,48.3)])
b.remove_via('GND',(72.575,48.3))
# DAC_COMP: C42 side and its via / B.Cu tail
segs('DAC_COMP',[(75.725,48.5),(75.1,48.5),(74.9,48.3),(74.925,48.3)]);b.remove_via('DAC_COMP',(74.925,48.3))
segs('DAC_COMP',[(74.925,48.3),(74.9,45.15),(75.65,44.4)],'B.Cu')
# C42 DAC_3V3 pad to the (78.075,48.3) via (the via stays for FB4)
segs('DAC_3V3',[(77.275,48.5),(77.9,48.5),(78.1,48.3)])
# stray In2 stub left at the removed (69.425,48.3) via
segs('DAC_3V3',[(69.425,48.3),(69.5,48.4),(69.55,48.4),(69.6,48.45),(69.7,48.45),(69.75,48.5),(70.1,48.5)],'In2.Cu')
segs('DAC_3V3',[(70.1,48.5),(70.15,48.55),(70.8,48.55)],'In2.Cu')   # re-joined from pin13's new via in step 3
# R14's old GND via (the pocket west of U3 is re-used for R14 + C44)
segs('GND',[(67.125,45.9),(68.05,45.9)]);b.remove_via('GND',(68.05,45.9))
b.save(sys.argv[2])
# C42 -> 0402: drop its footprint block as text; identity saved for the pcbnew step
import json,re,pcbnew as p
f=p.LoadBoard(sys.argv[1]).FindFootprintByReference('C42')
json.dump(dict(value=f.GetValue(),path=f.GetPath().AsString(),props=dict(f.GetProperties()),nets={q.GetNumber():q.GetNetname() for q in f.Pads()}),open(sys.argv[2]+'.c42.json','w'))
L=open(sys.argv[2],encoding='utf-8').read().split('\n');out=[];i=0
while i<len(L):
    if L[i].startswith('  (footprint '):
        j=i;d=0
        while True:
            d+=L[j].count('(')-L[j].count(')')
            if d==0 and j>i:break
            j+=1
        if re.search(r'\(fp_text reference "C42"','\n'.join(L[i:j+1])):i=j+1;continue
        out+=L[i:j+1];i=j+1;continue
    out.append(L[i]);i+=1
open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(out))
