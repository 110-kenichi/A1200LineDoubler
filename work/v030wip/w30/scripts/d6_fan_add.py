# Issue 6 / step 3 (pcbnew): DAC bus fan U2 -> U3 (R/G/B, BLANK), U3-side power re-connection, R10/R14/R24/R44 moves.
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'../tools') if 'scripts' in os.path.abspath(__file__) else os.environ.get('W30TOOLS','.'))
import pcbnew as p;from pcbk7 import V,path,via,finish
b=p.LoadBoard(sys.argv[1]);mm=p.ToMM
def place(ref,x,y,rot):f=b.FindFootprintByReference(ref);f.SetPosition(V(x,y));f.SetOrientationDegrees(rot);return f
def padpos(ref,num):
    q=[q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber()==str(num)][0];return (round(mm(q.GetPosition().x),4),round(mm(q.GetPosition().y),4))
def place_p1(ref,x,y,rot,side):                       # rotate so pad1 lies on the wanted side (N/S/E/W)
    for r in (rot,rot+180):
        place(ref,x,y,r%360);a=padpos(ref,1);c=padpos(ref,2)
        if {'N':a[1]<c[1],'S':a[1]>c[1],'E':a[0]>c[0],'W':a[0]<c[0]}[side]:return a,c
PW=0.25;DP=0.36                                        # power stub width, fan pitch
TOPY=36.625                                            # U2 top pad north end
UX=lambda k:round(54.2-0.4*(k-23),3)                  # U2 top pin x
RY=lambda k:round(46.2-0.4*(k-1),3)                   # U2 right pin y
# ---- top edge: pins 25..42 north to their row, east to their column, down to U3
rows={k:round(35.3-DP*(k-25),3) for k in range(25,43)}
col={}
col[26]=65.12;col[25]=64.76                            # B0,B1
col[27]=65.48                                          # BLANK
for j in range(8):col[35-j]=round(65.84+DP*(7-j),3)       # G7(28)=65.84 .. G0(35)=68.36
for i in range(1,8):col[42-(i-1)]=round(74.75-0.5*i,3)  # R1(42)=74.25 .. R7(36)=71.25
Y3G=lambda j:round(40.25+0.5*j,3)                      # U3 left pads G0..G7
YB=lambda i:round(47.65+DP*i,3)                        # B run rows
BN=lambda i:'DAC_B%d'%i
def brun(i,x):                                         # from column x at its row east, 45deg up to U3 bottom pad
    y=YB(i);xd=round(72.4+0.14*i,3);xp=round(72.75+0.5*i,3)
    return [(x,y),(xd,y),(xp,47.3),(xp,46.163)]
for k in range(25,43):
    x0=UX(k);y=rows[k];x=col[k];pts=[(x0,TOPY),(x0,y),(x,y)]
    if k in(25,26):i=26-k;path(b,BN(i),pts+brun(i,x));continue
    if k==27:
        path(b,'DAC_BLANK_N',pts+[(x,44.25),(69.838,44.25)])
        continue
    if 28<=k<=35:j=35-k;path(b,'DAC_G%d'%j,pts+[(x,Y3G(j)),(69.838,Y3G(j))]);continue
    i=43-k;path(b,'DAC_R%d'%i,pts+[(x,37.837)])        # R1..R7
# R0: from the B.Cu riser via (46.04,29.0)
y0=round(rows[42]-DP,3);path(b,'DAC_R0',[(46.04,29.0),(46.04+29.0-y0,y0),(74.75,y0),(74.75,37.837)])
# ---- right edge: pins 20..15 = B2..B7 east to columns 64.4..62.6, then down to the B run
for i in range(2,8):
    k=22-i;x=round(62.6+DP*(7-i),3);y=RY(k)
    path(b,BN(i),[(54.95,y),(x,y)]+brun(i,x))
