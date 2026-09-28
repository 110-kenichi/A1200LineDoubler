import re,collections,sys
def nets(f):
    t=open(f).read();c=collections.Counter()
    for b in t.split('[unconnected_items]')[1:]:
        m=re.findall(r'\[([^\]]+)\] (?:of|on)',b.split('\n[')[0]);c[m[0] if m else '?']+=1
    return c
a=nets(sys.argv[1]);b=nets(sys.argv[2])
print('before',sum(a.values()),'after',sum(b.values()))
for n in sorted(set(a)|set(b)):
    if a[n]!=b[n]:print(' ',n,a[n],'->',b[n])
