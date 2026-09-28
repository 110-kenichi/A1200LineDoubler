import sys;sys.path.insert(0,'/home/claude/tools')
from pcbedit import Board
b=Board(sys.argv[1])
nets=[f'ADC_G{i}' for i in range(8)]+[f'ADC_B{i}' for i in range(8)]
u1x=[32.0,31.5,31.0,30.5,30.0,29.5,29.0,28.5,25.0,24.5,24.0,23.5,23.0,22.5,22.0,21.5]
u2x=[46.2,46.6,47.0,47.4,47.8,48.2,48.6,49.0,49.4,49.8,50.6,51.0,51.4,51.8,52.2,52.6]
for j,net in enumerate(nets):
    x0=u1x[j];sx=x0+(.45 if j<8 else 0);h=51.6+.4*j;X=u2x[j]
    cB=.3+.234*(j if j<8 else j-8);cC=.3+.234*j
    pts=[(x0,49.65),(x0,50.4)]
    if sx!=x0:pts.append((sx,50.4+(sx-x0)))
    pts+=[(sx,h-cB),(sx+cB,h),(X-cC,h),(X,h-cC),(X,46.95)]
    b.add_path(net,[(round(x,4),round(y,4)) for x,y in pts])
b.save(sys.argv[2])
