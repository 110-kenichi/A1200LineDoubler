import sys;sys.path.insert(0,'/home/claude/tools')
from pcbedit import Board
b=Board(sys.argv[1])
ypin=[42.0,42.5,43.0,44.0,44.5,45.0,45.5,46.0]
yk=[42.05,42.5,43.0,44.1,44.5,45.0,45.5,46.0]
for k in range(8):
    Y=39.0+.4*k;const=79.0+.6*k;a=const-yk[k];xe=const-Y
    pts=[(33.65,ypin[k]),(34.4,ypin[k])]
    if yk[k]!=ypin[k]:pts.append((34.4+abs(yk[k]-ypin[k]),yk[k]))
    pts+=[(a,yk[k]),(xe,Y),(45.05,Y)]
    b.add_path(f'ADC_R{k}',[(round(x,4),round(y,4)) for x,y in pts])
b.save(sys.argv[2])
