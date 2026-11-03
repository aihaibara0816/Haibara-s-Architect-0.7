"""Sponge v3 export, independent full-volume and block-entity readback."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'support'),str(ROOT/'src')]
import numpy as np,nbtlib as n
from rail_nbt import to_nbt
from vendor.inspect_build import load_build,Limits,read_nbt,decode_varints
R=ROOT/'runs'/sys.argv[1]
L=Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024)
b=load_build(R/'Substation01.nbt',L)
w,h,d=b.size;pal=['minecraft:air']+sorted(set(b.blocks.values()));ids={st:i for i,st in enumerate(pal)}
arr=np.zeros((h,d,w),np.uint16)
for (x,y,z),st in b.blocks.items():arr[y,z,x]=ids[st]
flat=arr.reshape(-1)
if len(pal)<128:data=flat.astype(np.uint8).tobytes()
else:
 encoded=[]
 for i in range(len(pal)):
  v=i;out=[]
  while v>=128:out.append((v&127)|128);v>>=7
  out.append(v);encoded.append(bytes(out))
 data=b''.join(encoded[int(v)] for v in flat)
raw,_=read_nbt(R/'Substation01.nbt',L);bes=[];expected={}
for e in raw['blocks']:
 if 'nbt' not in e:continue
 q=e['nbt'];pos=tuple(e['pos']);expected[pos]=q
 payload=to_nbt(q);id=payload.pop('id');be=n.Compound({'Id':id,'Pos':n.IntArray(pos),'Data':payload})
 bes.append(be)
assert not raw.get('entities');del raw
origin=json.loads((R/'spec.json').read_text())['spawn_local'];offset=[-x for x in origin]
f=n.File({'Schematic':n.Compound({'Version':n.Int(3),'DataVersion':n.Int(3955),'Width':n.Short(w),'Height':n.Short(h),'Length':n.Short(d),'Offset':n.IntArray(offset),'Blocks':n.Compound({'Palette':n.Compound({st:n.Int(i) for st,i in ids.items()}),'Data':n.ByteArray(np.frombuffer(data,dtype=np.int8)),'BlockEntities':n.List[n.Compound](bes)}),'Entities':n.List[n.Compound]([]),'Metadata':n.Compound({'Name':n.String('Substation01 vanilla AIS architectural station'),'Author':n.String('GAFAcraft / HAF case adapter'),'RequiredMods':n.List[n.String]([])})})},gzipped=True)
path=R/'Substation01.schem';f.save(path)
raw,_=read_nbt(path,L);s=raw.get('Schematic',raw)
decoded=np.fromiter(decode_varints(s['Blocks']['Data'],w*h*d),dtype=np.uint16,count=w*h*d)
assert np.array_equal(decoded,flat);assert {k:int(v) for k,v in s['Blocks']['Palette'].items()}==ids
actual={tuple(e['Pos']):{'id':e['Id'],**e['Data']} for e in s['Blocks']['BlockEntities']}
assert actual==expected
report={'format':'Sponge v3','checked_cells':w*h*d,'mismatches':0,'block_entities':len(bes),'block_entity_mismatches':0,'origin_local':origin,'offset_xyz':offset,'source_nbt_sha256':hashlib.sha256((R/'Substation01.nbt').read_bytes()).hexdigest(),'schem_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'worldedit_import':'not_run','air':'full bounding box included; paste can replace existing blocks'}
(R/'schem_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
