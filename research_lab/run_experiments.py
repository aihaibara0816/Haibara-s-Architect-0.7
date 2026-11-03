"""Isolated, reproducible experiments. No network, world writes or core changes."""
from pathlib import Path
import argparse, json, sys, hashlib, tempfile, copy, os, platform
import numpy as np
from evidence import arbitrate
from stage_cache import demonstration, DiskCache, digest
from alignment import fit_similarity, transform

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def research_experiments(out):
    # Synthetic data explicitly labelled; no invented Canton measurements.
    common=dict(component_id='fixture.deck',attribute='height',source_type='photograph',status='estimated',phase='as_built',epoch='2025')
    rows=[dict(common,source_id='photo-a',source_family='capture-a',value=5,unit='m'),
          dict(common,source_id='photo-b',source_family='capture-b',value=500,unit='cm'),
          dict(common,source_id='historic',source_family='capture-old',value=8,unit='m',epoch='2019')]
    policy=dict(kind='length',tolerance=.02,target_epoch='2025',source_order=['survey','photograph','3d_model'],baseline_hash=digest('synthetic-v1'))
    decision=arbitrate(rows,**policy)
    save(out/'evidence_demo.json',dict(scope='synthetic fixture, not measured Canton data',input=rows,decision=decision))
    with tempfile.TemporaryDirectory() as td:
        cache=DiskCache(td);cold=demonstration(cache);warm=demonstration(DiskCache(td))
        material=demonstration(cache,left_material='minecraft:glass')
        geometry=demonstration(cache,width=3)
        with tempfile.TemporaryDirectory() as fd: full=demonstration(DiskCache(fd),width=3)
    for d in [cold,warm,material,geometry,full]:d.pop('output')
    save(out/'cache_demo.json',dict(scope='synthetic three-component bridge',cold=cold,warm=warm,material_edit=material,geometry_edit=geometry,full=full,
                                  incremental_equals_full=geometry['output_hash']==full['output_hash'],engine_integrated=False))
    a=np.array([[0,0,0],[1,0,0],[0,2,0],[0,0,3]],float)
    rot=np.array([[0,0,-1],[0,1,0],[1,0,0]]);b=a@rot*2.5+[10,20,30]
    aligned=fit_similarity(a,b,target_unit='m',tolerance=.001)
    withheld=np.array([[.2,.3,.7],[2,3,4]])
    aligned['withheld_max_error_m']=float(np.linalg.norm(transform(withheld,aligned['matrix'])-(withheld@rot*2.5+[10,20,30]),axis=1).max())
    aligned['scope']='Synthetic known 3D anchors; not VGGT inference or image-model registration'
    save(out/'alignment_demo.json',aligned)

