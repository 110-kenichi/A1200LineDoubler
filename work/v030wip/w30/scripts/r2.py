import sys,json;sys.path.insert(0,'/home/claude/tools')
from router import Router
brd,net,a,la,z,lz,blocks,opts=sys.argv[1],sys.argv[2],json.loads(sys.argv[3]),sys.argv[4],json.loads(sys.argv[5]),sys.argv[6],json.loads(sys.argv[7]),json.loads(sys.argv[8])
r=Router(brd,tuple(opts.get('region',[12,30,62,66])))
for g,ls in blocks:r.block(tuple([g[0]]+[tuple(x) if isinstance(x,list) else x for x in g[1:]]),set(ls))
r.build(r.b.FindNet(net).GetNetCode())
res=r.route(tuple(a),la,tuple(z),lz,via_cost=opts.get('via',25),turn=opts.get('turn',0.4),free_a=2,free_z=opts.get('fz',2))
print(json.dumps(res))
