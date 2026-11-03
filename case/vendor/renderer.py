"""Orthographic CPU z-buffer renderer of in-memory voxel blocks, five fixed cameras.

Full cubes, slabs and straight stairs use the existing BuildKit block-part model.
Glass uses an opaque schematic
color; emission, game textures, ambient occlusion and collision are not simulated.
"""
from pathlib import Path
import math, hashlib, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import voxel_core as core

VIEWS={
    "front":((1,0,0),(0,1,0),(0,0,-1)),
    "back":((-1,0,0),(0,1,0),(0,0,1)),
    "left":((0,0,-1),(0,1,0),(-1,0,0)),
    "right":((0,0,1),(0,1,0),(1,0,0)),
    # Horizontal azimuth 45 deg from -Z toward +X; camera elevation 45 deg.
    "iso45":((2**-.5,0,2**-.5),(-.5,2**-.5,.5),(.5,2**-.5,-.5))
}
LABELS={"front":"FRONT / MODEL -Z","back":"BACK / MODEL +Z","left":"LEFT / -X","right":"RIGHT / +X","iso45":"ISO / AZIMUTH 45 / ELEVATION 45"}
FACES=[((-1,0,0),(0,4,7,3)),((1,0,0),(1,2,6,5)),((0,-1,0),(0,1,5,4)),((0,1,0),(3,7,6,2)),((0,0,-1),(0,3,2,1)),((0,0,1),(4,5,6,7))]
CORNERS=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)],dtype=float)

def font(size):
    paths=["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arial.ttf","/System/Library/Fonts/Helvetica.ttc"]
    for p in paths:
        if Path(p).is_file(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def triangle(buf, depth, vertices, color):
    x0=max(0,int(math.floor(vertices[:,0].min())))
    x1=min(buf.shape[1]-1,int(math.ceil(vertices[:,0].max())))
    y0=max(0,int(math.floor(vertices[:,1].min())))
    y1=min(buf.shape[0]-1,int(math.ceil(vertices[:,1].max())))
    if x1<x0 or y1<y0:return
    a,b,c=vertices
    den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-10:return
    xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
    v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
    w=1-u-v
    z=u*a[2]+v*b[2]+w*c[2]
    area=depth[y0:y1+1,x0:x1+1]
    mask=(u>=-1e-7)&(v>=-1e-7)&(w>=-1e-7)&(z>area)
    area[mask]=z[mask]
    buf[y0:y1+1,x0:x1+1][mask]=color

def render_view(build, spec, view, path, build_id, geometry_sha, resolution=(760,1900)):
    width,height=resolution
    image=np.full((height,width,3),[40,55,59],dtype=np.uint8)
    zbuf=np.full((height,width),-np.inf,dtype=float)
    right,up,camera=map(np.array,VIEWS[view])
    points=np.array([np.array(build.size)*v for v in CORNERS])
    projected=np.stack([points@right,points@up],axis=1)
    lo,hi=projected.min(axis=0),projected.max(axis=0)
    zoom=min((width-150)/max(1,hi[0]-lo[0]),(height-230)/max(1,hi[1]-lo[1]))
    cx=(width-(hi[0]+lo[0])*zoom)/2
    cy=height-110+(lo[1])*zoom
    # Store the actual camera transform in both PNG metadata and render_report.
    metadata={"view":view,"projection":"orthographic","right":right.tolist(),"up":up.tolist(),"camera_direction":camera.tolist(),"pixels_per_block":zoom,"build_id":build_id,"geometry_sha256":geometry_sha,"source":"nbt_readback","glass":"opaque_schematic_color","lighting":"directional_face_shading_only"}
    colors={m["block_state"]:np.array([int(m["preview_color"][i:i+2],16) for i in (1,3,5)]) for m in spec["materials"].values()}
    blocks={p:s for p,s in build.blocks.items() if s!=core.AIR}
    light=np.array([-.35,.85,-.40]);light=light/np.linalg.norm(light)
    faces=0
    parts_cache={s:core.block_parts(s) for s in set(blocks.values())}
    full=[(0,0,0,1,1,1)]
    for (x,y,z),state in sorted(blocks.items()):
        parts=parts_cache[state]
        for bx0,by0,bz0,bx1,by1,bz1 in parts:
            verts=CORNERS*np.array([bx1-bx0,by1-by0,bz1-bz0])+np.array([x+bx0,y+by0,z+bz0])
            for normal,indices in FACES:
                normal=np.array(normal)
                if normal@camera<=1e-9:continue
                neighbor=blocks.get(tuple(np.array([x,y,z])+normal))
                if parts==full and neighbor and parts_cache[neighbor]==full:continue
                v=verts[list(indices)]
                xy=np.stack([v@right*zoom+cx,cy-v@up*zoom,v@camera],axis=1)
                variation=(((x*73856093^y*19349663^z*83492791)&15)-7.5)*.004
                shade=.76+.22*max(0,float(normal@light))+variation
                color=np.clip(colors[state]*shade,0,255).astype(np.uint8)
                triangle(image,zbuf,xy[[0,1,2]],color)
                triangle(image,zbuf,xy[[0,2,3]],color)
                faces+=1
    result=Image.fromarray(image)
    draw=ImageDraw.Draw(result)
    draw.rectangle((0,0,width,94),fill="#132B2D")
    draw.text((34,20),"GAFAcraft  /  ARCHITECT",font=font(25),fill="#FFFFFF")
    draw.text((35,57),f'{spec["spec_id"]}  |  {LABELS[view]}',font=font(17),fill="#BFD4C9")
    draw.line((34,height-69,width-34,height-69),fill="#536C70",width=1)
    draw.text((35,height-54),f'NBT geometry / {len(blocks):,} blocks in this view',font=font(17),fill="#D2DFDD")
    draw.text((35,height-29),f'{geometry_sha[:16]}  |  schematic colors; no game validation',font=font(13),fill="#9DB4B2")
    pngmeta=PngImagePlugin.PngInfo()
    metadata['block_geometry']='BuildKit full cubes, half slabs, straight stairs; not game engine mesh'
    for key,value in metadata.items():pngmeta.add_text(key,str(value))
    payload=io.BytesIO()
    result.save(payload,format="PNG",pnginfo=pngmeta)
    Path(path).write_bytes(payload.getvalue())
    with Image.open(path) as check:check.verify()
    return {**metadata,"file":Path(path).name,"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),"rendered_faces":faces,"non_background_pixels":int(np.isfinite(zbuf).sum()),"solid_pixel_bounds":[int(np.where(np.isfinite(zbuf))[1].min()),int(np.where(np.isfinite(zbuf))[0].min()),int(np.where(np.isfinite(zbuf))[1].max()),int(np.where(np.isfinite(zbuf))[0].max())],"resolution":list(resolution)}

def render_views(build,spec,out,build_id,geometry_sha):
    return [render_view(build,spec,v,Path(out)/f"preview_{v}.png",build_id,geometry_sha) for v in spec["output"]["views"]]

