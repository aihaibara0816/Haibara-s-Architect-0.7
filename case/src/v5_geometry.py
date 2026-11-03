"""V5 above-ground podium case adapter. Inputs are reviewed evidence, not pixel AI.

Keep tower geometry in the existing adapter. Author the podium with explicit
levels, curved masks, stable owners and a shared 1F floor. All visible objects
are real NBT blocks. The two court bottoms are deliberately truncated at 1F.
"""
from v4_geometry import *

PAVING=addmat('minecraft:light_gray_concrete','#AEB0B1')
PANEL=addmat('minecraft:gray_concrete','#747A7D')
STONE=addmat('minecraft:smooth_stone','#BCBDBB')
QUARTZ=addmat('minecraft:smooth_quartz','#DCDCD5')
PAVE=addmat('minecraft:stone_bricks','#A3A8A8')
SLAB=addmat('minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]','#DADBD5')
LOW_STONE=addmat('minecraft:smooth_stone_slab[type=bottom,waterlogged=false]','#B7BAB8')
SOIL=addmat('minecraft:dirt','#746453')
GRASS=addmat('minecraft:moss_block','#71814F')
LEAVES=addmat('minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]','#526E42')
GLASS=addmat('minecraft:light_blue_stained_glass','#97AFB5')
SKYGLASS=addmat('minecraft:gray_stained_glass','#89989E')
DARK=addmat('minecraft:polished_blackstone','#3D454A')
WATER=addmat('minecraft:water[level=0]','#315A68')

NEIGH=[(1,0),(-1,0),(0,1),(0,-1)]

def smooth_poly(points, closed=True, samples=12):
    p=[np.array(q,float) for q in points];out=[];n=len(p)
    for i in range(n if closed else n-1):
        a=p[(i-1)%n] if closed else p[max(i-1,0)]
        b=p[i];c=p[(i+1)%n];d=p[(i+2)%n] if closed else p[min(i+2,n-1)]
        for t in np.linspace(0,1,samples,endpoint=False):
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    if not closed:out.append(p[-1])
    return np.array(out)

def polygon_mask(points,size=(128,232)):
    p=np.asarray(points)
    xx,zz=np.meshgrid(np.arange(size[0])+.5,np.arange(size[1])+.5,indexing='ij')
    inside=np.zeros(xx.shape,dtype=bool)
    for a,b in zip(p,np.roll(p,1,axis=0)):
        if a[1]==b[1]:continue
        inside^=((a[1]>zz)!=(b[1]>zz)) & (xx<(b[0]-a[0])*(zz-a[1])/(b[1]-a[1])+a[0])
    return {tuple(map(int,q)) for q in np.argwhere(inside)}

def boundary(mask):return {p for p in mask if any((p[0]+dx,p[1]+dz) not in mask for dx,dz in NEIGH)}

def near_path(points,width):
    out=set();points=smooth_poly(points,False,15)
    for a,b in zip(points,points[1:]):
      for t in np.linspace(0,1,max(2,math.ceil(float(np.linalg.norm(b-a))*3))):
        x,z=a+(b-a)*t
        for xx in range(math.floor(x-width),math.ceil(x+width)):
         for zz in range(math.floor(z-width),math.ceil(z+width)):
          if (xx+.5-x)**2+(zz+.5-z)**2<=width*width:out.add((xx,zz))
    return out

