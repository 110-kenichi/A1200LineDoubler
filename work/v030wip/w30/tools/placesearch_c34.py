# C34 placement search: 0603 + via escape, F/In1/In2/B clearance check (shapely). usage: python3 placesearch_c34.py <board>
import pcbnew as p, math, sys
from shapely.geometry import Point, LineString, box
from shapely.strtree import STRtree
mm=p.ToMM
b=p.LoadBoard(sys.argv[1])
CL=0.2; HOLE=0.25
LAY={'F.Cu':p.F_Cu,'In1.Cu':p.In1_Cu,'In2.Cu':p.In2_Cu,'B.Cu':p.B_Cu}
obs={L:[] for L in LAY}  # (geom, net)
holes=[]
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):
        c=Point(mm(t.GetPosition().x),mm(t.GetPosition().y))
        for L in LAY: obs[L].append((c.buffer(mm(t.GetWidth())/2),t.GetNetname()))
        holes.append(c.buffer(mm(t.GetDrill())/2))
    else:
        g=LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2)
        obs[b.GetLayerName(t.GetLayer())].append((g,t.GetNetname()))
cy=[]
for f in b.GetFootprints():
    if f.GetReference()=='C34': continue
    try: bb=f.GetCourtyard(p.F_CrtYd).BBox(); cy.append(box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
    except Exception: pass
    for q in f.Pads():
        bb=q.GetBoundingBox(); g=box(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom()))
        for L,l in LAY.items():
            if q.IsOnLayer(l): obs[L].append((g,q.GetNetname()))
        if q.GetDrillSize().x>0: holes.append(Point(mm(q.GetPosition().x),mm(q.GetPosition().y)).buffer(mm(q.GetDrillSize().x)/2))
trees={L:STRtree([g for g,n in obs[L]]) for L in LAY}
def clear(L,g,net):
    for i in trees[L].query(g.buffer(CL)):
        og,on=obs[L][i]
        if on==net and net in('3V3','GND'): 
            continue
        if og.distance(g)<CL: return False
    return True
htree=STRtree(holes)
def hole_ok(pt):
    h=pt.buffer(0.15)
    return all(holes[i].distance(h)>=HOLE for i in htree.query(h.buffer(HOLE)))
edge=box(1.5,1.5,93.5,93.5)
ctree=STRtree(cy)
RES_F=box(41.2,42.1,45.5,44.1)      # U2 left control escape (F.Cu vias/traces planned)
RES_V=box(32.0,35.8,44.6,44.05)     # planned B.Cu control corridor to U1 inner vias
PIN58=(46.05,43.0)
res=[]
for rot in (0,90):
    ax=(1,0) if rot==0 else (0,1)
    hw,hh=(1.48,0.73) if rot==0 else (0.73,1.48)
    for i in range(int((35-35)/1),1):
        pass
    x=34.0
    while x<=52:
        y=44.0
        while y<=52:
            ctr=box(x-hw,y-hh,x+hw,y+hh)
            if not edge.contains(ctr) or any(cy[k].intersects(ctr) for k in ctree.query(ctr)) or ctr.intersects(RES_F):
                y+=0.05; continue
            pads=[(x-0.775*ax[0],y-0.775*ax[1]),(x+0.775*ax[0],y+0.775*ax[1])]
            best=None
            for order in ((0,1),(1,0)):
                nets={order[0]:'3V3',order[1]:'GND'}
                ok=True; sol=[]
                for k in (0,1):
                    px,py=pads[k]; net=nets[k]
                    pg=box(px-0.45*(1 if rot==0 else 0.95/0.9),py-0.475*(1 if rot==0 else 0.9/0.95),px+0.45*(1 if rot==0 else 0.95/0.9),py+0.475*(1 if rot==0 else 0.9/0.95)) if False else (box(px-0.45,py-0.475,px+0.45,py+0.475) if rot==0 else box(px-0.475,py-0.45,px+0.475,py+0.45))
                    if not clear('F.Cu',pg,net): ok=False;break
                    out=(-1 if k==0 else 1)
                    cands=[(px+out*ax[0]*d,py+out*ax[1]*d) for d in (0.95,1.1,1.3)]+[(px+s*ax[1]*d,py+s*ax[0]*d) for s in (-1,1) for d in (0.9,1.1)]
                    vs=None
                    for vx,vy in cands:
                        vp=Point(vx,vy); vg=vp.buffer(0.3 if net=='GND' else 0.275)
                        if RES_V.contains(vp) or ctr.buffer(-0.05).contains(vp) and False: continue
                        tr=LineString([(px,py),(vx,vy)]).buffer(0.125)
                        if all(clear(L,vg,net) for L in LAY if not (L=='In1.Cu' and net=='GND') and not (L=='In2.Cu' and net=='3V3')) and clear('F.Cu',tr,net) and hole_ok(vp) \
                           and Point(vx,vy).distance(Point(pads[1-k]))>0.475+0.3+CL:
                            vs=(vx,vy);break
                    if not vs: ok=False;break
                    sol.append((net,(px,py),vs))
                if ok:
                    v3=[s for s in sol if s[0]=='3V3'][0][2]
                    score=math.dist(v3,PIN58)
                    if best is None or score<best[0]: best=(score,rot,(round(x,2),round(y,2)),order,sol)
            if best: res.append(best)
            y+=0.05
        x+=0.05
res.sort()
for r in res[:15]: print(r)
