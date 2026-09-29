# J1/J2 -> HYC06-HDR15B-060, step 2 (pcbnew): place the new THT footprints (same sheet path/tstamp), assign pad nets.
# Edge offset: mounting-hole/middle-row line is 5.06mm from the PCB edge (x=0 / x=95).
import sys,os,json
import pcbnew as p
here=os.path.dirname(os.path.abspath(__file__))
b=p.LoadBoard(sys.argv[1]);meta=json.load(open(sys.argv[3]))
lib=os.path.join(here,'../../../../outputs/amiga_scandoubler/hardware/Amiga.pretty')
NETS={'J1':{'1':'R_IN','2':'G_IN','3':'B_IN','13':'H_IN','14':'V_IN'},
      'J2':{'1':'R_OUT','2':'G_OUT','3':'B_OUT','13':'H_OUT','14':'V_OUT'}}
GND={'5','6','7','8','10','16'}
POS={'J1':(5.06,42.0,-90.0),'J2':(89.94,42.0,90.0)}
for ref in ('J1','J2'):
    f=p.FootprintLoad(lib,'DE15_HOAUC_HYC06-HDR15B-060')
    f.SetFPIDAsString('Amiga:DE15_HOAUC_HYC06-HDR15B-060')
    f.SetReference(ref);f.SetValue('HYC06-HDR15B-060')
    f.SetPath(p.KIID_PATH(meta[ref]['path']))
    b.Add(f)
    x,y,r=POS[ref];f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));f.SetOrientationDegrees(r)
    for q in f.Pads():
        n=NETS[ref].get(q.GetNumber()) or ('GND' if q.GetNumber() in GND else None)   # 4/9/11/12/15: no net (as before)
        if n:q.SetNet(b.FindNet(n))
p.SaveBoard(sys.argv[2],b)
