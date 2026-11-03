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
 assert meta.get('texture_grid_max') in [2,4,6], 'Refuse untextured fallback in final review'
 egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit
master=json.loads((R/'spec.json').read_text());ids=sys.argv[3].split(',') if len(sys.argv)>3 else ['Qilou03']+[b['id']for b in master['buildings']]
(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
for g in ids:
 src=R/(g+'.nbt');b=load_build(src,Limits(cells=12000000,nodes=16000000));sp=json.loads((R/(g+'_spec.json')).read_text());w,h,d=b.size;maxy=max(q[1]for q in b.blocks);cx=w/2;cz=d/2;cy=maxy/2
 out=ROOT/'review/previews'/(RUN+'_'+g);out.mkdir(parents=True,exist_ok=True);sha=hashlib.sha256(src.read_bytes()).hexdigest();stamp=out/'mesh_source.txt'
 valid=False
 cap=2 if g=='Qilou03'else 4
 if stamp.exists() and stamp.read_text()==sha and (out/'scene/scene.json').exists():
  meta=json.loads((out/'scene/scene.json').read_text())
  valid=meta.get('texture_grid_max')==cap and all((out/'scene'/(name+'.bin')).stat().st_size==n*3*10*4 for name,n in meta['triangles'].items())
 if not valid:
  os.environ['TOWN_TEXTURE_GRID']=str(cap);write_mesh(b,src,out/'base_scene')
  (out/'scene').mkdir(exist_ok=True);shutil.copy2(out/'base_scene/blocklight.bin',out/'scene/blocklight.bin')
  apply(b,out/'scene',src,out/'base_scene/scene.json');stamp.write_text(sha)
 views=[];base={'width':1440 if g=='Qilou03' else 1080,'height':1050 if g=='Qilou03' else 788,'concept':False,'sun_day':[.6,.9,.8]}
 def view(id,eye,target,fov=70,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
 def pair(id,eye,target,fov=70,**kw):
  view(id,eye,target,fov,**kw);views.append({**views[-1],'id':id+'_night','night':True})
 span=max((w+d)*.73+4,(maxy*.8+(w+d)*.30+4)*1440/1050)
 for name,dx,dz in [('FR',1,1),('FL',-1,1),('BL',-1,-1),('BR',1,-1)]:pair('exterior_'+name,[cx+dx*100,cy+85,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440)
 elev=max(w+4,d+3,(maxy+4)*1440/1050)
 for name,dx,dz in [('F',0,1),('R',1,0),('B',0,-1),('L',-1,0)]:view('elevation_'+name,[cx+dx*100,cy,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=elev,spanZ=elev*1050/1440)
 view('top',[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4))
 if g=='Qilou03':
  pair('street',[25,4.62,109],[112,9,109],68)
  pair('street_reverse',[220,4.62,109],[125,9,109],68)
  pair('crossroad',[108,4.62,139],[108,10,80],70)
  pair('arcade',[45,4.62,98],[94,5.1,98],72)
  pair('turn',[96,4.62,98],[96,5,87],76)
  pair('corner_NW',[104,5.62,107],[91,11,94],70)
  pair('corner_NE',[116,5.62,109],[132,12,94],70)
  pair('corner_SW',[9,5.62,109],[25,12,130],70)
  pair('corner_SE',[114,5.62,109],[130,12,130],70)
  pair('courtyard',[207,4.62,192],[226,6,184],76)
  pair('lane',[38,4.62,65],[38,12,33],70)
  pair('mixed',[100,4.62,148],[64,16,135],70)
  for key,tx,tz,span0 in [('district_south',61,145,112),('district_north',63,88,108),('district_court',150,125,105)]:
   pair(key,[tx+100,88,tz+100],[tx,16,tz],40,ortho=True,spanX=span0,spanZ=span0*1050/1440)
  for i,f in enumerate([2,9,16]):view('plan_'+str(i),[cx,260,cz],[cx,0,cz],40,ortho=True,spanX=max(w+5,(d+5)*1440/1050),spanZ=max((w+5)*1050/1440,d+5),minY=f,cutY=f+3.99)
  view('section',[cx+150,130,cz+150],[cx,20,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=108)

 else:
  fs=sp['floors'];front=[cx+9,maxy*.5,85];frontspan=max(w+8,(maxy+5)*1440/1050);pair('front',front,[cx,maxy*.5,24],40,ortho=True,spanX=frontspan,spanZ=frontspan*1050/1440)
  for i,f in enumerate(fs):view('plan_'+str(i),[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1440/1050),spanZ=max((w+4)*1050/1440,d+4),minY=f,cutY=f+3.99)
  view('section',[cx+60,45,cz+60],[cx,maxy/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,cutX=9 if g!='Teahouse' else 13)
  for i,f in enumerate(fs):
   upper=fs[i+1] if i+1<len(fs) else (fs[-1]+7 if g.startswith('V') else (15 if len(fs)==2 else 21))
   view('layer_'+str(i),[cx+60,55,cz+60],[cx,(f+upper)/2,cz],40,ortho=True,spanX=span,spanZ=span*1050/1440,minY=f,cutY=upper-.01)
  eh=maxy+6*len(fs);espan=max((w+d)*.7072+6,(eh*.8165+(w+d)*.4083+6)*1440/1050)
  view('exploded',[cx+100,eh/2+100,cz+100],[cx,eh/2,cz],40,ortho=True,spanX=espan,spanZ=espan*1050/1440,explode_floors=fs+[(fs[-1]+7) if g.startswith('V') else (15 if len(fs)==2 else 21)],explode_gap=6)
  homefloor=sp['floors'][-1];special=g in ['Teahouse','Inn','Post','Bookshop']
  cams=[('inside',[10.5 if special else 7.5,4.62,22],[10 if special else 11,4.8,15]),('service',[6,4.62,10],[11,4.8,5]),('upper',[12 if special else 6,11.62,26 if special else 23],[13 if special else 10,11.8,17])]
  if g in ['Post','Bookshop']:cams.append(('upper_back',[10,11.62,13],[12,11.7,5]))
  elif g=='Inn':cams.append(('bedroom',[9.5,11.62,12],[9.5,11.2,7]))
  else:cams.append(('bedroom',[9.5,homefloor+2.62,12],[10,homefloor+2.2,7]))
  if g.startswith('V'):
   cams=[('inside',[10.5,4.62,26],[10.5,4.8,17]),('service',[6,4.62,10],[11,4.8,5]),('upper',[6,11.62,24],[10,11.8,18]),('bedroom',[9.5,homefloor+2.62,12],[10,homefloor+2.2,7])]
  for name,eye,target in cams:pair(name,eye,target,74)
  if not g.startswith('V'):pair('arcade',[1.5,4.62,26],[w-2,5.6,26],74)
 if MODE=='draft':views=[v for v in views if v['id']in['exterior_FR','front','inside','upper','arcade','street','corner_NW','corner_NE','corner_SE','lane','mixed']]
 if MODE=='fix_exploded':views=[v for v in views if v['id']=='exploded']
 (out/f'cameras_{MODE}.json').write_text(json.dumps(views,indent=2));records=[]
 for i in range(0,len(views),3):
  batch=out/f'batch_{MODE}_{i}.json';batch.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,RUN,'batch',RUN+'_'+g,str(batch)],check=True);records+=json.loads((out/'render_report.json').read_text())
 (out/f'views_{MODE}.json').write_text(json.dumps(records,indent=2));print('DONE',g,len(records),flush=True)

 if MODE=='fix_exploded':
  old=json.loads((out/'views_full.json').read_text());replace={q['camera']['id']:q for q in records};old=[replace.get(q['camera']['id'],q)for q in old];(out/'views_full.json').write_text(json.dumps(old,indent=2))
  cams=json.loads((out/'cameras_full.json').read_text());updated={q['id']:q for q in views};cams=[updated.get(q['id'],q)for q in cams];(out/'cameras_full.json').write_text(json.dumps(cams,indent=2))
