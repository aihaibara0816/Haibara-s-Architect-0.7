"""Bounded-memory Java structure writer; used only for large T16 landscapes."""
import gzip,struct,copy
import nbtlib as n
from vendor.voxel_core import parse_state
def tag(out,name,value):
 b=name.encode();out.write(bytes([value.tag_id])+struct.pack('>H',len(b))+b);value.write(out)
def write(path,scene,bes,entities):
 states=sorted(set(scene.blocks.values()));ids={s:i for i,s in enumerate(states)};pal=[]
 for st in states:
  name,props=parse_state(st);v=n.Compound({'Name':n.String(name)})
  if props:v['Properties']=n.Compound({k:n.String(p)for k,p in props.items()})
  pal.append(v)
 with path.open('wb')as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9)as out:
  out.write(b'\x0a\0\0');tag(out,'DataVersion',n.Int(3955));tag(out,'size',n.List[n.Int](scene.size));tag(out,'palette',n.List[n.Compound](pal))
  out.write(b'\x09\0\x06blocks\x0a'+struct.pack('>i',len(scene.blocks)))
  for q in sorted(scene.blocks,key=lambda p:(p[1],p[2],p[0])):
   out.write(b'\x09\0\x03pos\x03\0\0\0\x03'+struct.pack('>3i',*q)+b'\x03\0\x05state'+struct.pack('>i',ids[scene.blocks[q]]))
   if q in bes:tag(out,'nbt',bes[q])
   out.write(b'\0')
  tag(out,'entities',n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(e['Pos']),'blockPos':n.List[n.Int]([e[k]for k in['TileX','TileY','TileZ']]),'nbt':e})for e in entities]));out.write(b'\0')
