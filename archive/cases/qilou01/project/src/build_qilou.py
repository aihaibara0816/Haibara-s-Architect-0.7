"""Qilou01: three authored, connected Cantonese arcade shop-house studies.
Reference-inspired design, not a measured replica or a generic building solver.
"""
from pathlib import Path
import sys,json,hashlib,copy,gzip,io,random,math
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n,qilou_states
from prototype_base import Study
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state
RUN=sys.argv[1] if len(sys.argv)>1 else 'Q01'
SEED=int(sys.argv[2]) if len(sys.argv)>2 else 311145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=True)

def window(m,axis,c,a,b,y,h=3,out=1,tint='green',trim='quartz'):
 for u in range(a,b):
  x,z=(u,c) if axis=='x' else (c,u);dx,dz=(0,out) if axis=='x' else(out,0)
  for yy in range(y,y+h):m.p(x,yy,z,('white' if yy<y+h-1 else tint)+'_stained_glass_pane','window.glass')
  m.p(x,y-1,z,'dark_oak_planks','window.wood_sill')
  m.p(x,y+h,z,'dark_oak_planks','window.head')
  if 0<=x+dx<m.w and 0<=z+dz<m.d and not(axis=='x' and c==23 and y==4):
   m.p(x+dx,y-1,z+dz,trim+'_slab','window.projected_sill',type='top')
   m.p(x+dx,y+h,z+dz,trim+'_stairs','window.hood',facing={('x',1):'north',('x',-1):'south',('z',1):'west',('z',-1):'east'}[axis,out],half='top')
 for u in range(a+2,b,3):
  x,z=(u,c) if axis=='x' else(c,u)
  for yy in range(y,y+h):m.p(x,yy,z,'dark_oak_fence','window.mullion')

def table(m,x,z,f=2,w=3,d=1,chairs=True,id='table'):
 k=m.kit(f);k.table(x,z,w,d,id,'dark_oak')
 if chairs:
  k.chair(x,z-1,'south',material='dark_oak');k.chair(x+w-1,z+d,'north',material='dark_oak')
 m.p(x+1,f+2,z,'flower_pot',id+'.cup')
 if w>=3:m.p(x+w-1,f+2,z,'white_carpet',id+'.cloth')
 m.addkit(k)

def bench(m,x,z,f=2,w=3,color='green'):
 for xx in range(x,x+w):
  m.p(xx,f+1,z,'dark_oak_slab','bench.seat',type='bottom')
  m.p(xx,f+1,z+1,color+'_wool','bench.back');m.p(xx,f+2,z+1,color+'_carpet','bench.soft_edge')
 for xx,face in[(x-1,'west'),(x+w,'east')]:m.p(xx,f+1,z,'dark_oak_trapdoor','bench.arm',facing=face,open=True)

def kitchen(m,x,z,f=2,w=5):
 k=m.kit(f)
 for xx in range(x,x+w):m.barrel(xx,f+1,z);m.p(xx,f+2,z,'dark_oak_trapdoor','kitchen.countertop',half='bottom')
 k.furnace(x,z);k.sink(x+2,z)
 for xx in range(x,x+w):
  m.p(xx,f+3,z,'stone_bricks','kitchen.splashback');m.p(xx,f+4,z,'dark_oak_slab','kitchen.shelf',type='top')
 for xx in[x+1,x+w-1]:m.p(xx,f+5,z,'flower_pot','kitchen.storage_pot')
 m.addkit(k)

def bedroom(m,f,x0=6,x1=None):
 x1=x1 or m.w-2
 m.box((x0,f+1,4),(x0+1,f+6,14),'white_terracotta','bedroom.partition')
 m.box((x0,f+1,13),(x1+1,f+6,14),'white_terracotta','bedroom.partition')
 m.door(x0+3,f+1,13,wood='dark_oak')
 k=m.kit(f);k.bed(x0+3,8);k.cupboard(x1-1,5,1,'wardrobe')
 for xx in range(x0+2,x0+5):m.p(xx,f+1,6,'dark_oak_trapdoor','bed.headboard',facing='north',open=True)
 m.barrel(x0+2,f+1,7);m.pot(x0+2,f+2,7)
 for xx in range(x0+2,x0+5):m.p(xx,f+1,10,'light_gray_carpet','bed.rug')
 m.addkit(k);m.use('bed.'+str(f),x0+4,8,f)
 m.room('bed.'+str(f),'店主卧室',x0+1,4,x1+1,13,f,1)
 # Small screened wash room, clearly separate from the bed.
 m.box((1,f+1,4),(5,f+5,5),'white_terracotta','wash.wall')
 m.box((4,f+1,4),(5,f+5,7),'white_terracotta','wash.wall')
 m.door(2,f+1,6,wood='birch');m.p(1,f+1,5,'water_cauldron','wash',level=3)
 m.use('wash.'+str(f),2,5,f)

