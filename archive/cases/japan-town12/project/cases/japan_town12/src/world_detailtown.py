"""Java 1.21.1 Anvil world from the final structure; no game execution claimed."""
from pathlib import Path
import sys,json,io,zlib,time,collections,hashlib,math
import numpy as np
import nbtlib as n
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
RUN=sys.argv[1];R=C/'runs'/RUN;dest=Path(sys.argv[2]);assert not dest.exists()
(dest/'region').mkdir(parents=True)
rb=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));offset=(-rb.size[0]//2,60,-rb.size[2]//2)
by=collections.defaultdict(dict)
for (x,y,z),st in rb.blocks.items():
 x+=offset[0];y+=offset[1];z+=offset[2];by[x//16,z//16][x%16,y,z%16]=st
def pack(vals,bits):
 per=64//bits;vals=np.asarray(vals,np.uint64);a=np.zeros((len(vals)+per-1)//per,np.uint64)
 for j in range(per):
  v=vals[j::per];a[:len(v)]|=v<<np.uint64(j*bits)
 return n.LongArray(a.view(np.int64))
def palrec(st):
 name,props=parse_state(st);q=n.Compound({'Name':n.String(name)})
 if props:q['Properties']=n.Compound({k:n.String(v) for k,v in props.items()})
 return q
def ps(arr):
 pal,idx=np.unique(arr.reshape(-1),return_inverse=True);q=n.Compound({'palette':n.List[n.Compound]([palrec(s) for s in pal])})
 if len(pal)>1:q['data']=pack(idx,max(4,(len(pal)-1).bit_length()))
 return q
def canon(q):return str(q['Name'])+('['+','.join(k+'='+str(q['Properties'][k]) for k in sorted(q['Properties']))+']' if q.get('Properties') else '')
def decode(s):
 q=s['block_states'];pal=[canon(x) for x in q['palette']]
 if len(pal)==1:return np.full((16,16,16),pal[0],object)
 bits=max(4,(len(pal)-1).bit_length());per=64//bits;raw=np.asarray(q['data'],np.int64).view(np.uint64);idx=np.arange(4096);ids=(raw[idx//per]>>(idx%per*bits).astype(np.uint64))&((1<<bits)-1)
 return np.asarray(pal,object)[ids.astype(int)].reshape(16,16,16)
regions=collections.defaultdict(dict);expected={}
print('world chunks',flush=True)
for cz in range(-8,8):
 for cx in range(-8,8):
  allarr=np.full((384,16,16),'minecraft:air',object)
  allarr[0,:,:]='minecraft:bedrock';allarr[1:125,:,:]='minecraft:stone';allarr[125:128,:,:]='minecraft:dirt';allarr[128,:,:]=states.make('grass_block')
  # Flat surroundings meet y=64; clear the complete source bounding volume.
  for z in range(16):
   for x in range(16):
    if offset[0]<=cx*16+x<offset[0]+rb.size[0] and offset[2]<=cz*16+z<offset[2]+rb.size[2]:allarr[124:124+rb.size[1],z,x]='minecraft:air'
  for (x,y,z),st in by.get((cx,cz),{}).items():allarr[y+64,z,x]=st
  sections=[]
  for sy in range(-4,20):
   arr=allarr[(sy+4)*16:(sy+5)*16]
   sections.append(n.Compound({'Y':n.Byte(sy),'block_states':ps(arr),'biomes':n.Compound({'palette':n.List[n.String]([n.String('minecraft:plains')])})}))
  mask=allarr!='minecraft:air';ht=np.argmax(mask[::-1],axis=0);height=384-ht
  hm=n.Compound({k:pack(height.reshape(-1),9) for k in ['WORLD_SURFACE','MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES','OCEAN_FLOOR']})
  # Heightmaps that exclude water/leaves use their actual top occupied support.
  for key,exclude in [('OCEAN_FLOOR',('water',)),('MOTION_BLOCKING_NO_LEAVES',('leaves',))]:
   m=mask.copy()
   for val in np.unique(allarr):
    if any(t in val for t in exclude):m[allarr==val]=False
   hm[key]=pack((384-np.argmax(m[::-1],axis=0)).reshape(-1),9)
  c=n.File({'DataVersion':n.Int(3955),'xPos':n.Int(cx),'zPos':n.Int(cz),'yPos':n.Int(-4),'Status':n.String('minecraft:full'),'LastUpdate':n.Long(0),'InhabitedTime':n.Long(0),'isLightOn':n.Byte(0),'sections':n.List[n.Compound](sections),'block_entities':n.List[n.Compound]([n.Compound({'id':n.String('minecraft:banner'),'x':n.Int(cx*16+x),'y':n.Int(y),'z':n.Int(cz*16+z),'patterns':n.List[n.Compound]([])}) for (x,y,z),st in by.get((cx,cz),{}).items() if '_wall_banner' in st]),'block_ticks':n.List[n.Compound]([]),'fluid_ticks':n.List[n.Compound]([]),'Heightmaps':hm,'PostProcessing':n.List[n.List[n.Short]]([n.List[n.Short]([]) for _ in range(24)]),'structures':n.Compound({'starts':n.Compound({}),'References':n.Compound({})})})
  regions[cx//32,cz//32][cx%32+32*(cz%32)]=c
  if (cx,cz) in by:expected[cx,cz]=allarr[124:172].copy()
for (rx,rz),cc in regions.items():
 header=bytearray(8192);bodies=[];sector=2
 for i,c in sorted(cc.items()):
  out=io.BytesIO();c.write(out);blob=zlib.compress(out.getvalue(),6);data=(len(blob)+1).to_bytes(4,'big')+b'\x02'+blob;count=math.ceil(len(data)/4096)
  header[i*4:i*4+3]=sector.to_bytes(3,'big');header[i*4+3]=count;header[4096+i*4:4100+i*4]=int(time.time()).to_bytes(4,'big');bodies.append(data+bytes(count*4096-len(data)));sector+=count
 (dest/'region'/f'r.{rx}.{rz}.mca').write_bytes(header+b''.join(bodies))
level=n.load(C/'input/template_level.dat');d=level['Data'];d['LevelName']=n.String('Hiyori Old Town 18 - '+RUN);d['SpawnX']=n.Int(6+offset[0]);d['SpawnY']=n.Int(65);d['SpawnZ']=n.Int(68+offset[2]);d['SpawnAngle']=n.Float(-90);d['GameType']=n.Int(1);d['allowCommands']=n.Byte(1);d['Time']=n.Long(6000);d['DayTime']=n.Long(6000);d['raining']=n.Byte(0);d['thundering']=n.Byte(0);d.pop('Player',None)
d['GameRules'].update({'doDaylightCycle':n.String('false'),'doWeatherCycle':n.String('false'),'doMobSpawning':n.String('false'),'randomTickSpeed':n.String('0')});d['LastPlayed']=n.Long(int(time.time()*1000));level.save(dest/'level.dat')
# Independently decompress stored MCA and compare every scene cell, including air.
mismatch=checked=0;count_chunks=0
for p in (dest/'region').glob('*.mca'):
 raw=p.read_bytes()
 for i in range(1024):
  off=int.from_bytes(raw[i*4:i*4+3],'big')*4096
  if not off:continue
  size=int.from_bytes(raw[off:off+4],'big');assert raw[off+4]==2
  c=n.File.parse(io.BytesIO(zlib.decompress(raw[off+5:off+4+size])));key=(int(c['xPos']),int(c['zPos']));count_chunks+=1
  if key not in expected:continue
  sec={int(s['Y']):s for s in c['sections']};arr=np.concatenate([decode(sec[sy]) for sy in range(3,7)])[12:60]
  mismatch+=int(np.sum(arr!=expected[key]));checked+=arr.size
report=dict(version='Java 1.21.1',data_version=3955,source_nbt_sha256=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),world_offset=list(offset),spawn=[6+offset[0],65,68+offset[2]],chunks=count_chunks,scene_chunks=len(by),checked_cells=checked,mismatches=mismatch,lighting='isLightOn=0; game must recalculate on first load',game='pending',heightmaps='authored approximations; actual collision/light pending game',decorative=['furniture'],banner_block_entities=sum('_wall_banner' in st for st in rb.blocks.values()))
(R/'world_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));assert mismatch==0
(dest/'READ_ME.txt').write_text('日和旧街 18栋 / Java 1.21.1\n解压后，将此文件夹放进 Minecraft saves。默认创造模式，出生点 -74 65 4。\n白天 /time set day；夜景 /time set night。\n原版方块，不需要模组。预览不等于实机验收；首次加载须让游戏重新计算光照。家具为装饰；未测试实机门与楼梯交互。\n为稳定场景已关闭随机刻、天气和昼夜循环，可自行重新开启。\n',encoding='utf-8')
