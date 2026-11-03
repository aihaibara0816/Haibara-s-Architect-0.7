"""Write final NBT into a copy of the established Java 1.21.1 flat test world.
No server execution is claimed. Region readback verifies every state and empty cell.
"""
from pathlib import Path
import sys,io,zlib,json,time,collections,shutil,hashlib
import numpy as np
import nbtlib as n
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
run=sys.argv[1];template=Path(sys.argv[2]);dest=Path(sys.argv[3]);R=C/'runs'/run
assert not dest.exists(),dest
shutil.copytree(template,dest)
for f in ['entities','poi','playerdata','advancements','stats']:
 if (dest/f).exists():shutil.rmtree(dest/f)
b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));by=collections.defaultdict(dict)
for (x,y,z),st in b.blocks.items():by[x//16-10,z//16-9][x%16,y+60,z%16]=st
def canon(q):
 return str(q['Name'])+('['+','.join(k+'='+str(q['Properties'][k]) for k in sorted(q['Properties']))+']' if q.get('Properties') else '')
def pack(vals,bits):
 per=64//bits;vals=np.asarray(vals,np.uint64);a=np.zeros((len(vals)+per-1)//per,np.uint64)
 for j in range(per):
  v=vals[j::per];a[:len(v)]|=v<<np.uint64(j*bits)
 return n.LongArray(a.view(np.int64))
def palrec(st):
 name,props=parse_state(st);q=n.Compound({'Name':n.String(name)})
 if props:q['Properties']=n.Compound({k:n.String(v) for k,v in props.items()})
 return q
def decode(s):
 ps=s['block_states'];pal=[canon(q) for q in ps['palette']]
 if len(pal)==1:return np.full((16,16,16),pal[0],dtype=object)
 bits=max(4,(len(pal)-1).bit_length());per=64//bits;raw=np.asarray(ps['data'],np.int64).view(np.uint64);idx=np.arange(4096)
 ids=(raw[idx//per]>>(idx%per*bits).astype(np.uint64))&((1<<bits)-1)
 return np.asarray(pal,dtype=object)[ids.astype(int)].reshape(16,16,16)
def read_regions(path):
 out={}
 for p in (path/'region').glob('*.mca'):
  data=p.read_bytes()
  for i in range(1024):
   off=int.from_bytes(data[i*4:i*4+3],'big')*4096
   if not off:continue
   size=int.from_bytes(data[off:off+4],'big');assert data[off+4]==2
   c=n.File.parse(io.BytesIO(zlib.decompress(data[off+5:off+4+size])))
   out[int(c['xPos']),int(c['zPos'])]=c
 return out
chunks=read_regions(dest)
for key,cells in by.items():
 chunk=chunks[key];sm={int(s['Y']):s for s in chunk['sections']}
 for sy in range(3,7):
  s=sm[sy];arr=decode(s)
  for ly in range(16):
   yy=sy*16+ly
   if 60<=yy<108:arr[ly,:,:]='minecraft:air'
  for (x,y,z),st in cells.items():
   if y//16==sy:arr[y%16,z,x]=st
  pal,idx=np.unique(arr.reshape(-1),return_inverse=True)
  ps=n.Compound({'palette':n.List[n.Compound]([palrec(st) for st in pal])})
  if len(pal)>1:ps['data']=pack(idx,max(4,(len(pal)-1).bit_length()))
  s['block_states']=ps
 for s in chunk['sections']:s.pop('BlockLight',None);s.pop('SkyLight',None)
 chunk['isLightOn']=n.Byte(0)
 chunk['block_ticks']=n.List[n.Compound]([]);chunk['fluid_ticks']=n.List[n.Compound]([]);chunk['block_entities']=n.List[n.Compound]([])
 # All placed blocks are vanilla non-block-entity decorations. Ask the game to relight.
 tops={k:np.full(256,59,int) for k in ['WORLD_SURFACE','MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES','OCEAN_FLOOR']}
 for (x,y,z),st in cells.items():
  i=z*16+x;f=states.family(st);name=st.split('[')[0]
  tops['WORLD_SURFACE'][i]=max(tops['WORLD_SURFACE'][i],y)
  if f not in ['crop','flower','air']:
   tops['MOTION_BLOCKING'][i]=max(tops['MOTION_BLOCKING'][i],y)
   if f!='leaves':tops['MOTION_BLOCKING_NO_LEAVES'][i]=max(tops['MOTION_BLOCKING_NO_LEAVES'][i],y)
   if name!='minecraft:water':tops['OCEAN_FLOOR'][i]=max(tops['OCEAN_FLOOR'][i],y)
 chunk['Heightmaps']=n.Compound({k:pack(v+65,9) for k,v in tops.items()})
 chunk['DataVersion']=n.Int(3955);chunk['Status']=n.String('minecraft:full')
regions=collections.defaultdict(dict)
for (cx,cz),c in chunks.items():regions[cx//32,cz//32][cx%32+32*(cz%32)]=c
for (rx,rz),cc in regions.items():
 header=bytearray(8192);bodies=[];sector=2
 for i,c in sorted(cc.items()):
  out=io.BytesIO();c.write(out);blob=zlib.compress(out.getvalue(),6);data=(len(blob)+1).to_bytes(4,'big')+b'\x02'+blob;count=(len(data)+4095)//4096
  header[i*4:i*4+3]=sector.to_bytes(3,'big');header[i*4+3]=count;header[4096+i*4:4100+i*4]=int(time.time()).to_bytes(4,'big');bodies.append(data+bytes(count*4096-len(data)));sector+=count
 (dest/'region'/f'r.{rx}.{rz}.mca').write_bytes(header+b''.join(bodies))
f=n.load(dest/'level.dat');d=f['Data'];d['LevelName']=n.String('Tiangengli 18 - '+run+' Landscape');d['SpawnX']=n.Int(-15);d['SpawnY']=n.Int(64);d['SpawnZ']=n.Int(-9);d['SpawnAngle']=n.Float(180);d['GameType']=n.Int(1);d['allowCommands']=n.Byte(1);d['Time']=n.Long(6000);d['DayTime']=n.Long(6000);d['raining']=n.Byte(0);d['thundering']=n.Byte(0);d.pop('Player',None);f.save()
# Independently parse serialized regions, including all unoccupied positions in the site volume.
readback=read_regions(dest);bad=[];extra=[];checked=0
for (cx,cz),expected in by.items():
 chunk=readback[cx,cz];sm={int(s['Y']):s for s in chunk['sections']}
 for sy in range(3,7):
  arr=decode(sm[sy])
  for ly in range(16):
   y=sy*16+ly
   if not 60<=y<108:continue
   for z in range(16):
    for x in range(16):
     actual=arr[ly,z,x];want=expected.get((x,y,z),'minecraft:air');checked+=1
     if actual!=want:
      (extra if want=='minecraft:air' else bad).append([cx*16+x,y,cz*16+z,want,actual])
report=dict(source_nbt_sha256=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),version='Java 1.21.1',data_version=3955,modified_chunks=len(by),checked_cells=checked,blockstate_mismatches=len(bad),unexpected_blocks_in_air=len(extra),spawn=[-15,64,-9],offset=[-160,60,-144],all_chunks_full=all(str(readback[k]['Status'])=='minecraft:full' for k in by),lighting='isLightOn=0; Minecraft must recalculate lighting on first load',server_execution='not performed for this build',game_client='pending',screenshots='NBT-rendered previews only')
(R/'world_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));assert not bad and not extra
