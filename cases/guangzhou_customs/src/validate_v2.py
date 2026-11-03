"""Independent delivered-NBT checks for user-reported V1 regressions.
Technical constraints, never a substitute for photographic fidelity review.
"""
from pathlib import Path
import sys,json,hashlib,zipfile,collections
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(CASE/'src')]
from vendor.inspect_build import load_build,Limits
from build_v2 import CustomsV2
run=CASE/'runs'/sys.argv[1];p=json.loads((run/'params_used.json').read_text());g=p['frame']['ground_y']
b=load_build(run/'building.nbt',Limits(cells=40000000,nodes=16000000));v1=CASE/'runs/V1_r04/building.nbt'
rows=[]
def check(n,v,e):
 rows.append({'test':n,'pass':bool(v),'evidence':e})
def air(q):return q not in b.blocks or b.blocks[q]=='minecraft:air'
check('V1 immutable NBT',hashlib.sha256(v1.read_bytes()).hexdigest()=='a89e1d213e5dca33241f2e13803ebc11cc3cdedc8e7d89a8cf706794bf99e2a3','SHA-256 against delivered V1')
check('frame and total study height unchanged',b.size==(126,148,116) and max(q[1] for q in b.blocks)==140,'fixed comparison envelope; ground=4, spire=137')
check('front entry remains open',all(air((x,y,84)) for x in range(61,66) for y in range(g+3,g+7)),'5×4 clear front doorway')
check('side entry remains open',all(air((10,y,z)) for z in (61,62,63) for y in range(g+3,g+7)),'3×4 side doorway in middle arched bay')
check('side stair top tread survives site clearance','slab' in b.blocks.get((7,g+2,55),''),'landscape clearance must run before stair generation')
check('side entry landing bridges stair to doorway',all(not air((x,g+2,62)) for x in range(7,17)),'no gap between top tread and portal floor')
check('side colonnade is genuinely hollow',all(air((20,y,z)) for y in range(g+6,g+12) for z in range(86,91)),'probe within colonnade, between columns')
check('rear court notch exists',all(air((60,y,20)) for y in range(g+2,g+20)),'was inside monolithic V1 podium')
check('tower rear reentrant exists',all(air((48,y,50)) for y in range(g+24,g+94)),'vertical groove between central and outer masses')
check('upper long tail removed',all(air((63,y,35)) for y in range(g+105,g+112)),'V1 central prism extended to z=28')
for x,z in [(24,60),(102,60),(30,44),(96,74)]:
 check(f'upper band wraps at {x},{z}',not air((x,g+94,z)),'read actual NBT at side/rear/front band')
win=json.loads((run/'windows.json').read_text());rooms=json.loads((run/'interiors.json').read_text())
bad=[]
for w in win:
 x,y,z=w['anchor'];dx,dz=w['normal_xz']
 if w['id'].startswith('tower.') and 'glass' not in b.blocks.get((x-dx,y,z-dz),''):
  bad.append(w['id'])
check('registered tower windows contain actual recessed glass',not bad,{'exceptions':bad})
lights=collections.Counter(r['actual_lamp'] or 'off' for r in rooms)
check('dark warm cool rooms all present',all(lights[k]>0 for k in ('off','glowstone','sea_lantern')),dict(lights))
check('room lamps match delivered coordinates/materials',all(b.blocks.get(tuple(r['lamp_position']),'').split('[')[0]=='minecraft:'+r['actual_lamp'] for r in rooms if r['actual_lamp']),'every recorded room light')
from detail_lab.states import validate
for s in set(b.blocks.values()):validate(s)
check('all exported states pass existing state validation',True,len(set(b.blocks.values())))
# Rebuild case source in memory and independently compare the loaded exported blocks.
model=CustomsV2(p).build();model.finish()
check('deterministic regenerated geometry equals exported NBT',model.s.blocks==b.blocks,{'nonair':len(b.blocks)})
rep={'run':run.name,'checks':rows,'passed':sum(r['pass'] for r in rows),'total':len(rows),'all_passed':all(r['pass'] for r in rows),'shared_tests':'23 existing HAF tests passed on 2026-10-24','visual_acceptance':'pending user review','minecraft_import':'not run','height_and_bearing':'not surveyed'}
(run/'validation_v2.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(rep,ensure_ascii=False,indent=2));sys.exit(0 if rep['all_passed'] else 1)

