"""CPU triangle z-buffer previews of imported geometry; no generated imagery."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .model_io import world_meshes, selected_nodes

def preview(asset,output,roots=None):
    output=Path(output)
    if output.exists():raise ValueError('Preview exists')
    parts=list(world_meshes(asset,roots))
    if not parts:raise ValueError('Nothing to preview')
    vertices=np.vstack([x[2] for x in parts]);lo,hi=vertices.min(0),vertices.max(0);center=(lo+hi)/2
    cameras=[('LOCAL -Z',np.array([1.,0,0]),np.array([0.,1,0])),('LOCAL +X',np.array([0.,0,1]),np.array([0.,1,0])),('OBLIQUE',np.array([.70710678,0,.70710678]),np.array([-.24184476,.93969262,.24184476]))]
    width,height=1500,1080;canvas=Image.new('RGB',(width,height),'#f1f4ef');draw=ImageDraw.Draw(canvas)
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    except OSError:font=small=ImageFont.load_default()
    draw.rectangle((0,0,width,98),fill='#193c38');draw.text((30,22),'GAFAcraft / Imported model geometry',fill='white',font=font)
    draw.text((30,58),asset.document['model_id']+' | metres, Y-up | original origin retained',fill='#c8dfd6',font=small)
    for k,(name,right,up) in enumerate(cameras):
        forward=-np.cross(right,up);basis=np.stack([right,up,forward]);proj=(vertices-center)@basis.T
        span=proj.max(0)-proj.min(0);scale=min(420/max(span[0],1e-8),850/max(span[1],1e-8))
        W,H=480,920;buf=np.full((H,W,3),[241,244,239],dtype=np.uint8);depth=np.full((H,W),-np.inf)
        for n,m,v,f in parts:
            p=(v-center)@basis.T;p[:,:2]*=scale;p[:,0]+=W/2;p[:,1]=H/2-p[:,1]
            for face in f:
                tri=p[face];x,y=tri[:,0],tri[:,1]
                det=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
                if abs(det)<1e-9:continue
                x0=max(0,int(np.floor(x.min())));x1=min(W-1,int(np.ceil(x.max())))
                y0=max(0,int(np.floor(y.min())));y1=min(H-1,int(np.ceil(y.max())))
                if x1<x0 or y1<y0:continue
                xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
                a=((y[1]-y[2])*(xx-x[2])+(x[2]-x[1])*(yy-y[2]))/det
                b=((y[2]-y[0])*(xx-x[2])+(x[0]-x[2])*(yy-y[2]))/det;c=1-a-b
                z=a*tri[0,2]+b*tri[1,2]+c*tri[2,2]
                target=depth[y0:y1+1,x0:x1+1];mask=(a>=-1e-9)&(b>=-1e-9)&(c>=-1e-9)&(z>target)
                target[mask]=z[mask]
                w=v[face];normal=np.cross(w[1]-w[0],w[2]-w[0]);length=np.linalg.norm(normal)
                light=.66+.34*abs(np.dot(normal/length,[.3,.85,-.43])) if length else .7
                color=np.clip(np.asarray([174,190,184])*light,0,255).astype(np.uint8)
                buf[y0:y1+1,x0:x1+1][mask]=color
        canvas.paste(Image.fromarray(buf),(10+k*500,135));draw.text((25+k*500,108),name,font=small,fill='#193c38')
    dimensions=' x '.join(f'{x:.3f}' for x in hi-lo)
    draw.rectangle((0,1030,width,height),fill='#e4ece5')
    draw.text((25,1044),f'Bounds: {dimensions} m | neutral geometry view; not material reproduction | no Minecraft generation',font=small,fill='#193c38')
    canvas.save(output)

