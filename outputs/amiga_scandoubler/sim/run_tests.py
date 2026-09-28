"""Run with Python 3 and --bin-dir pointing to an Icarus Verilog bin folder."""
import argparse
import pathlib
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--bin-dir', required=True)
p.add_argument('--report', required=True)
a = p.parse_args()
root = pathlib.Path(__file__).resolve().parents[1]
bins = pathlib.Path(a.bin_dir).resolve()
suffix = '.exe' if __import__('os').name == 'nt' else ''
log = []

def run(args):
    if pathlib.Path(args[0]).name == 'iverilog.exe':
        args = args[:1] + ['-B', bins.parent/'lib/ivl'] + args[1:]
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.stdout: log.append(result.stdout.strip())
    if result.stderr: log.append(result.stderr.strip())
    if result.returncode:
        raise RuntimeError('\n'.join(log))

try:
    with tempfile.TemporaryDirectory(prefix='amiga_rtl_') as temp:
        exe = pathlib.Path(temp) / 'sim.vvp'
        for n in (32, 1816, 1820, 2048):
            run([bins / ('iverilog'+suffix), '-g2012', '-Wall', '-s', 'tb_line_double',
                 '-P', 'tb_line_double.N='+str(n), '-o', exe,
                 root/'rtl/line_double.sv', root/'sim/tb_line_double.sv'])
            run([bins/('vvp'+suffix), exe])
        for lines in (524, 525, 624, 625, 626):
            run([bins/('iverilog'+suffix), '-g2012', '-Wall', '-s', 'tb_field_sync',
                 '-P', 'tb_field_sync.FIELD_LINES='+str(lines),
                 '-o', exe, root/'rtl/field_sync.sv', root/'sim/tb_field_sync.sv'])
            run([bins/('vvp'+suffix), exe])
finally:
    pathlib.Path(a.report).write_text('\n'.join(log)+'\n', encoding='utf-8')
print('\n'.join(log))
