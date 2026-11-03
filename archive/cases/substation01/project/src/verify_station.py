"""Independent final-NBT checks of selected architectural invariants, not electrical certification."""
from pathlib import Path
import sys,json,hashlib,collections
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'src'),str(P/'support'),str(P/'deps')]
import industrial_states
from vendor.inspect_build import load_build,Limits
R=P/'runs'/sys.argv[1];nbt=R/'Substation01.nbt';b=load_build(nbt,Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024));blocks=b.blocks
sp=json.loads((R/'spec.json').read_text());access=json.loads((R/'access.json').read_text());eq=json.loads((R/'equipment.json').read_text());errors=[];tot=collections.Counter()
def st(x,y,z):return blocks.get((x,y,z),'minecraft:air')
def clear(p,tag,height=2):
 x,y,z=p;tot[tag]+=1
 for yy in range(y,y+height):
  if st(x,yy,z)!='minecraft:air':errors.append([tag,'obstruction',[x,yy,z],st(x,yy,z)])
 if st(x,y-1,z)=='minecraft:air':errors.append([tag,'no_floor',p])
for x,z,X,Z in access['roads']:
 for xx in range(x,X):
  for zz in range(z,Z):clear((xx,7,zz),'road_5_high',5)
for p in access['walks']:clear(p,'interior_aisles')
# Both front and rear doors have supporting ground and a 3-block opening.
for x,z,X,Z in [(40,185,94,222),(112,185,194,222),(204,185,236,222)]:
 for xx in range(X-13,X-8):
  for zz in [z-1,z,z+1,Z-2,Z-1,Z]:clear((xx,7,zz),'building_entries',3)
for stair in access['stairs']:
 x,z,fy=stair['x'],stair['z'],stair['floor_y']
 for i in range(6):
  for xx in range(x,x+stair['width']):
   y=fy+i;zz=z-i;tot['stair_cells']+=1
   if 'stairs' not in st(xx,y,zz):errors.append(['stair_missing',[xx,y,zz]])
   for yy in [y+1,y+2]:
    if st(xx,yy,zz)!='minecraft:air':errors.append(['stair_headroom',[xx,yy,zz],st(xx,yy,zz)])
 # Side landing to upper floor.
 for xx in range(x,x+6):clear((xx,fy+6,z-6),'upper_landing')
# Source/isolated equipment counts and geometry character are verified independently.
assert sum(d['kind']=='three-winding main transformer' for d in eq['devices'])==2
assert sum(d['kind'].startswith('10 kV') for d in eq['devices'])==12
for cz in [64,122]:
 for zz in [cz-16,cz+16]:
  for xx in range(122,159):
   for y in range(7,24):
    tot['firewall_cells']+=1
    if st(xx,y,zz)=='minecraft:air':errors.append(['firewall_gap',[xx,y,zz]])
 for xx,zz in [(126,cz-12),(155,cz-12),(126,cz+12),(155,cz+12)]:
  if st(xx,4,zz)!='minecraft:cobblestone' or st(xx,5,zz)!='minecraft:air':errors.append(['basin_depth',[xx,zz]])
 for z in range(cz-9,cz+10,2):
  if st(128,10,z)=='minecraft:air':errors.append(['radiator_missing',[128,10,z]])
for z in range(150,162):
 if st(110,3,z)!='minecraft:stone_bricks' or any(st(110,y,z)!='minecraft:air' for y in [4,5,6]):errors.append(['inspection_trench',[110,z]])
for x,y,z in eq['lightpoints']:
 if st(x,y,z)!='minecraft:sea_lantern':errors.append(['flush_light_missing',[x,y,z]])
badmods=[s for s in set(blocks.values()) if not s.startswith('minecraft:')]
assert not badmods
assert hashlib.sha256(nbt.read_bytes()).hexdigest()==sp['source_nbt_sha256']
greens=sum(s.startswith(('minecraft:grass_block','minecraft:oak_leaves')) for s in blocks.values())
out={'source_nbt_sha256':sp['source_nbt_sha256'],'errors':errors,'counts':tot,'vanilla_only':True,'palette_count':len(set(blocks.values())),'green_blocks':greens,'surface_area_blocks':256*240,'electrical_simulation':False,'game':'not_run'}
(R/'geometry_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False));assert not errors
