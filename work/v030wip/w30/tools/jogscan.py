# Report short "jogs": a segment shorter than JOG (default 0.3 mm) whose both ends are plain bends (two segments of the
# same net/layer meet, outside every pad and via land) with a direction change at each end. usage: jogscan.py board [JOG]
import sys,math,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from trackchains import build
from shapely.geometry import Point
JOG=float(sys.argv[2]) if len(sys.argv)>2 else 0.3
G=build(sys.argv[1]);segs,nodes,pads,vias=G['segs'],G['nodes'],G['pads'],G['vias']
def dirn(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];l=math.hypot(dx,dy);return (round(dx/l,3),round(dy/l,3))
def inside(net,L,pt):
    P=Point(pt);return any(d['net']==net and L in d['L'] and d['g'].buffer(0.005).contains(P) for d in pads) or any(v['net']==net and v['g'].buffer(0.005).contains(P) for v in vias)
hits=[]
for i,s in enumerate(segs):
    if s['L'] not in ('F.Cu','B.Cu','In2.Cu') or math.dist(s['a'],s['z'])>=JOG:continue
    ok=True
    for e in (s['a'],s['z']):
        lst=nodes[(s['net'],s['L'],e)]
        if len(lst)!=2 or inside(s['net'],s['L'],e):ok=False;break
        o=segs[[j for j in lst if j!=i][0]];oe=o['z'] if o['a']==e else o['a']
        if dirn(oe,e)==dirn(s['a'],s['z']) or dirn(oe,e)==dirn(s['z'],s['a']):ok=False;break
    if ok:hits.append((s['net'],s['L'],s['a'],s['z']))
print('jogs:',len(hits))
for h in hits:print('  ',h)
