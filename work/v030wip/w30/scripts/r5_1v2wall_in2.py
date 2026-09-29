# move the 1V2 right-side B.Cu link (vias (58,37.225)<->(58,45.225)) to In2.Cu, same geometry (text edit)
import re,sys
src,dst=sys.argv[1:3];L=open(src,encoding='utf-8').read().split('\n')
net=[int(m.group(1)) for l in L for m in [re.match(r'\s*\(net (\d+) "1V2"\)$',l)] if m][0];n=0
for i,l in enumerate(L):
    m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "B.Cu"\) \(net (\d+)\)',l)
    if m and int(m.group(5))==net:
        xs=[float(m.group(1)),float(m.group(3))];ys=[float(m.group(2)),float(m.group(4))]
        if min(xs)>=57.9 and max(xs)<=58.8 and min(ys)>=37.2 and max(ys)<=45.3:L[i]=l.replace('(layer "B.Cu")','(layer "In2.Cu")');n+=1
print('moved',n);open(dst,'w',encoding='utf-8').write('\n'.join(L))
