# JLC DFM follow-up: no track may run in the gap between two adjacent IC pins (U1..U9), even of the same net.
# Step 1 (text, pcbedit): delete every F.Cu segment of the pins' net that enters such a gap (same-net pin bridges).
# Step 2 (pcbnew + router7): every SMD pad left without a connection (own copper island without a via / the net's main
# body) is re-routed from the pad to the nearest connected copper of its net, with all pin gaps blocked on F.Cu.
# usage: dfm_gapfix.py in.kicad_pcb out.kicad_pcb
import sys,os,json,math
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
import pcbnew as p
from shapely.geometry import Polygon,LineString,Point,box
from shapely.strtree import STRtree
mm=p.ToMM
ICS=('U1','U2','U3','U4','U5','U6','U7','U8','U9')
def ppoly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
def gaps(b):
    """(ref,pinA,pinB,net or None,box) for side-by-side equal pads of the ICs, gap < 0.4 mm"""
    out=[]
    for ref in ICS:
        f=b.FindFootprintByReference(ref);pads=[]
        for q in f.Pads():
            if not q.GetNumber() or q.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
            bb=q.GetBoundingBox();pads.append((q.GetNumber(),q.GetNetname(),mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
        for i,a in enumerate(pads):
            for c in pads[i+1:]:
                n1,net1,ax0,ay0,ax1,ay1=a;n2,net2,cx0,cy0,cx1,cy1=c
                if abs((ax1-ax0)-(cx1-cx0))>1e-3 or abs((ay1-ay0)-(cy1-cy0))>1e-3:continue
                if abs(ay0-cy0)<1e-3 and 0<(max(ax0,cx0)-min(ax1,cx1))<0.4:g=box(min(ax1,cx1),ay0,max(ax0,cx0),ay1)
                elif abs(ax0-cx0)<1e-3 and 0<(max(ay0,cy0)-min(ay1,cy1))<0.4:g=box(ax0,min(ay1,cy1),ax1,max(ay0,cy0))
                else:continue
                out.append((ref,n1,n2,net1 if net1==net2 else None,g))
    return out
src,dst=sys.argv[1],sys.argv[2];work=dst.replace('.kicad_pcb','_rm.kicad_pcb')
# ---- step 1: delete same-net gap segments (text edit)
b=p.LoadBoard(src);G=gaps(b);rm={}
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA) or t.GetLayer()!=p.F_Cu:continue
    tg=LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2,8)
    for ref,n1,n2,net,g in G:
        if net and t.GetNetname()==net and tg.intersection(g).area>0.002:
            rm[(round(mm(t.GetStart().x),4),round(mm(t.GetStart().y),4),round(mm(t.GetEnd().x),4),round(mm(t.GetEnd().y),4))]=(net,ref,n1,n2)
from pcbedit import Board
E=Board(src)
for (ax,ay,zx,zy),(net,*_) in rm.items():E.remove_segment(net,(ax,ay),(zx,zy),'F.Cu')
E.save(work);print('gap segments deleted:',len(rm))
# ---- step 1b: pieces left dangling by the deletion (one end touches nothing of its net) go too, repeatedly
affected={v[0] for v in rm.values()};nd=0
while True:
    b=p.LoadBoard(work);cop={}
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetNetname() in affected and q.IsOnLayer(p.F_Cu):cop.setdefault(q.GetNetname(),[]).append((None,ppoly(q)))
    segs=[]
    for t in b.GetTracks():
        if t.GetNetname() not in affected:continue
        if isinstance(t,p.PCB_VIA):cop.setdefault(t.GetNetname(),[]).append((None,Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetWidth())/2,12)))
        elif t.GetLayer()==p.F_Cu:
            a=(mm(t.GetStart().x),mm(t.GetStart().y));z=(mm(t.GetEnd().x),mm(t.GetEnd().y))
            segs.append((t.GetNetname(),a,z));cop.setdefault(t.GetNetname(),[]).append(((a,z),LineString([a,z]).buffer(mm(t.GetWidth())/2,8)))
    dead=[]
    ends={}
    for net,a,z in segs:
        for e in (a,z):ends.setdefault(net,[]).append(((a,z),e))
    for net,a,z in segs:
        for e in (a,z):
            pt=Point(e)
            # like KiCad: an end is connected only if it lies in a pad / via land or on another track's end point
            inpad=any(key is None and g.buffer(0.005).contains(pt) for key,g in cop[net])
            onend=any(key!=(a,z) and abs(q[0]-e[0])<0.005 and abs(q[1]-e[1])<0.005 for key,q in ends[net])
            if not (inpad or onend):dead.append((net,a,z));break
    if not dead:break
    E=Board(work)
    for net,a,z in sorted(set(dead)):
        while True:   # duplicates of the same piece exist: remove every copy
            try:E.remove_segment(net,a,z,'F.Cu')
            except AssertionError as ex:
                if ex.args and ex.args[0][3]:   # several hits: drop the first and loop
                    del E.lines[ex.args[0][3][0]];continue
                break
    E.save(work);nd+=len(set(dead))
