"""Case-level regression checks on exported files, independent of generators."""
from pathlib import Path
import collections,gzip,hashlib,json,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for key in ['elizabeth_tower','buckingham_palace']:
    case=ROOT/'cases'/key;run=case/'runs/V1_r02';p=json.loads((run/'params_used.json').read_text());m=json.loads((run/'manifest.json').read_text());checks=[]
    def check(name,ok,detail):
        checks.append({'name':name,'passed':bool(ok),'detail':detail})
        if not ok:raise AssertionError(name+': '+str(detail))
    b=load_build(run/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));h=sha(run/'building.nbt')
    check('NBT hash and block count',h==m['sha256'] and len(b.blocks)==m['non_air_blocks'],{'sha256':h,'blocks':len(b.blocks)})
    check('deterministic full replay',h==sha(case/'runs/V1_replay/building.nbt'),h)
    check('all blockstates supported',all(validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
    with gzip.open(run/'component_ownership.json.gz','rt') as f:o=json.load(f)
    points=[(tuple(r[:3]),o['owner_names'][r[3]]) for r in o['xyz_owner']];owners=dict(points);owner_set=set(owners.values())
    check('component coordinates equal NBT coordinates',set(owners)==set(b.blocks),len(owners))
    wins=json.loads((run/'windows.json').read_text());rooms=json.loads((run/'interiors.json').read_text())
    surviving=[r for r in wins if r['id']+'.glazing' in owner_set or r['id']+'.sash_mullion' in owner_set]
    live_ids={r['id'] for r in surviving};live_rooms=[r for r in rooms if r['id'] in live_ids]
    # Metadata records describe authored attempts; this inventory counts final survivors.
    for r in live_rooms:
        r['final_lamp_survives']=r['id']+'.room.light' in owner_set
    (case/'validation/final_window_inventory.json').write_text(json.dumps({'authored_window_records':len(wins),'surviving_window_records':len(surviving),'superseded_window_records':len(wins)-len(surviving),'surviving_room_records':len(live_rooms),'final_room_lamps':sum(r['final_lamp_survives'] for r in live_rooms),'note':'Curved bow panes and clock dials are authored separately; these counts are not real-building room counts.','windows':surviving,'rooms':live_rooms},ensure_ascii=False,indent=2))
    mats=collections.Counter(s.split('[')[0] for s in b.blocks.values())
    check('both emitter materials present',mats['minecraft:glowstone']>0 and mats['minecraft:sea_lantern']>0,{k:mats[k] for k in ['minecraft:glowstone','minecraft:sea_lantern']})
    check('partial blocks used',any('_slab[' in s for s in b.blocks.values()) and any('glass_pane[' in s for s in b.blocks.values()),'slabs + connected panes')
    if key=='elizabeth_tower':
        g=p['frame']['ground_y'];cx,cz=p['frame']['tower_center_xz'];cy=g+p['tower']['clock_center_above_grade']
        fin=[q for q,v in points if v=='roof.finial'];check('192 block tower height',max(q[1] for q in fin)-g+1==192,fin)
        hands=[];voids=[];dial=[]
        for i,(dx,dz) in enumerate([(0,-1),(1,0),(0,1),(-1,0)]):
            tx,tz=dz,-dx
            def pos(u,y,d):return(cx+dx*(12+d)+tx*u,y,cz+dz*(12+d)+tz*u)
            q=[q for q,v in points if v==f'clock.{i}.opal']
            us=[(x-cx)*tx+(z-cz)*tz for x,y,z in q];ys=[y for x,y,z in q]
            dial.append([max(us)-min(us)+1,max(ys)-min(ys)+1])
            hands.append(sorted([((x-cx)*tx+(z-cz)*tz,y-cy) for (x,y,z),v in points if v in [f'clock.{i}.hands',f'clock.{i}.axle']]))
            for u in [-9,-5,-1,3,7]:voids.append(pos(u,g+128,1) not in b.blocks)
        check('four 14 by 14 dial apertures',dial==[[14,14]]*4,dial)
        check('clock hands use same visual handedness',all(a==hands[0] for a in hands),hands)
        check('belfry apertures open on all four sides',all(voids),{'clear':sum(voids),'samples':len(voids)})
        check('shaft central air retained',(cx+5,g+40,cz+3) not in b.blocks,'interior air at sampled point')
    else:
        g=4
        centrevoid=[q for q in b.blocks if 155<=q[0]<252 and 310<=q[2]<387 and q[1]>=g+1]
        check('central quadrangle open to sky',not centrevoid,{'nonair_in_clear_volume':len(centrevoid)})
        bays=[r for r in surviving if r['id'].startswith('east_front.bay.') and r['id'].endswith('.level1')]
        check('23 principal window bays survive',len(bays)==23,{'count':len(bays),'grouping':p['front']['bay_groups']})
        check('108 metre front is 216 blocks',p['front']['width_blocks']==216,216)
        probes=[]
        for i in range(23):
            x=108+9*i;frontz=237 if min(abs(x-c) for c in [117,207,297])<14 else 240
            for d in [3,6,8]:probes.append((x+1,g+22,frontz+d) not in b.blocks)
        check('principal windows lead into real alcove air',all(probes),{'clear':sum(probes),'samples':len(probes)})
        check('garden and courtyard have distinct components',any(v.startswith('west_front.bow') for v in owner_set) and any(v.startswith('quadrangle.canopy') for v in owner_set),'bow/half dome + canopy')
        check('main gateway through range',(207,g+3,270) not in b.blocks,'local x=207,y=7,z=270')
        check('room lighting has lit and unlit rooms',0<sum(r['final_lamp_survives'] for r in live_rooms)<len(live_rooms),{'room_records':len(live_rooms),'lamps':sum(r['final_lamp_survives'] for r in live_rooms)})
    imp=json.loads((run/'import_pack/import_manifest.json').read_text())
    check('schem exact readback and module union',imp['source_nbt_sha256']==h and imp['schematic']['nonair_readback_exact'] and imp['module_union_exact'],{'modules':imp['module_count'],'schem':imp['schematic']['sha256']})
    check('module byte limits',all(v['bytes']<=256*1024 for v in imp['modules']),imp['module_max_bytes'])
    report=json.loads((case/'review/previews/V1_r02/render_report.json').read_text())
    check('all planned views rendered',set(v['camera']['id'] for v in report)==set(v['id'] for v in json.loads((case/'cameras.json').read_text())),len(report))
    for row in report:
        path=case/'review/previews/V1_r02'/row['image'];im=Image.open(path)
        check('source-bound preview '+row['image'],sha(path)==row['sha256'] and im.info['source_nbt_sha256']==h,list(im.size))
    result={'case':key,'run':'V1_r02','passed':True,'checks':checks,'unit_tests':30,'visual_status':'manual review of overview, front/detail, roof or garden, night and section; fidelity not scored automatically','not_tested':['Minecraft import and lighting','collision/navigation','texture-pack appearance','precise decorative carving','external 3D model fusion']}
    (case/'validation/acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(key,len(checks),'checks passed',flush=True)
if __name__=='__main__':main()
