import re,sys
src,dst=sys.argv[1],sys.argv[2];targets=set(sys.argv[3].split(','));width=sys.argv[4] if len(sys.argv)>4 else '150'
t=open(src).read()
t=re.sub(r'\(layer (In\d\.Cu)\s*\(type signal\)',lambda m:f'(layer {m.group(1)}\n      (type power)',t)
ns=t.index('(network');we=t.index('(wiring');net=t[ns:we]
def keep(m):return m.group(0) if m.group(1) in targets else f'(net {m.group(1)}\n      (pins)\n    )'
net=re.sub(r'\(net ([^\s()]+)\s*\(pins[^)]*\)\s*\)',keep,net)
net=re.sub(r'\(use_via "[^"]*"\)','(use_via "Via[0-3]_550:300_um")',net)
net=net.replace('(width 200)',f'(width {width})')
t=t[:ns]+net+t[we:]
t=t.replace('(rule\n      (width 200)',f'(rule\n      (width {width})',1)
t=re.sub(r'\(type route\)','(type protect)',t)
open(dst,'w').write(t)
