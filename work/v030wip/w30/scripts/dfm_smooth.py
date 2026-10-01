# Smooth the 0.05-mm-grid staircases left by the A* router: chains of short diagonal / straight pieces are redrawn as
# a few long straight (0/90) and 45-degree segments, keeping both ends of each chain fixed.
#  - A chain is a run of segments of one net, layer and width between anchors. Anchors: degree != 2, inside a pad or a
#    via land, a T-junction (another track ending on it), a width change. A segment that carries a T-junction is fixed.
#  - Only chains with a "jog" are touched: a segment shorter than JOG between two direction changes (or, at a chain
#    end, after one) in a chain of 3 or more segments; the result is kept only when it has fewer segments.
#  - Greedy pull-taut: from the current vertex, the farthest later vertex reachable by one octilinear segment or by two
#    (45 deg + straight, either order) that keep clearance; of the two 2-segment shapes the one closer to the old path.
#  - Clearance (copper to copper, same layer): CL to other nets' tracks / pads / vias; same-net pads and vias other than
#    the chain's own anchors are obstacles too (keeps tracks out of pin gaps); the centre line may not cross a
#    same-net track's centre line except at the anchors; NPTH holes HOLE; board edge EDGE.
# Deletions and additions by text edit, then refill + DRC. usage: dfm_smooth.py in.kicad_pcb out.kicad_pcb
import sys,os,math,json
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
import pcbnew as p
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
from shapely.ops import unary_union
from trackchains import build
mm=p.ToMM;CL=0.2;HOLE=0.25;EDGE=0.5;JOG=0.3;EPS=1e-4;R=lambda v:round(v,4)
src,dst=sys.argv[1:3]
G=build(src);b,pads,npth,vias,segs,chains,edge=G['b'],G['pads'],G['npth'],G['vias'],G['segs'],G['chains'],G['edge']
def dirn(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];l=math.hypot(dx,dy);return (round(dx/l,3),round(dy/l,3))
def has_jog(v):
    # a segment shorter than JOG with a direction change at each of its ends inside the chain (the first / last segment
    # of a chain of 3 or more counts too: a small step just before a via or pad)
    n=len(v)-1
    if n<3:return False
    for k in range(n):
        if math.dist(v[k],v[k+1])>=JOG:continue
        d=dirn(v[k],v[k+1]);bends=[]
        if k>0:bends.append(dirn(v[k-1],v[k])!=d)
        if k<n-1:bends.append(dirn(v[k+1],v[k+2])!=d)
        if bends and all(bends):return True
    return False
todo=[c for c in chains if has_jog(c['v'])]
print('chains',len(chains),'with jogs',len(todo))
# obstacles per layer
def build_obs(c,skip):
    net,L=c['net'],c['L'];ends=[Point(c['v'][0]),Point(c['v'][-1])]
    hard=[];soft=[]   # hard: clearance CL; soft (same-net tracks): no contact away from anchors
    for k,s in enumerate(segs):
        if s['L']!=L or k in skip:continue
        if s['net']!=net:hard.append(s['g'])
        else:soft.append(LineString([s['a'],s['z']]))   # same net: centre lines must not cross
    for d in pads:
        if L not in d['L']:continue
        if d['net']==net and any(d['g'].buffer(0.005).contains(e) for e in ends):continue
        hard.append(d['g'])
    for v in vias:
        if v['net']==net and any(v['g'].buffer(0.005).contains(e) for e in ends):continue
        hard.append(v['g'])
    nearA=unary_union([e.buffer(0.05) for e in ends])
    soft=[g.difference(nearA) for g in soft];soft=[g for g in soft if not g.is_empty]
    return STRtree(hard) if hard else None,hard,STRtree(soft) if soft else None,soft
def ok_path(pts,c,obs):
    T,H,TS,S=obs;w=c['w']
    for a,z in zip(pts,pts[1:]):
        if math.dist(a,z)<1e-6:continue
        g=LineString([a,z]).buffer(w/2,8)
        if not edge.contains(g):return False
        if T is not None and any(g.distance(H[i])<CL-EPS for i in T.query(g.buffer(CL))):return False
        cl=LineString([a,z])
        if TS is not None and any(cl.intersects(S[i]) for i in TS.query(cl)):return False
        if any(g.distance(h)<HOLE-EPS for h in npth):return False
    return True
def octi(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1]
    return abs(dx)<EPS or abs(dy)<EPS or abs(abs(dx)-abs(dy))<EPS
def cands(a,z):
    if octi(a,z):return [[a,z]]
    dx,dy=z[0]-a[0],z[1]-a[1];d=min(abs(dx),abs(dy));sx=math.copysign(1,dx);sy=math.copysign(1,dy)
    m1=(R(a[0]+sx*d),R(a[1]+sy*d))           # 45 first
    m2=(R(z[0]-sx*d),R(z[1]-sy*d))           # straight first
    return [[a,m1,z],[a,m2,z]]
def simplify(c):
    v=c['v'];obs=build_obs(c,set(c['idx']));old=LineString(v)
    out=[v[0]];i=0
    while i<len(v)-1:
        done=False
        for j in range(len(v)-1,i,-1):
            cs=[pp for pp in cands(v[i],v[j]) if ok_path(pp,c,obs)]
            if cs:
                best=min(cs,key=lambda pp:LineString(pp).hausdorff_distance(LineString(v[i:j+1])) if j>i+1 else 0)
                if j==i+1 and len(best)==3 and not octi(v[i],v[j]):best=[v[i],v[j]]
                out+=best[1:];i=j;done=True;break
        if not done:out.append(v[i+1]);i+=1
    # drop collinear / zero-length vertices
    res=[out[0]]
    for q in out[1:]:
        if math.dist(q,res[-1])<1e-6:continue
        if len(res)>=2 and dirn(res[-2],res[-1])==dirn(res[-1],q):res[-1]=q
        else:res.append(q)
    return res
from pcbedit import Board
B=Board(src);log=[];nseg0=nseg1=0
for c in todo:
    new=simplify(c)
    if len(new)-1>=len(c['v'])-1 and not has_jog(c['v'])==False:pass
    if len(new)-1>=len(c['v'])-1:continue
    for k in c['idx']:
        s=segs[k];B.remove_segment(s['net'],s['a'],s['z'],s['L'],dup_ok=True)
        s['dead']=True
    for a,z in zip(new,new[1:]):B.add_segment(c['net'],a,z,c['L'],c['w'])
    # new copper becomes an obstacle for later chains
    for a,z in zip(new,new[1:]):segs.append(dict(net=c['net'],L=c['L'],a=a,z=z,w=c['w'],g=LineString([a,z]).buffer(c['w']/2,8)))
    for k in c['idx']:segs[k]['L']='-'   # retired
    nseg0+=len(c['v'])-1;nseg1+=len(new)-1
    log.append(dict(net=c['net'],L=c['L'],w=c['w'],old=c['v'],new=new))
print('chains smoothed',len(log),'segments',nseg0,'->',nseg1)
tmp=dst.replace('.kicad_pcb','_rm.kicad_pcb');B.save(tmp)
from pcbk7 import finish
finish(p.LoadBoard(tmp),dst);os.remove(tmp)
json.dump(log,open(dst.replace('.kicad_pcb','_smooth.json'),'w'))
