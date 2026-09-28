import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_adc_boot_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        for n,half,alc in [(1816,6,20),(1820,6,20),(2048,6,20),(1816,135,810000)]:
            cmd=[bins/('iverilog'+suffix)]
            if suffix:cmd+=['-B',bins.parent/'lib/ivl']
            cmd+=['-g2012','-Wall','-s','tb_tvp7002_boot','-P',f'tb_tvp7002_boot.N={n}',
                  '-P',f'tb_tvp7002_boot.HALF={half}','-P',f'tb_tvp7002_boot.ALC_WAIT={alc}','-o',exe]
            cmd+=[root/'rtl'/f for f in ['adc_power_sequence.sv','i2c_register_write.sv','tvp7002_boot.sv']]
            cmd+=[root/'sim/tb_tvp7002_boot.sv']
            for c in [cmd,[bins/('vvp'+suffix),exe]]:
                r=subprocess.run([str(x) for x in c],capture_output=True,text=True)
                if r.stdout:log.append(r.stdout.strip());print(r.stdout.strip(),flush=True)
                if r.stderr:log.append(r.stderr.strip())
                if r.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
