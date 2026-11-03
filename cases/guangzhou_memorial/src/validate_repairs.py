"""Behavioral regression checks against delivered NBT, not builder intermediates."""
from pathlib import Path
from collections import deque,Counter
import json,gzip,sys,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import support_cube
CASE=Path(__file__).resolve().parents[1]

def read(run):
    r=CASE/'runs'/run;b=load_build(r/'building.nbt',Limits(cells=40000000,nodes=64000000))
    p=json.loads((r/'params_used.json').read_text());o=json.loads(gzip.decompress((r/'component_ownership.json.gz').read_bytes()))
    return b,p,{tuple(x[:3]):o['owner_names'][x[3]] for x in o['xyz_owner']}

def review(b,p,owners):
    cx,cz=p['center_xz'];fy=p['floor_y'];checks=[]
    def solid(x,y,z):
        st=b.blocks.get((cx+x,y,cz+z));return bool(st and support_cube(st))
    def add(k,ok,detail):checks.append({'id':k,'pass':bool(ok),'detail':detail})
    # The first defect: full 5 x 5 bases need continuous bearing underneath, all eight columns.
    feet=[(u+dx,fy,z) for u in p['entrance_columns_x'] for dx in range(-2,3) for z in range(62,67)]
    missing=[q for q in feet if not solid(*q)]
    add('column_base_bearing',not missing,{'samples':len(feet),'unsupported':len(missing)})
    # Check the whole band that was previously absent, not just the eight anchor points.
    band=[(x,fy,z) for x in range(-40,41) for z in range(59,66)]
    miss=[q for q in band if not solid(*q)]
    add('portico_landing_continuity',not miss,{'samples':len(band),'missing':len(miss)})
    # Floor-top path with two air cells. Collision/half-block stair routing still needs a game.
    def walk(q):
        x,z=q
        return solid(x,fy,z) and all((cx+x,y,cz+z) not in b.blocks for y in [fy+1,fy+2])
    start=(0,70);goal=(0,51);seen={start} if walk(start) else set();todo=deque(seen)
    while todo:
        x,z=todo.popleft()
        for q in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
            if -40<=q[0]<=40 and 50<=q[1]<=70 and q not in seen and walk(q):seen.add(q);todo.append(q)
    add('porch_to_hall_path',goal in seen,{'visited':len(seen),'test':'flat full-block floor and two-cell headroom; not a game collision test'})
    base=[q for q,o in owners.items() if o.startswith('central.clerestory.face') and q[1]==61]
    unsupported=[q for q in base if (q[0],60,q[2]) not in b.blocks]
    add('clerestory_bottom_sealed',bool(base) and not unsupported,{'base_cells':len(base),'open_below':len(unsupported),'first_gaps':unsupported[:12]})
    corners=[]
    for x in [-46,46]:
        for z in [-38,38]:
            ys=[y for y in range(50,56) if 'lapis_block' in b.blocks.get((cx+x,y,cz+z),'')]
            corners.append({'xz':[x,z],'blue_roof_y':ys})
    add('four_roof_corner_connections',all(c['blue_roof_y'] for c in corners),corners)
    closings=[(x,y,z) for x in [-49,49] for z in [-38,38] for y in range(47,50)]
    add('corner_recessed_enclosure',all(solid(*q) for q in closings),{'samples':len(closings),'missing':sum(not solid(*q) for q in closings)})
    sign=[q for q,o in owners.items() if o.startswith('entry.plaque.')]
    width=max(q[0] for q in sign)-min(q[0] for q in sign)+1
    height=max(q[1] for q in sign)-min(q[1] for q in sign)+1
    symbols=sum(o=='entry.plaque.symbol' for o in owners.values())
    add('small_symbolic_plaque',width<=13 and height<=4 and symbols==4,{'width':width,'height':height,'one_block_symbols':symbols})
    soffit=[(x,35,z) for x in range(-36,37,12) for z in [57,60,63]]
    add('portico_soffit_coverage',all((cx+x,y,cz+z) in b.blocks for x,y,z in soffit),{'samples':len(soffit),'missing':sum((cx+x,y,cz+z) not in b.blocks for x,y,z in soffit)})
    return checks

def main():
    run=sys.argv[1];baseline='V1_r03';old,op,oo=read(baseline);new,np,no=read(run)
    before=review(old,op,oo);after=review(new,np,no)
    changed=[q for q in old.blocks.keys()|new.blocks.keys() if old.blocks.get(q)!=new.blocks.get(q)]
    # All repaired geometry must stay in the entry/upper-junction volume, not alter garden/interior seating.
    cx,cz=np['center_xz']
    def within(q):
        x,y,z=q[0]-cx,q[1],q[2]-cz
        return (-48<=x<=48 and 4<=y<=36 and 53<=z<=70) or (-25<=x<=25 and 40<=y<=52 and 58<=z<=63) or (-56<=x<=56 and -70<=z<=61 and 35<=y<=61)
    stray=[q for q in changed if not within(q)]
    report={'baseline':baseline,'run':run,'before':before,'after':after,'new_checks_passed':sum(x['pass'] for x in after),'new_checks_total':len(after),
      'negative_control_detects': [x['id'] for x in before if not x['pass']],
      'changed_cells':len(changed),'outside_authorized_regions':len(stray),'first_stray':stray[:12],
      'changed_owner_groups':dict(Counter((no.get(q) or oo.get(q)).split('.')[0] for q in changed)),
      'baseline_nbt_sha256':hashlib.sha256((CASE/'runs'/baseline/'building.nbt').read_bytes()).hexdigest(),
      'final_nbt_sha256':hashlib.sha256((CASE/'runs'/run/'building.nbt').read_bytes()).hexdigest(),
      'game_status':'pending','engine_version':'HAF 0.2','haf03_status':'planned after additional independent cases'}
    (CASE/'runs'/run/'repair_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
    assert not stray and all(x['pass'] for x in after)
    assert sum(not x['pass'] for x in before)>=6,'Negative control must actually catch the old defects'
if __name__=='__main__':main()
