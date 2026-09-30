# CPL rotation check against the JLC/EasyEDA footprints (read-only).
# EasyEDA data: https://easyeda.com/api/products/<LCSC>/components?version=6.4.19.5 (saved as <LCSC>.json in a directory).
# For each part: find the rotation R (0/90/180/270, CCW seen from the top) that maps the EasyEDA pads onto the KiCad
# footprint pads at 0 deg (same pad numbers, both relative to their pad centroids). JLC rotation = CPL rotation + R.
# Also reports the placement error if JLC puts the EasyEDA footprint origin on the CPL point (= KiCad origin).
# usage: jlc_rotcheck.py <board.kicad_pcb> <jlc_cpl.csv> <manifest.json> <easyeda json dir> <out.json>
import sys,os,json,math,csv
import pcbnew as p
U=0.254   # EasyEDA unit (10 mil) in mm
b=p.LoadBoard(sys.argv[1]);cpl={r['Designator']:r for r in csv.DictReader(open(sys.argv[2]))}
M=json.load(open(sys.argv[3]))['parts'];D=sys.argv[4]
REFS=['U1','U2','U3','U4','U5','U6','U7','U8','U9','Y1','J3','J4'] if not os.environ.get('ALL') else sorted(cpl,key=lambda r:(r.rstrip('0123456789'),int(r[len(r.rstrip('0123456789')):])))
# 2-pad parts are symmetric: R 0/180 fit equally (the first, 0, is reported); only 90/270 means a real mismatch.
def rot(v,deg):
    t=math.radians(deg);x,y=v;return (x*math.cos(t)+y*math.sin(t),-x*math.sin(t)+y*math.cos(t))   # CCW (top view), y down
out=[]
for ref in REFS:
    f=b.FindFootprintByReference(ref);lc=M[ref]['lcsc']
    try:ds=json.load(open(os.path.join(D,lc+'.json')))['result']['packageDetail']['dataStr']
    except (KeyError,TypeError,FileNotFoundError,json.JSONDecodeError):
        out.append(dict(ref=ref,lcsc=lc,no_easyeda_data=True));print('%-3s %-10s no EasyEDA footprint data'%(ref,lc));continue
    ep={}
    for s in ds['shape']:
        if not s.startswith('PAD~'):continue
        a=s.split('~');ep.setdefault(a[8],[]).append((float(a[2])*U,float(a[3])*U))
    ep={k:(sum(x for x,_ in v)/len(v),sum(y for _,y in v)/len(v)) for k,v in ep.items()}
    # KiCad pads at footprint rotation 0, relative to the footprint origin
    o=f.GetOrientationDegrees();c=f.GetPosition();kp={}
    for q in f.Pads():
        d=q.GetPosition()-c;v=rot((p.ToMM(d.x),p.ToMM(d.y)),-o)   # undo footprint rotation
        kp.setdefault(q.GetNumber(),[]).append(v)
    kp={k:(sum(x for x,_ in v)/len(v),sum(y for _,y in v)/len(v)) for k,v in kp.items() if k}
    common=sorted(set(ep)&set(kp))
    ce=(sum(ep[k][0] for k in common)/len(common),sum(ep[k][1] for k in common)/len(common))
    ck=(sum(kp[k][0] for k in common)/len(common),sum(kp[k][1] for k in common)/len(common))
    best=None
    for R in (0,90,180,270):
        err=0
        for k in common:
            e=rot((ep[k][0]-ce[0],ep[k][1]-ce[1]),R);kk=(kp[k][0]-ck[0],kp[k][1]-ck[1])
            err=max(err,math.hypot(e[0]-kk[0],e[1]-kk[1]))
        if best is None or err<best[1]:best=(R,err)
    R,err=best;cr=float(cpl[ref]['Rotation'])
    # placement offset: JLC puts the EasyEDA footprint origin (head x,y) on the CPL point.
    # KiCad CPL point = KiCad footprint origin. Error = where the part lands minus where it should be (board frame).
    eo=(float(ds['head']['x'])*U-ce[0],float(ds['head']['y'])*U-ce[1])   # EasyEDA origin rel. its pad centroid
    eo=rot(eo,R);ko=(-ck[0],-ck[1])                                      # KiCad origin rel. its pad centroid
    ob=rot((ko[0]-eo[0],ko[1]-eo[1]),o)  # shift of the pads if uncorrected (board frame, mm)
    out.append(dict(ref=ref,lcsc=lc,easyeda=ds['head'].get('c_para',{}).get('package') or '',pads_compared=len(common),
                    R=R,max_pad_err_mm=round(err,3),cpl_rot=cr,jlc_rot=(cr+R)%360,placement_error_mm=[round(ob[0],3),round(ob[1],3)]))
    print('%-3s %-10s pads %-3d R=%-3d maxerr %.3f mm  CPL %6.1f -> JLC %6.1f  pos err (%.3f,%.3f)'%(ref,lc,len(common),R,err,cr,(cr+R)%360,ob[0],ob[1]))
json.dump(out,open(sys.argv[5],'w'),indent=1,ensure_ascii=False)
