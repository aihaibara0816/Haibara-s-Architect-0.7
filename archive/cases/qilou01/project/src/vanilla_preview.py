"""Offline preview of NBT with Mojang 1.21.1 JSON models and texture-colour tessellation.
Uses local, hash-verified client assets, not redistributed in the project.
Entity-rendered bed/banner models fall back to the recorded shape envelopes.
No claim to client rendering, biome tint fidelity, collision, UV-lock or animated textures.
"""
from pathlib import Path
import json,sys,math,collections,os
from functools import lru_cache
import numpy as np
from PIL import Image
from vendor.voxel_core import parse_state
from detail_lab import states as S
ROOT=Path(__file__).resolve().parents[1]
ASSET=Path(os.environ.get('ROOM06_MC_ASSETS',ROOT/'assets/minecraft-source/assets/minecraft'))
DIR={'north':(0,0,-1),'south':(0,0,1),'east':(1,0,0),'west':(-1,0,0),'up':(0,1,0),'down':(0,-1,0)}
@lru_cache(None)
def data(path):return json.loads((ASSET/path).read_text())
@lru_cache(None)
def model(name):
 name=name.replace('minecraft:','');d=data('models/'+name+'.json');p=d.get('parent','')
 base={} if not p or 'builtin/' in p else model(p)
 out={**base,**d};out['textures']={**base.get('textures',{}),**d.get('textures',{})};return out
@lru_cache(None)
def texture(name):
 name=name.replace('minecraft:','');im=Image.open(ASSET/'textures'/f'{name}.png').convert('RGBA');w,h=im.size
 # First frame of animated textures; no temporal effects in a still preview.
 return np.asarray(im.crop((0,0,w,min(w,h))),dtype=np.uint8)
def match(when,props):
 if not when:return True
 if 'OR' in when:return any(match(x,props) for x in when['OR'])
 if 'AND' in when:return all(match(x,props) for x in when['AND'])
 return all(props.get(k) in str(v).split('|') for k,v in when.items())
@lru_cache(None)
def applications(st):
 name,props=parse_state(st);d=data('blockstates/'+name.split(':')[-1]+'.json');out=[]
 for k,v in d.get('variants',{}).items():
  if match(dict(a.split('=') for a in k.split(',') if a),props):out.append(v[0] if isinstance(v,list) else v);break
 for a in d.get('multipart',[]):
  if match(a.get('when',{}),props):v=a['apply'];out.append(v[0] if isinstance(v,list) else v)
 return out
