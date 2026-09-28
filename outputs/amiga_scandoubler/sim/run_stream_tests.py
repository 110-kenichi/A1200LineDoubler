import argparse,pathlib,subprocess,tempfile,os
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve()
suffix='.exe' if os.name=='nt' else '';log=[]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_stream_') as temp:
        exe=pathlib.Path(temp)/'sim.vvp'
        cases=[('stream_sync_frontend',32,l,7) for l in [524,525,624,625,626]]
        cases += [('stream_sync_frontend',32,625,0),('stream_sync_frontend',1816,625,31),('stream_input_video',0,0,0)]
        for module,n,fl,align in cases:
            cmd=[bins/('iverilog'+suffix)]
            if suffix:cmd+=['-B',bins.parent/'lib/ivl']
            cmd+=['-g2012','-Wall','-s','tb_'+module,'-o',exe]
            if n:
                for key,value in [('N',n),('FL',fl),('ALIGN',align)]:cmd+=['-P',f'tb_{module}.{key}={value}']
            cmd+=[root/'rtl'/f for f in ['line_double.sv','field_sync.sv','video_core.sv','stream_sync_frontend.sv','stream_input_video.sv']]
            cmd+=[root/'sim'/('tb_'+module+'.sv')]
            for c in [cmd,[bins/('vvp'+suffix),exe]]:
                result=subprocess.run([str(x) for x in c],capture_output=True,text=True)
                if result.stdout:log.append(result.stdout.strip());print(result.stdout.strip(),flush=True)
                if result.stderr:log.append(result.stderr.strip())
                if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
