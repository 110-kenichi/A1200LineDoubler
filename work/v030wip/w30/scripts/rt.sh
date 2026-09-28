# usage: rt.sh in out net ax ay la zx zy lz blocks opts
IN=$1;OUT=$2;NET=$3
/opt/kicad/squashfs-root/bin/python3 /tmp/s2/r2.py $IN $NET "[$4,$5]" $6 "[$7,$8]" $9 "${10}" "${11}" 2>/dev/null | tail -1 > /tmp/s2/res.json
python3 - "$IN" "$OUT" "$NET" "$4" "$5" "$7" "$8" <<'PY'
import json,sys,subprocess
IN,OUT,NET=sys.argv[1:4];a=[float(sys.argv[4]),float(sys.argv[5])];z=[float(sys.argv[6]),float(sys.argv[7])]
r=json.load(open('/tmp/s2/res.json'))
if not r:print(NET,'FAILED');sys.exit(1)
r['segments'][0][1].insert(0,a);r['segments'][-1][1].append(z)
print(NET,'vias',r['vias'])
for L,p in r['segments']:print(' ',L,p)
json.dump([[NET,0.15,r]],open('/tmp/s2/one.json','w'))
subprocess.run(['python3','/tmp/s/apply_multi.py',IN,OUT,'/tmp/s2/one.json'],check=True)
subprocess.run(['cp',IN.replace('.kicad_pcb','.kicad_pro'),OUT.replace('.kicad_pcb','.kicad_pro')])
PY
