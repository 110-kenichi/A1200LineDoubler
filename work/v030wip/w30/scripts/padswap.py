import re,sys
src,dst,pairs=sys.argv[1],sys.argv[2],eval(sys.argv[3])
t=open(src).read()
nets={m[1]:m[0] for m in re.findall(r'\(net (\d+) "([^"]+)"\)',t)}
i=t.find('(property "Reference" "U2"') 
if i<0:i=t.find('(fp_text reference "U2"')
fs=t.rfind('(footprint ',0,i)
# find footprint end by paren matching
d=0;j=fs
while True:
    c=t[j]
    if c=='(':d+=1
    elif c==')':
        d-=1
        if d==0:break
    j+=1
fp=t[fs:j+1]
cur={}
for m in re.finditer(r'\(pad "(\d+)"',fp):
    k=m.group(1);n=re.search(r'\(net (\d+) "([^"]+)"\)',fp[m.end():]);cur[k]=(m.end()+n.start(),m.end()+n.end(),n.group(2))
want={}
for a,b in pairs:want[a]=cur[b][2];want[b]=cur[a][2]
edits=sorted(((cur[k][0],cur[k][1],f'(net {nets[v]} "{v}")') for k,v in want.items()),reverse=True)
for s,e,r in edits:fp=fp[:s]+r+fp[e:]
t=t[:fs]+fp+t[j+1:]
open(dst,'w').write(t)
print({k:(cur[k][2],v) for k,v in want.items()})
