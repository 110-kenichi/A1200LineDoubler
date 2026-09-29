# J1/J2 -> HYC06-HDR15B-060, step 3: A* (tools/router7.py) from the new THT pins to the cut ends left by jc_rm.py.
# usage: python3 jc_route.py in.kicad_pcb out.kicad_pcb [order]
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools'))
from router7 import Router
import pcbnew as p
from pcbk7 import path as addpath,via as addvia
R1=(0,24,18,62);R2=(77,24,95,62)
# (net, pad centre, start layer, target, target layer, region)
JOBS={'H_IN':((3.08,41.735),'F.Cu',(11.175,53.5),'F.Cu',R1),'V_IN':((3.08,39.445),'F.Cu',(11.5,58.4),'F.Cu',R1),
      'R_IN':((7.04,46.315),'F.Cu',(11.15,38.0),'F.Cu',R1),'G_IN':((7.04,44.025),'F.Cu',(11.2,47.5),'F.Cu',R1),
      'B_IN':((7.04,41.735),'F.Cu',(11.175,51.5),'F.Cu',R1),
      'H_OUT':((91.92,42.265),'F.Cu',(83.3,46.375),'F.Cu',R2),'V_OUT':((91.92,44.555),'F.Cu',(83.5,50.675),'F.Cu',R2),
      'R_OUT':((87.96,37.685),'F.Cu',(82.55,38.75),'F.Cu',R2),'G_OUT':((87.96,39.975),'F.Cu',(82.5,43.3),'F.Cu',R2),
      'B_OUT':((87.96,42.265),'F.Cu',(81.9,48.1),'F.Cu',R2)}
VIAEND=set()  # all targets are F.Cu ends (jc_rm.py drops the old V_IN/H_OUT vias)
order=sys.argv[3].split(',') if len(sys.argv)>3 else list(JOBS)
cur=sys.argv[1];out=[];tmp=sys.argv[2].replace('.kicad_pcb','_step.kicad_pcb')
for net in order:
    a,la,z,lz,reg=JOBS[net]
    r=Router(cur,reg,width=0.15);r.build(r.b.FindNet(net).GetNetCode())
    # THT pins (and target vias) exist on both layers: try every start/end layer and keep the cheapest route.
    best=None
    for LA in ('F.Cu','B.Cu'):
        for LZ in ((lz,) if lz=='F.Cu' and net not in VIAEND else ('F.Cu','B.Cu')):
            q=r.route(a,LA,z,LZ,via_cost=40,turn=0.5,free_a=12,free_z=4,layer_cost={'F.Cu':1.0,'B.Cu':1.3})
            if q and (best is None or q['cost']<best['cost']):best=q
    res=best
    if not res:print(net,'FAILED',flush=True);continue
    print(net,res['segments'],res['vias'],flush=True)
    b=p.LoadBoard(cur);segs=[]
    for k,(L,pts) in enumerate(res['segments']):
        pts=[tuple(q) for q in pts]
        if k==0 and pts[0]!=a:pts=[a]+pts
        if k==len(res['segments'])-1 and pts[-1]!=z:pts=pts+[z]
        segs.append((L,pts))
        if len(pts)>1:addpath(b,net,pts,L)
    for v in res['vias']:addvia(b,net,tuple(v))
    p.SaveBoard(tmp,b);cur=tmp
    out.append({'net':net,'segments':segs,'vias':res['vias']})
json.dump(out,open(sys.argv[2].replace('.kicad_pcb','_routes.json'),'w'),indent=0)
b=p.LoadBoard(cur);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(sys.argv[2],b)
p.WriteDRCReport(b,sys.argv[2].replace('.kicad_pcb','_drc.txt'),p.EDA_UNITS_MILLIMETRES,True)
