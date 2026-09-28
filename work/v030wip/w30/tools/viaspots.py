import sys,json;sys.path.insert(0,'/home/claude/tools')
from router import Router
brd,net,reg=sys.argv[1],sys.argv[2],tuple(map(float,sys.argv[3].split(',')))
cands=json.loads(sys.argv[4])
r=Router(brd,(reg[0]-1,reg[1]-1,reg[2]+1,reg[3]+1));r.build(r.b.FindNet(net).GetNetCode(),allow_vip=True)
ok=[]
for x,y in cands:
    i,j=r.cell((x,y))
    if not r.mv[j*r.nx+i]:ok.append((x,y))
print(json.dumps(ok))
