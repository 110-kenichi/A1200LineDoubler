# Issue 10: JLC-format BOM / CPL from the manifest and KiCad's position export, plus fab sanity checks.
# usage: r10_fab.py <outputs/amiga_scandoubler>   (expects fab/v030wip/cpl_raw.csv and gerber/*.drl from kicad-cli)
import sys,os,csv,json,re,collections
import pcbnew as p
R=sys.argv[1];F=os.path.join(R,'fab','v030wip');H=os.path.join(R,'hardware')
M=json.load(open(os.path.join(H,'circuit_manifest.json')))['parts']
raw=list(csv.DictReader(open(os.path.join(F,'cpl_raw.csv'))))
refs={r['Ref'] for r in raw};assert refs==set(M),(refs^set(M))
# BOM grouped by value + footprint + LCSC
g=collections.OrderedDict()
for ref in sorted(M,key=lambda s:(re.sub(r'\d','',s),int(re.sub(r'\D','',s) or 0))):
    v=M[ref];k=(v['value'],v['footprint'].split(':')[-1],v.get('lcsc','') or '')
    g.setdefault(k,[]).append(ref)
with open(os.path.join(F,'jlc_bom.csv'),'w',newline='') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #','MPN'])
    for (val,fp,lcsc),rs in g.items():w.writerow([val,','.join(rs),fp,lcsc,M[rs[0]].get('mpn','')])
with open(os.path.join(F,'jlc_cpl.csv'),'w',newline='') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
    for r in raw:w.writerow([r['Ref'],r['PosX']+'mm',r['PosY']+'mm','Top' if r['Side']=='top' else 'Bottom',r['Rot']])
todo=[(','.join(rs),val,fp) for (val,fp,lcsc),rs in g.items() if not lcsc]
with open(os.path.join(F,'parts_to_select.csv'),'w',newline='') as f:
    w=csv.writer(f);w.writerow(['Designators','Value','Footprint','Qty']);[w.writerow([d,v,fp,len(d.split(','))]) for d,v,fp in todo]
# drill sanity: hits in the excellon files vs board
b=p.LoadBoard(os.path.join(H,'amiga_scandoubler_v030wip.kicad_pcb'))
nv=sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks())
npth=sum(1 for f in b.GetFootprints() for q in f.Pads() if q.GetAttribute()==p.PAD_ATTRIB_NPTH)
pth=sum(1 for f in b.GetFootprints() for q in f.Pads() if q.GetAttribute()==p.PAD_ATTRIB_PTH)
def hits(fn):return sum(1 for l in open(fn) if re.match(r'^X-?[\d.]+Y-?[\d.]+',l) or re.match(r'^G85',l))
dp=hits(os.path.join(F,'gerber','amiga_scandoubler_v030wip-PTH.drl'));dn=hits(os.path.join(F,'gerber','amiga_scandoubler_v030wip-NPTH.drl'))
rep=dict(parts=len(M),bom_lines=len(g),lcsc_missing_lines=len(todo),lcsc_missing_parts=sum(len(d.split(',')) for d,_,_ in todo),
         board_vias=nv,board_pth_pads=pth,board_npth_pads=npth,drill_pth_hits=dp,drill_npth_hits=dn,drill_ok=(dp==nv+pth and dn==npth))
json.dump(rep,open(os.path.join(F,'fab_check.json'),'w'),indent=1);print(rep)
