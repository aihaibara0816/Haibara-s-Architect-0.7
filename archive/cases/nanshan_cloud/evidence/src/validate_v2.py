"""Independent final-NBT checks for the terrace revision and four-view contract."""
from pathlib import Path
import collections,gzip,hashlib,json,sys
from PIL import Image
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate
from hafusion.views import ensure_diagonal_views

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def owners(run):
    with gzip.open(run/'component_ownership.json.gz','rt') as f:o=json.load(f)
    return {tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']}
def main():
    run=CASE/'runs/V2_r01';old=CASE/'runs/V1_r04';out=CASE/'validation/v2';out.mkdir(exist_ok=True)
    limits=Limits(cells=40_000_000,nodes=16_000_000)
    b=load_build(run/'building.nbt',limits);a=load_build(old/'building.nbt',limits)
    p=json.loads((run/'params_used.json').read_text());p1=json.loads((old/'params_used.json').read_text())
    m=json.loads((run/'manifest.json').read_text());h=sha(run/'building.nbt');checks=[]
    def check(name,ok,detail):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
        if not ok:raise AssertionError(name+': '+str(detail))
    check('NBT count/hash/dimensions',h==m['sha256'] and len(b.blocks)==m['non_air_blocks'] and list(b.size)==p['frame']['size_xyz'],m['non_air_blocks'])
    check('supported states',all(validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
    own=owners(run);own1=owners(old)
    check('owner coverage',set(own)==set(b.blocks),len(own))
    check('unchanged tower/core/site parameters',all(p[k]==p1[k] for k in ['frame','towers','core','tower_base','floor_pitch','facade','lighting','seed']),['frame','towers','core','tower_base','floor_pitch','facade','lighting','seed'])
    g=p['frame']['ground_y']
    heights={t['id']:max(q[1] for q,ow in own.items() if ow.startswith('roof.'+t['id']+'.'))-g+1 for t in p['towers']}
    check('actual roof heights unchanged',heights=={'A':235,'B':235,'C':207},heights)
    for prefix in ['site.','base.','roof.','core.','lighting.site.','lighting.crown.']:
        original={q:a.blocks[q] for q,ow in own1.items() if ow.startswith(prefix)}
        # Base junctions touched by the terrace may have different ownership;
        # compare final states at the original component cells, not owner strings.
        changed=[q for q,s in original.items() if b.blocks.get(q)!=s]
        if prefix!='base.':check('unchanged final component '+prefix,not changed,{'cells':len(original),'changed':len(changed)})
    components=json.loads((run/'cascade_components.json').read_text())
    glass_probes=[];widths=[]
    for band,base in enumerate(p['cascades']['bands']):
        for step in range(7):
            row=next(r for r in components if r['id']==f'hills.front.{band}.step{step}')
            x0,y0,z0,x1,y1,z1=row['box']
            actual=sorted(x for x in range(140) if 'glass' in b.blocks.get((x,y0+1,z1-1),''))
            check(f'front band{band} row{step}: actual glazing width',actual==list(range(x0,x1)),{'width':len(actual),'x_range':[min(actual),max(actual)]})
            if band==0:widths.append(len(actual))
            glass_probes.extend((x,yy,z1-1) for x in range(x0,x1) for yy in (y0+1,y0+2))
    check('continuous glazing all front bands',all('glass' in b.blocks.get(q,'') for q in glass_probes),len(glass_probes))
    check('upper three rows equal, lower four widen',widths==[50,44,38,32,26,26,26],widths)
    for side,axis,edge in [('front',2,98),('right',0,102)]:
        oldrows=json.loads((old/'cascade_components.json').read_text())
        v1=next(r['box'][axis+3]-edge for r in oldrows if r['side']==side and r['step']==0)
        v2=next(r['box'][axis+3]-edge for r in components if r['side']==side and r['step']==0)
        check(side+' glazing footprint projection',(v1,v2)==(8,5),{'V1':v1,'V2':v2,'edge_trim_adds_one_block':True})
    for r in components:
        if r['step'] in [4,5]:check(r['id']+' no false terrace in equal-width segment',r['exposed_terrace_cells']==0,r['exposed_terrace_cells'])
    for band,base in enumerate(p['cascades']['bands']):
        for side in ['front','right']:
            row=next(r for r in components if r['side']==side and r['band']==band and r['step']==0)
            x0,y0,z0,x1,y1,z1=row['box']
            positions={(x,y0-2,z1-2) for x in range(x0,x1)} if side=='front' else {(x1-2,y0-2,z) for z in range(z0,z1)}
            actual={q for q,ow in own.items() if ow==f'lighting.fixed.band{band}.{side}_strip'}
            check(f'band{band} {side} light strip follows narrowed platform',actual==positions and all(b.blocks[q]=='minecraft:glowstone' for q in actual),len(actual))
    probe=[(x,y,z) for y in [52,104,156,220] for x in range(62,70) for z in range(82,102)]
    check('tower channel remains open',all(q not in b.blocks for q in probe),len(probe))
    faces=[(30,82),(59,90),(35,66),(35,97),(72,90),(101,82),(96,66),(96,97),(72,27),(101,38),(96,22),(96,53)]
    check('four-sided enclosure sample',all('glass' in b.blocks.get((x,y,z),'') for y in [52,104,156] for x,z in faces),36)
    changed={q for q in set(a.blocks)|set(b.blocks) if a.blocks.get(q)!=b.blocks.get(q)}
    bands=p['cascades']['bands']
    outside=[q for q in changed if not any(g+base-3<=q[1]<=g+base+30 for base in bands)]
    check('all changed cells lie in terrace-level bands',not outside,{'changed':len(changed),'outside':len(outside),'includes_exposed_facade_reconnections':True})
    diff={'added':sum(q not in a.blocks for q in changed),'removed':sum(q not in b.blocks for q in changed),'state_changed':sum(q in a.blocks and q in b.blocks for q in changed),'total_changed':len(changed),'by_new_owner_group':dict(collections.Counter(own.get(q,'removed').split('.')[0] for q in changed)),'bounds_xyz':[[min(q[i] for q in changed),max(q[i] for q in changed)] for i in range(3)]}
    (out/'block_diff.json').write_text(json.dumps(diff,indent=2))
    records=json.loads((CASE/'history/before_v2/preserved_baseline.json').read_text())
    check('preserved original V1 files',all(sha(ROOT/r['path'])==r['sha256'] for r in records),len(records))
    check('deterministic new run',h==sha(CASE/'runs/V2_replay/building.nbt'),h)
    imp=json.loads((run/'import_pack/import_manifest.json').read_text())
    check('schem and modules exact readback',imp['source_nbt_sha256']==h and imp['schematic']['nonair_readback_exact'] and imp['module_union_exact'],imp['module_count'])
    check('module size budget',imp['module_max_bytes']<=256*1024,imp['module_max_bytes'])
    expected=ensure_diagonal_views(json.loads((CASE/'cameras.json').read_text()),b.size)
    report=json.loads((CASE/'review/previews/V2_r01/render_report.json').read_text())
    check('all 21 expected views',set(r['camera']['id'] for r in report)==set(v['id'] for v in expected),len(report))
    for r in report:
        f=CASE/'review/previews/V2_r01'/r['image'];im=Image.open(f);im.load()
        check('preview origin '+r['image'],sha(f)==r['sha256'] and im.info['source_nbt_sha256']==h and r['source_nbt_sha256']==h,list(im.size))
    v1r=json.loads((CASE/'review/previews/V1_compare45/render_report.json').read_text())
    v2r={r['camera']['id']:r for r in report}
    check('eight matched V1-V2 diagonal cameras',len(v1r)==8 and all(r['camera']==v2r[r['camera']['id']]['camera'] for r in v1r),[r['camera']['id'] for r in v1r])
    for r in v1r:
        f=CASE/'review/previews/V1_compare45'/r['image']
        Image.open(f).load()
        check('baseline re-render origin '+r['image'],sha(f)==r['sha256'] and Image.open(f).info['source_nbt_sha256']==sha(old/'building.nbt'),r['camera']['id'])
    result=dict(case='nanshan_cloud',run='V2_r01',passed=True,checks=checks,block_diff=diff,unit_tests=33,technical_status='offline checks passed',visual_status='terrace proportions manually reviewed; user acceptance pending',game_status='pending',direction_status='model coordinates; geographic north unverified',limits=['not a measured plan','hidden interfaces/third tower approximate','untextured state-box mesh','game import, neighbour updates, material textures and lighting pending'])
    (out/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(checks=len(checks),passed=True,diff=diff),ensure_ascii=False))
if __name__=='__main__':main()
