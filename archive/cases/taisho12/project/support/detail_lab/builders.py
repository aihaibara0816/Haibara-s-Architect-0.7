"""Eight original learning specimens, not replicas or a universal building engine.

All coordinates are local integer XYZ; front is -Z. Components have stable IDs.
Boxes use half-open ranges. Deliberate replacement is explicit and logged.
"""
import math
from collections import Counter
from vendor.voxel_core import Scene
from .states import make, connect, cube_control

class Builder:
    def __init__(self, sample_id, size):
        self.id=sample_id; self.scene=Scene(size); self.replacements=Counter()
    def put(self, xyz, material, part, replace=False, **props):
        s=make(material,**props); p=tuple(xyz); owner=self.id+'.'+part
        old=self.scene.blocks.get(p)
        if old is not None and old!=s:
            if not replace:raise ValueError(f'Unapproved overlap {self.id} {p}: {old} -> {s}')
            self.replacements[(self.scene.owners[p],owner)]+=1
        self.scene.set(p,s,owner)
    def box(self,lo,hi,mat,part,replace=False,**props):
        if any(a>=b for a,b in zip(lo,hi)):raise ValueError('Empty or reversed box')
        for x in range(lo[0],hi[0]):
            for y in range(lo[1],hi[1]):
                for z in range(lo[2],hi[2]):self.put((x,y,z),mat,part,replace,**props)
    def line(self,a,b,mat,part,replace=False,**props):
        """Manhattan-connected raster line; diagonal panes must not float apart."""
        p=list(a);self.put(p,mat,part,replace,**props)
        n=max(abs(b[i]-a[i]) for i in range(3))
        for j in range(1,n+1):
            q=[round(a[i]+(b[i]-a[i])*j/n) for i in range(3)]
            for axis in range(3):
                while p[axis]!=q[axis]:
                    p[axis]+=1 if q[axis]>p[axis] else -1
                    self.put(p,mat,part,replace,**props)
    def ground(self):
        x,y,z=self.scene.size;self.box((0,0,0),(x,1,z),'smooth_stone','site.paving')
    def done(self):
        self.scene.events=[{'from':a,'to':b,'replaced_cells':n} for (a,b),n in self.replacements.items()]
        connect(self.scene);return self.scene

def room(b,x0,x1,z0,z1,floor,top,part,back='light_gray_concrete'):
    b.box((x0,floor,z0),(x1,floor+1,z1),'polished_andesite',part+'.floor')
    b.box((x0,floor+1,z1-1),(x1,top,z1),back,part+'.background')
    b.box((x0,top,z0),(x1,top+1,z1),'smooth_quartz_slab',part+'.ceiling',type='bottom')
    for x in range(x0+2,x1-1,5):
        b.put((x,top-1,z1-3),'sea_lantern',part+'.light')
        b.box((x-1,floor+1,z1-5),(x+1,floor+2,z1-4),'oak_slab',part+'.desk',type='top')
        b.put((x,floor+1,z1-3),'quartz_stairs',part+'.seat',facing='south')
        b.put((x,top-1,z0+2),'end_rod',part+'.light',facing='east')

