# Grid A* router (F.Cu/B.Cu + through vias) using pcbnew for geometry. Usage from KiCad python.
import pcbnew as p, math, heapq, json, sys
mm=p.ToMM
CL=0.2; S=0.05; EPS=0.01
LAY={'F.Cu':p.F_Cu,'B.Cu':p.B_Cu}
class Router:
    def __init__(s,board_path,region,width=.15,via_d=.55,via_drill=.3,edge=(0,0,95,95),edge_cl=.5):
        s.b=p.LoadBoard(board_path);s.w=width;s.vd=via_d;s.vdr=via_drill
        x0,y0,x1,y1=region;s.x0=x0;s.y0=y0;s.nx=int(round((x1-x0)/S))+1;s.ny=int(round((y1-y0)/S))+1
        s.edge=edge;s.ecl=edge_cl
        s.items=[]  # (kind, net, layers(set of names or 'all'), geom)
        for f in s.b.GetFootprints():
            for q in f.Pads():
                bb=q.GetBoundingBox();ls={s.b.GetLayerName(l) for l in q.GetLayerSet().Seq()}
                shape=q.GetShape(p.F_Cu) if hasattr(q,'GetShape') else None
                hole=q.GetDrillSize().x>0
                if q.GetAttribute()==p.PAD_ATTRIB_NPTH:
                    r=mm(q.GetDrillSize().x)/2;c=(mm(q.GetPosition().x),mm(q.GetPosition().y))
                    s.items.append(('hole',-1,'all',('c',c,r)));continue
                geom=('r',(mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())))
                if q.GetAttribute()==p.PAD_ATTRIB_PTH:ls='all';s.items.append(('hole',q.GetNetCode(),'all',('c',(mm(q.GetPosition().x),mm(q.GetPosition().y)),mm(q.GetDrillSize().x)/2)))
                s.items.append(('pad',q.GetNetCode(),ls,geom))
        for t in s.b.GetTracks():
            if isinstance(t,p.PCB_VIA):
                c=(mm(t.GetPosition().x),mm(t.GetPosition().y))
                s.items.append(('via',t.GetNetCode(),'all',('c',c,mm(t.GetWidth(p.F_Cu))/2)))
                s.items.append(('hole',t.GetNetCode(),'all',('c',c,mm(t.GetDrill())/2)))
            else:
                s.items.append(('trk',t.GetNetCode(),{s.b.GetLayerName(t.GetLayer())},('s',(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y)),mm(t.GetWidth())/2)))
        s.extra=[]
    @staticmethod
    def dist(pt,g):
        x,y=pt
        if g[0]=='c':return math.hypot(x-g[1][0],y-g[1][1])-g[2]
        if g[0]=='r':
            l,t,r,b=g[1];dx=max(l-x,0,x-r);dy=max(t-y,0,y-b);return math.hypot(dx,dy)
        a,b_,hw=g[1],g[2],g[3];dx=b_[0]-a[0];dy=b_[1]-a[1];L=dx*dx+dy*dy
        u=0 if L==0 else max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/L))
        return math.hypot(x-a[0]-u*dx,y-a[1]-u*dy)-hw
    @staticmethod
    def bbox(g):
        if g[0]=='c':return (g[1][0]-g[2],g[1][1]-g[2],g[1][0]+g[2],g[1][1]+g[2])
        if g[0]=='r':return g[1]
        a,b,hw=g[1],g[2],g[3];return (min(a[0],b[0])-hw,min(a[1],b[1])-hw,max(a[0],b[0])+hw,max(a[1],b[1])+hw)
    def raster(s,mask,g,need):
        l,t,r,b=s.bbox(g);i0=max(0,math.floor((l-need-s.x0)/S));i1=min(s.nx-1,math.ceil((r+need-s.x0)/S))
        j0=max(0,math.floor((t-need-s.y0)/S));j1=min(s.ny-1,math.ceil((b+need-s.y0)/S))
        for j in range(j0,j1+1):
            y=s.y0+j*S;base=j*s.nx
            for i in range(i0,i1+1):
                if not mask[base+i] and s.dist((s.x0+i*S,y),g)<need:mask[base+i]=1
    def build(s,net):
        s.net=net;N=s.nx*s.ny;s.m={L:bytearray(N) for L in LAY};s.mv=bytearray(N)
        hw=s.w/2;vr=s.vd/2;hr=s.vdr/2
        for kind,n,ls,g in s.items+s.extra:
            if kind=='hole':
                # hole-to-copper for tracks (0.25) and hole-to-hole for vias
                need_t=.25+hw+EPS if n!=net else None
                if need_t:
                    for L in LAY:s.raster(s.m[L],g,need_t)
                s.raster(s.mv,g,.25+hr+EPS);continue
            if n==net:
                if kind=='pad' and ls!='all':s.raster(s.mv,g,vr+.05)
                continue
            for L in LAY:
                if ls=='all' or L in ls:s.raster(s.m[L],g,CL+hw+EPS)
            # via: copper on any layer (F,B,In2) ; In1 is plane
            if ls=='all' or ls & {'F.Cu','B.Cu','In2.Cu'}:s.raster(s.mv,g,CL+vr+EPS)
            if kind!='hole' and (ls=='all' or ls & {'F.Cu','B.Cu','In2.Cu','In1.Cu'}) and kind in('pad','via','trk') and (ls=='all' or 'In1.Cu' not in ls):
                pass
            # via hole to other copper
            if ls=='all' or ls & {'F.Cu','B.Cu','In2.Cu'}:s.raster(s.mv,g,.25+hr+EPS)
        # board edge
        ex0,ey0,ex1,ey1=s.edge
        for j in range(s.ny):
            y=s.y0+j*S
            for i in range(s.nx):
                x=s.x0+i*S;d=min(x-ex0,ex1-x,y-ey0,ey1-y)
                if d<s.ecl+hw+EPS:
                    for L in LAY:s.m[L][j*s.nx+i]=1
                if d<s.ecl+vr+EPS:s.mv[j*s.nx+i]=1
    def block(s,g,layers='all'):
        s.extra.append(('keep',-9,layers,g))
    def cell(s,pt):return (int(round((pt[0]-s.x0)/S)),int(round((pt[1]-s.y0)/S)))
    def route(s,a,la,z,lz,via_cost=40,turn=0.4,layer_cost=None,free_a=0,free_z=0):
        layer_cost=layer_cost or {'F.Cu':1.0,'B.Cu':1.0}
        Ls=list(LAY);A=s.cell(a);Z=s.cell(z);nx=s.nx
        dirs=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
        def free(i,j,L):
            if not(0<=i<nx and 0<=j<s.ny):return False
            if (abs(i-A[0])+abs(j-A[1])<=free_a and L==la) or (abs(i-Z[0])+abs(j-Z[1])<=free_z and L==lz):return True
            return not s.m[L][j*nx+i]
        h=lambda i,j:(max(abs(i-Z[0]),abs(j-Z[1]))+.41421*min(abs(i-Z[0]),abs(j-Z[1])))
        st=(A[0],A[1],la,-1);g={st:0};prev={};q=[(h(*A),0,st)];goal=None
        while q:
            f,c,u=heapq.heappop(q)
            if c>g[u]:continue
            i,j,L,d=u
            if (i,j)==Z and L==lz:goal=u;break
            for k,(dx,dy) in enumerate(dirs):
                ni,nj=i+dx,j+dy
                if not free(ni,nj,L):continue
                if dx and dy and not(free(i+dx,j,L) or free(i,j+dy,L)):continue
                cost=(1.41421 if dx and dy else 1)*layer_cost[L]
                if d>=0 and d!=k:
                    diff=min((k-d)%8,(d-k)%8)
                    if diff>2:continue  # no sharp (>90) turns
                    cost+=turn*diff
                v=(ni,nj,L,k);nc=c+cost
                if nc<g.get(v,1e18):g[v]=nc;prev[v]=u;heapq.heappush(q,(nc+h(ni,nj),nc,v))
            if not s.mv[j*nx+i]:
                for L2 in Ls:
                    if L2!=L and free(i,j,L2):
                        v=(i,j,L2,-1);nc=c+via_cost
                        if nc<g.get(v,1e18):g[v]=nc;prev[v]=u;heapq.heappush(q,(nc+h(i,j),nc,v))
        if not goal:return None
        path=[goal]
        while path[-1] in prev:path.append(prev[path[-1]])
        path.reverse()
        segs=[];vias=[];cur=[path[0]]
        for u in path[1:]:
            if u[2]!=cur[-1][2]:
                segs.append((cur[-1][2] if False else cur[0][2],cur));vias.append((s.x0+u[0]*S,s.y0+u[1]*S));cur=[u]
            else:cur.append(u)
        segs.append((cur[0][2],cur))
        out=[]
        for L,pts in segs:
            xy=[(round(s.x0+u[0]*S,4),round(s.y0+u[1]*S,4)) for u in pts]
            simp=[xy[0]]
            for k in range(1,len(xy)-1):
                d1=(round((xy[k][0]-xy[k-1][0])/S),round((xy[k][1]-xy[k-1][1])/S));d2=(round((xy[k+1][0]-xy[k][0])/S),round((xy[k+1][1]-xy[k][1])/S))
                if d1!=d2:simp.append(xy[k])
            if len(xy)>1:simp.append(xy[-1])
            out.append((L,simp))
        return {'segments':out,'vias':[(round(x,4),round(y,4)) for x,y in vias],'cost':g[goal]}
