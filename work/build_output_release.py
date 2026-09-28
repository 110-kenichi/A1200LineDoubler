from pathlib import Path
import subprocess,os
base=Path(__file__).resolve().parents[1];r=base/'outputs/amiga_scandoubler';out=r/'implementation/output_release';out.mkdir(exist_ok=True)
suite=base/'work/tools/pnr_v015/oss-cad-suite';env=os.environ.copy();env['PATH']=str(suite/'lib')+os.pathsep+env['PATH'];env['PYTHONHOME']=str(suite)
for n in [1816,2048]:
    ys=(r/f'synthesis/board_{n}.ys').read_text().replace('rtl/amiga_logic_core.sv','rtl/dac_output_stage.sv rtl/amiga_logic_core.sv').replace('# Yosys 0.69;','# Yosys 0.69+24 (d0e71cfb7-dirty);').replace(f'synthesis/board_{n}.json',f'implementation/output_release/board_{n}.json')
    (out/f'board_{n}.ys').write_text(ys)
    commands=[['yosys.exe','-l',f'implementation/output_release/board_{n}_synthesis.log',f'implementation/output_release/board_{n}.ys'],
      ['nextpnr-himbaechel.exe','--device','GW1N-LV4QN88C6/I5','--vopt','family=GW1N-4','--json',f'implementation/output_release/board_{n}.json',
       '--vopt','cst=constraints/amiga_board_top.cst','--vopt','sspi_as_gpio','--sdc','implementation/exploratory_periods.sdc','--freq','56.75',
       '--write',f'implementation/output_release/board_{n}_routed.json','--report',f'implementation/output_release/board_{n}_timing.json',
       '--sdf',f'implementation/output_release/capture_{n}.sdf','--log',f'implementation/output_release/board_{n}_route.log']]
    for i,cmd in enumerate(commands):
        with (base/f'work/output_stage_{n}_{i}_stdout.txt').open('w') as log:
            p=subprocess.run([str(suite/'bin'/cmd[0]),*cmd[1:]],cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT)
        assert p.returncode==0,(n,cmd[0],p.returncode)
        print('PASS',n,cmd[0],flush=True)


