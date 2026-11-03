from pathlib import Path
import sys,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states,japanese_detail_states,corner_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from preview_material_marks import apply
import render_egl_site as egl
egl.ROOT=ROOT/'review';mode=sys.argv[1]
if len(sys.argv)>2:egl.main(mode,sys.argv[2]);raise SystemExit()
R=ROOT/'runs'/mode;D=egl.ROOT/'previews'/mode
(egl.ROOT/'assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',egl.ROOT/'assets/render_shader_reference.html')
b=load_build(R/'InteriorDetail05.nbt',Limits(cells=1000000,nodes=5000000));write_mesh(b,R/'InteriorDetail05.nbt',D/'scene');apply(b,D/'scene')
vs=[]
for room in json.loads((R/'spec.json').read_text())['rooms']:
 ox,f,oz=room['origin'];id=room['id'];target=[ox+5.5,f+1.5,oz+3.5]
 vs.append(dict(id=id+'_eye',eye=[ox+6.5,f+2.62,oz+9.6],target=target,width=1400,height=1000,fov=79,concept=False))
 vs.append(dict(id=id+'_cut',eye=[ox+20,22,oz+24],target=[ox+6,2,oz+6],width=1400,height=1000,fov=40,ortho=True,spanX=17.8,spanZ=12.7,cutY=5,bounds=[ox,oz,ox+12,oz+12],concept=False))
(D/'cameras.json').write_text(json.dumps(vs,indent=2));records=[]
for i in range(0,len(vs),2):
 p=D/f'batch{i//2}.json';p.write_text(json.dumps(vs[i:i+2]));subprocess.run([sys.executable,__file__,mode,str(p)],check=True);records+=json.loads((D/'render_report.json').read_text())
(D/'render_report.json').write_text(json.dumps(records,indent=2));print(mode,len(records))
