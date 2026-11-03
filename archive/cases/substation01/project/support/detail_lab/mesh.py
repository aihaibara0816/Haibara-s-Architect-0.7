"""NBT-readback preview meshes. Untextured visual approximations, not game models."""
from pathlib import Path
from collections import deque
import hashlib,json,os,tempfile
import numpy as np
from .states import boxes,transparent,color,family

CORNERS=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)],np.float32)
FACES=[((-1,0,0),(0,4,7,3)),((1,0,0),(1,2,6,5)),((0,-1,0),(0,1,5,4)),((0,1,0),(3,7,6,2)),((0,0,-1),(0,3,2,1)),((0,0,1),(4,5,6,7))]

def write_array_atomic(array,path):
    """Bounded writes; never publish a partial mesh, including on short writes."""
    path=Path(path);data=memoryview(np.ascontiguousarray(array)).cast('B')
    fd,temp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        offset=0
        while offset<len(data):
            n=os.write(fd,data[offset:offset+8*1024*1024])
            if n<=0:raise OSError('mesh write made no progress')
            offset+=n
        os.fsync(fd)
        if os.fstat(fd).st_size!=len(data):raise OSError('incomplete mesh write')
        os.close(fd);fd=None;os.replace(temp,path)
    finally:
        if fd is not None:os.close(fd)
        if os.path.exists(temp):os.unlink(temp)

def visible_face(part,fi,parts):
    axis=fi//2;positive=fi%2;plane=part[axis+3 if positive else axis]
    others=[i for i in range(3) if i!=axis]
    for q in parts:
        if q==part:continue
        opposite=q[axis if positive else axis+3]
        if abs(plane-opposite)<1e-8 and all(q[j]<=part[j] and q[j+3]>=part[j+3] for j in others):return False
    return True

