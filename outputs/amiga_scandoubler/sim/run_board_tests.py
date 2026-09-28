import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_board_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp';cmd=[bins/('iverilog'+suffix)]
        if suffix:cmd+=['-B',bins.parent/'lib/ivl']
        cmd+=['-g2012','-Wall','-s','tb_board_startup','-o',exe]
        cmd+=[x for x in sorted((root/'rtl').glob('*.sv')) if x.name!='gowin_video_pll.sv']
        cmd+=[root/'sim/tb_board_startup.sv']
        for c in [cmd,[bins/('vvp'+suffix),exe]]:
            result=subprocess.run([str(x) for x in c],capture_output=True,text=True,timeout=120)
            if result.stdout:log.append(result.stdout.strip());print(result.stdout.strip(),flush=True)
            if result.stderr:log.append(result.stderr.strip())
            if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
