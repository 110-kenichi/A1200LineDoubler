# Issue 10 follow-up: pick LCSC parts for every BOM line from JLCPCB's live catalogue (stock / price / basic flag).
# Read-only lookups; nothing is ordered. Output: fab/v030wip/parts_selection.json + .csv
import sys,os,json,re,csv,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from jlcsel import search,row,attrs,num
R=sys.argv[1];BOARDS=int(os.environ.get('BOARDS','5'))
M=json.load(open(os.path.join(R,'hardware','circuit_manifest.json')))['parts']
SPEC=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'r11_parts_spec.json')))
groups=collections.OrderedDict()
for ref,p in M.items():groups.setdefault((re.sub(r'\d','',ref),p['value'],p['footprint'].split(':')[-1],p.get('mpn','')),[]).append(ref)
RANK={'basic':0,'preferred':1,'extended':2}
def pick(cands,q,minstock):
    ok=[c for c in cands if c['stock']>=minstock]
    return sorted(ok,key=lambda c:(RANK[c['lib']],-min(c['stock'],10**6),c['price_usd'] or 9))
def cap_ok(c,s,diel):
    a=c['attrs'];return (c['pkg']==s['pkg'] and num(a.get('Capacitance'))==num(s['cap']) and (num(a.get('Voltage Rating')) or 0)>=s['vmin']
        and any(d in a.get('Temperature Coefficient','') for d in diel))
def res_ok(c,pkg,val,tol,thin):
    a=c['attrs'];t=num((a.get('Tolerance') or '').replace('±',''))
    return (c['pkg']==pkg and num((a.get('Resistance') or '').replace('Ω',''))==val and t is not None and t<=tol
        and (not thin or 'Thin' in a.get('Type','')))
out=[]
for (pfx,val,fp,mpn),refs in groups.items():
    q=len(refs)*BOARDS;minstock=max(200,q*20);rec=dict(refs=refs,value=val,footprint=fp,qty_per_board=len(refs),fixed_lcsc=M[refs[0]].get('lcsc',''))
    cands=[];why=''
    if rec['fixed_lcsc']:
        cands=[row(c,q) for c in search(rec['fixed_lcsc'],5) if c['componentCode']==rec['fixed_lcsc']];why='manifest LCSC (verify)'
    elif pfx=='R':
        m=re.match(r'([\d.]+)\s*([kKM]?)R?',val);v=float(m.group(1))*{'':1,'k':1e3,'K':1e3,'M':1e6}[m.group(2)]
        tol=0.1 if '0.1%' in val else 1.0;thin=tol<=0.1;pkg=fp.split('_')[1]
        kw='%s%sΩ %s %s'%(m.group(1),m.group(2),pkg,'0.1%' if thin else '')
        cands=[r for r in (row(c,q) for c in search(kw,100)) if res_ok(r,pkg,v,tol,thin)];why='R %s %s%%%s'%(val,tol,' thin film' if thin else '')
    else:
        s=[s for s in SPEC if s['refs'].split(':')[0]==pfx and s['refs'].split(':')[1] in (val,mpn,'*') and (len(s['refs'].split(':'))<3 or s['refs'].split(':')[2]==fp)]
        s=s[0] if s else None
        if s and 'mpn' in s:
            cands=[row(c,q) for c in search(s['mpn'],20) if c['componentModelEn'].upper()==s['mpn'].upper()];why='exact MPN'
        elif s and 'cap' in s:
            L=[row(c,q) for c in search(s['kw'].split(' C0G')[0],100)]
            cands=[c for c in L if cap_ok(c,s,s['diel'])];why='C %s >=%dV %s'%(s['cap'],s['vmin'],'/'.join(s['diel']))
            if not pick(cands,q,minstock) and s.get('fallback_diel'):cands=[c for c in L if cap_ok(c,s,s['fallback_diel'])];why+=' (fallback '+'/'.join(s['fallback_diel'])+')'
        elif s and s.get('type')=='Ferrite':
            cands=[c for c in (row(c,q) for c in search(s['kw'],100)) if c['pkg']==s['pkg'] and c['attrs'].get('Impedance @ Frequency','').startswith('220Ω@100MHz') and (num(c['attrs'].get('Current Rating','').replace('A',''))or 0)>=s['imin']];why='FB 220R@100MHz >=0.5A'
        elif s and s.get('type')=='PTC':
            L=[row(c,q) for c in search(s['kw'],100)]
            def hold(c):
                m=re.search(r'([\d.]+)A',c['describe']);return float(m.group(1)) if m else 0
            cands=[c for c in L if c['pkg']==s['pkg'] and s['hold_min']<=hold(c)<=s['hold_max'] and (num(c['attrs'].get('Voltage - Max','').replace('V',''))or 0)>=s['vmin']];why='PTC 1206 hold 1.0-1.5A >=6V'
        elif s and s.get('type')=='header':
            cands=[c for c in (row(c,q) for c in search(s['kw'],50)) if '2x5P' in c['describe'] and 'Right' not in c['pkg']];why='SMD 2x5 2.54 vertical (footprint fit to be checked)'
    ranked=pick(cands,q,minstock);short=False
    if not ranked and cands:ranked=sorted(cands,key=lambda c:-c['stock']);short=True   # keep the best-stocked one, flagged
    rec.update(qty_needed=q,stock_short=bool(ranked and ranked[0]['stock']<q),low_margin=bool(ranked and q<=ranked[0]['stock']<q*20),rule=why,chosen=ranked[0] if ranked else None,alternatives=ranked[1:3],n_candidates=len(cands))
    out.append(rec);c=rec['chosen'];print('%-40s %-10s %s %s'%(','.join(refs)[:40],val[:10],(c['lcsc'],c['lib'],c['stock'],c['price_usd'],c['mpn']) if c else 'NONE (%d cands)'%len(cands),'STOCK SHORT' if rec['stock_short'] else ('low margin' if rec['low_margin'] else '')),flush=True)
F=os.path.join(R,'fab','v030wip');json.dump(out,open(os.path.join(F,'parts_selection.json'),'w'),indent=1,ensure_ascii=False)
with open(os.path.join(F,'parts_selection.csv'),'w',newline='') as f:
    w=csv.writer(f);w.writerow(['Designators','Qty/board','Qty needed','Stock short','Low margin (<20x)','Value','Footprint','LCSC','Library','MPN','Brand','Stock','Unit price USD (qty %d boards)'%BOARDS,'Rule','Alternatives'])
    for r in out:
        c=r['chosen'] or {};w.writerow([','.join(r['refs']),r['qty_per_board'],r['qty_needed'],'YES' if r['stock_short'] else '','yes' if r['low_margin'] else '',r['value'],r['footprint'],c.get('lcsc',''),c.get('lib',''),c.get('mpn',''),c.get('brand',''),c.get('stock',''),c.get('price_usd',''),r['rule'],' / '.join('%s(%s,%s)'%(a['lcsc'],a['lib'],a['stock']) for a in r['alternatives'])])
