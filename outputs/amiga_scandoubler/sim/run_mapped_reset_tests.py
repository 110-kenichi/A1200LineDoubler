import argparse,pathlib,subprocess,tempfile,os,hashlib
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--gowin-library',required=True);p.add_argument('--report',required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve();lib=pathlib.Path(a.gowin_library).resolve()
suffix='.exe' if os.name=='nt' else '';log=['Yosys Gowin cells_sim.v SHA256 '+hashlib.sha256(lib.read_bytes()).hexdigest()]
try:
    with tempfile.TemporaryDirectory(prefix='amiga_mapped_reset_') as temp:
        for n in [2,32,65]:
            exe=pathlib.Path(temp)/f'reset{n}.vvp';cmd=[bins/('iverilog'+suffix)]
            if suffix:cmd+=['-B',bins.parent/'lib/ivl']
            cmd+=['-g2012','-s','tb_mapped_reset',f'-Ptb_mapped_reset.CYCLES={n}','-o',exe,lib,root/f'synthesis/reset_{n}.v',root/'sim/tb_mapped_reset.sv']
            for c in [cmd,[bins/('vvp'+suffix),exe]]:
                result=subprocess.run([str(x) for x in c],capture_output=True,text=True,timeout=120)
                if result.stdout:log.append(result.stdout.strip());print(result.stdout.strip(),flush=True)
                if result.stderr:log.append(result.stderr.strip())
                if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log)+'\n',encoding='utf8')
