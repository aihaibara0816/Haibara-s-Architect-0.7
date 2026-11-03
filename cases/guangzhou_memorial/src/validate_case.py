"""File and case-geometry checks; deliberately not a game or aesthetic verdict."""
from pathlib import Path
import sys,json,gzip,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
CASE=Path(__file__).resolve().parents[1]
run=sys.argv[1];out=CASE/'runs'/run
b=load_build(out/'building.nbt',Limits(cells=40_000_000,nodes=64_000_000));p=json.loads((out/'params_used.json').read_text())
o=json.loads(gzip.decompress((out/'component_ownership.json.gz').read_bytes()));owners={tuple(row[:3]):o['owner_names'][row[3]] for row in o['xyz_owner']}
cx,cz=p['center_xz'];results=[]
def check(name,condition,detail):
    results.append({'check':name,'pass':bool(condition),'detail':detail})
check('declared_bounds',b.size==tuple(p['size_xyz']) and all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),'all final block coordinates')
check('owners_complete',set(owners)==set(b.blocks),'every non-air block has a component owner')
check('registered_states',all(states.validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
check('eight_faced_clerestory',len({o for o in owners.values() if o.startswith('central.clerestory.face')})==8,'8 separately owned faces')
geo=json.loads((out/'case_geometry.json').read_text());check('nine_roof_components',len(geo['roof_components'])==9,[q['id'] for q in geo['roof_components']])
clear=[q for q in b.blocks if abs(q[0]-cx)<12 and abs(q[2]-cz)<12 and 15<=q[1]<=55]
check('central_auditorium_clear_span',not clear,{'nonair_in_clear_volume':len(clear),'floor_seating_and_ceiling_excluded':True})
check('auditorium_stage_and_two_galleries',all(any(o.startswith(x) for o in owners.values()) for x in ['interior.stage','interior.gallery1','interior.gallery2']), 'source ref05')
check('rear_not_open_shell',sum(o=='hall.envelope' for q,o in owners.items() if q[2]<cz-70)>500,'enclosed rear wall with door and window openings')
check('front_door_clear',all((cx,y,cz+54) not in b.blocks for y in range(9,16)), 'central entrance remains open')
check('thin_block_detail',any('slab' in s for s in b.blocks.values()) and any('stairs' in s for s in b.blocks.values()) and any('pane' in s for s in b.blocks.values()),'slabs, stairs, panes preserved in NBT')
lights=collections.Counter();exposed=collections.Counter()
for q,s in b.blocks.items():
    if s not in [states.make('glowstone'),states.make('sea_lantern')]:continue
    own=owners[q];zone=own.split('.')[1] if own.startswith('lighting.') else own.split('.')[0];lights[zone]+=1
    if any(tuple(q[i]+off[i] for i in range(3)) not in b.blocks or 'glass' in b.blocks.get(tuple(q[i]+off[i] for i in range(3)),'') for off in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]):exposed[zone]+=1
for zone in ['entry','central','roof','interior','site']:
    check('lighting_zone_'+zone,lights[zone]>0 and exposed[zone]>0,{'lamps':lights[zone],'air_or_glass_adjacent':exposed[zone],'note':'fixture exposure only, not game lux or photometry'})
check('both_warm_cool_materials',all(any(s==states.make(n) for s in b.blocks.values()) for n in ['glowstone','sea_lantern']),'material appearance; vanilla has no RGB tinted lighting')
check('height_envelope_97',max(q[1] for q,o in owners.items() if o=='roof.central.finial')-p['ground_y']==97,'top 100, ground 3')
check('immutable_source_snapshot',hashlib.sha256((out/'build_case_snapshot.py').read_bytes()).hexdigest()==json.loads((out/'manifest.json').read_text())['source_code_sha256'],'snapshot matches run manifest')
report={'run':run,'source_nbt_sha256':hashlib.sha256((out/'building.nbt').read_bytes()).hexdigest(),'checks':results,'passed':sum(x['pass'] for x in results),'total':len(results),'game_status':'pending','aesthetic_status':'awaiting user review','light_counts':dict(lights),'lamp_exposure_counts':dict(exposed),'placement':{'world_assumption':'Java modern Overworld [-64,320)','origin_y_min':-64,'origin_y_max':320-b.size[1],'instruction':'use a clear site; sparse NBT does not erase existing blocks; Sponge explicit-air copy can'}}
(out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if all(x['pass'] for x in results) else 1)
