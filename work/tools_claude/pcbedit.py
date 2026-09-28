import re,uuid
class Board:
    def __init__(s,path):
        s.path=path;s.lines=open(path,encoding='utf-8').read().split('\n')
        s.nets={m.group(2):int(m.group(1)) for l in s.lines for m in [re.match(r'\s*\(net (\d+) "(.*)"\)$',l)] if m}
    def remove_segment(s,net,a,b,layer=None,tol=1e-3):
        n=s.nets[net];hit=[]
        for i,l in enumerate(s.lines):
            m=re.match(r'\s*\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width [\d.]+\) \(layer "([^"]+)"\) \(net (\d+)\)',l)
            if not m or int(m.group(6))!=n or (layer and m.group(5)!=layer):continue
            p=[float(m.group(k)) for k in range(1,5)]
            for A,B in ((a,b),(b,a)):
                if abs(p[0]-A[0])<tol and abs(p[1]-A[1])<tol and abs(p[2]-B[0])<tol and abs(p[3]-B[1])<tol:hit.append(i)
        assert len(hit)==1,(net,a,b,hit)
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
