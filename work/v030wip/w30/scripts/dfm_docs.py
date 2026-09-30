# JLC DFM / order follow-up: schematic, netlist and manifest follow the board.
#  - C47/C54/C55/C57/C59 (all C15850): value "10uF 25V" -> one JLC BOM line
#  - J3 footprint Amiga:USB_C_Receptacle_HRO_TYPE-C-31-M-12_Slot0.8 (slots 0.8 mm)
#  - L1-L3: Taiyo Yuden NRS4018T2R2MDGJ (C92959); C7413169 has no EasyEDA footprint, so JLC could not place it.
#    Same land (EasyEDA: 1.2x4.0 mm pads at +-1.4 mm vs ours 1.3x4.0 at +-1.35), footprint unchanged.
import os,re,json,sys
H=sys.argv[1]
CH={**{r:{'Value':'10uF 25V'} for r in ('C47','C54','C55','C57','C59')},
    'J3':{'Footprint':'Amiga:USB_C_Receptacle_HRO_TYPE-C-31-M-12_Slot0.8'},
    **{r:{'MPN':'NRS4018T2R2MDGJ','LCSC':'C92959'} for r in ('L1','L2','L3')}}
n=0
for fn in sorted(os.listdir(H)):
    if not fn.endswith('.kicad_sch'):continue
    L=open(os.path.join(H,fn),encoding='utf-8').read().split('\n');cur=None
    for i,l in enumerate(L):
        m=re.match(r'\(property "Reference" "([^"]+)"',l)
        if m:cur=m.group(1)
        if l.startswith('(symbol (lib_id'):cur=None
        m=re.match(r'\(property "(Value|Footprint|MPN|LCSC)" "([^"]*)"',l)
        if m and cur in CH and m.group(1) in CH[cur]:
            L[i]=l.replace('"%s" "%s"'%(m.group(1),m.group(2)),'"%s" "%s"'%(m.group(1),CH[cur][m.group(1)]),1);n+=1
        m=re.match(r'\(path "[^"]+" \(reference "([^"]+)"\) \(unit 1\) \(value "([^"]*)"\) \(footprint "([^"]*)"\)',l)
        if m and m.group(1) in CH:
            c=CH[m.group(1)]
            if 'Value' in c:L[i]=L[i].replace('(value "%s")'%m.group(2),'(value "%s")'%c['Value'])
            if 'Footprint' in c:L[i]=L[i].replace('(footprint "%s")'%m.group(3),'(footprint "%s")'%c['Footprint'])
    open(os.path.join(H,fn),'w',encoding='utf-8').write('\n'.join(L))
print('schematic properties',n)
p=os.path.join(H,'amiga_scandoubler.net');s=open(p,encoding='utf-8').read()
def comp(m):
    ref=m.group(1);blk=m.group(0);c=CH.get(ref)
    if not c:return blk
    if 'Value' in c:blk=re.sub(r'\(value "[^"]*"\)','(value "%s")'%c['Value'],blk,1)
    if 'Footprint' in c:blk=re.sub(r'\(footprint "[^"]*"\)','(footprint "%s")'%c['Footprint'],blk,1)
    for k in ('MPN','LCSC'):
        if k in c:blk=re.sub(r'\(field \(name "%s"\) "[^"]*"\)'%k,'(field (name "%s") "%s")'%(k,c[k]),blk);blk=re.sub(r'\(property \(name "%s"\) \(value "[^"]*"\)\)'%k,'(property (name "%s") (value "%s"))'%(k,c[k]),blk)
    return blk
s=re.sub(r'\(comp \(ref "([^"]+)"\).*?\(tstamps "[^"]*"\)\)',comp,s,flags=re.S)
open(p,'w',encoding='utf-8').write(s)
p=os.path.join(H,'circuit_manifest.json');J=json.load(open(p,encoding='utf-8'))
for r,c in CH.items():
    m=J['parts'][r]
    if 'Value' in c:m['value']=c['Value']
    if 'Footprint' in c:m['footprint']=c['Footprint'];m['notes']='HRO drawing 2020-12-08 reviewed. Shell slots widened 0.6 -> 0.8 mm (pads 1.2 mm) as in the JLC/EasyEDA footprint of C165948 (JLC DFM flagged 0.6 mm slots).'
    if 'MPN' in c:m['mpn']=c['MPN'];m['lcsc']=c['LCSC'];m['notes']='Taiyo Yuden NRS4018T2R2MDGJ (C92959): 2.2 uH, Isat 3 A, Irated 2.2 A, DCR 42 mOhm, 4.0x4.0x1.8 mm. Replaces TDK VLS4012CX-2R2M-1 (C7413169, no EasyEDA footprint -> not placeable at JLC). Same land.'
json.dump(J,open(p,'w',encoding='utf-8'),indent=2,ensure_ascii=False);print('manifest ok')
