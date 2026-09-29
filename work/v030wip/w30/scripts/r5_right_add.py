# Issue 5, step 2 (pcbnew): U2 right-side escape of pins 1-12 and the JTAG/config bundle to J4 + pull resistors.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p
from pcbk7 import V,MM,path,via,finish
b=p.LoadBoard(sys.argv[1])
mm=p.ToMM
def padnet(ref,num):return [q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber()==str(num)][0].GetNetname()
def place(ref,x,y,rot):
    f=b.FindFootprintByReference(ref);f.SetPosition(V(x,y));f.SetOrientationDegrees(rot);return f
def padpos(ref,num):
    q=[q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber()==str(num)][0];return (round(mm(q.GetPosition().x),4),round(mm(q.GetPosition().y),4))
PW=0.25   # power stub width

# --- 1V2: new In2 link under the right pad row (x=55.0) joining the y=37.225 run and the south diagonal
path(b,'1V2',[(55.0,37.225),(55.0,48.35)],'In2.Cu',w=0.4)
# pin 1 (1V2): short stub to a via, then In2 into the existing (55.95,47.3) run
path(b,'1V2',[(54.95,46.2),(55.6,46.2)],w=0.15);path(b,'1V2',[(55.6,46.2),(55.95,46.55),(55.95,46.75)],w=PW);via(b,'1V2',(55.95,46.75),0.6)
path(b,'1V2',[(55.95,46.75),(55.95,47.3)],'In2.Cu',w=0.4)
# pin 2 (GND): inward into the EP corner
path(b,'GND',[(54.95,45.8),(53.95,45.8),(53.4,45.25)])
# pin 12 (3V3): own plane via
path(b,'3V3',[(54.95,41.8),(55.75,41.8),(55.95,42.0)],w=0.2);via(b,'3V3',(55.95,42.0),0.6)

# --- staircase: pins 4..9 fan to vias stepping 0.55 up/right (bottom pin -> west column)
ST=[('JTAGSEL_N',45.0,55.60,56.55,45.45),('JTAG_TMS',44.6,55.70,57.10,44.90),('JTAG_TCK',44.2,55.80,58.60,44.35),
    ('JTAG_TDI',43.8,None,59.15,43.80),('JTAG_TDO',43.4,55.80,59.70,43.25),('FPGA_RECONFIG_N',43.0,55.70,60.25,42.70)]
for net,yp,xs,xv,yv in ST:
    pts=[(54.95,yp)]
    if xs is not None:pts+=[(xs,yp),(xs+abs(yv-yp),yv)]
    pts+=[(xv,yv)];path(b,net,pts);via(b,net,(xv,yv))
# pin 10 (DONE): inward to an inner via, then B.Cu under the pad row
path(b,'FPGA_DONE',[(54.95,42.6),(54.26,42.6),(53.96,42.9)]);via(b,'FPGA_DONE',(53.96,42.9))

# --- B.Cu bundle: north, 45deg NW at y=33.5, then to each J4 column
YT=33.5
COL=[('FPGA_DONE',54.80),('JTAGSEL_N',56.55),('JTAG_TMS',57.10),('JTAG_TCK',58.60),('JTAG_TDI',59.15),('JTAG_TDO',59.70),('FPGA_RECONFIG_N',60.25)]
XT={'FPGA_DONE':39.90,'JTAGSEL_N':42.40,'JTAG_TMS':44.96,'JTAG_TCK':47.50,'JTAG_TDI':50.04,'JTAG_TDO':52.58,'FPGA_RECONFIG_N':55.10}
VY_MAX=24.5
XV={'JTAG_TMS','JTAG_TCK','JTAG_TDI','JTAG_TDO','FPGA_RECONFIG_N'}   # keep F.Cu hops north of the future DAC-bus band
start={'FPGA_DONE':[(53.96,42.9),(54.8,42.06)]}
for net,y0 in [(n,yv) for n,_,_,_,yv in ST]:start[net]=None
top={}
for net,cx in COL:
    pts=start.get(net) or []
    if not pts:pts=[(cx,[yv for n,_,_,_,yv in ST if n==net][0])]
    pts+=[(cx,YT)]
    xt=XT[net];ye=round(YT-(cx-xt),4)
    pts.append((xt,ye))
    if net in XV:
        yv=min(round(ye-0.3,4),VY_MAX);pts.append((xt,yv));ye=yv   # via on the vertical, clear of the neighbour's diagonal
    path(b,net,pts,'B.Cu');via(b,net,(xt,ye));top[net]=(xt,ye)

