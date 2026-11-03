from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states,japanese_detail_states,corner_states
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
from detail_lab import states
import nbtlib
O=ROOT/'runs'/'after';src=O/'InteriorDetail05.nbt';b=load_build(src,Limits(cells=1000000,nodes=5000000));s=json.loads((O/'spec.json').read_text());errors=[]
blocks={p:v for p,v in b.blocks.items() if v!='minecraft:air'}
f=nbtlib.load(src);entitypos={tuple(map(int,x['pos'])):str(x['nbt']['id']) for x in f['blocks'] if 'nbt' in x}
for pos,st in blocks.items():
 states.validate(st);name,p=parse_state(st)
 if name.endswith('_bed'):
  off=states.DIRS[p['facing']];sign=1 if p['part']=='foot' else -1;q=tuple(a+sign*c for a,c in zip(pos,off));other=blocks.get(q,'');on,op=parse_state(other) if other else ('',{})
  if on!=name or op.get('facing')!=p['facing'] or op.get('part')==p['part']:errors.append(['bed_pair',pos])
  if entitypos.get(pos)!='minecraft:bed':errors.append(['bed_entity',pos])
 if name in ['minecraft:barrel','minecraft:furnace'] and entitypos.get(pos)!=name:errors.append(['entity_missing',pos])
 # Small table objects require a solid/top-slab support reaching the next cell.
 if name in ['minecraft:flower_pot','minecraft:potted_bamboo','minecraft:cake']:
  q=(pos[0],pos[1]-1,pos[2]);support=blocks.get(q,'minecraft:air');parts=states.boxes(support)
  if not any(a[4]>=1 and a[0]<=.4 and a[3]>=.6 and a[2]<=.4 and a[5]>=.6 for a in parts):errors.append(['prop_support',pos,support])
 if name.endswith('_wall_banner'):
  dx,dy,dz=states.DIRS[p['facing']];q=(pos[0]-dx,pos[1],pos[2]-dz)
  if q not in blocks:errors.append(['banner_support',pos])
paths=[]
def free(q):return blocks.get(q,'minecraft:air')=='minecraft:air' or blocks.get(q,'').split('[')[0].endswith('_carpet')
for r in s['rooms']:
 ox,f,oz=r['origin'];y=f+1
 valid={(x,y,z) for x in range(ox+1,ox+11) for z in range(oz+1,oz+12) if free((x,y,z)) and free((x,y+1,z)) and (x,f,z) in blocks}
 entry=tuple(r['entry']);seen={entry};queue=collections.deque([entry])
 while queue:
  x,y,z=queue.popleft()
  for q in [(x-1,y,z),(x+1,y,z),(x,y,z-1),(x,y,z+1)]:
   if q in valid and q not in seen:seen.add(q);queue.append(q)
 for c in s['components']:
  if not c['id'].startswith(r['id']+'.'):continue
  for point in c['use_points']:
   ok=tuple(point) in seen;paths.append({'component':c['id'],'point':point,'reachable_conservative_2high':ok})
   if not ok:errors.append(['use_point',c['id'],point])
 # Outer shell must remain intact except declared doorway/window; compares before.
base=load_build(ROOT/'runs/before/InteriorDetail05.nbt',Limits(cells=1000000,nodes=5000000));changes=[]
for r in s['rooms']:
 ox,f,oz=r['origin']
 for p,st in base.blocks.items():
  x,y,z=p
  if ox<=x<ox+12 and oz<=z<oz+12 and y in range(f+1,f+5) and (x in [ox,ox+11] or z in [oz,oz+11]) and blocks.get(p,'minecraft:air')!=st:changes.append(p)
# Authored beam cladding replaces only north-wall cells. East/south openings stay locked.
for p in changes:
 if not any(p[2]==r['origin'][2] for r in s['rooms']):errors.append(['shell_change',p])
out={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'nbt_readback':True,'registered_states':len(set(blocks.values())),'block_entities':len(entitypos),'bed_halves':sum(v=='minecraft:bed' for v in entitypos.values()),'use_points':paths,'errors':errors,'limitations':['Conservative whole-cell routes; not Minecraft collision/runtime tests','No resource-pack textures in rendered studies','No aesthetic acceptance implied'],'game_checked':False,'user_aesthetic':'pending','Corner01':'needs_revision'}
(O/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'errors':errors,'use_points':len(paths),'block_entities':len(entitypos)},ensure_ascii=False));sys.exit(bool(errors))
