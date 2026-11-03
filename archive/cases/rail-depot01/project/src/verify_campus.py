"""Independent final-NBT regression: all tracks, bridge approaches, shared podium."""
from pathlib import Path
import sys,json,math,collections
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'src'),str(P/'support')]
from vendor.inspect_build import load_build,Limits
from rail_nbt import curve_points
R=P/'runs'/sys.argv[1];lim=Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024)
b=load_build(R/'RailDepot01.nbt',lim);net=json.loads((R/'rail_network.json').read_text());sp=json.loads((R/'spec.json').read_text());campus=json.loads((R/'campus_revision.json').read_text())
owners=np.load(R/'owners.npz')['owners'];names=['none']+[q['id'] for q in sp['buildings']]
guard=set();bridgeguard=set()
for a,e,z in net['straight_lines']:
 for x in range(a,e):
  for zz in range(z-2,z+3):guard.add((x,zz))
  for zz in range(z-3,z+4):bridgeguard.add((x,zz))
for c in net['curves']:
 for x,y,z in curve_points(c['a'],c['b'],601):
  for xx in range(math.floor(x-3.5),math.ceil(x+3.5)):
   for zz in range(math.floor(z-3.5),math.ceil(z+3.5)):bridgeguard.add((xx,zz))
  for xx in range(math.floor(x-2.5),math.ceil(x+2.5)):
   for zz in range(math.floor(z-2.5),math.ceil(z+2.5)):guard.add((xx,zz))
bad=[];bridgebad=[]
for (x,y,z),st in b.blocks.items():
 cid=names[owners[y,z,x]]
 if (x,z) in guard and 8<=y<15:bad.append([x,y,z,cid])
 if cid=='bridges' and (x,z) in bridgeguard and 7<=y<18:bridgebad.append([x,y,z])
assert not bad,('all-track vehicle obstruction',len(bad),bad[:20])
assert not bridgebad,('bridge margin obstruction',len(bridgebad),bridgebad[:20])
routebad=[]
for q in campus['podium_routes']:
 x,y,z=q
 if (x,y-1,z) not in b.blocks or any((x,yy,z) in b.blocks for yy in range(y,y+3)):routebad.append(q)
assert not routebad,routebad[:10]
for q in campus['bridges']:
 bx=q['x'];z0,z1=q['z_span']
 for x in range(bx+1,bx+5):
  for z in range(z0,z1):
   assert (x,18,z) in b.blocks
   assert all((x,y,z) not in b.blocks for y in range(19,23)),(q['id'],x,z)
 for x,y,z in q['stairs']:
  assert 'stairs' in b.blocks.get((x,y,z),''),(x,y,z,'missing stair')
  assert all((x,y+dy,z) not in b.blocks for dy in [1,2]),(x,y,z,'stair headroom')
 # Low stair landings must be connected to supported ground, with no vertical jump.
 for x,y,z in q['stairs']:
  if y==7:
   dx=1 if x>bx else -1
   assert (x+dx,6,z) in b.blocks
   assert all((x+dx,yy,z) not in b.blocks for yy in [7,8]),(x,y,z,'landing')
for cid,(x,z,X,Z) in campus['utility_pads'].items():
 assert z==8
 for xx in range(x,X):
  assert b.blocks.get((xx,6,z)) is not None
 # Complete foundation, not a thin floating replacement skin.
 for xx in [x,X-1]:
  for zz in [z,Z-1]:assert all((xx,y,zz) in b.blocks for y in [4,5,6])
assert not [(x,y,z) for (x,y,z),st in b.blocks.items() if names[owners[y,z,x]]=='yardlights' and y>6]
# The approved tower above the three-storey podium remains byte-for-byte in block states.
old=load_build(P/'input/baseline_R12/RailDepot01.nbt',lim)
old_upper={p:s for p,s in old.blocks.items() if 63<=p[0]<105 and 172<=p[2]<221 and p[1]>=27}
new_upper={p:s for p,s in b.blocks.items() if 63<=p[0]<105 and 172<=p[2]<221 and p[1]>=27}
assert old_upper==new_upper,'upper tower changed'
oldbad=[p for p in old.blocks if (p[0],p[2]) in guard and 8<=p[1]<15]
assert any(251<=x<268 and 134<=z<=139 for x,y,z in oldbad),'old failed bridge regression missing'
result={'source_nbt_sha256':sp['source_nbt_sha256'],'all_straight_and_curved_tracks_checked':True,'vehicle_width_cells':5,'vehicle_clear_y':[8,15],'whole_yard_vehicle_obstructions':len(bad),'bridge_extra_lateral_margin_obstructions':len(bridgebad),'bridges':len(campus['bridges']),'bridge_deck_bottom_y':18,'bridge_bottom_above_rail_base':11,'bridge_stair_cells_checked':sum(len(q['stairs']) for q in campus['bridges']),'bridge_full_width_walkways_clear':True,'shared_podium_three_floors_connected':True,'upper_tower_state_identical':True,'utility_north_edges_z':8,'yard_lights_max_y':6,'baseline_R12_obstruction_cells':len(oldbad),'game':'not_run'}
(R/'campus_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
