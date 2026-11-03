"""Independent readback acceptance for the Guangzhou Customs delivery.

Checks actual exported coordinates/states, not the builder's proposed values.
Does not turn technical checks into a fidelity score or a game test.
"""
from pathlib import Path
import argparse, collections, csv, gzip, hashlib, json, math, sys
from PIL import Image
CASE=Path(__file__).resolve().parents[1]; ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab.states import validate,boxes,parse_state,DIRS,family
from hafusion.views import ensure_diagonal_views

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='V1_r04');ap.add_argument('--replay',default='V1_replay_r04');ap.add_argument('--geometry-only',action='store_true');a=ap.parse_args()
    run=CASE/'runs'/a.run; p=json.loads((run/'params_used.json').read_text());m=json.loads((run/'manifest.json').read_text())
    b=load_build(run/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000)); h=sha(run/'building.nbt');g=p['frame']['ground_y']
    with gzip.open(run/'component_ownership.json.gz','rt') as f: owner_data=json.load(f)
    own={tuple(v[:3]):owner_data['owner_names'][v[3]] for v in owner_data['xyz_owner']}
    checks=[]
    def ck(name,ok,details):
        checks.append(dict(name=name,passed=bool(ok),details=details))
        if not ok: print('FAIL',name,details,flush=True)
    ck('NBT exact manifest and dimensions',h==m['sha256'] and len(b.blocks)==m['non_air_blocks'] and list(b.size)==p['frame']['size_xyz'],{'blocks':len(b.blocks),'hash':h,'size':b.size})
    ck('supported complete block states',all(validate(s) for s in set(b.blocks.values())),len(set(b.blocks.values())))
    ck('complete component ownership',set(own)==set(b.blocks),len(own))
    top=max(y for x,y,z in b.blocks)
    ck('137-block study envelope including needle',top-g+1==137,{'top_cell_y':top,'grade_y':g,'not_a_survey':True})
    # Broad structure probes independent of each surface generation loop.
    probes=[(25,66,55),(101,66,55),(63,66,28),(52,66,75)]
    ck('all four sides have masonry enclosure',all('quartz' in b.blocks.get(q,'') for q in probes),probes)
    ck('rear central projection actually extends behind wings',all((63,y,28) in b.blocks for y in [42,66,94]) and all((42,y,28) not in b.blocks for y in [42,66,94]),'central z=28; side wings begin z=39')
    # True window reveals: glass at depth -1 and air at the external wall plane.
    windows=json.loads((run/'windows.json').read_text()); checked=[]
    for w in windows:
        if not w['id'].startswith('tower.') or '.upper.' in w['id'] or '.f19.' in w['id'] or '.f20.' in w['id']: continue
        x,y,z=w['anchor'];dx,dz=w['normal_xz']
        if y>=g+94:continue
        glass=b.blocks.get((x-dx,y,z-dz),'')
        if 'glass' not in glass or (x,y,z) in b.blocks:checked.append(w['id'])
    ck('recessed tower window glass and clear reveals',not checked,{'failures':checked,'definition':'front wall plane empty; glazing one block behind'})
    # The feature arch is on the front only, with a clear space behind it.
    ck('large front arch glazing',all('glass' in b.blocks.get((63,y,74),'') for y in [101,108,113]),'central large arch')
    ck('arch space behind glazing remains hollow',all((63,y,70) not in b.blocks for y in [102,106,110,114]),'no full floor slabs filling the arch')
    ck('crown paired columns separated',all((x,105,77) in b.blocks for x in [54,57,69,72]) and all((x,105,77) not in b.blocks for x in [55,56,70,71]),'one-block shafts preserve pair gaps')
    for face in range(4):
        face_cells={q:b.blocks[q] for q,o in own.items() if o.startswith(f'clock.dial{face}.')}
        whites=sum(v=='minecraft:white_concrete' for v in face_cells.values())
        ink=sum(v=='minecraft:black_concrete' for v in face_cells.values())
        ck(f'clock face {face}: light face readable',whites>ink*2 and whites>=30,{'white':whites,'black_marks':ink})
    dome=[q for q,o in own.items() if o=='clock.dome.metal']
    ck('dome cap supported without floating rings',all((q[0],q[1]-1,q[2]) in b.blocks for q in dome),len(dome))
    ck('slender needle not a solid multi-block mast',all(sum(1 for x,y,z in b.blocks if y==yy)<=1 for yy in range(g+130,g+137)),7)
    for i in range(2):
        ck(f'podium glass enclosure {i}',sum(1 for q,o in own.items() if o==f'podium.pavilion{i}.skin' and 'glass' in b.blocks[q])>100,'visible dark glazing, roof and opaque grid')
    for i in range(3):
        ck(f'podium side arch {i}',sum(1 for q,o in own.items() if o==f'podium.arcade{i}.glazing')>50,'provisional model-right assignment')
    ck('roof green proxy restricted to observed rear area',all(q[2]<38 for q,o in own.items() if o=='podium.roof.color_proxy'),'not a green lawn around the entire building')
    # Evaluate the actual centreline tread top heights from state geometry.
    heights=[]
    for z in range(107,100,-1):
        top=max(y+box[4] for (x,y,zz),s in b.blocks.items() if x==63 and zz==z and y<g+5 for box in boxes(s))
        heights.append(top)
    ck('entrance six half-block rises reach landing',heights==[4.5,5,5.5,6,6.5,7,7],heights)
    ck('entry doorway four-block clearance',all((x,y,84) not in b.blocks for x in range(60,67) for y in range(g+3,g+7)),'width 7, clear height 4')
    ck('entrance landing has solid support',all((63,y,99) in b.blocks for y in range(g-1,g+3)),'no suspended foundation band')
    rooms=json.loads((run/'interiors.json').read_text());ids=[r['id'] for r in rooms]
    ck('stable unique room IDs',len(ids)==len(set(ids)),len(ids))
    lamp_counts=collections.Counter(r['actual_lamp'] or 'off' for r in rooms)
    ck('each scheduled lamp matches exported block',all(b.blocks.get(tuple(r['lamp_position']))=='minecraft:'+r['actual_lamp'] for r in rooms if r['actual_lamp']),dict(lamp_counts))
    ck('unique reserved fixtures including dark rooms',len({tuple(r['lamp_candidate']) for r in rooms})==len(rooms),len(rooms))
    ck('no failed occupied room lamp placements',all(r['expected_material']==r['actual_lamp'] for r in rooms),'candidate slots reserved by geometry')
    ck('dark, warm and cool populations present',all(lamp_counts[n]>100 for n in ['off','glowstone','sea_lantern']),dict(lamp_counts))
    ck('furnishings go beyond a closed shell',all(any(s.startswith('minecraft:'+n) for s in b.blocks.values()) for n in ['bookshelf','anvil','oak_leaves','dark_oak_stairs']),'synthetic desks, shelves, planting and seats')
    # Connection flags describe the fully assembled scene, not per-module caps.
    bad=[]
    for q,s in b.blocks.items():
        if family(s)!='pane':continue
        _,state=parse_state(s)
        for name,off in DIRS.items():
            nq=tuple(q[i]+off[i] for i in range(3));ns=b.blocks.get(nq)
            if ns and family(ns)=='pane':
                opp={'north':'south','south':'north','east':'west','west':'east'}[name]
                if state[name]!='true' or parse_state(ns)[1][opp]!='true':bad.append(q)
    ck('pane and bar connections symmetric',not bad,len(bad))
    material_rows=list(csv.DictReader((run/'materials.csv').read_text(encoding='utf-8-sig').splitlines()))
    counts=collections.Counter(s.split('[')[0] for s in b.blocks.values())
    ck('material schedule from final states',counts=={r['block_id']:int(r['count']) for r in material_rows},len(counts))
    if not a.geometry_only:
        ck('deterministic replay NBT',h==sha(CASE/'runs'/a.replay/'building.nbt'),h)
        imp=json.loads((run/'import_pack/import_manifest.json').read_text())
        ck('schematic and module union readback',imp['source_nbt_sha256']==h and imp['schematic']['nonair_readback_exact'] and imp['module_union_exact'],imp['module_count'])
        ck('NBT module compressed size budget',imp['module_max_bytes']<=256*1024,imp['module_max_bytes'])
        prev=CASE/'review/previews'/a.run;rs=json.loads((prev/'render_report.json').read_text())
        expected=ensure_diagonal_views(json.loads((CASE/'cameras.json').read_text()),b.size)
        ck('complete full and detail camera set',{r['camera']['id'] for r in rs}=={v['id'] for v in expected},len(rs))
        for r in rs:
            fp=prev/r['image'];im=Image.open(fp);im.load()
            ck('source-linked preview '+r['image'],sha(fp)==r['sha256'] and im.info['source_nbt_sha256']==h and r['source_nbt_sha256']==h,im.size)
        byid={r['camera']['id']:r['camera'] for r in rs};keys=['target','spanX','spanZ','width','height','sun_day']
        diagonal=[byid[q+'_'+mode] for q in ['se','sw','ne','nw'] for mode in ['day','night']]
        ck('eight canonical quadrants share camera scale',all(all(c[k]==diagonal[0][k] for k in keys) for c in diagonal),keys)
        ck('exact horizontal 45 degrees',all(abs(abs(c['eye'][0]-c['target'][0])-abs(c['eye'][2]-c['target'][2]))<1e-9 for c in diagonal),8)
        ck('shared sun does not rotate between quadrants',all(c['sun_day']==[.6,.9,.8] for c in diagonal),diagonal[0]['sun_day'])
    out=CASE/'validation'/('geometry_acceptance.json' if a.geometry_only else 'acceptance.json')
    result={'case':'guangzhou_customs','run':a.run,'passed':all(c['passed'] for c in checks),'checks':checks,'technical_status':'offline file and geometry checks passed','fidelity_status':'manual preview review; user acceptance pending','game_status':'pending','limits':['height/plan/geo bearing unresolved','actual material textures and neighbour physics not rendered','night and interior are game design proposals','partial synthetic circulation; full building navigation not certified']}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'room_lighting':dict(lamp_counts),'failures':[c['name'] for c in checks if not c['passed']]},ensure_ascii=False));sys.exit(0 if result['passed'] else 1)

if __name__=='__main__':main()
