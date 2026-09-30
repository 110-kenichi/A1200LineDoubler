# J1/J2 -> HYC06-HDR15B-060, step 6: parts selection record for the new connector (JLCPCB search API, read-only).
import sys,os,json,csv
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from jlcsel import search,row
R=sys.argv[1];F=os.path.join(R,'fab','v030wip');here=os.path.dirname(os.path.abspath(__file__))
sp=os.path.join(here,'r11_parts_spec.json');s=open(sp).read()
s=s.replace('{"refs":"J:33DSMT1-E15SNCT","mpn":"33DSMT1-E15SNCT"}','{"refs":"J:HYC06-HDR15B-060","mpn":"HYC06-HDR15B-060"}');open(sp,'w').write(s)
c=[x for x in search('C711364',5) if x['componentCode']=='C711364'][0];ch=row(c,2);ch.pop('attrs',None);ch['attrs']={}
for a in (c.get('attributes') or []):ch['attrs'][a['attribute_name_en']]=a['attribute_value_name']
jp=os.path.join(F,'parts_selection.json');J=json.load(open(jp))
for r in J:
    if r['refs']==['J1','J2']:
        r.update(value='HYC06-HDR15B-060',footprint='DE15_HOAUC_HYC06-HDR15B-060',rule='exact MPN',chosen=ch,alternatives=[],n_candidates=1,
                 stock_short=ch['stock']<r['qty_needed'],low_margin=ch['stock']<20*r['qty_needed'])
json.dump(J,open(jp,'w'),indent=1,ensure_ascii=False)
cp=os.path.join(F,'parts_selection.csv');rows=list(csv.reader(open(cp)))
for w in rows:
    if w[0]=='J1,J2':w[3:15]=['YES' if ch['stock']<4 else '','yes' if ch['stock']<80 else '','HYC06-HDR15B-060','DE15_HOAUC_HYC06-HDR15B-060','C711364',ch['lib'],ch['mpn'],ch['brand'],ch['stock'],ch['price_usd'],'exact MPN','']
csv.writer(open(cp,'w',newline='')).writerows(rows)
qp=os.path.join(F,'parts_requirements.csv');rows=list(csv.reader(open(qp)))
for w in rows:
    if w[0]=='J1,J2':w[2:5]=['HYC06-HDR15B-060','DE15_HOAUC_HYC06-HDR15B-060','exact part: HYC06-HDR15B-060 (3-row HD-15 female, THT right angle)']
csv.writer(open(qp,'w',newline='')).writerows(rows)
tot=sum((r['chosen'] or {}).get('price_usd',0)*r['qty_per_board'] for r in J)
print(ch['lcsc'],ch['stock'],ch['price_usd'],'parts cost/board %.2f USD'%tot)
