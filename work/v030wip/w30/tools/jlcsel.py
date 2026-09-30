# JLCPCB part lookup/selection via jlcpcb.com's public component search API (read-only; nothing is ordered).
import json,re,sys,time,urllib.request
API='https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
def search(kw,n=100):
    req=urllib.request.Request(API,data=json.dumps({'keyword':kw,'currentPage':1,'pageSize':n}).encode(),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
    for k in range(3):
        try:return json.load(urllib.request.urlopen(req,timeout=40))['data']['componentPageInfo']['list'] or []
        except Exception as e:time.sleep(2*(k+1));err=e
    raise err
def attrs(c):return {a['attribute_name_en']:a['attribute_value_name'] for a in (c.get('attributes') or [])}
UNIT={'p':1e-12,'n':1e-9,'u':1e-6,'µ':1e-6,'m':1e-3,'':1,'k':1e3,'K':1e3,'M':1e6,'Ω':1}
def num(s):
    m=re.match(r'\s*([\d.]+)\s*([pnuµmkKM]?)',s or '');return float(m.group(1))*UNIT[m.group(2)] if m else None
def price(c,q):
    ps=c.get('componentPrices') or [];best=None
    for p in ps:
        if q>=p['startNumber'] and (p['endNumber']==-1 or q<=p['endNumber']):best=p['productPrice']
    return best if best is not None else (ps[0]['productPrice'] if ps else None)
def lib(c):return 'basic' if c['componentLibraryType']=='base' else ('preferred' if c.get('preferredComponentFlag') else 'extended')
def row(c,q):
    a=attrs(c);return dict(lcsc=c['componentCode'],mpn=c['componentModelEn'],brand=c['componentBrandEn'],pkg=c['componentSpecificationEn'],lib=lib(c),
        stock=c['stockCount'],price_usd=price(c,q),describe=c['describe'],attrs=a)
