"""Final-NBT terrain-town previews; same global coordinates, source hash and cameras."""
from pathlib import Path
import sys,json,os,subprocess,copy,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import terrain_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
run=sys.argv[1];group=sys.argv[2]if len(sys.argv)>2 else'overview';R=ROOT/'runs'/run;D=ROOT/'review/previews'/run
if group=='batch':egl.ROOT=ROOT/'review';egl.main(run,sys.argv[3]);raise SystemExit()
b=load_build(R/'Komorebi09.nbt',Limits(cells=4000000,nodes=40000000));sp=json.loads((R/'spec.json').read_text());H=np.load(R/'terrain_final.npy');views=[];bounds=None
base=dict(width=1400,height=1000,concept=False)
def v(id,eye,target,fov=76,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
if group=='overview':
 os.environ['TOWN_TEXTURE_GRID']='2'
 for name,dx,dz in[('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:
  v('day_'+name,[112+dx*210,170,92+dz*210],[112,12,92],40,ortho=True,spanX=319.2,spanZ=228)
  views.append({**views[-1],'id':'night_'+name,'night':True})
 v('top',[112,360,92],[112,0,92],40,ortho=True,spanX=268.8,spanZ=192)
 for name,dx,dz in[('south',0,1),('east',1,0),('north',0,-1),('west',-1,0)]:v('elevation_'+name,[112+dx*360,25,92+dz*360],[112,25,92],40,ortho=True,spanX=260.4,spanZ=186)
 v('valley_overview',[230,155,220],[110,15,84],50)
elif group=='walk':
 os.environ['TOWN_TEXTURE_GRID']='4'
 route={(x,z):h for x,z,h in sp['route_heights']}
 def eye(x,z):return[x+.5,route.get((x,z),int(H[x,z]))+2.62,z+.5]
 v('main_bend',eye(123,129),[98,14,110],78)
 v('hill_lane',eye(56,104),[58,27,77],78)
 v('creek_bridge',eye(123,72),[94,20,65],78)
 v('forest_edge',eye(83,48),[62,27,62],78)
 v('south_lane',eye(94,151),[128,12,140],78)
 v('bath_front',eye(190,144),[182,12,163],76)
 v('bamboo_lane',eye(81,80),[75,23,71],76)
 ch=next(t for t in sp['trees']if t['kind']=='cherry');cx,cz=ch['x'],ch['z'];v('cherry_bank',[cx+9.5,int(H[cx+9,cz-3])+2.62,cz-2.5],[cx,ch['ground']+5,cz],76)
 for name in['main_bend','creek_bridge']:views.append({**next(x for x in views if x['id']==name),'id':name+'_night','night':True})
elif group=='planting':
 os.environ['TOWN_TEXTURE_GRID']='4';bounds=[48,20,174,112]
 v('bamboo_lane',[63.5,25.62,66.5],[75,21,72],76)
 v('cherry_bank',[145.5,14.62,54.5],[151,12,75],76)
else:
 bd=next(x for x in sp['buildings']if x['id']==group);x0,_,z0,x1,_,z1=bd['bounds'];bounds=[max(0,x0-3),max(0,z0-3),min(b.size[0],x1+3),min(b.size[2],z1+3)];os.environ['TOWN_TEXTURE_GRID']='10'
 w,_,d=bd['module_size'];rot=bd['rotation']//90;ox,oy,oz=bd['origin']
 def tr(q):
  x,y,z=q
  if rot==1:x,z=d-z,x
  elif rot==2:x,z=w-x,d-z
  elif rot==3:x,z=z,w-x
  return[x+ox,y+oy,z+oz]
 if bd['family']=='machiya':v(group+'_inside',tr([11.5,4.62,19]),tr([10,4.4,12.5]),78)
 elif bd['family']=='compact':v(group+'_inside',tr([9,4.62,17.3]),tr([7.5,4.3,8]),78)
 else:v(group+'_inside',tr([w//2,4.62,d-4.2]),tr([6,4.2,7]),78)
 v(group+'_front',tr([w*.7,4.62,d+2]),tr([w*.48,5.2,d-3]),78)
 if group in['B01','B06','B15','B16']:
  if bd['family']=='machiya':v(group+'_upper',tr([9.5,9.62,15.3]),tr([15.5,8.8,18]),76)
  elif bd['family']=='compact':v(group+'_upper',tr([6.5,9.62,10]),tr([10,8.8,5.5]),76)
  else:v(group+'_detail',tr([w-6.5,4.62,9.5]),tr([5,4.1,7]),76)
  v(group+'_plan',tr([w/2,80,d/2]),tr([w/2,0,d/2]),40,ortho=True,spanX=max(w,d)*1.4,spanZ=max(w,d),minY=bd['floor_y'],cutY=bd['floor_y']+3.99)
D.mkdir(parents=True,exist_ok=True);(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
if bounds:
 x0,z0,x1,z1=bounds;b=copy.copy(b);b.blocks={q:s for q,s in b.blocks.items()if x0<=q[0]<x1 and z0<=q[2]<z1}
(D/(group+'_cameras.json')).write_text(json.dumps(views,indent=2))
if len(sys.argv)<4 or sys.argv[3]!='reuse':write_mesh(b,R/'Komorebi09.nbt',D/'scene');apply(b,D/'scene',R/'Komorebi09.nbt')
else:
 existing=json.loads((D/'scene/scene.json').read_text());assert existing['view_group']==group and existing['source_nbt_sha256']==sp['source_nbt_sha256']
meta=json.loads((D/'scene/scene.json').read_text());meta['view_group']=group;meta['geometry_crop']=bounds;(D/'scene/scene.json').write_text(json.dumps(meta,indent=2))
records=[]
batch_size=1 if group in ['walk','planting']else 3
for i in range(0,len(views),batch_size):
 f=D/f'{group}_batch{i}.json';f.write_text(json.dumps(views[i:i+batch_size]));subprocess.run([sys.executable,__file__,run,'batch',str(f)],check=True)
 records+=json.loads((D/'render_report.json').read_text())
for rec in records:rec['texture_grid_max']=int(os.environ['TOWN_TEXTURE_GRID']);rec['geometry_crop']=bounds
(D/(group+'_report.json')).write_text(json.dumps(records,indent=2))
if group=='planting':
 for name,key,replacements in [('walk_report.json','image',records),('walk_cameras.json','id',views)]:
  target=D/name
  if target.exists():
   old=json.loads(target.read_text());lookup={r[key]:r for r in replacements}
   target.write_text(json.dumps([lookup.get(r[key],r) for r in old],indent=2))
print(group,'done',len(records),flush=True)
