# J1/J2 -> HOAUC HYC06-HDR15B-060 (THT), step 1 (text edit; BOARD.Remove is unsafe in KiCad 7.0.11 python).
# Removes the old CONEC J1/J2 footprints, their fan-out tracks/vias (signal nets with an end in the connector
# zone) and the old GND stubs/vias of the SMD pads. Footprint path/tstamp are saved for jc_add.py.
import re,sys,json
src,dst,meta=sys.argv[1:4]
L=open(src,encoding='utf-8').read().split('\n')
nets={m.group(2):int(m.group(1)) for l in L for m in [re.match(r'\s*\(net (\d+) "(.*)"\)$',l)] if m}
ZONES={'J1':(lambda x,y:x<11.0 and 26<y<60,['R_IN','G_IN','B_IN','H_IN','V_IN'],lambda x,y:x<10.5 and 26<y<58),
       'J2':(lambda x,y:x>84.0 and 26<y<60,['R_OUT','G_OUT','B_OUT','H_OUT','V_OUT'],lambda x,y:x>86.5 and 26<y<58)}
# V_IN via (11.5,58.4) and H_OUT via (83.3,46.375) become dangling once the new routes land on F.Cu
VZ={'J1':lambda x,y:x<12.0 and 26<y<60,'J2':lambda x,y:x>83.0 and 26<y<60}
info={};out=[];i=0;rm={'seg':0,'via':0}
while i<len(L):
    l=L[i]
    if l.startswith('  (footprint "Amiga:DE15_Conec_33DSMT1-E15SNCT"'):
        j=i;d=0
        while True:
            d+=L[j].count('(')-L[j].count(')')
            if d==0:break
            j+=1
        blk='\n'.join(L[i:j+1]);ref=re.search(r'\(fp_text reference "([^"]+)"',blk).group(1)
        info[ref]=dict(path=re.search(r'\(path "([^"]+)"\)',blk).group(1),tstamp=re.search(r'\(tstamp ([0-9a-f-]+)\)',blk).group(1),
                       at=re.search(r'\n    \(at ([^)]*)\)',blk).group(1))
        i=j+1;continue
    m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net (\d+)\)',l)
    v=re.match(r'\s*\(via \(at ([-\d.]+) ([-\d.]+)\).*\(net (\d+)\)',l)
    kill=False
    for ref,(inz,sig,gz) in ZONES.items():
        ids={nets[n] for n in sig}
        if m:
            a=(float(m.group(1)),float(m.group(2)));b=(float(m.group(3)),float(m.group(4)));n=int(m.group(6))
            if n in ids and (inz(*a) or inz(*b)):kill=True
            if n==nets['GND'] and gz(*a) and gz(*b):kill=True
        if v:
            c=(float(v.group(1)),float(v.group(2)));n=int(v.group(3))
            if (n in ids and (inz(*c) or VZ[ref](*c))) or (n==nets['GND'] and gz(*c)):kill=True
    if kill:rm['seg' if m else 'via']+=1;i+=1;continue
    out.append(l);i+=1
open(dst,'w',encoding='utf-8').write('\n'.join(out))
json.dump(info,open(meta,'w'),indent=1);print(rm,info)
