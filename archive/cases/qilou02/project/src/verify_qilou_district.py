"""Independent replay, bounded seed variation and rotated assembly comparison."""
from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support')]
import qilou_states
from detail_lab import states as S
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
RUN=sys.argv[1];R=ROOT/'runs'/RUN;V=ROOT/'runs'/(RUN+'_VARIANT')
limits=Limits(cells=2000000,nodes=8000000)
read=lambda p:json.loads(p.read_text())
sp=read(R/'spec.json');vp=read(V/'spec.json');groups=['Qilou02']+[b['id']for b in sp['buildings']]
replay={g:(R/(g+'.nbt')).read_bytes()==(ROOT/'runs'/(RUN+'_REPLAY')/(g+'.nbt')).read_bytes()for g in groups}
assert all(replay.values()),replay
whole=load_build(R/'Qilou02.nbt',limits);variant=load_build(V/'Qilou02.nbt',limits)
def transform(q,r):
 x,y,z=q;w,d=r['w'],33
 for i in range(r['turn']):x,z=d-1-z,x;w,d=d,w
 return tuple([x+r['origin'][0],y+r['origin'][1],z+r['origin'][2]])
def rotate(st,k):
 for i in range(k):st=S.rotate_state(st)
 return st
def changes(a,b):
 return [(q,a.get(q,'minecraft:air'),b.get(q,'minecraft:air'))for q in sorted(set(a)|set(b))if a.get(q,'minecraft:air')!=b.get(q,'minecraft:air')]
assembly=[];bad=[];allowed_world=set();local_variations=[]
for bd in sp['buildings']:
 local=load_build(R/(bd['id']+'.nbt'),limits);other=load_build(V/(bd['id']+'.nbt'),limits)
 ls=read(R/(bd['id']+'_spec.json'));vs=read(V/(bd['id']+'_spec.json'))
 for key in ['placement','floors','doors','uses','stair_runs','rooms','arcade_cells_local']:
  assert ls[key]==vs[key],(bd['id'],key)
 missing=[];count=0;connection_updates=[]
 for q,st in local.blocks.items():
  if q[1]<=2 and not 3<=q[2]<=28:continue
  p=transform(q,bd);expect=rotate(st,bd['turn']);actual=whole.blocks.get(p,'minecraft:air');count+=1
  if expect!=actual:
   en,ep=parse_state(expect);an,ap=parse_state(actual)
   if en==an and ('_pane' in en or en=='minecraft:iron_bars')and {k:v for k,v in ep.items()if k not in S.DIRS}=={k:v for k,v in ap.items()if k not in S.DIRS}:connection_updates.append(p)
   else:missing.append([p,expect,actual])
 assert not missing,(bd['id'],missing[:10])
 assembly.append({'id':bd['id'],'compared_non_air':count,'mismatches':len(missing),'pane_boundary_connection_updates':len(connection_updates)})
 scope_counts=collections.Counter();top=15 if bd['levels']==2 else 21
 shutter_x=[1,6,9,14]if bd['w']>=17 else[1,6,8,13]
 shutter_z=26 if bd['kind']=='classical'else 29
 shutter_cells={(x,f+dy,shutter_z)for f in bd['floors'][1:]for dy in[2,3]for x in shutter_x if x<bd['w']}
 for q,a,b in changes(local.blocks,other.blocks):
  an,ap=parse_state(a);bn,bp=parse_state(b);scope=None
  if an.startswith('minecraft:potted_')and bn.startswith('minecraft:potted_'):scope='potted_species'
  elif q in shutter_cells and {an,bn}=={'minecraft:air','minecraft:dark_oak_trapdoor'}:scope='shutters'
  elif q[1]>=top+2 and {an,bn}=={'minecraft:quartz_slab','minecraft:smooth_sandstone_slab'}and ap==bp:scope='coping_material'
  if scope is None:bad.append([bd['id'],q,a,b])
  else:scope_counts[scope]+=1;allowed_world.add(transform(q,bd))
 local_variations.append({'id':bd['id'],'scope_counts':dict(scope_counts)})
assert not bad,bad[:10]
for k in ['arcade_cells','lane_cells','road_cells','alleys','court_bounds','court_approaches','spawn_local']:
 assert sp[k]==vp[k],k
tree_cells=set()
for t in sp['trees']+vp['trees']:
 x,y,z=t['anchor'];rad=t['radius']+2;h=t['height']
 for xx in range(x-rad,x+rad+1):
  for zz in range(z-rad,z+rad+1):
   for yy in range(3,3+h+3):tree_cells.add((xx,yy,zz))
vegetation={'minecraft:air','minecraft:oak_log','minecraft:oak_leaves','minecraft:azalea_leaves','minecraft:short_grass','minecraft:fern','minecraft:azure_bluet'}
diff=changes(whole.blocks,variant.blocks);global_counts=collections.Counter()
for q,a,b in diff:
 an,ap=parse_state(a);bn,bp=parse_state(b)
 if q in allowed_world:global_counts['local_facade_or_pots']+=1
 elif an.startswith('minecraft:potted_')and bn.startswith('minecraft:potted_'):global_counts['court_pots']+=1
 elif q in tree_cells and an in vegetation and bn in vegetation:global_counts['tree_and_groundcover']+=1
 else:bad.append(['Qilou02',q,a,b])
assert not bad,bad[:10]
out={'source_nbt_sha256':hashlib.sha256((R/'Qilou02.nbt').read_bytes()).hexdigest(),'identical_replay':replay,'seed_base':sp['seed'],'seed_variant':vp['seed'],'changed_cells':len(diff),'scope_counts':dict(global_counts),'local_variations':local_variations,'scope_violations':bad,'assembly':assembly,'protected_layout_identical':True,'scope':'Authored placements, programmes, floors and routes remain fixed. Seeds vary shutters, coping material, supported potted species and bounded tree/groundcover groups only.'}
(R/'repro_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
