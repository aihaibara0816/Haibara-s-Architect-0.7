"""Pack NBT-derived triangles into 14-byte vertices and per-building draw ranges."""
from pathlib import Path
import sys,json,zlib,base64,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import numpy as np,industrial_states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];sp=json.loads((R/'spec.json').read_text());scene=ROOT/'review/previews'/(R.name+'_Substation01')/'scene';meta=json.loads((scene/'scene.json').read_text());assert meta['source_nbt_sha256']==sp['source_nbt_sha256']
w,h,d=sp['size_xyz'];owners=np.zeros((h,d,w),np.uint8)
owners=np.load(R/'owners.npz')['owners']
data={};ranges={};stats={}
dtype=np.dtype([('pos','<u2',3),('normal','i1',3),('color','u1',3),('emission','u1'),('pad','u1')]);assert dtype.itemsize==14
for kind in ['opaque','glass']:
 a=np.fromfile(scene/(kind+'.bin'),'<f4').reshape(-1,3,10)
 center=np.floor(a[:,:,:3].mean(axis=1)-a[:,0,3:6]*.0001).astype(int)
 center[:,0]=np.clip(center[:,0],0,w-1);center[:,1]=np.clip(center[:,1],0,h-1);center[:,2]=np.clip(center[:,2],0,d-1)
 ids=owners[center[:,1],center[:,2],center[:,0]];order=np.argsort(ids,kind='stable');counts=np.bincount(ids,minlength=len(sp['buildings'])+1);starts=np.r_[0,np.cumsum(counts[:-1])]
 ranges[kind]=[[int(s*3),int(c*3)]for s,c in zip(starts,counts)]
 packed=np.zeros((len(a),3),dtype=dtype)
 packed['pos']=np.rint(a[:,:,:3]*32).astype('<u2');packed['normal']=np.rint(a[:,:,3:6]*127).astype('i1');packed['color']=np.clip(np.rint(a[:,:,6:9]*255),0,255).astype('u1');packed['emission']=np.rint(a[:,:,9]*255).astype('u1')
 # Error bounds describe the packed viewer only, not the source NBT.
 poserr=float(np.max(np.abs(packed['pos'].astype(float)/32-a[:,:,:3])))if len(a) else 0
 raw=packed[order].tobytes();z=zlib.compress(raw,9);data[kind]=base64.b64encode(z).decode();stats[kind]={'vertices':len(a)*3,'raw_bytes':len(raw),'compressed_bytes':len(z),'sha256':hashlib.sha256(raw).hexdigest(),'position_quantization_max':poserr}
 print(kind,len(a),'triangles',len(z),'compressed',flush=True);del a,packed,raw,z,ids,center,order
data['light']=base64.b64encode(zlib.compress((scene/'blocklight.bin').read_bytes(),9)).decode()
payload={'size':sp['size_xyz'],'source_nbt_sha256':sp['source_nbt_sha256'],'ranges':ranges,'buildings':sp['buildings'],'bins':data,'stats':stats}
(R/'interactive_payload.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
(R/'interactive_metrics.json').write_text(json.dumps({k:v for k,v in payload.items()if k not in ['bins','buildings','ranges']},indent=2))
