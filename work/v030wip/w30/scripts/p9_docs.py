# Issue 9: bring the design documents in line with the v0.31 U2 pin assignment.
# Source of truth: U2 pad nets on the board (v030wip) and constraints/amiga_board_top.cst (= v031dac).
# Updates: 02_fpga.kicad_sch global labels on U2 pins, amiga_scandoubler.net (U2 nodes),
#          circuit_manifest.json (U2 pins + net lists), fpga_pin_assignment.json (nets), board_port_map.json (pin/io_name).
import sys,os,re,json
import pcbnew as p
R=sys.argv[1]   # outputs/amiga_scandoubler
H=os.path.join(R,'hardware')
b=p.LoadBoard(os.path.join(H,'amiga_scandoubler_v030wip.kicad_pcb'))
bn={q.GetNumber():q.GetNetname() for q in b.FindFootprintByReference('U2').Pads() if q.GetNumber()}
log=[]
# ---- manifest
mf=os.path.join(H,'circuit_manifest.json');M=json.load(open(mf))
pins=M['parts']['U2']['pins'];chg={k:(pins[k]['net'],bn[k]) for k in pins if pins[k]['net']!=bn[k]}
for k,(o,n) in chg.items():pins[k]['net']=n
for net,nodes in M['nets'].items():
    M['nets'][net]=[x for x in nodes if not (x[0]=='U2' and x[1] in chg)]
for k,(o,n) in chg.items():M['nets'].setdefault(n,[]).append(['U2',k])
json.dump(M,open(mf,'w'),indent=2,ensure_ascii=False);log.append('manifest U2 pins changed %d'%len(chg))
# ---- fpga_pin_assignment.json
ff=os.path.join(H,'fpga_pin_assignment.json');F=json.load(open(ff));c=0
for k,v in F['pins'].items():
    if k in bn and v.get('net')!=bn[k] and v.get('function')=='I/O':v['net']=bn[k];c+=1
json.dump(F,open(ff,'w'),indent=2,ensure_ascii=False);log.append('fpga_pin_assignment nets changed %d'%c)
# ---- board_port_map.json from the cst
cst=open(os.path.join(R,'constraints','amiga_board_top.cst')).read()
loc={m.group(1):m.group(2) for m in re.finditer(r'IO_LOC\s+"([^"]+)"\s+(\d+);',cst)}
pf=os.path.join(R,'constraints','board_port_map.json');P=json.load(open(pf));c=0;bad=[]
for port,v in P['ports'].items():
    if port in loc and str(v['pin'])!=loc[port]:v['pin']=int(loc[port]);v['io_name']=F['pins'][loc[port]]['name'];c+=1
    if bn.get(str(v['pin']))!=v['net']:bad.append((port,v['pin'],v['net'],bn.get(str(v['pin']))))
json.dump(P,open(pf,'w'),indent=2,ensure_ascii=False);log.append('board_port_map pins changed %d, port/board net mismatches %s'%(c,bad))
# ---- netlist: move U2 node lines to their new nets
nf=os.path.join(H,'amiga_scandoubler.net');L=open(nf).read().split('\n');moved={};out=[]
for l in L:
    m=re.match(r'\s*\(node \(ref "U2"\) \(pin "(\d+)"\)',l)
    if m and m.group(1) in chg:
        moved[m.group(1)]=l.rstrip(')') if l.rstrip().endswith('))))') else l
        # a node that closes its net block carries one extra ')'
        if l.rstrip().endswith(')))') and l.count('(')<l.count(')'):
            out[-1]=out[-1]+')'*(l.count(')')-l.count('('));moved[m.group(1)]=l[:len(l)-(l.count(')')-l.count('('))]
        continue
    out.append(l)
L=out;out=[];cur=None
for l in L:
    m=re.match(r'\s*\(net \(code "\d+"\) \(name "([^"]*)"\)',l)
    out.append(l)
    if m:
        cur=m.group(1)
        for k,(o,n) in chg.items():
            if n==cur:out.append(moved[k])
open(nf,'w').write('\n'.join(out));log.append('netlist nodes moved %d'%len(moved))
# ---- schematic labels on U2 pins
sf=os.path.join(H,'02_fpga.kicad_sch');S=open(sf).read()
libpins={}
for m in re.finditer(r'\(symbol "GW1N-LV4QN88C6_I5_(\d+)_1"(.*?)\n\)\n',S,re.S):
    for q in re.finditer(r'\(pin \w+ line \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "(\d+)"',m.group(2)):
        libpins.setdefault(int(m.group(1)),[]).append((float(q.group(1)),float(q.group(2)),q.group(4)))
end={}
for m in re.finditer(r'\(symbol \(lib_id "Amiga:GW1N-LV4QN88C6_I5"\) \(at ([-\d.]+) ([-\d.]+) 0\) \(unit (\d+)\)',S):
    X,Y,u=float(m.group(1)),float(m.group(2)),int(m.group(3))
    for px,py,num in libpins.get(u,[]):end[(round(X+px,2),round(Y-py,2))]=num
wires=[tuple(map(float,m.groups())) for m in re.finditer(r'\(wire \(pts \(xy ([-\d.]+) ([-\d.]+)\) \(xy ([-\d.]+) ([-\d.]+)\)\)',S)]
far={}
for x1,y1,x2,y2 in wires:
    a=(round(x1,2),round(y1,2));z=(round(x2,2),round(y2,2))
    if a in end:far[z]=end[a]
    elif z in end:far[a]=end[z]
done=0;seen=set()
def sub(m):
    global done
    at=(round(float(m.group(2)),2),round(float(m.group(3)),2));num=far.get(at) or end.get(at)
    if num:
        seen.add(num)
        if num in chg:
            assert m.group(1)==chg[num][0],(num,m.group(1),chg[num]);done+=1
            return m.group(0).replace('"%s"'%m.group(1),'"%s"'%chg[num][1],1)
    return m.group(0)
S=re.sub(r'\(global_label "([^"]+)" \(shape \w+\) \(at ([-\d.]+) ([-\d.]+) \d+\)',sub,S)
open(sf,'w').write(S);log.append('schematic labels renamed %d (U2 pins with labels found %d)'%(done,len(seen)))
# ---- sync_out_progress.json: H/V_OUT_RAW now leave U2 on pins 14/13 (v0.31); the route is F.Cu -> via -> B.Cu
sp=os.path.join(H,'sync_out_progress.json');J=json.load(open(sp));c=0
for r in J['connections']:
    if r['from'][0]=='U2' and r['from'][1]!=[k for k,v in bn.items() if v==r['net']][0]:
        r['from'][1]=[k for k,v in bn.items() if v==r['net']][0];r['layer']='F.Cu+B.Cu';c+=1
json.dump(J,open(sp,'w'),indent=2,ensure_ascii=False);log.append('sync_out_progress U2 pins changed %d'%c)
print('\n'.join(log))
