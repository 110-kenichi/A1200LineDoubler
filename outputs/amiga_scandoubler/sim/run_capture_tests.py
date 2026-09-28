import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True);p.add_argument('--phase',type=int,choices=[90,180],default=180)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_capture_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        for period in [41667,35242,34921,31000]:
            for duty in [48,50,52]:
                for delay in [0,1500]:
                    cmd=[bins/('iverilog'+suffix)]
                    if suffix:cmd+=['-B',bins.parent/'lib/ivl']
                    cmd+=['-g2012','-Wall','-s','tb_adc_rgb_capture','-o',exe]
                    for key,value in [('PERIOD_PS',period),('DUTY_PERCENT',duty),('DATA_DELAY_PS',delay),('PHASE_DEGREES',a.phase)]:
                        cmd+=['-P',f'tb_adc_rgb_capture.{key}={value}']
                    cmd+=[root/'rtl/adc_rgb_capture.sv',root/'sim/tb_adc_rgb_capture.sv']
                    for c in [cmd,[bins/('vvp'+suffix),exe]]:
                        result=subprocess.run([str(x) for x in c],capture_output=True,text=True)
                        if result.stdout:log.append(result.stdout.strip());print(result.stdout.strip(),flush=True)
                        if result.stderr:log.append(result.stderr.strip())
                        if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
