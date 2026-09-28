"""Structural video-FF to DAC output-buffer-input delay budget. Not signoff.
No OBUF/ODDR delay is invented. Non-video fan-in and absent arcs are listed.
"""
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
import re,json,hashlib,argparse
p=argparse.ArgumentParser()
p.add_argument('--implementation',choices=['phase180','output_stage','output_release'],default='phase180')
a=p.parse_args();folder=a.implementation
r=Path(__file__).resolve().parents[1];results=[]
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
    p=r/f'implementation/{folder}/capture_{n}.sdf';tree=parse(p.read_text())
    assert ['TIMESCALE','1ps'] in tree
    cells={};inter=[]
    for cell in tree:
        if not isinstance(cell,list) or cell[0]!='CELL':continue
        ins=next(a for a in cell if a[0]=='INSTANCE');name=ins[1] if len(ins)>1 else ''
        c={'type':next(a[1].strip('"') for a in cell if a[0]=='CELLTYPE'),'arcs':[]}
        for a in cell:
            if a[0]=='DELAY':c['arcs']=a[1][1:]
        if name:cells[name]=c
        else:inter=[a for a in c['arcs'] if a[0]=='INTERCONNECT']
    # Missing small-LUT arcs are estimates from physical LUT4 arcs in this SDF.
    # Preserve an explicit list; this is not a substitute for a timing model.
    model=defaultdict(list);estimated=[]
    for c in cells.values():
        if c['type']=='LUT4':
            for a in c['arcs']:
                if a[0]=='IOPATH' and a[2]=='F' and isinstance(a[1],str):model[a[1]].append(limits(a[3:]))
    raw=json.loads((r/f'implementation/{folder}/board_{n}_routed.json').read_text())['modules']['top']['cells']
    reverse=defaultdict(list)
    for a in inter:reverse[a[2]].append((a[1],*limits(a[3:])))
    for name,c in cells.items():
        if c['type'].startswith('DFF'):continue
        for a in c['arcs']:
            if a[0]=='IOPATH' and isinstance(a[1],str):reverse[name+'/'+a[2]].append((name+'/'+a[1],*limits(a[3:])))
        if re.fullmatch('LUT[1-4]',c['type']) and not c['arcs']:
            key=re.sub(r'\\(.)',r'\1',name)
            for port,direction in raw[key]['port_directions'].items():
                if direction!='input':continue
                assert model[port],port
                lo=min(v[0] for v in model[port]);hi=max(v[1] for v in model[port])
                reverse[name+'/F'].append((name+'/'+port,lo,hi));estimated.append(name+'/'+port+'->F')
    excluded=set();missing=set();source_mode='all_video'
    @lru_cache(None)
    def walk(endpoint):
        cell,port=endpoint.rsplit('/',1)
        if cells[cell]['type'].startswith('DFF'):
            if port!='Q':excluded.add(endpoint);return None
            clocks=reverse[cell+'/CLK']
            if len(clocks)!=1 or clocks[0][0]!='clocks.pll/CLKOUTP':excluded.add(endpoint);return None
            if source_mode=='rgb_payload' and not cell.startswith(('logic_core.video.core.rgb2_DFF','logic_core.output_stage.rgb_DFF')):return None
            arc=next((a for a in cells[cell]['arcs'] if a[:3]==['IOPATH','CLK','Q']),None)
            if arc is None:missing.add(endpoint);return None
            lo,hi=limits(arc[3:]);return (lo+clocks[0][1],hi+clocks[0][2],endpoint,endpoint)
        if not reverse[endpoint]:
            if cells[cell]['type'] not in ['GND','VCC']:missing.add(endpoint)
            return None
        paths=[]
        for prev,lo,hi in reverse[endpoint]:
            w=walk(prev)
            if w:paths.append((w[0]+lo,w[1]+hi,w[2],w[3]))
        if not paths:return None
        fast=min(paths,key=lambda x:x[0]);slow=max(paths,key=lambda x:x[1])
        return fast[0],slow[1],fast[2],slow[3]
    outputs=[]
    for name,c in cells.items():
        if c['type']!='OBUF' or not re.fullmatch(r'DAC_(?:[RGB]_OBUF_O(?:_\d+)?|BLANK_N_OBUF_O)',name):continue
        delay=walk(name+'/I');assert delay is not None,name
        outputs.append({'output_buffer':name,'estimated_min_ps':delay[0],'estimated_max_ps':delay[1],'fastest_video_source':delay[2],'slowest_video_source':delay[3]})
    assert len(outputs)==25
    source_mode='rgb_payload';walk.cache_clear()
    for o in outputs:
        delay=walk(o['output_buffer']+'/I')
        o['rgb_payload_only_estimated_ps']=list(delay[:2]) if delay else None
    clk=reverse['dac_clock_output/CLK'];assert len(clk)==1 and clk[0][0]=='clocks.pll/CLKOUTP'
    q=reverse['DAC_CLK_RAW_OBUF_O/I']
    # Dedicated IO connection may be absent from SDF. Keep its entire delay
    # in the unknown clock term; do not claim a zero-delay connection.
    assert not q or (len(q)==1 and q[0][0]=='dac_clock_output/Q0'),q
    clklo=clk[0][1]+(q[0][1] if q else 0)
    clkhi=clk[0][2]+(q[0][2] if q else 0)
    half=1e6/56.75/2
    envelopes=[]
    for load,bmin,bmax in [('15pF',1500,4600),('50pF',1800,5500)]:
        # X = unknown data pad/trace delay minus unknown clock ODDR/pad/trace delay.
        per_pin=[]
        for o in outputs:
            setup=half+clklo+bmin-200-o['estimated_max_ps']
            hold=-half+clkhi+bmax+1500-o['estimated_min_ps']
            per_pin.append({'output_buffer':o['output_buffer'],
              'required_Xmax_at_most_ps':setup,'required_Xmin_at_least_ps':hold,
              'estimated_interval_nonempty':hold<=setup})
        envelopes.append({'buffer_load_test':load,'buffer_min_ps':bmin,'buffer_max_ps':bmax,
          'per_pin':per_pin})
    results.append({'H_SAMPLES':n,'sdf_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'video_MHz':56.75,'DAC_setup_ps':200,'DAC_hold_ps':1500,'DAC_min_high_low_ps':2850,
      'clock_known_min_ps':clklo,'clock_known_max_ps':clkhi,'outputs':outputs,'envelopes':envelopes,
      'missing_dedicated_clock_connection':not bool(q),
      'excluded_non_video_sources':sorted(excluded),'unmodelled_fanin_endpoints':sorted(missing),
      'estimated_LUT_arcs_in_model':estimated,
      'missing_output_models':[name for name,c in cells.items() if (name=='dac_clock_output' or name=='DAC_CLK_RAW_OBUF_O' or name in [o['output_buffer'] for o in outputs]) and not c['arcs']]})
destination=r/('implementation/dac_timing_budget.json' if folder=='phase180' else f'implementation/{folder}/dac_timing_budget.json')
destination.write_text(json.dumps({'status':'PARTIAL_STRUCTURAL_ENVELOPE_NOT_SIGNOFF','profiles':results},indent=2)+'\n')
for p in results:
    print(p['H_SAMPLES'],'25 output cones; max estimated ns',max(o['estimated_max_ps'] for o in p['outputs'])/1000,
      'missing fanin',len(p['unmodelled_fanin_endpoints']),
      'estimated empty per-pin intervals',[(e['buffer_load_test'],sum(not o['estimated_interval_nonempty'] for o in e['per_pin'])) for e in p['envelopes']])