def upstream_experiment(out,architect):
    sys.path.insert(0,str(ROOT/'upstream/PlanCraft/tools/building'))
    sys.path.insert(0,str(architect))
    from building.model import Model
    from building import buildpaste
    from architect.legacy import core,inspector
    from architect.export_nbt import export_and_readback
    palette={'foundation':'minecraft:stone','facade':'minecraft:white_concrete','door':'minecraft:oak_door','glass_pane':'minecraft:glass_pane'}
    def house(width, mode, tol=.1, door=False):
        shape=[[0,0],[width,0],[width,800],[0,800]]
        wall=dict(type='wall',name='outer',material='facade',closed=True,path=shape,thickness=40,bottom=0,top=300,outside='left')
        if door: wall['openings']=[dict(at=300,width=100,top=200,kind='door')]
        return dict(name='research-house',scale=100,margin=2,ground=0,levels={'ground':0,'roof':300},quantize=mode,quantization={'tolerance':tol},
                    parts=[dict(type='slab',material='foundation',polygon=shape,bottom=-30,top=0),wall,dict(type='slab',material='facade',polygon=shape,bottom=300,top=330)])
    rows=[]
    for width in [1000,985]:
        for mode,tol in [('round',.1),('ceil',.1),('ceil',0.0)]:
            c=Model(house(width,mode,tol),palette).compile();f,g=c.frame,c.grid
            y,z=f.cy(150),f.cz(400)
            start,end=f.cx(40),f.cx(width-40)
            interior=[g.get(x,y,z) for x in range(start,end)]
            rows.append(dict(width_cm=width,real_clear_width_m=(width-80)/100,mode=mode,tolerance_blocks=tol,
                             mapped_outer_width_blocks=f.fx(width)-f.fx(0),mapped_clear_span_blocks=f.fx(width-40)-f.fx(40),
                             clear_air_cells=sum(s=='minecraft:air' for s in interior),grid_size=list(g.shape),non_air=sum(1 for _ in g.non_air())))
    compiled=Model(house(1000,'ceil',0.0,True),palette).compile()
    grid=compiled.grid
    # This transfer is a grid/NBT boundary experiment. It does not extend BuildingSpec.
    scene=core.Scene(grid.shape)
    for x,y,z,state in grid.non_air(): scene.set((x,y,z),state,'fixture.house')
    spec={'environment':{'data_version':3955},'output':{'include_air':False}}
    meta,back,inspection=export_and_readback(scene,spec,out/'plancraft_house_bridge.nbt')
    bp=buildpaste.write(grid,out/'plancraft_house.buildpaste.json')
    bp_diff=buildpaste.diff(grid,buildpaste.read(bp))
    assert bp_diff['ok'] and back.blocks==scene.blocks
    save(out/'quantization_bridge.json',dict(scope='PlanCraft source executed on analytic house; existing Architect/BuildKit NBT writer reused',
          quantization=rows,nbt=meta,buildpaste_readback=bp_diff,nbt_exact=True,
          block_states=sorted(set(scene.blocks.values())),component_identity='one fixture owner; PlanCraft Grid has no original per-component ownership',
          registry_validation='not_run: target Minecraft registry absent',game_validation='not_tested',building_spec_changed=False))

def v5_readback(out,architect,case):
    sys.path.insert(0,str(architect))
    from architect.legacy import inspector
    path=case/'runs/V5_r02/canton280_plaza_v5.nbt'
    build=inspector.load_build(path,inspector.Limits(cells=16_000_000))
    baseline=json.loads((case/'runs/V5_r02/blocks.json').read_text())
    expected={tuple(r[:3]):r[3] for r in baseline['blocks']}
    manifest=json.loads((case/'runs/V5_r02/placement_manifest.json').read_text())
    assembled={};count=0
    for part in manifest['modules']:
        b=inspector.load_build(case/'runs/V5_r02/modules'/part['file'],inspector.Limits(cells=16_000_000))
        offset=part['origin_xyz'];count+=1
        for p,s in b.blocks.items():
            q=tuple(p[i]+offset[i] for i in range(3))
            if q in assembled:raise ValueError('overlapping module coordinates')
            assembled[q]=s
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    result=dict(size=list(build.size),non_air=len(build.blocks),nbt_sha256=sha,
                blocks_json_exact=build.blocks==expected,module_count=count,modules_exact=assembled==build.blocks,
                source_scope='V5_r02 existing files, not regenerated',game_validation='not_tested')
    assert result['blocks_json_exact'] and result['modules_exact']
    save(out/'v5_readback.json',result)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--architect',type=Path,default=ROOT/'baselines/architect-v03')
    p.add_argument('--v5',type=Path,default=ROOT/'baselines/canton-v5')
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    research_experiments(args.out);upstream_experiment(args.out,args.architect)
    if args.v5.exists(): v5_readback(args.out,args.architect,args.v5)
    else: save(args.out/'v5_readback.json',dict(status='not_tested',reason='Provide extracted V5 with --v5; baseline assets are not duplicated in this lab bundle'))
    save(args.out/'environment.json',dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),cuda_inference='not_run',world_changes=False))
    print(json.dumps({'status':'pass','output':str(args.out),'files':[x.name for x in args.out.iterdir()]},ensure_ascii=False))

if __name__=='__main__':main()