class Podium:
    def __init__(self,scene,config):
        self.s=scene;self.c=config;self.floor=config['levels']['first_floor_surface_y']-1
        self.deck=config['levels']['upper_deck_surface_y']-1
        self.records=[];self.stairs=[];self.trees=[];self.plants={};self.water=set()
        self.outline_points=[(26,13),(60,7),(92,16),(106,38),(109,66),(116,95),(117,122),(110,150),(112,178),(108,213),(97,220),(72,220),(48,224),(27,218),(19,199),(16,172),(11,144),(10,115),(14,87),(18,61),(19,33)]
        self.deckmask=polygon_mask(smooth_poly(self.outline_points))
        self.groundmask={(x+dx,z+dz) for x,z in self.deckmask for dx,dz in [(0,0),(4,0),(-4,0),(0,4),(0,-4)] if 2<=x+dx<126 and 2<=z+dz<230}
        self.edge=boundary(self.deckmask)

    def w(self,x,y,z,state,owner):self.s.set((int(x),int(y),int(z)),state,owner)
    def record(self,id,evidence,decision,confidence='medium',**extra):
        self.records.append({'component_id':id,'evidence':evidence,'decision':decision,'confidence':confidence,**extra})

    def shell(self):
        for x,z in sorted(self.groundmask):
            self.w(x,0,z,STONE,'site.foundation.skin')
            mat=STONE if x%15==0 or z%18==0 else PAVE
            self.w(x,self.floor,z,mat,'site.first_floor.paving')
        # Roofed first floor: an above-ground shell, no B1 volume.
        for x,z in sorted(self.deckmask):
            self.w(x,self.deck-1,z,PANEL,'podium.structure.slab')
            self.w(x,self.deck,z,PAVING if (x+z)%31 else STONE,'podium.upper_deck')
            if x%12==4 and z%14==4:
                for y in range(self.floor+1,self.deck-1):self.w(x,y,z,QUARTZ,'podium.structure.column')
            if x%12==9 and z%14==9:self.w(x,self.deck-1,z,LIGHT,'lighting.podium.first_floor')
        for x,z in self.edge:
            for y in range(self.floor+1,self.deck):
                self.w(x,y,z,QUARTZ if x%9==0 or z%12==0 or y==self.deck-1 else SKYGLASS,'podium.edge_facade')
            self.w(x,self.deck,z,QUARTZ,'podium.upper_edge')
            # Low transparent parapet on the raised outside boundary.
            self.w(x,self.deck+1,z,GLASS,'podium.edge_rail')
        self.record('podium.upper_deck',['N05','N04','S1','S2'],'Continuous upper platform with separate 1F edge; dimensions and +5 block rise estimated.',level_surface_y=self.deck+1)

    @staticmethod
    def local(x,z,p):
        cx,cz=p['center_xz'];a,b=p['radii'];phi=math.radians(p['rotation_degrees']);co,si=math.cos(phi),math.sin(phi)
        dx=x+.5-cx;dz=z+.5-cz;u=dx*co+dz*si;v=-dx*si+dz*co
        return u,v,math.hypot(u/a,v/b),math.atan2(v/b,u/a)

    @staticmethod
    def world(u,v,p):
        phi=math.radians(p['rotation_degrees']);co,si=math.cos(phi),math.sin(phi)
        return p['center_xz'][0]+u*co-v*si,p['center_xz'][1]+u*si+v*co

    def court(self,id,p):
        cx,cz=p['center_xz'];a,b=p['radii'];owner='court.'+id
        for x in range(int(cx)-34,int(cx)+35):
         for z in range(int(cz)-35,int(cz)+36):
          u,v,r,theta=self.local(x,z,p)
          if r<.97:
            for y in range(self.floor+1,16):self.w(x,y,z,AIR,owner+'.clear')
            self.w(x,self.floor,z,STONE if int(r*17)%5 else PAVE,owner+'.first_floor')
          # Single above-ground shop front beneath the upper deck.
          if .93<r<1.00:
            for y in range(self.floor+1,self.deck):
                st=SKYGLASS if y<self.deck-1 and int((theta+math.pi)*14)%7 else QUARTZ
                self.w(x,y,z,st,owner+'.first_floor_facade')
          if .94<r<1.09:
            self.w(x,self.deck,z,QUARTZ if r<1.0 else PAVING,owner+'.upper_rim')
          if .93<r<.98:self.w(x,self.deck+1,z,GLASS,owner+'.rail')
          # Asymmetric wave canopy. Stair sector remains open, roof is a thin slab/glass band.
          if 1.07<r<1.25 and not (abs(u)<8.5 and v>0):
            roof=self.deck+2+round(p['canopy_rise']*(.5+.5*math.cos(theta+.8)))
            edge=r<1.11 or r>1.21
            self.w(x,roof,z,SLAB if edge or int((theta+math.pi)*15)%8==0 else GLASS,owner+'.canopy')
            if edge and (x+z)%13==0:self.w(x,roof-1,z,WARM,'lighting.'+owner+'.canopy')
        # Ascend from a 1F court to 2F; no negative-level access.
        samples=[]
        for x in range(int(cx)-30,int(cx)+31):
         for z in range(int(cz)-30,int(cz)+32):
          u,v,r,th=self.local(x,z,p)
          if abs(u)<6.5 and b-8<=v<b+7:
            tread=self.floor+min(self.deck-self.floor,max(0,int((v-(b-8))/2)))
            for y in range(self.floor+1,15):self.w(x,y,z,AIR,owner+'.stairs.clear')
            for y in range(self.floor,tread+1):self.w(x,y,z,QUARTZ,owner+'.stairs')
            samples.append((x,tread,z))
            if abs(u)>5.5 and int(v)%4==0:self.w(x,tread,z,LIGHT,'lighting.'+owner+'.stairs')
        self.stairs.append({'component_id':owner+'.stairs','treads':samples})
        for k in range(14):
            theta=2*math.pi*k/14
            u=1.16*a*math.cos(theta);v=1.16*b*math.sin(theta)
            if abs(u)<9 and v>0:continue
            x,z=self.world(u,v,p);roof=self.deck+2+round(p['canopy_rise']*(.5+.5*math.cos(theta+.8)))
            thin_line(self.s,[x+math.cos(theta),self.deck+1,z+math.sin(theta)],[x,roof,z],WALL,owner+'.canopy_support')
        self.record(owner,['N05','N03' if id=='north' else 'N04','P08'],'Distinct rotated oval, single above-ground edge facade, thin wave canopy. Original below-grade depth removed; floor set at 1F.',confidence='medium',floor_surface_y=self.floor+1,below_grade_omitted=True)

    def landscape(self):
        shapes={
         'west_01':[(23,66),(33,65),(39,74),(35,85),(21,90)],
         'west_02':[(19,94),(31,89),(39,94),(35,110),(39,126),(31,134),(20,125)],
         'west_03':[(20,140),(34,134),(43,143),(41,156),(34,168),(20,160)],
         'west_04':[(24,176),(37,169),(43,181),(40,198),(32,211),(24,205)],
         'east_01':[(89,65),(104,63),(108,79),(104,93),(93,90)],
         'east_02':[(94,98),(110,94),(112,114),(103,131),(88,130),(89,119)],
         'east_03':[(87,140),(102,136),(106,155),(98,176),(86,169),(84,154)],
         'east_04':[(87,184),(100,177),(106,193),(102,210),(88,215),(85,202)]}
        for i,(id,points) in enumerate(shapes.items()):
            cells=polygon_mask(smooth_poly(points))&self.deckmask
            # Leave paths crossing planted roofs as circulation, not arbitrary green stripes.
            path=near_path([(points[0][0]-1,points[0][1]+3),(sum(x for x,z in points)/len(points),sum(z for x,z in points)/len(points)),(points[-2][0]+1,points[-2][1]-3)],1.05)
            cells-=path
            edge=boundary(cells)
            self.plants[id]=cells
            for x,z in cells:
                self.w(x,self.deck,z,SOIL,'landscape.'+id+'.soil')
                self.w(x,self.deck+1,z,LOW_STONE if (x,z) in edge else GRASS,'landscape.'+id+'.roof_garden')
            for x,z in path&self.deckmask:
                if x<43 or x>85:self.w(x,self.deck,z,STONE,'landscape.'+id+'.path')
            candidates=sorted(cells,key=lambda q:((q[0]*73856093 ^ q[1]*19349663)&0xffff))
            placed=[]
            for x,z in candidates:
                if (x,z) in edge or (x,z) not in cells:continue
                if any((x+dx,z+dz) not in cells for dx in [-2,0,2] for dz in [-2,0,2]):continue
                if any((x-a)**2+(z-b)**2<35 for a,b in placed):continue
                placed.append((x,z));self.tree(x,z,self.deck+2,f'landscape.{id}.tree.{len(placed):02}',3+(len(placed)+i)%2)
                if len(placed)==4:break
            self.record('landscape.'+id,['N05','N04'],'Curved roof garden with soil slab, internal path and sparse trees; exact boundary and elevation estimated.',support_component='podium.upper_deck',surface_y=self.deck+2)
        # Two specifically ground-supported green pockets, not assigned to 2F.
        for id,cx,cz,a,b in [('ground_west',10,62,4,13),('ground_east',117,166,5,15)]:
            cells={(x,z) for x,z in self.groundmask if ell(x,z,cx,cz,a,b)<1 and (x,z) not in self.deckmask}
            for x,z in cells:self.w(x,self.floor,z,GRASS,'landscape.'+id)
            self.record('landscape.'+id,['N04'],'Ground-level planted edge; independent from roof planting.',confidence='low',support_component='site.first_floor.paving',surface_y=self.floor+1)

    def tree(self,x,z,y,id,height):
        self.trees.append({'id':id,'root_xyz':[x,y,z],'support_y':y-1})
        for yy in range(y,y+height):self.w(x,yy,z,LOG,id+'.trunk')
        for dx in range(-2,3):
         for dz in range(-2,3):
          for dy in range(-1,3):
           if dx*dx+dz*dz+(dy-.2)**2<5.5:self.w(x+dx,y+height+dy,z+dz,LEAVES,id+'.leaves')

    def glazed_walk(self,id,points,width=1.25):
        cells=near_path(points,width)&self.deckmask;edge=boundary(cells)
        for x,z in cells:
            y=self.deck+4+round(.6*math.sin(z/21))
            self.w(x,y,z,SLAB if (x,z) in edge else GLASS,'canopy.'+id)
        sampled=smooth_poly(points,False,5)
        for k,(x,z) in enumerate(sampled[::7]):
            y=self.deck+4+round(.6*math.sin(z/21))
            thin_line(self.s,[x,self.deck+1,z],[x,y,z],WALL,'canopy.'+id+'.support')
            self.w(x,y-1,z,LIGHT,'lighting.canopy.'+id)
        self.record('canopy.'+id,['N05','FB-U03'],'Narrow curved glass cover with restrained pale edge; covered circulation, precise usage unresolved.',confidence='medium')

    def pool(self,p):
        cx,cz=p['center_xz'];lo,hi=p['z_range']
        for z in range(lo,hi+1):
            half=p['half_width']+1.5*((z-cz)/16)**2
            for x in range(math.ceil(cx-half),math.floor(cx+half)):
                self.water.add((x,z))
        edge=boundary(self.water)
        for x,z in self.water:
            for y in range(self.deck+1,self.deck+4):self.w(x,y,z,AIR,'pool.clear')
            self.w(x,self.deck-1,z,DARK,'pool.basin')
            self.w(x,self.deck,z,QUARTZ if (x,z) in edge else WATER,'pool.edge' if (x,z) in edge else 'pool.water')
        self.water-=edge
        # Pair of sloping glazed ribbons beside the reflective pool, not four generic pavilions.
        for side,xmid in [('west',46),('east',83)]:
          for z in range(lo-2,hi+3):
            roof=self.deck+1+max(0,round(3*(hi+2-z)/(hi-lo+4)))
            for x in range(xmid-1,xmid+2):
                self.w(x,roof,z,SLAB if x!=xmid or z%7==0 else GLASS,'pool.'+side+'.glazed_roof')
                if x==xmid and z%9==0:
                    for y in range(self.deck+1,roof):self.w(x,y,z,GLASS,'pool.'+side+'.roof_end')
                    self.w(x,roof-1,z,LIGHT,'lighting.pool.'+side)
        self.record('pool',['N05','P09','S2'],'Reflection pool on the upper platform; paired tapering glazed roofs. No simulated mirror or downward access.',level_surface_y=self.deck+1)

    def base_interface(self,tower):
        # One shared ground surface; avoid a redundant floor above the plaza floor.
        removed=0
        for q in list(tower.blocks):
            if q[1]==2 and tower.owners[q]=='program.A':
                tower.set(q,AIR,'base.floor.adaptation');removed+=1
        # First-floor entry aligns to the retained core entrance and preserves frame.
        for x in range(27,30):
         for z in range(29,45):
          for y in range(2,6):
           q=(x,y,z)
           if tower.owners.get(q,'').startswith(('program.','core')):tower.set(q,AIR,'entry.clear')
        # Do not push the new deck through the original glass/floor interior.
        cx,cz=64.5,40.5
        for x,z in self.deckmask:
            if ell(x,z,cx,cz,17,12)<1:
                for y in [self.deck-1,self.deck]:self.w(x,y,z,AIR,'tower.base.interface.void')
        # Open a broad front door through the podium edge at 1F, with a small glass canopy.
        for x in range(58,72):
         for z in range(57,80):
          for y in range(self.floor+1,self.deck-1):self.w(x,y,z,AIR,'tower.base.entry.clear')
        for x in range(55,75):
         for z in range(68,76):
            roof=self.deck+1+round(.9*math.cos((x-64.5)/10*math.pi/2))
            self.w(x,roof,z,SLAB if x in [55,74] or z in [68,75] or x%5==0 else GLASS,'tower.base.entry_canopy')
        for x in [55,74]:
            thin_line(self.s,[x,self.floor+1,75],[x,self.deck+1,72],WALL,'tower.base.entry_canopy.support')
        for x in [58,64,70]:self.w(x,self.deck,73,LIGHT,'lighting.tower.base.entry')
        # Three small roof lights retain the photo's front-platform punctuation.
        for i,xmid in enumerate([52,59,66]):
            for x in range(xmid-3,xmid+4):
             for z in range(77,84):
                r=ell(x,z,xmid+.5,80.5,2.7,2.7)
                if r<1:self.w(x,self.deck,z,SKYGLASS if r<.55 else QUARTZ,f'tower.base.skylight.{i:02}')
            self.w(xmid,self.deck-2,80,LIGHT,'lighting.tower.base.skylight')
        self.record('tower.base.interface',['H01','P10','N03','FB-U03'],'Shared 1F floor, integrated upper slab around exposed tower feet, lower entry canopy. Historic source used only for level relation.',removed_old_base_floor_cells=removed)

    def outer_stairs(self):
        # Broad south arrival stairs: 1F outside to 2F platform, no basement steps.
        samples=[]
        for x in range(44,84):
         for z in range(215,229):
            y=self.floor+min(self.deck-self.floor,max(0,(228-z)//2))
            for yy in range(self.floor+1,15):self.w(x,yy,z,AIR,'site.south_steps.clear')
            self.w(x,0,z,STONE,'site.foundation.skin')
            for yy in range(self.floor,y+1):self.w(x,yy,z,STONE if x%8 else QUARTZ,'site.south_steps')
            samples.append((x,y,z))
        self.stairs.append({'component_id':'site.south_steps','treads':samples})
        # Two clear side entries at ground level; a curved roof edge stays above them.
        for side,xrange,z0 in [('west',range(7,23),150),('east',range(103,121),118)]:
          for x in xrange:
           for z in range(z0,z0+7):
            for y in range(self.floor+1,self.deck-1):self.w(x,y,z,AIR,'site.'+side+'.entry.clear')
          self.record('site.'+side+'.entry',['FB-U03','N06'],'1F access under upper platform; shop rooms remain schematic.',confidence='low')
        self.record('site.south_steps',['N05'],'Broad south arrival connects 1F to upper deck; staircase shape estimated.')

    def lighting(self):
        for z in range(67,214,12):
         for side in [-1,1]:
            x=round(64+side*(42+2*math.sin(z/23)))
            if (x,z) not in self.deckmask:continue
            if any((x,z) in cells for cells in self.plants.values()):continue
            for y in range(self.deck+1,self.deck+4):self.w(x,y,z,register_state(member_state(BARS)),'lighting.path.post')
            self.w(x,self.deck+4,z,WARM,'lighting.path.source')
        for x,z in self.edge:
            if (x*3+z)%17==0 and self.s.owners.get((x,self.deck,z))=='podium.upper_edge':self.w(x,self.deck,z,LIGHT,'lighting.podium.edge')
        # Flush guide lights on main approach, deliberately low density.
        for z in range(71,214,8):
         for x in [40,88]:
            if self.s.owners.get((x,self.deck,z))=='podium.upper_deck':self.w(x,self.deck,z,LIGHT,'lighting.podium.walk')

    def build(self,tower):
        self.shell()
        self.court('north',self.c['site']['north_court']);self.court('south',self.c['site']['south_court'])
        self.landscape()
        self.glazed_walk('west_ribbon',[(20,82),(26,100),(24,124),(20,151),(27,177),(29,205)],1.65)
        self.glazed_walk('east_ribbon',[(103,75),(99,97),(106,121),(101,149),(105,173),(100,201)],1.65)
        self.glazed_walk('west_cross',[(18,85),(27,85),(39,86)],1.7)
        self.glazed_walk('east_cross',[(88,136),(99,134),(109,134)],1.7)
        self.glazed_walk('west_south_cross',[(22,166),(34,166),(43,165)],1.7)
        self.pool(self.c['site']['pool'])
        self.base_interface(tower);self.outer_stairs();self.lighting()
        return self
