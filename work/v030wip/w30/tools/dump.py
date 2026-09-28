import sys,json,pcbnew as p
b=p.LoadBoard(sys.argv[1]);mm=p.ToMM
out={'pads':[],'tracks':[],'vias':[]}
for f in b.GetFootprints():
  for q in f.Pads():
    bb=q.GetBoundingBox();ls=[b.GetLayerName(l) for l in q.GetLayerSet().Seq() if l in (p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu)]
    out['pads'].append(dict(ref=f.GetReference(),num=q.GetNumber(),net=q.GetNetname(),x=mm(q.GetPosition().x),y=mm(q.GetPosition().y),bb=[mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())],layers=ls,th=q.GetAttribute()==p.PAD_ATTRIB_PTH))
for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):out['vias'].append(dict(x=mm(t.GetPosition().x),y=mm(t.GetPosition().y),d=mm(t.GetWidth(p.F_Cu)) if hasattr(t,'GetWidth') else .6,drill=mm(t.GetDrill()),net=t.GetNetname()))
  else:out['tracks'].append(dict(a=[mm(t.GetStart().x),mm(t.GetStart().y)],b=[mm(t.GetEnd().x),mm(t.GetEnd().y)],w=mm(t.GetWidth()),layer=b.GetLayerName(t.GetLayer()),net=t.GetNetname()))
json.dump(out,open(sys.argv[2],'w'))
print(len(out['pads']),len(out['tracks']),len(out['vias']))