# ---- pocket west of U3: R14 (BLANK pull-down) over C44 (pin13 VAA decap)
a,g=place_p1('R14',66.9,45.05,0,'W')
path(b,'DAC_BLANK_N',[(a[0],44.25),a]);path(b,'GND',[g,(68.4,g[1]),(68.638,44.95)],w=PW)   # GND to pin12's via
v,g2=place_p1('C44',66.9,46.55,0,'E')
path(b,'DAC_3V3',[v,(71.25,v[1])],w=PW)                                                   # into pin13
path(b,'GND',[g2,(66.85,45.825),(67.5,45.3)],w=0.2)                                         # to R14.2
# ---- U3 power pins re-connected inward (under the body)
path(b,'GND',[(69.838,39.25),(71.35,39.25),(71.4,39.2)],w=0.2);path(b,'GND',[(69.838,39.75),(70.85,39.75),(71.4,39.2)],w=0.2);via(b,'GND',(71.4,39.2),0.6)
path(b,'GND',[(71.75,46.163),(71.75,45.1),(72.0,44.85)],w=0.2);path(b,'GND',[(72.25,46.163),(72.25,45.1),(72.0,44.85)],w=0.2);via(b,'GND',(72.0,44.85),0.55)
path(b,'DAC_3V3',[(71.25,46.163),(71.25,44.55),(71.2,44.5)],w=0.2);via(b,'DAC_3V3',(71.2,44.5),0.55)
path(b,'DAC_3V3',[(71.2,44.5),(71.2,48.15),(70.8,48.55)],'In2.Cu',w=0.4)
# ---- DAC_CLK: U3.24 -> R24 (moved south of the B run) -> U6.4
a,c=place_p1('R24',72.6,51.6,0,'W')                    # pad1 DAC_CLK_BUF west, pad2 DAC_CLK east
path(b,'DAC_CLK',[(76.75,46.163),(76.75,47.3),(c[0],round(124.05-c[0],3)),c])
u4=padpos('U6',4);path(b,'DAC_CLK_BUF',[a,(u4[0]+0.3,a[1]+a[0]-u4[0]-0.3),(u4[0]+0.3,u4[1]),u4])
# ---- R10 (RSET) out of the R columns
a,g=place_p1('R10',75.7,33.8,90,'S')
path(b,'DAC_RSET',[(76.2,34.85),(75.975,a[1]),a])
path(b,'GND',[g,(g[0],g[1]-0.9)],w=PW);via(b,'GND',(g[0],g[1]-0.9),0.6)
# ---- R44 (PSAVE pull-down) in the pocket between the B1 row and the B2 row; PSAVE B.Cu extended north
a,g=place_p1('R44',62.4,36.95,0,'E')
path(b,'DAC_PSAVE_N',[a,(a[0]+0.275,a[1]),(63.95,a[1]+0.725-0.275),(63.95,37.9)]);via(b,'DAC_PSAVE_N',(63.95,37.9))
path(b,'DAC_PSAVE_N',[(63.75,39.8),(63.75,38.1),(63.95,37.9)],'B.Cu')
path(b,'GND',[g,(g[0],36.0)],w=PW);via(b,'GND',(g[0],36.0),0.6)
# ---- decoupling re-placed
import json
o=json.load(open(sys.argv[1]+'.c42.json'))
f=p.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0402_1005Metric');f.SetParent(b)
f.SetReference('C42');f.SetValue(o['value']);f.SetPath(p.KIID_PATH(o['path']))
for k,x in o['props'].items():f.SetProperty(k,x)
b.Add(f)
for q in f.Pads():q.SetNet(b.FindNet(o['nets'][q.GetNumber()]))
fr=f.Reference();fr.SetTextSize(p.VECTOR2I(p.FromMM(0.5),p.FromMM(0.5)));fr.SetTextThickness(p.FromMM(0.08))
a,c=place_p1('C42',77.35,48.12,90,'N')                  # 0402 in U3's SE corner: COMP north, VAA south on the FB4 feed via
path(b,'DAC_COMP',[a,(77.55,a[1]-0.2),(77.55,46.75)],w=0.2);via(b,'DAC_COMP',(77.55,46.75))
path(b,'DAC_COMP',[(75.65,44.4),(77.55,46.3),(77.55,46.75)],'B.Cu')
path(b,'DAC_3V3',[c,(77.7,48.7)],w=PW)
a,g=place_p1('C29',57.2,36.3,0,'E')                    # pin22 1V2 decap on the end via of the In2 1V2 run
path(b,'1V2',[a,(58.0,a[1]+0.225),(58.0,37.225)],w=PW)
path(b,'GND',[g,(55.55,g[1])],w=PW);via(b,'GND',(55.55,g[1]),0.6)
a,g=place_p1('C35',44.4,33.2,0,'E')                    # 3V3 decaps stacked on C36's plane vias
a4,g4=place_p1('C40',44.4,31.3,0,'E')
path(b,'3V3',[(45.175,a4[1]),(45.175,34.1)],w=0.3);path(b,'GND',[(43.625,g4[1]),(43.625,34.1)],w=0.3)
finish(b,sys.argv[2],drc=len(sys.argv)<4)
