"""Small classical-building primitives used by the London V1 cases.

These are authored construction rules, not a style classifier or survey model.
Every window has an actual opening, a recessed pane, a frame and a room-back.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from hafusion.site_scene import SiteScene
from hafusion.lighting import room_lighting
from hafusion.interiors import room_style, furnishing_cells
from detail_lab import states
M=states.make

def mask_polygon(size,points):
    im=Image.new('1',size);ImageDraw.Draw(im).polygon(points,fill=1)
    return np.asarray(im,dtype=bool)

def erode(mask,r=1):
    return np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MinFilter(r*2+1)))>0

class Builder:
    def __init__(self,size,seed=20261023):
        self.s=SiteScene(tuple(size));self.seed=seed;self.rooms=[];self.windows=[]
    def put(self,x,y,z,mat,owner,empty=False):
        q=tuple(math.floor(v+.5) for v in (x,y,z))
        if empty and q in self.s.blocks:return False
        self.s.set(q,mat if mat.startswith('minecraft:') else M(mat),owner);return True
    def box(self,lo,hi,mat,owner):
        self.s.fill(tuple(map(int,lo)),tuple(map(int,hi)),mat if mat.startswith('minecraft:') else M(mat),owner)
    def line(self,a,b,mat,owner):
        a=np.array(a,float);b=np.array(b,float);n=max(1,int(max(abs(b-a))*3))
        for t in np.linspace(0,1,n+1):self.put(*(a+(b-a)*t),mat,owner)
    def disk(self,x,z,r,y,mat,owner,inner=0):
        for zz in range(math.floor(z-r),math.ceil(z+r)):
            for xx in range(math.floor(x-r),math.ceil(x+r)):
                if inner**2<=(xx+.5-x)**2+(zz+.5-z)**2<=r*r:self.put(xx,y,zz,mat,owner)
    def surface(self,mask,y,mat,owner):
        for z,x in zip(*np.where(mask)):self.put(int(x),y,int(z),mat,owner)
    def frame(self,x,z,normal):return Facade(self,x,z,normal)
    def hip_roof(self,rect,y,rise,mat,owner):
        x0,z0,x1,z1=rect
        for z in range(z0,z1):
            for x in range(x0,x1):
                inset=min(x-x0,x1-1-x,z-z0,z1-1-z)
                yy=y+min(rise,inset//2)
                self.put(x,yy,z,mat,owner)
                if inset%2==0:self.put(x,yy+1,z,M('polished_deepslate_slab'),owner+'.tiles')
    def tree(self,x,z,y,h=15,r=6):
        self.line((x,y,z),(x,y+h-3,z),'oak_log','site.tree.trunk')
        for yy in range(y+h-7,y+h+2):
            for xx in range(x-r,x+r+1):
                for zz in range(z-r,z+r+1):
                    if ((xx-x)/r)**2+((zz-z)/r)**2+((yy-y-h+3)/5)**2<1:
                        self.put(xx,yy,zz,'oak_leaves','site.tree.leaves',empty=True)
    def lamp(self,x,z,y):
        self.line((x,y,z),(x,y+7,z),'iron_bars','lighting.site.post')
        for dx in [-2,2]:
            self.line((x,y+6,z),(x+dx,y+7,z),'iron_bars','lighting.site.arm')
            self.put(x+dx,y+8,z,'glowstone','lighting.site.lamp')
            self.put(x+dx,y+9,z,M('polished_deepslate_slab'),'lighting.site.cap')
    def finish(self):
        updates=states.connect(self.s)
        for s in set(self.s.blocks.values()):states.validate(s)
        return updates

class Facade:
    """u increases to the viewer's right; positive depth points OUTWARD."""
    def __init__(self,b,x,z,normal):
        self.b=b;self.x=x;self.z=z;self.n=normal;self.t=(normal[1],-normal[0])
    def xyz(self,u,y,d=0):return (self.x+self.t[0]*u+self.n[0]*d,y,self.z+self.t[1]*u+self.n[1]*d)
    def put(self,u,y,d,mat,owner,empty=False):return self.b.put(*self.xyz(u,y,d),mat,owner,empty)
    def rect(self,u0,u1,y0,y1,d0,d1,mat,owner):
        for u in range(u0,u1):
            for y in range(y0,y1):
                for d in range(d0,d1):self.put(u,y,d,mat,owner)
    def line(self,a,b,mat,owner):self.b.line(self.xyz(*a),self.xyz(*b),mat,owner)
    def pediment(self,u,y,width,rise,mat='smooth_quartz',owner='facade.pediment'):
        half=width/2
        for uu in range(math.floor(u-half),math.ceil(u+half)+1):
            h=max(0,math.floor(rise*(1-abs(uu-u)/half)))
            self.rect(uu,uu+1,y,y+h+1,0,2,mat,owner+'.tympanum')
            self.put(uu,y+h+1,2,M('smooth_quartz_slab' if 'quartz' in mat else 'smooth_sandstone_slab'),owner+'.raking_cornice')
        self.rect(math.floor(u-half)-1,math.ceil(u+half)+2,y-1,y,0,3,mat,owner+'.base')
    def column(self,u,y,h,width=2,mat='smooth_quartz',owner='facade.column'):
        self.rect(u,u+width,y,y+h,1,3,mat,owner+'.shaft')
        for yy in [y,y+1,y+h-2,y+h-1]:self.rect(u-1,u+width+1,yy,yy+1,0,4,mat,owner+'.capital_base')
        # Thin edge shafts make a shadow line without turning every bay into bars.
        for uu in [u-1,u+width]:
            for yy in range(y+3,y+h-3):self.put(uu,yy,2,M('diorite_wall'),owner+'.flute')
    def balustrade(self,u0,u1,y,mat='smooth_quartz',owner='facade.balustrade'):
        slab=M('smooth_quartz_slab' if 'quartz' in mat else 'smooth_sandstone_slab')
        for u in range(u0,u1):
            self.put(u,y,1,slab,owner+'.base');self.put(u,y+3,1,slab,owner+'.rail')
            if (u-u0)%2==0:
                for yy in [y+1,y+2]:self.put(u,yy,1,M('diorite_wall'),owner+'.baluster')
    def window(self,u,y,width,height,owner,*,stone='smooth_quartz',arched=False,pediment=False,room=True,floor_y=None):
        lo=math.floor(u-width/2);hi=lo+width
        # Actual masonry void: no glass painted on the outside of a solid wall.
        for uu in range(lo,hi):
            top=y+height
            if arched:top-=max(0,int(abs(uu+.5-u)-width*.22))
            self.rect(uu,uu+1,y,top,-3,1,'minecraft:air',owner+'.opening')
            self.rect(uu,uu+1,y,top,-1,0,'gray_stained_glass_pane',owner+'.glazing')
        self.rect(lo-1,lo,y-1,y+height+1,0,1,stone,owner+'.jamb')
        self.rect(hi,hi+1,y-1,y+height+1,0,1,stone,owner+'.jamb')
        slab=M('smooth_quartz_slab' if 'quartz' in stone else 'smooth_sandstone_slab')
        for uu in range(lo-1,hi+1):
            self.put(uu,y-1,1,slab,owner+'.sill')
            self.put(uu,y+height,1,slab,owner+'.lintel')
            if height>=6:self.put(uu,y+height//2,-1,M('iron_trapdoor',half='top'),owner+'.sash_rail')
        if width>=4:
            for yy in range(y,y+height):self.put(lo+width//2,yy,-1,'white_stained_glass_pane',owner+'.sash_mullion')
        if pediment:self.pediment(u,y+height+2,width+3,2,stone,owner+'.pediment')
        self.b.windows.append({'id':owner,'opening_anchor':list(self.xyz(u,y,0)),'size':[width,height],'normal_xz':self.n,'glass_recess_blocks':1})
        if not room:return
        fy=y-2 if floor_y is None else floor_y
        # Window-back alcoves use stable IDs; no claim to real room plans.
        self.rect(lo,hi,fy+1,y+height+2,-9,-2,'minecraft:air',owner+'.room.void')
        self.rect(lo-1,hi+1,fy,fy+1,-10,-2,'dark_oak_planks',owner+'.room.floor')
        self.rect(lo-1,hi+1,fy+1,y+height+2,-10,-9,stone,owner+'.room.back')
        self.rect(lo-1,lo,fy+1,y+height+2,-9,-2,stone,owner+'.room.side')
        self.rect(hi,hi+1,fy+1,y+height+2,-9,-2,stone,owner+'.room.side')
        style=room_style(self.b.seed,owner,height,'residential')
        for xx,yy,zz,mat in furnishing_cells(style['style'],height):
            self.put(lo+xx,fy+1+yy,-5-zz,mat,owner+'.room.furniture',empty=True)
        decision=room_lighting(self.b.seed,str(fy),owner,'palace',.34,namespace='london-v1')
        # Style's warm share applies only to synthetic room lighting.
        placed=False
        if decision['lit']:placed=self.put(u,y+height,-5,style['light'],owner+'.room.light',empty=True)
        self.b.rooms.append({'id':owner,'floor_y':fy,'style':style,'occupancy':decision,'actual_lamp':style['light'] if placed else None,'fidelity':'synthetic window-back furnishings'})
