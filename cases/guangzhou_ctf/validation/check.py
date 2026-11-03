"""Release checks on independently reloaded voxels, not a visual fidelity score."""
from pathlib import Path
import sys,json,hashlib
from collections import Counter,deque
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1];sys.path.insert(0,str(HAF/'support'))
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
from detail_lab import states

def main():
 run=CASE/'runs/V1';b=load_build(run/'building.nbt',Limits(cells=2_000_000));params=json.loads((run/'params_used.json').read_text());r=json.loads((run/'build_report.json').read_text());rows=json.loads((run/'blocks.json').read_text())['blocks'];owned={tuple(a[:3]):a[4] for a in rows};checks=[]
 def check(name,passed,detail):
  checks.append({'name':name,'passed':bool(passed),'detail':detail});assert passed,name
 check('NBT independent readback',r['nbt_readback_exact_match'] and len(rows)==len(b.blocks),len(b.blocks))
 check('Explicit bounded scene',b.size==(80,269,92) and 80*269*92<=2_000_000,list(b.size))
 check('Tower height',max(q[1] for q in b.blocks)==266,'top surface267 - grade2 = 265 blocks')
 check('Registered blockstates',all(states.validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
 counts=Counter(parse_state(s)[0] for s in b.blocks.values())
 check('Thin fins and glass panes exist',counts['minecraft:diorite_wall']>5000 and counts['minecraft:gray_stained_glass_pane']>10000,dict(counts))
 check('Partial-state floors',sum(n for s,n in counts.items() if s.endswith('_slab'))>10000,'Slabs retained as states')
 groups=Counter(o.split('.')[0] for o in owned.values());check('All requested component groups',all(groups[k]>0 for k in ['site','podium','interior','facade','roofs','lighting']),dict(groups))
 check('Four facade directions',all(any(o.startswith('facade.'+s+'.') for o in owned.values()) for s in ['north','east','south','west']),'Cardinal working frame, not surveyed north')
 check('Corner infill and backing',counts['minecraft:gray_stained_glass']>1000 and sum(o=='interior.continuous_window_backing' for o in owned.values())>1000,'Physical infill at quantized turns; closed backing ring')
 # Cell-level flood enclosure: partial blocks count as occupied, explicitly not collision proof.
 areas=[]
 for y in [40,180,235,258]:
  occupied={(x,z) for x,yy,z in b.blocks if yy==y};q=deque([(0,0)]);outside={(0,0)}
  while q:
   x,z=q.popleft()
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
    a=(x+dx,z+dz)
    if 0<=a[0]<b.size[0] and 0<=a[1]<b.size[2] and a not in occupied and a not in outside:outside.add(a);q.append(a)
  areas.append({'y':y,'enclosed_or_occupied_cells':b.size[0]*b.size[2]-len(outside)})
 check('Upper floorplate reduction',all(areas[i]['enclosed_or_occupied_cells']>areas[i+1]['enclosed_or_occupied_cells'] for i in range(3)),areas)
 crown_y=[q[1] for q,o in owned.items() if o=='roofs.crown'];check('Sloping crown',max(crown_y)-min(crown_y)>=4,{'min':min(crown_y),'max':max(crown_y)})
 rooms=json.loads((run/'rooms.json').read_text());lit=sum(bool(v['lamp_position']) for v in rooms)
 check('Room variation and mixed fixtures',.25<len([v for v in rooms if v['lamp_position']])/len(rooms)<.75 and counts['minecraft:sea_lantern']>0 and counts['minecraft:glowstone']>0,{'rooms':len(rooms),'lit':lit,'sea_lantern':counts['minecraft:sea_lantern'],'glowstone':counts['minecraft:glowstone']})
 check('Exact chunk reassembly',json.loads((CASE/'validation/template_reassembly.json').read_text())['exact_reassembly'],'All 32-cell tiles independently read')
 old=json.loads((CASE/'validation/shenzhen_regression.json').read_text());check('Shenzhen reproduction',old['exact_prior_nbt_reproduced'],old['sha256'])
 before=json.loads((CASE/'validation/preserved_shenzhen_before.json').read_text());changed=[n for n,h in before.items() if hashlib.sha256((HAF/n).read_bytes()).hexdigest()!=h];check('Prior Shenzhen files intact',not changed,len(before))
 replay=CASE/'runs/V1_replay/building.nbt';check('Deterministic replay',replay.read_bytes()==(run/'building.nbt').read_bytes(),'Same seed, same NBT bytes')
 alt=load_build(CASE/'runs/V1_other_seed/building.nbt',Limits(cells=2_000_000));delta=[q for q in b.blocks.keys()|alt.blocks.keys() if b.blocks.get(q)!=alt.blocks.get(q)];allowed={None,'minecraft:sea_lantern','minecraft:glowstone'}
 check('Seed changes only light cells',len(delta)>0 and all(b.blocks.get(q) in allowed and alt.blocks.get(q) in allowed for q in delta),len(delta))
 c=json.loads((CASE/'runs/V1_other_seed/cache_report.json').read_text());check('Local lighting stage invalidation',c['hits']==6 and c['rebuilt']==['lighting'],c)
 from PIL import Image
 previews=CASE/'review/previews/V1';imgs=list(previews.glob('*.png'))
 for img in imgs:
  with Image.open(img) as im:im.load();assert im.info.get('source_nbt_sha256')==r['nbt']['sha256'],str(img)
 check('Preview decodes and matches NBT',len(imgs)==15,{'images':len(imgs),'sha256':r['nbt']['sha256']})
 out={'status':'technical checks pass; visual/user/game acceptance separate','checks':checks,'count':len(checks),'game_test':'not run','fidelity_score':None,'known_limits':r['limitations']};(CASE/'validation/release_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('PASS',len(checks),'checks')
if __name__=='__main__':main()
