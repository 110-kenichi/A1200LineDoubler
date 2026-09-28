"""Routed release FF to output async controls. Recovery/removal not modelled."""
from pathlib import Path
import json,re,hashlib
d=Path(__file__).resolve().parent;results=[]
def parse(text):
    stack=[[]]
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|(?:\\.|[^\s()])+',text):
        if t=='(':a=[];stack[-1].append(a);stack.append(a)
        elif t==')':stack.pop()
        else:stack[-1].append(t)
    assert len(stack)==1
    return stack[0][0]
def limits(items):
    values=[float(v) for a in items for v in a[0].split(':')]
    return min(values),max(values)
for n in [1816,2048]:
    path=d/f'capture_{n}.sdf';tree=parse(path.read_text());assert ['TIMESCALE','1ps'] in tree
    cells={};links={}
    for c in tree:
        if not isinstance(c,list) or c[0]!='CELL':continue
        ins=next(a for a in c if a[0]=='INSTANCE')
        if len(ins)>1:cells[ins[1]]=c
        else:
            for a in c:
                if a[0]=='DELAY':
                    for arc in a[1][1:]:
                        if arc[0]=='INTERCONNECT':links[arc[2]]=(arc[1],*limits(arc[3:]))
    source='logic_core.output_stage.clear_DFFP_Q'
    cq=next(arc for a in cells[source] if a[0]=='DELAY' for arc in a[1][1:] if arc[:3]==['IOPATH','CLK','Q'])
    cqlo,cqhi=limits(cq[3:]);sc=links[source+'/CLK'];assert sc[0]=='clocks.pll/CLKOUTP'
    paths=[]
    for endpoint,net in links.items():
        if net[0]!=source+'/Q':continue
        name,port=endpoint.rsplit('/',1)
        assert port in ['CLEAR','PRESET']
        dc=links[name+'/CLK'];assert dc[0]==sc[0]
        checks=[a for a in cells[name] if a[0]=='TIMINGCHECK']
        async_checks=[a for block in checks for a in block[1:] if a[0] in ['RECOVERY','REMOVAL','RECREM']]
        lo=sc[1]+cqlo+net[1]-dc[2];hi=sc[2]+cqhi+net[2]-dc[1]
        paths.append({'destination':endpoint,'release_after_same_edge_min_ps':lo,'release_after_same_edge_max_ps':hi,
          'time_before_next_edge_min_ps':1e6/56.75-hi,'async_timing_checks':async_checks})
    assert len(paths)==27
    results.append({'H_SAMPLES':n,'sdf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':source,
      'missing_recovery_removal_models':sum(not p['async_timing_checks'] for p in paths),'paths':paths})
record={'status':'ROUTE_INTERVAL_ONLY_NOT_RECOVERY_REMOVAL_SIGNOFF','profiles':results}
(d/'release_timing.json').write_text(json.dumps(record,indent=2)+'\n')
for p in results:
    print(p['H_SAMPLES'],'27 async-control paths; arrival ps',min(x['release_after_same_edge_min_ps'] for x in p['paths']),max(x['release_after_same_edge_max_ps'] for x in p['paths']),
      'minimum before next edge ps',min(x['time_before_next_edge_min_ps'] for x in p['paths']),'missing checks',p['missing_recovery_removal_models'])
