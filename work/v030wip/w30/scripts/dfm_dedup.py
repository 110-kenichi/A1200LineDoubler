# Clean-up: same-net tracks that run over each other (duplicates, near-parallel copies 0.05 mm apart, left-overs of
# earlier routes). A track of an overlapping pair is deleted only if the net's pad connectivity (which pads share an
# island; vias of GND/3V3 count as tied together by the planes) is unchanged without it. Pieces that become dangling
# (end not on a pad / via land / another track's end, like KiCad) are deleted too. Deletions by text edit.
# usage: dfm_dedup.py in.kicad_pcb out.kicad_pcb
import sys,os,re,json
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
import pcbnew as p
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
mm=p.ToMM;PLANE={'GND','3V3'}
src,dst=sys.argv[1:3];work=dst.replace('.kicad_pcb','_rm.kicad_pcb')
def ppoly(q):
    o=q.GetEffectivePolygon().Outline(0);return Polygon([(mm(o.CPoint(i).x),mm(o.CPoint(i).y)) for i in range(o.PointCount())])
b=p.LoadBoard(src)
pads={};vias={};trks=[]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.GetNetname():pads.setdefault(q.GetNetname(),[]).append((f.GetReference()+'.'+q.GetNumber(),{b.GetLayerName(l) for l in q.GetLayerSet().Seq()},ppoly(q)))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):vias.setdefault(t.GetNetname(),[]).append(Point(mm(t.GetPosition().x),mm(t.GetPosition().y)).buffer(mm(t.GetWidth())/2,12))
    else:
        a=(round(mm(t.GetStart().x),4),round(mm(t.GetStart().y),4));z=(round(mm(t.GetEnd().x),4),round(mm(t.GetEnd().y),4))
        trks.append(dict(net=t.GetNetname(),L=t.GetLayerName(),a=a,z=z,w=mm(t.GetWidth()),g=LineString([a,z]).buffer(mm(t.GetWidth())/2,8) if a!=z else Point(a).buffer(mm(t.GetWidth())/2,8),dead=False))
def partition(net):
    it=[('pad',n,ls,g) for n,ls,g in pads.get(net,[])]+[('via',None,{'F.Cu','In1.Cu','In2.Cu','B.Cu'},g) for g in vias.get(net,[])]+[('trk',None,{t['L']},t['g']) for t in trks if t['net']==net and not t['dead']]
    par=list(range(len(it)))
    def fd(i):
        while par[i]!=i:par[i]=par[par[i]];i=par[i]
        return i
    T=STRtree([x[3] for x in it])
    for i,x in enumerate(it):
        for j in T.query(x[3]):
            if j>i and x[2]&it[j][2] and x[3].intersects(it[j][3]):par[fd(i)]=fd(j)
        if net in PLANE and x[0]=='via':par[fd(i)]=fd(next(k for k,y in enumerate(it) if y[0]=='via'))
    groups={}
    for i,x in enumerate(it):
        if x[0]=='pad':groups.setdefault(fd(i),set()).add(x[1])
    return sorted(sorted(g) for g in groups.values())
# overlapping same-net pairs
T=STRtree([t['g'] for t in trks]);pairs=[]
for i,t in enumerate(trks):
    for j in T.query(t['g']):
        if j<=i:continue
        u=trks[j]
        if u['net']!=t['net'] or u['L']!=t['L']:continue
        ov=t['g'].intersection(u['g']).area;w=max(t['w'],u['w'])
        if ov>w*w*1.6:pairs.append((i,j))
print('overlapping pairs:',len(pairs))
base={}
removed=[]
for i,j in pairs:
    if trks[i]['dead'] or trks[j]['dead']:continue
    net=trks[i]['net']
    if net not in base:base[net]=partition(net)
    # try the shorter (then the longer) of the pair
    for k in sorted((i,j),key=lambda k:trks[k]['g'].length):
        trks[k]['dead']=True
        if partition(net)==base[net]:removed.append(k);break
        trks[k]['dead']=False
print('overlap copies removed:',len(removed))
# dangling clean-up (repeat)
nd=0;keep=set()
while True:
    ends={};dead=[]
    live=[k for k,t in enumerate(trks) if not t['dead']]
    for k in live:
        t=trks[k];ends.setdefault((t['net'],t['L']),[]).extend([(k,t['a']),(k,t['z'])])
    for k in live:
        t=trks[k]
        for e in (t['a'],t['z']):
            pt=Point(e)
            inpad=any(t['L'] in ls and g.buffer(0.005).contains(pt) for _,ls,g in pads.get(t['net'],[]))
            invia=any(g.buffer(0.005).contains(pt) for g in vias.get(t['net'],[]))
            # on another live track of the same net/layer (its end point or a T onto its centre line)
            onend=any(kk!=k and LineString([trks[kk]['a'],trks[kk]['z']]).distance(pt)<=trks[kk]['w']/2 if trks[kk]['a']!=trks[kk]['z'] else False
                      for kk in {kk for kk,_ in ends[(t['net'],t['L'])]})
            if not(inpad or invia or onend):dead.append(k);break
    dead=[k for k in dead if k not in keep]
    if not dead:break
    for k in dead:   # each deletion must keep the net's pad connectivity, else the piece stays
        net=trks[k]['net']
        if net not in base:base[net]=partition(net)
        trks[k]['dead']=True
        if partition(net)!=base[net]:trks[k]['dead']=False;keep.add(k)
        else:nd+=1
