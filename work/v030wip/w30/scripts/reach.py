import sys,json;sys.path.insert(0,'/home/claude/tools')
from router import Router,S
brd,net,a,z=sys.argv[1],sys.argv[2],json.loads(sys.argv[3]),json.loads(sys.argv[4])
blocks=json.loads(sys.argv[5]) if len(sys.argv)>5 else []
r=Router(brd,(14,30,60,62))
for g,ls in blocks:r.block(tuple([g[0]]+[tuple(x) if isinstance(x,list) else x for x in g[1:]]),set(ls))
r.build(r.b.FindNet(net).GetNetCode())
def flood(pt):
  A=r.cell(pt);seen=set();st=[(A[0],A[1],'F.Cu')];nx=r.nx
  while st:
    i,j,L=st.pop()
    if (i,j,L) in seen:continue
    if not(0<=i<nx and 0<=j<r.ny):continue
    if (abs(i-A[0])+abs(j-A[1])>2) and r.m[L][j*nx+i]:continue
    seen.add((i,j,L))
    for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):st.append((i+dx,j+dy,L))
    if not r.mv[j*nx+i]:
      for L2 in r.LAY:
        if L2!=L and not r.m[L2][j*nx+i]:st.append((i,j,L2))
  return seen
for pt in (a,z):
  s=flood(pt);xs=[r.x0+i*S for i,j,L in s];ys=[r.y0+j*S for i,j,L in s]
  print(pt,len(s),min(xs),max(xs),min(ys),max(ys),'vias', sum(1 for i,j,L in s if L=='B.Cu'))
