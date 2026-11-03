from pathlib import Path
import sys,json,math,collections,hashlib,functools
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import terrain_states,nbtlib as n
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];src=R/'Komorebi09.nbt';b=load_build(src,Limits(cells=4000000,nodes=40000000));sp=json.loads((R/'spec.json').read_text());f=n.load(src);errors=[]
blocks=b.blocks;be={tuple(map(int,e['pos'])):e['nbt']for e in f['blocks']if'nbt'in e};H=np.load(R/'terrain_final.npy')
def block(q):return blocks.get(tuple(q),'minecraft:air')
@functools.lru_cache(None)
def boxes(st):return S.boxes(st)
for st in set(blocks.values()):S.validate(st)
for q,st in blocks.items():
 name,pr=parse_state(st)
 if name.endswith('_bed'):
  d=S.DIRS[pr['facing']];other=tuple(q[i]+d[i]*(1 if pr['part']=='foot'else -1)for i in range(3));nn,pp=parse_state(block(other))
  if nn!=name or pp.get('part')==pr['part']or pp.get('facing')!=pr['facing']:errors.append(['bed_pair',q])
  if str(be.get(q,{}).get('id',''))!='minecraft:bed':errors.append(['bed_entity',q])
 if name.startswith('minecraft:potted_')or name in ['minecraft:flower_pot','minecraft:sea_pickle']or name.endswith('_candle')or name.endswith('_carpet'):
  bb=boxes(block((q[0],q[1]-1,q[2])))
  if not any(v[4]>=1 and v[0]<=.5<=v[3]and v[2]<=.5<=v[5]for v in bb):errors.append(['small_object_support',q,name])
 if name.endswith('_wall_banner')or name.endswith('_wall_sign'):
  d=S.DIRS[pr['facing']];back=tuple(q[i]-d[i]for i in range(3))
  if block(back)=='minecraft:air':errors.append(['wall_attachment',q])
 if name.endswith('_leaves')and pr.get('persistent')!='true':errors.append(['decaying_leaves',q])
 if name in ['minecraft:tall_grass','minecraft:large_fern']:
  dy=1 if pr['half']=='lower'else -1;nn,pp=parse_state(block((q[0],q[1]+dy,q[2])))
  if nn!=name or pp.get('half')==pr['half']:errors.append(['double_plant',q])
for q,e in be.items():
 name,_=parse_state(block(q));expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:banner'if name.endswith('_wall_banner')else'minecraft:bed'if name.endswith('_bed')else name
 if str(e['id'])!=expected:errors.append(['be_type',q,name,str(e['id'])])
for bd in sp['buildings']:
 for d in bd['doors']:
  q=d['pos'];nn,lo=parse_state(block(q));nu,up=parse_state(block((q[0],q[1]+1,q[2])))
  if nn!=nu or lo.get('half')!='lower'or up.get('half')!='upper'or any(lo.get(k)!=up.get(k)for k in ['facing','hinge','open']):errors.append(['door_pair',d['id']])
  if block(d['lintel'])=='minecraft:air':errors.append(['lintel',d['id']])
  delta=(1,0,0)if d['facing']in ['north','south']else(0,0,1)
  for sign in [-1,1]:
   if not S.support_cube(block(tuple(q[i]+sign*delta[i]for i in range(3)))):errors.append(['frame',d['id']])
for l in sp['lights']:
 q=l['position'];pr=parse_state(block(q))[1];bb=boxes(block(l['support']));ok=any(v[1]<=0 and v[0]<=.5<=v[3]and v[2]<=.5<=v[5]for v in bb)if pr.get('hanging')=='true'else any(v[4]>=1 for v in bb)
 if not ok:errors.append(['lamp_support',q])
def hit(x,y,z,opened=True):
 lo=[x-.299,y+.07,z-.299];hi=[x+.299,y+1.8,z+.299];hits=[]
 for xx in range(math.floor(lo[0]),math.ceil(hi[0])):
  for zz in range(math.floor(lo[2]),math.ceil(hi[2])):
   for yy in range(math.floor(lo[1]),math.ceil(hi[1])):
    st=block((xx,yy,zz));name=parse_state(st)[0]
    if opened and(name.endswith('_door')or name.endswith('_carpet')):continue
    for bb in boxes(st):
     v=[bb[i]+[xx,yy,zz][i%3]for i in range(6)]
     if all(lo[i]<v[i+3]-1e-5 and hi[i]>v[i]+1e-5 for i in range(3)):hits.append([xx,yy,zz,st])
 return hits
@functools.lru_cache(None)
def free(x,z,floor):return S.support_cube(block((x,floor,z)))and not hit(x+.5,floor+1,z+.5)
def flood(valid,start):
 seen=set();queue=collections.deque([start])
 while queue:
  q=queue.popleft()
  if q in seen or q not in valid:continue
  seen.add(q);x,z=q;queue.extend([(x+1,z),(x-1,z),(x,z+1),(x,z-1)])
 return seen
# Route elevations are checked from final geometry; stairs add a standing surface above road base.
route={(x,z):h for x,z,h in sp['route_heights']};valid={}
for q,h in route.items():
 x,z=q;st=block((x,h+1,z));y=h+2 if '_stairs'in st else h+1
 if not hit(x+.5,y,z+.5)and boxes(block((x,y-1,z))):valid[q]=y
