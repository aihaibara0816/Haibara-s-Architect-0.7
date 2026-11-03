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
b=load_build(R/'Machiya08.nbt',Limits(cells=2_000_000,nodes=6_000_000));write_mesh(b,R/'Machiya08.nbt',D/'scene');apply(b,D/'scene',R/'Machiya08.nbt');vs=[]
for name,dx,dz in [('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:
 v=dict(id='exterior_'+name,eye=[17+dx*42,40,16+dz*42],target=[17,9,16],fov=40,ortho=True,spanX=53.2,spanZ=38)
 vs.append(v);vs.append({**v,'id':'night_'+name,'night':True})
for name,dx,dz in [('south',0,1),('east',1,0),('north',0,-1),('west',-1,0)]:vs.append(dict(id='elevation_'+name,eye=[15.5+dx*60,10,15.5+dz*60],target=[15.5,10,15.5],fov=40,ortho=True,spanX=39.2,spanZ=28))
vs.append(dict(id='top',eye=[17,70,17],target=[17,0,17],fov=40,ortho=True,spanX=47.6,spanZ=34))
for i,f in enumerate([2,7],1):vs.append(dict(id='plan_'+str(i),eye=[15.5,60,15],target=[15.5,0,15],fov=40,ortho=True,spanX=26.6,spanZ=19,minY=f,cutY=f+3.99,bounds=[7,7,24,23]))
vs.append(dict(id='section',eye=[65,10,15],target=[15,10,15],fov=40,ortho=True,spanX=35,spanZ=25,cutX=19.99,bounds=[5,5,26,26]))
for id,eye,target,fov in [('front_eye',[18.5,4.62,27],[16,4.9,22],76),('entry_eye',[16.5,4.62,21],[16,4.4,14.7],78),('bar_eye',[20.5,4.62,18.5],[15,4.2,14],76),('dining_eye',[18,4.62,20.8],[10,4,19],78),('kitchen_eye',[17.5,4.62,12],[15.5,4.3,8.5],78),('bath_eye',[21.5,4.62,11.4],[20.6,3.9,9],80),('bedroom_eye',[17.5,9.62,14],[17.4,8.9,9.8],76),('tea_eye',[14.5,9.62,17.3],[20.5,8.8,20],76),('study_eye',[12.3,9.62,20.3],[8.8,8.9,19.5],78),('garden_eye',[16.8,4.62,5.7],[10,4.2,3.5],78),('stairs_eye',[9.5,4.62,16.3],[8.8,5.5,12.3],75),('eave_detail',[25.5,9.5,27],[22,11.5,23],72)]:vs.append(dict(id=id,eye=eye,target=target,fov=fov))
for id,eye,target in [('booth_eye',[14.2,4.62,20],[9.3,4.5,19.5]),('stock_eye',[10.5,4.62,11.5],[12,4.4,10.5]),('service_eye',[20.4,4.62,17.5],[21,4.2,13])]:vs.append(dict(id=id,eye=eye,target=target,fov=76))
for id,eye,target,fov in [('understair_eye',[11.4,4.62,16.5],[11.9,4.5,13],78),('understair_detail',[10.5,4.62,16],[12.4,4.4,14],72)]:vs.append(dict(id=id,eye=eye,target=target,fov=fov))
vs.append(dict(id='understair_section',eye=[2,5.5,14],target=[12,5.5,14],fov=40,ortho=True,spanX=10.5,spanZ=7.5,bounds=[10.9,11,13,17],cutY=8))
for name in ['front_eye','entry_eye','tea_eye']:
 v=next(v for v in vs if v['id']==name);vs.append({**v,'id':name+'_night','night':True})
for v in vs:v.update(width=1400,height=1000,concept=False)
(D/'cameras.json').write_text(json.dumps(vs,indent=2));records=[]
for i in range(0,len(vs),3):
 p=D/f'batch{i}.json';p.write_text(json.dumps(vs[i:i+3]));subprocess.run([sys.executable,__file__,run,str(p)],check=True);records+=json.loads((D/'render_report.json').read_text())
(D/'render_report.json').write_text(json.dumps(records,indent=2))
