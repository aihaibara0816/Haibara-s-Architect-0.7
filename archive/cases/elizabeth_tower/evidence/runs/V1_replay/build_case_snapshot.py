"""Elizabeth Tower, 2 blocks/metre. Photo-based component adapter, HAF 0.2."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.classical import Builder,M
from hafusion.case_io import save_run

class Tower(Builder):
    def __init__(self,p):
        super().__init__(p['frame']['size_xyz'],p['seed']);self.p=p
        self.cx,self.cz=p['frame']['tower_center_xz'];self.g=p['frame']['ground_y']
    def faces(self,r=12):
        for n in [(0,-1),(1,0),(0,1),(-1,0)]:
            yield self.frame(self.cx+n[0]*r,self.cz+n[1]*r,n)
    def square_band(self,y,r,mat,owner):
        for f in self.faces(r):f.rect(-r,r+1,y,y+1,0,1,mat,owner)
    def ground(self):
        self.box((0,0,0),(100,2,96),'stone_bricks','site.foundation')
        self.box((0,2,0),(100,4,96),'smooth_stone','site.paving')
        # Light joint grid, kept subordinate to the tower.
        for x in range(0,100,10):self.box((x,3,0),(x+1,4,96),'polished_andesite','site.paving_joint')
        for z in range(0,96,10):self.box((0,3,z),(100,4,z+1),'polished_andesite','site.paving_joint')
        for x,z in [(12,12),(90,12),(90,82)]:self.lamp(x,z,4)
        for x,z in [(86,55),(86,68)]:
            self.box((x-3,4,z-2),(x+4,6,z+3),'cut_sandstone','site.planter')
            self.box((x-2,6,z-1),(x+3,8,z+2),'azalea_leaves','site.hedge')
    def context(self):
        # Cropped attached wing, not a claim to reproduce all neighbouring halls.
        rect=(8,47,74,90);x0,z0,x1,z1=rect;g=self.g
        self.box((x0,g,z0),(x1,g+47,z1),'smooth_sandstone','context.masonry')
        self.box((x0+2,g+1,z0+2),(x1-2,g+45,z1-2),'minecraft:air','context.void')
        for yy in [g,g+14,g+29,g+44]:self.box((x0,yy,z0),(x1,yy+1,z1),'oak_planks','context.floor')
        for z,n in [(z0,(0,-1)),(z1-1,(0,1))]:
            f=self.frame((x0+x1)//2,z,n)
            for u in range(-27,29,9):
                for y in [g+3,g+17,g+32]:f.window(u,y,4,9,f'context.window.{z}.{u}.{y}',stone='smooth_sandstone',arched=True,room=False)
            for u in range(-31,33,8):
                f.rect(u,u+1,g,g+49,1,2,'cut_sandstone','context.buttress')
                for yy in range(g+49,g+54):f.put(u,yy,1,'diorite_wall','context.pinnacle')
                f.put(u,g+54,1,'gold_block','context.finial')
            f.balustrade(-33,33,g+47,'smooth_sandstone','context.parapet')
        for xx,n in [(x0,(-1,0)),(x1-1,(1,0))]:
            f=self.frame(xx,(z0+z1)//2,n)
            for u in [-15,-7,1,9,17]:
                for yy in [g+3,g+17,g+32]:f.window(u,yy,4,9,f'context.end.{xx}.{u}.{yy}',stone='smooth_sandstone',arched=True,room=False)
            for u in [-20,-11,-2,7,16,20]:f.rect(u,u+1,g,g+48,1,2,'cut_sandstone','context.end.buttress')
        self.hip_roof((x0+3,z0+3,x1-3,z1-3),g+47,9,'polished_deepslate','context.roof')
        for x in range(15,70,14):
            self.box((x,g+52,65),(x+3,g+61,68),'cut_sandstone','context.chimney')
            self.box((x-1,g+61,64),(x+4,g+62,69),'smooth_sandstone','context.chimney_cap')
    def shaft(self):
        x,z,g=self.cx,self.cz,self.g
        self.box((x-12,g,z-12),(x+13,g+96,z+13),'smooth_sandstone','tower.shaft.masonry')
        self.box((x-10,g+1,z-10),(x+11,g+96,z+11),'minecraft:air','tower.shaft.void')
        # Strong continuous corner buttresses, thinner middle ribs.
        for f in self.faces():
            for u in [-11,-7,-3,3,7,11]:
                f.rect(u,u+1,g+1,g+94,1,2,'cut_sandstone','tower.shaft.ribs')
            for level,(y,h) in enumerate([(g+6,14),(g+27,15),(g+49,16),(g+72,17)]):
                for u in [-8,-4,0,4,8]:
                    f.window(u,y,2,h,f'tower.shaft.window.{f.n}.{level}.{u}',stone='smooth_sandstone',arched=True,room=False)
                    # Transoms divide tall recesses; dark depth remains behind.
                    if h>14:f.rect(u-1,u+1,y+8,y+9,0,1,'cut_sandstone','tower.shaft.transom')
            for u in [-11,11]:
                f.rect(u-1,u+2,g+2,g+92,0,2,'smooth_sandstone','tower.corner_buttress')
        for y in [g+1,g+23,g+45,g+68,g+92,g+94]:
            self.square_band(y,13,M('smooth_sandstone_slab',type='top'),'tower.shaft.stringcourse')
        # Entrance in the exposed north face.
        f=next(self.faces());f.rect(-2,3,g+1,g+8,-3,2,'minecraft:air','tower.entrance')
        for yy in range(g+1,g+8):f.put(-3,yy,1,'cut_sandstone','tower.entrance.frame');f.put(3,yy,1,'cut_sandstone','tower.entrance.frame')
        for u in range(-3,4):f.put(u,g+8+int(2-abs(u)/2),1,'smooth_sandstone','tower.entrance.arch')
        # A playable-scale stair candidate, intentionally not the real 334 steps.
        path=[(xx,z-8) for xx in range(x-8,x+8)]+[(x+8,zz) for zz in range(z-8,z+8)]+[(xx,z+8) for xx in range(x+8,x-8,-1)]+[(x-8,zz) for zz in range(z+8,z-8,-1)]
        for i in range(216):
            xx,zz=path[i%len(path)];yy=g+1+i//2
            for dx,dz in [(0,0),(-1 if xx>x else 1 if xx<x else 0,-1 if zz>z else 1 if zz<z else 0)]:
                self.put(xx+dx,yy,zz+dz,M('smooth_sandstone_slab',type='top' if i%2 else 'bottom'),'tower.interior.stair')
        for yy in [g+23,g+45,g+68,g+92,g+108]:
            self.box((x-4,yy,z-4),(x+5,yy+1,z+5),'oak_planks','tower.interior.service_platform')
            self.put(x,yy+3,z,'glowstone','lighting.interior.service')
    def clock(self):
        g=self.g;c=g+self.p['tower']['clock_center_above_grade'];rad=self.p['tower']['dial_diameter_blocks']/2
        x,z=self.cx,self.cz
        self.box((x-12,g+96,z-12),(x+13,g+124,z+13),'smooth_sandstone','clock.masonry')
        self.box((x-10,g+97,z-10),(x+11,g+124,z+11),'minecraft:air','clock.room_void')
        for face_i,f in enumerate(self.faces()):
            f.rect(-10,11,c-10,c+11,1,2,'gold_block',f'clock.{face_i}.gold_frame')
            f.rect(-9,10,c-9,c+10,1,2,'cut_sandstone',f'clock.{face_i}.spandrel')
            for u in range(-9,10):
                for dy in range(-9,10):
                    d=math.hypot(u+.5,dy+.5)
                    if d<=rad:
                        f.rect(u,u+1,c+dy,c+dy+1,-2,2,'minecraft:air',f'clock.{face_i}.aperture')
                        f.put(u,c+dy,-1,'sea_lantern',f'lighting.clock.{face_i}.opal_backlight')
                        f.put(u,c+dy,0,'white_stained_glass',f'clock.{face_i}.opal')
                        if d>rad-1:f.put(u,c+dy,1,'lapis_block',f'clock.{face_i}.blue_ring')
                    elif abs(u)>=7 and abs(dy)>=7 and (abs(u)+abs(dy))%3==0:
                        f.put(u,c+dy,2,'gold_block',f'clock.{face_i}.spandrel_relief')
            for hour in range(12):
                a=hour*math.tau/12;u=round((rad-1.6)*math.sin(a));yy=c+round((rad-1.6)*math.cos(a))
                f.put(u,yy,1,'lapis_block',f'clock.{face_i}.hour_markers')
            # Minute and hour hands in the same visual handedness on all faces.
            hour,minute=self.p['tower']['clock_time']
            for a,r in [(minute/60*math.tau,rad-2),(hour/12*math.tau+minute/720*math.tau,rad-3.5)]:
                f.line((0,c,2),(r*math.sin(a),c+r*math.cos(a),2),'lapis_block',f'clock.{face_i}.hands')
            f.put(0,c,2,'lapis_block',f'clock.{face_i}.axle')
            for u in [-4,0,4]:
                for dy in [-3,2]:f.put(u,c+dy,-3,'sea_lantern',f'lighting.clock.{face_i}.backlight')
            for u in [-10,10]:f.rect(u,u+1,g+97,g+124,2,3,'smooth_sandstone','clock.outer_pier')
        self.square_band(g+96,14,'smooth_sandstone','clock.plinth')
        self.square_band(g+123,14,M('smooth_sandstone_slab'),'clock.cornice')
        # Decorative blind arcade below clock, readable shadow pockets.
        for f in self.faces(13):
            for u in range(-10,11,3):
                f.rect(u,u+1,g+93,g+96,0,1,'polished_deepslate','clock.lower_arcade.recess')
                f.put(u,g+96,1,M('smooth_sandstone_slab'),'clock.lower_arcade.cap')
    def belfry_roof(self):
        g,x,z=self.g,self.cx,self.cz;p=self.p['tower']
        b0,b1=p['belfry'];r0,r1=p['lower_roof'];l0,l1=p['lantern'];s0,s1=p['upper_spire']
        self.box((x-11,g+b0,z-11),(x+12,g+b0+1,z+12),'oak_planks','belfry.floor')
        self.box((x-11,g+b1-1,z-11),(x+12,g+b1,z+12),'cut_sandstone','belfry.ceiling')
        # Open lancets are cut into masonry; solid corners tie the chamber together.
        for f in self.faces(12):
            f.rect(-12,13,g+b0+1,g+b1,0,2,'smooth_sandstone','belfry.arcade.masonry')
            for u in [-8,-4,0,4,8]:
                f.rect(u-1,u+2,g+b0+2,g+b1-3,-1,2,'minecraft:air','belfry.lancet.opening')
                for yy in range(g+b0+2,g+b1-3):f.put(u,yy,0,'iron_bars','belfry.open_screen')
                f.put(u,g+b1-3,1,'gold_block','belfry.lancet.arch_tip')
                for du in [-1,1]:f.put(u+du,g+b1-4,1,M('smooth_sandstone_slab'),'belfry.lancet.arch')
            f.rect(-13,14,g+b1-1,g+b1,0,2,'lapis_block','belfry.heraldic_frieze')
            for u in [-10,-5,0,5,10]:
                f.put(u,g+b1-1,2,'gold_block','belfry.heraldic_frieze.accent')
            for u in [-8,0,8]:f.put(u,g+b1-2,-1,'glowstone','lighting.belfry.arcade')
        for xx,zz,r,h in [(x,z,3.2,6),(x-6,z-6,1.6,4),(x+6,z-6,1.6,4),(x-6,z+6,1.6,4),(x+6,z+6,1.6,4)]:
            for j in range(h):self.disk(xx,zz,max(1,r*(1-j/h*.65)),g+b0+2+j,'polished_deepslate','belfry.bell')
            self.line((xx,g+b0+2+h,zz),(xx,g+b1-1,zz),'chain','belfry.hanger')
        # Roof metal is dark; blue/gold remains in fine trim, not large stripes.
        for yy in range(r0,r1):
            r=12-(yy-r0)*7/(r1-r0)
            for xx in range(math.floor(x-r),math.ceil(x+r)+1):
                for zz in range(math.floor(z-r),math.ceil(z+r)+1):
                    if max(abs(xx-x),abs(zz-z))>=r-1.1:
                        self.put(xx,g+yy,zz,'polished_deepslate','roof.lower.cast_iron')
            for dx,dz in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                self.put(x+dx*r,g+yy,z+dz*r,'gold_block' if yy%6==0 else 'polished_deepslate','roof.lower.hip_rib')
        for f in self.faces(9):
            for u in [-5,5]:
                f.rect(u-1,u+2,g+r0+6,g+r0+10,1,2,'black_stained_glass','roof.dormer')
                f.put(u,g+r0+10,2,'gold_block','roof.dormer.crest')
        for yy,rr in [(r0,13),(r1,6)]:self.square_band(g+yy,rr,'gold_block','roof.gold_rail')
        for f in self.faces(5):
            for u in [-5,-2,2,5]:f.rect(u,u+1,g+l0,g+l1,0,1,'lapis_block','lantern.column')
            f.rect(-4,5,g+l0+2,g+l1-2,-1,0,'black_stained_glass_pane','lantern.glazing')
            for u in [-2,2]:f.put(u,g+l0+5,-2,'sea_lantern','lighting.ayrton')
            f.rect(-6,7,g+l1-1,g+l1,0,1,'gold_block','lantern.cornice')
            for u in [-5,5]:f.put(u,g+l0+2,1,'gold_block','lantern.gilt_detail')
        for yy in range(s0,s1-2):
            r=max(.35,6*(s1-2-yy)/(s1-2-s0))
            for xx in range(math.floor(x-r),math.ceil(x+r)+1):
                for zz in range(math.floor(z-r),math.ceil(z+r)+1):
                    if max(abs(xx-x),abs(zz-z))<=r:self.put(xx,g+yy,zz,'polished_deepslate','roof.upper.spire')
            for dx,dz in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                if yy%5==0:self.put(x+dx*r,g+yy,z+dz*r,'gold_block','roof.upper.crockets')
        for yy in [s1-2,s1-1]:self.put(x,g+yy,z,'gold_block','roof.finial')
        for xx,zz in [(x-13,z-13),(x-13,z+13),(x+13,z-13),(x+13,z+13)]:
            self.line((xx,g+r0,zz),(xx,g+r0+8,zz),'iron_bars','roof.corner_pinnacle')
            self.put(xx,g+r0+9,zz,'gold_block','roof.corner_pinnacle.finial')
    def build(self):
        for name,fn in [('ground',self.ground),('context',self.context),('shaft',self.shaft),('clock',self.clock),('roof',self.belfry_roof)]:
            fn();print(name,len(self.s.blocks),flush=True)
        return self

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name!=a.run:ap.error('simple run name required')
    p=json.loads((a.params or CASE/'params.json').read_text());b=Tower(p).build()
    save_run(CASE,a.run,p,b,__file__,{'scale_blocks_per_metre':2,'tower_height_blocks':192,'clock_face_count':4,'clock_dial_diameter_blocks':14,'scope':p['scope'],'limitations':['Clock numerals simplified to voxel hour markers; static hands','Context wing and internal staircase are approximations','No automatic image reconstruction or game verification']})
if __name__=='__main__':main()
