from pathlib import Path
import sys,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
egl.ROOT=ROOT/'review';run=sys.argv[1]
if len(sys.argv)>2:egl.main(run,sys.argv[2]);raise SystemExit()
R=ROOT/'runs'/run;D=egl.ROOT/'previews'/run
(egl.ROOT/'assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',egl.ROOT/'assets/render_shader_reference.html')
b=load_build(R/'Room06.nbt',Limits(cells=1000000,nodes=3000000));write_mesh(b,R/'Room06.nbt',D/'scene');apply(b,D/'scene')
views=[
 dict(id='entry_eye',eye=[9.5,4.62,12.4],target=[7.2,4.15,6.6],fov=76),
 dict(id='sofa_eye',eye=[8.7,4.62,8.8],target=[4.8,4.0,6.5],fov=74),
 dict(id='bed_eye',eye=[8.4,4.62,9.2],target=[10.2,3.9,5.5],fov=72),
 dict(id='service_eye',eye=[8.3,4.62,7.7],target=[10.4,4.1,11.5],fov=76),
 dict(id='bath_eye',eye=[6.4,4.62,11.4],target=[4.1,3.9,10.9],fov=76),
 dict(id='cutaway',eye=[24,22,28],target=[8,2.5,9],fov=38,ortho=True,spanX=18,spanZ=12.85,cutY=5.99,bounds=[3,4,13,14]),
 dict(id='plan',eye=[8,30,9],target=[8,2,9],fov=40,ortho=True,spanX=15,spanZ=12,cutY=5.99,bounds=[3,4,13,14]),
 dict(id='exterior',eye=[25,15,30],target=[8,4,9],fov=42),
 dict(id='entry_night',eye=[9.5,4.62,12.4],target=[7.2,4.15,6.6],fov=76,night=True)
]
for v in views:v.update(width=1400,height=1000,concept=False)
(D/'cameras.json').write_text(json.dumps(views,indent=2));records=[]
for i in range(0,len(views),3):
 p=D/f'batch{i}.json';p.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,run,str(p)],check=True);records+=json.loads((D/'render_report.json').read_text())
(D/'render_report.json').write_text(json.dumps(records,indent=2))
