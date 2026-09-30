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
# JLC placement corrections (tools/jlc_rotcheck.py vs the EasyEDA footprints JLC places with):
#   rotation += R; position -= placement_error (board frame, y down; the CPL y axis is up).
CORR={c['ref']:c for c in json.load(open(os.path.join(F,'jlc_rotation_check.json'))) if c.get('max_pad_err_mm',99)<0.3} if os.path.exists(os.path.join(F,'jlc_rotation_check.json')) else {}
#   (J1/J2: EasyEDA numbers the two board locks 16/17, so the automatic match is invalid (11.97 mm) -> no correction; they are DNP anyway)
DNP={'J1','J2'}   # hand-soldered by the user (jlc_*_dnp_J1J2.csv)
rows=[]
for r in raw:
    c=CORR.get(r['Ref'],{});R=c.get('R',0);ex,ey=c.get('placement_error_mm',[0,0])
    x=float(r['PosX'])-ex;y=float(r['PosY'])+ey;rot=(float(r['Rot'])+R)%360
    rows.append([r['Ref'],'%.6fmm'%x,'%.6fmm'%y,'Top' if r['Side']=='top' else 'Bottom','%.6f'%rot])
for fn,skip in (('jlc_cpl.csv',set()),('jlc_cpl_dnp_J1J2.csv',DNP)):
    with open(os.path.join(F,fn),'w',newline='') as f:
        w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation']);[w.writerow(r) for r in rows if r[0] not in skip]
with open(os.path.join(F,'jlc_bom_dnp_J1J2.csv'),'w',newline='') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #','MPN'])
    for (val,fp,lcsc),rs in g.items():
        d=[x for x in rs if x not in DNP]
        if d:w.writerow([val,','.join(d),fp,lcsc,M[rs[0]].get('mpn','')])
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
