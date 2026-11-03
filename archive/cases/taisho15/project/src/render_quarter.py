from pathlib import Path
import sys,json,os,shutil,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import taisho_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
RUN=sys.argv[1];MODE=sys.argv[2]if len(sys.argv)>2 else'draft';R=ROOT/'runs'/RUN
if MODE=='batch':egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit()
sp=json.loads((R/'spec.json').read_text());ids=['Taisho15']+[b['id']for b in sp['buildings']]
if len(sys.argv)>3:ids=sys.argv[3].split(',')
if MODE=='draft'and len(sys.argv)<4:ids=['Taisho15','School','Clock','Residence','Library']
catalog=[]
for group in ids:
 src=R/(group+'.nbt');b=load_build(src,Limits(cells=4000000,nodes=20000000));w,h,d=b.size;label=RUN+'_'+group;out=ROOT/'review/previews'/label;out.mkdir(parents=True,exist_ok=True)
 views=[];base={'width':1400,'height':1000,'concept':False}
 def v(id,eye,target,fov=70,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'fov':fov,**kw})
 def paired(id,eye,target,fov=70,**kw):
  v(id,eye,target,fov,**kw);views.append({**views[-1],'id':id+'_night','night':True})
 if group=='Taisho15':
  center=[w/2,18,d/2]
  hm=json.loads((R/'heightmap.json').read_text())
  for name,dx,dz in[('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:paired('overview_'+name,[w/2+dx*280,245,d/2+dz*280],center,40,ortho=True,spanX=335,spanZ=335/1.4)
  paired('hero',[270,100,248],[105,17,102],62)
  def near(id,dist=10):
   q=next(b for b in sp['buildings']if b['id']==id);ex,ey,ez=q['entry_world'];r=q['rotation']//90;dx,dz=[(0,1),(-1,0),(0,-1),(1,0)][r];x,z=round(ex+dx*dist),round(ez+dz*dist);return [x+.5,hm[z][x]+2.62,z+.5],[ex,ey+5,ez]
  for key,bid in [('clock_square','Clock'),('station_front','Station'),('school_court','School'),('upper_street','Bookshop'),('lower_street','Residence'),('side_lane','Photo')]:
   ey,ta=near(bid,12)
   if bid=='Clock':ey,ta=[181,10.62,164],[163,20,130]
   paired(key,ey,ta,76)
  paired('bridge_arrival',[215,7.62,98],[157,14,100],76)
  lp=sp['terrain']['lookout']['point'];paired('slope_west',[lp[0]+1,lp[1]+1.62,lp[2]+4.4],[145,12,126],85)
  for name,cx,cz,span in[('west',42,103,130),('school',119,54,132),('station',158,142,140)]:
   for dir,dx,dz in[('SE',1,1),('SW',-1,1),('NW',-1,-1),('NE',1,-1)]:paired('district_'+name+'_'+dir,[cx+dx*110,105,cz+dz*110],[cx,14,cz],40,ortho=True,spanX=span,spanZ=span/1.4)
  for name,cx,cz,span,cy in[('mountain',32,27,100,29),('river',194,107,90,7),('yard',69,163,83,12)]:
   paired(name,[cx+90,cy+85,cz+90],[cx,cy,cz],40,ortho=True,spanX=span,spanZ=span/1.4)
  v('top',[w/2,400,d/2],[w/2,0,d/2],40,ortho=True,spanX=max(w+10,(d+10)*1.4),spanZ=max((w+10)/1.4,d+10))
  for dir,dx,dz in[('S',0,1),('E',1,0),('N',0,-1),('W',-1,0)]:v('elevation_'+dir,[w/2+dx*350,28,d/2+dz*350],[w/2,28,d/2],40,ortho=True,spanX=265,spanZ=265/1.4)
  v('section',[290,160,240],[120,17,100],40,ortho=True,spanX=285,spanZ=285/1.4,cutX=120)
  if MODE=='focus':views=[q for q in views if q['id']in['slope_west','slope_west_night']]
  if MODE=='draft':views=[q for q in views if q['id']in['hero','clock_square','overview_SE','mountain','river','yard','district_west_SE']]
 else:
  bd=next(q for q in sp['buildings']if q['id']==group);maxy=max(q[1]for q in b.blocks);cx=w/2;cz=d/2;cy=maxy/2+1;span=max((w+d)*.74+5,(maxy*.8+(w+d)*.31+4)*1.4)
  for dir,dx,dz in[('FR',1,1),('FL',-1,1),('BL',-1,-1),('BR',1,-1)]:paired('exterior_'+dir,[cx+dx*100,cy+100,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=span,spanZ=span/1.4)
  elevspan=max(w+6,d+6,(maxy+5)*1.4)
  for dir,dx,dz in[('F',0,1),('R',1,0),('B',0,-1),('L',-1,0)]:v('elevation_'+dir,[cx+dx*100,cy,cz+dz*100],[cx,cy,cz],40,ortho=True,spanX=elevspan,spanZ=elevspan/1.4)
  paired('front',[cx+min(9,w/3),max(8,maxy*.42),d+14],[cx,maxy*.45,d-7],65)
  for idx,f in enumerate(bd['floors']):v('plan_'+str(idx),[cx,150,cz],[cx,0,cz],40,ortho=True,spanX=max(w+4,(d+4)*1.4),spanZ=max((w+4)/1.4,d+4),minY=f,cutY=f+3.99)
  for name,lo,hi in[('ground',2,7.99),('roof',max(bd['floors'])+6,h)]:v('layer_'+name,[cx+45,55,cz+45],[cx,(lo+hi)/2,cz],40,ortho=True,spanX=span,spanZ=span/1.4,minY=lo,cutY=hi)
  v('section',[cx+50,45,cz+60],[cx,maxy/2,cz],40,ortho=True,spanX=span,spanZ=span/1.4,cutX=cx+.6)
  cameras={
   'Bookshop':([13.5,4.62,25],[14,4.7,17]),'Pharmacy':([22,4.62,24],[15,4.4,19]),'Inn':([22,4.62,27],[28,4.5,23]),'Tea':([10,4.62,17],[7,4.5,9]),'Photo':([13,4.62,18],[10,4.5,11]),'Post':([12,4.62,19],[11,4.5,13]),
   'School':([17.5,4.62,27],[17,5,8]),'Library':([13.5,4.62,23],[14,4.7,8]),'Clinic':([14,4.62,21],[13,4.8,9]),'Textile':([10,4.62,19],[10,4.5,8]),'Residence':([13,4.62,21],[12,4.5,8]),'Bakery':([10,4.62,17],[8,4.5,10]),'Florist':([8,4.62,15],[8,4.8,5]),'Sake':([10,4.62,18],[10,4.5,7]),'Workshop':([13,4.62,20],[12,4.8,9]),'Bath':([20.5,4.62,12],[10,4.3,7]),'Clock':([10,4.62,11],[6,4.7,6]),'Station':([18,4.62,28],[13,4.8,18])}
  eye,target=cameras[group];paired('inside',eye,target,76)
  if len(bd['floors'])>1:
   upper={'Bookshop':([15,10.62,20],[11,10.1,25]),'Inn':([16,10.62,20],[13,10.1,12]),'Pharmacy':([16,10.62,24],[21,10.5,13]),'Photo':([14,10.62,18],[14,10.1,6]),'Post':([14,10.62,17],[10,10.5,15]),'Clinic':([14,10.62,20],[14,10.4,8])}
   ey,ta=upper.get(group,([w/2,10.62,d-8],[w/2,10.5,8]));paired('upper_inside',ey,ta,76)
  if group=='Station':paired('platform',[18,4.62,6],[5,5,10],76)
  if MODE=='draft':views=[q for q in views if q['id']in['exterior_FR','front','inside']]
 (ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
 sha=hashlib.sha256(src.read_bytes()).hexdigest();stamp=out/'mesh_source.txt'
 if not stamp.exists()or stamp.read_text()!=sha:
  os.environ['TOWN_TEXTURE_GRID']='3'if group=='Taisho15'else'4';write_mesh(b,src,out/'scene');apply(b,out/'scene',src);stamp.write_text(sha)
 (out/('cameras_'+MODE+'.json')).write_text(json.dumps(views,indent=2));records=[]
 for i in range(0,len(views),3):
  f=out/f'batch_{MODE}{i}.json';f.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,RUN,'batch',label,str(f)],check=True);records+=json.loads((out/'render_report.json').read_text())
 (out/('views_'+MODE+'.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2));catalog.append({'id':group,'source_nbt_sha256':sha,'views':records});print('GROUP',group,len(records),flush=True)
(ROOT/'review'/('catalog_'+RUN+'_'+MODE+'.json')).write_text(json.dumps(catalog,ensure_ascii=False,indent=2));print('RENDER DONE',RUN,MODE,sum(len(q['views'])for q in catalog),flush=True)
