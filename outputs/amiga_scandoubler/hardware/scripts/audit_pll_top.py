from pathlib import Path
import pcbnew as p,json,re,collections,hashlib
h=Path(__file__).resolve().parents[1]
board=p.LoadBoard(str(h/'amiga_scandoubler_pll_top.kicad_pcb'));board.BuildConnectivity();conn=board.GetConnectivity()
fps={f.GetReference():f for f in board.GetFootprints()};m=json.loads((h/'circuit_manifest.json').read_text());progress=json.loads((h/'distribution_progress.json').read_text())
def pad(ref,num):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(num))
cache={}
def component(item):
    key=item.m_Uuid.AsString()
    if key in cache:return cache[key]
    todo=[item];seen=set()
    while todo:
        q=todo.pop();uid=q.m_Uuid.AsString()
        if uid in seen:continue
        seen.add(uid)
        todo.extend(list(conn.GetConnectedTracks(q))+list(conn.GetConnectedPads(q)))
    for uid in seen:cache[uid]=seen
    return seen
def connected(a,z):return pad(*z).m_Uuid.AsString() in component(pad(*a))
old=json.loads((h/'power_routing_report.json').read_text())
for a,z in old['verified_local_power_connections']:assert connected(a,z),(a,z)
sources={'3V3':('C56',1),'1V9':('C58',1),'1V2':('C60',1),'ADC_3V3A':('FB1',2),'ADC_1V9A':('FB2',2),'ADC_1V9PLL':('FB3',2),'DAC_3V3':('FB4',2)}
zone=next(iter(board.Zones()));filled=zone.GetFilledPolysList(p.In1_Cu);assert filled.OutlineCount()==1,filled.OutlineCount()
gv={v.m_Uuid.AsString() for v in board.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()=='GND' and filled.Contains(v.GetPosition())}
ground_checks=[];power_checks=[]
for record in progress['escapes']:
    endpoint=record['pad'];assert record['via_mm'],endpoint
    q=pad(*endpoint)
    if q.GetNetname()=='GND':assert component(q)&gv,endpoint;ground_checks.append(endpoint)
    else:
        source=sources[q.GetNetname()];assert connected(endpoint,source),(endpoint,source);power_checks.append([endpoint,source])
for record in progress['IC_grounds']:
    endpoint=record['pad'];assert component(pad(*endpoint))&gv,endpoint;ground_checks.append(endpoint)
for record in progress['connections']:
    a,z=record['from'],record['to'];assert connected(a,z),(a,z)
    source=sources[pad(*a).GetNetname()];assert connected(a,source),(a,source);power_checks.append([a,source])
analog=json.loads((h/'analog_progress.json').read_text())
for row in analog['connections']:assert connected(row['from'],row['to']),row
for endpoint in analog['ground_pads']:assert component(pad(*endpoint))&gv,endpoint
net_status={}
for net in analog['selected_nets']:
    qs=[q for f in fps.values() for q in f.Pads() if q.GetNetname()==net]
    net_status[net]=all(q.m_Uuid.AsString() in component(qs[0]) for q in qs)
for net in ['PLL_FILT1','PLL_FILT2','PLL_F','PLL_RC']:assert net_status[net],net
count=0
for ref,f in fps.items():
    for q in f.Pads():
        if q.GetNumber() in m['parts'][ref]['pins']:
            assert q.GetNetname()==(m['parts'][ref]['pins'][q.GetNumber()]['net'] or '');count+=1
assert len(fps)==135 and count==592
bb=board.GetBoardEdgesBoundingBox()
assert abs(p.ToMM(bb.GetWidth())-.05-95)<.001 and abs(p.ToMM(bb.GetHeight())-.05-95)<.001
assert board.GetCopperLayerCount()==4
assert p.WriteDRCReport(board,str(h/'pll_top_drc.txt'),p.EDA_UNITS_MILLIMETRES,True)
txt=(h/'pll_top_drc.txt').read_text();counts=dict(collections.Counter(re.findall(r'^\[([^]]+)\]',txt,re.M)))
for category in ['clearance','shorting_items','hole_clearance','hole_near_hole','courtyards_overlap','via_dangling','track_dangling','solder_mask_bridge','track_width','via_diameter','drill_out_of_range']:
    assert not counts.get(category),(category,counts.get(category))
lengths={net:sum(p.ToMM(t.GetLength()) for t in board.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net) for net in analog['selected_nets']}
for t in board.GetTracks():
    if t.GetNetname() in ['PLL_FILT1','PLL_FILT2','PLL_F','PLL_RC']:assert not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu
tracks=list(board.GetTracks());vias=[v for v in tracks if isinstance(v,p.PCB_VIA)]
result={'modified_decoupling_paths_require_requalification':True,'PLL_signal_vias':0,'analog_total_copper_length_mm':lengths,'analog_net_complete':net_status,'analog_connections_checked':len(analog['connections']),'additional_ground_returns':len(analog['ground_pads']),'status':'ANALOG_REVIEW_NOT_MANUFACTURING','parts':135,'pad_net_checks':count,'board_mm':[95,95],
 'previous_power_connections_rechecked':len(old['verified_local_power_connections']),
 'verified_supply_connections':power_checks,'verified_ground_plane_returns':ground_checks,
 'decoupling_pair_count':len(progress['connections']),'historical_v022_maximum_IC_to_cap_trace_mm':max(x['length_mm'] for x in progress['connections']),
 'track_segments':len(tracks)-len(vias),'through_vias':len(vias),'unconnected_items':conn.GetUnconnectedCount(False),'drc_categories':counts,
 'board_sha256':hashlib.sha256((h/'amiga_scandoubler_pll_top.kicad_pcb').read_bytes()).hexdigest()}
(h/'pll_top_report.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS 57 previous connections,',len(power_checks),'supply and',len(ground_checks),'ground checks;',count,'pad nets')
print('tracks',result['track_segments'],'vias',len(vias),'remaining',result['unconnected_items']);print(counts)
