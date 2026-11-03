from pathlib import Path
import sys,json,hashlib,collections,math
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
import nbtlib as n
R=ROOT/'runs'/sys.argv[1];src=R/'Machiya08.nbt';b=load_build(src,Limits(cells=1000000,nodes=3000000));sp=json.loads((R/'spec.json').read_text());errors=[]
blocks={q:v for q,v in b.blocks.items() if v!='minecraft:air'};f=n.load(src);entities={tuple(map(int,r['pos'])):str(r['nbt']['id']) for r in f['blocks'] if 'nbt'in r}
def block(q):return blocks.get(tuple(q),'minecraft:air')
for q,st in blocks.items():
 S.validate(st);name,pr=parse_state(st)
 if name.endswith('_bed'):
  d=S.DIRS[pr['facing']];other=tuple(q[i]+d[i]*(1 if pr['part']=='foot' else -1) for i in range(3));nn,pp=parse_state(block(other))
  if nn!=name or pp.get('part')==pr['part'] or pp.get('facing')!=pr['facing']:errors.append(['bed_pair',q])
  if entities.get(q)!='minecraft:bed':errors.append(['bed_entity',q])
 if name in ['minecraft:barrel','minecraft:furnace'] and entities.get(q)!=name:errors.append(['missing_entity',q])
 if name.startswith('minecraft:potted_') or name=='minecraft:flower_pot':
  under=(q[0],q[1]-1,q[2]);bb=S.boxes(block(under))
  if not any(v[4]>=1 and v[0]<=.4 and v[3]>=.6 and v[2]<=.4 and v[5]>=.6 for v in bb):errors.append(['pot_support',q])
 if name.endswith('_wall_banner'):
  d=S.DIRS[pr['facing']];under=tuple(q[i]-d[i] for i in range(3))
  if block(under)=='minecraft:air':errors.append(['banner_support',q])
# Check hanging lamp underside contact, rather than just any block in the cell above.
for light in sp['lights']:
 q=light['position'];name,pr=parse_state(block(q));support=light['support'];bb=S.boxes(block(support))
 if pr.get('hanging')=='true':ok=any(v[1]<=0 and v[0]<=.5<=v[3] and v[2]<=.5<=v[5]for v in bb)
 else:ok=any(v[4]>=1 and v[0]<=.5<=v[3] and v[2]<=.5<=v[5]for v in bb)
 if not ok:errors.append(['lamp_support',light])
for d in sp['doors']:
 x,y,z=d['pos'];nn,lo=parse_state(block((x,y,z)));nu,up=parse_state(block((x,y+1,z)))
 if nn!=nu or lo.get('half')!='lower' or up.get('half')!='upper' or any(lo.get(k)!=up.get(k) for k in ['facing','hinge','open']):errors.append(['door_pair',d['id']])
 if block(d['lintel'])=='minecraft:air':errors.append(['lintel',d['id']])
 ends=[(x-1,y,z),(x+1,y,z)] if d['facing'] in ['north','south'] else [(x,y,z-1),(x,y,z+1)]
 for e in ends:
  if not S.support_cube(block(e)):errors.append(['frame',d['id'],e])
# Player-body sampling with .6 width / 1.8 height; doors are treated open.
# This uses preview boxes, not official collision shapes. Edges are sampled too.
def free(x,z,floor):
 if not S.support_cube(block((int(x),floor,int(z)))):return False
 for xx in range(math.floor(x-.299),math.ceil(x+.299)):
  for zz in range(math.floor(z-.299),math.ceil(z+.299)):
   for yy in range(floor+1,floor+4):
    st=block((xx,yy,zz));name,pr=parse_state(st)
    if name.endswith('_door') or name.endswith('_carpet'):continue
    for v in S.boxes(st):
     a,c,e,aa,cc,ee=[v[i]+[xx,yy,zz][i%3] for i in range(6)]
     if x+.299>a+1e-4 and x-.299<aa-1e-4 and z+.299>e+1e-4 and z-.299<ee-1e-4 and floor+2.87>c+1e-4 and floor+1.07<cc-1e-4:return False
 return True
paths=[];reach={}
for floor in sp['floor_blocks']:
 valid={(x,z) for x in range(b.size[0]) for z in range(b.size[2]) if free(x+.5,z+.5,floor)}
 start=tuple(sp['floor_starts'][str(floor)])
 seen={start};queue=collections.deque([start])
 while queue:
  x,z=queue.popleft()
  for xx,zz in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
   if (xx,zz) not in valid or (xx,zz) in seen:continue
   if not all(free(x+.5+(xx-x)*t,z+.5+(zz-z)*t,floor) for t in [.25,.5,.75]):continue
   seen.add((xx,zz));queue.append((xx,zz))
 reach[floor]=len(seen)
 for u in sp['use_points']:
  if u['floor_block_y']!=floor:continue
  x,y,z=u['pos'];ok=(x,z)in seen;paths.append({**u,'reachable_sampled':ok})
  if not ok:errors.append(['approach',u])
out={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'errors':errors,'use_points':paths,'door_pairs':len(sp['doors']),'plant_groups':len(sp['plants']),'block_entities':len(entities),'reachable_cells_by_floor':reach,'game_checked':False,'aesthetic':'pending','scope':'NBT state/bed/door/entities/support + sampled preview-box movement with doors treated open; not client collision or interaction validation'}
(R/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'errors':errors,'use_points':len(paths),'reachable':reach},ensure_ascii=False));sys.exit(bool(errors))
