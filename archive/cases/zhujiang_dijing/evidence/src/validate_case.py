"""Independent final-file checks. No claims about game collision or visual fidelity."""
from pathlib import Path
import argparse,collections,gzip,json,sys
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from hafusion.case_io import dump,sha
CASE=Path(__file__).resolve().parents[1]

def check(run):
    path=CASE/'runs'/run;b=load_build(path/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));p=json.loads((path/'params_used.json').read_text());r=json.loads((path/'construction_records.json').read_text());rooms=json.loads((path/'interiors.json').read_text());checks=[]
    def add(id,ok,detail):checks.append({'id':id,'status':'pass' if ok else 'fail','detail':detail})
    def at(q):return b.blocks.get(tuple(q),'minecraft:air')
    def solid(q):return states.support_cube(at(q))
    add('readback_bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),{'size_xyz':b.size,'blocks':len(b.blocks)})
    add('state_vocabulary',all(states.validate(s) for s in set(b.blocks.values())),{'states':len(set(b.blocks.values()))})
    gaps=[]
    for s in r['supports']:
        for x in range(s['x0'],s['x1']):
            for z in range(s['z0'],s['z1']):
                if not solid((x,s['base_y']-1,z)):gaps.append([x,s['base_y']-1,z,s['id']])
    add('full_column_bearing',not gaps,{'missing_cells':len(gaps),'examples':gaps[:10]})
    failures=[]
    for a in r['balconies']:
        q=a['clear_test'];f=a['floor_test'];rail=a['rail_test'];glass=a['glazing_test']
        if at(q)!='minecraft:air' or not solid(f) or 'glass_pane' not in at(rail) or 'glass_pane' not in at(glass):failures.append(a['id'])
    add('balcony_layer_and_clearance',not failures,{'balconies':len(r['balconies']),'failed':failures})
    blocked=[]
    for a in r['balconies']:
        x,y,z=a['glazing_test']
        for dz in [1,2,3]:
            if solid((x,y,z+dz)):blocked.append([x,y,z+dz])
    add('glazing_not_buried_behind_wall',not blocked,{'opaque_cells_in_front_of_test_glazing':len(blocked),'examples':blocked[:6]})
    # Entry corridor: occupied floor height may change by at most one full cell.
    entries=[]
    for e in r['entries']:
        x=e['center_x'];old=None;ok=True
        for z in range(e['range_z'][0],e['range_z'][1]+1):
            floors=[y for y in range(3,7) if solid((x,y,z)) and at((x,y+1,z))=='minecraft:air' and at((x,y+2,z))=='minecraft:air']
            if not floors:ok=False;break
            y=max(floors)
            if old is not None and abs(y-old)>1:ok=False
            old=y
        entries.append({'id':e['id'],'pass':ok})
    add('entry_floor_continuity',all(e['pass'] for e in entries),entries)
    add('open_roof_crown',all(at(q)=='minecraft:air' for q in r['roof_openings']),{'sample_cells':r['roof_openings']})
    furn=[f for f in r['furniture'] if not solid(f['support']) or at(f['xyz'])=='minecraft:air']
    add('furniture_supported',not furn,{'checked':len(r['furniture']),'failed':furn[:5]})
    water=[q for q,s in b.blocks.items() if s.startswith('minecraft:water')];leaks=[]
    for x,y,z in water:
        for dx,dy,dz in [(1,0,0),(-1,0,0),(0,0,1),(0,0,-1),(0,-1,0)]:
            q=(x+dx,y+dy,z+dz)
            if at(q)=='minecraft:air':leaks.append(q)
    add('lake_retaining_basin',not leaks and bool(water),{'water_cells':len(water),'open_edges_or_bottom':len(leaks)})
    # All horizontal pane connection flags are validated against final neighbors.
    wrong=[]
    for q,s in b.blocks.items():
        if states.family(s)!='pane':continue
        n,props=states.parse_state(s)
        for name,off in states.DIRS.items():
            other=at(tuple(q[i]+off[i] for i in range(3)));expected=states.family(other)=='pane' or states.support_cube(other)
            if props[name]!=str(expected).lower():wrong.append([q,name])
    add('pane_connections_final_assembly',not wrong,{'mismatches':len(wrong)})
    lit=sum(x['actual_lamp'] is not None for x in rooms);mats=collections.Counter(x['actual_lamp'] for x in rooms if x['actual_lamp'])
    add('residential_light_variation',0<lit<len(rooms) and len(mats)==2,{'rooms':len(rooms),'lit':lit,'dark':len(rooms)-lit,'lamp_types':dict(mats)})
    overwritten=[l for l in r['lamps'] if at(l['xyz']).split('[')[0]!='minecraft:'+l['material']]
    add('lamps_survive_assembly',not overwritten,{'recorded':len(r['lamps']),'overwritten':overwritten[:4]})
    add('three_complete_rear_enclosures',all(solid((cx,40,cz-9)) for cx,cz in p['tower_centers_xz']),{'note':'sampled core/backing, no claim to real rear window survey'})
    counts=collections.Counter(s.split('[')[0] for s in b.blocks.values());add('thin_blocks_present',any('_slab' in s for s in counts) and any('_pane' in s for s in counts) and 'minecraft:iron_bars' in counts,dict(counts))
    outcome={'run':run,'source_nbt_sha256':sha(path/'building.nbt'),'checks':checks,'passed':sum(c['status']=='pass' for c in checks),'failed':sum(c['status']=='fail' for c in checks),'visual_status':'separate review','game_status':'pending','limitations':['floor-cell continuity is not Minecraft collision/pathfinding','preview water is a static translucent full-cell approximation','unknown room plans and lights remain synthetic']}
    dump(path/'validation.json',outcome);print(json.dumps({'run':run,'passed':outcome['passed'],'failed':outcome['failed'],'failures':[c for c in checks if c['status']=='fail']},ensure_ascii=False));return outcome
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();r=check(a.run);raise SystemExit(bool(r['failed']))
