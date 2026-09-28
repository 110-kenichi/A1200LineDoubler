import pcbnew as p,sys,math,json
b=p.LoadBoard(sys.argv[1]);mm=p.ToMM
ignore=set(sys.argv[2].split(','));w,h=map(float,sys.argv[3].split(','));cx,cy=map(float,sys.argv[4].split(','));R=float(sys.argv[5]) if len(sys.argv)>5 else 6
boxes=[]
for f in b.GetFootprints():
    if f.GetReference() in ignore:continue
    try:
        cy_=f.GetCourtyard(p.F_CrtYd);bb=cy_.BBox()
        boxes.append((f.GetReference(),mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
    except Exception as e:
        bb=f.GetBoundingBox(False,False);boxes.append((f.GetReference(),mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
res=[]
for i in range(-int(R/0.1),int(R/0.1)+1):
    for j in range(-int(R/0.1),int(R/0.1)+1):
        x=cx+i*0.1;y=cy+j*0.1
        l,t,r,bm=x-w/2,y-h/2,x+w/2,y+h/2
        if l<1 or t<1 or r>94 or bm>94:continue
        if any(not(r<=B[1] or l>=B[3] or bm<=B[2] or t>=B[4]) for B in boxes):continue
        res.append((round(math.hypot(x-cx,y-cy),2),round(x,2),round(y,2)))
res.sort();print(res[:10])
