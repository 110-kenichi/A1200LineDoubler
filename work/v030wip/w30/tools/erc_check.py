# Apply hardware/erc_exclusions.json to a KiCad ERC report (kicad-cli sch erc output). Exit 1 if anything is left.
import re,sys,json
rep=open(sys.argv[1],encoding='utf-8').read();ex=json.load(open(sys.argv[2]))['exclusions']
items=re.findall(r'^\[(\w+)\]: ([^\n]*)\n((?:    [^\n]*\n)+)',rep,re.M)
left=[];used=[0]*len(ex)
for code,msg,body in items:
    refs=re.findall(r'Symbol (\S+) Pin (\S+) ',body)
    hit=None
    for k,e in enumerate(ex):
        if e['code']!=code:continue
        if e['ref']=='*':hit=k;break
        u3=[(r,p) for r,p in refs if r==e['ref'] and p in e['pins']]
        others=[(r,p) for r,p in refs if not (r==e['ref'] and p in e['pins']) and not r.startswith('#FLG')]
        if u3 and not others:hit=k;break
    if hit is None:left.append('[%s] %s %s'%(code,msg,' '.join('%s.%s'%x for x in refs)))
    else:used[hit]+=1
print('items',len(items),'excluded',dict(zip([e['code'] for e in ex],used)),'left',len(left))
for l in left:print('  ',l)
sys.exit(1 if left else 0)
