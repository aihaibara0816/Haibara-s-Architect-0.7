from pathlib import Path
import sys,os,json,shutil,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import qilou_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
RUN=sys.argv[1];MODE=sys.argv[2] if len(sys.argv)>2 else 'full';R=ROOT/'runs'/RUN
if MODE=='batch':egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit
ids=sys.argv[3].split(',') if len(sys.argv)>3 else ['Qilou01','Grocery','Apothecary','Teahouse']
(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
for g in ids:
 src=R/(g+'.nbt');b=load_build(src,Limits(cells=2000000,nodes=6000000));sp=json.loads((R/(g+'_spec.json')).read_text());w,h,d=b.size;maxy=max(q[1]for q in b.blocks);cx=w/2;cz=d/2;cy=maxy/2
 out=ROOT/'review/previews'/(RUN+'_'+g);out.mkdir(parents=True,exist_ok=True);sha=hashlib.sha256(src.read_bytes()).hexdigest();stamp=out/'mesh_source.txt'
 valid=False
 if stamp.exists() and stamp.read_text()==sha and (out/'scene/scene.json').exists():
  meta=json.loads((out/'scene/scene.json').read_text())
  valid=meta.get('texture_grid_max')==8 and all((out/'scene'/(name+'.bin')).stat().st_size==n*3*10*4 for name,n in meta['triangles'].items())
 if not valid:
  os.environ['TOWN_TEXTURE_GRID']='8';write_mesh(b,src,out/'scene');apply(b,out/'scene',src);stamp.write_text(sha)
 views=[];base={'width':1440,'height':1050,'concept':False,'sun_day':[.6,.9,.8]}
 def view(id,eye,target,fov=70,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
 def pair(id,eye,target,fov=70,**kw):
  view(id,eye,target,fov,**kw);views.append({**views[-1],'id':id+'_night','night':True})
 span=max((w+d)*.73+4,(maxy*.8+(w+d)*.30+4)*1440/1050)
 for name,dx,dz in [('FR',1,1),('FL',-1,1),('BL',-1,-1),('BR',1,-1)]:pair('exterior_'+name,[cx+dx*100,cy+85,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440)
 elev=max(w+4,d+3,(maxy+4)*1440/1050)
 for name,dx,dz in [('F',0,1),('R',1,0),('B',0,-1),('L',-1,0)]:view('elevation_'+name,[cx+dx*100,cy,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=elev,spanZ=elev*1050/1440)
 view('top',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4))
 if g=='Qilou01':
  pair('street',[61,7.62,53],[34,12,32],66)
  pair('arcade',[11,4.62,32],[51,5.2,32],72)
  pair('corner',[70,6.62,41],[54,13,26],72)
  view('ground_plan',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=82,spanZ=82*1050/1440,cutY=6.99)
  view('section',[cx+90,75,cz+90],[cx,12,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=49)
 else:
  fs=sp['floors'];front=[cx+5,11,51];pair('front',front,[cx,13,26],65)
  for i,f in enumerate(fs):view('plan_'+str(i),[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4),minY=f,cutY=f+3.99)
  view('section',[cx+60,45,cz+60],[cx,maxy/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=9 if g!='Teahouse' else 13)
  for i,f in enumerate(fs):
   upper=fs[i+1] if i+1<len(fs) else(15 if len(fs)==2 else 21)
   view('layer_'+str(i),[cx+60,55,cz+60],[cx,(f+upper)/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,minY=f,cutY=upper-.01)
  view('exploded',[cx+100,105,cz+100],[cx,(maxy+6*len(fs))/2,cz],40,ortho=True,spanX=span+15,spanZ=(span+15)*1050/1440,explode_floors=fs+[15 if len(fs)==2 else 21],explode_gap=6)
  cams={
   'Grocery': [('inside',[7.5,4.62,22],[9,4.7,16]),('service',[6,4.62,12],[10,4.6,6]),('upper',[6,11.62,20],[10,11.8,25]),('bedroom',[9.5,11.62,12],[10,11.2,7])],
   'Apothecary':[('inside',[8,4.62,22],[10,5,13]),('service',[6,4.62,14],[12,5.2,10]),('upper',[5,11.62,23],[10,11.8,17]),('bedroom',[9.5,17.62,12],[10,17.2,7])],
   'Teahouse':[('inside',[10.5,4.62,22],[9,4.7,15]),('service',[6,4.62,10],[12,4.9,5]),('upper',[12,11.62,26],[14,11.6,17]),('bedroom',[6,17.62,21],[13,17.7,24])]
  }
  for name,eye,target in cams[g]:pair(name,eye,target,74)
  pair('arcade',[1.5,4.62,26],[w-2,5.6,26],74)
 if MODE=='draft':views=[v for v in views if v['id']in['exterior_FR','front','inside','upper','arcade','street','corner']]
 (out/f'cameras_{MODE}.json').write_text(json.dumps(views,indent=2));records=[]
 for i in range(0,len(views),3):
  batch=out/f'batch_{MODE}_{i}.json';batch.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,RUN,'batch',RUN+'_'+g,str(batch)],check=True);records+=json.loads((out/'render_report.json').read_text())
 (out/f'views_{MODE}.json').write_text(json.dumps(records,indent=2));print('DONE',g,len(records),flush=True)
