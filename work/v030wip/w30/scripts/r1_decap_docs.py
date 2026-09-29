# Review #1 (docs): add C70/C71 (100nF 0402, 3V3-GND, U2 VCCO pins 12/23) to 02_fpga.kicad_sch, the netlist and the manifest.
import sys,os,re,json,uuid
R=sys.argv[1];H=os.path.join(R,'hardware')
NEW={'C70':('a0e1c070-0000-4000-8000-00000000c070',256.0),'C71':('a0e1c071-0000-4000-8000-00000000c071',268.0)}
U=lambda s:str(uuid.uuid5(uuid.NAMESPACE_URL,'amiga-scandoubler/'+s))
# ---- schematic: clone C36 (symbol + 2 wires + 2 labels at y=152) to new y
sf=os.path.join(H,'02_fpga.kicad_sch');S=open(sf).read()
if '"C70"' not in S:
    L=S.split('\n');i=[k for k,l in enumerate(L) if l.startswith('(wire (pts (xy 357.84 152)')][0]
    j=i+4;d=0
    while True:
        d+=L[j].count('(')-L[j].count(')')
        if d==0:break
        j+=1
    blk='\n'.join(L[i:j+1]);add=[]
    for ref,(uid,y) in NEW.items():
        t=blk.replace(' 152)',' %g)'%y).replace(' 152 ',' %g '%y).replace('(at 368 145 ','(at 368 %g '%(y-7)).replace('(at 368 147.8 ','(at 368 %g '%(y-4.2))
        t=t.replace('"C36"','"%s"'%ref).replace('C_0603_1608Metric','C_0402_1005Metric')
        t=re.sub(r'\(uuid ([0-9a-f-]+)\)',lambda m:'(uuid %s)'%(uid if m.group(1)=='f25a1926-877c-5038-a457-b9606053b4e7' else U(ref+m.group(1))),t)
        add.append(t)
    L[j+1:j+1]=add;S='\n'.join(L)
    inst=[l for l in S.split('\n') if '(reference "C36")' in l][0]
    newi=[inst.replace('f25a1926-877c-5038-a457-b9606053b4e7',uid).replace('"C36"','"%s"'%ref).replace('C_0603_1608Metric','C_0402_1005Metric') for ref,(uid,y) in NEW.items()]
    S=S.replace(inst,inst+'\n'+'\n'.join(newi))
    open(sf,'w').write(S)
# ---- manifest
mf=os.path.join(H,'circuit_manifest.json');M=json.load(open(mf))
for ref in NEW:
    M['parts'][ref]=dict(M['parts']['C36'],reference=ref,footprint='Capacitor_SMD:C_0402_1005Metric',notes='U2 VCCO decap (pin %s), added in v0.30wip review'%('12' if ref=='C70' else '23'))
    M['parts'][ref]['pins']=json.loads(json.dumps(M['parts']['C36']['pins']))
    for pin,net in (('1','3V3'),('2','GND')):
        if [ref,pin] not in M['nets'][net]:M['nets'][net].append([ref,pin])
json.dump(M,open(mf,'w'),indent=2,ensure_ascii=False)
# ---- netlist
nf=os.path.join(H,'amiga_scandoubler.net');N=open(nf).read()
if '(ref "C70")' not in N:
    a=N.index('    (comp (ref "C36")');z=N.index('    (comp (ref',a+10);comp=N[a:z]
    new=''.join(comp.replace('"C36"','"%s"'%r).replace('C_0603_1608Metric','C_0402_1005Metric').replace('f25a1926-877c-5038-a457-b9606053b4e7',u) for r,(u,y) in NEW.items())
    N=N[:z]+new+N[z:]
    for net,pin in (('3V3','1'),('GND','2')):
        m=re.search(r'\(net \(code "\d+"\) \(name "%s"\)\n'%net,N);k=m.end()
        N=N[:k]+''.join('      (node (ref "%s") (pin "%s") (pintype "passive"))\n'%(r,pin) for r in NEW)+N[k:]
    open(nf,'w').write(N)
print('ok')
