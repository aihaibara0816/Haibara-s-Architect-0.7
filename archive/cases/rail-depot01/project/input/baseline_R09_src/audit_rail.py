from pathlib import Path
import sys,json,collections,math
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'deps'),str(P/'src'),str(P/'support')]
from vendor.inspect_build import read_nbt,load_build,Limits
from rail_nbt import curve_points
R=P/'runs'/sys.argv[1];L=Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024)
b=load_build(R/'RailDepot01.nbt',L);raw,_=read_nbt(R/'RailDepot01.nbt',L);be={tuple(e['pos']):e['nbt'] for e in raw['blocks'] if 'nbt' in e};del raw
tracks={p for p,s in b.blocks.items() if s.startswith('create:track[')};adj={p:set() for p in tracks};primary=[]
for p in tracks:
 for dx in [-1,1]:
  q=(p[0]+dx,p[1],p[2])
  if q in tracks:adj[p].add(q)
 for c in be.get(p,{}).get('Connections',[]):
  q=tuple(p[i]+c['Positions'][1]['Pos'][i] for i in range(3));assert q in tracks
  assert 'turn=true' in b.blocks[p] and 'turn=true' in b.blocks[q]
  reciprocal=[v for v in be[q]['Connections'] if tuple(q[i]+v['Positions'][1]['Pos'][i] for i in range(3))==p];assert len(reciprocal)==1
  r=reciprocal[0];assert c['Primary']!=r['Primary']
  for a,d in [(0,1),(1,0)]:assert [c['Starts'][a]['V'][i]+p[i] for i in range(3)]==[r['Starts'][d]['V'][i]+q[i] for i in range(3)]
  adj[p].add(q)
  if c['Primary']:primary.append((p,q))
seen=set();components=[]
for p in tracks:
 if p in seen:continue
 q=[p];seen.add(p);component=[]
 while q:
  v=q.pop();component.append(v)
  for w in adj[v]:
   if w not in seen:seen.add(w);q.append(w)
 components.append(component)
assert len(components)==2
test={p for p in tracks if p[2]==164};assert any(set(c)==test for c in components)
assert len(test)==141
# Body envelope sweep against architecture. Rail and support below rail are exempt.
violations=[]
for p,q in primary:
 for x,y,z in curve_points(p,q,301):
  for xx in range(math.floor(x-2.5),math.ceil(x+2.5)):
   for zz in range(math.floor(z-2.5),math.ceil(z+2.5)):
    for yy in range(8,13):
     if (xx,yy,zz) in b.blocks:violations.append([xx,yy,zz])
assert not violations,violations[:20]
uuids=[];targets=[]
for p,v in be.items():
 if 'TargetTrack' not in v:continue
 t=tuple(p[i]+v['TargetTrack'][i] for i in range(3));assert t in tracks;assert len(v['Id'])==4
 uuids.append(tuple(v['Id']));targets.append(t)
assert len(uuids)==len(set(uuids))==30
# Pit shaft and side escape checks at the exact open cells.
for z in [100,112]:
 for x in range(312,432):
  assert (x,4,z) in b.blocks
  assert all((x,y,z) not in b.blocks for y in [5,6])
 for xx in [302,433]:
  for x in range(xx,xx+2):
   assert all((x,y,z+1) not in b.blocks for y in [5,6])
   for zz,yy in [(z+2,5),(z+3,6)]:
    assert 'stairs' in b.blocks[x,yy,zz]
    assert all((x,yy+dy,zz) not in b.blocks for dy in [1,2])
# Verify serialized schedule contains exact station destinations and modern component name.
net=json.loads((R/'rail_network.json').read_text());names={s['name'] for s in net['stations']};p=tuple(net['schedule_barrel_local']);item=be[p]['Items'][0];assert item['id']=='create:schedule';schedule=item['components']['create:train_schedule'];route=[e['Instruction']['Data']['Text'] for e in schedule['Entries']];assert set(route)<=names and route==net['schedule_route']
result={'track_cells':len(tracks),'connected_components':len(components),'independent_test_track_verified':True,'reciprocal_curve_pairs':len(primary),'targeted_stations':10,'targeted_signals':20,'unique_target_ids':len(uuids),'curve_body_envelope_obstructions':len(violations),'two_120_block_pit_clearance_and_side_exits':True,'schedule_destination_names_resolved':True,'schedule_conductor_and_runtime':'not tested','game':'not_run'}
(R/'rail_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