def rot(axis,angle):
 a=math.radians(angle);c,s=math.cos(a),math.sin(a)
 return np.array({'x':[[1,0,0],[0,c,-s],[0,s,c]],'y':[[c,0,s],[0,1,0],[-s,0,c]],'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis],float)
def facepoints(v,d):
 x,y,z,X,Y,Z=v
 return np.array({'north':[(X,y,z),(x,y,z),(x,Y,z),(X,Y,z)],'south':[(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],'west':[(x,y,z),(x,y,Z),(x,Y,Z),(x,Y,z)],'east':[(X,y,Z),(X,y,z),(X,Y,z),(X,Y,Z)],'up':[(x,Y,Z),(X,Y,Z),(X,Y,z),(x,Y,z)],'down':[(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)]}[d],float)
def defaults(v,d):
 x,y,z,X,Y,Z=v
 return {'down':[x,16-Z,X,16-z],'up':[x,z,X,Z],'north':[16-X,16-Y,16-x,16-y],'south':[x,16-Y,X,16-y],'west':[z,16-Y,Z,16-y],'east':[16-Z,16-Y,16-z,16-y]}[d]
def resolve(tx,m):
 for _ in range(20):
  if not tx.startswith('#'):return tx
  tx=m['textures'][tx[1:]]
 raise ValueError('texture cycle')
def gridface(q,normal,uv,tex,angle,tint,emission):
 u0,v0,u1,v1=uv;cap=int(os.environ.get('TOWN_TEXTURE_GRID','16'));nx=max(1,min(cap,math.ceil(abs(u1-u0))));ny=max(1,min(cap,math.ceil(abs(v1-v0))))
 # Pixel-centred texture sampling onto the model's own face; no extra furniture.
 ii,jj=np.meshgrid(np.arange(nx),np.arange(ny));u=(ii.ravel()+.5)/nx;v=(jj.ravel()+.5)/ny
 if angle: 
  for _ in range((angle//90)%4):u,v=1-v,u
 px=np.clip(((u0+(u1-u0)*u)/16*tex.shape[1]).astype(int),0,tex.shape[1]-1)
 py=np.clip(((v1-(v1-v0)*v)/16*tex.shape[0]).astype(int),0,tex.shape[0]-1)
 colors=tex[py,px];keep=colors[:,3]>=80
 i=ii.ravel()[keep];j=jj.ravel()[keep];col=colors[keep,:3]/255*tint
 if len(i)==0:return np.zeros((0,10),np.float32)
 du=q[1]-q[0];dv=q[3]-q[0]
 coords=np.stack([np.stack([(i+di)/nx,(j+dj)/ny],axis=-1) for di,dj in [(0,0),(1,0),(1,1),(0,0),(1,1),(0,1)]],axis=1)
 pts=q[0]+coords[:,:,0,None]*du+coords[:,:,1,None]*dv
 nn=np.broadcast_to(normal,(len(i),6,3));cc=np.broadcast_to(col[:,None,:],(len(i),6,3));ee=np.full((len(i),6,1),emission)
 return np.concatenate([pts,nn,cc,ee],axis=2).reshape(-1,10).astype('<f4')
@lru_cache(None)
def cube_template(st):
 if S.family(st) not in ['cube','leaves']:return None
 name,props=parse_state(st);faces=[];names=[]
 try:
  apps=applications(st)
  if not apps:return None
  for app in apps:
   m=model(app['model']);names.append(app['model']);els=m.get('elements',[])
   if len(els)!=1 or els[0].get('rotation') or els[0]['from']!=[0,0,0] or els[0]['to']!=[16,16,16]:return None
   el=els[0];bounds=np.array(el['from']+el['to'],float);rm=rot('y',-app.get('y',0))@rot('x',-app.get('x',0))
   emission=1.0 if any(t in name for t in ['sea_lantern','lantern','end_rod','glowstone'])else 0.0
   for direction,face in el['faces'].items():
    dn=tuple(np.rint(rm@np.array(DIR[face['cullface']])).astype(int))if 'cullface'in face else None
    q=(facepoints(bounds,direction)/16-.5)@rm.T+.5;normal=rm@np.array(DIR[direction],float);txname=resolve(face['texture'],m);tx=texture(txname)
    tint=(np.array([.25,.48,.90])if 'water'in txname else np.array([.57,.74,.35]))if 'tintindex'in face else np.ones(3)
    if 'cherry_leaves'in st:tint=np.ones(3)
    elif 'spruce_leaves'in st and 'tintindex'in face:tint=np.array([97,153,97])/255
    arr=gridface(q,normal,face.get('uv',defaults(bounds,direction)),tx,face.get('rotation',0),tint,emission);faces.append((dn,arr))
  return faces,names
 except (FileNotFoundError,KeyError,ValueError):return None
@lru_cache(None)
def opaque(st):return S.support_cube(st)and 'glass'not in st
def occludes(st,neighbor):return opaque(neighbor)or('_leaves['in st and neighbor==st)
def apply(build,scene,nbt_path=None):
 scene=Path(scene);chunks={'opaque':[],'glass':[]};fallback=collections.Counter();used_models=set();total=0
 for pos,st in build.blocks.items():
  if st=='minecraft:air':continue
  # Interior faces of solid terrain contribute no visible geometry.
  if (opaque(st)or '_leaves['in st)and all(occludes(st,build.blocks.get(tuple(pos[i]+d[i]for i in range(3)),'minecraft:air'))for d in DIR.values()):continue
  name,props=parse_state(st);isglass='glass' in name or name=='minecraft:water';bucket='glass' if isglass else 'opaque';emission=1.0 if any(x in name for x in ['sea_lantern','lantern','end_rod','glowstone']) else 0.0
  cached=cube_template(st)
  if cached is not None:
   faces,names=cached;used_models.update(names)
   for dn,arr in faces:
    if dn is not None:
     ns=build.blocks.get(tuple(pos[i]+int(dn[i])for i in range(3)),'minecraft:air')
     if occludes(st,ns):continue
    out=arr.copy();out[:,:3]+=pos;chunks[bucket].append(out)
   total+=1;continue
  try:
   apps=applications(st)
   if not apps:raise ValueError('no application')
   emitted=False
   for app in apps:
    m=model(app['model']);used_models.add(app['model']);els=m.get('elements')
    if not els:raise ValueError('entity or built-in model')
    rm=rot('y',-app.get('y',0))@rot('x',-app.get('x',0))
    for el in els:
     bounds=np.array(el['from']+el['to'],float);er=el.get('rotation');erm=rot(er['axis'],er['angle']) if er else np.eye(3);origin=np.array(er.get('origin',[8,8,8]) if er else [8,8,8])/16
     for direction,face in el['faces'].items():
      if 'cullface' in face:
       dn=np.rint(rm@np.array(DIR[face['cullface']])).astype(int);neighbor=tuple(pos[i]+int(dn[i]) for i in range(3));ns=build.blocks.get(neighbor,'minecraft:air')
       if occludes(st,ns):continue
      q=facepoints(bounds,direction)/16;normal=np.array(DIR[direction],float)
      if er:q=(q-origin)@erm.T+origin;normal=erm@normal
      q=(q-.5)@rm.T+.5+pos;normal=rm@normal
      txname=resolve(face['texture'],m);tx=texture(txname);tint=(np.array([.25,.48,.90]) if 'water' in txname else np.array([.57,.74,.35])) if 'tintindex' in face else np.ones(3)
      # Cherry foliage uses its intrinsic pink texture; no grass tint in vanilla.
      if 'cherry_leaves' in st:tint=np.ones(3)
      elif 'spruce_leaves' in st and 'tintindex' in face:tint=np.array([97,153,97])/255
      arr=gridface(q,normal,face.get('uv',defaults(bounds,direction)),tx,face.get('rotation',0),tint,emission)
      chunks[bucket].append(arr);emitted=True
   if not emitted:pass
  except (FileNotFoundError,KeyError,ValueError) as e:
   fallback[name]+=1
   for bi,bb in enumerate(S.boxes(st)):
    for d in DIR:
     q=facepoints(np.array(bb)*16,d)/16+pos;c=np.array(S.color(st))/255;tex=np.array([[[*list((c*255).astype(int)),255]]],np.uint8)
     uv=[0,0,1,1]
     if name.endswith('_bed'):
      if bi>0:tex=np.array([[[137,103,66,255]]],np.uint8)
      elif d=='up':
       tex=np.full((16,16,4),[226,224,210,255],np.uint8);uv=[0,0,16,16]
       if props.get('part')=='head':tex[1:7,1:15]=[250,248,237,255]
     chunks[bucket].append(gridface(q,np.array(DIR[d]),uv,tex,0,np.ones(3),emission))
  total+=1
 painting_count=0
 if nbt_path:
  import nbtlib
  source={'entities':build.info['entities_payload']} if 'entities_payload' in build.info else nbtlib.load(nbt_path)
  for e in source.get('entities',[]):
   ent=e['nbt']
   if str(ent.get('id'))!='minecraft:painting':continue
   anchor=tuple(int(ent[k])for k in ['TileX','TileY','TileZ']);face0=['south','west','north','east'][int(ent['facing'])];delta=DIR[face0];back=tuple(anchor[i]-delta[i]for i in range(3))
   if back not in build.blocks:continue
   # The case uses 1x1 vanilla variants. Mesh their actual atlas sprites from the NBT entity.
   key=str(ent['variant']).split(':')[-1]
   definition=json.loads((ASSET.parents[1]/'data/minecraft/painting_variant'/f'{key}.json').read_text())
   w,h=definition['width'],definition['height'];assert w==h==1
   face=['south','west','north','east'][int(ent['facing'])]
   center=np.array(list(map(float,ent['Pos'])));half=np.array([w/2,h/2,w/2]);half[0 if face in ['west','east']else 2]=1/32
   bounds=np.concatenate([center-half,center+half]);tx=texture('painting/'+definition['asset_id'].split(':')[-1])
   for side in DIR:
    t=tx if side==face else np.array([[[102,74,43,255]]],np.uint8)
    chunks['opaque'].append(gridface(facepoints(bounds,side),np.array(DIR[side]),[0,0,16,16],t,0,np.ones(3),0))
   painting_count+=1
 for bucket,arrays in chunks.items():
  import os
  temporary=scene/(bucket+'.bin.tmp')
  expected=sum(arr.nbytes for arr in arrays)
  with temporary.open('wb') as out:
   for arr in arrays:out.write(arr.tobytes())
   out.flush();os.fsync(out.fileno())
  assert temporary.stat().st_size==expected,(bucket,temporary.stat().st_size,expected)
  os.replace(temporary,scene/(bucket+'.bin'))
 meta=json.loads((scene/'scene.json').read_text());meta['texture_grid_max']=int(os.environ.get('TOWN_TEXTURE_GRID','16'));meta['painting_entities_rendered']=painting_count;meta['triangles']={k:sum(len(a)//3 for a in v) for k,v in chunks.items()};meta['material_mode']='Minecraft Java 1.21.1 JSON models + first-frame texture colours, offline EGL; not game footage';meta['model_fallbacks']=dict(fallback);meta['limitations']=['Entity beds and banners use approximate boxes','1x1 paintings use their NBT positions and official variant textures','Biome tint approximated; weighted model variants use first item','UV lock and element rescale not fully reproduced; no Minecraft client lighting'];tmpmeta=scene/'scene.json.tmp'
 with tmpmeta.open('w') as f:
  f.write(json.dumps(meta,indent=2));f.flush();os.fsync(f.fileno())
 os.replace(tmpmeta,scene/'scene.json')
 assert json.loads((scene/'scene.json').read_text())['triangles']==meta['triangles']
 print('texture mesh',meta['triangles'],dict(fallback),flush=True)
