# U1/U2 exposed-pad vias (9 + 9, GND): land 0.6 -> 0.5 mm, drill 0.3 unchanged, so they fall inside JLC's
# "Epoxy Filled & Capped" range (via diameters 0.15-0.55 mm) whichever diameter it means. Text edit, then refill + DRC.
# usage: ep_via05.py in.kicad_pcb out.kicad_pcb
import sys,os,re
here=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,os.path.join(here,'../tools'))
EP=[(x,y) for x in (24.0,25.5,27.0) for y in (40.0,41.5,43.0)]+[(x,y) for x in (48.0,50.0,52.0) for y in (40.0,42.0,44.0)]
L=open(sys.argv[1],encoding='utf-8').read().split('\n');n=0
for i,l in enumerate(L):
    m=re.match(r'(\s*\(via \(at ([-\d.]+) ([-\d.]+)\) \(size )0\.6(\) \(drill 0\.3\).*)$',l)
    if m and any(abs(float(m.group(2))-x)<1e-3 and abs(float(m.group(3))-y)<1e-3 for x,y in EP):
        L[i]=m.group(1)+'0.5'+m.group(4);n+=1
assert n==18,n
tmp=sys.argv[2].replace('.kicad_pcb','_rm.kicad_pcb');open(tmp,'w',encoding='utf-8').write('\n'.join(L))
import pcbnew as p;from pcbk7 import finish
finish(p.LoadBoard(tmp),sys.argv[2]);os.remove(tmp);print('vias changed:',n)
