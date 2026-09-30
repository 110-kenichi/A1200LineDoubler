# Replace Y1 (ECS-3225MVLC-270-CN-TR, LCSC stock 4) by YXC OT2EL4C4JI-111OLP-27M (LCSC C5203549):
# same 3225 4-pad land, pin 1 tri-state (high/float = enable), 2 GND, 3 OUT, 4 VDD, 1.8-3.3 V CMOS (datasheet checked).
# Updates manifest, schematic symbol properties, netlist comp and the board footprint's Value text. Footprint unchanged.
import sys,os,re,json,glob
R=sys.argv[1];H=os.path.join(R,'hardware')
VAL='27MHz OT2EL4C4JI-111OLP-27M';MPN='OT2EL4C4JI-111OLP-27M';LCSC='C5203549'
mf=os.path.join(H,'circuit_manifest.json');M=json.load(open(mf))
M['parts']['Y1'].update(value=VAL,mpn=MPN,lcsc=LCSC,notes='YXC YSO110TR series; replaces ECS-3225MVLC-270-CN-TR (LCSC stock 4)')
json.dump(M,open(mf,'w'),indent=2,ensure_ascii=False)
for sf in glob.glob(os.path.join(H,'0*_*.kicad_sch')):
    L=open(sf).read().split('\n');cur=None;ch=False
    for i,l in enumerate(L):
        m=re.match(r'\(property "Reference" "([^"]+)"',l)
        if m:cur=m.group(1)
        if cur=='Y1':
            for k,v in (('Value',VAL),('MPN',MPN),('LCSC',LCSC)):
                if l.startswith('(property "%s" '%k):L[i]=re.sub(r'^\(property "%s" "[^"]*"'%k,'(property "%s" "%s"'%(k,v),l);ch=True
            if l.startswith('(property "LCSC" '):cur=None
        m=re.match(r'\(path "[^"]*" \(reference "Y1"\) \(unit 1\) \(value "[^"]*"\)',l)
        if m:L[i]=re.sub(r'\(value "[^"]*"\)','(value "%s")'%VAL,l);ch=True
    if ch:open(sf,'w').write('\n'.join(L));print('schematic',os.path.basename(sf))
nf=os.path.join(H,'amiga_scandoubler.net');N=open(nf).read()
def fix(m):
    b=m.group(0)
    b=re.sub(r'\(value "[^"]*"\)','(value "%s")'%VAL,b,count=1)
    b=re.sub(r'\(field \(name "MPN"\) "[^"]*"\)','(field (name "MPN") "%s")'%MPN,b)
    b=re.sub(r'\(property \(name "MPN"\) \(value "[^"]*"\)\)','(property (name "MPN") (value "%s"))'%MPN,b)
    return re.sub(r'\(property \(name "LCSC"\) \(value "[^"]*"\)\)','(property (name "LCSC") (value "%s"))'%LCSC,b)
N=re.sub(r'    \(comp \(ref "Y1"\).*?\(tstamps "[^"]*"\)\)',fix,N,flags=re.S);open(nf,'w').write(N)
if len(sys.argv)>3:   # board Value text (pcbnew)
    sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
    import pcbnew as p;from pcbk7 import finish
    b=p.LoadBoard(sys.argv[2]);b.FindFootprintByReference('Y1').SetValue(VAL);finish(b,sys.argv[3])
print('ok')
