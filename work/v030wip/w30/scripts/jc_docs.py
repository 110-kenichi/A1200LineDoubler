# J1/J2 -> HYC06-HDR15B-060, step 5: schematic (04_connectors), netlist and manifest follow the board.
import os,json,re
H=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../../../outputs/amiga_scandoubler/hardware')
REP=[('Amiga:DE15_Conec_33DSMT1-E15SNCT','Amiga:DE15_HOAUC_HYC06-HDR15B-060'),('33DSMT1-E15SNCT','HYC06-HDR15B-060'),('C3146802','C711364')]
for fn in ('04_connectors.kicad_sch','amiga_scandoubler.net'):
    p=os.path.join(H,fn);s=open(p,encoding='utf-8').read();n=0
    for a,b in REP:n+=s.count(a);s=s.replace(a,b)
    open(p,'w',encoding='utf-8').write(s);print(fn,n)
p=os.path.join(H,'circuit_manifest.json');s=open(p,encoding='utf-8').read()
note=('HOAUC HYC06-HDR15B-060 (LCSC C711364, JLC extended, stock 2230 on 2026-09-29): 3-row HD-15 female, right angle, THT. '
      'Replaces CONEC 33DSMT1-E15SNCT (LCSC stock 0, 0.76 mm SMD). Pin rows 3.08/5.06/7.04 mm from the PCB edge, body 8.9 mm onto the board. '
      'Must stay a 3-row DE-15 (CLAUDE.md).')
s=re.sub(r'"notes": "LCSC stock 0 at selection \(2026-09-29\): DNP at JLCPCB[^"]*"','"notes": '+json.dumps(note),s)
for a,b in REP:s=s.replace(a,b)
json.loads(s);open(p,'w',encoding='utf-8').write(s);print('manifest ok',s.count('HYC06-HDR15B-060'))
