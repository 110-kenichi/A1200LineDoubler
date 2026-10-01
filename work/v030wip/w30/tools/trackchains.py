# Track chains shared by dfm_smooth.py / dfm_planeloop.py: loads a board into plain geometry (pads, NPTH holes, vias,
# segments) and splits every net/layer into chains of segments between anchors. Anchors: degree != 2, inside a pad or
# a via land, a T-junction (another track ending on it; neighbours within 3 hops on a 0.05-grid staircase do not
# count), a width change. A segment carrying a T-junction is "fixed" and belongs to no chain.
import math
def build(src,LAY=('F.Cu','B.Cu','In2.Cu')):
    import pcbnew as p
    from shapely.geometry import Polygon,LineString,Point,box
    from shapely.strtree import STRtree
    from shapely.ops import unary_union
    mm=p.ToMM;CL=0.2;HOLE=0.25;EDGE=0.5;JOG=0.3;EPS=1e-4;R=lambda v:round(v,4)
    b=p.LoadBoard(src)
    def ppoly(q):
        o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
    pads=[];npth=[]
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetAttribute()==p.PAD_ATTRIB_NPTH:
                npth.append(Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(max(mm(q.GetDrillSize().x),mm(q.GetDrillSize().y))/2,16));continue
            ls={b.GetLayerName(l) for l in q.GetLayerSet().Seq()}
            if q.GetAttribute()==p.PAD_ATTRIB_PTH:ls|=set(LAY)
            pads.append(dict(net=q.GetNetname(),L=ls,g=ppoly(q),name=f.GetReference()+'.'+q.GetNumber()))
    vias=[];segs=[]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):
            c=(R(mm(t.GetPosition().x)),R(mm(t.GetPosition().y)));vias.append(dict(net=t.GetNetname(),c=c,g=Point(c).buffer(mm(t.GetWidth())/2,16)))
        else:
            a=(R(mm(t.GetStart().x)),R(mm(t.GetStart().y)));z=(R(mm(t.GetEnd().x)),R(mm(t.GetEnd().y)))
            if a==z:continue
            segs.append(dict(net=t.GetNetname(),L=t.GetLayerName(),a=a,z=z,w=round(mm(t.GetWidth()),4)))
    for s in segs:s['g']=LineString([s['a'],s['z']]).buffer(s['w']/2,8)
    edge=box(EDGE,EDGE,95-EDGE,95-EDGE)
    def inside_anchor_copper(net,L,pt):
        P=Point(pt)
        return any(d['net']==net and L in d['L'] and d['g'].buffer(0.005).contains(P) for d in pads) or \
               any(v['net']==net and v['g'].buffer(0.005).contains(P) for v in vias)
    # graph per net/layer
    from collections import defaultdict
    nodes=defaultdict(list)
    for i,s in enumerate(segs):nodes[(s['net'],s['L'],s['a'])].append(i);nodes[(s['net'],s['L'],s['z'])].append(i)
    def on_centre(s,pt):
        if pt in (s['a'],s['z']):return False
        return LineString([s['a'],s['z']]).distance(Point(pt))<=s['w']/2
    fixed=set();tnodes=set()
    bykey=defaultdict(list)
    for i,s in enumerate(segs):bykey[(s['net'],s['L'])].append(i)
    def near_segs(i,hops=3):
        # segments within a few hops along the track graph: on a 0.05-grid staircase a vertex lies within w/2 of the
        # next-but-one piece, which is not a T-junction
        seen={i};fr=[i]
        for _ in range(hops):
            nx=[]
            for k in fr:
                s=segs[k]
                for e in (s['a'],s['z']):
                    for j in nodes[(s['net'],s['L'],e)]:
                        if j not in seen:seen.add(j);nx.append(j)
            fr=nx
        return seen
    for (net,L,pt),lst in nodes.items():
        nb=set().union(*[near_segs(i) for i in lst])
        for j in bykey[(net,L)]:
            if j not in nb and on_centre(segs[j],pt):fixed.add(j);tnodes.add((net,L,pt))
    def is_anchor(key):
        net,L,pt=key;lst=nodes[key]
        if len(lst)!=2 or key in tnodes:return True
        if segs[lst[0]]['w']!=segs[lst[1]]['w']:return True
        if any(i in fixed for i in lst):return True
        return inside_anchor_copper(net,L,pt)
    anchor={k:is_anchor(k) for k in nodes}
    # chains
    used=set();chains=[]
    for i,s in enumerate(segs):
        if i in used or i in fixed or s['L'] not in LAY:continue
        # walk to one end
        def walk(i,end):
            pts=[];cur=i;pt=end;seen={i}
            while True:
                key=(s['net'],s['L'],pt)
                if anchor[key]:return pts,pt,True
                nx=[j for j in nodes[key] if j!=cur][0]
                if nx in seen:return pts,pt,False
                seen.add(nx);pts.append((nx,pt));cur=nx;sn=segs[nx];pt=sn['z'] if sn['a']==pt else sn['a']
        left,pa,ok1=walk(i,s['a']);right,pz,ok2=walk(i,s['z'])
        if not(ok1 and ok2):used.add(i);continue
        order=[j for j,_ in reversed(left)]+[i]+[j for j,_ in right]
        used.update(order)
        # vertex list from pa to pz
        vs=[pa];cur=pa
        for j in order:
            sj=segs[j];cur=sj['z'] if sj['a']==cur else sj['a'];vs.append(cur)
        assert vs[-1]==pz
        chains.append(dict(net=s['net'],L=s['L'],w=s['w'],idx=order,v=vs))
    return dict(b=b,pads=pads,npth=npth,vias=vias,segs=segs,chains=chains,nodes=nodes,anchor=anchor,fixed=fixed,edge=edge,R=R)
