import sys,json,subprocess,time
sys.path.insert(0,'/home/claude/tools')
cur,out,order_json,blocks_json,opts=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
P=json.load(open('/tmp/r/buspins.json'))
order=json.loads(order_json)
code=r'''
import sys,json;sys.path.insert(0,'/home/claude/tools')
from router import Router
brd,net,a,z,blocks,opts=sys.argv[1],sys.argv[2],json.loads(sys.argv[3]),json.loads(sys.argv[4]),json.loads(sys.argv[5]),json.loads(sys.argv[6])
r=Router(brd,tuple(opts.get('region',[12,30,62,66])))
for g,ls in blocks:r.block(tuple([g[0]]+[tuple(x) if isinstance(x,list) else x for x in g[1:]]),set(ls) if ls!="all" else "all")
r.build(r.b.FindNet(net).GetNetCode())
res=r.route(tuple(a),'F.Cu',tuple(z),'F.Cu',via_cost=opts.get('via',25),turn=opts.get('turn',0.4),layer_cost=opts.get('lc'),free_a=2,free_z=2)
print(json.dumps(res))
'''
open('/tmp/r/_rone.py','w').write(code)
for k,net in enumerate(order):
    a=list(P[net]['U1']);z=list(P[net]['U2'])
    t=time.time()
    r=subprocess.run(['/opt/kicad/squashfs-root/bin/python3','/tmp/r/_rone.py',cur,net,json.dumps(a),json.dumps(z),blocks_json,json.dumps(opts)],capture_output=True,text=True)
    line=[l for l in r.stdout.split('\n') if l.startswith('{') or l=='null']
    res=json.loads(line[-1]) if line else None
    if not res:print(net,'FAILED',round(time.time()-t));continue
    L=sum(abs(p2[0]-p1[0])+abs(p2[1]-p1[1]) for L_,pts in res['segments'] for p1,p2 in zip(pts,pts[1:]))
    print(net,'ok vias',len(res['vias']),'len~',round(L,1),'t',round(time.time()-t),flush=True)
    res['segments'][0][1].insert(0,a);res['segments'][-1][1].append(z)
    json.dump([[net,0.15,res]],open('/tmp/r/_one.json','w'))
    nxt='/tmp/r/_bus.kicad_pcb'
    subprocess.run(['python3','/tmp/s/apply_multi.py',cur,nxt,'/tmp/r/_one.json'],check=True)
    subprocess.run(['cp',nxt,out]);cur=out
subprocess.run(['cp','/tmp/r/r1.kicad_pro',out.replace('.kicad_pcb','.kicad_pro')])
