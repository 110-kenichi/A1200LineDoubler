import re,sys
src,dst,want=sys.argv[1],sys.argv[2],eval(sys.argv[3])
t=open(src).read()
nets={m[1]:m[0] for m in re.findall(r'\(net (\d+) "([^"]+)"\)',t)}
i=t.find('(fp_text reference "U2"');fs=t.rfind('(footprint ',0,i)
d=0;j=fs
while True:
    c=t[j]
    if c=='(':d+=1
    elif c==')':
        d-=1
        if d==0:break
    j+=1
fp=t[fs:j+1];ed=[]
for m in re.finditer(r'\(pad "(\d+)"',fp):
    k=m.group(1)
    if k in want:
        n=re.search(r'\(net (\d+) "([^"]+)"\)',fp[m.end():]);ed.append((m.end()+n.start(),m.end()+n.end(),f'(net {nets[want[k]]} "{want[k]}")',n.group(2),k))
for s,e,r,old,k in sorted(ed,reverse=True):fp=fp[:s]+r+fp[e:];print(k,old,'->',want[k])
open(dst,'w').write(t[:fs]+fp+t[j+1:])
