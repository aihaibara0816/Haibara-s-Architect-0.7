"""Read case NBT, construct the existing state-box mesh and render fixed views."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'support'),str(ROOT/'cases/namsan_tower/src')]
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
import render_egl_site as egl
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--run',required=True);ap.add_argument('--only',nargs='*');ap.add_argument('--reuse-mesh',action='store_true');a=ap.parse_args()
    for name in [a.case,a.run]:
        if Path(name).name!=name:ap.error('simple names required')
    case=ROOT/'cases'/a.case;out=case/'review/previews'/a.run;out.mkdir(parents=True,exist_ok=True)
    if not a.reuse_mesh:
        nbt=case/'runs'/a.run/'building.nbt';print('readback',flush=True)
        b=load_build(nbt,Limits(cells=40_000_000,nodes=16_000_000));print('mesh',len(b.blocks),flush=True)
        meta=write_mesh(b,nbt,out/'scene');print('triangles',meta['triangles'],flush=True);del b
    views=json.loads((case/'cameras.json').read_text());views=[v for v in views if not a.only or v['id'] in a.only]
    cp=out/'cameras.json';cp.write_text(json.dumps(views,indent=2));prior=[]
    if (out/'render_report.json').exists():prior=json.loads((out/'render_report.json').read_text())
    egl.ROOT=case/'review';egl.main(a.run,cp,emission_policy='material')
    current=json.loads((out/'render_report.json').read_text());merged={v['camera']['id']:v for v in prior};merged.update({v['camera']['id']:v for v in current})
    (out/'render_report.json').write_text(json.dumps(list(merged.values()),indent=2));cp.write_text(json.dumps([v['camera'] for v in merged.values()],indent=2))
if __name__=='__main__':main()
