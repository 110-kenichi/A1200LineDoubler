"""Control-plane regression; use the same --bin-dir convention as run_tests.py."""
import argparse, pathlib, subprocess, tempfile, os
p=argparse.ArgumentParser()
p.add_argument('--bin-dir',required=True)
p.add_argument('--report',required=True)
a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else ''
log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_control_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        for module,half in [('i2c_register_write',6),('i2c_register_write',135),('adc_power_sequence',None)]:
            log.append('TEST '+module+(' HALF_CYCLES='+str(half) if half else ''))
            args=[bins/('iverilog'+suffix)]
            if suffix: args+=['-B',bins.parent/'lib/ivl']
            args+=['-g2012','-Wall','-s','tb_'+module]
            if half: args+=['-P','tb_'+module+'.HALF='+str(half)]
            args+=['-o',exe,root/'rtl'/(module+'.sv'),root/'sim'/('tb_'+module+'.sv')]
            for cmd in [args,[bins/('vvp'+suffix),exe]]:
                r=subprocess.run([str(x) for x in cmd],capture_output=True,text=True)
                if r.stdout: log.append(r.stdout.strip())
                if r.stderr: log.append(r.stderr.strip())
                if r.returncode: raise RuntimeError('\n'.join(log))
finally:
    pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
print('\n'.join(log))
