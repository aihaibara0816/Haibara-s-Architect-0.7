"""Read final NBT independently and check explicit sample/region contracts.
This does not judge photographic similarity or game physics.
"""
from pathlib import Path
import sys,json,hashlib,collections,math,gzip
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate,boxes
from hafusion.review import review_samples,review_views
from hafusion.case_io import dump
from PIL import Image
C=Path(__file__).resolve().parent;run=C/'runs/v2b_03_final';nbt=run/'building.nbt'
b=load_build(nbt,Limits(cells=40_000_000,nodes=16_000_000));sha=hashlib.sha256(nbt.read_bytes()).hexdigest();blocks=b.blocks
checks=[
 dict(id='road_clearance',kind='air',samples=[[x,y,z] for x in range(56) for y in range(1,7) for z in range(30,41)]),
 dict(id='top_aperture',kind='air',samples=[[x,y,z] for x in range(26,30) for y in [93,94] for z in range(37,49)]),
 dict(id='canyon_front_void',kind='air',samples=[[x,y,z] for x in range(26,30) for y in range(39,45) for z in range(46,50)]),
 dict(id='soffit_grid_material',kind='material',material='iron_trapdoor',samples=[[14,77,z] for z in range(40,46)]+[[x,77,40] for x in range(14,42)]),
 dict(id='bridge_transverse_ribs',kind='material',material='iron_trapdoor',samples=[[x,20,27] for x in range(20,36)]),
 dict(id='entry_floor',kind='full_bearing',samples=[[x,0,z] for x in range(26,31) for z in [26,45]]),
 dict(id='entry_clearance',kind='air',samples=[[x,y,z] for x in range(26,31) for y in [1,2] for z in [26,45]])]
results=review_samples(blocks,b.size,checks)
for state in set(blocks.values()):validate(state)
results.append(dict(id='all_palette_states_supported',status='pass',states=len(set(blocks.values()))))
def volume(s):return sum((X-x)*(Y-y)*(Z-z) for x,y,z,X,Y,Z in boxes(s))
samples=[(17,40,46),(36,40,46)];vs=[volume(blocks[q]) for q in samples]
results.append(dict(id='thin_front_glass',status='pass' if all(v<.3 for v in vs) else 'fail',samples=[list(q) for q in samples],volumes=vs))
rr=json.loads((C/'review/previews/v2b_03_final/render_report.json').read_text());viewcheck=review_views(rr,sha)
for r in rr:
 f=C/'review/previews/v2b_03_final'/r['image']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
 with Image.open(f) as im:im.load()
 assert r['source_nbt_sha256']==sha
rooms=json.loads((run/'interiors.json').read_text());owners=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()))
assert len(owners['xyz_owner'])==len(blocks)
counts=collections.Counter(owners['owner_names'][row[-1]].split('.')[0] for row in owners['xyz_owner'])
old_path=C/'research/legacy/building.nbt'
regression=[]
if old_path.exists():
 old=load_build(old_path,Limits(cells=40_000_000,nodes=16_000_000));oldblocks={q:s for q,s in old.blocks.items() if s!='minecraft:air'}
 for check in checks:
  if check['id'] in ['top_aperture','soffit_grid_material','bridge_transverse_ribs']:
   regression.append(dict(id=check['id'],old=review_samples(oldblocks,old.size,[check])[0],new=next(x for x in results if x['id']==check['id'])))
 dump(C/'review/old_nbt_manifest.json',dict(sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),size_xyz=old.size,non_air_blocks=len(oldblocks)))
out=dict(nbt_sha256=sha,size_xyz=b.size,non_air_blocks=len(blocks),material_types=len(set(x.split('[')[0] for x in blocks.values())),state_types=len(set(blocks.values())),geometry=results,views=viewcheck,rendered_images=len(rr),owner_counts=counts,rooms=dict(total=len(rooms),lit=sum(bool(x['actual_lamp']) for x in rooms),fidelity='synthetic only'),old_regression=regression,game='pending',user_review='pending',visual_status='needs_revision',visual_reason='局部构造类型已实现，但玻璃真实反射、底格密度、点灯色彩、背侧与裙楼细部尚不完整')
dump(C/'review/verification.json',out)
# True plan slices from final readback, y unchanged and no camera projection.
plans=C/'review/plans';plans.mkdir(exist_ok=True)
for y in range(b.size[1]):
 im=Image.new('RGB',(b.size[0],b.size[2]),'#edf0e9');px=im.load()
 for (x,yy,z),s in blocks.items():
  if yy!=y:continue
  col=(99,149,163) if 'glass' in s else (234,188,76) if any(k in s for k in ['end_rod','lantern','glowstone']) else (85,123,73) if any(k in s for k in ['leaves','moss','grass']) else (91,96,94)
  px[x,z]=col
 im.save(plans/f'y{y:03}.png')
print(json.dumps({'checks':len(results),'failed':[c['id'] for c in results if c['status']!='pass'],'view_checks':len(viewcheck),'views_not_pass':[c['id'] for c in viewcheck if c['status']!='pass'],'blocks':len(blocks),'rooms':out['rooms']},ensure_ascii=False))
assert all(c['status']=='pass' for c in results+viewcheck)
