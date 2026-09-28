import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_video_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        for n,lines in [(32,l) for l in [524,525,624,625,626]]+[(1816,625)]:
            cmd=[bins/('iverilog'+suffix)]
            if suffix:cmd+=['-B',bins.parent/'lib/ivl']
            cmd+=['-g2012','-Wall','-s','tb_video_core','-P','tb_video_core.N='+str(n),'-P','tb_video_core.FIELD_LINES='+str(lines),'-o',exe]
            cmd+=[root/'rtl'/f for f in ['line_double.sv','field_sync.sv','video_core.sv']]+[root/'sim/tb_video_core.sv']
            for c in [cmd,[bins/('vvp'+suffix),exe]]:
                r=subprocess.run([str(x) for x in c],capture_output=True,text=True)
                if r.stdout:log.append(r.stdout.strip());print(r.stdout.strip(),flush=True)
                if r.stderr:log.append(r.stderr.strip())
                if r.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
