from pathlib import Path
from collections import Counter
import json,hashlib
d=Path(__file__).resolve().parent;r=d.parents[1];results=[]
for n in [1816,2048]:
    data=json.loads((d/f'board_{n}.json').read_text());m=data['modules']['amiga_board_top']
    cells=m['cells'];counts=Counter(c['type'] for c in cells.values())
    stage={name:c for name,c in cells.items() if name.startswith('logic_core.output_stage.') and c['type'].startswith('DFF')}
    assert len(stage)==29
    assert Counter(c['type'] for c in stage.values())=={'DFFC':25,'DFFP':4}
    release=[c for c in stage.values() if not any(x['type']=='OBUF' and x['connections']['I']==c['connections']['Q'] for x in cells.values())]
    assert len(release)==2 and all(c['type']=='DFFP' for c in release)
    assert sum(x['connections']['D']==y['connections']['Q'] for x in release for y in release)==1
    for c in stage.values():
        default=1 if c['type']=='DFFP' else 0
        assert int(c['parameters'].get('INIT',str(default)),2)==default
        q=c['connections']['Q']
        if c not in release:
            assert sum(x['type']=='OBUF' and x['connections']['I']==q for x in cells.values())==1
            assert c['connections'].get('CLEAR',c['connections'].get('PRESET')) in [x['connections']['Q'] for x in release]
    pll=next(c for c in cells.values() if c['type']=='rPLL')
    old=json.loads((r/f'synthesis/board_{n}.json').read_text())['modules']['amiga_board_top']['cells']
    oldpll=next(c for c in old.values() if c['type']=='rPLL')
    # Yosys JSON appends a space to distinguish bit-looking strings.
    assert pll['parameters']['PSDA_SEL'].rstrip()=='1000'
    for k,v in oldpll['parameters'].items():
        if k!='PSDA_SEL':assert pll['parameters'][k]==v,(n,k)
    assert (counts['IBUF'],counts['OBUF'],counts['IOBUF'],counts['ODDR'],counts['rPLL'],counts['DPX9B'])==(29,31,2,1,1,6)
    assert sum(len(p['bits']) for p in m['ports'].values())==62
    syn=(d/f'board_{n}_synthesis.log').read_text();route=(d/f'board_{n}_route.log').read_text()
    assert 'Found and reported 0 problems.' in syn and 'End of script.' in syn
    assert 'Program finished normally.' in route and '0 errors' in route
    routed=json.loads((d/f'board_{n}_routed.json').read_text())['modules']['top']
    assert routed['cells']['clocks.pll']['parameters']['PSDA_SEL'].rstrip()=='1000'
    assert routed['cells']['dac_clock_output']['attributes']['NEXTPNR_BEL']=='X0Y1/IOLOGICAO'   # v0.31: DAC_CLK_RAW on pin 3 (IOL2A)
    timing=json.loads((d/f'board_{n}_timing.json').read_text())
    for name,f in [('clocks.adc_clock',28.375),('logic_core.clk_ref',27),('video_clock',56.75)]:
        assert abs(timing['fmax'][name]['constraint']-f)<0.001
        assert timing['fmax'][name]['achieved']>f
    results.append({'H_SAMPLES':n,'tool':data['creator'],'cells':dict(sorted(counts.items())),
      'fmax':timing['fmax'],'utilization':timing['utilization'],
      'warnings':[line for line in route.splitlines() if line.startswith('Warning:')]})
record={'status':'OUTPUT_RELEASE_ROUTED_NOT_SIGNOFF','profiles':results,
 'rtl_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'rtl').glob('*.sv'))}}
(d/'summary.json').write_text(json.dumps(record,indent=2)+'\n')
(d/'verification.txt').write_text('PASS 1816/2048: two local DFFP release stages connected in sequence; 27 output FFs directly drive OBUF inputs and use local release reset; RGB/BLANK DFFC INIT=0, H/V and release DFFP INIT=1 (Yosys primitive defaults); PSDA_SEL=1000; 62 ports; RAM6; ODDR pin16; source periods; single-domain timing\nNOT validated: actual device GSR/PLL phase/jitter, full IO/CDC setup and hold, asynchronous clear recovery/removal and board trace timing.\n')
print('PASS phase180 verification for both profiles')
