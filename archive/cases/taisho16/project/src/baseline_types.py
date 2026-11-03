"""Taisho12, three authored types. HAF 0.4. Not measured historical replicas."""
from pathlib import Path
import sys,json,hashlib,copy,io,gzip,random,os
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
from prototype_base import Study
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure
import nbtlib as n
SEED=1145
# Same epoch, three genuinely different use and silhouette families.
def init(id,w,d,name):
 m=Study(id,w,d,2,name);m.seed=SEED;m.floors=[2,8];m.ground();return m
def frame(m,axis,c,a,b,y=4,h=3,out=1,trim='dark_oak',tint='green'):
 for u in range(a,b):
  x,z=(u,c)if axis=='x'else(c,u);dx,dz=(0,out)if axis=='x'else(out,0)
  for yy in range(y,y+h):m.p(x,yy,z,('white'if yy<y+h-1 else tint)+'_stained_glass_pane','window')
  for yy in[y-1,y+h]:m.p(x,yy,z,trim+'_planks'if trim in['oak','dark_oak','spruce']else'smooth_quartz','window.frame')
  m.p(x+dx,y-1,z+dz,trim+'_slab','window.sill',type='top')
  m.p(x+dx,y+h,z+dz,trim+'_stairs','window.hood',half='top',facing={('x',1):'north',('x',-1):'south',('z',1):'west',('z',-1):'east'}[axis,out])
 for u in range(a+2,b,3):
  x,z=(u,c)if axis=='x'else(c,u)
  for yy in range(y,y+h):m.p(x,yy,z,'dark_oak_fence','window.mullion')
def lamps(m,positions):
 for x,y,z in positions:
  m.lamp(x,y,z);m.p(x,y+1,z,'chain','light.chain',axis='y')
def stairs(m,x,z):
 for xx in[x,x+1]:
  m.box((xx,3,z),(xx+1,14,z+8),'air','stair.clear')
  for t in range(6):m.p(xx,3+t,z+6-t,'spruce_stairs','stair',facing='north')
  m.p(xx,8,z,'oak_planks','landing')
 for zz in range(z+1,z+8):m.p(x+2,9,zz,'dark_oak_fence','stair.guard')
 m.stair_paths=[[[x+.5,3,z+7.5-i*.125]for i in range(57)]]
 m.upper_start=[x,z];m.use('stairs.bottom',x,z+7);m.use('stairs.top',x,z,8)
 for xx in[x,x+1]:m.barrel(xx,3,z+1)
def beam(m,x,X,z,y):m.box((x,y,z),(X,y+1,z+1),'stripped_spruce_log','ceiling.beam',axis='x')
def sign(m,x,y,z,text):m.p(x,y,z-1,'dark_oak_planks','sign.back');m.sign(x,y,z,'south',text)
def picture(m,x,y,z):m.p(x,y,z-1,'dark_oak_planks','art.back');m.picture(x,y,z,'south','aztec')
def seat(m,x,z,f=2,w=3,color='brown'):
 for xx in range(x,x+w):m.p(xx,f+1,z,'dark_oak_slab','seat',type='bottom');m.p(xx,f+1,z+1,color+'_wool','soft.back');m.p(xx,f+2,z+1,color+'_carpet','soft.edge')
 for xx,face in[(x-1,'west'),(x+w,'east')]:m.p(xx,f+1,z,'dark_oak_trapdoor','arm',facing=face,open=True)
def finish(m):
 rr=random.Random(SEED+sum(map(ord,m.id)))
 for x in range(m.w):
  for z in range(m.d-4,m.d):m.p(x,2,z,rr.choices(['cobblestone','andesite','mossy_cobblestone'],[82,14,4])[0],'street')
 for x,z in[(2,3),(m.w-3,5),(2,m.d-6)]:
  m.p(x,3,z,'terracotta','pot');m.p(x,4,z,'azalea_leaves','shrub');m.pot(x+1,3,z)
 for x in range(1,m.w-1):
  for z in range(1,m.d-4):
   if m.blocks.get((x,2,z))==S.make('grass_block') and (x,3,z)not in m.blocks and rr.random()<.22:m.p(x,3,z,rr.choice(['short_grass','fern','oxeye_daisy']),'groundcover')
 for q,be in list(m.bes.items()):
  name=m.blocks.get(q,'air').split('[')[0];bid=str(be['id']);expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else name
  assert bid==expected,(m.id,q,bid,name)
 return m

