import json,math,sys
def clusters(g,ref,stop_at_via=True):
    pads=[q for q in g['pads'] if q['ref']==ref]
    out={}
    for q in pads:
        l,t,r,b=q['bb'];net=q['net']
        inpad=lambda p:l-.01<=p[0]<=r+.01 and t-.01<=p[1]<=b+.01
        segs=set();vias=set();front=[]
        for i,s in enumerate(g['tracks']):
            if s['net']==net and s['layer'] in q['layers'] and (inpad(s['a']) or inpad(s['b'])):segs.add(i);front+= [tuple(s['a']),tuple(s['b'])]
        seen=set()
        while front:
            p=front.pop()
            if p in seen:continue
            seen.add(p)
            vhit=[j for j,v in enumerate(g['vias']) if v['net']==net and math.dist((v['x'],v['y']),p)<.01]
            if vhit:vias.update(vhit);continue
            # stop at other pads
            if any(o['net']==net and o is not q and o['bb'][0]-.01<=p[0]<=o['bb'][2]+.01 and o['bb'][1]-.01<=p[1]<=o['bb'][3]+.01 for o in g['pads']):continue
            for i,s in enumerate(g['tracks']):
                if i in segs or s['net']!=net or s['layer']!='F.Cu':continue
                if math.dist(s['a'],p)<.01 or math.dist(s['b'],p)<.01:segs.add(i);front+=[tuple(s['a']),tuple(s['b'])]
        out[q['num']]=(net,sorted(segs),sorted(vias))
    return out
if __name__=='__main__':
    g=json.load(open(sys.argv[1]))
    for ref in sys.argv[2].split(','):
        for num,(net,segs,vias) in clusters(g,ref).items():
            print(ref,num,net,'segs',[(g['tracks'][i]['a'],g['tracks'][i]['b']) for i in segs],'vias',[(g['vias'][j]['x'],g['vias'][j]['y']) for j in vias])
