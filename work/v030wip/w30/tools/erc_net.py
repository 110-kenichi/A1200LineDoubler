# ERC substitute for KiCad 7 (its CLI has no ERC): checks on the netlist exported by
#   kicad-cli sch export netlist -o sch.net amiga_scandoubler.kicad_sch
# using the pin electrical types in the netlist. usage: erc_net.py sch.net [report.json]
import re,sys,json,collections
s=open(sys.argv[1],encoding='utf-8').read()
nets={}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)',s,re.S):
    nodes=[dict(ref=n.group(1),pin=n.group(2),func=n.group(3),type=n.group(4)) for n in
           re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))? \(pintype "([^"]+)"\)',m.group(2))]
    nets[m.group(1)]=nodes
DRV={'output','bidirectional','tri_state','power_out','open_collector','open_emitter','passive'}   # as KiCad: passive pins count as drivers
rep=collections.OrderedDict((k,[]) for k in ('error_pin_not_connected','error_output_conflict','warn_single_pin_net',
     'warn_input_not_driven','info_power_in_without_power_out','info_similar_names','ok_no_connect_pins'))
for name,nodes in nets.items():
    types=[n['type'].split('+')[0] for n in nodes]
    if name.startswith('unconnected-'):
        for n in nodes:
            (rep['ok_no_connect_pins'] if 'no_connect' in n['type'] else rep['error_pin_not_connected']).append('%s.%s %s (%s)'%(n['ref'],n['pin'],n['func'] or '',n['type']))
        continue
    if len(nodes)==1:rep['warn_single_pin_net'].append('%s: %s.%s'%(name,nodes[0]['ref'],nodes[0]['pin']))
    outs=[n for n in nodes if n['type'].split('+')[0]=='output']
    if len(outs)>1:rep['error_output_conflict'].append('%s: %s'%(name,', '.join('%s.%s'%(n['ref'],n['pin']) for n in outs)))
    if 'input' in types and not DRV & set(types):
        rep['warn_input_not_driven'].append('%s: inputs %s; others %s'%(name,','.join('%s.%s'%(n['ref'],n['pin']) for n in nodes if n['type'].startswith('input')),
            ','.join(sorted({'%s.%s'%(n['ref'],n['pin']) for n in nodes if not n['type'].startswith('input')}))[:120] or '-'))
    if 'power_in' in types and 'power_out' not in types:rep['info_power_in_without_power_out'].append('%s (%d power_in)'%(name,types.count('power_in')))
low=collections.defaultdict(list)
for name in nets:
    if not name.startswith('unconnected-'):low[re.sub(r'[^a-z0-9]','',name.split('/')[-1].lower())].append(name)
rep['info_similar_names']=[' / '.join(v) for v in low.values() if len(v)>1]
for k,v in rep.items():print('%-34s %d'%(k,len(v)));[print('   ',x) for x in v[:60]] if not k.startswith('ok_') else None
if len(sys.argv)>2:json.dump(rep,open(sys.argv[2],'w'),indent=1,ensure_ascii=False)
