"""Canton V4 case adapter. Inset rings, actual lights, photo-interpreted plaza.
The inherited engine and V3a baseline remain unchanged. Units are blocks.
"""
from common import *
from open_lattice import OpenLatticeGeometry,connect_thin_members,thin_line,BARS,WALL,member_state,register_state,in_shaft
from hybrid_geometry import face_path

class SiteScene(Scene):
    """Explicit larger sparse case budget; vendor's 1M-cell bound is unchanged."""
    def __post_init__(self):
        self.size=tuple(self.size)
        if len(self.size)!=3 or any(type(v)!=int or v<1 for v in self.size) or math.prod(self.size)>16_000_000:raise ValueError('V4 bounds budget')
    def set(self,p,s,owner):
        if len(self.blocks)>500_000:raise ValueError('V4 non-air budget')
        super().set(p,s,owner)

def addmat(name,color):
    parse_state(name);PALETTE[name]=(name,color);return name
STONE=addmat('minecraft:smooth_stone','#B9C6C0')
QUARTZ=addmat('minecraft:smooth_quartz','#DFDDD0')
PAVE=addmat('minecraft:stone_bricks','#AAAFA8')
DARK=addmat('minecraft:polished_blackstone','#434B50')
GRASS=addmat('minecraft:moss_block','#748A50')
SOIL=addmat('minecraft:dirt','#726451')
GLASS=addmat('minecraft:light_blue_stained_glass','#829C9F')
WATER=addmat('minecraft:water[level=0]','#345766')
LEAVES=addmat('minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]','#527244')
LOG=addmat('minecraft:oak_log[axis=y]','#71634D')
LIGHT=addmat('minecraft:sea_lantern','#F0EACC')
WARM=addmat('minecraft:shroomlight','#ECC58D')
SLAB=addmat('minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]','#E1DECC')

def poly_margin(poly,x,z):
    p=np.asarray(poly)[:,[0,2]];q=np.roll(p,-1,axis=0);e=q-p
    cross=e[:,0]*(z-p[:,1])-e[:,1]*(x-p[:,0]);sign=1 if np.mean(cross)>=0 else -1
    return float(np.min(cross*sign/np.linalg.norm(e,axis=1)))

class V4Geometry(OpenLatticeGeometry):
    def __init__(self,c,p,v4):
        super().__init__(c,p);self.v4=v4;self.ring_audit=[]
    def frame(self,s):
        old=Scene(s.size);super().frame(old)
        levels=np.linspace(2,204,46)
        for k,y in enumerate(levels):
            outer=[self.at(j,y) for j in range(24)];center=np.mean(outer,axis=0);inner=[]
            for p in outer:
                v=p-center;v[1]=0;inner.append(p-v/np.linalg.norm(v)*self.v4['rings']['inset_blocks'])
            candidates=set()
            for a,b in zip(inner,inner[1:]+inner[:1]):candidates.update(face_path(a,b))
            margins=[];shaft_skip=0;core_overlap=0
            for q in sorted(candidates):
                margins.append(min(poly_margin(outer,q[0]+dx,q[2]+dz) for dx,dz in [(0,0),(0,1),(1,0),(1,1)]))
                if in_shaft(q):shaft_skip+=1;continue
                if s.owners.get(q)=='core':core_overlap+=1;continue
                s.set(q,PALETTE['ring'][0],f'frame.ring.{k:02}')
            # Short radial connectors, written before protected main members.
            for j,(a,b) in enumerate(zip(inner,outer)):
                for q in face_path(a,b):
                    if q not in s.blocks and not in_shaft(q):s.set(q,register_state(member_state(BARS)),f'frame.ring_joint.{k:02}.{j:02}')
            self.ring_audit.append({'id':f'frame.ring.{k:02}','y':float(y),'cells':len(candidates),'minimum_box_corner_margin':min(margins),'shaft_skips':shaft_skip,'core_contacts':core_overlap})
        for q,st in old.blocks.items():
            if not old.owners[q].startswith('frame.ring.'):s.set(q,st,old.owners[q])
    def lighting(self,s):
        counts={}
        for zone in self.zones:
            owner='program.'+zone['id'];n=0
            for q,state in list(s.blocks.items()):
                x,y,z=q
                if s.owners[q]==owner and state==PALETTE['floor'][0] and x%5==2 and z%5==2 and not in_shaft((x,y-1,z)) and y>zone['local_y_half_open'][0]:
                    s.set(q,LIGHT,f'lighting.interior.{zone["id"]}');n+=1
            counts[zone['id']]=n
        # Inset lights replace existing core shell, never add infill across open bands.
        for q,st in list(s.blocks.items()):
            if s.owners[q]=='core' and q[1]%12==7 and (q[0],q[2]) in [(25,28),(31,28),(28,25),(28,31)]:s.set(q,LIGHT,'lighting.core')
        return counts

