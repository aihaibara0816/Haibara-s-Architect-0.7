"""Offline acceptance checks; never claim Minecraft runtime validation."""
from pathlib import Path
import collections,gzip,hashlib,json,math,sys
import numpy as np
from PIL import Image
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    run=CASE/'runs/V1_r02';manifest=json.loads((run/'manifest.json').read_text());checks=[]
    def check(name,ok,detail):
        checks.append({'name':name,'passed':bool(ok),'detail':detail})
        if not ok:raise AssertionError(name+': '+str(detail))
    nbt=run/'building.nbt';b=load_build(nbt,Limits(cells=40_000_000,nodes=12_000_000))
    check('exact deterministic replay',sha(nbt)==sha(CASE/'runs/V1_replay/building.nbt'),sha(nbt))
    check('all states supported',all(validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
    check('same exported block count',len(b.blocks)==manifest['non_air_blocks'],len(b.blocks))
    with gzip.open(run/'component_ownership.json.gz','rt') as f:owner=json.load(f)
    ids=owner['owner_names'];points=[(r[:3],ids[r[3]]) for r in owner['xyz_owner']]
    tower=[p for p,o in points if o.startswith('tower.')]
    check('237 block tower envelope',max(p[1] for p in tower)-67+1==237,{'base_y':67,'tip_y':max(p[1] for p in tower)})
    floors=[p for p,o in points if o=='tower.core_service_floor']
    check('service floor stays inside concrete shaft',all(math.hypot(p[0]+.5-160,p[2]+.5-176)<=2.5 for p in floors),len(floors))
    voids=[]
    for y in [116,128]:
        annulus=[(x,y,z) for x in range(151,170) for z in range(167,186) if 5<math.hypot(x-160,z-176)<8]
        ratio=sum(q not in b.blocks for q in annulus)/len(annulus);voids.append(ratio)
    check('equipment rings retain open cells',min(voids)>.1,voids)
    check('dense schematic and module union',json.loads((run/'import_pack/import_manifest.json').read_text())['module_union_exact'], 'Verified by package_import.py against source NBT')
    imp=json.loads((run/'import_pack/import_manifest.json').read_text())
    check('all modules within 256 KiB',all(q['bytes']<=256*1024 for q in imp['modules']),{'count':len(imp['modules']),'largest':imp['module_max_bytes']})
    render=json.loads((CASE/'review/previews/V1_r02/render_report.json').read_text())
    check('ten actual NBT previews',len(render)==10,len(render))
    for r in render:
        image=CASE/'review/previews/V1_r02'/r['image'];im=Image.open(image)
        check('preview '+r['image'],sha(image)==r['sha256'] and im.info['source_nbt_sha256']==sha(nbt),list(im.size))
    baseline=json.loads((CASE/'validation/protected_baseline.json').read_text())
    check('historical core and outputs preserved',all(sha(HAF/p)==s for p,s in baseline.items()),list(baseline))
    grid=json.loads((CASE/'research/terrain/dem_grid.json').read_text())
    check('saved public terrain is complete',len(grid['points'])==121 and all(q['elevation'] is not None for q in grid['points']),grid['dataset'])
    mats=collections.Counter(s.split('[')[0] for s in b.blocks.values())
    check('warm and cool emitters present',mats['minecraft:glowstone']>0 and mats['minecraft:sea_lantern']>0,dict((k,mats[k]) for k in ['minecraft:glowstone','minecraft:sea_lantern','minecraft:redstone_torch']))
    result={'run':'V1_r02','passed':True,'checks':checks,'not_tested':['Minecraft import/game lighting','full pedestrian navigation/collision','real building interiors','high precision topographic survey','RGB tower floodlighting']}
    (CASE/'validation/acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'passed':True,'checks':len(checks),'blocks':len(b.blocks),'nbt_sha256':sha(nbt)}))

if __name__=='__main__':main()
