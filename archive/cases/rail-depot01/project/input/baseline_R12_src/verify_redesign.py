"""Read-back checks for the current twin-interface yard revision."""
from pathlib import Path
import sys,json,math
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'src'),str(P/'support')]
from vendor.inspect_build import load_build,Limits
from rail_nbt import curve_points
R=P/'runs'/sys.argv[1]
b=load_build(R/'RailDepot01.nbt',Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024));net=json.loads((R/'rail_network.json').read_text());yard=json.loads((R/'yard_revision.json').read_text())
tracks={p for p,s in b.blocks.items() if s.startswith('create:track[')}
assert sorted(z for x,y,z in tracks if x==0)==[87,93]
assert not any(z==164 for x,y,z in tracks)
assert sorted(z for x,y,z in tracks if x==430)==[20,32,44,56,68,80,100,112,124,136]
errors=[]
for x in range(40,181):
 assert (x,7,135) in tracks and (x,6,135) in b.blocks
 for z in range(133,138):
  for y in range(8,14):
   if (x,y,z) in b.blocks:errors.append([x,y,z])
assert not errors,errors[:15]
for x in range(48,169):
 assert (x,8,139) in b.blocks
 assert all((x,y,139) not in b.blocks for y in [9,10])
# Reclaimed northern road contains exposed new track formations, not traffic markings.
assert (400,7,20) in tracks
assert (400,6,15) not in b.blocks
assert b.blocks[400,4,15]!='minecraft:white_concrete'
for z,start in [(32,354),(20,354)]:
 for x in range(start,454):
  assert (x,7,z) in tracks and (x,6,z) in b.blocks
  assert all((x,y,zz) not in b.blocks for y in range(8,14) for zz in range(z-2,z+3))
# Each authored step rim is present in the final file, not just in the planning record.
wrong=[q for q in yard['step_borders'] if b.blocks.get(tuple(q))!='minecraft:gray_concrete']
assert not wrong,wrong[:12]
assert len(yard['lamp_groups'])>=30
for q in yard['lamp_groups']:
 x,y,z=q['pole'];assert 'iron_bars' in b.blocks[x,y,z]
 if 'clear_axis_gap' in q:assert q['clear_axis_gap']>=10
assert len(yard['flush_guide_lights'])>=100
for q in yard['flush_guide_lights']:assert b.blocks[tuple(q)]=='minecraft:sea_lantern'
# Equipment foundations and the access landing/stair were moved with their facilities.
for x,z in [(207,8),(280,28),(137,23),(193,49)]:assert all((x,y,z) in b.blocks for y in [4,5,6])
for i in range(14):
 for z in range(24,27):
  x=143+i;y=7+i;assert 'stairs' in b.blocks[x,y,z];assert all((x,y+d,z) not in b.blocks for d in [1,2])
assert (103,50,200) in b.blocks and (103,86,200) not in b.blocks and (98,86,200) in b.blocks
for x in [45,86,125,167]:assert 'oak_log' in b.blocks[x,9,145]
metrics=[]
for c in net['curves']:
 a=curve_points(c['a'],c['b'],2001);d=np.gradient(a,axis=0);dd=np.gradient(d,axis=0);k=np.linalg.norm(np.cross(d,dd),axis=1)/np.linalg.norm(d,axis=1)**3
 metrics.append({'a':c['a'],'b':c['b'],'max_heading_degrees':float(np.degrees(np.arctan2(abs(d[:,2]),d[:,0])).max()),'min_sampled_radius_blocks':float(1/k[2:-2].max())})
assert max(c['max_heading_degrees'] for c in metrics)<21
result={'baseline':'R09','source_nbt_sha256':json.loads((R/'spec.json').read_text())['source_nbt_sha256'],'double_external_interface_verified':True,'external_axis_spacing':6,'main_track_count':10,'group_counts':[6,4],'independent_lane_z':135,'test_track_body_corridor_clear':True,'test_platform_route_clear':True,'north_road_removed':True,'all_authored_step_borders_intact':True,'lamp_group_count':len(yard['lamp_groups']),'flush_light_count':len(yard['flush_guide_lights']),'new_max_heading_degrees':max(c['max_heading_degrees'] for c in metrics),'curve_metrics':metrics,'relocated_equipment_foundations_and_stairs_verified':True,'tree_count':4,'game':'not_run','lighting_simulation':'offline only'}
(R/'redesign_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='curve_metrics'}))
