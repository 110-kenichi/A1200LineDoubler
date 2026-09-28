import argparse,pathlib,subprocess,tempfile,os,hashlib
p=argparse.ArgumentParser();p.add_argument('--bin-dir',required=True);p.add_argument('--report',required=True)
p.add_argument('--gowin-library',help='Use the mapped stage instead of RTL with this Yosys cells_sim.v')
p.add_argument('--implementation',choices=['output_stage','output_release'],default='output_release')
a=p.parse_args();r=pathlib.Path(__file__).resolve().parents[1];bins=pathlib.Path(a.bin_dir).resolve();log=[]
suffix='.exe' if os.name=='nt' else ''
sources=[r/'rtl/dac_output_stage.sv']
if a.gowin_library:
    lib=pathlib.Path(a.gowin_library).resolve()
    log.append('Yosys cells_sim.v SHA256 '+hashlib.sha256(lib.read_bytes()).hexdigest())
    sources=[lib,r/f'implementation/{a.implementation}/dac_output_stage_mapped.v']
try:
    with tempfile.TemporaryDirectory(prefix='amiga_stage_') as tmp:
        exe=pathlib.Path(tmp)/'stage.vvp';cmd=[bins/('iverilog'+suffix)]
        if suffix:cmd+=['-B',bins.parent/'lib/ivl']
        cmd+=['-g2012','-s','tb_dac_output_stage','-o',exe,*sources,r/'sim/tb_dac_output_stage.sv']
        for command in [cmd,[bins/('vvp'+suffix),exe]]:
            result=subprocess.run(list(map(str,command)),capture_output=True,text=True)
            log.append(result.stdout+result.stderr)
            if result.returncode:raise RuntimeError('\n'.join(log))
finally:pathlib.Path(a.report).write_text('\n'.join(log),encoding='utf8')
print('\n'.join(log))
