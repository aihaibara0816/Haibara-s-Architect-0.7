from pathlib import Path
import sys,os,json,shutil,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import qilou_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
RUN=sys.argv[1];MODE=sys.argv[2] if len(sys.argv)>2 else 'full';R=ROOT/'runs'/RUN
if MODE=='batch':
 meta=json.loads((ROOT/'review/previews'/sys.argv[3]/'scene/scene.json').read_text())
 assert meta.get('texture_grid_max') in [4,6], 'Refuse untextured fallback in final review'
 egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit
master=json.loads((R/'spec.json').read_text());ids=sys.argv[3].split(',') if len(sys.argv)>3 else ['Qilou02']+[b['id']for b in master['buildings']]
(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
for g in ids:
 src=R/(g+'.nbt');b=load_build(src,Limits(cells=2000000,nodes=6000000));sp=json.loads((R/(g+'_spec.json')).read_text());w,h,d=b.size;maxy=max(q[1]for q in b.blocks);cx=w/2;cz=d/2;cy=maxy/2
 out=ROOT/'review/previews'/(RUN+'_'+g);out.mkdir(parents=True,exist_ok=True);sha=hashlib.sha256(src.read_bytes()).hexdigest();stamp=out/'mesh_source.txt'
 valid=False
 cap=4 if g=='Qilou02'else 6
 if stamp.exists() and stamp.read_text()==sha and (out/'scene/scene.json').exists():
  meta=json.loads((out/'scene/scene.json').read_text())
  valid=meta.get('texture_grid_max')==cap and all((out/'scene'/(name+'.bin')).stat().st_size==n*3*10*4 for name,n in meta['triangles'].items())
 if not valid:
  os.environ['TOWN_TEXTURE_GRID']=str(cap);write_mesh(b,src,out/'base_scene')
  (out/'scene').mkdir(exist_ok=True);shutil.copy2(out/'base_scene/blocklight.bin',out/'scene/blocklight.bin')
  apply(b,out/'scene',src,out/'base_scene/scene.json');stamp.write_text(sha)
 views=[];base={'width':1440,'height':1050,'concept':False,'sun_day':[.6,.9,.8]}
 def view(id,eye,target,fov=70,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
 def pair(id,eye,target,fov=70,**kw):
  view(id,eye,target,fov,**kw);views.append({**views[-1],'id':id+'_night','night':True})
 span=max((w+d)*.73+4,(maxy*.8+(w+d)*.30+4)*1440/1050)
 for name,dx,dz in [('FR',1,1),('FL',-1,1),('BL',-1,-1),('BR',1,-1)]:pair('exterior_'+name,[cx+dx*100,cy+85,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440)
 elev=max(w+4,d+3,(maxy+4)*1440/1050)
 for name,dx,dz in [('F',0,1),('R',1,0),('B',0,-1),('L',-1,0)]:view('elevation_'+name,[cx+dx*100,cy,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=elev,spanZ=elev*1050/1440)
 view('top',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4))
 if g=='Qilou02':
  pair('street',[76,5.62,130],[76,12,109],70)
  pair('arcade',[59,4.62,111],[104,5.1,111],72)
  pair('turn',[112,4.62,109],[112,5.1,94],74)
  pair('corner_SE',[129,6.62,129],[102,12,103],70)
  pair('corner_SW',[12,6.62,130],[37,12,103],70)
  pair('corner_NE',[130,6.62,13],[103,10,40],70)
  pair('corner_NW',[12,6.62,13],[40,10,40],70)
  pair('courtyard',[70,4.62,75],[82,6,82],78)
  pair('lane',[71,4.62,116],[71,5,75],72)
  for key,tx,tz in [('district_south',72,102),('district_north',72,40),('district_court',71,71)]:
   pair(key,[tx+100,85,tz+100],[tx,11,tz],40,ortho=True,spanX=90,spanZ=90*1050/1440)
  for i,f in enumerate([2,9,15]):view('plan_'+str(i),[cx,180,cz],[cx,0,cz],40,ortho=True,spanX=151*1440/1050,spanZ=151,minY=f,cutY=f+3.99)
  view('section',[cx+150,110,cz+150],[cx,13,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=72)
 else:
  fs=sp['floors'];front=[cx+5,11,51];pair('front',front,[cx,13,26],65)
  for i,f in enumerate(fs):view('plan_'+str(i),[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4),minY=f,cutY=f+3.99)
  view('section',[cx+60,45,cz+60],[cx,maxy/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=9 if g!='Teahouse' else 13)
  for i,f in enumerate(fs):
   upper=fs[i+1] if i+1<len(fs) else(15 if len(fs)==2 else 21)
   view('layer_'+str(i),[cx+60,55,cz+60],[cx,(f+upper)/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,minY=f,cutY=upper-.01)
  view('exploded',[cx+100,105,cz+100],[cx,(maxy+6*len(fs))/2,cz],40,ortho=True,spanX=span+15,spanZ=(span+15)*1050/1440,explode_floors=fs+[15 if len(fs)==2 else 21],explode_gap=6)
  homefloor=sp['floors'][-1];special=g in ['Teahouse','Inn','Post','Bookshop']
  cams=[('inside',[10.5 if special else 7.5,4.62,22],[10 if special else 11,4.8,15]),('service',[6,4.62,10],[11,4.8,5]),('upper',[12 if special else 6,11.62,26 if special else 23],[13 if special else 10,11.8,17])]
  if g in ['Post','Bookshop']:cams.append(('upper_back',[10,11.62,13],[12,11.7,5]))
  elif g=='Inn':cams.append(('bedroom',[9.5,11.62,12],[9.5,11.2,7]))
  else:cams.append(('bedroom',[9.5,homefloor+2.62,12],[10,homefloor+2.2,7]))
  for name,eye,target in cams:pair(name,eye,target,74)
  pair('arcade',[1.5,4.62,26],[w-2,5.6,26],74)
 if MODE=='draft':views=[v for v in views if v['id']in['exterior_FR','front','inside','upper','arcade','street','corner_SE','courtyard','lane']]
 (out/f'cameras_{MODE}.json').write_text(json.dumps(views,indent=2));records=[]
 for i in range(0,len(views),3):
  batch=out/f'batch_{MODE}_{i}.json';batch.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,RUN,'batch',RUN+'_'+g,str(batch)],check=True);records+=json.loads((out/'render_report.json').read_text())
 (out/f'views_{MODE}.json').write_text(json.dumps(records,indent=2));print('DONE',g,len(records),flush=True)
