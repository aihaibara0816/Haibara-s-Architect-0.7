"""Bounded block primitives, deterministic Java structure NBT export. No network/API.
Coordinates are X,Y,Z; boxes are half-open. Prototype, not a game validator.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import math, json, gzip, struct, hashlib, re
from typing import Iterable

VERSION = '0.3.0'
AIR='minecraft:air'
MAX_CELLS=1_000_000

def state(name:str, **properties:str)->str:
    if not re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+',name): raise ValueError('Invalid block ID')
    for k,v in properties.items():
        if not re.fullmatch(r'[a-z0-9_]+',k) or not isinstance(v,str) or not re.fullmatch(r'[a-z0-9_:.+-]+',v): raise ValueError('Invalid state property')
    return name+('['+','.join(k+'='+properties[k] for k in sorted(properties))+']' if properties else '')

def parse_state(s:str):
    if '[' in s:
        n,p=s[:-1].split('[',1)
        props=dict(x.split('=',1) for x in p.split(','))
    else: n,props=s,{}
    if state(n,**props)!=s: raise ValueError('Block states must be canonical and sorted')
    return n,props

def quantize(v:float)->int:
    if not math.isfinite(v): raise ValueError('Non-finite coordinate')
    return math.floor(v+0.5)

def repeated_axes(origin:float, pitch:float, count:int)->list[int]:
    if count<1 or pitch<=0: raise ValueError('Invalid repeated grid')
    a=[quantize(origin+i*pitch) for i in range(count)]
    if len(set(a))!=len(a): raise ValueError('Repeated axes collapse on block grid')
    return a

@dataclass
class Scene:
    size:tuple[int,int,int]
    blocks:dict=field(default_factory=dict)
    owners:dict=field(default_factory=dict)
    events:list=field(default_factory=list)
    max_cells:int=MAX_CELLS
    def __post_init__(self):
        self.size=tuple(self.size)
        if type(self.max_cells)!=int or not 1<=self.max_cells<=2_000_000: raise ValueError('Explicit scene budget must be between 1 and 2,000,000')
        if len(self.size)!=3 or any(type(v)!=int or v<1 for v in self.size) or math.prod(self.size)>self.max_cells: raise ValueError('Invalid/budget-exceeding size')
    def set(self,p,s,owner):
        p=tuple(p)
        if len(p)!=3 or any(type(v)!=int for v in p) or any(not 0<=p[i]<self.size[i] for i in range(3)): raise ValueError(f'Out of bounds: {p}')
        if not isinstance(owner,str) or not owner: raise ValueError('Component ID required')
        if s==AIR:
            self.blocks.pop(p,None);self.owners.pop(p,None)
        else:
            self.blocks[p]=s;self.owners[p]=owner
    def fill(self,lo,hi,s,owner):
        if len(lo)!=3 or len(hi)!=3 or any(type(v)!=int for v in (*lo,*hi)): raise ValueError('Integer box required')
        if any(lo[i]<0 or hi[i]>self.size[i] or lo[i]>=hi[i] for i in range(3)): raise ValueError('Invalid/out-of-bounds box')
        for y in range(lo[1],hi[1]):
            for z in range(lo[2],hi[2]):
                for x in range(lo[0],hi[0]):self.set((x,y,z),s,owner)
    def cylinder(self,cx,cz,r,y0,y1,s,owner):
        if r<=0 or y0>=y1:raise ValueError('Invalid cylinder')
        for x in range(math.floor(cx-r),math.ceil(cx+r)):
            for z in range(math.floor(cz-r),math.ceil(cz+r)):
                if (x+0.5-cx)**2+(z+0.5-cz)**2<=r*r:
                    self.fill((x,y0,z),(x+1,y1,z+1),s,owner)
    def snapshot(self):
        return Scene(self.size,dict(self.blocks),dict(self.owners),list(self.events),max_cells=self.max_cells)
    def fingerprint(self):
        return hashlib.sha256(json.dumps([list(self.size),[[*p,s] for p,s in sorted(self.blocks.items())]],separators=(',',':')).encode()).hexdigest()

# Minimal typed NBT writer. Strings emitted by this writer are ASCII IDs only;
# it intentionally refuses arbitrary Unicode rather than mis-encoding Java MUTF-8.
def _text(s):
    b=s.encode('ascii')
    if len(b)>65535:raise ValueError('NBT string too long')
    return struct.pack('>H',len(b))+b

def _payload(kind,value):
    if kind==3:return struct.pack('>i',value)
    if kind==8:return _text(value)
    if kind==9:
        item,vals=value
        return bytes([item])+struct.pack('>i',len(vals))+b''.join(_payload(item,v) for v in vals)
    if kind==10:return b''.join(bytes([t])+_text(n)+_payload(t,v) for n,(t,v) in value.items())+b'\0'
    raise ValueError('Writer supports only its documented tag subset')

def export_structure(scene:Scene,path:Path,data_version:int=3955,include_air:bool=True):
    if not scene.blocks:raise ValueError('Refusing to export an empty building')
    names=sorted(set(scene.blocks.values())|({AIR} if include_air else set()))
    palette=[]
    for s in names:
        n,props=parse_state(s);p={'Name':(8,n)}
        if props:p['Properties']=(10,{k:(8,v) for k,v in props.items()})
        palette.append(p)
    ids={s:i for i,s in enumerate(names)}
    entries=[]
    sx,sy,sz=scene.size
    coords=((x,y,z) for y in range(sy) for z in range(sz) for x in range(sx)) if include_air else sorted(scene.blocks,key=lambda p:(p[1],p[2],p[0]))
    for p in coords:
        st=scene.blocks.get(p,AIR)
        entry={'pos':(9,(3,list(p))),'state':(3,ids[st])}
        if '_wall_banner' in st:
            entry['nbt']=(10,{'id':(8,'minecraft:banner'),'patterns':(9,(10,[]))})
        entries.append(entry)
    root={'DataVersion':(3,data_version),'size':(9,(3,list(scene.size))),
          'palette':(9,(10,palette)),'blocks':(9,(10,entries)),'entities':(9,(10,[]))}
    raw=b'\x0a\0\0'+_payload(10,root)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    compressed=gzip.compress(raw,compresslevel=9,mtime=0)
    with path.open('xb') as f:f.write(compressed)
    return {'file':path.name,'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),
            'listed_blocks':len(entries),'non_air_blocks':len(scene.blocks),'size_xyz':list(scene.size),
            'contains_explicit_air':include_air,'geometry_sha256':scene.fingerprint(),'data_version':data_version}

# Approximate visual models, not Minecraft collision geometry.
def block_parts(s):
    name,p=parse_state(s)
    if name==AIR:return []
    if name.endswith('_slab'):
        ty=p.get('type','bottom')
        return [(0,0 if ty!='top' else .5,0,1,1 if ty!='bottom' else .5,1)]
    if name.endswith('_stairs'):
        if p.get('shape','straight')!='straight':raise ValueError('Preview supports only straight stairs')
        high={'east':(.5,0,1,1),'west':(0,0,.5,1),'north':(0,0,1,.5),'south':(0,.5,1,1)}[p.get('facing','north')]
        x0,z0,x1,z1=high
        if p.get('half','bottom')=='bottom':return [(0,0,0,1,.5,1),(x0,.5,z0,x1,1,z1)]
        return [(0,.5,0,1,1,1),(x0,0,z0,x1,.5,z1)]
    if name.endswith('_fence'):
        a=[(.375,0,.375,.625,1.5,.625)]
        for d,b in [('north',(.4375,0,0,.5625,0,.5)),('south',(.4375,0,.5,.5625,0,1)),('west',(0,0,.4375,.5,0,.5625)),('east',(.5,0,.4375,1,0,.5625))]:
            if p.get(d)=='true':
                for y0,y1 in [(.375,.5625),(.75,.9375)]:a.append((b[0],y0,b[2],b[3],y1,b[5]))
        return a
    return [(0,0,0,1,1,1)]

COLORS={'minecraft:red_terracotta':(153,72,48),'minecraft:terracotta':(155,96,72),
 'minecraft:gray_concrete':(81,86,84),'minecraft:polished_andesite':(121,126,119),
 'minecraft:polished_blackstone':(43,43,47),'minecraft:smooth_quartz':(233,231,218),
 'minecraft:smooth_quartz_slab':(233,231,218),'minecraft:quartz_stairs':(233,231,218),
 'minecraft:light_gray_concrete':(181,180,166),'minecraft:smooth_stone':(170,174,170),
 'minecraft:smooth_stone_slab':(174,179,175),'minecraft:stone_bricks':(126,133,128),
 'minecraft:black_stained_glass':(40,63,72),'minecraft:black_concrete':(33,38,36),
 'minecraft:nether_brick_fence':(57,37,36)}

def build_mesh(build):
    """Accepts a *read-back* Build, ensuring preview comes from exported NBT."""
    out=[]
    faces=[((-1,0,0),(0,4,7,3)),((1,0,0),(1,2,6,5)),((0,-1,0),(0,1,5,4)),
           ((0,1,0),(3,7,6,2)),((0,0,-1),(0,3,2,1)),((0,0,1),(4,5,6,7))]
    def is_full(s):return block_parts(s)==[(0,0,0,1,1,1)]
    for (x,y,z),s in build.blocks.items():
        if s==AIR:continue
        n,p=parse_state(s);color=COLORS.get(n,(202,66,179))
        parts=block_parts(s);full=parts==[(0,0,0,1,1,1)]
        for bx0,by0,bz0,bx1,by1,bz1 in parts:
            v=[(x+bx0,y+by0,z+bz0),(x+bx1,y+by0,z+bz0),(x+bx1,y+by1,z+bz0),(x+bx0,y+by1,z+bz0),
               (x+bx0,y+by0,z+bz1),(x+bx1,y+by0,z+bz1),(x+bx1,y+by1,z+bz1),(x+bx0,y+by1,z+bz1)]
            for norm,idx in faces:
                neighbor=build.blocks.get((x+norm[0],y+norm[1],z+norm[2]),AIR)
                if full and norm!=(0,1,0) and neighbor!=AIR and is_full(neighbor):continue
                # Deterministic, subtle per-block variation; not game textures.
                shade=1.+(((x*73856093^y*19349663^z*83492791)&15)-7.5)*.002
                c=[round(v/255*shade,5) for v in color]
                for k in [idx[0],idx[1],idx[2],idx[0],idx[2],idx[3]]:out.extend([*v[k],*norm,*c,float(y)])
    return out
