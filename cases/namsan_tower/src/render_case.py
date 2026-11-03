"""Read exported NBT, then render its state-aware mesh. No generated scenery."""
from pathlib import Path
import argparse,json,shutil,sys
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF/'support'),str(Path(__file__).parent)]
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh

def cameras():
    def view(name,eye,target,w,h,sx,sz,**kw):
        return dict(id=name,eye=eye,target=target,width=w,height=h,spanX=sx,spanZ=sz,ortho=True,fov=36,concept=False,**kw)
    return [
        view('overview',[630,380,680],[160,135,165],2200,2000,480,436.36),
        view('night',[630,380,680],[160,135,165],2200,2000,480,436.36,night=True),
        view('site_top',[160,780,160],[160,0,160],1700,1700,352,352),
        view('podium',[270,145,305],[163,81,179],1800,1296,125,90),
        view('podium_night',[270,145,305],[163,81,179],1800,1296,125,90,night=True),
        view('observation_pod',[255,215,340],[160,185,176],1700,1500,85,75),
        view('antenna',[250,330,310],[160,253,176],1250,1700,85,115.6),
        view('park_north',[-40,210,0],[135,70,120],1800,1332,250,185),
        view('pavilion',[110,145,185],[110,98,124],1700,1292,50,38),
        view('north_elevation',[160,155,-500],[160,155,176],1450,1800,282,350),
    ]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--only',nargs='*');ap.add_argument('--reuse-mesh',action='store_true');a=ap.parse_args()
    review=CASE/'review';out=review/'previews'/a.run;out.mkdir(parents=True,exist_ok=True)
    assets=review/'assets';assets.mkdir(exist_ok=True)
    shader=HAF/'cases/guangzhou_ctf/review/assets/render_shader_reference.html'
    if not (assets/shader.name).exists():shutil.copy2(shader,assets/shader.name)
    if not a.reuse_mesh:
        print('NBT readback for mesh',flush=True)
        nbt=CASE/'runs'/a.run/'building.nbt';b=load_build(nbt,Limits(cells=40_000_000,nodes=12_000_000))
        meta=write_mesh(b,nbt,out/'scene');print('mesh',meta['triangles'],flush=True);del b
    vs=[v for v in cameras() if not a.only or v['id'] in a.only]
    (out/'cameras.json').write_text(json.dumps(vs,indent=2))
    import render_egl_site as renderer
    prior=json.loads((out/'render_report.json').read_text()) if (out/'render_report.json').exists() else []
    renderer.ROOT=review;renderer.main(a.run,out/'cameras.json',emission_policy='material')
    current=json.loads((out/'render_report.json').read_text())
    merged={v['camera']['id']:v for v in prior};merged.update({v['camera']['id']:v for v in current})
    (out/'render_report.json').write_text(json.dumps(list(merged.values()),indent=2))
    (out/'cameras.json').write_text(json.dumps([v['camera'] for v in merged.values()],indent=2))

if __name__=='__main__':main()
