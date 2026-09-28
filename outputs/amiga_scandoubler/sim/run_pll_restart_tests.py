import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_pll_restart_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        for module,full in [('pll_restart_control',False),('pll_restart_control',True),('clock_recovery_system',False)]:
            cmd=[bins/('iverilog'+suffix)]
            if suffix:cmd+=['-B',bins.parent/'lib/ivl']
            cmd+=['-g2012','-Wall','-s','tb_'+module,'-o',exe]
            if full:cmd+=['-P','tb_pll_restart_control.HOLD=270','-P','tb_pll_restart_control.TIMEOUT=270000']
            cmd+=[root/'rtl'/f for f in ['video_clock_guard.sv','pll_restart_control.sv','clock_recovery_system.sv']]
            cmd+=[root/'sim'/('tb_'+module+'.sv')]
            for c in [cmd,[bins/('vvp'+suffix),exe]]:
                result=subprocess.run([str(x) for x in c],capture_output=True,text=True)
                if result.stdout:log.append(result.stdout.strip());print(result.stdout.strip(),flush=True)
                if result.stderr:log.append(result.stderr.strip())
                if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
