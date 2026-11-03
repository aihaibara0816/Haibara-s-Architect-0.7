"""Render final read-back Create track cells and reciprocal Bezier connections."""
import numpy as np,json
from vendor.inspect_build import read_nbt,Limits
from rail_nbt import curve_points
from vendor.voxel_core import parse_state
from detail_lab.mesh import CORNERS,FACES,write_array_atomic

def append_tracks(build,path,out):
 triangles=[]
 def cuboid(lo,hi,col,transform=None):
  vs=CORNERS*(np.array(hi)-lo)+lo
  if transform is not None:vs=vs@transform[0].T+transform[1]
  for normal,inds in FACES:
   norm=np.array(normal) if transform is None else transform[0]@np.array(normal)
   v=np.zeros((6,10),np.float32);v[:,:3]=vs[np.array(inds)[[0,1,2,0,2,3]]];v[:,3:6]=norm;v[:,6:9]=np.array(col)/255;triangles.append(v)
 rail=(139,149,151);tie=(101,92,77)
 for p,s in build.blocks.items():
  n,props=parse_state(s)
  if n!='create:track':continue
  # Longitudinal local X, transverse local Z; envelope from official 6.0.10 model.
  rot=np.eye(3) if props['shape']=='xo' else np.array([[0,0,1],[0,1,0],[-1,0,0]])
  org=np.array(p,float)+([0,0,.5] if props['shape']=='xo' else [.5,0,1])
  for x in [.125,.625]:cuboid([x,-.12,-1.371875],[x+.25,.1,1.371875],tie,(rot,org))
  for z in [-.965625,.965625]:cuboid([0,.08,z-.125],[1,.346484,z+.125],rail,(rot,org))
 raw,_=read_nbt(path,Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024));curve_count=0
 for e in raw['blocks']:
  be=e.get('nbt',{})
  for c in be.get('Connections',[]):
   if not c['Primary']:continue
   p=np.array(e['pos']);q=p+np.array(c['Positions'][1]['Pos']);pts=curve_points(p,q,257);cum=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
   s=np.linspace(0,cum[-1],max(2,int(cum[-1]*2)+1));ps=np.array([np.interp(s,cum,pts[:,k]) for k in range(3)]).T
   for i in range(len(ps)-1):
    v=ps[i+1]-ps[i];le=np.linalg.norm(v);dx=v/le;side=np.array([-dx[2],0,dx[0]]);rot=np.stack([dx,[0,1,0],side],axis=1)
    for z in [-.965625,.965625]:cuboid([0,.08,z-.125],[le+.015,.346484,z+.125],rail,(rot,ps[i]))
    if i%2==0:cuboid([-.13,-.12,-1.371875],[.13,.10,1.371875],tie,(rot,ps[i]))
   curve_count+=1
 del raw
 extra=np.concatenate(triangles);dest=out/'opaque.bin';old=np.fromfile(dest,'<f4').reshape(-1,10);start=len(old)//3
 write_array_atomic(np.concatenate([old,extra]).astype('<f4'),dest)
 meta=json.loads((out/'scene.json').read_text());meta['rail_extra_triangles']=[start,len(extra)//3];meta['triangles']['opaque']+=len(extra)//3;meta['Create_curve_count']=curve_count;meta['source']='independent final NBT: vanilla approximate boxes + Create measured straight meshes and NBT Bezier curves';meta['limitations'].append('Create stations/signals are untextured approximate housings; signal colour is not runtime state')
 (out/'scene.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));return meta
