import sys,json,re;sys.path.insert(0,'/home/claude/tools')
from pcbedit import Board
from cluster import clusters
NEW={**{48+i:f'ADC_R{i}' for i in range(8)},68:'ADC_G0',69:'ADC_G1',70:'ADC_G2',71:'ADC_G3',72:'ADC_G4',73:'ADC_G5',74:'ADC_G6',75:'ADC_G7',
     76:'ADC_B0',77:'ADC_B1',79:'ADC_B2',80:'ADC_B3',81:'ADC_B4',82:'ADC_B5',83:'ADC_B6',84:'ADC_B7',85:'ADC_HS',86:'ADC_VS'}
json.dump(NEW,open('/tmp/r/newpin.json','w'))
g=json.load(open('gc0.json'));b=Board('c0.kicad_pcb')
# 1 remove bus tracks
buses=[f'ADC_R{i}' for i in range(8)]+[f'ADC_G{i}' for i in range(8)]+['ADC_B0','ADC_B1']
n=0
for net in buses:n+=b.remove_net_layer(net,'F.Cu')
print('removed bus segs',n)
# 2 U2 pad nets
L=b.lines;inU2=False;cnt=0
for i,l in enumerate(L):
    if l.startswith('  (footprint '):inU2='QFN-88_GW1N4' in l
    if inU2:
        m=re.match(r'\s*\(pad "(\d+)" ',l)
        if m and int(m.group(1)) in NEW:
            newnet=NEW[int(m.group(1))];nc=b.nets[newnet]
            L[i+1]=re.sub(r'\(net \d+ "[^"]*"\)',f'(net {nc} "{newnet}")',L[i+1]);cnt+=1
print('U2 pads renetted',cnt)
# 3 C32/C34 clusters
for ref in ['C32','C34']:
    for num,(net,segs,vias) in clusters(g,ref).items():
        for k in segs:s=g['tracks'][k];b.remove_segment(net,tuple(s['a']),tuple(s['b']),s['layer'])
        for j in vias:
            v=g['vias'][j]
            if (round(v['x'],3),round(v['y'],3))==(44.0,37.225):continue  # keep 1V2 via (B.Cu link)
            b.remove_via(net,(v['x'],v['y']))
b.set_fp('C32',43.0,37.35,90 if True else 0)
b.set_fp('R40',43.0,34.3,90);b.set_fp('R37',39.0,31.5,0);b.set_fp('R39',41.0,30.0,0);b.set_fp('C34',37.0,30.0,0)
b.save('c1a.kicad_pcb')