start=tuple(sp['spawn_local'][::2]);seen=set();queue=collections.deque([start])
while queue:
 q=queue.popleft()
 if q in seen or q not in valid:continue
 seen.add(q);x,z=q
 for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
  t=x+dx,z+dz
  if t in valid and abs(valid[q]-valid[t])<=1.01:queue.append(t)
# Each preserved room layout is separately flooded on its own slab; ground connects through entry.
records=[]
for bd in sp['buildings']:
 uses=[];h=bd['floor_y'];x0,_,z0,x1,_,z1=bd['bounds'];ex,ey,ez=bd['entry']
 outside=tuple(bd['front_outside'][::2]);outside_ok=outside in seen
 for floor in [h,h+5][:bd['floors']]:
  v={(x,z)for x in range(x0,x1)for z in range(z0,z1)if free(x,z,floor)}
  reach=flood(v,tuple(bd['floor_starts'][str(floor)]))
  for u in bd['use_points']:
   if u['floor_block_y']!=floor:continue
   x,y,z=u['pos'];ok=(x,z)in reach;uses.append({**u,'reachable':ok})
   if not ok:errors.append(['approach',u['id'],u['pos'],hit(x+.5,y,z+.5)])
 entry=(ex,ez)in seen and outside_ok
 if not entry:errors.append(['entry',bd['id'],bd['entry'],outside, outside_ok])
 records.append({'id':bd['id'],'entry_reachable':entry,'use_points':uses})
stairs=[]
for bd in sp['buildings']:
 h=bd['floor_y']
 for path in bd['stairs']:
  prev=h+1.;pp=[];bad=[]
  for x,_,z in path:
   tops=[]
   for xx in range(math.floor(x-.299),math.ceil(x+.299)):
    for zz in range(math.floor(z-.299),math.ceil(z+.299)):
     for yy in range(h-1,h+7):
      for bb in boxes(block((xx,yy,zz))):
       if xx+bb[0]<x+.299 and xx+bb[3]>x-.299 and zz+bb[2]<z+.299 and zz+bb[5]>z-.299 and prev-.51<=yy+bb[4]<=prev+.51:tops.append(yy+bb[4])
   y=max(tops)if tops else prev;hits=hit(x,y,z)
   if hits or not tops:bad.append({'at':[x,y,z],'hits':hits,'support':bool(tops)})
   pp.append([x,y,z]);prev=y
  if bad or abs(prev-(h+6))>.01:errors.append(['stairs',bd['id'],len(bad),prev])
  stairs.append({'id':bd['id'],'samples':len(pp),'end_y':prev,'collisions':bad,'pass':not bad and abs(prev-(h+6))<.01})
for rec in sp['groundcover']:
 x,y,z=rec['anchor']
 if(x,z)in route:errors.append(['plant_on_route',rec['anchor']])
 if not any(v in block((x,y-1,z))for v in ['grass_block','podzol']):errors.append(['plant_soil',rec['anchor']])
waters={(x,z):h for x,z,h in sp['water_levels']};waterissues=[]
for(x,z),h in waters.items():
 if not S.support_cube(block((x,int(H[x,z]),z))):waterissues.append(['water_bottom',x,z])
 for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
  q=x+dx,z+dz
  if q not in waters and 0<=q[0]<b.size[0]and 0<=q[1]<b.size[2]and not S.support_cube(block((q[0],h,q[1]))):waterissues.append(['water_side',x,z,dx,dz])
errors+=waterissues
uuids=set();paintings=[]
for en in f['entities']:
 e=en['nbt'];q=tuple(int(e[k])for k in['TileX','TileY','TileZ']);face=['south','west','north','east'][int(e['facing'])];d=S.DIRS[face];back=tuple(q[i]-d[i]for i in range(3));uid=tuple(map(int,e['UUID']))
 if uid in uuids or not S.support_cube(block(back))or block(q)!='minecraft:air':errors.append(['painting',q])
 if any(abs(float(e['Pos'][i])-(q[i]+.5-d[i]*.46875))>1e-7 for i in range(3)):errors.append(['painting_pos',q])
 uuids.add(uid);paintings.append({'anchor':q,'variant':str(e['variant'])})
# Explicit grade problem list for all declared centerline samples, rather than silently accepting steep roads.
road_gaps=[]
for road in sp['roads']:
 for x,_,z in road['points']:
  if(x,z)not in seen:road_gaps.append([road['id'],x,z])
summary={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'buildings':len(records),'entries_reachable':sum(v['entry_reachable']for v in records),'use_points':sum(len(v['use_points'])for v in records),'route_cells_reachable':len(seen),'route_centerline_unreachable':road_gaps,'tree_groups':len(sp['trees']),'groundcover_plants':len(sp['groundcover']),'paintings':len(paintings),'block_entities':len(be),'stair_flights':len(stairs),'mountain':sp['mountain'],'errors':errors,'scope':'final NBT states/support; approximate .6x1.8 player-body room and stair checks; exterior route graph permits <=1-block changes, including jumps; not continuous game navigation','game':'pending','aesthetic':'pending','fluid_simulation':'pending; checked containment, not live flowing water'}
(R/'audit.json').write_text(json.dumps({**summary,'building_records':records,'stair_records':stairs},ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False)[:14000]);sys.exit(bool(errors or road_gaps))
