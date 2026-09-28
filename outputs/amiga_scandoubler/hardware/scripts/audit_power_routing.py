from pathlib import Path
import pcbnew as p,json,re,collections,hashlib
out=Path(__file__).resolve().parents[2];h=out/'hardware'
board=p.LoadBoard(str(h/'amiga_scandoubler_routing.kicad_pcb'));board.BuildConnectivity();c=board.GetConnectivity()
fps={f.GetReference():f for f in board.GetFootprints()};manifest=json.loads((h/'circuit_manifest.json').read_text())
assert len(fps)==135
count=0
for ref,f in fps.items():
    for pad in f.Pads():
        if pad.GetNumber() in manifest['parts'][ref]['pins']:
            assert pad.GetNetname()==(manifest['parts'][ref]['pins'][pad.GetNumber()]['net'] or '')
            count+=1
assert count==592
def pad(ref,num):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(num))
def reach(a,z):
    pending=[a];seen=set();target=z.m_Uuid.AsString()
    while pending:
        item=pending.pop();key=item.m_Uuid.AsString()
        if key==target:return True
        if key in seen:continue
        seen.add(key)
        pending.extend(x for x in list(c.GetConnectedTracks(item))+list(c.GetConnectedPads(item)) if x.GetNetCode()==a.GetNetCode())
    return False
checks=[]
def check(a,z):
    assert reach(pad(*a),pad(*z)),(a,z)
    checks.append([a,z])
for i in range(3):
    u=f'U{7+i}';l=f'L{i+1}';ci=f'C{55+2*i}';co=f'C{56+2*i}';rt=f'R{27+2*i}';rb=f'R{28+2*i}'
    for a,z in [((u,2),(ci,1)),((u,2),('F1',2)),((u,2),('C54',1)),((u,7),(l,1)),((u,6),(co,1)),((l,2),(co,1)),((rt,1),(co,1)),((u,5),(rt,2)),((u,5),(rb,1)),((u,9),(u,1)),((u,9),(u,4)),((u,9),(ci,2)),((u,9),(co,2)),((u,9),(rb,2))]:check(a,z)
    if i<2:check((u,2),(u,3))
for number in ['A4','A9','B4','B9']:check(('J3',number),('F1',1))
for a,z in [(('J3','A5'),('R25',1)),(('J3','B5'),('R26',1)),(('U7',8),('U9',3)),(('U7',8),('R33',1)),(('U7',8),('R35',1)),(('U8',8),('U9',8)),(('U8',8),('R34',1)),(('C56',1),('R33',2)),(('C56',1),('R34',2))]:check(a,z)
zone=next(iter(board.Zones()));filled=zone.GetFilledPolysList(p.In1_Cu)
assert filled.OutlineCount()==1
ground_vias=[x for x in board.GetTracks() if isinstance(x,p.PCB_VIA) and x.GetNetname()=='GND']
assert all(filled.Contains(x.GetPosition()) for x in ground_vias)
ground_checks=[]
for endpoint in [('J3','A1'),('J3','A12'),('R25',2),('R26',2),('R35',2),('C54',2)]:
    assert any(reach(pad(*endpoint),v) for v in ground_vias),endpoint
    ground_checks.append(endpoint)
report=h/'power_routing_drc.txt';assert p.WriteDRCReport(board,str(report),p.EDA_UNITS_MILLIMETRES,True)
txt=report.read_text();counts=dict(collections.Counter(re.findall(r'^\[([^]]+)\]',txt,re.M)))
for category in ['clearance','shorting_items','hole_clearance','courtyards_overlap','via_dangling','solder_mask_bridge','track_width','via_diameter','drill_out_of_range']:
    assert counts.get(category,0)==0,(category,counts[category])
tracks=list(board.GetTracks());vias=[x for x in tracks if isinstance(x,p.PCB_VIA)]
bb=board.GetBoardEdgesBoundingBox();size=[p.ToMM(bb.GetWidth())-.05,p.ToMM(bb.GetHeight())-.05]
assert all(abs(x-95)<.001 for x in size),size
record={'status':'PARTIAL_POWER_ROUTING_NOT_FOR_MANUFACTURING','parts':len(fps),'checked_pad_occurrences':count,'board_mm':[95,95],
  'track_segments':len(tracks)-len(vias),'through_vias':len(vias),'filled_zones':len(list(board.Zones())),
  'verified_local_power_connections':checks,'verified_ground_plane_returns':ground_checks,'unconnected_count':c.GetUnconnectedCount(False),'drc_categories':counts,
  'minimum_default_clearance_mm':.2,'via_diameter_mm':.6,'via_drill_mm':.3,
  'routing_board_sha256':hashlib.sha256((h/'amiga_scandoubler_routing.kicad_pcb').read_bytes()).hexdigest(),
  'placement':{ref:{'x_mm':p.ToMM(f.GetPosition().x),'y_mm':p.ToMM(f.GetPosition().y),'angle_deg':f.GetOrientationDegrees()} for ref,f in fps.items()}}
(h/'power_routing_report.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS',len(checks),'local power connections;',count,'pad net assignments;',len(tracks)-len(vias),'tracks;',len(vias),'vias;',c.GetUnconnectedCount(False),'unconnected')
print(counts)
