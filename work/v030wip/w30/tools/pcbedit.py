import re,uuid
class Board:
    def __init__(s,path):
        s.path=path;s.lines=open(path,encoding='utf-8').read().split('\n')
        s.nets={m.group(2):int(m.group(1)) for l in s.lines for m in [re.match(r'\s*\(net (\d+) "(.*)"\)$',l)] if m}
    def remove_segment(s,net,a,b,layer=None,tol=1e-3,dup_ok=False):
        # dup_ok: identical copies may exist; remove one (call once per copy)
        n=s.nets[net];hit=[]
        for i,l in enumerate(s.lines):
            m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net (\d+)\)',l)
            if not m or int(m.group(6))!=n or (layer and m.group(5)!=layer):continue
            p=[float(m.group(k)) for k in range(1,5)]
            for A,B in ((a,b),(b,a)):
                if abs(p[0]-A[0])<tol and abs(p[1]-A[1])<tol and abs(p[2]-B[0])<tol and abs(p[3]-B[1])<tol:hit.append(i)
        assert len(hit)==1 or (dup_ok and hit),(net,a,b,hit)
        del s.lines[hit[0]]
    def _insert(s,text):
        # insert before final closing paren
        j=max(i for i,l in enumerate(s.lines) if l.strip()==')')
        s.lines.insert(j,text)
    def add_segment(s,net,a,b,layer='F.Cu',width=.15):
        f=lambda v:('%.4f'%v).rstrip('0').rstrip('.')
        s._insert(f'  (segment (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (width {f(width)}) (layer "{layer}") (net {s.nets[net]}) (tstamp {uuid.uuid4()}))')
    def add_path(s,net,pts,layer='F.Cu',width=.15):
        for a,b in zip(pts,pts[1:]):s.add_segment(net,a,b,layer,width)
    def add_via(s,net,p,size=.55,drill=.3):
        f=lambda v:('%.4f'%v).rstrip('0').rstrip('.')
        s._insert(f'  (via (at {f(p[0])} {f(p[1])}) (size {f(size)}) (drill {f(drill)}) (layers "F.Cu" "B.Cu") (net {s.nets[net]}) (tstamp {uuid.uuid4()}))')
    def save(s,path):open(path,'w',encoding='utf-8').write('\n'.join(s.lines))

def _fmt(v):return ('%.6f'%v).rstrip('0').rstrip('.')
def set_fp(self,ref,x,y,rot):
    import re
    L=self.lines
    for i,l in enumerate(L):
        if l.startswith('  (footprint '):
            j=i;depth=0
            while True:
                depth+=L[j].count('(')-L[j].count(')')
                if depth==0 and j>i:break
                j+=1
            txt='\n'.join(L[i:j+1])
            m=re.search(r'\(fp_text reference "([^"]+)"',txt)
            if not m or m.group(1)!=ref:continue
            m0=re.search(r'\n    \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',txt)
            old=float(m0.group(3)) if m0.group(3) else 0.0;delta=rot-old
            first=[True]
            def sub(m):
                a,b=float(m.group(1)),float(m.group(2));r=float(m.group(3)) if m.group(3) else 0.0
                if first[0]:
                    first[0]=False;nr=rot%360
                    return f'(at {_fmt(x)} {_fmt(y)}'+(f' {_fmt(nr)}' if abs(nr)>1e-9 else '')+')'
                nr=(r+delta)%360
                return f'(at {_fmt(a)} {_fmt(b)}'+(f' {_fmt(nr)}' if abs(nr)>1e-9 else '')+')'
            txt=re.sub(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',sub,txt)
            L[i:j+1]=txt.split('\n');return
    raise KeyError(ref)
Board.set_fp=set_fp
def remove_via(self,net,pt,tol=1e-3):
    import re
    n=self.nets[net];hit=[]
    for i,l in enumerate(self.lines):
        m=re.match(r'  \(via \(at ([-\d.]+) ([-\d.]+)\).*\(net (\d+)\)',l)
        if m and int(m.group(3))==n and abs(float(m.group(1))-pt[0])<tol and abs(float(m.group(2))-pt[1])<tol:hit.append(i)
    assert len(hit)==1,(net,pt,hit);del self.lines[hit[0]]
Board.remove_via=remove_via
def remove_net_layer(self,net,layer):
    import re
    n=self.nets[net];before=len(self.lines)
    self.lines=[l for l in self.lines if not (l.startswith('  (segment') and f'(layer "{layer}") (net {n})' in l)]
    return before-len(self.lines)
Board.remove_net_layer=remove_net_layer
