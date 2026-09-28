"""Audit mapped IO and startup connectivity; not a placement/timing check."""
from pathlib import Path
from collections import Counter
import json,hashlib,re
r=Path(__file__).resolve().parents[1];reports=[];profiles=[]
for n in [1816,2048]:
    m=json.loads((r/f'synthesis/board_{n}.json').read_text())['modules']['amiga_board_top']
    cells=m['cells'];counts=Counter(c['type'] for c in cells.values())
    assert counts['rPLL']==counts['ODDR']==1 and counts['DPX9B']==6
    assert (counts['IBUF'],counts['OBUF'],counts['IOBUF'])==(29,31,2)
    assert not any(t.startswith('$') and t!='$scopeinfo' for t in counts)
    bits=lambda name:m['netnames'][name]['bits']
    drivers={b:c for c in cells.values() for port,bs in c['connections'].items() if c['port_directions'][port]=='output' for b in bs if isinstance(b,int)}
    def value(bit,inputs=None):
        inputs=inputs or {}
        if bit in inputs:return inputs[bit]
        if bit in ['0','1']:return int(bit)
        c=drivers[bit];t=c['type'];cs=c['connections']
        if t in ['GND','VCC']:return int(t=='VCC')
        if re.fullmatch('LUT[1-4]',t):
            idx=sum(value(cs[f'I{i}'][0],inputs)<<i for i in range(int(t[-1])))
            return (int(c['parameters']['INIT'],2)>>idx)&1
        raise AssertionError(('unexpected combinational cone',t))
    for port,low in [('I2C_SCL','scl_low'),('I2C_SDA','sda_low')]:
        buf=next(c for c in cells.values() if c['type']=='IOBUF' and c['connections']['IO']==m['ports'][port]['bits'])
        assert value(buf['connections']['I'][0])==0
        for state in [0,1]:assert value(buf['connections']['OEN'][0],{bits(low)[0]:state})==1-state
        assert buf['connections']['O'][0] in bits('logic_core.'+('scl_in' if low=='scl_low' else 'sda_in'))
    oddr=next(c for c in cells.values() if c['type']=='ODDR')['connections']
    assert value(oddr['D0'][0])==0 and value(oddr['D1'][0])==1 and value(oddr['TX'][0])==0
    out=next(c for c in cells.values() if c['type']=='OBUF' and c['connections']['O']==m['ports']['DAC_CLK_RAW']['bits'])
    assert out['connections']['I']==oddr['Q0']
    pll=next(c for c in cells.values() if c['type']=='rPLL')['connections']
    assert oddr['CLK']==pll['CLKOUTP']==bits('video_clock')
    released=bits('startup.released');assert len(released)==32
    for i,bit in enumerate(released):
        ff=drivers[bit];assert ff['type']=='DFF'
        assert int(ff['parameters'].get('INIT','0'),2)==0
        d=ff['connections']['D'][0]
        assert (value(d)==1 if i==0 else d==released[i-1])
    ports=set()
    for name,info in m['ports'].items():
        ports.update([name] if len(info['bits'])==1 else [f'{name}[{i}]' for i in range(len(info['bits']))])
    mapping=json.loads((r/'constraints/board_port_map.json').read_text())['ports']
    assert ports==set(mapping)
    log=(r/f'synthesis/board_{n}.log').read_text()
    assert 'End of script.' in log and 'Found and reported 0 problems.' in log
    profiles.append({'H_SAMPLES':n,'cells':dict(sorted(counts.items())),
        'LUT1_to_4':sum(v for k,v in counts.items() if re.fullmatch('LUT[1-4]',k)),
        'FF':sum(v for k,v in counts.items() if k.startswith('DFF'))})
    reports.append(f'PASS board_{n}: 62 mapped ports; I2C low/open and readback; ODDR direct output; PLL clock; 32 initialized reset stages; RAM6; final CHECK0')
record={'status':'SYNTHESIS_ONLY_NOT_FITTED','profiles':profiles,'rtl_sha256':{str(p.relative_to(r)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'rtl').glob('*.sv'))}}
(r/'synthesis/board_summary.json').write_text(json.dumps(record,indent=2)+'\n')
(r/'board_netlist_audit.txt').write_text('\n'.join(reports)+'\nScope: synthesis connectivity/initialization only; no placement or timing proof.\n')
print('\n'.join(reports));print(json.dumps(profiles,indent=2))
