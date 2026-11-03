"""Read back R08 geometry and compare curve behaviour against the delivered R07."""
from pathlib import Path
import sys,json,math
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'src'),str(P/'support')]
from vendor.inspect_build import load_build,Limits
from rail_nbt import curve_points
R=P/'runs'/sys.argv[1]
b=load_build(R/'RailDepot01.nbt',Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024))
net=json.loads((R/'rail_network.json').read_text())
errors=[]
# Independent test line has a continuous rail, supported formation and clear body corridor.
for x in range(40,181):
 assert b.blocks[x,7,164].startswith('create:track[')
 assert (x,6,164) in b.blocks
 for z in range(162,167):
  for y in range(8,14):
   if (x,y,z) in b.blocks:errors.append([x,y,z])
assert not errors,errors[:15]
for x in range(48,169):
 assert (x,8,168) in b.blocks
 assert (x,9,168) not in b.blocks and (x,10,168) not in b.blocks
# Explicit levels in a clear cross-section through the twin approach.
assert all((200,y,90) not in b.blocks for y in [5,6,7])
assert (200,4,90) in b.blocks
assert (200,6,80) in b.blocks and (200,6,100) in b.blocks
assert [z for x,y,z in b.blocks if x==80 and y==7 and z<149 and b.blocks[x,y,z].startswith('create:track[')]==[87,93]
assert [z for x,y,z in b.blocks if x==0 and y==7 and b.blocks[x,y,z].startswith('create:track[')]==[90]
# Utility pads have foundations; accesses meet the perimeter road without rail crossing.
for x,z in [(36,31),(109,60),(137,31),(193,57),(70,121),(143,141)]:
 assert all((x,y,z) in b.blocks for y in [4,5,6])
for x,z in [(55,29),(185,29),(135,146)]:
 assert (x,6,z) in b.blocks
 assert all((x,y,z) not in b.blocks for y in [7,8,9])
# New roof access and test-platform steps keep two cells of headroom.
for i in range(14):
 for z in range(32,35):
  x=143+i;y=7+i
  assert 'stairs' in b.blocks[x,y,z]
  assert all((x,y+d,z) not in b.blocks for d in [1,2])
# Actual upper-floor footprint is smaller than the middle floor, with core stairs preserved.
assert (103,50,200) in b.blocks
assert (103,86,200) not in b.blocks
assert (98,86,200) in b.blocks

def metrics(c):
 a=curve_points(c['a'],c['b'],2001);d=np.gradient(a,axis=0);dd=np.gradient(d,axis=0)
 curvature=np.linalg.norm(np.cross(d,dd),axis=1)/np.linalg.norm(d,axis=1)**3
 return {'a':c['a'],'b':c['b'],'max_heading_degrees':float(np.degrees(np.arctan2(abs(d[:,2]),d[:,0])).max()),'min_sampled_radius_blocks':float(1/curvature[2:-2].max())}
old=json.loads((P/'runs/R07/rail_network.json').read_text())
oldmetrics=[metrics(c) for c in old['curves']];newmetrics=[metrics(c) for c in net['curves']]
assert max(c['max_heading_degrees'] for c in newmetrics)<21
result={'baseline':'R07','source_nbt_sha256':json.loads((R/'spec.json').read_text())['source_nbt_sha256'],'old_max_heading_degrees':max(c['max_heading_degrees'] for c in oldmetrics),'new_max_heading_degrees':max(c['max_heading_degrees'] for c in newmetrics),'curve_metrics':newmetrics,'test_track_body_corridor_clear':True,'test_platform_route_clear':True,'three_grade_levels_verified':True,'single_external_interface_verified':True,'neck_axis_spacing':6,'utility_foundations_and_access_verified':True,'tank_stair_headroom_verified':True,'tower_setback_verified':True,'game':'not_run','engineering_certification':False}
(R/'redesign_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='curve_metrics'}))
