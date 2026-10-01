# Corner check: (1) two same-net segments of different width meeting at a bend outside pads / vias (the wider cap
# sticks out past the narrower line); (2) a free end (one segment, outside every same-net pad / via land) that runs past
# a same-net track it crosses by more than that track's half width (overshoot). usage: cornerscan.py board
import sys,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from trackchains import build
from shapely.geometry import Point,LineString
G=build(sys.argv[1]);segs,nodes,pads,vias=G['segs'],G['nodes'],G['pads'],G['vias']
def inside(net,L,pt):
    P=Point(pt);return any(d['net']==net and L in d['L'] and d['g'].buffer(0.005).contains(P) for d in pads) or any(v['net']==net and v['g'].buffer(0.005).contains(P) for v in vias)
def dirn(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];l=math.hypot(dx,dy);return (dx/l,dy/l)
corner=[];over=[]
for (net,L,pt),lst in nodes.items():
    if inside(net,L,pt):continue
    if len(lst)==2:
        s,t=segs[lst[0]],segs[lst[1]]
        ds=dirn(pt,s['z'] if s['a']==pt else s['a']);dt=dirn(pt,t['z'] if t['a']==pt else t['a'])
        if abs(s['w']-t['w'])>=0.05 and abs(ds[0]*dt[0]+ds[1]*dt[1])<0.99:corner.append((net,L,pt,s['w'],t['w']))
    if len(lst)==1:
        s=segs[lst[0]];me=LineString([s['a'],s['z']])
        # a T onto another same-net track is not a free end
        if any(k!=lst[0] and u['net']==net and u['L']==L and LineString([u['a'],u['z']]).distance(Point(pt))<=u['w']/2 for k,u in enumerate(segs)):continue
        for k,u in enumerate(segs):
            if k==lst[0] or u['net']!=net or u['L']!=L:continue
            cl=LineString([u['a'],u['z']]);x=me.intersection(cl)
            if x.is_empty or x.geom_type!='Point':continue
            d=Point(pt).distance(x)
            if d>u['w']/2+0.01 and cl.distance(Point(pt))>u['w']/2:over.append((net,L,pt,round(d,3),u['a'],u['z']));break
print('width-change corners:',len(corner))
for c in corner:print('  ',c)
print('overshooting free ends:',len(over))
for c in over:print('  ',c)