def ell(x,z,cx,cz,a,b):return ((x+.5-cx)/a)**2+((z+.5-cz)/b)**2

def plaza(s,p):
    """2024/25 visual topology, authored approximation; no surveyed site plan."""
    sx,sy,sz=s.size;cx=p['axis_x'];grade=p['ground_top_y'];courts=p['courts']
    def write(x,y,z,st,owner):s.set((int(x),int(y),int(z)),st,owner)
    # Compact study boundary: surrounding roads, river and unrelated buildings excluded.
    for x in range(4,sx-4):
      for z in range(4,sz-4):
        lawn=(x<cx-34 or x>cx+34) and z>65 and not (z%36<5)
        surf=GRASS if lawn else PAVE
        if not lawn and (x%12==0 or z%16==0):surf=STONE
        write(x,grade-1,z,SOIL,'plaza.ground');write(x,grade,z,surf,'plaza.landscape' if lawn else 'plaza.paving')
    # Tower forecourt paving accent.
    for x in range(sx):
      for z in range(4,74):
        r=ell(x,z,cx,40.5,28,27)
        if .83<r<1:write(x,grade,z,QUARTZ,'plaza.tower_apron')
    for court in courts:
      ix= court['id'];ccx,ccz=court['center_xz'];a,b=court['radii'];floor=court['floor_y'];R=max(a,b)+12
      for x in range(max(0,int(ccx-R)),min(sx,int(ccx+R+1))):
       for z in range(max(0,int(ccz-R)),min(sz,int(ccz+R+1))):
        r=math.sqrt(ell(x,z,ccx,ccz,a,b));theta=math.atan2((z+.5-ccz)/b,(x+.5-ccx)/a)
        # Clear the light well through all surface layers; preserve a solid floor.
        if r<1:
         for y in range(floor+1,grade+8):write(x,y,z,AIR,'plaza.clear')
         write(x,floor-1,z,SOIL,f'plaza.{ix}.floor');write(x,floor,z,QUARTZ if int(r*15)%4==0 else STONE,f'plaza.{ix}.floor')
        # Two recessed shop levels around the perimeter, inward-facing glass.
        if .88<r<1:
         for y in range(floor+1,grade+1):
          st=GLASS if y not in [floor+3,grade] else QUARTZ
          if int(theta*18)%6==0:st=QUARTZ
          write(x,y,z,st,f'plaza.{ix}.gallery')
        # Mid-level gallery/balcony, leaving the centre genuinely open.
        if .72<r<.9:
         write(x,floor+3,z,QUARTZ,f'plaza.{ix}.gallery')
         if .72<r<.76:write(x,floor+4,z,GLASS,f'plaza.{ix}.rail')
        # Oval wave canopy, north complete; south steps towards the near end.
        if .99<r<1.19:
         roof=grade+1+int(round(court['canopy_rise']*(.5+.5*math.cos(theta+.7))))
         write(x,roof,z,SLAB,f'plaza.{ix}.canopy')
         if int((theta+math.pi)*20)%7==0 and 1.04<r<1.11:write(x,roof-1,z,LIGHT,f'lighting.plaza.{ix}.canopy')
         if 1.15<r<1.19:write(x,roof+1,z,GLASS,f'plaza.{ix}.canopy_rail')
        # Curved stepped seating on south court's far side.
        if ix=='south' and 1.18<=r<1.45 and theta>0:
         y=grade+max(0,4-int((r-1.18)*17))
         write(x,y,z,QUARTZ,f'plaza.{ix}.terrace')
      # A 7-block-wide staircase cutting the near edge; every tread has support.
      for step in range(grade-floor+1):
       z=int(ccz+b)-9+step
       for x in range(int(ccx)-3,int(ccx)+4):
        y=floor+step
        for yy in range(floor+1,grade+8):write(x,yy,z,AIR,'plaza.stair.clear')
        for yy in range(floor,y+1):write(x,yy,z,QUARTZ,f'plaza.{ix}.stairs')
        if step%2==0:
         write(int(ccx)-3,y,z,LIGHT,f'lighting.plaza.{ix}.stairs');write(int(ccx)+3,y,z,LIGHT,f'lighting.plaza.{ix}.stairs')
      # Continue a level bridge from stair top to outer walkway (2 cells).
      end=int(ccz+b)-9+grade-floor
      for z in range(end+1,int(ccz+b)+5):
       for x in range(int(ccx)-3,int(ccx)+4):
        for y in range(grade+1,grade+8):write(x,y,z,AIR,'plaza.entry.clear')
        write(x,grade,z,QUARTZ,f'plaza.{ix}.entry')
      # Photo-based refinement: sparse slanted canopy supports and lower-level lights.
      for k in range(12):
       theta=2*math.pi*k/12
       if math.sin(theta)>.9:continue # keep the south staircase open
       x=ccx+1.07*a*math.cos(theta);z=ccz+1.07*b*math.sin(theta)
       roof=grade+1+int(round(court['canopy_rise']*(.5+.5*math.cos(theta+.7))))
       thin_line(s,[x+math.cos(theta),grade,z+math.sin(theta)],[x,roof,z],WALL,f'plaza.{ix}.canopy_support')
      for k in range(16):
       theta=2*math.pi*k/16
       for radius,y in [(.5,floor),(.82,floor+3)]:
        q=(int(ccx+radius*a*math.cos(theta)),y,int(ccz+radius*b*math.sin(theta)))
        if q in s.blocks and s.owners[q].endswith(('.floor','.gallery')):
         s.set(q,LIGHT,f'lighting.plaza.{ix}.lower')
    # Contained reflection pool with bowed edges (authored curve, not traced survey).
    pool=set()
    for z in range(137,159):
     half=14+4*((z-147.5)/11.5)**2
     for x in range(int(cx-half),int(cx+half)+1):pool.add((x,z))
    for x,z in pool:
     edge=any((x+dx,z+dz) not in pool for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
     if edge:write(x,grade,z,QUARTZ,'plaza.pool.edge')
     else:
      write(x,grade-1,z,DARK,'plaza.pool.base');write(x,grade,z,WATER,'plaza.pool.water')
    # Small glazed access pavilions flanking axis; all deliberately schematic.
    for x0,z0 in [(18,101),(97,116),(18,177),(97,192)]:
     for x in range(x0,x0+9):
      for z in range(z0,z0+17):
       roof=grade+2+min(3,(z-z0)//4)
       for y in range(grade+1,roof):
        if x in [x0,x0+8] or z in [z0,z0+16]:
         if z==z0 and x0+3<=x<=x0+5 and y<=grade+3:continue
         write(x,y,z,GLASS,'plaza.access_pavilions')
       write(x,roof,z,GLASS if (z-z0)%4 else QUARTZ,'plaza.access_pavilions.roof')
     write(x0+4,grade+4,z0+8,LIGHT,'lighting.plaza.pavilions')
    # Two planted bands; tree positions avoid the courts, galleries and pavilions.
    for x in [10,27,100,117]:
     for z in range(74,sz-10,22):
      if any(ell(x,z,*v['center_xz'],v['radii'][0]+14,v['radii'][1]+14)<1 for v in courts):continue
      if any(abs(x-a)<12 and abs(z-b)<19 for a,b in [(18,101),(97,116),(18,177),(97,192)]):continue
      for y in range(grade+1,grade+6):write(x,y,z,LOG,'plaza.trees')
      for dx in range(-2,3):
       for dz in range(-2,3):
        for dy in range(3):
         if dx*dx+dz*dz+(dy-1)**2<=7:write(x+dx,grade+5+dy,z+dz,LEAVES,'plaza.trees')
    for x in [34,93]:
     for z in range(69,sz-9,14):
      if any(ell(x,z,*v['center_xz'],v['radii'][0]+5,v['radii'][1]+5)<1 for v in courts):continue
      for y in range(grade+1,grade+4):write(x,y,z,register_state(member_state(BARS)),'plaza.lamp_posts')
      write(x,grade+4,z,WARM,'lighting.plaza.paths')
