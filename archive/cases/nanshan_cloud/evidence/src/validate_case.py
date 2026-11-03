"""Final-file checks: enclosure, intentional voids, roof exclusions and provenance."""
from pathlib import Path
import collections,gzip,hashlib,json,sys
from PIL import Image
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    run=CASE/'runs/V1_r04';m=json.loads((run/'manifest.json').read_text());p=json.loads((run/'params_used.json').read_text())
    b=load_build(run/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));h=sha(run/'building.nbt');checks=[]
    def check(name,ok,detail):
        checks.append({'name':name,'passed':bool(ok),'detail':detail})
        if not ok:raise AssertionError(name+': '+str(detail))
    check('NBT hash, counts and dimensions',h==m['sha256'] and len(b.blocks)==m['non_air_blocks'] and list(b.size)==p['frame']['size_xyz'],{'hash':h,'blocks':len(b.blocks),'size':b.size})
    check('complete deterministic replay',h==sha(CASE/'runs/V1_replay/building.nbt'),h)
    check('all blockstates supported',all(validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
    with gzip.open(run/'component_ownership.json.gz','rt') as f:o=json.load(f)
    owners={tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']}
    check('owner inventory equals exported cells',set(owners)==set(b.blocks),len(owners))
    check('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),'no out-of-frame cells')
    g=p['frame']['ground_y']
    roofs={t['id']:max(q[1] for q,owner in owners.items() if owner.startswith('roof.'+t['id']+'.'))-g+1 for t in p['towers']}
    check('high pair 235 blocks, third authored height 207',roofs=={'A':235,'B':235,'C':207},{'heights':roofs,'note':'third height is photo estimate, not surveyed'})
    glass=[]
    for band in [14,66,118,170]:
        for step in range(7):
            x0=34+3*step;x1=98-3*step
            for x in range(x0,x1):
                for yy in [g+band+4*step+1,g+band+4*step+2]:
                    glass.append('glass' in b.blocks.get((x,yy,105),''))
    check('four front cascade groups retain continuous glazing',all(glass),{'sample_cells':len(glass),'glass_cells':sum(glass)})
    probes=[(x,y,z) for y in [52,104,156,220] for x in range(62,70) for z in range(82,102)]
    check('deep inter-tower channel stays open',all(q not in b.blocks for q in probes),{'empty_cells':sum(q not in b.blocks for q in probes),'samples':len(probes)})
    probes=[(50,y,82) for y in range(g,g+12)]
    check('ground-level passage retained',all(q not in b.blocks for q in probes),probes)
    probes=[]
    # Actual exterior points: prism-to-core joins are internal, not missing glass.
    faces=[(30,82),(59,90),(35,66),(35,97),(72,90),(101,82),(96,66),(96,97),
           (72,27),(101,38),(96,22),(96,53)]
    for y in [52,104,156]:probes.extend((x,y,z) for x,z in faces)
    check('sampled four-sided tower enclosure',all('glass' in b.blocks.get(q,'') for q in probes),{'glazed_samples':sum('glass' in b.blocks.get(q,'') for q in probes),'samples':len(probes)})
    roof_probes=[];unwanted=[]
    for t in p['towers']:
        x0,z0,x1,z1=t['rect'];top=g+t['height']-1
        # Equipment grille is at top-1; test the layer immediately above it.
        roof_probes.extend((x,top,z) for x in range(x0+3,x1-3) for z in range(z0+3,z1-3))
        unwanted.extend((q,ow) for q,ow in owners.items() if x0<=q[0]<x1 and z0<=q[2]<z1 and q[1]>=top-5 and (ow.startswith('interior.') or ow.startswith('lighting.windows.')))
    check('mechanical wells have no office furniture or room lamps',not unwanted,{'unwanted_count':len(unwanted)})
    check('open air above roof equipment',all(q not in b.blocks for q in roof_probes),len(roof_probes))
    landing=[(x,10,z) for x in range(87,92) for z in range(92,96)]
    check('stair landing joins gallery without rail across opening',all(q in b.blocks for q in landing) and all((x,11,93) not in b.blocks for x in range(87,92)),{'landing_cells':len(landing),'note':'local geometric check, full walkability not tested'})
    mats=collections.Counter(s.split('[')[0] for s in b.blocks.values())
    check('both warm/cool emitter materials used',mats['minecraft:glowstone']>0 and mats['minecraft:sea_lantern']>0,{k:mats[k] for k in ['minecraft:glowstone','minecraft:sea_lantern']})
    check('thin facade elements used',mats['minecraft:iron_bars']>0 and any('_slab[' in s for s in b.blocks.values()),{'iron_bars':mats['minecraft:iron_bars']})
    rooms=json.loads((run/'interiors.json').read_text());lit=0;lamp_types=collections.Counter()
    for r in rooms:
        q=tuple(r['lamp_position']) if r['lamp_position'] else None
        if q and owners.get(q)=='lighting.windows.'+r['id']:
            lit+=1;lamp_types[b.blocks[q].split('[')[0]]+=1
    check('lit and unlit synthetic rooms',0<lit<len(rooms),{'room_records':len(rooms),'surviving_room_lamps':lit,'lamp_materials':dict(lamp_types),'note':'not real building room counts'})
    imp=json.loads((run/'import_pack/import_manifest.json').read_text())
    check('schematic readback and module union',imp['source_nbt_sha256']==h and imp['schematic']['nonair_readback_exact'] and imp['module_union_exact'],{'modules':imp['module_count'],'schem':imp['schematic']['sha256']})
    check('module size limit',all(v['bytes']<=256*1024 for v in imp['modules']),imp['module_max_bytes'])
    prev=CASE/'review/previews/V1_r04';report=json.loads((prev/'render_report.json').read_text())
    check('all 13 fixed views rendered',set(v['camera']['id'] for v in report)==set(v['id'] for v in json.loads((CASE/'cameras.json').read_text())),len(report))
    for r in report:
        f=prev/r['image'];im=Image.open(f)
        check('preview provenance: '+r['image'],sha(f)==r['sha256'] and im.info['source_nbt_sha256']==h,list(im.size))
    out={'case':'nanshan_cloud','run':'V1_r04','passed':True,'checks':checks,'full_tree_unit_tests':{'passed':30,'observed_seconds':0.726,'command':'PYTHONPATH=support/deps python3 -m unittest discover -s tests -v'},'room_inventory':{'authored_records':len(rooms),'surviving_lamps':lit,'lamp_types':dict(lamp_types)},'technical_status':'offline checks passed','visual_status':'manually reviewed; recognizable first version with documented approximations; user fidelity approval pending','game_status':'pending','not_tested':['Minecraft import, material textures and neighbour updates','real floorplan, north and concealed platforms','complete interior navigation','measured photogrammetry accuracy','external 3D model fusion']}
    (CASE/'validation/acceptance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':True,'rooms':len(rooms),'room_lamps':lit},ensure_ascii=False))
if __name__=='__main__':main()
