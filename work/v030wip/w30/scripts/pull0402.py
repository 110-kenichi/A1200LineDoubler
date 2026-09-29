# Replace R37-R40 (0603) by R_0402_1005Metric at planned positions, then add their F.Cu leads and vias.
# usage: swap0402.py <src.kicad_pcb> <plan.json> <dst.kicad_pcb>
import sys,json,re,os;sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in __file__ else os.path.dirname(os.path.abspath(__file__)))
import pcbnew as p
from pcbk7 import V,MM,seg,via,finish
src,planf,dst=sys.argv[1:4];plan={r['ref']:r for r in json.load(open(planf))}
FPLIB=os.environ.get('FPLIB','/usr/share/kicad/footprints/Resistor_SMD.pretty')
# 1) remember old footprint identity (pcbnew, read-only)
b=p.LoadBoard(src);old={}
for ref in plan:
    f=b.FindFootprintByReference(ref)
    old[ref]=dict(value=f.GetValue(),path=f.GetPath().AsString(),props=dict(f.GetProperties()),nets={q.GetNumber():q.GetNetname() for q in f.Pads()})
del b
# 2) drop the old footprint blocks as text (pcbnew Remove() is unsafe in KiCad 7.0.11)
L=open(src,encoding='utf-8').read().split('\n');out=[];i=0
while i<len(L):
    if L[i].startswith('  (footprint '):
        j=i;d=0
        while True:
            d+=L[j].count('(')-L[j].count(')')
            if d==0 and j>i:break
            j+=1
        m=re.search(r'\(fp_text reference "([^"]+)"','\n'.join(L[i:j+1]))
        if m and m.group(1) in plan:i=j+1;continue
        out+=L[i:j+1];i=j+1;continue
    out.append(L[i]);i+=1
tmp=dst+'.tmp.kicad_pcb';open(tmp,'w',encoding='utf-8').write('\n'.join(out))
# 3) add new 0402 footprints and their connections
b=p.LoadBoard(tmp);os.remove(tmp)
for ref,r in plan.items():
    f=p.FootprintLoad(FPLIB,'R_0402_1005Metric');f.SetParent(b)
    f.SetReference(ref);f.SetValue(old[ref]['value']);f.SetPath(p.KIID_PATH(old[ref]['path']))
    for k,v in old[ref]['props'].items():f.SetProperty(k,v)
    b.Add(f)
    f.SetPosition(V(*r['center']))
    # pad1 carries the signal: choose orientation so pad1 lands on sig_pad
    for ang in (0,90,180,270):
        f.SetOrientationDegrees(ang)
        q1=[q for q in f.Pads() if q.GetNumber()=='1'][0]
        if abs(p.ToMM(q1.GetPosition().x)-r['sig_pad'][0])<1e-3 and abs(p.ToMM(q1.GetPosition().y)-r['sig_pad'][1])<1e-3:break
    else:raise SystemExit(ref+': orientation not found')
    for q in f.Pads():q.SetNet(b.FindNet(old[ref]['nets'][q.GetNumber()]))
    sig=old[ref]['nets']['1'];oth=old[ref]['nets']['2']
    fr=f.Reference();fr.SetTextSize(p.VECTOR2I(MM(0.5),MM(0.5)));fr.SetTextThickness(MM(0.08));fr.SetTextAngleDegrees(-f.GetOrientationDegrees())
    if 'ref_at' in r:fr.SetPosition(V(*r['ref_at']))
    seg(b,sig,tuple(r['sig_pad']),tuple(r['sig_via']));via(b,sig,tuple(r['sig_via']))
    seg(b,oth,tuple(r['other_pad']),tuple(r['other_via']),w=0.25)
    if not r.get('other_via_shared'):via(b,oth,tuple(r['other_via']),0.6)
finish(b,dst)
