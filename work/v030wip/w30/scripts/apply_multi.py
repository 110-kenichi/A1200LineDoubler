import sys,json;sys.path.insert(0,'/home/claude/tools')
from pcbedit import Board
b=Board(sys.argv[1])
for item in json.load(open(sys.argv[3])):
    net,w,out=item[0],item[1],item[2]
    for L,pts in out['segments']:
        pts=[tuple(p) for p in pts];c=[pts[0]]
        for q in pts[1:]:
            if q!=c[-1]:c.append(q)
        if len(c)>1:b.add_path(net,c,layer=L,width=w)
    for v in out['vias']:b.add_via(net,tuple(v))
b.save(sys.argv[2])
