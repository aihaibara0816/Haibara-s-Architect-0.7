"""Typed rail payloads and case exporter; every mod data field remains in final NBT."""
import uuid,struct,gzip,hashlib,json
import numpy as np
from vendor import voxel_core as C
_base=C._payload
def payload(t,v):
 if t in {1,2,4,5,6}:return struct.pack({1:'>b',2:'>h',4:'>q',5:'>f',6:'>d'}[t],v)
 if t==11:return struct.pack('>i',len(v))+b''.join(struct.pack('>i',int(x)) for x in v)
 if t==12:return struct.pack('>i',len(v))+b''.join(struct.pack('>q',int(x)) for x in v)
 return _base(t,v)
C._payload=payload
B=lambda x:(1,int(x));I=lambda x:(3,int(x));D=lambda x:(6,float(x));T=lambda x:(8,x);A=lambda x:(11,list(x));CO=lambda x:(10,x)
L=lambda kind,x:(9,(kind,x))
def uid(name):return A(np.frombuffer(uuid.uuid5(uuid.NAMESPACE_URL,'gafacraft/RailDepot01/R01/'+name).bytes,dtype='>i4').tolist())
def targeting(name,pos,target,positive=True):
 return {'Id':uid(name),'TargetTrack':A([target[i]-pos[i] for i in range(3)]),'TargetDirection':B(positive),'Ortho':B(1),'PrevAxis':L(6,[1.,0.,0.]),'HasAttachedComputer':B(0)}
def conn(p,q,primary):
 sign=1 if q[0]>p[0] else -1
 a=[p[0]+(1 if sign>0 else 0),p[1],p[2]+.5];b=[q[0]+(0 if sign>0 else 1),q[1],q[2]+.5]
 return {'Positions':L(10,[{'Pos':A([0,0,0])},{'Pos':A([q[i]-p[i] for i in range(3)])}]),'Starts':L(10,[{'V':L(6,[float(a[i]-p[i]) for i in range(3)])},{'V':L(6,[float(b[i]-p[i]) for i in range(3)])}]),'Axes':L(10,[{'V':L(6,[float(sign),0.,0.])},{'V':L(6,[float(-sign),0.,0.])}]),'Normals':L(10,[{'V':L(6,[0.,1.,0.])},{'V':L(6,[0.,1.,0.])}]),'Primary':B(primary),'Girder':B(0),'Material':T('create:andesite')}
def curve_points(p,q,count=257):
 # Create BezierConnection.Runtime.determineHandles, parallel horizontal axes.
 a=np.array([p[0]+1,p[1],p[2]+.5],float);b=np.array([q[0],q[1],q[2]+.5],float)
 run=abs(b[0]-a[0]);rise=abs(b[2]-a[2]);mi,ma=min(run,rise),max(run,rise)
 h=ma-mi if mi>1.2 and 1<ma/mi<3 else np.linalg.norm(b-a)/3
 c=a+[h,0,0];d=b-[h,0,0];t=np.linspace(0,1,count)[:,None]
 return (1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*b

def export(scene,bes,path):
 names=sorted(set(scene.blocks.values()));ids={s:i for i,s in enumerate(names)};palette=[]
 for s in names:
  n,p=C.parse_state(s);r={'Name':T(n)}
  if p:r['Properties']=CO({k:T(v) for k,v in p.items()})
  palette.append(r)
 entries=[]
 for pos,s in sorted(scene.blocks.items(),key=lambda v:(v[0][1],v[0][2],v[0][0])):
  r={'pos':L(3,list(pos)),'state':I(ids[s])};name=C.parse_state(s)[0]
  if pos in bes:r['nbt']=CO(bes[pos])
  elif name.endswith('_bed'):r['nbt']=CO({'id':T('minecraft:bed')})
  elif name in {'minecraft:barrel','minecraft:furnace'}:r['nbt']=CO({'id':T(name),'Items':L(10,[])})
  entries.append(r)
 root={'DataVersion':I(3955),'size':L(3,list(scene.size)),'palette':L(10,palette),'blocks':L(10,entries),'entities':L(10,[])}
 blob=gzip.compress(b'\x0a\0\0'+payload(10,root),compresslevel=9,mtime=0);path.write_bytes(blob)
 return hashlib.sha256(blob).hexdigest()

def to_nbt(raw,key=''):
 import nbtlib as n
 if isinstance(raw,dict):return n.Compound({k:to_nbt(v,k) for k,v in raw.items()})
 if isinstance(raw,list):
  if key in {'Id','TargetTrack','Pos'} and all(isinstance(x,int) for x in raw):return n.IntArray(raw)
  ty=n.Compound if not raw or isinstance(raw[0],dict) else n.List if isinstance(raw[0],list) else n.Double if isinstance(raw[0],float) else n.Int
  return n.List[ty]([to_nbt(v) for v in raw])
 if isinstance(raw,str):return n.String(raw)
 if isinstance(raw,float):return n.Double(raw)
 if key in {'Primary','Girder','TargetDirection','Ortho','HasAttachedComputer','AlternateModel','Power','Cyclic','Assembling','Slot'}:return n.Byte(raw)
 return n.Int(raw)
