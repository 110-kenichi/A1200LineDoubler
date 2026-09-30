# Order follow-up: parts selection record. L1-L3 -> C92959; C15850 rows get the unified value "10uF 25V" (merged).
import sys,os,json,csv
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from jlcsel import search,row
F=os.path.join(sys.argv[1],'fab','v030wip');here=os.path.dirname(os.path.abspath(__file__))
c=[x for x in search('C92959',5) if x['componentCode']=='C92959'][0];ch=row(c,2);ch['attrs']={a['attribute_name_en']:a['attribute_value_name'] for a in (c.get('attributes') or [])}
jp=os.path.join(F,'parts_selection.json');J=json.load(open(jp));out=[];cap=None
for r in J:
    if r['refs'][:1]==['L1']:
        r.update(chosen=ch,rule='exact MPN (EasyEDA footprint available)',alternatives=[],stock_short=ch['stock']<r['qty_needed'],low_margin=ch['stock']<20*r['qty_needed'])
    if r.get('chosen') and r['chosen'].get('lcsc')=='C15850':
        if cap is None:cap=r;r['value']='10uF 25V'
        else:
            cap['refs']=sorted(cap['refs']+r['refs'],key=lambda s:int(s[1:]));cap['qty_per_board']+=r['qty_per_board'];cap['qty_needed']+=r['qty_needed'];continue
    out.append(r)
json.dump(out,open(jp,'w'),indent=1,ensure_ascii=False)
cp=os.path.join(F,'parts_selection.csv');rows=list(csv.reader(open(cp)));hdr=rows[0];new=[hdr]
for r in out:
    c2=r['chosen'] or {};new.append([','.join(r['refs']),r['qty_per_board'],r['qty_needed'],'YES' if r['stock_short'] else '','yes' if r['low_margin'] else '',r['value'],r['footprint'],
        c2.get('lcsc',''),c2.get('lib',''),c2.get('mpn',''),c2.get('brand',''),c2.get('stock',''),c2.get('price_usd',''),r['rule'],' / '.join('%s(%s,%s)'%(a['lcsc'],a['lib'],a['stock']) for a in r['alternatives'])])
csv.writer(open(cp,'w',newline='')).writerows(new)
sp=os.path.join(here,'r11_parts_spec.json');s=open(sp).read()
if 'VLS4012CX-2R2M-1' in s:open(sp,'w').write(s.replace('VLS4012CX-2R2M-1','NRS4018T2R2MDGJ'))
tot=sum((r['chosen'] or {}).get('price_usd',0)*r['qty_per_board'] for r in out)
print('C92959',ch['stock'],ch['price_usd'],'lines',len(out),'parts cost/board %.2f USD'%tot)
