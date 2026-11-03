"""Immutable V5 runs, actual NBT readback, module export and evidence ledger."""
from v5_geometry import *
from open_lattice import check_voids
from collections import Counter
import argparse,time

def read_write(s,path,c):
    meta=export_structure(s,path,c['data_version'],include_air=False)
    b=inspect_build.load_build(path,inspect_build.Limits(cells=16_000_000))
    assert b.blocks==s.blocks and tuple(b.size)==s.size,'NBT round-trip mismatch'
    return meta,b

def base(st):return parse_state(st)[0]

def build(run):
    out=ROOT/'runs'/run
    if out.exists():raise ValueError('Immutable run exists; choose another ID')
    c=json.loads((ROOT/'inputs/common.json').read_text());p=json.loads((ROOT/'inputs/v3a_parameters.json').read_text())
    v4=json.loads((ROOT/'inputs/v4_parameters.json').read_text());v=json.loads((ROOT/'inputs/v5_parameters.json').read_text())
    out.mkdir(parents=True);start=time.time();g=V4Geometry(c,p,v4);t=Scene((56,282,56))
    g.inner(t);g.frame(t);g.crown(t);g.mast(t);interior_lights=g.lighting(t)
    s=SiteScene(tuple(v['size_xyz']));site=Podium(s,v).build(t);offset=v['tower_offset_xyz']
    connect_thin_members(t);tower_meta,_=read_write(t,out/'tower_v5.nbt',c)
    for q,st in t.blocks.items():s.set(tuple(q[i]+offset[i] for i in range(3)),st,t.owners[q])
    # Do not fill the reserved core shaft with the new podium floor/slab.
    for x in range(27,30):
     for z in range(27,30):
      for y in range(2,211):
        q=(x+offset[0],y+offset[1],z+offset[2])
        if q in s.blocks and not s.owners[q].startswith(('frame.','crown.','antenna')):s.set(q,AIR,'shaft.clear')
    connect_thin_members(s)
    meta,b=read_write(s,out/'canton280_plaza_v5.nbt',c)
    towerq={tuple(q[i]+offset[i] for i in range(3)) for q in t.blocks if tuple(q[i]+offset[i] for i in range(3)) in s.blocks}
    oldrows=json.loads((ROOT/'baselines/V4_r02/blocks.json').read_text())['blocks']
    old={tuple(r[i]-[36,6,12][i] for i in range(3)):r[3] for r in oldrows if r[4].startswith(('frame.','program.','core','crown.','antenna','lighting.interior.','lighting.core'))}
    protected={q:st for q,st in old.items() if q[1]>=12}
    upper_ok=all(q in t.blocks and t.blocks[q]==st for q,st in protected.items())
    # Protected tower components must also survive composition in the FINAL scene.
    final_upper_ok=all(b.blocks.get(tuple(q[i]+offset[i] for i in range(3)))==st for q,st in protected.items())
    void=check_voids(t.blocks,t.owners,g.zones)
    modules=[];assembled={}
    def module(id,entries,origin,size):
        m=Scene(tuple(size))
        for q,st in entries.items():m.set(tuple(q[i]-origin[i] for i in range(3)),st,s.owners[q])
        mm,rb=read_write(m,out/'modules'/f'{id}.nbt',c)
        for q,st in rb.blocks.items():
            w=tuple(q[i]+origin[i] for i in range(3));assert w not in assembled;assembled[w]=st
        modules.append({'id':id,'origin_xyz':origin,**mm})
    for y0 in range(0,s.size[1],64):
        entries={q:st for q,st in b.blocks.items() if q in towerq and y0<=q[1]<y0+64}
        if entries:module(f'tower_y{y0:03}',entries,[offset[0],y0,offset[2]],[56,min(64,s.size[1]-y0),56])
    for x0 in [0,64]:
     for z0 in [0,116]:
        entries={q:st for q,st in b.blocks.items() if q not in towerq and x0<=q[0]<x0+64 and z0<=q[2]<z0+116}
        if entries:module(f'podium_x{x0:03}_z{z0:03}',entries,[x0,0,z0],[64,20,116])
    assert assembled==b.blocks
    stair_checks=[]
    for stair in site.stairs:
        bad=[q for q in stair['treads'] if q not in b.blocks or any((q[0],q[1]+dy,q[2]) in b.blocks for dy in [1,2])]
        stair_checks.append({'component_id':stair['component_id'],'treads':len(stair['treads']),'blocked_count':len(bad),'blocked_examples':bad[:12],'pass':not bad})
    waterq=[q for q,st in b.blocks.items() if base(st)=='minecraft:water']
    water_bad=[q for q in waterq if (q[0],q[1]-1,q[2]) not in b.blocks or any((q[0]+dx,q[1],q[2]+dz) not in b.blocks for dx,dz in NEIGH)]
    # Actual trunk roots, after all canopy and scene composition operations.
    roots=[q for q,o in s.owners.items() if o.endswith('.trunk') and (q[0],q[1]-1,q[2]) not in s.blocks]
    floor_checks=[]
    for id in ['north','south']:
        cp=v['site'][id+'_court'];x,z=map(int,cp['center_xz']);floor=site.floor
        floor_checks.append({'court':id,'floor_y':floor,'walk_surface_y':floor+1,'no_below_grade_court':all(q[1]>=floor for q,o in s.owners.items() if o.startswith('court.'+id)),
          'center_open':all((x,y,z) not in b.blocks for y in range(floor+1,16))})
    # Upper platform touches retained column paths; explicit interface, not a detached site.
    contacts=[]
    for q in towerq:
        if q[1] in [site.deck-1,site.deck] and s.owners[q].startswith('frame.column.'):
            if any(s.owners.get((q[0]+dx,q[1],q[2]+dz),'').startswith(('podium.','tower.base.')) for dx,dz in NEIGH):contacts.append(q)
    lights=Counter(o for q,o in s.owners.items() if base(b.blocks[q]) in ['minecraft:sea_lantern','minecraft:shroomlight'])
    checks={
      'nbt_roundtrip_exact':b.blocks==s.blocks,
      'module_reassembly_exact':assembled==b.blocks,
      'modules_under_1M_cells_and_256KiB':all(math.prod(m['size_xyz'])<=1_000_000 and m['bytes']<262144 for m in modules),
      'tower_structure_height_280':max(q[1] for q in towerq)-2+1==280,
      'upper_tower_y12_plus_matches_V4':upper_ok and final_upper_ok,
      'program_voids_and_core_shaft_preserved':void['pass'] and all((x+36,y,z+12) not in b.blocks for x in range(27,30) for z in range(27,30) for y in range(2,211)),
      'court_bottoms_1F_and_open':all(r['no_below_grade_court'] and r['center_open'] for r in floor_checks),
      'no_underground_room_blocks':all(q[1]>=1 or o=='site.foundation.skin' for q,o in s.owners.items()),
      'stairs_have_two_cell_clearance':all(r['pass'] for r in stair_checks),
      'pool_water_contained':bool(waterq) and not water_bad,
      'tree_roots_have_support':not roots,
      'tower_columns_meet_podium':len(contacts)>=12,
      'all_five_program_groups_lit':all(n>0 for n in interior_lights.values()),
      'actual_site_and_interior_light_blocks':any(o.startswith('lighting.podium.') for o in lights) and any(o.startswith('lighting.interior.') for o in lights),
      'ring_slab_box_inside_column_polygon':min(r['minimum_box_corner_margin'] for r in g.ring_audit)>=0
    }
    counts=Counter(base(st) for st in b.blocks.values());statecounts=Counter(b.blocks.values());materials=[]
    for name,n in counts.most_common():
        liquid=name=='minecraft:water';materials.append({'block':name,'count':n,'unit':'water source cells, not buckets' if liquid else 'finished blocks/items','full_stacks':None if liquid else n//64,'remainder':None if liquid else n%64,'slots_at_64':None if liquid else math.ceil(n/64)})
    ownercounts=Counter(s.owners.values())
    dump(out/'materials.json',{'scope':'final NBT readback; finished items, not raw crafting ingredients','non_air_total':len(b.blocks),'solid_item_total':sum(n for k,n in counts.items() if k!='minecraft:water'),'materials':materials,'blockstates':dict(statecounts),'lights_by_component':dict(lights),'water_note':'水源单元数量不是水桶需求；游戏流体更新待测。'})
    dump(out/'placement_manifest.json',{'size_xyz':list(s.size),'levels':v['levels'],'tower_offset_xyz':offset,'tower_height_blocks':280,'max_origin_y_if_world_exclusive_upper_bound_320':38,'modules':modules,'reassembly_exact':True,'mode':'Complete NBT OR module pack; do not place both. Sparse NBT does not clear existing terrain. Site includes one-block foundation skin only, not B1.'})
    dump(out/'site_validation.json',{'stairs':stair_checks,'court_floors':floor_checks,'unsupported_tree_root_cells':roots,'water_source_cells':len(waterq),'uncontained_water_examples':water_bad[:20],'column_podium_contact_cells':contacts,'level_definition':v['levels'],'not_tested':['Minecraft collision','fluid ticks','actual walk-through','architectural dimension accuracy']})
    dump(out/'ring_validation.json',{'rings':g.ring_audit,'core_contacts':sum(r['core_contacts'] for r in g.ring_audit),'shaft_skips':sum(r['shaft_skips'] for r in g.ring_audit),'limitation':'V4 inheritance: equal hoop spacing; separate closed continuity at old off-centre core contacts not solved.'})
    dump(out/'component_decisions.json',{'build_id':run,'method':'Reviewed case-level evidence selection, explicit parametric composition before voxel export; no learned segmentation, camera reconstruction or automated aesthetic score.',
      'tower':[{'component_id':'frame','adopt':'SKP reviewed 24 column paths + V3a thin walls/bars + V4 inward hoops','evidence':['model/source.skp','R06','R08','R16','U04','IBA_tvt05','IBA_tvt06']},
      {'component_id':'program','adopt':'Only photo/diagram functional bands have glass, hollow core retained; low floor interface revised','evidence':['U03','R14','R16']},
      {'component_id':'crown','adopt':'V2A fitted inclined plane and track; 16 schematic cabins','evidence':['SKP track fit','R09','R12','dated official 2019 record']}],
      'site':site.records,'rejected':['SKP background terrain as new plaza','B1 and underground interiors','Duplicating two identical oval templates','Treating every glass roof as an entry pavilion','Event orange carpet as permanent material','Night colour cast as day material','2019 layout as 2024 survey'],
      'component_block_counts':dict(ownercounts)})
    dump(out/'void_validation.json',void);dump(out/'palette.json',PALETTE);dump(out/'parameters.json',v)
    dump(out/'blocks.json',{'size_xyz':list(s.size),'geometry_sha256':s.fingerprint(),'blocks':[[*q,st,s.owners[q]] for q,st in sorted(s.blocks.items())]})
    dump(out/'build_report.json',{'build_id':run,'adapter':'canton-v5-0.1','geometry_sha256':s.fingerprint(),'nbt':meta,'tower_nbt':tower_meta,'non_air_blocks':len(b.blocks),'checks':checks,'status':'pass' if all(checks.values()) else 'fail','interior_lights_by_band':interior_lights,'actual_light_blocks':sum(lights.values()),'game_validation':'pending','seconds':round(time.time()-start,2),'limitations':v['limits']})
    dump(out/'input_hashes.json',{str(f.relative_to(ROOT)):digest(f) for folder in ['src','vendor','inputs'] for f in sorted((ROOT/folder).rglob('*')) if f.is_file() and '__pycache__' not in str(f)})
    print(json.dumps({'run':run,'nbt':meta,'checks':checks,'site_contacts':len(contacts),'lights_total':sum(lights.values()),'seconds':time.time()-start},ensure_ascii=False),flush=True)
    if not all(checks.values()):raise ValueError('V5 checks failed; inspect run diagnostics')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);build(ap.parse_args().run)