def circulation(m):
 m.upper_starts={};m.stair_runs=[]
 for j,(f,up) in enumerate(zip(m.floors,m.floors[1:])):
  rise=up-f;start=15;end=start-rise-1
  for xx in[1,2]:
   m.box((xx,f+1,end+1),(xx+1,up+3,start+1),'air','stair.clear')
   for t in range(rise):m.p(xx,f+1+t,start-1-t,'dark_oak_stairs','stair.tread',facing='north')
   m.p(xx,up,end,'oak_planks','stair.landing')
   m.p(xx,f,start,'oak_planks','stair.lower_landing')
  for z in range(end+1,start+1):m.p(3,up+1,z,'dark_oak_fence','stair.guard')
  # Fixed stair openings, with under-stair stock only where adequate headroom is irrelevant.
  if j==0:
   for x in[1,2]:m.barrel(x,f+1,end+2)
  path=[[1.5,f+1,start+.5-i*.125]for i in range(int((start-end)*8)+1)]
  m.stair_paths.append(path);m.stair_runs.append({'from_floor':f,'to_floor':up,'path':path})
  m.upper_starts[str(up)]=[1,end]
  m.use('stairs.lower.'+str(f),1,start,f);m.use('stairs.upper.'+str(up),1,end,up)
  m.lamp(4,up-2,15)

