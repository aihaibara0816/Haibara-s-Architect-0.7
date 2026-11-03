"""Actual local HAFusion execution: staged geometry -> materials -> NBT -> QA."""
from .bootstrap import ROOT,CASE
from .cache import Stages
from .constraints import make_rings,choose_axis
from .canton import CantonGeometry,load,rows,scene,make_site
from .qa import export_checked,export_modules,validate_final
from .evidence import apply_reviewed
from common import Scene,dump,digest as file_hash,PALETTE,parse_state
from member_shapes import block_parts
from research_lab.stage_cache import digest
from collections import Counter,defaultdict
from pathlib import Path
import json,time,sys,platform

def build(run_id, *, cache_root=None, material_overrides=None, core_max_shift=3, ring_inset=1.6):
    out=ROOT/'runs'/run_id
    if out.exists():raise ValueError('Immutable run exists; choose a new run ID')
    out.mkdir(parents=True)
    start=time.time();overrides=material_overrides or {}
    source={str(p.relative_to(ROOT)):file_hash(p) for p in sorted((CASE/'inputs').rglob('*')) if p.is_file()}
    original=json.loads((CASE/'runs/V5_r02/blocks.json').read_text())
    if file_hash(CASE/'runs/V5_r02/canton280_plaza_v5.nbt')!='9cacf7cc2ebe615e63b799c5fde792736af624a94b58414776e03e574855d18b':
        raise ValueError('Frozen V5 NBT changed')
    code={str(p.relative_to(ROOT)):file_hash(p) for folder in [ROOT/'hafusion',CASE/'src',CASE/'vendor',ROOT/'research_lab'] for p in sorted(folder.glob('*.py'))}
    context={'frame_id':'canton-v5-x-yup-z+south-study','units':'block','target_epoch':'V5-reviewed-2024-2025-site','source_hash':digest(source)}
    stages=Stages(cache_root or ROOT/'cache',context,digest(code))
    holder={}
    def geom(center=None):
        center=center or [28.5,28.5]
        if tuple(center) not in holder:holder[tuple(center)]=CantonGeometry(center)
        return holder[tuple(center)]
    def fit():
        g=geom();rings=make_rings(g,ring_inset);axis=choose_axis(g,rings,max_shift=core_max_shift)
        return {'rings':rings,'axis':axis,'model_transform':g.route.report['matrix_source_metres_to_blocks']}
    fitdata=stages.run('geometry.layout',{'max_core_shift':core_max_shift,'ring_inset':ring_inset},{},fit)
    base={'core_center_xz':[28.5,28.5]}
    proposal={'path':'/core_center_xz','old':base['core_center_xz'],'new':fitdata['axis']['selected']['center_xz'],
              'review':'accepted','status':'estimated','reason':'Minimum feasible integer translation within 3 cells avoids checked ring/frame collisions; external model silhouette remains fixed.',
              'evidence':['inputs/images/R08.jpg','inputs/images/R14.jpg','inputs/v4_images/U04.png','geometry.layout/axis/candidates']}
    chosen=apply_reviewed(base,[proposal],digest(base),lambda v:None,{'/core_center_xz'})
    center=chosen['core_center_xz'];parts={}
    for name in ['inner','rings','outer','crown','mast']:
        def create(name=name):
            s=Scene((56,282,56));g=geom(center)
            if name=='rings':g.rings(s,fitdata['rings'])
            else:getattr(g,name)(s)
            return rows(s)
        parts[name]=stages.run('geometry.'+name,{'core_center':center} if name=='inner' else {},
                               {'reviewed_layout':'geometry.layout'},create)
    site=stages.run('geometry.assembly',{'scope':'1F and above'},
                   {name:'geometry.'+name for name in parts},lambda:make_site(geom(center),parts))
    # Geometry retains original block-shape tokens. Material substitutions are
    # cached independently and must retain those shapes; no fake preview thinning.
    groups=defaultdict(list)
    for r in site['rows']:
        o=r[4];group='frame.rings' if o.startswith(('frame.ring.','frame.ring_joint.')) else o.split('.')[0]
        groups[group].append(r)
    final=[]
    for group,data in sorted(groups.items()):
        used={r[3] for r in data};mapping={k:v for k,v in overrides.items() if k in used}
        for old,new in mapping.items():
            parse_state(new)
            if block_parts(old)!=block_parts(new):raise ValueError('Material edit changes block geometry; use a geometry revision')
        result=stages.run('material.'+group,{'mapping':mapping},{'geometry':'geometry.assembly'},
                         lambda data=data,mapping=mapping:[[*r[:3],mapping.get(r[3],r[3]),r[4]] for r in data])
        final.extend(result)
    s=scene(final,site['size']);meta,b=export_checked(s,out/'GAFAcraft_Canton280_V6.nbt')
    modules=export_modules(s,out,site['offset'])
    checks,details=validate_final(s,site,fitdata['rings'],original['blocks'])
    checks.update(nbt_independent_readback_exact=True,modules_reassemble_exactly=True)
    checks['source_model_hash_unchanged']=file_hash(CASE/'inputs/model/source.skp')=='26d4ca7237b4d3e870b421ba3260412d8e215d63e335beb559e48a4927c3fa72'
    occupancy=digest(sorted([list(q) for q in s.blocks]));ownership=digest([[*q,s.owners[q]] for q in sorted(s.blocks)])
    dump(out/'blocks.json',{'size_xyz':list(s.size),'geometry_sha256':s.fingerprint(),'occupancy_sha256':occupancy,'ownership_sha256':ownership,'blocks':rows(s)})
    dump(out/'component_artifacts.json',{'geometry':stages.keys,'component_counts':dict(Counter(s.owners.values())),'note':'Material stages have grouped keys; actual per-block component IDs remain retained.'})
    dump(out/'evidence_decisions.json',{'core':proposal,'core_search':fitdata['axis'],
       'kept':[{'component':'outer_columns','source':'Reviewed SKP centerlines; original source hash fixed'},
               {'component':'crown','source':'V2A fitted inclined roof plane and 16 historical schematic cabins'},
               {'component':'program','source':'Reviewed R14 design diagram bands + R08/R16 qualitative photo checks'},
               {'component':'plaza','source':'V5 reviewed above-ground scope and dated photo topology'}],
       'not_measured':['core center','ring inclination and nonuniform spacing','site elevations','geographic north'],
       'source_hashes':source})
    dump(out/'geometry_layout.json',fitdata);dump(out/'cache_report.json',stages.summary())
    dump(out/'validation.json',{'checks':checks,'details':details,'game':'pending'})
    dump(out/'materials.json',{'scope':'Final independently read NBT; finished blocks, not raw crafting materials',
                             'non_air_total':len(b.blocks),'block_states':dict(Counter(b.blocks.values())),
                             'blocks':dict(Counter(parse_state(v)[0] for v in b.blocks.values()))})
    dump(out/'placement_manifest.json',{'size_xyz':list(s.size),'modules':modules,'reassembly_exact':True,'levels':site['levels'],
            'max_origin_y_if_world_exclusive_upper_bound_320':38,'mode':'Complete NBT OR modules. Sparse output does not clear old blocks. Use an empty test region.'})
    # Load palette by the frozen final V5 instead of import-order-dependent globals.
    palette=json.loads((CASE/'runs/V5_r02/palette.json').read_text());known={v[0]:v[1] for v in palette.values()}
    for st in set(b.blocks.values()):
        if st not in known:
            n=parse_state(st)[0];color=next((c for state,c in known.items() if parse_state(state)[0]==n),'#B8C5C4')
            palette[st]=[st,color]
    dump(out/'palette.json',palette)
    dump(out/'configuration.json',{'version':'HAFusion 0.1','core_max_shift':core_max_shift,'ring_inset':ring_inset,
                                    'core_center':center,'material_overrides':overrides,'source_hash':digest(source),'code_hashes':code})
    report={'run_id':run_id,'status':'pass' if all(checks.values()) else 'fail','checks':checks,'nbt':meta,
            'non_air':len(b.blocks),'geometry_sha256':s.fingerprint(),'occupancy_sha256':occupancy,'ownership_sha256':ownership,
            'seconds':round(time.time()-start,3),'cache':stages.summary(),'game_validation':'pending',
            'python':sys.version,'platform':platform.platform(),'upstream':'PlanCraft code reused; Arnis / ObjToSchematic staging concepts independently implemented.'}
    dump(out/'build_report.json',report)
    print(json.dumps({k:report[k] for k in ['run_id','status','non_air','seconds','checks']},ensure_ascii=False),flush=True)
    if not all(checks.values()):raise ValueError('Final QA failed; run retained for diagnosis')
    return report