def write_mesh(build,nbt_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);sx,sy,sz=build.size
    pal=sorted(set(build.blocks.values())|{'minecraft:air'});ids={s:i for i,s in enumerate(pal)}
    a=np.full((sy,sz,sx),ids['minecraft:air'],np.int32)
    for (x,y,z),s in build.blocks.items():a[y,z,x]=ids[s]
    full=np.array([boxes(s)==((0,0,0,1,1,1),) for s in pal]);opaque=full & np.array([not transparent(s) for s in pal])
    buckets={'opaque':[],'glass':[]};lamps=[];volume=0.
    for si,s in enumerate(pal):
        parts=boxes(s)
        if not parts:continue
        yy,zz,xx=np.where(a==si);pos=np.stack([xx,yy,zz],axis=1).astype(np.float32)
        if not len(pos):continue
        trans=transparent(s);emit=14 if 'end_rod' in s else 15 if any(q in s for q in ['sea_lantern','glowstone','minecraft:lantern']) else 7 if 'redstone_torch' in s and 'lit=true' in s else 0
        if emit:lamps.extend([int(x),int(y),int(z),emit] for x,y,z in pos)
        col=np.array(color(s),np.float32)/255;bucket=buckets['glass' if trans else 'opaque']
        for b in parts:
            volume+=len(pos)*float(np.prod(np.array(b[3:])-b[:3]))
            corners=CORNERS*(np.array(b[3:])-b[:3])+b[:3]
            for fi,(n,inds) in enumerate(FACES):
                if not visible_face(b,fi,parts):continue
                axis=fi//2;boundary=b[axis]==0 if fi%2==0 else b[axis+3]==1
                mask=np.ones(len(pos),bool)
                if boundary:
                    q=pos.astype(int)+n;inside=np.all((q>=0)&(q<np.array(build.size)),axis=1);ix=np.where(inside)[0]
                    neighbors=a[q[ix,1],q[ix,2],q[ix,0]]
                    # Full opaque neighbours hide either face; equal glass volumes also cull.
                    mask[ix]=~(full[neighbors] if trans else opaque[neighbors])
                pp=pos[mask]
                if not len(pp):continue
                verts=pp[:,None,:]+corners[np.array(inds)[[0,1,2,0,2,3]]][None,:,:]
                v=np.empty((len(pp),6,10),np.float32);v[:,:,:3]=verts;v[:,:,3:6]=n;v[:,:,6:9]=col;v[:,:,9]=1 if emit else 0
                bucket.append(v.reshape(-1,10))
    triangles={}
    for k,ls in buckets.items():
        arr=np.concatenate(ls) if ls else np.empty((0,10),np.float32);write_array_atomic(arr.astype('<f4'),out/(k+'.bin'));triangles[k]=len(arr)//3
    # Deliberately conservative cell approximation: slabs, stairs and closed
    # non-glass trapdoors block a whole cell of light. This prevents ceiling leak
    # but does not implement Minecraft's per-face light occlusion.
    blocked=opaque | np.array([family(s) in {'slab','stairs'} or family(s)=='trapdoor' and 'open=false' in s for s in pal])
    light=np.zeros((sz,sy,sx),np.uint8);queue=deque()
    for x,y,z,level in lamps:light[z,y,x]=level;queue.append((x,y,z,level))
    while queue:
        x,y,z,v=queue.popleft()
        if v<=1:continue
        for dx,dy,dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
            nx,ny,nz=x+dx,y+dy,z+dz
            if not (0<=nx<sx and 0<=ny<sy and 0<=nz<sz):continue
            if blocked[a[ny,nz,nx]] or light[nz,ny,nx]>=v-1:continue
            light[nz,ny,nx]=v-1;queue.append((nx,ny,nz,v-1))
    write_array_atomic(light,out/'blocklight.bin')
    meta={'source_nbt_sha256':hashlib.sha256(Path(nbt_path).read_bytes()).hexdigest(),'size_xyz':list(build.size),'triangles':triangles,'lamps':lamps,'visual_box_volume':round(volume,4),'source':'independent NBT readback, state-aware preview boxes','limitations':['No resource-pack textures','Glass alpha is approximate','Bars/chains/flowers are simplified solid boxes','Slabs/stairs/closed trapdoors conservatively block whole light cells','No game collision verification']}
    (out/'scene.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));return meta

def cameras(size,sample):
    w,h,d=size;cx=w/2;cz=d/2;target=[cx,h*.43,cz];ratio=1400/1050
    span=max(h*1.4,w/ratio*1.5,d*1.1)
    common={'width':1400,'height':1050,'fov':36,'ortho':True,'spanX':span*ratio,'spanZ':span,'concept':True}
    dist=max(size)*2.4
    views=[{**common,'id':'oblique','eye':[cx+dist*.8,h*.6+dist*.45,cz-dist],'target':target},
           {**common,'id':'front','eye':[cx,h*.47,cz-dist],'target':[cx,h*.47,cz]},
           {**common,'id':'night','eye':[cx+dist*.8,h*.6+dist*.45,cz-dist],'target':target,'night':True,'concept':False},
           {**common,'id':'cutaway','eye':[cx+dist,h*.5+dist*.5,cz-dist],'target':target,'cutX':int(w*.57)}]
    ps=max(d*1.2,w/ratio*1.2)
    views.append({**common,'id':'plan','eye':[cx,h+dist,cz],'target':[cx,0,cz],'spanX':ps*ratio,'spanZ':ps,'cutY':6 if sample not in ['antenna','framework'] else 19})
    if sample in ['modern','millennium','western']:
        detail=[min(w*.42,12),5.5,5];ds=12
    elif sample=='antenna':detail=[cx,25,cz];ds=20
    elif sample=='planter':detail=[10,3,10];ds=15
    elif sample=='chinese':detail=[14,7,6];ds=16
    elif sample=='framework':detail=[13,16,7];ds=16
    else:detail=[14,11,6];ds=18
    views.append({**common,'id':'detail','target':detail,'eye':[detail[0]+dist*.36,detail[1]+dist*.15,detail[2]-dist], 'spanX':ds*ratio,'spanZ':ds})
    return views
