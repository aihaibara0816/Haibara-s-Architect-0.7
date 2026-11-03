"""Export a verified Sponge v3 copy plus <=256KiB sparse NBT modules.

Sponge spec: https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-3.md
The preserved reader is used for readback; the dense schematic is streamed into
non-air entries so a 320m site's empty sky does not create 31 million dict rows.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,math,shutil,struct,sys
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.site_scene import SiteScene
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build,read_nbt,decode_varints,Limits
LIMITS=Limits(cells=40_000_000,nodes=64_000_000)

def text(s):
    b=s.encode('ascii');return struct.pack('>H',len(b))+b

def payload(t,v):
    if t==2:return struct.pack('>H',v)
    if t==3:return struct.pack('>i',v)
    if t==7:return struct.pack('>i',len(v))+v
    if t==8:return text(v)
    if t==9:
        kind,ls=v;return bytes([kind])+struct.pack('>i',len(ls))+b''.join(payload(kind,x) for x in ls)
    if t==10:return b''.join(bytes([kind])+text(n)+payload(kind,x) for n,(kind,x) in v.items())+b'\0'
    if t==11:return struct.pack('>i',len(v))+b''.join(struct.pack('>i',x) for x in v)
    raise ValueError(t)

def varint(i):
    b=bytearray()
    while i>=128:b.append((i&127)|128);i>>=7
    b.append(i);return b

def write_schem(build,path):
    names=['minecraft:air']+sorted(set(build.blocks.values())-{'minecraft:air'});ids={s:i for i,s in enumerate(names)}
    w,h,d=build.size;data=bytearray();at=0
    for n,s in sorted((x+z*w+y*w*d,s) for (x,y,z),s in build.blocks.items()):
        data.extend(b'\0'*(n-at));data.extend(varint(ids[s]));at=n+1
    data.extend(b'\0'*(w*h*d-at))
    schema={'Version':(3,3),'DataVersion':(3,3955),'Width':(2,w),'Height':(2,h),'Length':(2,d),
        'Offset':(11,[0,0,0]),'Metadata':(10,{'Name':(8,'Namsan Tower HAF V1'),'Author':(8,'HaibaraAi / HAF 0.2')}),
        'Blocks':(10,{'Palette':(10,{s:(3,i) for s,i in ids.items()}),'Data':(7,bytes(data)),'BlockEntities':(9,(10,[]))}),
        'Entities':(9,(10,[]))}
    raw=b'\x0a\0\0'+payload(10,{'Schematic':(10,schema)})
    with path.open('xb') as f:f.write(gzip.compress(raw,compresslevel=9,mtime=0))
    # Independent generic NBT reader + independent existing varint decoder.
    root,info=read_nbt(path,LIMITS);s=root['Schematic'];pal={i:k for k,i in s['Blocks']['Palette'].items()};nonair={}
    for n,i in enumerate(decode_varints(s['Blocks']['Data'],w*h*d)):
        if i not in pal:raise ValueError('unknown schematic palette reference')
        if pal[i]!='minecraft:air':nonair[(n%w,n//(w*d),(n//w)%d)]=pal[i]
    assert nonair==build.blocks and [s['Width'],s['Height'],s['Length']]==list(build.size)
    return {'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'format':'Sponge schematic v3','contains_explicit_air':True,'nonair_readback_exact':True,'non_air_blocks':len(nonair)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=CASE/'runs'/a.run;out=run/'import_pack'
    if out.exists():raise SystemExit('Refusing to overwrite '+str(out))
    out.mkdir();modules=out/'modules';modules.mkdir();b=load_build(run/'building.nbt',LIMITS)
    shutil.copy2(run/'building.nbt',out/'Namsan_Tower_HAF_V1.nbt');shutil.copy2(run/'materials.csv',out/'materials.csv')
    print('schematic export and readback',flush=True);sm=write_schem(b,out/'Namsan_Tower_HAF_V1.schem')
    rows=[];union={};serial=0
    def emit(cells,lo,hi,label):
        if not cells:return
        nonlocal serial
        size=tuple(hi[i]-lo[i] for i in range(3));scene=SiteScene(size)
        for p,s in cells.items():scene.set(tuple(p[i]-lo[i] for i in range(3)),s,'module')
        path=modules/(label+'.nbt');meta=export_structure(scene,path,include_air=False)
        if path.stat().st_size>256*1024:
            path.unlink();axis=max(range(3),key=lambda i:size[i]);mid=(lo[axis]+hi[axis])//2
            if mid==lo[axis]:raise ValueError('cannot split module further')
            mhi=list(hi);mhi[axis]=mid;mlo=list(lo);mlo[axis]=mid
            emit({q:s for q,s in cells.items() if q[axis]<mid},lo,tuple(mhi),label+'a')
            emit({q:s for q,s in cells.items() if q[axis]>=mid},tuple(mlo),hi,label+'b');return
        rb=load_build(path,LIMITS)
        for q,s in rb.blocks.items():
            p=tuple(q[i]+lo[i] for i in range(3))
            if p in union:raise ValueError('module overlap')
            union[p]=s
        rows.append({'file':'modules/'+path.name,'offset_xyz':list(lo),**{k:v for k,v in meta.items() if k!='file'}})
        print('module',path.name,path.stat().st_size,flush=True)
    # Four quadrants; adaptive vertical/horizontal splitting keeps import sizes low.
    for xi in range(2):
        for zi in range(2):
            lo=(xi*160,0,zi*160);hi=((xi+1)*160,b.size[1],(zi+1)*160)
            emit({q:s for q,s in b.blocks.items() if lo[0]<=q[0]<hi[0] and lo[2]<=q[2]<hi[2]},lo,hi,f'q{xi}{zi}')
    assert union==b.blocks
    index={'source_nbt_sha256':hashlib.sha256((run/'building.nbt').read_bytes()).hexdigest(),'size_xyz':list(b.size),
        'schematic':sm,'modules':rows,'module_count':len(rows),'module_union_exact':True,'module_max_bytes':max(q['bytes'] for q in rows),
        'coordinate_convention':'Each module lower corner = chosen project origin + offset_xyz; no rotation; X east, -Z north',
        'tested':'readback and exact coordinate/state union only; not imported into Minecraft'}
    (out/'import_manifest.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
    (out/'module_offsets.csv').write_text('file,x,y,z,size_x,size_y,size_z,bytes\n'+''.join(q['file']+','+','.join(map(str,q['offset_xyz']+q['size_xyz']+[q['bytes']]))+'\n' for q in rows))
    print(json.dumps({'schem_bytes':sm['bytes'],'modules':len(rows),'module_union_exact':True}),flush=True)

if __name__=='__main__':main()