print('dangling pieces deleted:',nd)
# ---- step 2: find unconnected SMD pads (islands) of the affected nets and re-route them
b=p.LoadBoard(work)
def islands(net):
    it=[]
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetNetname()==net:it.append(('pad',(f.GetReference(),q.GetNumber()),{b.GetLayerName(l) for l in q.GetLayerSet().Seq()},ppoly(q)))
    for t in b.GetTracks():
        if t.GetNetname()!=net:continue
        if isinstance(t,p.PCB_VIA):it.append(('via',(mm(t.GetPosition().x),mm(t.GetPosition().y)),{'F.Cu','In1.Cu','In2.Cu','B.Cu'},Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetWidth())/2,12)))
        else:it.append(('trk',None,{t.GetLayerName()},LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2,8)))
    par=list(range(len(it)))
    def fd(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    T=STRtree([x[3] for x in it])
    for i,x in enumerate(it):
        for j in T.query(x[3]):
            if j>i and x[2]&it[j][2] and x[3].intersects(it[j][3]):par[fd(i)]=fd(j)
    comp={}
    for i,x in enumerate(it):comp.setdefault(fd(i),[]).append(x)
    return list(comp.values())
nets=sorted({v[0] for v in rm.values()});jobs=[]
for net in nets:
    comps=islands(net);plane=net in ('GND','3V3')
    main=max(comps,key=len)
    for c in comps:
        smd=[x for x in c if x[0]=='pad' and x[1][0] in ICS]
        if not smd:continue
        anchored=any(x[0]=='via' for x in c) if plane else (c is main)
        thru=any(x[0]=='pad' and 'In1.Cu' in x[2] for x in c)
        if anchored or thru:continue
        # targets: connected copper of the net (vias for plane nets, else items of the main body), nearest first
        good=[x for cc in comps for x in cc if ((plane and any(y[0]=='via' for y in cc)) or (not plane and cc is main))]
        jobs.append((net,smd[0][1],smd[0][3],good))
print('pads to reconnect:',[(j[0],j[1]) for j in jobs])
from router7 import Router
from pcbk7 import path as addpath,via as addvia,finish
cur=work;log=[]
for net,(ref,pin),pg,good in jobs:
    c=pg.centroid;cx,cy=c.x,c.y
    cands=[]
    icpads=[ppoly(q).buffer(0.4) for rf in ICS for q in b.FindFootprintByReference(rf).Pads() if q.GetNumber() and q.GetAttribute()==p.PAD_ATTRIB_SMD and not (rf in ('U1','U2') and q.GetNumber() in ('101','89'))]
    ICT=STRtree(icpads)
    for x in good:
        if x[0]=='pad' or 'F.Cu' not in x[2]:continue   # F.Cu tracks or vias only
        g=x[3]
        if x[0]=='via':pts=[g.centroid]
        else:   # sample points along the track body
            ln=g.minimum_rotated_rectangle.exterior;pts=[g.centroid]
        for q in pts:
            if any(icpads[i].contains(q) for i in ICT.query(q)):continue   # target must be away from IC pins
            d=math.hypot(q.x-cx,q.y-cy)
            if 0.3<d<6:cands.append((d,(round(q.x/0.05)*0.05,round(q.y/0.05)*0.05),x[0]))
    cands.sort()
    done=None
    for d,z,kind in cands[:8]:
        r=Router(cur,(cx-7,cy-7,cx+7,cy+7),width=0.2,layers=('F.Cu',))
        r.build(r.b.FindNet(net).GetNetCode())
        for gref,n1,n2,gnet,g in G:        # block every IC pin gap for this net's track centre line (+ half width)
            gg=g.buffer(0.09)
            x0,y0,x1,y1=gg.bounds
            for j in range(max(0,int((y0-r.y0)/0.05)),min(r.ny,int((y1-r.y0)/0.05)+2)):
                for i in range(max(0,int((x0-r.x0)/0.05)),min(r.nx,int((x1-r.x0)/0.05)+2)):
                    if gg.contains(Point(r.x0+i*0.05,r.y0+j*0.05)):r.m['F.Cu'][j*r.nx+i]=1
        res=r.route((round(cx/0.05)*0.05,round(cy/0.05)*0.05),'F.Cu',z,'F.Cu',via_cost=99,turn=0.5,free_a=0,free_z=2)
        if res:done=(z,kind,res);break
    if not done:print('FAILED',net,ref,pin);log.append(dict(net=net,pad=[ref,pin],ok=False));continue
    z,kind,res=done;B=p.LoadBoard(cur)
    for L,pts in res['segments']:
        pts=[tuple(q) for q in pts]
        if pts[0]!=(round(cx,4),round(cy,4)):pts=[(round(cx,4),round(cy,4))]+pts
        if pts[-1]!=z:pts=pts+[z]
        addpath(B,net,pts,L,w=0.2)
    p.SaveBoard(cur,B)
    log.append(dict(net=net,pad=[ref,pin],to=list(z),kind=kind,segments=res['segments']))
    print('reconnected',net,ref,pin,'->',kind,z)
# U1.72 (GND): the router finds no F.Cu path (boxed in by pins 71/73, the 1V9 via (35.0,37.775) and the SCL/RESET
# escapes); hand route off the pin tip to the GND stub end (34.7,36.95) of pin 73's via.
B=p.LoadBoard(cur)
if any(l['pad']==['U1','72'] and not l.get('ok',True) for l in log):
    addpath(B,'GND',[(33.65,37.5),(34.45,37.5),(34.7,37.25),(34.7,36.95)],'F.Cu',w=0.15);log.append(dict(net='GND',pad=['U1','72'],hand=True))
# U5.5 (3V3) left its pad through the side into the U5.4/5 gap: its bend points move to leave straight off the inner end
def mvpt(B,net,old,new):
    for t in B.GetTracks():
        if t.GetNetname()!=net or isinstance(t,p.PCB_VIA):continue
        for get,setp in ((t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)):
            q=get()
            if abs(mm(q.x)-old[0])<1e-3 and abs(mm(q.y)-old[1])<1e-3:setp(p.VECTOR2I(p.FromMM(new[0]),p.FromMM(new[1])))
for old,new in (((82.85,55.3),(82.3,55.0)),((82.5,55.3),(82.15,55.15)),((82.45,55.35),(82.15,55.35))):mvpt(B,'3V3',old,new)
p.SaveBoard(cur,B)
json.dump(dict(deleted=[list(k)+list(v) for k,v in rm.items()],routes=log),open(dst.replace('.kicad_pcb','_gapfix.json'),'w'),indent=0)
# zero-length pieces from the router output are deleted by text edit, then refill + DRC
import re
L=open(cur,encoding='utf-8').read().split('\n');n0=len(L)
L=[l for l in L if not (lambda m:m and m.group(1)==m.group(3) and m.group(2)==m.group(4))(re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)',l))]
open(cur,'w',encoding='utf-8').write('\n'.join(L));print('zero-length deleted:',n0-len(L))
B=p.LoadBoard(cur);finish(B,dst)