def build_shell(id,w,levels,name,wall,kind):
 m=Study(id,w,33,levels,name);m.seed=SEED;m.floors=[2,9,15][:levels];m.h=34;m.owners={};m.variation=[];m.kind=kind
 m.source=['E01 Enning street','E02 Enning 140 facade','E03 arcade portal','E04 Fuxing adaptive reuse interior']
 m.box((0,0,0),(w,2,33),'dirt','base')
 m.box((0,2,0),(w,3,33),'stone_bricks','paving')
 # Four clear blocks between the shop wall and the front pier line.
 for x in range(w):
  for z in range(24,28):m.p(x,2,z,'polished_andesite' if (x//4+z//2)%7==0 else 'smooth_stone','arcade.floor')
 top=(15 if levels==2 else 21)
 def in_upper(x,z):return 0<=x<w and 3<=z<=28 and not(kind=='corner' and x+z>47)
 for fi,f in enumerate(m.floors):
  ceiling=m.floors[fi+1] if fi+1<len(m.floors) else top
  front=23 if fi==0 else(25 if kind=='classical' else 28)
  side=w-6 if kind=='corner' and fi==0 else w-1
  for x in range(w):
   for z in range(3,29):
    if in_upper(x,z):
     m.p(x,ceiling,z,'oak_planks','floor_or_ceiling')
     if fi>0 or (z<=front and x<=side):m.p(x,f,z,'oak_planks' if fi else 'polished_diorite','floor')
  for y in range(f+1,ceiling):
   for x in range(side+1):
    m.p(x,y,3,wall,'rear.wall');m.p(x,y,front,wall,'front.wall')
   for z in range(3,front+1):m.p(0,y,z,wall,'party.wall');m.p(side,y,z,wall,'side.wall')
  if kind=='corner' and fi>0:
   # Replace the square corner with a three-block splay, coherent on every floor.
   for x in range(w):
    for z in range(24,29):
     if x+z>47:m.box((x,f,z),(x+1,ceiling+1,z+1),'air','corner.cut')
     elif x+z==47:m.box((x,f+1,z),(x+1,ceiling,z+1),wall,'corner.splay')
  # Secondary elevations have real windows; party wall remains mostly solid.
  window(m,'x',3,6,min(w-2,12),f+2,2,-1,'green')
  if kind=='corner':
   for a,b in[(6,10),(13,17),(20,24)]:
    if fi>0:window(m,'z',w-1,a,b,f+2,2,1,'green')
  # Non-corner right walls meet the next shop; only front/rear windows are used there.
  if fi>0:
   for a,b in ([(2,6),(9,13)] if w==15 else [(2,6),(10,14)] if w==17 else [(2,6),(9,14),(16,19)]):
    window(m,'x',front,a,b,f+2,3 if kind!='corner' else 2,1,'green' if a<8 else 'cyan')
   if kind=='classical':
    m.door(w//2,f+1,25,wood='dark_oak')
    for x in range(1,w-1):m.p(x,f+1,28,'iron_bars','balcony.rail');m.p(x,f+2,28,'quartz_slab','balcony.cap',type='bottom')
    m.use('balcony.'+str(f),w//2,27,f)
  # Interior beams and varied light anchors follow use zones, not a universal grid.
  for z in[12,21]:
   for x in range(1,side):m.p(x,ceiling-1,z,'dark_oak_slab','interior.beam',type='top')
  for x,z in[(w//2,19),(max(7,w//2),7),(max(5,side-3),12)]:m.lamp(x,ceiling-2,z)
 # Arcade columns carry the upper facade; no cross-party ground wall in the corridor.
 cols=([0,7,14] if w==15 else [0,8,16] if w==17 else [0,7,14])
 for x in cols:
  m.p(x,3,28,'polished_andesite','column.base')
  for y in range(4,8):m.p(x,y,28,'quartz_pillar','column.shaft',axis='y')
  m.p(x,8,28,'chiseled_quartz_block','column.capital')
  for dx in[-1,1]:
   if 0<=x+dx<w:m.p(x+dx,8,28,'quartz_stairs','column.abacus',half='top',facing='east' if dx<0 else 'west')
 if kind=='corner':
  for x,z in[(20,27),(22,19),(22,11),(22,3)]:
   m.p(x,3,z,'polished_andesite','column.base')
   for y in range(4,8):m.p(x,y,z,'quartz_pillar','column.shaft',axis='y')
   m.p(x,8,z,'chiseled_quartz_block','column.capital')
  for a,b in[(0,7),(7,14)]:
   for xx in[a+1,b-1]:m.p(xx,7,28,'quartz_stairs','arch.haunch',facing='east' if xx==a+1 else 'west',half='top')
  for a,b in[(3,11),(11,19)]:
   for zz in[a+1,b-1]:m.p(22,7,zz,'quartz_stairs','arch.haunch',facing='south' if zz==a+1 else 'north',half='top')
 # Continuous fascia/cornice on public sides, modest ornament at selected bays.
 for y in[9,top]:
  for x in range(w):
   if in_upper(x,28):m.p(x,y,29,'quartz_slab','public.cornice',type='top')
  if kind=='corner':
   for z in range(3,26):m.p(22,y,z,'quartz_slab','side.cornice',type='top')
 if kind=='classical':
  for x in[0,w-1]:
   for y in range(10,top):m.p(x,y,28,'quartz_pillar','giant.pilaster',axis='y')
   m.p(x,top,29,'chiseled_quartz_block','giant.capital')
 elif kind=='corner':
  for x in[0,7,15]:
   for y in range(10,top):m.p(x,y,29,'quartz_slab','pilaster',type='double')
  # Circular colored-window motif is a block-scale interpretation, not replicated carving.
  for x in range(9,14):
   for y in range(16,21):
    dist=(x-11)**2+(y-18)**2
    if dist<=5:m.p(x,y,28,'green_stained_glass_pane' if (x+y)%3 else 'cyan_stained_glass_pane','round.window')
    elif dist<=8:m.p(x,y,29,'smooth_quartz','round.frame')
 # Roof behind the parapet, rear slopes; no giant Japanese overhanging tile roof.
 for x in range(1,w-1):
  for z in range(4,24):
   h=top+min(x,w-1-x)//4
   m.p(x,h,z,'deepslate_tile_slab','rear.roof',type='top' if x%2 else 'bottom')
 for x in range(w):
  if not in_upper(x,28):continue
  crest=(1 if kind=='plain' else 2)+max(0,(2 if kind=='plain' else 3)-abs(x-(7 if kind=='plain' else 8 if kind=='classical' else 11))//2)
  for y in range(top+1,top+crest+1):m.p(x,y,28,wall,'parapet.wall')
  m.p(x,top+crest+1,28,'quartz_slab','parapet.coping',type='top')
  if x%4==2:m.p(x,top+1,29,'chiseled_quartz_block','parapet.relief')
 if kind=='corner':
  for z in range(3,26):
   for y in[22,23]:m.p(22,y,z,wall,'side.parapet')
   m.p(22,24,z,'quartz_slab','side.coping',type='top')
 # Rear gutter/downpipe is attached to the facade, not random wall damage.
 for y in range(3,top+1):m.p(w-2,y,2,'diorite_wall','rear.downpipe',up=True)
 # Setback storefront and door/frame all share their own plane.
 ent=w//2 if kind!='corner' else 10
 m.door(ent,3,23,wood='dark_oak');m.entry=[ent,3,23]
 for a,b in[(1,ent-1),(ent+2,(w-6 if kind=='corner' else w-1))]:
  if b>a:window(m,'x',23,a,b,4,2,1,'green','dark_oak')
 for x in range(1,(w-5 if kind=='corner' else w-1)):m.p(x,7,23,'dark_oak_planks','shop.signband')
 m.sign(ent,7,24,'south',[name,'下店上居' if kind!='corner' else '茶・点心'])
 if kind=='corner':m.door(17,3,16,'east','dark_oak');m.use('side_entry',16,16)
 # Lights are on the store side, well above the four-wide walking strip.
 for x in[3,w-4]:m.lamp(x,7,25)
 # A single recess-side plant pair, not one identical pot under every column.
 m.barrel(1,3,22);m.pot(1,4,22)
 m.use('main_entry',ent,22)
 return m

def grocery():
 m=build_shell('Grocery',15,2,'和顺杂货','white_terracotta','plain')
 k=m.kit(2)
 for x in[2,4]:
  for z in[18,21]:m.barrel(x,3,z);m.p(x,4,z,'flower_pot','wares.pot')
 for z in range(16,22):
  m.barrel(13,3,z,'west');m.p(13,5,z,'dark_oak_slab','wares.shelf',type='top')
  if z%2==0:m.p(13,6,z,'flower_pot','wares.upper')
 for x in range(8,13):m.barrel(x,3,17);m.p(x,4,17,'dark_oak_trapdoor','counter.trim')
 k.table(9,10,3,2,'packing','dark_oak');m.p(10,4,10,'white_carpet','packing.paper');m.addkit(k)
 kitchen(m,7,4,2,6)
 m.box((5,3,13),(14,9,14),'white_terracotta','backroom.partition');m.door(9,3,13,wood='dark_oak')
 bedroom(m,9)
 bench(m,7,25,9,4,'brown');table(m,8,22,9,3,1,False,'tea.table')
 table(m,8,17,9,3,1,True,'family.dining');m.p(12,10,19,'bookshelf','living.books');m.barrel(12,10,24);m.pot(12,11,24)
 for a in[('browse',6,20,2),('pay',10,19,2),('staff',11,16,2),('packing',9,12,2),('kitchen',10,6,2),('living',6,24,9),('dining',12,17,9)]:m.use(*a)
 for a in[('shop','杂货陈列与结账',1,14,14,23,2,5),('back','备货与厨房',5,4,14,13,2,2),('living','起居、茶桌与餐桌',5,15,14,28,9,3)]:m.room(*a)
 circulation(m);return m

def apothecary():
 m=build_shell('Apothecary',17,3,'济安药铺','white_concrete','classical')
 # Drawer walls are broken by open vessel shelves and work surfaces.
 for x in range(6,16):
  for y in[3,4]:m.barrel(x,y,10)
  if x%3:m.p(x,6,10,'dark_oak_slab','medicine.shelf',type='top');m.p(x,7,10,'flower_pot','medicine.jar')
 for x in range(7,15):m.barrel(x,3,16);m.p(x,4,16,'dark_oak_trapdoor','counter.edge')
 for x in[8,12]:m.p(x,4,16,'flower_pot','counter.jar')
 table(m,9,13,2,4,1,False,'medicine.weighing');table(m,4,19,2,2,1,True,'consultation')
 bench(m,10,21,2,4,'green')
 # Middle floor combines inventory with ledger and packing work, separate from the residence.
 for x in[6,10,14]:
  for z in[5,8,11]:m.barrel(x,10,z);m.barrel(x,11,z)
 k=m.kit(9);k.shelf(6,16,3,2,'account.archive');m.addkit(k)
 table(m,8,20,9,4,2,True,'accounts');m.barrel(14,10,22);m.pot(14,11,22)
 bedroom(m,15,6,15);kitchen(m,7,15,15,6)
 bench(m,7,21,15,4,'green');table(m,8,18,15,3,1,False,'living.tea')
 for a in[('consult',7,20,2),('counter',10,18,2),('preparation',13,14,2),('drawers',12,11,2),('inventory',12,8,9),('accounts',13,20,9),('home',6,22,15),('home.kitchen',10,17,15)]:m.use(*a)
 for a in[('dispense','药柜、称量与发药',5,10,16,19,2,3),('waiting','咨询与等候',2,18,16,23,2,5),('inventory','库存与分装',5,4,16,14,9,2),('accounts','账房与包装',5,15,16,25,9,2),('home','店主起居',5,15,16,25,15,3)]:m.room(*a)
 circulation(m);return m

def teahouse():
 m=build_shell('Teahouse',23,3,'榕荫茶楼','smooth_sandstone','corner')
 # Ground-floor kitchen and washing screened from guests.
 m.box((5,3,11),(17,9,12),'white_terracotta','kitchen.partition');m.door(13,3,11,wood='dark_oak')
 kitchen(m,7,4,2,8);table(m,8,8,2,4,1,False,'prep')
 for x,z in[(5,17),(11,20)]:table(m,x,z,2,3,2,True,'guest.table')
 bench(m,2,21,2,3,'brown');m.barrel(15,3,13);m.p(15,4,13,'flower_pot','tea.service')
 # Upstairs public tea room with varied seating sizes, booth and service sideboard.
 for x,z,w in[(6,18,3),(13,21,4),(17,12,3),(7,8,4)]:table(m,x,z,9,w,2,True,'tea.room')
 bench(m,7,25,9,5,'brown');table(m,8,23,9,4,1,False,'booth.tea')
 for z in[5,6,7]:m.barrel(20,10,z,'west')
 m.p(20,11,6,'flower_pot','service.cup');m.p(20,11,7,'flower_pot','service.cup')
 m.barrel(20,10,21);m.pot(20,11,21)
 # Third level: family / staff home rather than repeating a restaurant plan.
 bedroom(m,15,6,15);kitchen(m,16,4,15,5)
 bench(m,7,24,15,5,'green');table(m,8,21,15,4,1,False,'home.tea');table(m,16,17,15,3,2,True,'home.dining')
 k=m.kit(15);k.shelf(17,9,3,3,'home.books');m.addkit(k)
 m.barrel(20,16,24);m.pot(20,17,24)
 # Small independent plant cluster against a solid bay, away from the L arcade.
 m.barrel(16,3,21);m.pot(16,4,21)
 for a in[('ground.seats',9,18,2),('kitchen',12,7,2),('wash',13,6,2),('tea.room',12,18,9),('tea.service',19,7,9),('window.booth',13,25,9),('home.living',6,23,15),('home.dining',20,17,15),('home.books',18,10,15)]:m.use(*a)
 for a in[('restaurant','首层茶座与收银',1,12,17,23,2,10),('kitchen','备餐、炉灶、清洗',5,4,17,11,2,3),('tearoom','二层茶厅、窗边长座与服务柜',5,4,22,28,9,18),('home','三层起居、餐厨与书柜',5,14,22,28,15,4)]:m.room(*a)
 circulation(m);return m

def interior_finish(m):
 # Layered shop fit-out: a restrained wall base, integrated door trim, and purpose-led wall furnishings.
 wallnames={'minecraft:white_terracotta','minecraft:white_concrete','minecraft:smooth_sandstone'}
 for f in m.floors:
  for q,st in list(m.blocks.items()):
   x,y,z=q
   if y==f+1 and st in wallnames and (x in [0,m.w-1] or z in [3,13 if m.id=='Grocery' else 11 if m.id=='Teahouse' and f==2 else -1]):
    m.p(x,y,z,'dark_oak_planks','interior.wainscot')
 for d in m.doors:
  x,y,z=d['pos'];dx,dz=(1,0) if d['facing'] in ['north','south'] else (0,1)
  m.p(x,y+2,z,'dark_oak_planks','door.integrated_head')
  for sg in [-1,1]:
   for yy in [y,y+1]:m.p(x+sg*dx,yy,z+sg*dz,'dark_oak_planks','door.integrated_jamb')
 if m.id=='Grocery':
  for x in [5,6,7]:
   m.barrel(x,3,14);m.p(x,4,14,'dark_oak_slab','wares.counter',type='top')
   m.p(x,5,14,'flower_pot','wares.jars');m.p(x,6,14,'dark_oak_slab','wares.upper',type='top')
   if x!=6:m.p(x,7,14,'flower_pot','wares.jars')
  for z in range(17,22):
   for y in [4,6]:m.p(1,y,z,'dark_oak_slab','wares.wall_shelf',type='top')
   if z%2:
    m.p(1,5,z,'flower_pot','wares.ceramics');m.p(1,7,z,'flower_pot','wares.ceramics')
  m.picture(11,6,14,'south','bomb')
  m.barrel(12,10,15);m.pot(12,11,15)
 elif m.id=='Apothecary':
  # Separate stock drawers from the front counter with a full-height framed display.
  for x in [5,15]:
   for y in range(3,8):m.p(x,y,10,'dark_oak_planks','medicine.cabinet_frame')
  for x in range(5,16):m.p(x,8,10,'dark_oak_slab','medicine.cornice',type='top')
  for z in [17,18,19]:
   m.barrel(15,3,z,'west');m.p(15,4,z,'dark_oak_slab','dispensary.sideboard',type='top')
  m.pot(15,5,19)
 elif m.id=='Teahouse':
  for x in range(6,11):
   m.barrel(x,3,12);m.p(x,4,12,'dark_oak_slab','tea.service_counter',type='top')
  for x in [6,9]:m.p(x,5,12,'flower_pot','tea.cups')
  m.pot(10,5,12)
  for x,var in [(7,'kebab'),(10,'bomb'),(15,'aztec')]:m.picture(x,6,12,'south',var)
  for x in range(6,17):m.p(x,8,12,'dark_oak_slab','wall.picture_rail',type='top')
  for x in [14,15,16,17]:
   m.barrel(x,10,4);m.p(x,11,4,'dark_oak_slab','upper.tea_sideboard',type='top')
   if x%2:m.p(x,12,4,'flower_pot','upper.tea_cups')
  for x,z,f in [(16,18,2),(20,18,9),(5,26,9),(20,23,15)]:
   if (x,f+1,z)not in m.blocks:
    m.p(x,f+1,z,'terracotta','plant.container');m.pot(x,f+2,z)
 return m

def finish(m):
 # Group-wise, separately seeded ceramic/plant choices; structure and route never sampled.
 for i,(x,z,f) in enumerate([(m.w-3,4,2),(m.w-3,24,max(m.floors))]):
  # Valid candidates only: the second is skipped if it would occupy a balcony or doorway.
  if m.kind=='classical' and z>=24:continue
  if m.kind=='corner' and f==2 and x>=18:continue
  if (x,f+1,z) in m.blocks:continue
  rng=random.Random(f'{SEED}/plants/{m.id}/{i}');plant=rng.choice(['potted_fern','potted_bamboo','potted_azalea_bush'])
  m.p(x,f+1,z,'terracotta','plant.pot');m.p(x,f+2,z,plant,'plant.group')
  m.variation.append({'id':f'{m.id}.plant.{i}','channel':'plant','seed':f'{SEED}/plants/{m.id}/{i}','selected':plant,'position':[x,f+2,z]})
 # Fully supported small artwork in the rear living wall.
 f=max(m.floors);m.picture(7,f+3,4,'south','aztec')
 m.p(7,f+3,3,'dark_oak_planks','art.back')
 for lamp in m.lights:m.p(*lamp['support'],'chain','light.chain',axis='y')
 return m

def save(m,name,sp,size):
 sc=Scene(size,max_cells=2000000)
 for q,st in m.blocks.items():sc.set(q,st,m.owners.get(q,'detail'))
 S.connect(sc)
 for st in set(sc.blocks.values()):S.validate(st)
 raw=OUT/(name+'.tmp');export_structure(sc,raw,include_air=False);f=n.load(raw)
 for b in f['blocks']:
  q=tuple(map(int,b['pos']))
  if q in m.bes:
   be=m.bes[q];name0=sc.blocks[q].split('[')[0]
   expect='minecraft:sign' if name0.endswith('_wall_sign') else 'minecraft:bed' if name0.endswith('_bed') else name0
   assert str(be['id'])==expect,(q,name0,be)
   b['nbt']=be
 f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(e['Pos']),'blockPos':n.List[n.Int]([e[k]for k in['TileX','TileY','TileZ']]),'nbt':e})for e in m.entities])
 buf=io.BytesIO();f.write(buf);p=OUT/(name+'.nbt');p.write_bytes(gzip.compress(buf.getvalue(),mtime=0));raw.unlink()
 if 'size' in sp:sp['size']=list(size)
 sp.update(source_nbt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size_xyz=list(size),non_air=len(sc.blocks),block_entities=len(m.bes),entities=len(m.entities))
 (OUT/(name+'_spec.json')).write_text(json.dumps(sp,ensure_ascii=False,indent=2));return sp

mods=[finish(interior_finish(grocery())),finish(interior_finish(apothecary())),finish(interior_finish(teahouse()))]
city=Study('Qilou01',76,52,1,'西关骑楼三栋试作');city.seed=SEED;city.box((0,0,0),(76,2,52),'dirt','test.site');city.box((0,2,0),(76,3,52),'smooth_stone','test.paving')
# A bounded street strip only; the full neighborhood is intentionally not generated yet.
for x in range(76):
 for z in range(37,46):city.p(x,2,z,'andesite','street.surface')
 city.p(x,2,36,'polished_andesite','street.kerb')
records=[];ox=7
for m in mods:
 sp=m.stats();sp.update(kind=m.kind,levels=m.levels,upper_starts=m.upper_starts,stair_runs=m.stair_runs,spawn_local=[m.w//2,3,31],arcade_clear=[0,3,24,m.w,7,28],variation=m.variation)
 save(m,m.id,sp,(m.w,m.h,m.d));origin=[ox,0,6]
 for q,st in m.blocks.items():city.p(q[0]+ox,q[1],q[2]+6,st,m.owners.get(q,'detail'))
 for q,be in m.bes.items():city.bes[q[0]+ox,q[1],q[2]+6]=copy.deepcopy(be)
 for e in m.entities:
  ee=copy.deepcopy(e);ee['Pos']=n.List[n.Double]([n.Double(float(e['Pos'][i])+origin[i])for i in range(3)])
  for i,k in enumerate(['TileX','TileY','TileZ']):ee[k]=n.Int(int(ee[k])+origin[i])
  city.entities.append(ee)
 records.append({'id':m.id,'name':m.program,'origin':origin,'size':[m.w,m.h,m.d],'floors':m.floors,'entry':[m.entry[i]+origin[i]for i in range(3)],'kind':m.kind})
 ox+=m.w
# Small rear planters: street test stays readable, no forest transplanted into this urban case.
for x in[4,69]:
 city.box((x,3,12),(x+2,4,16),'stone_bricks','planter.base')
 for z in range(12,16):city.p(x,4,z,'azalea_leaves','planter.shrub');city.p(x+1,4,z,'azalea_leaves','planter.shrub')
sp={'case_id':'Qilou01','run':RUN,'mainline':'HAF 0.4','seed':SEED,'scope':'Three connected prototype shop-houses; not a complete streetscape or measured replica','coordinates':{'X':'east','Y':'up','Z':'south','front':'south'},'spawn_local':[35,3,43],'buildings':records,'arcade_paths':[{'id':'continuous_front','bounds':[7,3,30,59,7,34]},{'id':'corner_return','bounds':[57,3,10,61,7,30]},{'id':'corner_splay','bounds':[57,3,30,61,7,33]}],'status':{'game':'pending','aesthetic':'pending user review'}}
save(city,'Qilou01',sp,(76,40,52));(OUT/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2))
print(json.dumps({'run':RUN,'buildings':3,'blocks':len(city.blocks),'seed':SEED,'sha256':sp['source_nbt_sha256']}))
