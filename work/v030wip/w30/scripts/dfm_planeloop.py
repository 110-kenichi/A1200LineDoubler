# GND / 3V3 tracks that only duplicate the plane: on F.Cu / B.Cu, a chain of a plane net (GND -> In1, 3V3 -> In2)
# with 0.05-grid jogs (the router's detours; power tracks of 0.25 mm and wider are left alone) is
# removed when every pad of the net keeps the same connection without it - vias and through-hole pads of the net count
# as tied together through the plane. Longest chains are tried first, so each pad keeps its short way to a plane via
# and long detours (often 0.05-grid staircases around other copper) go. Pieces left without a pad / via / track at one
# end are removed too (same check), then whatever KiCad's DRC still reports as dangling (same check). Deletions by text edit, then refill + DRC.
# usage: dfm_planeloop.py in.kicad_pcb out.kicad_pcb [min_len_mm=0.8]
import sys,os,json
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
import pcbnew as p
from shapely.geometry import LineString,Point
from shapely.strtree import STRtree
from trackchains import build
src,dst=sys.argv[1:3];MINLEN=float(sys.argv[3]) if len(sys.argv)>3 else 0.8
PLANE={'GND','3V3'};SIG=('F.Cu','B.Cu')
G=build(src);pads,vias,segs,chains=G['pads'],G['vias'],G['segs'],G['chains']
ALL={'F.Cu','In1.Cu','In2.Cu','B.Cu'}
def partition(net,dead):
    it=[('pad',d['name'],d['L'],d['g'],'B.Cu' in d['L'] and 'F.Cu' in d['L']) for d in pads if d['net']==net]+\
       [('via',None,ALL,v['g'],True) for v in vias if v['net']==net]+\
       [('trk',None,{s['L']},s['g'],False) for k,s in enumerate(segs) if s['net']==net and k not in dead]
    par=list(range(len(it)+1));PL=len(it)
    def fd(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    T=STRtree([x[3] for x in it])
    for i,x in enumerate(it):
        if x[4]:par[fd(i)]=fd(PL)          # via / through-hole pad: on the plane
        for j in T.query(x[3]):
            if j>i and x[2]&it[j][2] and x[3].intersects(it[j][3]):par[fd(i)]=fd(j)
    g={}
    for i,x in enumerate(it):
        if x[0]=='pad':g.setdefault(fd(i),set()).add(x[1])
    return sorted(sorted(v)+(['<plane>'] if k==fd(PL) else []) for k,v in g.items())
import math
def dirn(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];l=math.hypot(dx,dy);return (round(dx/l,3),round(dy/l,3))
def has_jog(v,JOG=0.3):   # same test as dfm_smooth.py
    for k in range(1,len(v)-2):
        if math.dist(v[k],v[k+1])<JOG and dirn(v[k-1],v[k])!=dirn(v[k],v[k+1]) and dirn(v[k],v[k+1])!=dirn(v[k+1],v[k+2]):return True
    return False
def clen(c):return sum(LineString([segs[k]['a'],segs[k]['z']]).length for k in c['idx'])
dead=set();log=[]
for net in sorted(PLANE):
    base=partition(net,dead)
    cand=sorted([c for c in chains if c['net']==net and c['L'] in SIG and clen(c)>=MINLEN and c['w']<=0.2 and has_jog(c['v'])],key=clen,reverse=True)
    for c in cand:
        trial=dead|set(c['idx'])
        if partition(net,trial)==base:dead=trial;log.append(dict(net=net,L=c['L'],len=round(clen(c),2),v=c['v']))
    # left-over pieces: an end that touches no pad / via / other live segment of the net
    while True:
        more=[]
        for c in chains:
            if c['net']!=net or c['L'] not in SIG or set(c['idx'])<=dead:continue
            for e in (c['v'][0],c['v'][-1]):
                P=Point(e).buffer(0.01)
                hit=any(c['L'] in d['L'] and d['g'].intersects(P) for d in pads if d['net']==net) or \
                    any(v['g'].intersects(P) for v in vias if v['net']==net) or \
                    any(k not in dead and k not in c['idx'] and s['net']==net and s['L']==c['L'] and s['g'].intersects(P) for k,s in enumerate(segs))
                if not hit:more.append(c);break
        added=False
        for c in more:
            trial=dead|set(c['idx'])
            if partition(net,trial)==base:dead=trial;added=True;log.append(dict(net=net,L=c['L'],len=round(clen(c),2),v=c['v'],leftover=True))
        if not added:break
    assert partition(net,dead)==base,net
print('plane-net chains removed:',len(log),' track length %.1f mm'%sum(x['len'] for x in log),' segments',len(dead))
for x in log:print('  %-4s %s %5.2f mm  %s -> %s%s'%(x['net'],x['L'],x['len'],x['v'][0],x['v'][-1],' (left-over)' if x.get('leftover') else ''))
from pcbedit import Board
from pcbk7 import finish
import re
def write():
    B=Board(src)
    for k in sorted(dead):
        s=segs[k];B.remove_segment(s['net'],s['a'],s['z'],s['L'],dup_ok=True)
    tmp=dst.replace('.kicad_pcb','_rm.kicad_pcb');B.save(tmp)
    finish(p.LoadBoard(tmp),dst);os.remove(tmp)
write()
for rnd in range(20):
    rep=open(dst.replace('.kicad_pcb','_drc.txt'),encoding='utf-8').read();n=0
    for x,y,net,L,ln in re.findall(r'\[track_dangling\].*?\n.*?\n\s*@\(([-\d.]+) mm, ([-\d.]+) mm\): Track \[([^\]]*)\] on (\S+), length ([\d.]+) mm',rep):
        if net not in PLANE:continue
        x,y,ln=float(x),float(y),float(ln)
        for k,s in enumerate(segs):
            if k in dead or s['net']!=net or s['L']!=L:continue
            if not any(abs(e[0]-x)<0.002 and abs(e[1]-y)<0.002 for e in (s['a'],s['z'])):continue
            if abs(LineString([s['a'],s['z']]).length-ln)>0.002:continue
            if partition(net,dead|{k})==partition(net,dead):dead.add(k);n+=1;log.append(dict(net=net,L=L,len=round(ln,2),v=[s['a'],s['z']],leftover=True))
            break
    print('round',rnd,'dangling pieces removed:',n)
    if not n:break
    write()
json.dump(log,open(dst.replace('.kicad_pcb','_planeloop.json'),'w'))