def modern(c):
    p=c['parameters'];count=p['bays'];pitch=p['bay_pitch'];fh=p['floor_pitch'];w=4+count*pitch;zglass=p['glass_z']
    b=Builder(c['id'],(w,2*fh+4,18));b.ground()
    for k in range(2):
        f=1+k*fh;ceiling=f+fh-1
        room(b,2,w-2,zglass+1,16,f,ceiling,f'interior.level{k}')
        for bay in range(count):
            x=2+bay*pitch
            b.box((x+1,f+1,zglass),(x+pitch,ceiling,zglass+1),'light_blue_stained_glass_pane',f'facade.bay{bay}.level{k}.glass')
            b.box((x+pitch//2,f+1,zglass-1),(x+pitch//2+1,ceiling,zglass),'iron_bars',f'facade.bay{bay}.level{k}.fin')
        b.box((2,ceiling,zglass),(w-2,ceiling+1,zglass+1),'black_concrete',f'facade.spandrel{k}')
        b.box((2,ceiling,zglass-2),(w-2,ceiling+1,zglass-1),'iron_trapdoor',f'facade.floor_edge{k}',half='top')
    for x in range(2,w-1,pitch):b.box((x,1,zglass-1),(x+1,2*fh+2,zglass+2),'gray_concrete','structure.column',replace=True)
    for z in range(zglass+1,16):
        b.put((w-3,1,z),'gray_concrete','structure.side_base',replace=True)
        for k in range(2):b.box((w-3,2+k*fh,z),(w-2,fh+k*fh,z+1),'gray_stained_glass_pane','facade.return',replace=True)
    b.box((3,1,1),(w-3,2,3),'smooth_quartz_slab','entry.step')
    return b.done()

def millennium(c):
    p=c['parameters'];pitch=p['bay_pitch'];w=4+p['bays']*pitch;fh=p['floor_pitch'];gz=p['glass_z']
    b=Builder(c['id'],(w,3*fh+5,19));b.ground()
    for k in range(3):
        f=1+k*fh;top=f+fh-1
        room(b,2,w-2,gz+1,16,f,top,f'interior.level{k}','yellow_terracotta')
        for bay in range(p['bays']):
            x=2+bay*pitch
            b.box((x+1,f+1,gz),(x+pitch,top,gz+1),'light_blue_stained_glass',f'facade.bay{bay}.level{k}.glass')
            b.box((x+pitch//2,f+1,gz-1),(x+pitch//2+1,top,gz),'white_stained_glass_pane',f'facade.bay{bay}.level{k}.rib')
        b.box((2,top,3),(w-2,top+1,gz+1),'smooth_quartz_slab',f'facade.band{k}',type='top')
        # This extra decorative line is NOT a full floor slab.
        b.box((3,f+2,3),(w-3,f+3,4),'smooth_quartz_slab',f'facade.decorative_band{k}',type='bottom')
    for x in range(2,w-1,pitch):b.box((x,1,3),(x+1,3*fh+2,gz+1),'smooth_quartz','structure.pilaster',replace=True)
    b.box((1,3*fh+2,2),(w-1,3*fh+3,8),'quartz_stairs','roof.cornice',facing='south')
    b.box((3,1,1),(w-3,2,3),'polished_andesite_slab','entry.step')
    return b.done()

def western(c):
    p=c['parameters'];pitch=p['bay_pitch'];w=4+p['bays']*pitch
    b=Builder(c['id'],(w,18,19));b.ground();room(b,2,w-2,7,17,1,14,'interior','dark_oak_planks')
    b.box((2,2,4),(w-2,14,7),'bricks','wall.masonry')
    for k,base in enumerate([2,8]):
        for bay in range(p['bays']):
            x=2+bay*pitch;center=x+pitch//2
            for xx in range(center-1,center+2):
                h=4 if xx==center else 3
                b.box((xx,base+1,4),(xx+1,base+1+h,7),'air',f'opening.bay{bay}.level{k}',replace=True)
                b.box((xx,base+1,6),(xx+1,base+1+h,7),'gray_stained_glass_pane',f'window.bay{bay}.level{k}')
            for xx in [center-2,center+2]:b.box((xx,base,3),(xx+1,base+5,4),'smooth_quartz',f'window.frame{bay}.{k}')
            b.box((center-1,base,3),(center+2,base+1,4),'quartz_slab',f'window.sill{bay}.{k}',type='top')
            b.put((center-1,base+4,3),'quartz_stairs',f'window.arch{bay}.{k}',facing='east',half='top')
            b.put((center+1,base+4,3),'quartz_stairs',f'window.arch{bay}.{k}',facing='west',half='top')
            b.put((center,base+5,3),'smooth_quartz',f'window.keystone{bay}.{k}')
    b.box((1,14,3),(w-1,15,8),'quartz_stairs','roof.cornice',replace=True,facing='south')
    b.box((1,15,2),(w-1,16,9),'quartz_slab','roof.cap',type='bottom')
    for x in [2,w-3]:b.box((x,2,3),(x+1,14,4),'smooth_quartz','wall.corner',replace=True)
    return b.done()

def chinese(c):
    # Contemporary Jiangnan-inspired experiment, NOT a historical taxonomy or replica.
    b=Builder(c['id'],(29,17,23));b.ground()
    b.box((3,1,4),(26,2,20),'stone_bricks','courtyard.floor')
    b.box((3,2,5),(26,10,6),'white_concrete','wall.front')
    b.box((3,2,18),(26,9,19),'white_concrete','wall.back')
    b.box((3,2,6),(4,10,18),'white_concrete','wall.side')
    b.box((25,2,6),(26,10,18),'white_concrete','wall.side')
    # Central geometric courtyard opening; real clear air, not black paint.
    b.box((11,2,5),(18,8,6),'air','opening.center',replace=True)
    b.box((12,8,5),(17,9,6),'air','opening.center',replace=True)
    for x in [6,21]:
        b.box((x,4,5),(x+3,8,6),'air','opening.window',replace=True)
        b.box((x,4,6),(x+3,8,7),'gray_stained_glass_pane','window.glass')
        b.box((x+1,4,4),(x+2,8,5),'dark_oak_trapdoor','window.wood_screen',facing='south',open=True)
        b.box((x-1,3,4),(x+4,4,6),'polished_deepslate_slab','window.sill',replace=True,type='top')
    # Roof strips north/south rising toward ridge; open center is a courtyard.
    for z in range(3,11):
        y=10+min(z-3,10-z)
        b.box((2,y,z),(27,y+1,z+1),'polished_deepslate_stairs','roof.front',facing='south' if z<=6 else 'north')
    for z in range(17,21):
        y=9+min(z-17,20-z)
        b.box((2,y,z),(27,y+1,z+1),'polished_deepslate_stairs','roof.back',replace=True,facing='south' if z<=18 else 'north')
    b.box((5,2,12),(10,3,17),'grass_block','courtyard.garden')
    b.box((6,3,13),(9,4,16),'azalea_leaves','courtyard.shrub')
    b.box((20,2,12),(24,3,14),'oak_slab','courtyard.bench')
    for x in [6,22]:b.put((x,8,17),'sea_lantern','courtyard.light')
    return b.done()

def antenna(c):
    b=Builder(c['id'],(19,39,19));b.ground()
    b.box((2,1,2),(17,3,17),'light_gray_concrete','roof.plinth')
    b.box((3,3,3),(16,4,16),'smooth_stone_slab','roof.edge',type='top')
    b.box((7,3,7),(12,6,12),'white_concrete','mast.base',replace=True)
    for x,z in [(6,6),(12,6),(6,12),(12,12)]:
        b.box((x,4,z),(x+1,15,z+1),'iron_block','mast.primary')
    for y in [7,13]:
        for z in [6,12]:b.line((6,y,z),(12,y,z),'iron_bars','mast.tie',replace=True)
        for x in [6,12]:b.line((x,y,6),(x,y,12),'iron_bars','mast.tie',replace=True)
    for z in [6,12]:
        b.line((6,5,z),(12,12,z),'iron_bars','mast.brace',replace=True)
        b.line((12,5,z),(6,12,z),'iron_bars','mast.brace',replace=True)
    for x,z in [(6,6),(12,6),(6,12),(12,12)]:
        b.box((x,4,z),(x+1,15,z+1),'iron_block','mast.primary',replace=True)
    b.box((5,15,5),(14,16,14),'smooth_quartz_slab','mast.platform',type='top')
    for x,z in [(8,8),(10,8),(8,10),(10,10)]:
        for y in range(16,29):b.put((x,y,z),'red_stained_glass_pane' if (y//4)%2 else 'white_stained_glass_pane','mast.upper_leg')
    for y in [18,23,28]:
        for z in [8,10]:b.line((8,y,z),(10,y,z),'iron_bars','mast.upper_tie',replace=True)
        for x in [8,10]:b.line((x,y,8),(x,y,10),'iron_bars','mast.upper_tie',replace=True)
    b.box((8,29,8),(11,30,11),'iron_trapdoor','mast.collar',half='top')
    for y in range(30,37):b.put((9,y,9),'red_stained_glass_pane' if (y//3)%2 else 'white_stained_glass_pane','mast.tip')
    b.put((9,37,9),'end_rod','mast.beacon')
    for x,z in [(4,4),(14,4),(4,14),(14,14)]:b.put((x,4,z),'sea_lantern','roof.light')
    return b.done()

def planter(c):
    b=Builder(c['id'],(34,11,28));b.ground()
    for z in [3,14,25]:b.box((1,0,z),(33,1,z+1),'light_gray_concrete','site.paving_band',replace=True)
    beds=[(4,5,13,11),(19,17,30,23)]
    for i,(x0,z0,x1,z1) in enumerate(beds):
        part=f'garden.bed{i}'
        b.box((x0,1,z0),(x1,2,z1),'stone_bricks',part+'.wall')
        b.box((x0+1,1,z0+1),(x1-1,2,z1-1),'grass_block',part+'.soil',replace=True)
        for x in range(x0,x1):
            for z in [z0,z1-1]:b.put((x,2,z),'stone_brick_slab',part+'.coping')
        for z in range(z0+1,z1-1):
            for x in [x0,x1-1]:b.put((x,2,z),'stone_brick_slab',part+'.coping')
        for x in range(x0+1,x1-1):
            for z in range(z0+1,z1-1):
                if (x+z)%3==0:b.put((x,2,z),'poppy' if i else 'oxeye_daisy',part+'.flowers')
        tx=x0+3;tz=z0+3
        b.box((tx,2,tz),(tx+1,7,tz+1),'oak_log',part+'.tree',replace=True)
        for y,r in [(5,2),(6,2),(7,2),(8,1)]:
            for x in range(tx-r,tx+r+1):
                for z in range(tz-r,tz+r+1):
                    if abs(x-tx)+abs(z-tz)<=r+1 and (x,z)!=(tx,tz):b.put((x,y,z),'oak_leaves',part+'.leaves')
        b.put((tx,8,tz),'oak_leaves',part+'.leaves')
    for i,(x,z) in enumerate([(5,16),(22,6)]):
        b.box((x,1,z),(x+6,2,z+1),'oak_slab',f'furniture.bench{i}.seat',type='top')
        b.box((x,1,z+1),(x+6,3,z+2),'dark_oak_trapdoor',f'furniture.bench{i}.back',facing='north',open=True)
        for xx in [x,x+5]:b.put((xx,1,z),'stone_brick_stairs',f'furniture.bench{i}.leg',replace=True,facing='south')
    for i,(x,z) in enumerate([(2,3),(31,14),(16,24)]):
        b.box((x,1,z),(x+1,6,z+1),'iron_bars',f'light.pole{i}')
        b.put((x,6,z),'sea_lantern',f'light.lamp{i}')
        b.put((x,7,z),'iron_trapdoor',f'light.cap{i}')
    return b.done()

def framework(c):
    b=Builder(c['id'],(27,29,23));b.ground()
    b.box((11,1,9),(16,26,14),'light_gray_concrete','core')
    for x,z in [(4,4),(22,4),(4,18),(22,18)]:b.box((x,1,z),(x+1,27,z+1),'iron_block','frame.primary')
    for y in [2,12,25]:
        for z in [4,18]:b.line((4,y,z),(22,y,z),'iron_bars','frame.ring',replace=True)
        for x in [4,22]:b.line((x,y,4),(x,y,18),'iron_bars','frame.ring',replace=True)
    for z in [4,18]:
        b.line((4,3,z),(22,24,z),'iron_bars','frame.diagonal',replace=True)
        b.line((22,3,z),(4,24,z),'iron_bars','frame.diagonal',replace=True)
    for x in [4,22]:
        b.line((x,3,4),(x,24,18),'iron_bars','frame.diagonal',replace=True)
        b.line((x,3,18),(x,24,4),'iron_bars','frame.diagonal',replace=True)
    b.box((6,13,6),(21,14,17),'smooth_quartz_slab','occupied.floor',replace=True,type='top')
    b.box((6,19,6),(21,20,17),'smooth_quartz_slab','occupied.ceiling',replace=True,type='top')
    for z in [6,16]:b.box((6,14,z),(21,19,z+1),'gray_stained_glass_pane','occupied.glass')
    for x in [6,20]:b.box((x,14,7),(x+1,19,16),'gray_stained_glass_pane','occupied.glass')
    b.box((11,1,9),(16,26,14),'light_gray_concrete','core',replace=True)
    for x,z in [(4,4),(22,4),(4,18),(22,18)]:b.box((x,1,z),(x+1,27,z+1),'iron_block','frame.primary',replace=True)
    for x,z in [(8,8),(18,8),(8,14),(18,14)]:
        b.put((x,18,z),'end_rod','occupied.light')
        b.put((x,14,z),'quartz_stairs','occupied.seat',facing='south')
    return b.done()

def canopy(c):
    b=Builder(c['id'],(29,20,25));b.ground()
    b.box((2,1,3),(27,2,23),'stone_bricks','platform')
    for z in range(4,23):
        for x in range(4,25):
            yy=9+round(7*math.sqrt(max(0,1-((x-14)/10)**2)))
            b.put((x,yy,z),'glass','canopy.glass')
    for i,z in enumerate([4,10,16,22]):
        last=None
        for x in range(4,25):
            yy=9+round(7*math.sqrt(max(0,1-((x-14)/10)**2)))
            pt=(x,yy-1,z)
            if last:b.line(last,pt,'iron_bars',f'canopy.rib{i}',replace=True)
            else:b.put(pt,'iron_bars',f'canopy.rib{i}')
            last=pt
        for x in [4,24]:b.box((x,2,z),(x+1,9,z+1),'iron_block','canopy.column',replace=True)
    for x in [7,14,21]:b.box((x,3,2),(x+2,12,4),'bricks','station.pier')
    b.box((6,12,2),(24,13,4),'quartz_stairs','station.cornice',facing='south')
    for x in [9,16]:
        b.box((x,3,3),(x+5,9,4),'gray_stained_glass_pane','station.window')
        b.box((x,2,2),(x+5,3,4),'quartz_slab','station.sill',type='top')
    for z in [9,18]:
        for x in [7,20]:b.box((x,2,z),(x+2,3,z+3),'oak_slab','platform.bench',type='top')
        b.put((14,14,z),'chain','lighting.hanger')
        b.put((14,15,z),'chain','lighting.hanger')
        b.put((14,13,z),'end_rod','lighting.light',facing='east')
    return b.done()

FACTORIES={'modern':modern,'millennium':millennium,'western':western,'chinese':chinese,'antenna':antenna,'planter':planter,'framework':framework,'canopy':canopy}

def build(c):return FACTORIES[c['id']](c)
def control(scene):
    out=Scene(scene.size)
    for p,s in scene.blocks.items():out.set(p,cube_control(s),scene.owners[p])
    return out
