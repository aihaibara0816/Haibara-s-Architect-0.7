from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from vendor.inspect_build import load_build,Limits
from detail_lab import states
R=C/'runs'/sys.argv[1];rb=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));B=rb.blocks
sp=json.loads((R/'site_records.json').read_text());checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,pass_=bool(ok),detail=detail))
air=lambda p:B.get(tuple(p),'minecraft:air')=='minecraft:air'
check('building_count_18',len(sp['buildings'])==18)
check('uses_8_homes_6_shops_4_public',collections.Counter(h['use'] for h in sp['buildings'])==dict(home=8,sweets=1,miso=1,tea=1,tavern=1,stationery=1,rice=1,inn=1,bath=1,community=1,shrine=1))
over=[]
for i,h in enumerate(sp['buildings']):
 for j in sp['buildings'][i+1:]:
  if h['x']<j['x']+j['w'] and j['x']<h['x']+h['w'] and h['z']<j['z']+j['d'] and j['z']<h['z']+h['d']:over.append([h['id'],j['id']])
check('building_footprints_do_not_overlap',not over,over)
bad=[]
for e in sp['entrances']:
 for k in ['inside','outside']:
  p=e[k]
  if not air(p) or not air([p[0],p[1]+1,p[2]]):bad.append([e['building'],k,p,B.get(tuple(p))])
check('all_door_leaf_inside_outside_two_cell_clearance',not bad,bad)
bad=[]
for p in sp['stair_clearance_samples']:
 if not air(p) or not air([p[0],p[1]+1,p[2]]):bad.append([p,B.get(tuple(p)),B.get((p[0],p[1]+1,p[2]))])
check('stairs_2_wide_two_cell_clearance',not bad,bad[:20])
bad=[]
for r in sp['connections']:
 path=r['path'];dx=abs(path[-1][0]-path[0][0]);dz=abs(path[-1][2]-path[0][2])
 for p in path:
  for a in [-1,0,1]:
   x,y,z=p; x+=a if dz>=dx else 0;z+=a if dx>dz else 0
   if not air([x,y,z]) or not air([x,y+1,z]):bad.append([r['building'],[x,y,z],B.get((x,y,z)),B.get((x,y+1,z))])
check('three_cell_entry_paths_clear',not bad,bad[:30])
bad=[]
for h in sp['buildings']:
 for x,y,z in h.get('stair_landing_samples',[]):
  if not air([x,y,z]) or not air([x,y+1,z]) or (x,y-1,z) not in B:bad.append([h['id'],x,y,z])
check('upper_stair_landings_clear_and_supported',not bad,bad)
lights=[]
for room in sp['rooms']:
 h=next(h for h in sp['buildings'] if h['id']==room['building']);y=room['ceiling_y']
 n=sum(1 for (x,yy,z),s in B.items() if y-1<=yy<=y and h['x']<=x<h['x']+h['w'] and h['z']<=z<h['z']+h['d'] and any(k in s for k in ['glowstone','sea_lantern','lantern']))
 lights.append([room['id'],n])
check('occupied_floors_have_supported_ceiling_lights',all(v>0 for _,v in lights),lights)
water=[q for q,s in B.items() if s.startswith('minecraft:water')];bad=[]
for x,y,z in water:
 for dx,dy,dz in [(0,-1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]:
  q=(x+dx,y+dy,z+dz)
  if q not in B:bad.append(q)
check('drain_water_has_bottom_and_side_containment',not bad,bad[:20])
state_errors=[]
for s in set(B.values()):
 try:states.validate(s)
 except Exception as e:state_errors.append([s,str(e)])
check('registered_vanilla_blockstates',not state_errors,state_errors)
bad=[]
for (x,y,z),st in B.items():
 if states.family(st) not in ['candle','pot']:continue
 below=B.get((x,y-1,z));ok=False
 if below:
  from vendor.voxel_core import parse_state
  name,pr=parse_state(below);ok=states.support_cube(below) or (states.family(below)=='slab' and pr['type'] in ['top','double'])
 if not ok:bad.append([x,y,z,st,below])
check('display_candles_and_pots_have_level_support',not bad,bad)
plants=[q for q,s in B.items() if states.family(s) in ['flower','crop']]
check('ground_plants_supported',all((x,y-1,z) in B for x,y,z in plants),len(plants))
path_support=[]
for r in sp['connections']:
 for x,y,z in r['path']:
  if (x,y-1,z) not in B:path_support.append([x,y,z])
check('entry_paths_have_support',not path_support,path_support)
steep=[]
for r in sp['connections']:
 for a,z in zip(r['path'],r['path'][1:]):
  if abs(a[1]-z[1])>1 or (a[0]==z[0] and a[2]==z[2] and a[1]!=z[1]):steep.append([r['building'],a,z])
check('path_steps_at_most_one_block_and_no_vertical_duplicates',not steep,steep)
if sp['site']['size_xyz'][0]==160:
 from PIL import Image,ImageDraw
 mask=Image.new('1',(rb.size[0],rb.size[2]));dr=ImageDraw.Draw(mask)
 for r in sp['roads']:
  if r['kind']=='asphalt':dr.line([tuple(q) for q in r['path']],fill=1,width=r['width'])
 roadbad=[]
 for z,x in zip(*np.where(np.array(mask))):
  for y in [5,6,7]:
   if (int(x),y,int(z)) in B:roadbad.append([int(x),y,int(z),B[int(x),y,int(z)]])
 check('vehicle_road_three_cell_clearance',not roadbad,roadbad[:20])
 bannerbad=[];lampbad=[]
 for (x,y,z),st in B.items():
  if '_wall_banner' in st:
   facing=states.parse_state(st)[1]['facing'] if hasattr(states,'parse_state') else None
   dx,_,dz=states.DIRS[facing];support=B.get((x-dx,y,z-dz))
   if not support:bannerbad.append([x,y,z,st])
  if 'minecraft:lantern[hanging=true' in st and (x,y+1,z) not in B:lampbad.append([x,y,z])
 check('wall_banners_have_attachment_block',not bannerbad,bannerbad)
 check('hanging_lanterns_have_support_above',not lampbad,lampbad)
out=dict(source_nbt_sha256=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),checks=checks,block_count=len(B),file_status='readback exact in build exporter',geometry='pass' if all(c['pass_'] for c in checks) else 'fail',preview='pending',game='pending; client not run',limitations=['Door opening, stair collision and banner appearance need game test','Furniture decorative','Water containment is voxel enclosure only'])
(R/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'geometry':out['geometry'],'checks':[(x['name'],x['pass_']) for x in checks],'failures':[x for x in checks if not x['pass_']]},ensure_ascii=False,indent=2));sys.exit(0 if out['geometry']=='pass' else 1)
