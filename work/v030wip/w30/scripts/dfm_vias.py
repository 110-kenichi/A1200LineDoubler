# JLC DFM follow-up (pcbnew, moves only - no BOARD.Remove): move vias that sit in / too close to SMD pads.
# Target: via copper >= GAP (0.15) from every pad (any net, F.Cu and THT), fallback 0.10. Thermal vias inside the
# U1/U2 exposed pads are intentional (plugged at fab) and are left alone. Every track ending on a moved via follows it.
# Checks: other-net copper on F/In1/In2/B >= 0.2 (via and moved tracks), hole-to-hole >= 0.25, board edge >= 0.5.
import sys,os,math,json
import pcbnew as p
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree
mm=p.ToMM;V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
b=p.LoadBoard(sys.argv[1]);EP={('U1','101'),('U2','89')};GAP=(0.15,0.10);CL=0.2;HOLE=0.25;EDGE=(0.5,0.5,94.5,94.5)
def ppoly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
pads=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if (f.GetReference(),q.GetNumber()) in EP:continue
        ls={b.GetLayerName(l) for l in q.GetLayerSet().Seq()};hole=q.GetDrillSize().x>0
        pads.append(dict(name=f.GetReference()+'.'+q.GetNumber(),net=q.GetNetCode(),g=ppoly(q),layers=ls if not hole else {'F.Cu','In1.Cu','In2.Cu','B.Cu'},
                         hole=Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(mm(q.GetDrillSize().x)/2) if hole else None))
EPg=[ppoly(q) for f in b.GetFootprints() for q in f.Pads() if (f.GetReference(),q.GetNumber()) in EP]
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)];trks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
def vg(v,pos=None):
    x,y=pos or (mm(v.GetPosition().x),mm(v.GetPosition().y));return Point(x,y).buffer(mm(v.GetWidth())/2,32)
def tg(t,a=None,e=None):
    a=a or (mm(t.GetStart().x),mm(t.GetStart().y));e=e or (mm(t.GetEnd().x),mm(t.GetEnd().y));return LineString([a,e]).buffer(mm(t.GetWidth())/2,16)
def gap_to_pads(g,own_pos):
    d=9
    for pd in pads:
        dd=g.distance(pd['g'])
        if dd<d:d=dd
    return d
# candidates
cand=[]
for v in vias:
    g=vg(v);c=Point(mm(v.GetPosition().x),mm(v.GetPosition().y))
    if any(e.contains(c) for e in EPg):continue
    near=[(g.distance(pd['g']),pd['name']) for pd in pads if 'F.Cu' in pd['layers'] or pd['hole']]
    near=[x for x in near if x[0]<GAP[1]]
    if near:cand.append((v,min(near)))
