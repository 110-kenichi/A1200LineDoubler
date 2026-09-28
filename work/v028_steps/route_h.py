import sys,json,time;sys.path.insert(0,'/home/claude/tools')
from router import Router
t=time.time()
r=Router(sys.argv[1],(12,30,40,62))
net=r.b.FindNet(sys.argv[2]).GetNetCode()
# reserve REF_27M escape from pin 80 inward + its via
r.block(('s',(30.0,35.1),(30.0,37.1),0.075),{'F.Cu'})
r.block(('c',(30.05,37.1),0.275))
for g,ls in (json.loads(sys.argv[7]) if len(sys.argv)>7 else []):r.block(tuple([g[0]]+[tuple(x) if isinstance(x,list) else x for x in g[1:]]),set(ls) if ls!="all" else "all")
r.build(net)
a=tuple(map(float,sys.argv[3].split(',')));z=tuple(map(float,sys.argv[5].split(',')))
res=r.route(a,sys.argv[4],z,sys.argv[6],via_cost=30,free_a=2,free_z=2)
print(json.dumps(res));print('t',time.time()-t,file=sys.stderr)
