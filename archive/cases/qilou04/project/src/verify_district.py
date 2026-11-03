from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT/'pydeps')]
import qilou_states
from detail_lab import states as ST
class Q:
 @staticmethod
 def rotate(st,n):
  for _ in range(n):st=ST.rotate_state(st)
  return st
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
R=ROOT/'runs'/sys.argv[1];rp=ROOT/'runs'/sys.argv[2];vp=ROOT/'runs'/sys.argv[3]
read=lambda p:json.loads(p.read_text());s=read(R/'spec.json');v=read(vp/'spec.json');assert read(R/'audit.json')['pass']and read(vp/'audit.json')['pass']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
replay={b['id']:sha(R/(b['id']+'.nbt'))==sha(rp/(b['id']+'.nbt'))for b in s['buildings']};replay['Qilou04']=sha(R/'Qilou04.nbt')==sha(rp/'Qilou04.nbt');assert all(replay.values()),replay
b=load_build(R/'Qilou04.nbt',Limits(cells=12_000_000,nodes=25_000_000));checked=0;errors=[];connect=0
for r in s['buildings']:
 m=load_build(R/(r['id']+'.nbt'),Limits(cells=12_000_000,nodes=25_000_000))
 for (x,y,z),st in m.blocks.items():
  if y<=2:continue
  W,D=r['w'],r['d']
  for _ in range(r['turn']):x,z=D-1-z,x;W,D=D,W
  p=(x+r['origin'][0],y+r['origin'][1],z+r['origin'][2]);expected=Q.rotate(st,r['turn']);actual=b.blocks.get(p,'minecraft:air');checked+=1
  if actual==expected:continue
  na,pa=parse_state(actual);ne,pe=parse_state(expected)
  allowed=any(x in na for x in ['_pane','_fence','_wall'])and not na.endswith('_wall_sign')
  if na==ne and allowed and {k:v for k,v in pa.items()if k not in ['north','south','east','west','up']}=={k:v for k,v in pe.items()if k not in ['north','south','east','west','up']}:connect+=1;continue
  errors.append([r['id'],p,expected,actual])
assert not errors,errors[:20]
lots={r['id']:r['lot']for r in s['buildings']if r['family']=='village'};other={r['id']:r['lot']for r in v['buildings']if r['family']=='village'};changes=[]
for id,t in lots.items():
 u=other[id];keys=['w','d','floors','x','z'];diff={k:[t[k],u[k]]for k in keys if t[k]!=u[k]};changes.append({'id':id,'changes':diff})
report={'same_seed_nbt_bytes_identical':all(replay.values()),'replay_files':len(replay),'source_sha256':s['source_nbt_sha256'],'variant_seed':v['seed'],'variant_sha256':v['source_nbt_sha256'],'changed_massing':sum(any(k in c['changes']for k in ['w','d','floors'])for c in changes),'changed_setbacks':sum(any(k in c['changes']for k in ['x','z'])for c in changes),'unique_residential_width_depth_height':len({(t['w'],t['d'],t['floors'])for t in lots.values()}),'residential_height_histogram':dict(collections.Counter(t['floors']for t in lots.values())),'shape_histogram':dict(collections.Counter(t['shape']for t in lots.values())),'variant_offline_audit_pass':True,'preserved_module_blocks_checked':checked,'allowed_join_connection_updates':connect,'overwritten_module_blocks':len(errors),'scope':'Authored irregular street/parcel topology with bounded independent massing/household/detail variation. Demonstrated for baseline and one alternative; not arbitrary-city generation.','changes':changes}
other_buildings={q['id']:q for q in v['buildings']}
report['changed_whole_building_palette']=sum(q['facade_revision']['palette']!=other_buildings[q['id']]['facade_revision']['palette']for q in s['buildings'])
report['changed_qilou_roof_type']=sum(q['facade_revision']['roof']!=other_buildings[q['id']]['facade_revision']['roof']for q in s['buildings']if q['family']=='qilou')
assert report['changed_whole_building_palette']>0 and report['changed_qilou_roof_type']>0
(R/'variation_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items()if k!='changes'},ensure_ascii=False))
