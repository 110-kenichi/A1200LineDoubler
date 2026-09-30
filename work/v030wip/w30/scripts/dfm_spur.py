# Clean-up: dead spurs of routed nets - track pieces (and vias) that lie on no path between two pads, including
# hair-pin loops whose ends all touch their own copper (KiCad's dangling check and dfm_dedup.py miss those).
# Per net: graph of copper items (pads, vias, tracks; edge = copper overlap on a shared layer), biconnected blocks;
# a leaf block (one cut vertex) with no pad besides the cut vertex is removed, repeatedly. GND/3V3 are skipped
# (their copper also connects through the pours). The pad partition of every touched net must stay the same.
# Deletions by text edit (BOARD.Remove is unsafe in KiCad 7.0.11). usage: dfm_spur.py in.kicad_pcb out.kicad_pcb
import sys,os,re,json
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
import pcbnew as p
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
mm=p.ToMM;SKIP={'GND','3V3'};ALL={'F.Cu','In1.Cu','In2.Cu','B.Cu'}
src,dst=sys.argv[1:3];work=dst.replace('.kicad_pcb','_rm.kicad_pcb')
b=p.LoadBoard(src);items={}
def add(net,it):items.setdefault(net,[]).append(it)
for f in b.GetFootprints():
    for q in f.Pads():
        if not q.GetNetname() or q.GetNetname() in SKIP:continue
        o=q.GetEffectivePolygon().Outline(0);g=Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
        ls=ALL if q.GetAttribute()==p.PAD_ATTRIB_PTH else {b.GetLayerName(l) for l in q.GetLayerSet().Seq()}
        add(q.GetNetname(),dict(k='pad',name=f.GetReference()+'.'+q.GetNumber(),L=ls,g=g))
for t in b.GetTracks():
    net=t.GetNetname()
    if net in SKIP:continue
    if isinstance(t,p.PCB_VIA):
        c=(round(mm(t.GetPosition().x),4),round(mm(t.GetPosition().y),4))
        add(net,dict(k='via',c=c,L=ALL,g=Point(c).buffer(mm(t.GetWidth())/2,16)))
    else:
        a=(round(mm(t.GetStart().x),4),round(mm(t.GetStart().y),4));z=(round(mm(t.GetEnd().x),4),round(mm(t.GetEnd().y),4))
        w=mm(t.GetWidth());add(net,dict(k='trk',a=a,z=z,w=w,L={t.GetLayerName()},g=LineString([a,z]).buffer(w/2,8) if a!=z else Point(a).buffer(w/2,8)))
def graph(its):
    alive=[i for i,x in enumerate(its) if not x.get('dead')];T=STRtree([its[i]['g'] for i in alive]);adj={i:set() for i in alive}
    for n,i in enumerate(alive):
        for m in T.query(its[i]['g']):
            j=alive[m]
            if j!=i and its[i]['L']&its[j]['L'] and its[i]['g'].intersects(its[j]['g']):adj[i].add(j);adj[j].add(i)
    return adj
def blocks(adj):
    # Hopcroft-Tarjan biconnected components (iterative); returns list of node sets and the set of cut vertices
    disc={};low={};res=[];cut=set();t=[0]
    for r in adj:
        if r in disc:continue
        disc[r]=low[r]=t[0];t[0]+=1;st=[(r,None,iter(adj[r]))];es=[];kids=0
        if not adj[r]:res.append({r})
        while st:
            u,pa,it=st[-1];adv=False
            for v in it:
                if v==pa:continue
                if v not in disc:
                    disc[v]=low[v]=t[0];t[0]+=1;es.append((u,v));st.append((v,u,iter(adj[v])));adv=True
                    if u==r:kids+=1
                    break
                elif disc[v]<disc[u]:low[u]=min(low[u],disc[v]);es.append((u,v))
            if adv:continue
            st.pop()
            if st:
                w=st[-1][0];low[w]=min(low[w],low[u])
                if low[u]>=disc[w]:
                    if w!=r:cut.add(w)
                    comp=set()
                    while es:
                        e=es.pop();comp|=set(e)
                        if e==(w,u):break
                    res.append(comp)
        if kids>1:cut.add(r)
    return res,cut
def partition(its):
    adj=graph(its);seen=set();out=[]
    for i in adj:
        if i in seen:continue
        stk=[i];seen.add(i);comp=[]
        while stk:
            u=stk.pop();comp.append(u)
            for v in adj[u]:
                if v not in seen:seen.add(v);stk.append(v)
        pads=sorted(its[u]['name'] for u in comp if its[u]['k']=='pad')
        if pads:out.append(pads)
    return sorted(out)
log={}
for net,its in items.items():
    if not any(x['k']!='pad' for x in its):continue
    base=partition(its);gone=[]
    while True:
        adj=graph(its);bl,cut=blocks(adj);rm=set()
        # a connected part with no pad at all, or a leaf block whose non-cut members hold no pad
        comps={};seen=set()
        for i in adj:
            if i in seen:continue
            stk=[i];seen.add(i);c=set()
            while stk:
                u=stk.pop();c.add(u)
                for v in adj[u]:
                    if v not in seen:seen.add(v);stk.append(v)
            if not any(its[u]['k']=='pad' for u in c):rm|=c
        for B in bl:
            cv=B&cut
            if len(cv)==1 and not any(its[u]['k']=='pad' for u in B-cv):rm|=B-cv
        if not rm:break
        for u in rm:its[u]['dead']=True
        gone+=list(rm)
    if gone:
        assert partition(its)==base,net
        log[net]=[dict(k=its[u]['k'],L=sorted(its[u]['L'])[0] if its[u]['k']=='trk' else 'via',a=its[u].get('a',its[u].get('c')),z=its[u].get('z'),
                       len=round(its[u]['g'].length/2,3) if its[u]['k']=='trk' else 0) for u in gone]
tot=sum(len(v) for v in log.values())
for net,v in sorted(log.items()):
    print('%-14s %2d items, track length %.2f mm, vias %d'%(net,len(v),sum(x['len'] for x in v if x['k']=='trk'),sum(x['k']=='via' for x in v)))
print('spur items removed:',tot)
# text edit
L=open(src,encoding='utf-8').read().split('\n')
nets={m.group(2):int(m.group(1)) for l in L for m in [re.match(r'\s*\(net (\d+) "(.*)"\)$',l)] if m};inv={v:k for k,v in nets.items()}
kill={}
for net,v in log.items():
    for x in v:
        key=(net,'via',tuple(x['a'])) if x['k']=='via' else (net,x['L'],tuple(x['a']),tuple(x['z']))
        kill[key]=kill.get(key,0)+1
out=[];n=0;r4=lambda s:round(float(s),4)
for l in L:
    m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net (\d+)\)',l)
    key=None
    if m:key=(inv[int(m.group(6))],m.group(5),(r4(m.group(1)),r4(m.group(2))),(r4(m.group(3)),r4(m.group(4))))
    mv=re.match(r'\s*\(via \(at ([-\d.]+) ([-\d.]+)\).*\(net (\d+)\)',l)
    if mv:key=(inv[int(mv.group(3))],'via',(r4(mv.group(1)),r4(mv.group(2))))
    if key and kill.get(key,0)>0:kill[key]-=1;n+=1;continue
    out.append(l)
assert not any(kill.values()),[k for k,v in kill.items() if v]
open(work,'w',encoding='utf-8').write('\n'.join(out))
print('lines deleted:',n)
from pcbk7 import finish
finish(p.LoadBoard(work),dst);os.remove(work)
json.dump(log,open(dst.replace('.kicad_pcb','_spur.json'),'w'),indent=1)
