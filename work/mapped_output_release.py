from pathlib import Path
import subprocess,os,hashlib
b=Path(__file__).resolve().parents[1];r=b/'outputs/amiga_scandoubler';d=r/'implementation/output_release'
s=b/'work/tools/pnr_v015/oss-cad-suite';env=os.environ.copy();env['PATH']=str(s/'lib')+os.pathsep+env['PATH']
ys='read_verilog -sv rtl/dac_output_stage.sv\nsynth_gowin -top dac_output_stage\nwrite_verilog -noattr implementation/output_release/dac_output_stage_mapped.v\n'
(d/'stage.ys').write_text(ys)
with (d/'stage_synthesis.log').open('w') as log:
    p=subprocess.run([str(s/'bin/yosys.exe'),'implementation/output_release/stage.ys'],cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0
bins=Path((b/'work/tools/simulator_path.txt').read_text().strip());lib=s/'share/yosys/gowin/cells_sim.v'
log=['Yosys cells_sim.v SHA256 '+hashlib.sha256(lib.read_bytes()).hexdigest()]
for cmd in [[bins/'iverilog.exe','-B',bins.parent/'lib/ivl','-g2012','-s','tb_dac_output_stage','-o',b/'work/mapped_stage.vvp',lib,d/'dac_output_stage_mapped.v',r/'sim/tb_dac_output_stage.sv'],[bins/'vvp.exe',b/'work/mapped_stage.vvp']]:
    p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);log.append(p.stdout+p.stderr);assert p.returncode==0,log
(r/'output_release_mapped_test.txt').write_text('\n'.join(log));print('\n'.join(log))