def bookstore():
 m=init('Bookshop',28,36,'青葉書肆｜铜板门面书店');m.source=['Chiyoda-kanban','Haikara4']
 for f,top in[(2,8),(8,14)]:
  m.shell_rect(4,5,23,28,f,top,'white_terracotta','spruce_planks')
  for z in[5,27]:beam(m,4,23,z,top-1)
  for x in[4,22]:
   m.box((x,f+1,5),(x+1,top,6),'stripped_spruce_log','timber.post',axis='y');m.box((x,f+1,27),(x+1,top,28),'stripped_spruce_log','timber.post',axis='y')
  for a,b in[(9,13),(18,23)]:frame(m,'z',22,a,b,f+2,3,1)
  frame(m,'x',5,10,21,f+2,3,-1);frame(m,'z',4,19,25,f+2,3,-1)
 # Timber roof extends in depth behind a narrow, tall decorated street face.
 for x in range(3,24):
  for z in range(3,28):
   t=min(x-3,23-x);m.p(x,14+t//2,z,'deepslate_tile_slab','rear.gable',type='top'if t%2 else'bottom')
   if z in[5,26]:
    for y in range(14,14+t//2):m.p(x,y,z,'white_terracotta','attic')
 for z in range(3,28):m.p(13,20,z,'polished_deepslate_slab','ridge',type='bottom')
 # Kanban front is a wall attached to timber body, with separate reliefs and recessed windows.
 m.box((4,3,27),(23,19,28),'oxidized_copper','kanban.face')
 for y in[3,8,14,18]:
  for x in range(3,24):m.p(x,y,28,'quartz_slab','cornice',type='top')
 for x in[4,10,16,22]:
  for y in range(9,18):m.p(x,y,28,'dark_prismarine','pilaster')
  m.p(x,17,29,'quartz_stairs','capital',facing='north',half='top')
 for a,b in[(5,10),(11,16),(17,22)]:
  frame(m,'x',27,a,b,10,3,1,trim='quartz',tint='cyan')
  m.p((a+b)//2,15,28,'smooth_quartz','ornament');m.p((a+b)//2,16,28,'quartz_stairs','ornament',facing='north')
 # shallow stepped crest, not full width giant triangle
 for a,b,y in[(8,19,19),(10,17,20),(12,15,21)]:
  for x in range(a,b):m.p(x,y,27,'oxidized_copper','crest');m.p(x,y,28,'quartz_slab','crest.edge',type='top')
 for a,b in[(5,11),(16,22)]:frame(m,'x',27,a,b,4,2,1,trim='dark_oak')
 m.door(13,3,27);m.entry=[13,3,27]
 for x in range(4,23):
  for z in[28,29]:m.p(x,6+(z==28),z,'dark_oak_slab','shop.canopy',type='top')
 for x in[5,10,16,21]:m.p(x,6,28,'dark_oak_stairs','canopy.bracket',facing='north',half='top')
 sign(m,13,8,29,['青 葉 書 肆','古書・文具']);sign(m,6,4,30,['新刊・古書','BOOKS'])
 # Inside ground: perimeter catalogue, two browse islands, counter and a packing area.
 stairs(m,5,7);k=m.kit(2)
 for z in[18,22]:
  k.shelf(5,z,1,3,'wall.books');k.shelf(21,z,1,3,'wall.books')
 for x in[9,16]:k.shelf(x,17,2,2,'browse');k.shelf(x,18,2,2,'browse')
 for x in range(12,21):m.barrel(x,3,9);m.p(x,4,9,'dark_oak_trapdoor','counter.top',half='bottom')
 k.table(13,6,5,1,'packing','dark_oak');m.p(14,4,6,'white_carpet','paper');m.p(17,4,6,'flower_pot','ink')
 k.shelf(19,6,2,3,'archive');k.table(7,25,3,1,'window.display','dark_oak');m.p(8,4,25,'white_carpet','books.paper')
 seat(m,17,24);m.barrel(20,3,24);m.pot(20,4,24);m.addkit(k)
 picture(m,15,5,6);picture(m,20,5,14)
 for x,z in[(10,23),(19,21)]:m.barrel(x,3,z);m.pot(x,4,z)
 # Added short browsable wall runs, a paper display and a small reading spot.
 extra=m.kit(2)
 for z in [19,20,23,24]:
  extra.shelf(5,z,1,3,'wall.run');extra.shelf(21,z,1,3,'wall.run')
 extra.table(11,23,4,1,'new.books','dark_oak');m.p(12,4,23,'white_carpet','paper.stack');m.p(14,4,23,'flower_pot','ink');m.addkit(extra)
 # Upstairs: private bedroom behind a door; editorial worktable and reading wall in front.
 m.box((15,9,6),(16,14,14),'white_terracotta','private.wall');m.box((16,9,13),(22,14,14),'white_terracotta','private.wall');m.door(18,9,13,wood='birch')
 u=m.kit(8);u.bed(18,9);u.bed(19,9);u.cupboard(20,6,2,'wardrobe');m.barrel(17,9,8);m.pot(17,10,8)
 for x in[18,19]:m.p(x,9,7,'dark_oak_trapdoor','headboard',facing='north',open=True)
 u.shelf(8,6,6,3,'upper.archive');u.table(10,16,5,2,'editorial','dark_oak')
 for x in[10,14]:u.chair(x,15,'south',material='dark_oak');u.chair(x,18,'north',material='dark_oak')
 m.p(12,10,16,'white_carpet','paper');m.p(14,10,17,'flower_pot','ink');seat(m,9,24,8,4)
 u.table(9,22,4,1,'tea','dark_oak',True);m.barrel(14,9,24);m.pot(14,10,24);u.shelf(21,17,1,3,'shelf');u.shelf(21,21,1,3,'shelf');m.addkit(u)
 for f in[2,8]:
  for z in[15,22]:beam(m,5,22,z,f+5)
 lamps(m,[(12,6,21),(18,6,17),(16,6,7),(7,6,16),(12,12,17),(12,12,24),(18,12,10),(9,12,8),(13,5,29)])
 for x in[11,12,13,14,15]:
  for z in range(28,32):m.p(x,2,z,'stone_bricks','threshold')
 for x in range(12,15):m.p(x,3,28,'air','entry.clear')
 for a in[('browse',13,21,2),('counter',15,10,2),('packing',16,7,2),('read',14,23,8),('work',16,17,8),('bed',20,10,8)]:m.use(*a)
 for a in[('shop','选书与结账',5,15,22,27,2,7),('service','柜台与包装',9,6,22,14,2,2),('studio','编辑、阅读',8,14,22,27,8,6),('bed','店主卧室',16,6,22,13,8,2)]:m.room(*a)
 return finish(m)

def pharmacy():
 m=init('Pharmacy',34,36,'白鷺薬局｜转角洋式药局');m.source=['Murakami1928','Dekiru-pharmacy']
 for f,top in[(2,8),(8,14)]:
  m.shell_rect(5,5,28,28,f,top,'white_terracotta','birch_planks')
  # brick plinth and a light cornice continuing around both street elevations.
  for x in range(5,28):m.p(x,f+1,27,'bricks','plinth')
  for z in range(5,28):m.p(27,f+1,z,'bricks','plinth')
  for a,b in[(7,13),(16,21)]:frame(m,'x',27,a,b,f+2,3,1,'quartz','light_blue')
  for a,b in[(8,13),(16,21)]:frame(m,'z',27,a,b,f+2,3,1,'quartz','light_blue')
  frame(m,'x',5,12,25,f+2,3,-1,'dark_oak');frame(m,'z',5,19,25,f+2,3,-1,'dark_oak')
 for x in[5,14,22,27]:
  for y in range(4,14):m.p(x,y,28,'smooth_quartz','pilaster')
  for y in[3,8,13]:m.p(x,y,29,'quartz_stairs','capital',facing='north',half='top')
 for z in[6,14,22]:
  for y in range(4,14):m.p(28,y,z,'smooth_quartz','pilaster')
 for y in[8,14]:
  for x in range(4,30):m.p(x,y,28,'quartz_slab','cornice',type='top')
  for z in range(4,29):m.p(28,y,z,'quartz_slab','cornice',type='top')
 # Corner entrance recess creates a small covered threshold with two street openings.
 m.box((23,3,23),(28,8,28),'air','corner.recess')
 m.box((22,3,23),(23,8,28),'white_terracotta','entry.inner');m.box((23,3,22),(28,8,23),'white_terracotta','entry.inner')
 m.door(25,3,22);m.door(22,3,25,'east');m.entry=[25,3,22]
 for x,z in[(27,27),(22,27),(27,22)]:m.box((x,3,z),(x+1,8,z+1),'smooth_quartz','portico.column')
 for x in range(23,28):
  for z in range(23,28):m.p(x,2,z,'polished_diorite','threshold')
 # Compact corner belvedere, hipped roof; main roof shallow hip with dormer-faced windows.
 m.hip(3,3,30,30,14,'deepslate_tile',2)
 for x in range(22,29):
  for z in range(22,29):
   m.p(x,15,z,'birch_planks','tower.floor');m.p(x,20,z,'birch_planks','tower.ceiling')
   if x in[22,28]or z in[22,28]:
    for y in range(16,20):m.p(x,y,z,'white_terracotta','corner.lantern')
 frame(m,'x',28,23,28,16,3,1,'quartz','cyan');frame(m,'z',28,23,28,16,3,1,'quartz','cyan')
 m.hip(21,21,30,30,20,'dark_prismarine',2)
 # Tower is a sealed decorative roof lantern, not an advertised third usable room.
 for z in[27,28]:m.p(25,23,z,'polished_deepslate_slab','ridge',type='bottom')
 sign(m,24,10,29,['白 鷺','薬 局']);m.p(29,10,24,'white_terracotta','sign.back');m.sign(30,10,24,'east',['白鷺薬局','薬・化粧品'])
 for x in range(7,21):m.p(x,6,29,'green_wool'if x%5 else'white_wool','canopy');m.p(x,6,30,'green_carpet'if x%5 else'white_carpet','canopy.edge');m.p(x,5,30,'green_wool'if x%5 else'white_wool','canopy.support')
 stairs(m,6,7);k=m.kit(2)
 # Apothecary drawers are real barrels, display bays have thin shelves and vessels.
 for x in range(11,26):
  m.barrel(x,3,6)
  if x%4!=0:m.barrel(x,4,6)
  m.p(x,6,6,'dark_oak_slab','display.shelf',type='top');m.p(x,7,6,'flower_pot','vessel')
 for z in range(9,20):
  m.barrel(26,3,z,'west');m.p(26,5,z,'dark_oak_slab','wall.shelf',type='top')
  if z%2:m.p(26,6,z,'flower_pot','apothecary.vessel')
 for x in range(13,24):m.barrel(x,3,12);m.p(x,4,12,'dark_oak_trapdoor','counter.edge',half='bottom')
 for x in[13,17,21]:m.p(x,4,12,'flower_pot','counter.vessel')
 k.table(17,9,4,1,'preparation','dark_oak');m.p(18,4,9,'white_carpet','work.cloth');k.sink(24,6)
 # Two glass-ended display tables and bench form a loop, no empty warehouse floor.
 for x in[10,18]:
  k.table(x,19,4,1,'display','dark_oak')
  for xx in range(x,x+4):m.p(xx,4,19,'flower_pot','vessel')
 seat(m,8,24,2,4,'green');m.barrel(13,3,24);m.pot(13,4,24);k.table(7,18,1,1,'consult','dark_oak');k.chair(7,20,'north',material='dark_oak');m.addkit(k)
 picture(m,16,5,6);picture(m,6,5,23)
 # upper office, stock room, a modest owner room; no repeated restaurant seating.
 m.box((18,9,6),(19,14,18),'white_terracotta','stock.wall');m.box((19,9,17),(27,14,18),'white_terracotta','stock.wall');m.door(22,9,17,wood='birch')
 u=m.kit(8);u.table(10,20,5,2,'office','dark_oak');u.chair(12,18,'south',material='dark_oak');u.chair(11,23,'north',material='dark_oak');m.p(11,10,20,'white_carpet','ledger');m.p(14,10,21,'flower_pot','ink')
 for x in[20,23,26]:
  for z in[7,10,13]:m.barrel(x,9,z);m.barrel(x,10,z)
 u.shelf(10,6,7,3,'records');u.bed(22,22);u.bed(23,22);u.cupboard(26,21,1,'linen');m.barrel(21,9,21);m.pot(21,10,21)
 m.box((19,9,19),(20,12,26),'dark_oak_planks','bed.screen');picture(m,20,11,20);m.p(20,11,19,'dark_oak_planks')
 m.barrel(16,9,24);m.pot(16,10,24);m.addkit(u)
 for f in[2,8]:
  for z in[15,22]:beam(m,6,27,z,f+5)
 lamps(m,[(15,6,17),(22,6,20),(18,6,9),(9,6,22),(8,6,15),(12,12,20),(13,12,8),(22,12,12),(24,12,23),(25,6,25)])
 for a in[('entry',25,23,2),('shop',16,21,2),('service',19,13,2),('prep',22,9,2),('office',16,21,8),('stock',22,15,8),('bed',24,22,8)]:m.use(*a)
 for a in[('retail','陈列、咨询与等候',7,15,26,27,2,8),('prep','调配、柜台、药柜',10,6,27,14,2,3),('office','账房与资料',9,6,18,27,8,3),('stock','分类储藏',19,6,27,17,8,1),('rest','店主休息',20,19,27,27,8,2)]:m.room(*a)
 return finish(m)

def inn():
 m=init('Inn',40,40,'松風館｜和洋小旅馆');m.source=['Notoya-official','Notoya-bunka']
 for f,top in[(2,8),(8,14)]:
  m.shell_rect(5,7,33,30,f,top,'white_terracotta','spruce_planks')
  for x in[5,13,22,32]:
   for z in[7,29]:m.box((x,f+1,z),(x+1,top,z+1),'stripped_spruce_log','post',axis='y')
  for z in[7,29]:beam(m,5,33,z,top-1)
  for a,b in[(7,13),(14,21),(23,31)]:frame(m,'x',29,a,b,f+2,3,1,'dark_oak','green')
  for a,b in[(11,17),(21,27)]:frame(m,'z',32,a,b,f+2,3,1)
  frame(m,'x',7,10,30,f+2,3,-1);frame(m,'z',5,21,27,f+2,3,-1)
 # Main broad hip with raised central gable and lean-to entrance; distinct from copper flat face.
 roof={}
 for x in range(3,35):
  for z in range(5,32):
   t=min(x-3,34-x,z-5,31-z);roof[x,z]=(14+t//2,'slab','top'if t%2 else'bottom')
 for x in range(13,25):
  for z in range(23,34):
   y=15+min(x-13,24-x)
   if (x,z)not in roof or y>=roof[x,z][0]:roof[x,z]=(y,'stairs','east'if x<19 else'west')
 for (x,z),(y,typ,prop)in roof.items():
  mat='dark_oak'if z==33 else'deepslate_tile'
  
  for yy in range(14,y):m.p(x,yy,z,'dark_oak_planks','roof.boarding')
  m.p(x,y,z,mat+'_'+typ,'roof.envelope',**({'type':prop}if typ=='slab'else{'facing':prop}))
  if z==29 and 13<=x<25:
   for yy in range(14,y):m.p(x,yy,z,'white_terracotta','gable.infill')
 for z in range(23,34):
  for x in[18,19]:m.p(x,21,z,'polished_deepslate_slab','gable.ridge',type='bottom')
 for yy in range(15,20):
  for x in[18,19]:m.p(x,yy,30,'stripped_spruce_log','gable.post',axis='y')
 for x in[16,17,20,21]:
  for y in[16,17]:m.p(x,y,29,'green_stained_glass_pane','gable.transom')
 for x in range(14,24):m.p(x,14,30,'dark_oak_slab','gable.band',type='top')
 # Small rooftop lantern breaks the long silhouette. Decorative, no third guest floor.
 m.box((15,19,12),(23,21,20),'white_terracotta','tower.base')
 for x in range(15,23):
  for z in range(12,20):
   if x in[15,22]or z in[12,19]:
    for y in range(21,25):m.p(x,y,z,'white_terracotta','tower.wall')
 m.box((15,25,12),(23,26,20),'dark_oak_planks','tower.ceiling')
 for x in[15,22]:
  for z in[12,19]:m.box((x,21,z),(x+1,25,z+1),'stripped_spruce_log','tower.post',axis='y')
 frame(m,'x',19,16,22,21,3,1,'dark_oak');frame(m,'x',12,16,22,21,3,-1,'dark_oak')
 frame(m,'z',22,13,19,21,3,1,'dark_oak');frame(m,'z',15,13,19,21,3,-1,'dark_oak')
 m.hip(13,10,25,22,25,'deepslate_tile',3)
 # Full-width balcony with open supports; private outdoor access from upstairs hall.
 for x in range(7,31):
  for z in[30,31]:m.p(x,8,z,'dark_oak_slab','balcony',type='top')
  m.p(x,9,32,'dark_oak_fence','balcony.rail');m.p(x,8,32,'dark_oak_slab','balcony.edge',type='top')
 for x in[7,13,24,30]:m.box((x,3,31),(x+1,8,32),'stripped_spruce_log','balcony.post',axis='y')
 for z in[30,31]:m.p(7,9,z,'dark_oak_fence','balcony.end');m.p(30,9,z,'dark_oak_fence','balcony.end')
 m.door(18,3,29);m.door(18,9,29);m.entry=[18,3,29]
 # Projected portico uses pale brackets and its own lower hipped roof.
 for x in[15,21]:m.box((x,3,34),(x+1,7,35),'stripped_spruce_log','porch.post',axis='y')
 m.hip(14,30,23,36,7,'dark_prismarine',2)
 for x in range(16,21):
  for z in range(30,38):m.p(x,2,z,'stone_bricks','entry.path')
 sign(m,18,6,35,['松 風 館','旅館・お泊り'])
 # Downstairs divides reception/lounge from bath and kitchen; services have real doors.
 stairs(m,6,10)
 m.box((9,3,16),(18,8,17),'white_terracotta','bath.wall');m.box((17,3,8),(18,8,16),'white_terracotta','bath.wall');m.door(13,3,16,wood='birch')
 m.box((23,3,8),(24,8,17),'white_terracotta','kitchen.wall');m.box((24,3,16),(32,8,17),'white_terracotta','kitchen.wall');m.door(27,3,16)
 k=m.kit(2)
 # Bath water is contained in cauldrons; no loose source blocks leaking through slabs.
 for x in[10,13]:m.p(x,3,9,'water_cauldron','wash',level=3);m.p(x,3,10,'dark_oak_trapdoor','wash.mat',half='bottom')
 for x in range(10,16):m.barrel(x,3,14);m.p(x,4,14,'white_carpet','towels')
 for x in[10,12,14]:m.p(x,3,12,'spruce_slab','wash.stool',type='bottom')
 for x in range(25,32):m.barrel(x,3,8);m.p(x,5,8,'dark_oak_slab','kitchen.shelf',type='top')
 k.furnace(25,8);k.sink(28,8);k.table(25,12,5,1,'prep','dark_oak');m.p(26,4,12,'white_carpet','cloth');m.p(29,4,12,'flower_pot','vessel')
 for x in[26,29,31]:m.p(x,6,8,'flower_pot','kitchen.vessel')
 # Reception wraps its work area, waiting has upholstery and a distinct tea corner.
 for z in range(20,26):m.barrel(25,3,z,'west');m.p(25,4,z,'dark_oak_trapdoor','desk.edge',half='bottom')
 for x in range(26,31):m.barrel(x,3,20)
 k.shelf(30,23,1,3,'key.cabinet');k.table(28,25,3,1,'reception.work','dark_oak');m.p(29,4,25,'white_carpet','guest.ledger');k.chair(29,24,'south',material='dark_oak')
 seat(m,9,25,2,4);k.table(9,22,4,1,'tea','dark_oak',True);m.barrel(14,3,25);m.pot(14,4,25)
 k.table(18,19,3,2,'breakfast','dark_oak');k.chair(18,18,'south',material='dark_oak');k.chair(20,18,'south',material='dark_oak');k.chair(18,22,'north',material='dark_oak');k.chair(20,22,'north',material='dark_oak');m.p(19,4,19,'flower_pot','tea.vessel')
 m.barrel(21,3,26);m.pot(21,4,26);picture(m,20,5,8);picture(m,28,5,21);m.addkit(k)
 # Lobby edge: a shoe cabinet, display recess and two grouped plants.
 for x in[15,16]:m.barrel(x,3,27);m.p(x,4,27,'dark_oak_trapdoor','shoe.top',half='bottom')
 m.pot(15,5,27);m.p(15,4,27,'dark_oak_slab','shoe.top',type='top')
 # Two individually furnished suites, corridor leads to balcony. Real beds, alcoves and cabinets.
 m.box((9,9,21),(32,14,22),'white_terracotta','room.wall');m.box((20,9,8),(21,14,21),'white_terracotta','room.divider');m.door(14,9,21,wood='birch');m.door(26,9,21,wood='birch')
 u=m.kit(8)
 for x in[12,13,25,26]:u.bed(x,11);m.p(x,9,9,'dark_oak_trapdoor','bed.headboard',facing='north',open=True)
 for x,z in[(11,10),(24,10)]:m.barrel(x,9,z);m.pot(x,10,z)
 u.cupboard(17,8,3,'west.linen');u.cupboard(29,8,3,'east.linen')
 for x in[11,24]:
  m.tatami(x,15,x+7,20,8);u.table(x+2,17,3,1,'low.tea','dark_oak',True)
  for xx in[x+2,x+4]:m.p(xx,9,16,'brown_carpet','cushion');m.p(xx,9,19,'brown_carpet','cushion')
  m.p(x+6,9,18,'oak_slab','alcove',type='top');m.pot(x+6,10,18)
  picture(m,x+6,11,18)
 seat(m,10,26,8,4);u.table(10,24,4,1,'hall.tea','dark_oak',True);m.barrel(24,9,26);m.pot(24,10,26)
 # Window desk and shelf in east guest room, western room has writing/reading alcove.
 u.table(30,14,1,3,'window.desk','dark_oak');u.chair(28,15,'east',material='dark_oak');u.table(17,14,2,1,'writing','dark_oak');u.chair(18,13,'south',material='dark_oak');m.addkit(u)
 for f in[2,8]:
  for z in[18,25]:beam(m,6,32,z,f+5)
 lamps(m,[(12,6,23),(19,6,19),(23,6,26),(29,6,23),(27,6,12),(12,6,13),(8,6,19),(12,12,17),(25,12,17),(14,12,11),(27,12,11),(18,12,25),(8,12,11),(18,5,33)])
 m.p(18,3,30,'air','entry.clear');m.p(18,9,30,'air','balcony.clear')
 for a in[('lobby',18,27,2),('reception',24,23,2),('tea',14,23,2),('bath',13,15,2),('kitchen',27,14,2),('dining',22,20,2),('hall',18,25,8),('west.room',14,20,8),('east.room',26,20,8),('bed.west',14,11,8),('bed.east',27,11,8),('balcony',18,31,8)]:m.use(*a)
 m.p(18,3,30,'air','entry.clear');m.p(18,9,30,'air','balcony.clear')
 for a in[('lobby','玄关、接待、茶歇',9,18,32,29,2,10),('bath','共用盥洗与毛巾',9,8,17,16,2,2),('kitchen','早餐后厨',24,8,32,16,2,2),('guest.west','和式客房',9,8,20,21,8,2),('guest.east','和洋客房',21,8,32,21,8,2),('hall','休息廊与阳台',9,22,32,32,8,4)]:m.room(*a)
 return finish(m)

