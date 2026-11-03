from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'support')]
import numpy as np,nbtlib as n
from vendor.inspect_build import load_build,Limits,read_nbt,decode_varints
R=ROOT/'runs'/sys.argv[1];b=load_build(R/'Guanggang01.nbt',Limits(cells=12_000_000,nodes=30_000_000,decoded_bytes=128*1024*1024))
w,h,d=b.size;pal=['minecraft:air']+sorted(set(b.blocks.values()));ids={st:i for i,st in enumerate(pal)};assert len(pal)<128
arr=np.zeros((h,d,w),np.uint8)
for (x,y,z),st in b.blocks.items():arr[y,z,x]=ids[st]
f=n.File({'Version':n.Int(2),'DataVersion':n.Int(3955),'Width':n.Short(w),'Height':n.Short(h),'Length':n.Short(d),'Offset':n.IntArray([-132,-3,-179]),'PaletteMax':n.Int(len(pal)),'Palette':n.Compound({st:n.Int(i) for i,st in enumerate(pal)}),'BlockData':n.ByteArray(arr.reshape(-1).view(np.int8)),'BlockEntities':n.List[n.Compound]([]),'Entities':n.List[n.Compound]([]),'Metadata':n.Compound({'Name':n.String('Guanggang01 - original steelworks study'),'Author':n.String('GAFAcraft / HAF case adapter')})},root_name='Schematic',gzipped=True)
path=R/'Guanggang01.schem';f.save(path)
raw,info=read_nbt(path,Limits(cells=12_000_000,nodes=30_000_000,decoded_bytes=128*1024*1024));s=raw.get('Schematic',raw)
decoded=np.fromiter(decode_varints(s['BlockData'],w*h*d),dtype=np.uint8,count=w*h*d);assert np.array_equal(decoded,arr.reshape(-1));assert {k:int(v) for k,v in s['Palette'].items()}==ids
report={'format':'Sponge v2','checked_cells':w*h*d,'mismatches':0,'origin_local':[132,3,179],'offset_xyz':[-132,-3,-179],'source_nbt_sha256':hashlib.sha256((R/'Guanggang01.nbt').read_bytes()).hexdigest(),'schem_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'worldedit_import':'not_run','air':'full bounding box included; paste can replace existing blocks'}
(R/'schem_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
