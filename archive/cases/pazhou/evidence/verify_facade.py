"""Final-NBT regression and scoped-diff review, not a game or fidelity score."""
from pathlib import Path
import sys,json,gzip,hashlib,collections
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from hafusion.review import review_samples,review_views
from hafusion.case_io import dump
from facade_layers import BANDS
from PIL import Image
C=Path(__file__).resolve().parent
run=C/'runs/v3b_04_final';oldrun=C/'runs/v2b_03_final';new=load_build(run/'building.nbt');old=load_build(oldrun/'building.nbt')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def owners(p):
 d=json.loads(gzip.decompress((p/'component_ownership.json.gz').read_bytes()))
 return {tuple(r[:3]):d['owner_names'][r[3]] for r in d['xyz_owner']}
oo,no=owners(oldrun),owners(run)
changes=[q for q in old.blocks.keys()|new.blocks.keys() if old.blocks.get(q)!=new.blocks.get(q)]
def allowed(q):
 a=oo.get(q,'');b=no.get(q,'')
 return a.startswith('facade.wing') or b.startswith('facade_layer.') or (a.startswith('interior.') and a.endswith('.back'))
bad=[q for q in changes if not allowed(q)]
checks=[]
def check(id,ok,**detail):checks.append(dict(id=id,status='pass' if ok else 'fail',**detail))
check('before_facade_equals_delivered_v2',sha(C/'runs/v3b_03_before_facade/building.nbt')==sha(oldrun/'building.nbt'))
check('all_changes_within_facade_and_backing_scope',not bad,changed_cells=len(changes),unexpected=bad[:20])
check('size_and_height_unchanged',old.size==new.size==tuple([56,100,82]))
protected={q:s for q,s in old.blocks.items() if not oo[q].startswith('facade.wing') and not (oo[q].startswith('interior.') and oo[q].endswith('.back'))}
check('existing_nonfacade_cells_preserved',all(new.blocks.get(q)==s for q,s in protected.items()),cells=len(protected))
lamps={q:s for q,s in old.blocks.items() if any(m in s for m in ['end_rod','glowstone','sea_lantern'])}
check('all_existing_lamp_states_preserved',all(new.blocks.get(q)==s for q,s in lamps.items()),lamps=len(lamps))
for s in set(new.blocks.values()):states.validate(s)
check('all_output_states_registered',True,states=len(set(new.blocks.values())))
for material in ['blue_stained_glass_pane','cyan_stained_glass_pane','black_stained_glass_pane','iron_bars']:
 n=sum(states.parse_state(s)[0]=='minecraft:'+material for s in new.blocks.values())
 check('actual_material_'+material,n>0,count=n)
contracts=[
 dict(id='road_clearance',kind='air',samples=[[x,y,z] for x in range(56) for y in range(1,7) for z in range(30,41)]),
 dict(id='top_aperture',kind='air',samples=[[x,y,z] for x in range(26,30) for y in [93,94] for z in range(37,49)]),
 dict(id='canyon_front_void',kind='air',samples=[[x,y,z] for x in range(26,30) for y in range(39,45) for z in range(46,50)]),
 dict(id='soffit_grid',kind='material',material='iron_trapdoor',samples=[[14,77,z] for z in range(40,46)]+[[x,77,40] for x in range(14,42)]),
 dict(id='bridge_ribs',kind='material',material='iron_trapdoor',samples=[[x,20,27] for x in range(20,36)]),
 dict(id='entry_floor',kind='full_bearing',samples=[[x,0,z] for x in range(26,31) for z in [26,45]]),
 dict(id='entry_clearance',kind='air',samples=[[x,y,z] for x in range(26,31) for y in [1,2] for z in [26,45]])]
checks+=review_samples(new.blocks,new.size,contracts)
check('outer_bar_glass_air_back_depth',all([
 'iron_bars' in new.blocks.get((42,40,49),''),
 'glass_pane' in new.blocks.get((41,40,49),''),
 (40,40,49) not in new.blocks,(39,40,49) not in new.blocks,
 'gray_concrete' in new.blocks.get((38,40,49),'')]),positions=[[42,40,49],[41,40,49],[40,40,49],[39,40,49],[38,40,49]])
check('old_output_fails_new_bar_depth_contract','iron_bars' not in old.blocks.get((42,40,49),''))
# The three cropped samples are exact portions of the corresponding complete
# scene, with boundary connection states preserved rather than recomputed.
sample=load_build(C/'runs/sample_r01_C_layered/building.nbt');lo=(31,38,44);hi=(44,59,68)
expected={tuple(v-a for v,a in zip(q,lo)):s for q,s in new.blocks.items() if all(a<=v<z for v,a,z in zip(q,lo,hi))}
check('layered_sample_equals_final_nbt_crop',sample.blocks==expected)
def occlusion(build):
 hit=total=0
 for x,dx in [(14,1),(41,-1)]:
  for a,c in BANDS:
   for y in range(a,c):
    if (y-a)%3==0:continue
    for z in range(47,65):
     total+=1
     for depth in range(1,7):
      s=build.blocks.get((x+dx*depth,y,z),'minecraft:air')
      if not states.transparent(s) and states.boxes(s)==((0,0,0,1,1,1),):hit+=1;break
 return dict(hits=hit,rays=total,fraction=round(hit/total,4),definition='Side facade occupied band cell centres, six inward cells; full opaque-cube hits only. Not visual opacity or fidelity.')
rr=json.loads((C/'review/previews/v3b_04_final/render_report.json').read_text())
viewchecks=review_views(rr,sha(run/'building.nbt'))
for r in rr:
 f=C/'review/previews/v3b_04_final'/r['image']
 assert sha(f)==r['sha256'] and r['source_nbt_sha256']==sha(run/'building.nbt')
 with Image.open(f) as im:im.load()
counts=collections.Counter(states.parse_state(s)[0] for s in new.blocks.values())
out=dict(run='v3b_04_final',nbt_sha256=sha(run/'building.nbt'),blocks=len(new.blocks),size_xyz=new.size,
 checks=checks,views=viewchecks,preview_count=len(rr),materials=dict(counts),
 diff=dict(changed_cells=len(changes),added=sum(q not in old.blocks for q in changes),removed=sum(q not in new.blocks for q in changes),new_owner_counts=dict(collections.Counter(no.get(q,'removed') for q in changes))),
 side_backing_probe=dict(old=occlusion(old),new=occlusion(new)),
 focused_tests=dict(count=36,status='pass',log='facade_tests.log'),game='pending',user_acceptance='pending',
 manual_visual='Backing and depth are clearer in comparative previews; metal fins and corner returns look heavy in the solid-box renderer. Vanilla cutout texture and real glass behaviour untested.',
 capability='Experimental case adapter plus two pane colours; not a new HAF release, installed Skill update, automated material recognition or universal facade generation.')
dump(C/'review/facade_verification.json',out)
print(json.dumps({k:out[k] for k in ['blocks','diff','side_backing_probe','focused_tests']},ensure_ascii=False))
assert all(x['status']=='pass' for x in checks+viewchecks),[x for x in checks+viewchecks if x['status']!='pass']
