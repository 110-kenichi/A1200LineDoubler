# ERC follow-up (text edit, KiCad 7 schematic format 20230121): add PWR_FLAG to the 9 supply nets that have no
# power-output pin (supplies come through inductors / ferrites). Placed on 05_power, row y=256.54 (1.27 grid),
# each flag's pin on a new global label of the net. Library copy = KiCad 7.0.11 power.kicad_sym PWR_FLAG. PWR_FLAG is not in the BOM and has no footprint: board unchanged.
import re,sys,uuid,os
H=sys.argv[1];fn=os.path.join(H,'05_power.kicad_sch');s=open(fn,encoding='utf-8').read()
assert 'power:PWR_FLAG' not in s
ROOT='d7285cc1-01a7-52b5-b1b4-a16a6a4410c1';SHEET='9a882110-f218-58d3-9709-ffb02fc976d9'
NETS=['5V','3V3','1V9','1V2','ADC_3V3A','ADC_1V9A','ADC_1V9PLL','DAC_3V3','GND']
U=lambda:str(uuid.uuid4())
LIB=('(symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)\n'
 '(property "Reference" "#FLG" (id 0) (at 0 1.905 0) (effects (font (size 1.27 1.27)) hide))\n'
 '(property "Value" "PWR_FLAG" (id 1) (at 0 3.81 0) (effects (font (size 1.27 1.27))))\n'
 '(property "Footprint" "" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
 '(property "Datasheet" "~" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
 '(property "ki_keywords" "flag power" (id 4) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
 '(property "ki_description" "Special symbol for telling ERC where power comes from" (id 5) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
 '(symbol "PWR_FLAG_0_0" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))\n'
 '(symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none))))\n'
 ')\n')
s=s.replace('(lib_symbols ','(lib_symbols '+LIB,1)
body=[];inst=[]
y=256.54
for k,n in enumerate(NETS):
    x=round(50.8+k*33.02,2);su=U()
    body.append(f'(global_label "{n}" (shape passive) (at {x} {y} 180) (effects (font (size 0.9 0.9)) (justify right)) (uuid {U()}))')
    ref='#FLG%02d'%(k+1)
    body.append(f'(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (uuid {su})\n'
        f'(property "Reference" "{ref}" (id 0) (at {x} {round(y-1.905,3)} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Value" "PWR_FLAG" (id 1) (at {x} {round(y-3.81,2)} 0) (effects (font (size 1.0 1.0))))\n'
        f'(property "Footprint" "" (id 2) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Datasheet" "~" (id 3) (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(pin "1" (uuid {U()}))\n)')
    inst.append(f'(path "/{ROOT}/{SHEET}/{su}" (reference "{ref}") (unit 1) (value "PWR_FLAG") (footprint ""))')
body.append(f'(text "PWR_FLAG: supplies reach these nets through L / FB / fuse (no power-output pin). ERC only." (at 50.8 {round(y+6.35,2)} 0) (effects (font (size 1.2 1.2)) (justify left top)) (uuid {U()}))')
i=s.index('(sheet_instances');s=s[:i]+'\n'.join(body)+'\n'+s[i:]
i=s.index('(symbol_instances\n')+len('(symbol_instances\n');s=s[:i]+'\n'.join(inst)+'\n'+s[i:]
open(fn,'w',encoding='utf-8').write(s);print('added',len(NETS))
