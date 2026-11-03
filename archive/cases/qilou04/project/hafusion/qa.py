"""Final NBT / component / PlanCraft circulation checks. Game remains pending."""
from collections import Counter
from pathlib import Path
import json,hashlib,math
import numpy as np
from .bootstrap import ROOT,CASE
from .canton import scene
from common import export_structure,inspect_build,parse_state
from building.grid import Grid
from building.validate import reachable,check_pairs
from research_lab.stage_cache import digest

def circulation(blocks,size,targets):
    # Explicit TEST fixture at the same level, never inserted into exported NBT.
    # Without an apron, upstream edge-seeding cannot reach an isolated footprint.
    grid=Grid(size[0]+2,24,size[2]+2)
    grid.fill(0,1,0,size[0]+1,1,size[2]+1,'minecraft:stone')
    for (x,y,z),st in blocks.items():
        if y<24:grid.set(x+1,y,z+1,st)
    r=reachable(grid,2,max_drop=1)
    tests=[{'id':name,'feet_xyz':[x,y,z],'reachable':bool(r[x+1,y,z+1])} for name,x,y,z in targets]
    return {'provider':'PlanCraft reachable() b0746140 (unmodified MIT code)',
            'fixture':'One-cell exterior apron plus level-1 test ground beneath unoccupied exterior; not output NBT.',
            'max_drop':1,'targets':tests,'reachable_cells':int(r.sum()),'paired_block_errors':check_pairs(grid),
            'game_collision':'pending; upstream is a block-state heuristic, not Minecraft physics'}

def export_checked(s,path):
    m=export_structure(s,path,3955,include_air=False)
    b=inspect_build.load_build(path,inspect_build.Limits(cells=16_000_000))
    if b.blocks!=s.blocks or tuple(b.size)!=s.size:raise ValueError('Independent NBT readback mismatch')
    return m,b

def export_modules(s,out,offset):
    tower={q for q,o in s.owners.items() if o.startswith(('core','program.','frame.','crown.','antenna','lighting.interior.','lighting.core'))}
    modules=[];assembled={}
    def one(name,entries,origin,size):
        if not entries:return
        m=scene([[*[q[i]-origin[i] for i in range(3)],st,s.owners[q]] for q,st in entries.items()],size)
        meta,rb=export_checked(m,out/'modules'/f'{name}.nbt')
        for q,st in rb.blocks.items():
            w=tuple(q[i]+origin[i] for i in range(3))
            if w in assembled:raise ValueError('Overlapping export partitions')
            assembled[w]=st
        if math.prod(size)>1_000_000 or meta['bytes']>=262144:raise ValueError('Module exceeds declared budget')
        modules.append({'id':name,'origin_xyz':origin,**meta})
    for y in range(0,s.size[1],64):
        one(f'tower_y{y:03}',{q:s.blocks[q] for q in tower if y<=q[1]<y+64},[offset[0],y,offset[2]],[56,min(64,s.size[1]-y),56])
    for x in [0,64]:
      for z in [0,116]:
        one(f'podium_x{x:03}_z{z:03}',{q:st for q,st in s.blocks.items() if q not in tower and x<=q[0]<x+64 and z<=q[2]<z+116},[x,0,z],[64,20,116])
    if assembled!=s.blocks:raise ValueError('Partition reassembly mismatch')
    return modules

def compare(base,s):
    before={tuple(r[:3]):(r[3],r[4]) for r in base}
    after={q:(st,s.owners[q]) for q,st in s.blocks.items()}
    changed=[q for q in sorted(before.keys()|after.keys()) if before.get(q)!=after.get(q)]
    states=[q for q in changed if (before.get(q)or(None,))[0]!=(after.get(q)or(None,))[0]]
    groups=Counter()
    for q in changed:
        for o in {v[1] for v in [before.get(q),after.get(q)] if v}:groups[o.split('.')[0]]+=1
    return {'before_non_air':len(before),'after_non_air':len(after),'changed_state_or_owner':len(changed),'changed_block_states':len(states),
            'added':sum(q not in before for q in after),'removed':sum(q not in after for q in before),
            'changed_groups':dict(groups),'changed_rows':[[*q,before.get(q),after.get(q)] for q in changed],
            'meaning':'Difference counts, not a reconstruction accuracy score.'}

