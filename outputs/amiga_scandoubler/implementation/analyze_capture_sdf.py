"""Extract the 26 capture paths. Estimates are NOT timing signoff.
Missing inserted-LUT timing arcs are explicitly reported and estimated from
other LUT4 I3->F arcs in the SAME SDF, never silently treated as zero.
"""
from pathlib import Path
import re,json,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--phase',type=int,choices=[90,180],default=90)
ap.add_argument('--implementation',choices=['output_stage','output_release'])
args=ap.parse_args()
r=Path(__file__).resolve().parents[1];results=[]
directory=r/'implementation'
if args.phase==180:directory=directory/'phase180'
if args.implementation:
    assert args.phase==180,'output_stage uses 180 degree PLL'
    directory=r/'implementation'/args.implementation
def parse(text):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|(?:\\.|[^\s()])+',text)
    stack=[[]]
    for t in tokens:
        if t=='(':node=[];stack[-1].append(node);stack.append(node)
        elif t==')':stack.pop()
        else:stack[-1].append(t)
    assert len(stack)==1
    return stack[0][0]
def maximum(items):
    return max(float(x) for item in items for x in item[0].split(':'))
for n in [1816,2048]:
    p=directory/f'capture_{n}.sdf';tree=parse(p.read_text())
    assert ['TIMESCALE','1ps'] in tree
    cells={};inter=[]
    for c in tree:
        if not isinstance(c,list) or c[0]!='CELL':continue
        instance=next(x for x in c if x[0]=='INSTANCE')
        name=instance[1] if len(instance)>1 else ''
        kind=next(x[1].strip('"') for x in c if x[0]=='CELLTYPE')
        arcs=[];checks=[]
        for x in c:
            if x[0]=='DELAY':arcs=x[1][1:]
            if x[0]=='TIMINGCHECK':checks=x[1:]
        if not name:inter=[x for x in arcs if x[0]=='INTERCONNECT']
        else:cells[name]={'kind':kind,'arcs':arcs,'checks':checks}
    models=[]
    for name,c in cells.items():
        if c['kind']=='LUT4':
            models += [(name,maximum(a[3:])) for a in c['arcs'] if a[:3]==['IOPATH','I3','F']]
    assert models
    borrowed=max(v for _,v in models)
    clock_arcs={a[2]:a for a in inter if a[2].endswith('/CLK')}
    paths=[]
    for a in inter:
        if not re.match(r'logic_core\.capture\.(captured|token)_DFF.*?/Q$',a[1]):continue
        if not re.match(r'logic_core\.capture\.(stage1|tag1)_.*?/I3$',a[2]):continue
        src=a[1].rsplit('/',1)[0];lut=a[2].rsplit('/',1)[0]
        assert cells[lut]['kind']=='LUT4'
        targets=[x for x in inter if x[1]==lut+'/F' and x[2].endswith('/D')]
        assert len(targets)==1
        tail=targets[0];dst=tail[2].rsplit('/',1)[0]
        cq=maximum(next(x[3:] for x in cells[src]['arcs'] if x[:3]==['IOPATH','CLK','Q']))
        setup=max(maximum([x[3]]) for x in cells[dst]['checks'] if x[0]=='SETUPHOLD' and x[1] in [['posedge','D'],['negedge','D']] and x[2]==['posedge','CLK'])
        assert any(x[0]=='SETUPHOLD' and x[2]==['negedge','CLK'] for x in cells[src]['checks'])
        actual=[x for x in cells[lut]['arcs'] if x[:3]==['IOPATH','I3','F']]
        lut_delay=maximum(actual[0][3:]) if actual else borrowed
        launch=clock_arcs[src+'/CLK'];capture=clock_arcs[dst+'/CLK']
        assert launch[1]=='clocks.adc_clock_IBUF_O/O' and capture[1]=='clocks.pll/CLKOUTP'
        ld=maximum(launch[3:]);cd=maximum(capture[3:])
        data=cq+maximum(a[3:])+lut_delay+maximum(tail[3:])+setup
        paths.append({'source':src,'destination':dst,'clock_to_Q_ps':cq,'route_to_LUT_ps':maximum(a[3:]),
          'LUT_ps':lut_delay,'LUT_arc_missing':not bool(actual),'route_to_D_ps':maximum(tail[3:]),
          'setup_ps':setup,'ADC_clock_route_ps':ld,'video_clock_route_ps':cd,
          'required_ideal_edge_gap_ps_estimate':data+ld-cd})
    assert len(paths)==26 and len({p['source'] for p in paths})==26
    assert len({p['destination'] for p in paths})==26
    worst=max(p['required_ideal_edge_gap_ps_estimate'] for p in paths)
    period=1e6/28.375
    gaps={str(duty):period*(0.5+args.phase/720-duty) for duty in [0.48,0.5,0.52]}
    results.append({'H_SAMPLES':n,'sdf_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'source_clock_MHz':28.375,'PLL_phase_video_degrees_assumed':args.phase,
      'missing_LUT_arcs':sum(p['LUT_arc_missing'] for p in paths),
      'borrowed_LUT4_I3_F_max_ps':borrowed,'matching_model_count':len(models),
      'worst_required_ideal_gap_ps_estimate':worst,
      'ideal_gap_ps_by_ADC_duty':gaps,
      'remaining_budget_ps_estimate':{k:v-worst for k,v in gaps.items()},'paths':paths})
record={'status':'INDICATIVE_ONLY_MISSING_TIMING_ARCS_AND_PLL_UNCERTAINTY','profiles':results}
(directory/'capture_timing_estimate.json').write_text(json.dumps(record,indent=2)+'\n')
for p in results:print(p['H_SAMPLES'],'paths',len(p['paths']),'missing LUT arcs',p['missing_LUT_arcs'],'required ps',p['worst_required_ideal_gap_ps_estimate'],'remaining ps',p['remaining_budget_ps_estimate'])
