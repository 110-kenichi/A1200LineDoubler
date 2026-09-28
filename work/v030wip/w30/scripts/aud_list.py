import os,sys
src=open('/root/w2/work/audit_sync_in.py').read()
head=src.split("old=json.loads")[0]
exec(head.replace("__file__","'/root/w2/work/audit_sync_in.py'"))
old=json.loads((h/'power_routing_report.json').read_text())
bad=[(a,z) for a,z in old['verified_local_power_connections'] if not connected(a,z)]
print(len(old['verified_local_power_connections']),'bad',bad)
for a,z in bad:
  q=pad(*a);print(a,q.GetNetname(),q.GetPosition().x/1e6,q.GetPosition().y/1e6)
progress=json.loads((h/'distribution_progress.json').read_text())
sources={'3V3':('C56',1),'1V9':('C58',1),'1V2':('C60',1),'ADC_3V3A':('FB1',2),'ADC_1V9A':('FB2',2),'ADC_1V9PLL':('FB3',2),'DAC_3V3':('FB4',2)}
for r in progress['escapes']:
  q=pad(*r['pad'])
  if q.GetNetname()!='GND' and not connected(r['pad'],sources[q.GetNetname()]):print('esc',r['pad'],q.GetNetname(),q.GetPosition().x/1e6,q.GetPosition().y/1e6)
for r in progress['connections']:
  a,z=r['from'],r['to']
  if not connected(a,z) or not connected(a,sources[pad(*a).GetNetname()]):print('conn',a,z)