# --- F.Cu north to J4, pull resistors beside the lines
J4={'JTAG_TMS':3,'JTAG_TCK':5,'JTAG_TDI':7,'JTAG_TDO':9,'FPGA_RECONFIG_N':10}
PULL={'JTAG_TMS':'R6','JTAG_TCK':'R5','JTAG_TDI':'R7','FPGA_RECONFIG_N':'R8'}
for net,pin in J4.items():
    xt,ye=top[net];jx,jy=padpos('J4',pin)
    if net=='FPGA_RECONFIG_N':path(b,net,[(xt,ye),(xt,jy),(jx,jy)])      # around the east end of J4 into pin 10
    else:path(b,net,[(xt,ye),(jx,jy)])
    if net in PULL:
        r=PULL[net];xr=xt+1.25;place(r,xr,18.3,90)                          # pad1 lands at y=19.125 (south)
        p1=padpos(r,1);p2=padpos(r,2)
        if p1[1]<p2[1]:place(r,xr,18.3,270);p1=padpos(r,1);p2=padpos(r,2)
        path(b,net,[(xt,p1[1]),p1])
        o=padnet(r,2);path(b,o,[p2,(p2[0],p2[1]-0.95)],w=PW);via(b,o,(p2[0],p2[1]-0.95),0.6)
# DONE -> R9, JTAGSEL -> R4 at the end of their lines
for net,r in [('FPGA_DONE','R9'),('JTAGSEL_N','R4')]:
    xt,ye=top[net];dy=1.75 if r=='R4' else 2.0;place(r,xt,ye-dy,90)   # R4 kept clear of J4's courtyard (y<=15.9)
    p1=padpos(r,1);p2=padpos(r,2)
    if p1[1]<p2[1]:place(r,xt,ye-dy,270);p1=padpos(r,1);p2=padpos(r,2)
    path(b,net,[(xt,ye),p1])
    o=padnet(r,2);path(b,o,[p2,(p2[0],p2[1]-0.95)],w=PW);via(b,o,(p2[0],p2[1]-0.95),0.6)

# --- decoupling caps moved south-east of U2 (plane-connected)
place('C31',57.6,47.2,0);a=padpos('C31',1);g=padpos('C31',2)       # pad1 1V2 west
path(b,'1V2',[(55.95,46.75),(56.4,47.2),a],w=PW)
path(b,'GND',[g,(g[0]+0.85,g[1])],w=PW);via(b,'GND',(g[0]+0.85,g[1]),0.6)
place('C37',61.3,47.2,0);a=padpos('C37',1);g=padpos('C37',2)       # pad1 3V3 west
path(b,'3V3',[a,(a[0],a[1]+0.9)],w=PW);via(b,'3V3',(a[0],a[1]+0.9),0.6)
path(b,'GND',[g,(g[0],g[1]+0.9)],w=PW);via(b,'GND',(g[0],g[1]+0.9),0.6)
# --- silk: pull-resistor references and the board title (moved out of the new resistor row)
for r,(x,y) in {'R6':(46.21,20.45),'R5':(48.75,20.45),'R7':(51.29,20.45),'R8':(56.35,20.45),'R4':(43.75,17.6),'R9':(38.35,16.6)}.items():
    f=b.FindFootprintByReference(r);t=f.Reference();t.SetTextAngleDegrees(-f.GetOrientationDegrees());t.SetPosition(V(x,y))
    t.SetTextSize(p.VECTOR2I(MM(0.6),MM(0.6)));t.SetTextThickness(MM(0.1))
for d in b.GetDrawings():
    if isinstance(d,p.PCB_TEXT) and d.GetText().startswith('AMIGA 15k'):d.SetPosition(V(73.5,25.0))
finish(b,sys.argv[2])
