"""Orthographic CPU z-buffer renderer of exported NBT blocks, five fixed cameras.

All currently supported materials are full cubes. Glass uses an opaque schematic
color; emission, game textures, ambient occlusion and collision are not simulated.
"""
from pathlib import Path
import math, hashlib, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
from .legacy import core

VIEWS={
    "front":((1,0,0),(0,1,0),(0,0,-1)),
    "back":((-1,0,0),(0,1,0),(0,0,1)),
    "left":((0,0,-1),(0,1,0),(-1,0,0)),
    "right":((0,0,1),(0,1,0),(1,0,0)),
    # Horizontal azimuth 45 deg from -Z toward +X; camera elevation 45 deg.
    "iso45":((2**-.5,0,2**-.5),(-.5,2**-.5,.5),(.5,2**-.5,-.5))
}
LABELS={"front":"FRONT / -Z","back":"BACK / +Z","left":"LEFT / -X","right":"RIGHT / +X","iso45":"ISO / AZIMUTH 45 / ELEVATION 45"}
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

def render_view(build, spec, view, path, build_id, geometry_sha, resolution=(1280,1000)):
    width,height=resolution
    image=np.full((height,width,3),[242,244,242],dtype=np.uint8)
    zbuf=np.full((height,width),-np.inf,dtype=float)
    right,up,camera=map(np.array,VIEWS[view])
    points=np.array([np.array(build.size)*v for v in CORNERS])
    projected=np.stack([points@right,points@up],axis=1)
    lo,hi=projected.min(axis=0),projected.max(axis=0)
    zoom=min((width-150)/max(1,hi[0]-lo[0]),(height-230)/max(1,hi[1]-lo[1]))
    cx=(width-(hi[0]+lo[0])*zoom)/2
    cy=height-110+(lo[1])*zoom
    # Store the actual camera transform in both PNG metadata and render_report.
    metadata={"view":view,"projection":"orthographic","right":right.tolist(),"up":up.tolist(),"camera_direction":camera.tolist(),"pixels_per_block":zoom,"build_id":build_id,"geometry_sha256":geometry_sha,"source":"NBT_readback","glass":"opaque_schematic_color","lighting":"directional_face_shading_only"}
    colors={m["block_state"]:np.array([int(m["preview_color"][i:i+2],16) for i in (1,3,5)]) for m in spec["materials"].values()}
    blocks={p:s for p,s in build.blocks.items() if s!=core.AIR}
    light=np.array([-.35,.85,-.40]);light=light/np.linalg.norm(light)
    faces=0
    for (x,y,z),state in sorted(blocks.items()):
        verts=CORNERS+np.array([x,y,z])
        for normal,indices in FACES:
            normal=np.array(normal)
            if normal@camera<=1e-9:continue
            if tuple(np.array([x,y,z])+normal) in blocks:continue
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
    draw.rectangle((0,0,width,94),fill="#183B39")
    draw.text((34,20),"GAFAcraft  /  ARCHITECT",font=font(25),fill="#FFFFFF")
    draw.text((35,57),f'{spec["spec_id"]}  |  {LABELS[view]}',font=font(17),fill="#BFD4C9")
    draw.line((34,height-69,width-34,height-69),fill="#CAD4CC",width=1)
    draw.text((35,height-54),f'{build.size[0]} x {build.size[1]} x {build.size[2]} blocks  /  {len(blocks):,} non-air  /  NBT-derived',font=font(17),fill="#365452")
    draw.text((35,height-29),f'{geometry_sha[:20]}  |  schematic colors; game validation pending',font=font(13),fill="#667D78")
    pngmeta=PngImagePlugin.PngInfo()
    for key,value in metadata.items():pngmeta.add_text(key,str(value))
    payload=io.BytesIO()
    result.save(payload,format="PNG",pnginfo=pngmeta)
    Path(path).write_bytes(payload.getvalue())
    with Image.open(path) as check:check.verify()
    return {**metadata,"file":Path(path).name,"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),"rendered_faces":faces,"non_background_pixels":int(np.isfinite(zbuf).sum()),"resolution":list(resolution)}

def render_views(build,spec,out,build_id,geometry_sha):
    return [render_view(build,spec,v,Path(out)/f"preview_{v}.png",build_id,geometry_sha) for v in spec["output"]["views"]]

