from pathlib import Path
import sys,json,os,subprocess,copy
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import town_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
run=sys.argv[1];group=sys.argv[2]if len(sys.argv)>2 else'overview';R=ROOT/'runs'/run;D=ROOT/'review/previews'/run
if group=='batch':
 egl.ROOT=ROOT/'review';egl.main(run,sys.argv[3]);raise SystemExit()
b=load_build(R/'Komorebi09.nbt',Limits(cells=1000000,nodes=8000000));sp=json.loads((R/'spec.json').read_text());views=[];bounds=None
base=dict(width=1400,height=1000,concept=False)
def v(id,eye,target,fov=76,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
if group=='overview':
 os.environ['TOWN_TEXTURE_GRID']='3'
 for name,dx,dz in [('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:
  v('day_'+name,[82+dx*144,120,56+dz*144],[82,7,56],40,ortho=True,spanX=225.4,spanZ=161)
  views.append({**views[-1],'id':'night_'+name,'night':True})
 v('top',[82,230,56],[82,0,56],40,ortho=True,spanX=182,spanZ=130)
 for name,dx,dz in [('south',0,1),('east',1,0),('north',0,-1),('west',-1,0)]:v('elevation_'+name,[82+dx*250,10,56+dz*250],[82,10,56],40,ortho=True,spanX=189,spanZ=135)
 for floor in [2,7]:v('plan_'+str(floor),[82,230,56],[82,0,56],40,ortho=True,spanX=182,spanZ=130,minY=floor,cutY=floor+3.99)
 v('section',[82,60,230],[82,5,56],40,ortho=True,spanX=189,spanZ=135,cutZ=60,bounds=[2,44,138,73],cutY=20)
 v('creek_overview',[177,48,121],[125,4,68],58)
elif group=='streets':
 os.environ['TOWN_TEXTURE_GRID']='4'
 for id,eye,target in [('main_west',[14,4.62,42],[55,5,40]),('main_east',[132,4.62,41],[90,5.2,41]),('cross_alley',[67.5,4.62,65],[67.5,5,38]),('quiet_lane',[71,4.62,76],[117,5,77]),('green_pocket',[35,4.62,71],[57,4.5,71]),('creek_bank',[160,4.62,65],[126,5,81]),('creek_walk',[141.5,4.62,98],[148,5,48]),('wood_bridge',[150,4.62,77],[121,5,77])]:v(id,eye,target,78)
 for name in ['main_west','creek_bank','quiet_lane']:
  vv=next(x for x in views if x['id']==name);views.append({**vv,'id':name+'_night','night':True})
elif group=='creek':
 os.environ['TOWN_TEXTURE_GRID']='12';bounds=[115,0,164,112]
 v('creek_bend',[150,4.62,41],[146,4.1,68],78)
 v('creek_cherry',[159,4.62,81],[140,5,68],78)
 v('grass_flowers',[138,4.62,100],[143,3.4,103],76)
 vv=views[0];views.append({**vv,'id':'creek_bend_night','night':True})
else:
 bd=next(x for x in sp['buildings']if x['id']==group);x0,_,z0,x1,_,z1=bd['bounds'];bounds=[max(0,x0-2),max(0,z0-2),min(b.size[0],x1+2),min(b.size[2],z1+2)];os.environ['TOWN_TEXTURE_GRID']='12'
 w,_,d=bd['module_size'];rot=bd['rotation']
 def tr(q):
  x,y,z=q
  if rot==180:x,z=w-x,d-z
  return[x+x0,y,z+z0]
 if bd['family']=='machiya':
  v(group+'_inside',tr([11.5,4.62,19]),tr([10,4.4,12.5]),78)
  v(group+'_upper',tr([9.5,9.62,15.3]),tr([15.5,8.8,18]),76)
 elif bd['family']=='compact':
  v(group+'_inside',tr([9,4.62,17.3]),tr([7.5,4.3,8]),78)
  v(group+'_upper',tr([6.5,9.62,10]),tr([10,8.8,5.5]),76)
 else:
  v(group+'_inside',tr([w//2,4.62,d-4.2]),tr([6,4.2,7]),78)
  v(group+'_detail',tr([w-6.5,4.62,9.5]),tr([5,4.1,7]),76)
 v(group+'_front',tr([w*.7,4.62,d+1]),tr([w*.48,5.2,d-3]),78)
 v(group+'_plan',tr([w/2,60,d/2]),tr([w/2,0,d/2]),40,ortho=True,spanX=max(w,d)*1.4,spanZ=max(w,d),minY=2,cutY=5.99)
# Mesh cache belongs to its view group; cropped detail geometry is read directly from final NBT.
D.mkdir(parents=True,exist_ok=True);(ROOT/'review/assets').mkdir(parents=True,exist_ok=True)
import shutil
shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
if bounds:
 x0,z0,x1,z1=bounds;b=copy.copy(b);b.blocks={q:s for q,s in b.blocks.items()if x0<=q[0]<x1 and z0<=q[2]<z1}
write_mesh(b,R/'Komorebi09.nbt',D/'scene');apply(b,D/'scene',R/'Komorebi09.nbt')
meta=json.loads((D/'scene/scene.json').read_text());meta['view_group']=group;meta['geometry_crop']=bounds;(D/'scene/scene.json').write_text(json.dumps(meta,indent=2))
records=[]
for i in range(0,len(views),3):
 f=D/f'{group}_batch{i}.json';f.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,run,'batch',str(f)],check=True)
 records+=json.loads((D/'render_report.json').read_text())
for rec in records:rec['texture_grid_max']=int(os.environ['TOWN_TEXTURE_GRID']);rec['geometry_crop']=bounds
(D/(group+'_report.json')).write_text(json.dumps(records,indent=2));print(group,'done',len(records),flush=True)
