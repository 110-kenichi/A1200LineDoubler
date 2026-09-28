import json,sys
from PIL import Image,ImageDraw,ImageFont
g=json.load(open(sys.argv[1]));x0,y0,x1,y1=map(float,sys.argv[3].split(','));S=float(sys.argv[4]) if len(sys.argv)>4 else 25
hl=set(sys.argv[5].split(',')) if len(sys.argv)>5 else set()
W,H=int((x1-x0)*S),int((y1-y0)*S);im=Image.new('RGB',(W,H),(20,20,20));d=ImageDraw.Draw(im,'RGBA')
P=lambda x,y:((x-x0)*S,(y-y0)*S)
col={'In2.Cu':(230,150,40,110),'B.Cu':(60,110,255,150),'F.Cu':(230,50,50,170)}
for L in ['In2.Cu','B.Cu','F.Cu']:
  for t in g['tracks']:
    if t['layer']!=L:continue
    c=(255,255,0,230) if t['net'] in hl else col[L]
    d.line([P(*t['a']),P(*t['b'])],fill=c,width=max(1,int(t['w']*S)))
for q in g['pads']:
  l,t,r,b=q['bb'];c=(255,255,0,200) if q['net'] in hl else ((200,200,200,160) if 'F.Cu' in q['layers'] else (100,100,255,160))
  d.rectangle([P(l,t),P(r,b)],outline=c,width=1)
  if (r-l)*S>14: d.text(P(l+.05,t+.02),q['num'],fill=(255,255,255))
for v in g['vias']:
  x,y=P(v['x'],v['y']);rr=v['d']/2*S;c=(255,255,0,255) if v['net'] in hl else (200,200,200,255)
  d.ellipse([x-rr,y-rr,x+rr,y+rr],outline=c,width=2)
# labels for refs
seen={}
for q in g['pads']:seen.setdefault(q['ref'],[]).append((q['x'],q['y']))
for ref,pts in seen.items():
  x=sum(p[0] for p in pts)/len(pts);y=sum(p[1] for p in pts)/len(pts)
  if x0<x<x1 and y0<y<y1:d.text(P(x,y),ref,fill=(0,255,120))
for gx in range(int(x0),int(x1)+1):
  if gx%5==0:d.line([P(gx,y0),P(gx,y1)],fill=(80,80,80,90));d.text(P(gx,y0),str(gx),fill=(150,150,150))
for gy in range(int(y0),int(y1)+1):
  if gy%5==0:d.line([P(x0,gy),P(x1,gy)],fill=(80,80,80,90));d.text(P(x0,gy),str(gy),fill=(150,150,150))
im.save(sys.argv[2])