print('vias to move:',len(cand))
log=[]
for v,(d0,pn) in cand:
    net=v.GetNetCode();x0,y0=mm(v.GetPosition().x),mm(v.GetPosition().y);r=mm(v.GetWidth())/2;hr=mm(v.GetDrill())/2
    # tracks of the same net whose end lies inside the via land (some ends are off-centre, e.g. 0.0125 mm) follow the via
    inside=lambda q:(mm(q.x)-x0)**2+(mm(q.y)-y0)**2<(r-0.01)**2
    # a track with BOTH ends in the land (a short via->pad stub) stays put: moving it would collapse it to length 0
    both=lambda t:inside(t.GetStart()) and inside(t.GetEnd())
    att=[(t,'s') for t in trks if t.GetNetCode()==net and inside(t.GetStart()) and not both(t)]+\
        [(t,'e') for t in trks if t.GetNetCode()==net and inside(t.GetEnd()) and not both(t)]
    # same-net pads the via touched: they get a new track pad centre -> new via (width of the widest track on this via)
    land=Point(x0,y0).buffer(r,32)
    tpads=[pd for pd in pads if pd['net']==net and pd['g'].intersects(land) and 'F.Cu' in pd['layers']]
    ws=[mm(t.GetWidth()) for t in trks if t.GetNetCode()==net and (inside(t.GetStart()) or inside(t.GetEnd()))]
    wnew=max(ws+[0.25]);pc=[(pd,(pd['g'].centroid.x,pd['g'].centroid.y)) for pd in tpads]
    attset={id(t) for t,_ in att}
    # obstacles of other nets
    obs={L:[] for L in ('F.Cu','In1.Cu','In2.Cu','B.Cu')};holes=[]
    for t in trks:
        if id(t) in attset:continue
        L=b.GetLayerName(t.GetLayer())
        if t.GetNetCode()!=net and L in obs:obs[L].append(tg(t))
    for u in vias:
        if u is v:continue
        holes.append(Point(mm(u.GetPosition().x),mm(u.GetPosition().y)).buffer(mm(u.GetDrill())/2))
        if u.GetNetCode()!=net:
            for L in obs:obs[L].append(vg(u))
    for pd in pads:
        if pd['hole'] is not None:holes.append(pd['hole'])
        if pd['net']!=net:
            for L in pd['layers']:
                if L in obs:obs[L].append(pd['g'])
    tree={L:STRtree(g) if g else None for L,g in obs.items()};ht=STRtree(holes)
    def ok(x,y,gap):
        if not(EDGE[0]+r<=x<=EDGE[2]-r and EDGE[1]+r<=y<=EDGE[3]-r):return False
        g=Point(x,y).buffer(r,32)
        if any(e.intersects(g.buffer(0.1)) for e in EPg):return False
        if gap_to_pads(g,(x,y))<gap:return False
        h=Point(x,y).buffer(hr)
        if any(h.distance(holes[i])<HOLE for i in ht.query(h.buffer(HOLE))):return False
        for L,T in tree.items():
            if T is None:continue
            if any(g.distance(obs[L][i])<CL for i in T.query(g.buffer(CL))):return False
        for t,end in att:
            L=b.GetLayerName(t.GetLayer());other=(mm(t.GetEnd().x),mm(t.GetEnd().y)) if end=='s' else (mm(t.GetStart().x),mm(t.GetStart().y))
            sg=tg(t,(x,y),other)
            T=tree.get(L)
            if T is not None and any(sg.distance(obs[L][i])<CL for i in T.query(sg.buffer(CL))):return False
        for pd,c in pc:   # new pad -> via tracks
            sg=LineString([c,(x,y)]).buffer(wnew/2,16);T=tree.get('F.Cu')
            if T is not None and any(sg.distance(obs['F.Cu'][i])<CL for i in T.query(sg.buffer(CL))):return False
        return True
    best=None
    for gap in GAP:
        for k in range(1,49):           # radius 0.025 .. 1.2 mm
            rr=k*0.025;n=max(8,int(2*math.pi*rr/0.025))
            for a in [math.pi/4*j for j in range(8)]+[2*math.pi*i/n for i in range(n)]:   # axis / 45-degree moves first
                x,y=round(x0+rr*math.cos(a),4),round(y0+rr*math.sin(a),4)
                if ok(x,y,gap):best=(x,y,gap,rr);break
            if best:break
        if best:break
    if not best:log.append(dict(via=[x0,y0],net=v.GetNetname(),pad=pn,gap0=round(d0,3),moved=False));print('NOT MOVED',v.GetNetname(),(x0,y0),pn,round(d0,3));continue
    x,y,gap,rr=best;v.SetPosition(V(x,y))
    for t,end in att:(t.SetStart if end=='s' else t.SetEnd)(V(x,y))
    for pd,c in pc:
        t=p.PCB_TRACK(b);t.SetStart(V(round(c[0],4),round(c[1],4)));t.SetEnd(V(x,y));t.SetWidth(p.FromMM(wnew));t.SetLayer(p.F_Cu);t.SetNet(v.GetNet());b.Add(t);trks.append(t)
    log.append(dict(via=[x0,y0],to=[x,y],net=v.GetNetname(),pad=pn,gap0=round(d0,3),gap_target=gap,shift=round(rr,3),tracks=len(att)))
    print('moved %-12s (%.3f,%.3f)->(%.4f,%.4f) shift %.3f  pad %s gap %.3f -> >=%.2f, %d tracks'%(v.GetNetname(),x0,y0,x,y,rr,pn,d0,gap,len(att)))
zero=[(t.GetNetname(),mm(t.GetStart().x),mm(t.GetStart().y)) for t in trks if t.GetStart()==t.GetEnd()]
assert not zero,('zero-length tracks',zero)
json.dump(log,open(sys.argv[2].replace('.kicad_pcb','_vias.json'),'w'),indent=1)
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from pcbk7 import finish
finish(b,sys.argv[2])
