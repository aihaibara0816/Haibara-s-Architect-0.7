"""Independent final-NBT checks; body and step checks are offline approximations."""
from pathlib import Path
import sys,json,math,collections,functools,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n,qilou_states
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
from vanilla_preview import applications
R=ROOT/'runs'/sys.argv[1];sp=json.loads((R/'spec.json').read_text());vd=json.loads((R/'urban_records.json').read_text());src=R/'Qilou04.nbt';rb=load_build(src,Limits(cells=12_000_000,nodes=24_000_000));blocks=rb.blocks;f=n.load(src);errors=[];counts=collections.Counter()
bes={tuple(map(int,e['pos'])):e['nbt'] for e in f['blocks']if'nbt'in e}
def block(q):return blocks.get(tuple(q),'minecraft:air')
@functools.lru_cache(None)
def boxes(s):return S.boxes(s)
def hit(x,y,z):
 lo=[x-.299,y+.07,z-.299];hi=[x+.299,y+1.8,z+.299]
 for xx in range(math.floor(lo[0]),math.ceil(hi[0])):
  for zz in range(math.floor(lo[2]),math.ceil(hi[2])):
   for yy in range(math.floor(lo[1]),math.ceil(hi[1])):
    s=block((xx,yy,zz))
    if '_door['in s or '_carpet'in s:continue
    for bb in boxes(s):
     a=[bb[i]+[xx,yy,zz][i%3]for i in range(6)]
     if all(lo[i]<a[i+3]-1e-5 and hi[i]>a[i]+1e-5 for i in range(3)):return [xx,yy,zz,s]
 return None
def support(x,y,z):return any(bb[4]>=1 and bb[0]<=.5<=bb[3]and bb[2]<=.5<=bb[5]for bb in boxes(block((x,y,z))))
def flood(start,rect):
 x,y,z=start;X0,Z0,X1,Z1=rect;q=collections.deque([(x,z)]);seen=set();checked=set()
 while q:
  a,c=q.popleft()
  if(a,c)in checked:continue
  checked.add((a,c))
  if not(X0<=a<X1 and Z0<=c<Z1)or not support(a,y-1,c)or hit(a+.5,y,c+.5):continue
  seen.add((a,c));q.extend([(a+1,c),(a-1,c),(a,c+1),(a,c-1)])
 return seen
for s in set(blocks.values()):
 try:S.validate(s);assert applications(s)
 except Exception as e:errors.append(['state',s,str(e)])
for q,s in blocks.items():
 name,pr=parse_state(s)
 if name.endswith('_bed'):
  counts['bed_blocks']+=1;d=S.DIRS[pr['facing']];other=tuple(q[i]+d[i]*(1 if pr['part']=='foot'else-1)for i in range(3));nn,pp=parse_state(block(other))
  if nn!=name or pp.get('part')==pr['part']or pp.get('facing')!=pr['facing']:errors.append(['bed_pair',q,other])
  if str(bes.get(q,{}).get('id',''))!='minecraft:bed':errors.append(['bed_entity',q])
 if name.startswith('minecraft:potted_')or name=='minecraft:flower_pot'or name.endswith('_carpet'):
  counts['supported_small_props']+=1
  if not support(q[0],q[1]-1,q[2]):errors.append(['small_support',q,name,block((q[0],q[1]-1,q[2]))])
 if name.endswith('_leaves')and pr.get('persistent')!='true':errors.append(['leaf_decay',q])
for q,e in bes.items():
 name,_=parse_state(block(q));expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else name
 if str(e['id'])!=expected:errors.append(['block_entity_type',q])
for en in f['entities']:
 e=en['nbt'];q=tuple(int(e[k])for k in['TileX','TileY','TileZ']);d=S.DIRS[['south','west','north','east'][int(e['facing'])]];back=tuple(q[i]-d[i]for i in range(3))
 if not S.support_cube(block(back))or block(q)!='minecraft:air':errors.append(['painting',q,block(q)])
print('states and support',len(errors),flush=True)
reach=flood(sp['spawn_local'],[0,0,rb.size[0],rb.size[2]])
for e in sp['entries']:
 q=e['outside'];counts['external_entries']+=1
 if (q[0],q[2])not in reach:errors.append(['external_entry',e['id'],q])
for kind in ['road_cells','lane_cells']:
 for x,z in sp[kind]:
  if(x,z)not in reach or hit(x+.5,3,z+.5):errors.append(['public_path',kind,x,z])
counts['public_road_cells']=len(sp['road_cells']);counts['public_lane_cells']=len(sp['lane_cells'])
def tx(q,r,point=False):
 x,y,z=q;w,d=r['w'],r['d']
 for _ in range(r['turn']):x,z=d-(0 if point else 1)-z,x;w,d=d,w
 return[x+r['origin'][0],y+r['origin'][1],z+r['origin'][2]]
