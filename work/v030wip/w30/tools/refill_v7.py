# Refill all zones with KiCad10 and transplant filled polygons (per zone, matched by tstamp/uuid) into the KiCad7-format file
import re,subprocess,sys
src,dst=sys.argv[1],sys.argv[2]
tmp='/tmp/_fill.kicad_pcb'
r=subprocess.run(['/opt/kicad/squashfs-root/bin/python3','-c',f"import pcbnew as p;b=p.LoadBoard('{src}');p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard('{tmp}',b)"],capture_output=True,text=True)
new=open(tmp).read()
def zones_new(t):
    out={}
    for m in re.finditer(r'\n\t\(zone\n',t):
        s=m.start()+1;d=0;i=s
        while True:
            c=t[i]
            if c=='(':d+=1
            elif c==')':
                d-=1
                if d==0:break
            i+=1
        blk=t[s:i+1];u=re.search(r'\(uuid "([^"]+)"\)',blk).group(1)
        polys=[]
        for fm in re.finditer(r'\(filled_polygon\s*\(layer "([^"]+)"\)\s*\(pts(.*?)\)\s*\)',blk,re.S):
            polys.append((fm.group(1),re.findall(r'\(xy [-\d.]+ [-\d.]+\)',fm.group(2))))
        out[u]=polys
    return out
Z=zones_new(new)
old=open(src).read().split('\n');res=[];i=0;cnt={}
while i<len(old):
    l=old[i]
    if l.startswith('  (zone '):
        j=i;d=0
        while True:
            d+=old[j].count('(')-old[j].count(')')
            if d==0 and j>i:break
            j+=1
        blk=old[i:j+1];u=re.search(r'\(tstamp ([0-9a-f-]+)\)',blk[0]).group(1)
        # drop existing filled polygons
        keep=[];k=0
        while k<len(blk)-1:
            if blk[k].strip().startswith('(filled_polygon'):
                d=0
                while True:
                    d+=blk[k].count('(')-blk[k].count(')');k+=1
                    if d==0:break
                continue
            keep.append(blk[k]);k+=1
        for layer,pts in Z.get(u,[]):
            keep.append('    (filled_polygon');keep.append(f'      (layer "{layer}")');keep.append('      (pts')
            keep+=['        '+p for p in pts];keep.append('      )');keep.append('    )')
        keep.append(blk[-1]);res+=keep;cnt[u]=len(Z.get(u,[]));i=j+1;continue
    res.append(l);i+=1
open(dst,'w').write('\n'.join(res));print('zones',cnt)
