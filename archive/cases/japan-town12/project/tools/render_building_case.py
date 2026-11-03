"""Read case NBT, construct the existing state-box mesh and render fixed views."""
from pathlib import Path
import argparse,json,sys,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(ROOT/'cases/namsan_tower/src')]
from hafusion.views import ensure_review_views
from vendor.inspect_build import load_build,Limits
import rural_states
from detail_lab.mesh import write_mesh
from PIL import Image
import render_egl_site as egl
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--run',required=True);ap.add_argument('--only',nargs='*');ap.add_argument('--reuse-mesh',action='store_true');ap.add_argument('--output-label');a=ap.parse_args()
    for name in [a.case,a.run,a.output_label or a.run]:
        if Path(name).name!=name:ap.error('simple names required')
    case=ROOT/'cases'/a.case;out=case/'review/previews'/(a.output_label or a.run);out.mkdir(parents=True,exist_ok=True)
    nbt=case/'runs'/a.run/'building.nbt'
    if not a.reuse_mesh:
        print('readback',flush=True)
        b=load_build(nbt,Limits(cells=40_000_000,nodes=16_000_000));print('mesh',len(b.blocks),flush=True)
        meta=write_mesh(b,nbt,out/'scene');print('triangles',meta['triangles'],flush=True);del b
    meta=json.loads((out/'scene/scene.json').read_text())
    if meta['source_nbt_sha256']!=hashlib.sha256(nbt.read_bytes()).hexdigest():raise ValueError('mesh source differs from requested NBT')
    for name,n in meta['triangles'].items():
        if (out/'scene'/(name+'.bin')).stat().st_size!=n*3*10*4:raise ValueError('incomplete mesh buffer: '+name)
    views=ensure_review_views(json.loads((case/'cameras.json').read_text()),meta['size_xyz'])
    unknown=set(a.only or [])-{v['id'] for v in views}
    if unknown:ap.error('unknown view IDs: '+', '.join(sorted(unknown)))
    views=[v for v in views if not a.only or v['id'] in a.only]
    # The preserved EGL renderer retains per-view GPU buffers until process exit.
    # Bound memory by starting a fresh renderer process for each small batch.
    if len(views)>3:
        for start in range(0,len(views),3):
            cmd=[sys.executable,__file__,'--case',a.case,'--run',a.run,'--reuse-mesh','--only',*[v['id'] for v in views[start:start+3]]]
            if a.output_label:cmd.extend(['--output-label',a.output_label])
            subprocess.run(cmd,check=True)
        return
    cp=out/'cameras.json';cp.write_text(json.dumps(views,indent=2));prior=[]
    if (out/'render_report.json').exists():prior=json.loads((out/'render_report.json').read_text())
    egl.ROOT=case/'review';egl.main(a.output_label or a.run,cp,emission_policy='material')
    current=json.loads((out/'render_report.json').read_text())
    for record in current:
        frame=out/record['image']
        with Image.open(frame) as im:im.load()
        if hashlib.sha256(frame.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('preview hash mismatch')
    merged={v['camera']['id']:v for v in prior};merged.update({v['camera']['id']:v for v in current})
    (out/'render_report.json').write_text(json.dumps(list(merged.values()),indent=2));cp.write_text(json.dumps([v['camera'] for v in merged.values()],indent=2))
if __name__=='__main__':main()
