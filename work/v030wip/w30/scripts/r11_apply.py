# Write the selected LCSC numbers / MPNs (parts_selection.json) into circuit_manifest.json and the schematic symbols
# (properties "MPN" and "LCSC"). Lines whose stock is short or which need a design decision are left untouched.
import sys,os,json,re,glob
R=sys.argv[1];H=os.path.join(R,'hardware');SKIP=set(sys.argv[2].split(',')) if len(sys.argv)>2 else set()
sel=json.load(open(os.path.join(R,'fab','v030wip','parts_selection.json')))
mf=os.path.join(H,'circuit_manifest.json');M=json.load(open(mf));upd={}
for r in sel:
    c=r['chosen']
    if not c or r['stock_short'] or any(x in SKIP for x in r['refs']):continue
    for ref in r['refs']:
        M['parts'][ref]['lcsc']=c['lcsc'];M['parts'][ref]['mpn']=c['mpn'];upd[ref]=(c['mpn'],c['lcsc'])
json.dump(M,open(mf,'w'),indent=2,ensure_ascii=False)
n=0
for sf in sorted(glob.glob(os.path.join(H,'0*_*.kicad_sch'))):
    L=open(sf).read().split('\n');cur=None
    for i,l in enumerate(L):
        m=re.match(r'\(property "Reference" "([^"]+)"',l)
        if m:cur=m.group(1)
        if cur in upd:
            if l.startswith('(property "MPN" '):L[i]=re.sub(r'^\(property "MPN" "[^"]*"','(property "MPN" "%s"'%upd[cur][0],l)
            elif l.startswith('(property "LCSC" '):L[i]=re.sub(r'^\(property "LCSC" "[^"]*"','(property "LCSC" "%s"'%upd[cur][1],l);n+=1;cur=None
    open(sf,'w').write('\n'.join(L))
print('manifest refs updated',len(upd),'schematic symbols updated',n)
# netlist file: comp blocks carry the same MPN/LCSC properties
nf=os.path.join(H,'amiga_scandoubler.net');N=open(nf).read()
def fix(m):
    blk=m.group(0);ref=re.search(r'\(comp \(ref "([^"]+)"\)',blk).group(1)
    if ref not in upd:return blk
    mpn,lc=upd[ref]
    blk=re.sub(r'\(field \(name "MPN"\) "[^"]*"\)','(field (name "MPN") "%s")'%mpn,blk)
    blk=re.sub(r'\(property \(name "MPN"\) \(value "[^"]*"\)\)','(property (name "MPN") (value "%s"))'%mpn,blk)
    return re.sub(r'\(property \(name "LCSC"\) \(value "[^"]*"\)\)','(property (name "LCSC") (value "%s"))'%lc,blk)
N=re.sub(r'    \(comp \(ref "[^"]+"\).*?\(tstamps "[^"]*"\)\)',fix,N,flags=re.S)
open(nf,'w').write(N);print('netlist comps with LCSC',len(re.findall(r'\(property \(name "LCSC"\) \(value "C\d+"\)\)',N)))
