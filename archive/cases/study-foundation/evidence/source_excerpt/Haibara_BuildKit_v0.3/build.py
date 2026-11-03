#!/usr/bin/env python3
"""Build a known project adapter. No API calls, credentials, world edits or uploads."""
from pathlib import Path
import sys,argparse,json,hashlib,time
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from voxel_core import VERSION,AIR,export_structure
from gafa_colonnade import build
from inspect_build import load_build,inspect,bbox
from make_viewer import make_viewer

def write_json(p,d):
    with Path(p).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2)

def run(project,out):
    start=time.monotonic()
    if out.exists():raise ValueError('Output directory already exists; use a new run name to protect prior results')
    p=json.loads((project/'parameters.json').read_text(encoding='utf8'))
    if p.get('generator')!='gafa_colonnade':raise ValueError('No registered adapter for this project. Ask Codex to implement one; do not guess.')
    scene,stages,geometry=build(p)
    out.mkdir(parents=True)
    events=[];man=[]
    for name,s in stages:
        meta=export_structure(s,out/'stages'/f'{name}.nbt',p['data_version'])
        check=inspect(load_build(out/'stages'/f'{name}.nbt'))
        if not check['usable_nonempty_sample']:raise ValueError('Empty stage')
        events.append({'stage':name,'status':'pass','artifact':'stages/'+name+'.nbt','non_air_blocks':len(s.blocks),'file_sha256':meta['sha256']})
    path=out/'gafa_admin_colonnade.nbt';m=export_structure(scene,path,p['data_version'])
    readback=load_build(path);q=inspect(readback)
    visible={pos:s for pos,s in readback.blocks.items() if s!=AIR}
    if visible!=scene.blocks:raise ValueError('Read-back mismatch: source geometry and NBT differ')
    q.update(source_to_nbt_exact_blockstate_match=True,geometry_checks=geometry,
             validation_scope='Structural subset and source equality, not game or measured reconstruction',
             target_registry_validation='pending',scale_validation='pending',game_validation='pending')
    write_json(out/'qa_report.json',q)
    write_json(out/'parameters_snapshot.json',p)
    write_json(out/'materials.json',dict(Counter(s.split('[')[0] for s in scene.blocks.values())))
    groups=defaultdict(list)
    for pos,cid in scene.owners.items():groups[cid].append(pos)
    write_json(out/'components.json',{cid:{'blocks':len(pts),'bbox_inclusive':bbox(pts)} for cid,pts in groups.items()})
    write_json(out/'model.json',{'size':list(scene.size),'geometry_sha256':scene.fingerprint(),'blocks':[[*pos,s] for pos,s in sorted(scene.blocks.items())]})
    meta={'build_id':out.name,'file_sha256':m['sha256'],'geometry_sha256':scene.fingerprint(),'non_air_blocks':len(scene.blocks),'game_validation':'pending','scale_validation':'pending','materials':'schematic_colors_not_game_textures'}
    viewer=make_viewer(readback,p['title'],out/'review.html',meta)
    events.extend([{'stage':'export_readback','status':'pass','artifact':path.name,'file_sha256':m['sha256']},{'stage':'viewer_written','status':'pass','artifact':'review.html','triangles':viewer['triangles']},{'stage':'game_validation','status':'pending','reason':'No Minecraft process or matching world was accessed'}])
    write_json(out/'placement_manifest.json',{'module':m,'ground_top_local_y':2,'origin_world_xyz':None,'rotation':0,'includes_air':True,'clearance_warning':'Air is explicit throughout the bounding box; use an empty test area. Import/replacement behavior must be tested.','actual_world_version':'unverified','game_validation':'pending'})
    write_json(out/'run_record.json',{'tool_version':VERSION,'events':events,'elapsed_seconds':round(time.monotonic()-start,3),'paid_api_calls':0,'network_calls':0,'cost_note':'Script does not call AI. ChatGPT/Codex authoring consumes account usage separately; not measured here.'})
    print(json.dumps({'status':'prototype_generated_game_pending','out':str(out),'size_xyz':list(scene.size),'non_air_blocks':len(scene.blocks),'nbt_bytes':m['bytes'],'elapsed_seconds':round(time.monotonic()-start,2)},ensure_ascii=False))
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,default=ROOT/'projects'/'gafa_admin')
    ap.add_argument('--run',default='gafa_admin_v001')
    args=ap.parse_args()
    if not args.run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.run):ap.error('Use letters, digits, underscore or hyphen for --run')
    try:run(args.project.resolve(),ROOT/'runs'/args.run)
    except (ValueError,OSError,KeyError,TypeError) as e:print(f'BUILD FAILED: {e}',file=sys.stderr);sys.exit(2)
