"""Java 1.21.1 Anvil world from the final structure; no game execution claimed."""
from pathlib import Path
import sys,json,io,zlib,time,collections,hashlib,math
import numpy as np
import nbtlib as n
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import qilou_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
R=ROOT/'runs'/sys.argv[1];RUN=R.name;dest=Path(sys.argv[2]);assert not dest.exists()
(dest/'region').mkdir(parents=True)
rb=load_build(R/'Qilou01.nbt',Limits(cells=40_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024));offset=(-rb.size[0]//2,62,-rb.size[2]//2)
structure=n.load(R/'Qilou01.nbt');source_bes={}
source_entities=[]
for entity in structure.get('entities',[]):
 q=entity['nbt'].copy()
 q['Pos']=n.List[n.Double]([n.Double(float(v)+offset[i])for i,v in enumerate(q['Pos'])])
 for i,key in enumerate(['TileX','TileY','TileZ']):q[key]=n.Int(int(q[key])+offset[i])
 source_entities.append(q)
for e in structure['blocks']:
 if 'nbt' in e:
  q=e['nbt'].copy();p=tuple(int(e['pos'][i])+offset[i] for i in range(3));q.update({k:n.Int(v) for k,v in zip(['x','y','z'],p)});source_bes[p]=q
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
for cz in range(offset[2]//16-1,(offset[2]+rb.size[2]-1)//16+2):
 for cx in range(offset[0]//16-1,(offset[0]+rb.size[0]-1)//16+2):
  allarr=np.full((384,16,16),'minecraft:air',object)
  allarr[0,:,:]='minecraft:bedrock';allarr[1:125,:,:]='minecraft:stone';allarr[125:128,:,:]='minecraft:dirt';allarr[128,:,:]=states.make('grass_block')
  # Flat surroundings meet y=64; clear the complete source bounding volume.
  for z in range(16):
   for x in range(16):
    if offset[0]<=cx*16+x<offset[0]+rb.size[0] and offset[2]<=cz*16+z<offset[2]+rb.size[2]:allarr[126:126+rb.size[1],z,x]='minecraft:air'
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
  c=n.File({'DataVersion':n.Int(3955),'xPos':n.Int(cx),'zPos':n.Int(cz),'yPos':n.Int(-4),'Status':n.String('minecraft:full'),'LastUpdate':n.Long(0),'InhabitedTime':n.Long(0),'isLightOn':n.Byte(0),'sections':n.List[n.Compound](sections),'block_entities':n.List[n.Compound]([q for (bx,byy,bz),q in source_bes.items() if bx//16==cx and bz//16==cz]),'block_ticks':n.List[n.Compound]([]),'fluid_ticks':n.List[n.Compound]([]),'Heightmaps':hm,'PostProcessing':n.List[n.List[n.Short]]([n.List[n.Short]([]) for _ in range(24)]),'structures':n.Compound({'starts':n.Compound({}),'References':n.Compound({})})})
  regions[cx//32,cz//32][cx%32+32*(cz%32)]=c
  if (cx,cz) in by:expected[cx,cz]=allarr[126:126+rb.size[1]].copy()
for (rx,rz),cc in regions.items():
 header=bytearray(8192);bodies=[];sector=2
 for i,c in sorted(cc.items()):
  out=io.BytesIO();c.write(out);blob=zlib.compress(out.getvalue(),6);data=(len(blob)+1).to_bytes(4,'big')+b'\x02'+blob;count=math.ceil(len(data)/4096)
  header[i*4:i*4+3]=sector.to_bytes(3,'big');header[i*4+3]=count;header[4096+i*4:4100+i*4]=int(time.time()).to_bytes(4,'big');bodies.append(data+bytes(count*4096-len(data)));sector+=count
 (dest/'region'/f'r.{rx}.{rz}.mca').write_bytes(header+b''.join(bodies))
# Modern Anvil stores non-block entities in a separate entities/ region tree.
entity_chunks=collections.defaultdict(list)
for q in source_entities:entity_chunks[math.floor(float(q['Pos'][0]))//16,math.floor(float(q['Pos'][2]))//16].append(q)
entity_regions=collections.defaultdict(dict)
for (cx,cz),es in entity_chunks.items():entity_regions[cx//32,cz//32][cx%32+32*(cz%32)]=n.File({'DataVersion':n.Int(3955),'Position':n.IntArray([cx,cz]),'Entities':n.List[n.Compound](es)})
(dest/'entities').mkdir()
for (rx,rz),cc in entity_regions.items():
 header=bytearray(8192);bodies=[];sector=2
 for i,c in sorted(cc.items()):
  out=io.BytesIO();c.write(out);blob=zlib.compress(out.getvalue(),6);data=(len(blob)+1).to_bytes(4,'big')+b'\x02'+blob;count=math.ceil(len(data)/4096)
  header[i*4:i*4+3]=sector.to_bytes(3,'big');header[i*4+3]=count;header[4096+i*4:4100+i*4]=int(time.time()).to_bytes(4,'big');bodies.append(data+bytes(count*4096-len(data)));sector+=count
 (dest/'entities'/f'r.{rx}.{rz}.mca').write_bytes(header+b''.join(bodies))
loaded_entities=[]
for ep in (dest/'entities').glob('*.mca'):
 raw=ep.read_bytes()
 for i in range(1024):
  off=int.from_bytes(raw[i*4:i*4+3],'big')*4096
  if not off:continue
  size=int.from_bytes(raw[off:off+4],'big');ee=n.File.parse(io.BytesIO(zlib.decompress(raw[off+5:off+4+size])))
  for en in ee['Entities']:
   assert list(map(int,ee['Position']))==[math.floor(float(en['Pos'][j]))//16 for j in [0,2]]
   loaded_entities.append(en)
key=lambda q:tuple(map(int,q['UUID']))
assert sorted(source_entities,key=key)==sorted(loaded_entities,key=key)
spec=json.loads((R/'spec.json').read_text());spawn=[spec['spawn_local'][i]+offset[i] for i in range(3)]
level=n.load(ROOT/'input/template_level.dat');d=level['Data'];d['LevelName']=n.String('Qilou01 - '+RUN);d['SpawnX']=n.Int(spawn[0]);d['SpawnY']=n.Int(spawn[1]);d['SpawnZ']=n.Int(spawn[2]);d['SpawnAngle']=n.Float(180);d['GameType']=n.Int(1);d['allowCommands']=n.Byte(1);d['Time']=n.Long(6000);d['DayTime']=n.Long(6000);d['raining']=n.Byte(0);d['thundering']=n.Byte(0);d.pop('Player',None)
d['GameRules'].update({'doDaylightCycle':n.String('false'),'doWeatherCycle':n.String('false'),'doMobSpawning':n.String('false'),'randomTickSpeed':n.String('0')});d['GameRules']['spawnRadius']=n.String('0');d['LastPlayed']=n.Long(int(time.time()*1000));level.save(dest/'level.dat')
# Independently decompress stored MCA and compare every scene cell, including air.
mismatch=checked=0;count_chunks=0;world_bes={}
for p in (dest/'region').glob('*.mca'):
 raw=p.read_bytes()
 for i in range(1024):
  off=int.from_bytes(raw[i*4:i*4+3],'big')*4096
  if not off:continue
  size=int.from_bytes(raw[off:off+4],'big');assert raw[off+4]==2
  c=n.File.parse(io.BytesIO(zlib.decompress(raw[off+5:off+4+size])));key=(int(c['xPos']),int(c['zPos']));count_chunks+=1
  for be in c['block_entities']:world_bes[tuple(int(be[a]) for a in ['x','y','z'])]=be
  if key not in expected:continue
  sec={int(s['Y']):s for s in c['sections']};sy0=offset[1]//16;start=offset[1]-sy0*16;arr=np.concatenate([decode(sec[sy]) for sy in range(sy0,(offset[1]+rb.size[1]-1)//16+1)])[start:start+rb.size[1]]
  mismatch+=int(np.sum(arr!=expected[key]));checked+=arr.size
assert world_bes==source_bes
report=dict(block_entity_payload_exact=True,version='Java 1.21.1',data_version=3955,source_nbt_sha256=hashlib.sha256((R/'Qilou01.nbt').read_bytes()).hexdigest(),world_offset=list(offset),spawn=spawn,chunks=count_chunks,scene_chunks=len(by),checked_cells=checked,mismatches=mismatch,lighting='isLightOn=0; game must recalculate on first load',game='pending',heightmaps='authored approximations; actual collision/light pending game',decorative=['furniture'],block_entities=len(source_bes))
report.update(entities=len(source_entities),entity_payload_exact=True,entity_chunks=len(entity_chunks))
(R/'world_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));assert mismatch==0
(dest/'READ_ME.txt').write_text('Qilou01 / Java 1.21.1\n西关骑楼三栋试作：杂货铺、药材铺与转角茶楼；连续风雨廊。\n解压本文件夹至 saves；原版方块，无必需模组。\n床、桶、熔炉与告示牌有原版数据；沙发、杯具为造型。\n离线回读检查完成，未运行客户端。首次加载需计算光照。\n/time set night 查看夜景。\n',encoding='utf-8')
