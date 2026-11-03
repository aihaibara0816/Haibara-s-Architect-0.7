from pathlib import Path
import sys,os,json,hashlib,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import qilou_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
import render_egl_site as egl
RUN=sys.argv[1];MODE=sys.argv[2]if len(sys.argv)>2 else'full';R=ROOT/'runs'/RUN
if MODE=='batch':
 egl.ROOT=ROOT/'review';egl.main(sys.argv[3],sys.argv[4]);raise SystemExit
master=json.loads((R/'spec.json').read_text());ids=sys.argv[3].split(',')if len(sys.argv)>3 else['Qilou04']+[b['id']for b in master['buildings']]
(ROOT/'review/assets').mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/'assets/render_shader_reference.html',ROOT/'review/assets/render_shader_reference.html')
for id in ids:
 src=R/(id+'.nbt');b=load_build(src,Limits(cells=12_000_000,nodes=20_000_000));sp=json.loads((R/(id+'_spec.json')).read_text());w,h,d=b.size;maxy=max(q[1]for q in b.blocks);cx=w/2;cz=d/2;cy=maxy/2
 out=ROOT/'review/previews'/(RUN+'_'+id);out.mkdir(parents=True,exist_ok=True);sha=hashlib.sha256(src.read_bytes()).hexdigest();stamp=out/'mesh_source.txt';cap=1 if id=='Qilou04'else 2
 if not(stamp.exists()and stamp.read_text()==sha+'|alpha-v1' and (out/'scene/scene.json').exists()):
  os.environ['TOWN_TEXTURE_GRID']=str(cap);write_mesh(b,src,out/'base_scene');(out/'scene').mkdir(exist_ok=True);shutil.copy2(out/'base_scene/blocklight.bin',out/'scene/blocklight.bin');apply(b,out/'scene',src,out/'base_scene/scene.json');stamp.write_text(sha+'|alpha-v1')
 print('mesh',id,flush=True)
 if MODE=='mesh':continue
 base=dict(width=1600 if id=='Qilou04'else 1000,height=1120 if id=='Qilou04'else 760,concept=False,sun_day=[.6,.9,.8]);views=[];ratio=base['height']/base['width']
 def v(name,eye,target,span=None,**kw):
  a=dict(base,id=name,eye=eye,target=target,fov=72,**kw)
  if span:a.update(ortho=True,spanX=span,spanZ=span*ratio)
  views.append(a)
 def pair(name,eye,target,span=None,**kw):v(name,eye,target,span,**kw);views.append(dict(views[-1],id=name+'_night',night=True))
 span=max((w+d)*.76,(maxy*.82+(w+d)*.33+5)/ratio)
 if id=='Qilou04':
  for name,dx,dz in [('SE',1,1),('SW',-1,1),('NE',1,-1),('NW',-1,-1)]:pair('overall_'+name,[cx+180*dx,cy+156,cz+180*dz],[cx,cy-3,cz],span)
  v('top',[cx,350,cz],[cx,0,cz],max(w+8,(d+8)/ratio))
  pair('street_west',[43,4.62,132],[170,11,132]);pair('street_east',[205,4.62,132],[108,12,132])
  pair('plaza',[217,5.62,127],[189,11,100]);pair('village_entry',[219,4.62,155],[253,11,168])
  pair('lane',[108,4.62,84],[108,13,42]);pair('across_road',[229,5.62,133],[297,16,165])
  pair('arcade',[91,4.62,119],[130,5.7,119])
  pair('region_west',[65,70,230],[105,16,132],200)
  pair('region_plaza',[250,84,180],[179,15,106],141)
  pair('region_east',[390,105,250],[289,20,155],190)
  v('ground_cut',[cx,350,cz],[cx,0,cz],max(w+8,(d+8)/ratio),cutY=5.99)
  v('section',[cx+150,130,cz+150],[cx,18,cz],span,cutX=218)
  for name,dx,dz in [('south',0,1),('east',1,0),('north',0,-1),('west',-1,0)]:v('elevation_'+name,[cx+200*dx,cy,cz+200*dz],[cx,cy,cz],max(w+8,d+8,(maxy+8)/ratio))
 else:
  # Front follows the actual house orientation. Urban NBTs already carry global rotation.
  rot=sp.get('urban',{}).get('rotation',0);dx,dz=[(0,-1),(1,0),(0,1),(-1,0)][rot]if sp['family']=='village'else(0,1)
  pair('front',[cx+dx*80+(15 if dx==0 else 0),cy+9,cz+dz*80+(15 if dz==0 else 0)],[cx,cy,cz],max(w+d+6,(maxy+8)/ratio))
  v('plan',[cx,150,cz],[cx,0,cz],max(w+4,(d+4)/ratio),minY=2,cutY=5.99)
  if id in ['N03','N08','S03','A1','A2','B3','D5','E4']:
   v('section',[cx+100,cy+60,cz+100],[cx,cy,cz],span,cutX=w//2)
   fs=sp['floors'];eh=maxy+6*len(fs);espan=max((w+d)*.7072+6,(eh*.8165+(w+d)*.4083+6)/ratio)
   v('exploded',[cx+100,eh/2+100,cz+100],[cx,eh/2,cz],espan,explode_floors=fs+[fs[-1]+(5 if sp['family']=='village'else 6)],explode_gap=6)
   if sp['family']=='qilou':pair('interior',[10.5,4.62,sp['placement']['depth_extension']+21],[10,4.9,sp['placement']['depth_extension']+12])
   else:
    t=sp['urban'];W0,D0=(t['w'],t['d'])if t['rotation']%2==0 else(t['d'],t['w'])
    def tpt(x,y,z):
     from rong_site import local
     a,c=local(t,x,z);return[a-sp['placement']['origin'][0],y,c-sp['placement']['origin'][2]]
    pair('interior',tpt(11.5,4.62,13.5),tpt(W0-2,4.4,8))
 if MODE=='draft':views=[a for a in views if a['id']in ['overall_SE','street_west','plaza','lane','region_plaza','front','interior']]
 (out/('cameras_'+MODE+'.json')).write_text(json.dumps(views,indent=2));records=[]
 for i in range(0,len(views),3):
  f=out/f'batch_{MODE}_{i}.json';f.write_text(json.dumps(views[i:i+3]));subprocess.run([sys.executable,__file__,RUN,'batch',RUN+'_'+id,str(f)],check=True);records+=json.loads((out/'render_report.json').read_text())
 (out/('views_'+MODE+'.json')).write_text(json.dumps(records,indent=2));print('render',id,len(records),flush=True)
