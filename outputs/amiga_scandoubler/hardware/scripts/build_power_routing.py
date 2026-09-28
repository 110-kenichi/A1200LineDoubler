from pathlib import Path
import pcbnew as p,json
out=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(out/'amiga_scandoubler_placement.kicad_pcb'))
fp={f.GetReference():f for f in board.GetFootprints()}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pad(ref,num):return next(a for a in fp[ref].Pads() if a.GetNumber()==str(num))
def xy(a):return (p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y))
def place(ref,x,y,angle):
    f=fp[ref];f.SetOrientationDegrees(angle);f.SetPosition(pt(x,y))
    f.Reference().SetPosition(pt(x,y-1.8));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
def route(net,points,width=.25,layer=p.F_Cu):
    for a,z in zip(points,points[1:]):
        if a==z:continue
        t=p.PCB_TRACK(board);t.SetStart(pt(*a));t.SetEnd(pt(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNetCode(net);board.Add(t)
def via(net,x,y):
    v=p.PCB_VIA(board);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(net);board.Add(v)
def conn(a,z,mid=(),width=.25):
    aa=pad(*a);zz=pad(*z);assert aa.GetNetCode()==zz.GetNetCode(),(a,z)
    route(aa.GetNetCode(),[xy(aa),*mid,xy(zz)],width)
place('F1',47.5,82,0);place('C54',53,82,0);place('R33',38,77.8,0);place('R35',38,84,0)
place('R25',41,84.8,180);place('R26',54.5,84.8,0);place('R34',61,64.5,0)
for i,x in enumerate([25,47.5,70]):
    y=73;u=f'U{7+i}';l=f'L{i+1}';ci=f'C{55+2*i}';co=f'C{56+2*i}';rt=f'R{27+2*i}';rb=f'R{28+2*i}'
    def a(dx,dy):return (x+dx,y+dy)
    place(u,x,y,0);place(l,*a(4.5,-.25),0);place(ci,*a(-3.5,-.25),180);place(co,*a(9,-.25),0)
    if i==2:place(ci,*a(-4,-.25),180)
    place(rt,*a(3,3),180);place(rb,*a(0,3),180)
    # Small pin escapes expand outside the 0.5-mm-pitch WSON land row.
    conn((u,2),(ci,1),width=.25)
    if i<2:conn((u,2),(u,3),[a(-1.6,-.25),a(-1.6,.25)],.2)
    conn((u,7),(l,1),[a(1.55,-.25)],.25)
    conn((l,2),(co,1),width=.8)
    # Sense after the inductor, at output capacitor; keep below SW.
    conn((u,6),(co,1),[a(1.8,.25),a(1.8,2.2),a(8.05,2.2)],.2)
    conn((rt,1),(co,1),[a(8.05,3),a(8.05,2.2)],.2)
    conn((u,5),(rt,2),[a(1.25,.75),a(1.25,3)],.2)
    conn((rb,1),(rt,2),width=.2)
    # Power and quiet grounds return locally; inner GND is filled below.
    conn((u,1),(u,9),[a(-.5,-.75)],.2)
    conn((u,4),(u,9),[a(-.5,.75)],.2)
    conn((u,1),(ci,2),[a(-1.4,-.75),a(-1.4,-1.8),a(-4.45,-1.8)],.2)
    conn((co,2),(ci,2),[a(10.3,-.25),a(10.3,-3.3),a(-5.2,-3.3),a(-5.2,-.25)],.6)
    g=pad(u,1).GetNetCode()
    for dx,dy in [(-5.2,-.25),(10.3,-.25),(-1.4,-1.8),(-.825,4)]:via(g,*a(dx,dy))
    route(g,[xy(pad(rb,2)),a(-.825,4)],.3)
    # Dedicated quiet-ground link to AGND, on back copper with ground vias.
    agy=1.5 if i==2 else 1.1
    via(g,*a(-1.6,agy));route(g,[xy(pad(u,4)),a(-1.6,agy)],.2)
    route(g,[a(-.825,4),a(-1.6,4),a(-1.6,agy)],.3,p.B_Cu)
# Protected 5-V distribution.
five=pad('F1',2).GetNetCode()
route(five,[(22.45,80),(67.45,80)],.8)
for ci,x in [('C55',25),('C57',47.5),('C59',70)]:
    position=xy(pad(ci,1));route(five,[position,(position[0],80)],.6)
route(five,[xy(pad('F1',2)),(50.5,82),(50.5,80)],.8)
conn(('F1',2),('C54',1),width=.8)
g=pad('C54',2).GetNetCode();route(g,[xy(pad('C54',2)),(54.8,82)],.6);via(g,54.8,82)
# USB VBUS contacts share back-side feed to the fuse. CC lines stay on front.
vbus=pad('F1',1).GetNetCode()
for number,x in [('A4',45.05),('A9',49.95)]:
    route(vbus,[xy(pad('J3',number)),(x,86.3)],.4);via(vbus,x,86.3)
route(vbus,[(45.05,86.3),(49.95,86.3)],.8,p.B_Cu)
route(vbus,[(45.05,86.3),(45.05,83),(44.3,82)],.8,p.B_Cu)
via(vbus,44.3,82);route(vbus,[(44.3,82),xy(pad('F1',1))],.8)
conn(('J3','A5'),('R25',1),[(46.25,85.5),(41.825,85.5)],.2)
conn(('J3','B5'),('R26',1),[(49.25,85.5),(53.675,85.5)],.2)
for ref in ['R25','R26']:
    position=xy(pad(ref,2));route(g,[position,(position[0],85.8)],.3);via(g,position[0],85.8)
for number,x in [('A1',43.6),('A12',51.4)]:
    route(g,[xy(pad('J3',number)),(x,87.305),(x,86.3)],.3);via(g,x,86.3)
# 3V3 PG enables the 1V2 regulator; both lower-rail PG outputs share POWER_GOOD.
pg=pad('U7',8).GetNetCode()
route(pg,[xy(pad('R35',1)),(37.175,83)],.2);via(pg,37.175,83)
route(pg,[(37.175,78.5),(37.175,83)],.2,p.B_Cu)
for ref,point in [('U7',(26.5,71)),('U8',(49,71)),('U9',(71.5,71))]:
    q=pad(ref,8);route(q.GetNetCode(),[xy(q),(point[0],72.25),point],.2);via(q.GetNetCode(),*point)
route(pg,[xy(pad('R33',1)),(37.175,76.6)],.2);via(pg,37.175,76.6)
route(pg,[(26.5,71),(37.175,71),(37.175,78.5),(70,78.5),(70,73.4),(68.3,73.4)],.2,p.B_Cu)
via(pg,68.3,73.4);route(pg,[(68.3,73.4),xy(pad('U9',3))],.2)
good=pad('U8',8).GetNetCode()
route(good,[(49,71),(49,67.5),(71.5,67.5),(71.5,71)],.2,p.B_Cu)
via(good,60.175,65.7);route(good,[(60.175,65.7),(60.175,67.5)],.2,p.B_Cu)
route(good,[(60.175,65.7),xy(pad('R34',1))],.2)
rail=pad('C56',1).GetNetCode()
for xx,yy in [(33.05,75.2),(38.825,76.6),(61.825,63.3)]:via(rail,xx,yy)
route(rail,[xy(pad('R33',2)),(38.825,76.6)],.2)
route(rail,[xy(pad('R34',2)),(61.825,63.3)],.2)
route(rail,[(33.05,75.2),(61.825,75.2),(61.825,63.3)],.3,p.In2_Cu)
route(rail,[(38.825,75.2),(38.825,76.6)],.3,p.In2_Cu)
route(g,[xy(pad('R35',2)),(39.7,84)],.3);via(g,39.7,84)
# Continuous inner reference plane, 1 mm inside the board boundary.
z=p.ZONE(board);z.SetLayer(p.In1_Cu);z.SetNetCode(g);z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
poly=z.Outline();poly.NewOutline()
for x,y in [(1,1),(94,1),(94,94),(1,94)]:poly.Append(int(p.FromMM(x)),int(p.FromMM(y)))
board.Add(z);p.ZONE_FILLER(board).Fill(board.Zones())
for t in board.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetText()=='PLACEMENT STUDY - UNROUTED':t.SetText('PARTIAL POWER ROUTING - REVIEW ONLY')
name=out/'amiga_scandoubler_routing.kicad_pcb';board.SetFileName(str(name));p.SaveBoard(str(name),board)
print('Saved',name,'tracks/vias',len(list(board.GetTracks())))