print('dangling pieces removed:',nd)
for net in base:assert partition(net)==base[net],net
# text edit: remove every dead segment (all copies of identical ones are dead together or kept)
from pcbk7 import finish
shortened=[]
def write():
    L=open(src,encoding='utf-8').read().split('\n')
    kill={}
    for t in trks:
        if t['dead']:kill[(t['net'],t['L'],t['a'],t['z'])]=kill.get((t['net'],t['L'],t['a'],t['z']),0)+1
    nets={m.group(2):int(m.group(1)) for l in L for m in [re.match(r'\s*\(net (\d+) "(.*)"\)$',l)] if m};inv={v:k for k,v in nets.items()}
    out=[];n=0
    for l in L:
        m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net (\d+)\)',l)
        if m:
            k=(inv[int(m.group(6))],m.group(5),(round(float(m.group(1)),4),round(float(m.group(2)),4)),(round(float(m.group(3)),4),round(float(m.group(4)),4)))
            if kill.get(k,0)>0:kill[k]-=1;n+=1;continue
            for net,Lr,old,new in shortened:
                if (net,Lr)==k[:2] and (old==k[2:] or old==k[2:][::-1]):
                    f=lambda v:('%.4f'%v).rstrip('0').rstrip('.')
                    l=re.sub(r'\(start [-\d.]+ [-\d.]+\) \(end [-\d.]+ [-\d.]+\)','(start %s %s) (end %s %s)'%(f(new[0][0]),f(new[0][1]),f(new[1][0]),f(new[1][1])),l,1);break
        out.append(l)
    open(work,'w',encoding='utf-8').write('\n'.join(out))
    finish(p.LoadBoard(work),dst);os.remove(work);return n
n=write()
# KiCad's own dangling report decides the rest: a reported piece is removed if pad connectivity stays the same
for rnd in range(6):
    rep=open(dst.replace('.kicad_pcb','_drc.txt'),encoding='utf-8').read()
    hits=re.findall(r'\[track_dangling\].*?\n.*?\n\s*@\(([-\d.]+) mm, ([-\d.]+) mm\): Track \[([^\]]*)\] on (\S+), length ([\d.]+) mm',rep)
    newdead=0
    for x,y,net,Lr,ln in hits:
        x,y,ln=float(x),float(y),float(ln)
        for k,t in enumerate(trks):
            if t['dead'] or t['net']!=net or t['L']!=Lr:continue
            if not any(abs(e[0]-x)<0.002 and abs(e[1]-y)<0.002 for e in (t['a'],t['z'])):continue
            if abs(((t['a'][0]-t['z'][0])**2+(t['a'][1]-t['z'][1])**2)**0.5-ln)>0.002:continue
            if net not in base:base[net]=partition(net)
            t['dead']=True
            if partition(net)!=base[net]:
                t['dead']=False
                # it still carries a connection: the dangling end (the one not on a pad / via / other track) is
                # pulled back to the centre of the nearest same-net via or pad whose copper the track touches
                def free_end(e):
                    pt=Point(e)
                    if any(Lr in ls and g.buffer(0.005).contains(pt) for _,ls,g in pads.get(net,[])):return False
                    if any(g.buffer(0.005).contains(pt) for g in vias.get(net,[])):return False
                    return not any(kk!=k and not u['dead'] and u['net']==net and u['L']==Lr and u['a']!=u['z'] and LineString([u['a'],u['z']]).distance(pt)<=u['w']/2 for kk,u in enumerate(trks))
                for e,o in ((t['a'],t['z']),(t['z'],t['a'])):
                    if not free_end(e):continue
                    cand=[g for g in vias.get(net,[])]+[g for _,ls,g in pads.get(net,[]) if Lr in ls]
                    cand=[g.centroid for g in cand if g.intersects(t['g']) and g.centroid.distance(Point(o))>0.01]
                    if not cand:continue
                    c=min(cand,key=lambda c:c.distance(Point(e)));old=(t['a'],t['z'])
                    t['a'],t['z']=(o,(round(c.x,4),round(c.y,4)))
                    t['g']=LineString([t['a'],t['z']]).buffer(t['w']/2,8)
                    if partition(net)!=base[net]:t['a'],t['z']=old;t['g']=LineString(list(old)).buffer(t['w']/2,8)
                    else:newdead+=1;shortened.append((net,Lr,old,(t['a'],t['z'])));break
            else:newdead+=1;nd+=1
            break
    print('round',rnd,'KiCad-dangling pieces removed:',newdead)
    if not newdead:break
    n=write()
print('segments deleted in file:',n)
json.dump(dict(pairs=len(pairs),removed=len(removed),dangling=nd,deleted=n),open(dst.replace('.kicad_pcb','_dedup.json'),'w'))