def stairtrack(line,fr,to):
 prev=fr+1;bad=[]
 for q in line:
  x,_,z=q;tops=[]
  for xx in range(math.floor(x-.299),math.ceil(x+.299)):
   for zz in range(math.floor(z-.299),math.ceil(z+.299)):
    for yy in range(fr,to+2):
     for bb in boxes(block((xx,yy,zz))):
      if xx+bb[0]<x+.299 and xx+bb[3]>x-.299 and zz+bb[2]<z+.299 and zz+bb[5]>z-.299 and prev-.51<=yy+bb[4]<=prev+.51:tops.append(yy+bb[4])
  y=max(tops)if tops else prev;hh=hit(x,y,z)
  if not tops or hh:bad.append([x,y,z,hh])
  prev=y
 return bad,prev
for r in sp['buildings']:
 if r['family']!='qilou':continue
 s=json.loads((R/(r['id']+'_spec.json')).read_text());b=r['geometry_bounds'];rect=[b[0][0],b[2][0],b[0][1],b[2][1]]
 cache={2:flood(tx(s['entry'],r),rect)}
 for fy,q in s['upper_starts'].items():cache[int(fy)]=flood(tx([q[0],int(fy)+1,q[1]],r),rect)
 for u in s['uses']:
  x,y,z=tx(u['pos'],r);counts['qilou_functional_approaches']+=1
  if(x,z)not in cache.get(u['floor_block_y'],set()):errors.append(['qilou_use',r['id'],u['id'],[x,y,z],hit(x+.5,y,z+.5)])
 for st in s['stair_runs']:
  bad,last=stairtrack([tx(q,r,True)for q in st['path']],st['from_floor'],st['to_floor']);counts['qilou_stair_links']+=1
  if bad or abs(last-st['to_floor']-1)>.01:errors.append(['qilou_stair',r['id'],st['from_floor'],bad[:2],last])
 for d in s['doors']:
  q=tx(d['pos'],r);name,lo=parse_state(block(q));nu,up=parse_state(block([q[0],q[1]+1,q[2]]));counts['paired_doors']+=1
  if not name.endswith('_door')or nu!=name or lo.get('half')!='lower'or up.get('half')!='upper':errors.append(['door_pair',r['id'],q])
 print('qilou',r['id'],len(errors),flush=True)
houses={r['id']:r['lot'] for r in sp['buildings']if r['family']=='village'};ee={e['id']:e for e in vd['entries']};rooms={r['id']:r for r in vd['rooms']};cache={};cores={}
for u in vd['units']:
 t=houses[u['building']];rect=[t['x']-3,t['z']-3,t['x']+t['w']+3,t['z']+t['d']+3];seen=flood(u['entry'],rect);cache[u['id']]=seen;counts['urban_units']+=1
 if not seen:errors.append(['unit_entry',u['id'],u['entry']])
 for rid in u['rooms']:
  for x,y,z in rooms[rid]['entrances']:
   if(x,z)not in seen:errors.append(['room_access',rid,[x,y,z]])
 key=(u['building'],u['floor'])
 if key not in cores:
  q=list(ee[u['building']]['core_landing']);q[1]=u['floor_y'];cores[key]=flood(q,rect)
 if(u['entry'][0],u['entry'][2])not in cores[key]:errors.append(['landing_to_unit',u['id']])
for st in vd['stairs']:
 counts['urban_stair_links']+=1
 for track in st['tracks']:
  for x,y,z in track:
   if hit(x+.5,y,z+.5)or block((x,y-1,z))=='minecraft:air':errors.append(['urban_stair',st['id'],[x,y,z],hit(x+.5,y,z+.5)])
for m in vd['modules']:
 x,y,z,X,Y,Z=m['bounds_xyz'];br=rooms[m['room_id']]['bounds_xyz'];adj={(a,c)for a in range(x-1,X+1)for c in range(z-1,Z+1)if (a<x or a>=X or c<z or c>=Z)and br[0]<=a<br[3]and br[2]<=c<br[5]};counts['urban_furniture']+=1
 if not(adj&cache[m['unit_id']]):errors.append(['furniture_access',m['component_id']])
report={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pass':not errors,'counts':dict(counts),'buildings':len(sp['buildings']),'states':len(set(blocks.values())),'block_entities':len(bes),'paintings':len(f['entities']),'errors':errors,'scope':'Independent NBT state/model availability, supported props, entry/room/furniture flood fill, approximate 0.6×1.8 body and stair records. Doors treated open. Not a Minecraft client test.','game_status':'pending'}
(R/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'pass':not errors,'counts':dict(counts),'errors':errors[:15],'error_count':len(errors)},ensure_ascii=False),flush=True)
raise SystemExit(bool(errors))
