import sys,json;sys.path.insert(0,'/home/claude/tools')
from pcbedit import Board
src,dst,net,rj=sys.argv[1:5];pad=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
b=Board(src);res=json.load(open(rj))
segs=res['segments']
# exact pad-center stubs
if 'a' in pad:segs[0][1].insert(0,pad['a'])
if 'z' in pad:segs[-1][1].append(pad['z'])
for L,pts in segs:
    pts=[tuple(p) for p in pts];clean=[pts[0]]
    for q in pts[1:]:
        if q!=clean[-1]:clean.append(q)
    b.add_path(net,clean,layer=L)
for v in res['vias']:b.add_via(net,tuple(v))
b.save(dst)