def validate_final(s,site,rings,baseline):
    off=site['offset'];a,b=site['shaft_min'];checks={};details={}
    shaft=[(x+off[0],y,z+off[2]) for x in range(a,a+3) for z in range(b,b+3) for y in range(2,211)]
    checks['reserved_3x3_shaft_empty']=all(q not in s.blocks for q in shaft)
    allowed={y for zone in site['zones'] for y in range(*zone['local_y_half_open'])}
    checks['program_only_in_reviewed_bands']=all(q[1] in allowed for q,o in s.owners.items() if o.startswith('program.'))
    audits=[]
    for r in rings:
        world=[tuple(q[i]+off[i] for i in range(3)) for q in r['path']]
        missing=[q for q in world if q not in s.blocks]
        core=[q for q in world if s.owners.get(q)=='core']
        closed=world[0]==world[-1] and all(sum(abs(a-b) for a,b in zip(x,y))==1 for x,y in zip(world,world[1:]))
        audits.append({'id':r['id'],'y':r['y'],'missing':len(missing),'core_contacts':len(core),
                       'closed_face_path':closed,'inside_outer_frame':r['minimum_outer_margin']>=0,
                       'shared_with_other_components':sum(s.owners.get(q)!=r['id'] for q in set(world))})
    details['rings']=audits
    checks['all_46_planned_ring_paths_present']=all(r['missing']==0 and r['closed_face_path'] for r in audits)
    checks['ring_paths_avoid_core']=all(r['core_contacts']==0 for r in audits)
    checks['ring_footprints_inside_columns']=all(r['inside_outer_frame'] for r in audits)
    checks['tower_height_280']=max(q[1] for q,o in s.owners.items() if o.startswith('antenna'))-2+1==280
    checks['no_underground_room_blocks']=all(q[1]>=1 or o=='site.foundation.skin' for q,o in s.owners.items())
    stairs=[]
    for stair in site['stairs']:
        bad=[q for q in stair['treads'] if tuple(q) not in s.blocks or any((q[0],q[1]+dy,q[2]) in s.blocks for dy in [1,2])]
        stairs.append({'component_id':stair['component_id'],'blocked':len(bad)})
    checks['stairs_two_cell_clearance']=all(r['blocked']==0 for r in stairs);details['stairs']=stairs
    water=[q for q,st in s.blocks.items() if st.startswith('minecraft:water')]
    checks['water_contained']=bool(water) and all((x,y-1,z) in s.blocks and all((x+dx,y,z+dz) in s.blocks for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]) for x,y,z in water)
    checks['tree_roots_supported']=all((q[0],q[1]-1,q[2]) in s.blocks for q,o in s.owners.items() if o.endswith('.trunk'))
    d=compare(baseline,s);details['difference']=d
    siteprefix=('site.','podium.','landscape.','court.','pool.','canopy.','tower.base.','lighting.podium.','lighting.path.','lighting.pool.','lighting.canopy.','lighting.court.','lighting.tower.')
    frozen={(tuple(r[:3]),r[3],r[4]) for r in baseline if r[4].startswith(siteprefix)}
    current={(q,st,s.owners[q]) for q,st in s.blocks.items() if s.owners[q].startswith(siteprefix)}
    checks['site_states_and_ownership_frozen']=frozen==current
    details['site_difference_count']=len(frozen^current)
    targets=[('north_court',64,2,103),('south_court',64,2,191),('core_entry',a+1+off[0],2,b+3+off[2]),('west_upper_deck',40,7,100),('east_upper_deck',90,7,150),('south_arrival',64,2,228)]
    details['circulation']=circulation(s.blocks,s.size,targets)
    checks['plancraft_six_access_targets']=all(t['reachable'] for t in details['circulation']['targets'])
    checks['all_five_program_bands_lit']=all(n>0 for n in site['lights_by_band'].values())
    return checks,details
