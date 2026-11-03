from pathlib import Path
import sys,json,os,shutil,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import taisho_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
run=sys.argv[1];group=sys.argv[2];R=ROOT/'runs'/run;label=run+'_'+group;D=ROOT/'review/previews'/label
if group=='batch':egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit()
file=R/(group+'.nbt');b=load_build(file,Limits(cells=1000000,nodes=8000000));w,h,d=b.size;views=[]
base={'width':1200,'height':900,'concept':False}
def v(id,eye,target,fov=74,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
cx,cz=w/2,d/2;isworld=group=='Taisho12';span=max(w,d)*1.22;os.environ['TOWN_TEXTURE_GRID']='3'if isworld else'7';dist=max(w,d)*2
for name,dx,dz in[('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:
 v('day_'+name,[cx+dx*dist,dist*.8,cz+dz*dist],[cx,8,cz],40,ortho=True,spanX=span*1.3333,spanZ=span)
 views.append({**views[-1],'id':'night_'+name,'night':True})
v('top',[cx,200,cz],[cx,0,cz],40,ortho=True,spanX=max(w,d)*1.3333,spanZ=max(w,d))
if not isworld:
 for name,dx,dz in[('south',0,1),('east',1,0),('north',0,-1),('west',-1,0)]:v('elevation_'+name,[cx+dx*dist,8,cz+dz*dist],[cx,8,cz],40,ortho=True,spanX=span*1.3333,spanZ=span)
 v('plan_ground',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=span*1.3333,spanZ=span,minY=2,cutY=5.99)
 # Exact geometric cut plane, not a newly imagined room.
 v('section',[w+30,27,d+30],[cx,8,cz],40,ortho=True,spanX=span*1.3333,spanZ=span,cutX=cx)
if not isworld:
 v('plan_upper',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=span*1.3333,spanZ=span,minY=8,cutY=11.99)
 for title,lo,hi in [('ground',0,7.99),('upper',8,13.99),('roof',14,28)]:v('layer_'+title,[cx+40,40,cz+50],[cx,(lo+hi)/2,cz],40,ortho=True,spanX=span*1.3333,spanZ=span,minY=lo,cutY=hi)
cam={
'Bookshop':[
 ('front',[24,4.62,35],[13,10,27]),('entry',[13,4.62,31],[13,4.6,23]),('browse',[13.5,4.62,25],[14,4.7,17]),('counter',[18,4.62,14],[16,4.5,8]),('work',[18,10.62,20],[12,10.3,16]),('reading',[15,10.62,20],[11,10.1,25]),('bed',[20,10.62,12],[18,10.2,9])],
'Pharmacy':[
 ('front',[34,4.62,35],[24,10,25]),('entry',[29,4.62,30],[23,4.5,23]),('display',[22,4.62,24],[15,4.4,19]),('counter',[18,4.62,15],[20,4.6,8]),('office',[16,10.62,25],[12,10.3,20]),('stock',[22,10.62,15],[23,10.6,8]),('bed',[25,10.62,26],[23,10.2,22])],
'Inn':[
 ('front',[34,4.62,39],[19,10,29]),('entry',[18,4.62,37],[18,5,29]),('lounge',[16,4.62,26],[11,4.2,23]),('reception',[22,4.62,27],[28,4.5,23]),('kitchen',[30,4.62,15],[27,4.5,9]),('bath',[15,4.62,15],[12,4.2,10]),('guest',[16,10.62,20],[13,10.1,12]),('guest_east',[28,10.62,20],[25,10.2,12]),('hall',[20,10.62,25],[12,10.1,26]),('balcony',[18,10.62,31],[28,11,31])],
'Taisho12':[('street',[53,4.62,47],[79,10,33]),('street_west',[29,4.62,46],[15,10,32])]
}
for name,eye,target in cam[group]:v(name,eye,target,78)
D.mkdir(parents=True,exist_ok=True);(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
(D/'cameras.json').write_text(json.dumps(views,indent=2));write_mesh(b,file,D/'scene');apply(b,D/'scene',file)
records=[]
for i in range(0,len(views),2):
 f=D/f'batch{i}.json';f.write_text(json.dumps(views[i:i+2]));subprocess.run([sys.executable,__file__,run,'batch',label,str(f)],check=True);records+=json.loads((D/'render_report.json').read_text())
(D/'all_views.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(group,'completed',len(records),flush=True)
