"""Twelve new authored programs and facade refinements. HAF0.4 / Taisho14."""
import math
from prototype_base import Study
from baseline_types import frame,stairs,seat,lamps,beam,sign,picture
from street_types import enrich,smallshop,bookstore,pharmacy,inn
from detail_lab import states as S

def gable(m,x,z,X,Z,y,axis='z',skin='deepslate_tile',wall='white_terracotta'):
 for xx in range(x,X):
  for zz in range(z,Z):
   t=min(xx-x,X-1-xx)if axis=='z'else min(zz-z,Z-1-zz);yy=y+t//2
   m.p(xx,yy,zz,skin+'_slab','roof.skin',type='top'if t%2 else'bottom')
   # Continuous backing is confined to the attic and its eave edges.
   for yb in range(y,yy):m.p(xx,yb,zz,wall if xx in[x+1,X-2]or zz in[z+1,Z-2]else'dark_oak_planks','roof.backing')
 if axis=='z':
  for zz in range(z,Z):m.p((x+X-1)//2,y+(X-x-1)//4+1,zz,'polished_deepslate_slab','roof.ridge',type='bottom')
 else:
  for xx in range(x,X):m.p(xx,y+(Z-z-1)//4+1,(z+Z-1)//2,'polished_deepslate_slab','roof.ridge',type='bottom')

def facade(m,style,wall):
 w,d=m.w,m.d;front=d-5;trim='quartz'if style in['brick','civic','clinic']else'dark_oak';post='smooth_quartz'if trim=='quartz'else'stripped_dark_oak_log'
 for f in m.floors:
  m.shell_rect(3,3,w-3,front+1,f,f+6,wall,'birch_planks'if trim=='quartz'else'spruce_planks')
  for x in [3,w-4]:
   for z in[3,front]:m.box((x,f+1,z),(x+1,f+6,z+1),post,'corner.pier',**({'axis':'y'}if post.startswith('stripped')else{}))
  # Offset two window bays, with transoms and projected hoods.
  for a,b in[(5,w//2-2),(w//2+3,w-5)]:
   if b>a:frame(m,'x',front,a,b,f+2,3,1,trim,'cyan'if style=='clinic'else'green')
  for side,out in[(3,-1),(w-4,1)]:
   for a,b in [(6,10),(d-13,d-8)]:
    if b>a:frame(m,'z',side,a,b,f+2,3,out,trim)
  frame(m,'x',3,9,w-6,f+2,3,-1,trim)
  for z in[3,front]:
   for x in range(3,w-3):
    m.p(x,f+1,z,'bricks'if style in['brick','civic','clinic']else'dark_oak_planks','wall.plinth')
    m.p(x,f+5,z+(-1 if z==3 else 1),trim+'_slab','cornice',type='top')
  for z in range(3,front+1):
   for x in[2,w-3]:m.p(x,f+5,z,trim+'_slab','side.cornice',type='top')
  # Separate capitals, lintels and knee braces give actual depth, not paint variation.
  for x in[3,w//2,w-4]:
   m.p(x,f+4,front+1,trim+'_stairs','capital',half='top',facing='north')
   if f==8:
    for y in[f+2,f+3]:m.p(x,y,front+1,'dark_oak_trapdoor','shutter',facing='south',open=True)
 top=max(m.floors)+6
 gable(m,1,1,w-1,front+3,top,'z'if style in['brick','civic']else'x',wall=wall)
 # Shop canopy: layered lower rim, braces and a contrasting sign band.
 for x in range(3,w-3):
  m.p(x,6,front+1,'dark_oak_slab','canopy.inner',type='top');m.p(x,5,front+2,'dark_oak_slab','canopy.edge',type='top')
  if style in['bakery','florist']:
   m.p(x,6,front+2,('green'if x%4 else'white')+'_carpet','cloth.awning')
 for x in[4,w-5]:m.p(x,5,front+1,'dark_oak_stairs','canopy.bracket',half='top',facing='north')
 m.door(w//2,3,front);m.entry=[w//2,3,front]
 sign(m,w//2,7,front+1,[m.program.split('｜')[0],{'brick':'商店','civic':'公共施設','clinic':'診療所'}.get(style,'営業中')])
 for x in [4,w-5]:m.barrel(x,3,front-1);m.pot(x,4,front-1)
 # A small projecting upper bay on selected facades. Protected door remains below.
 if len(m.floors)>1 and style in['timber','clinic','brick']:
  a,b=w//2-2,w//2+3
  for x in range(a,b):
   for z in range(front+1,front+3):m.p(x,8,z,trim+'_slab','bay.floor',type='top')
   for y in[10,11]:m.p(x,y,front+2,'white_stained_glass_pane','bay.glazing')
   m.p(x,9,front+2,wall,'bay.spandrel');m.p(x,12,front+2,trim+'_slab','bay.head',type='top')
  for x in[a,b-1]:
   for y in[9,10,11]:m.p(x,y,front+2,post,'bay.post',**({'axis':'y'}if post.startswith('stripped')else{}))
  for x in range(a-1,b+1):m.p(x,13,front+2,'deepslate_tile_slab','bay.roof',type='bottom')
 if style=='civic':
  for x in range(w//2-3,w//2+4):
   h=3-abs(x-w//2);m.box((x,top,front),(x+1,top+h+1,front+1),wall,'central.gable');m.p(x,top+h+1,front+1,'quartz_slab','central.gable.edge',type='top')
 if style=='brick':
  for x in[3,w-4]:
   for y in range(3,top+3):m.p(x,y,front+1,'bricks','front.pilaster')
  for x in range(3,w-3):m.p(x,top+2,front+1,'quartz_slab','parapet.cap',type='top')
 return m

def make(id,w,d,levels,name,style='timber',wall='white_terracotta'):
 m=Study(id,w,d,levels,name);m.floors=[2+6*i for i in range(levels)];m.ground();m.seed=141145;m.source=['Taisho14 original program; prior video street observations']
 facade(m,style,wall)
 if levels>1:stairs(m,4,5)
 else:m.upper_start=[4,4]
 for f in m.floors:
  for x,z in[(w//2, d-9),(w-7,7),(7,d//2)]:m.lamp(x,f+4,z)
 m.use('entry',w//2,d-6)
 m.room('main',name,7,4,w-4,d-5,2,6)
 if levels>1:m.room('upper','二层功能空间',7,4,w-4,d-5,8,4)
 return m

def table(m,k,x,z,w=3,kind='work'):
 k.table(x,z,w,1,kind,'dark_oak');m.p(x+1,k.origin[1]+2 if hasattr(k,'origin')else 4,z,'white_carpet','paper')

def upper_home(m,kind='home'):
 w,d=m.w,m.d;u=m.kit(8)
 # Actual private sleeping room with a door; clear path from stair landing.
 m.box((w-11,9,4),(w-10,14,12),'white_terracotta','bedroom.wall');m.box((w-10,9,11),(w-4,14,12),'white_terracotta','bedroom.wall');m.door(w-8,9,11,wood='birch')
 u.bed(w-9,7);u.cupboard(w-6,4,1,'wardrobe');m.barrel(w-10,9,6);m.pot(w-10,10,6)
 u.shelf(8,4,2,3,'archive');u.table(8,d-11,4,2,'work','dark_oak');u.chair(9,d-13,'south',material='dark_oak');m.p(9,10,d-11,'white_carpet','work.paper')
 seat(m,8,d-8,8,3,'green');m.barrel(12,9,d-7);m.pot(12,10,d-7);picture(m,w-7,11,12)
 m.addkit(u);m.use('upper.work',13,d-11,8);m.use('upper.bed',w-8,8,8)

def library():
 m=make('Library',26,30,2,'櫻坂文庫｜公共阅览室','civic');w,d=m.w,m.d
 for q,st in list(m.blocks.items()):
  if 'deepslate_tile_slab'in st:m.p(*q,st.replace('deepslate_tile_slab','dark_prismarine_slab'),'copper.roof')
 for f in[2,8]:
  k=m.kit(f)
  for x in[8,15]:
   k.shelf(x,4,5,3,'wall.books');k.shelf(x,12,3,2,'catalogue');k.shelf(x,13,3,2,'catalogue')
  for x in[8,16]:
   k.table(x,20,4,2,'reading','dark_oak')
   for xx in[x,x+3]:k.chair(xx,19,'south',material='dark_oak');k.chair(xx,22,'north',material='dark_oak')
   m.p(x+1,f+2,20,'white_carpet','reading.paper')
  m.barrel(20,f+1,7);m.pot(20,f+2,7);m.addkit(k);m.use('reading.'+str(f),14,21,f);m.use('browse.'+str(f),14,11,f)
 picture(m,20,6,4);return m

def school():
 m=make('School',34,34,2,'櫻坂尋常学校｜学校','civic','white_terracotta');w,d=m.w,m.d
 for f in[2,8]:
  k=m.kit(f)
  # Blackboard and teacher desk face grouped desks; a broad aisle leads from the door.
  m.box((10,f+2,3),(25,f+5,4),'green_wool','blackboard');k.table(16,7,5,1,'teacher.desk','dark_oak')
  for x in[10,17,24]:
   for z in[12,18,24]:
    k.table(x,z,3,1,'pupil.desk','oak');k.chair(x+1,z+2,'north',material='oak');m.p(x+1,f+2,z,'white_carpet','exercise.book')
  k.shelf(28,5,1,3,'class.books');k.shelf(28,8,1,3,'class.books');m.barrel(8,f+1,27);m.pot(8,f+2,27);m.addkit(k)
  m.use('classroom.'+str(f),15,20,f);m.use('teacher.'+str(f),21,9,f)
 # Attached entrance portico, including roof bracket and stone base.
 for x in[12,22]:m.box((x,3,31),(x+1,7,32),'smooth_quartz','portico.pillar')
 for x in range(11,24):
  for z in range(30,33):m.p(x,7,z,'quartz_slab','portico.roof',type='top')
 # The civic pediment rises in front of the main roof, not hidden inside the attic.
 for x in range(11,24):
  peak=23-abs(x-17)
  for y in range(14,peak+1):m.p(x,y,31,'white_terracotta','civic.frontispiece')
  m.p(x,peak+1,32,'quartz_slab','pediment.coping',type='top')
 for x in[12,22]:
  for y in range(9,19):m.p(x,y,31,'smooth_quartz','frontispiece.pier')
 for x in range(15,20):
  for y in range(16,20):m.p(x,y,31,'cyan_stained_glass_pane','attic.window')
 for x in[14,20]:
  for y in range(15,21):m.p(x,y,32,'quartz_slab','attic.window.frame',type='double')
 for x in range(14,21):m.p(x,15,32,'quartz_slab','attic.sill',type='top');m.p(x,20,32,'quartz_slab','attic.head',type='top')
 return m

def clinic():
 m=make('Clinic',22,28,2,'白川診療所｜诊所','clinic');k=m.kit(2)
 for x in range(9,17):m.barrel(x,3,9);m.p(x,4,9,'dark_oak_trapdoor','reception.trim')
 seat(m,8,19,2,3,'green');k.table(8,17,3,1,'waiting','dark_oak');k.sink(17,4);k.cupboard(12,4,3,'medicine');m.addkit(k)
 m.box((8,9,4),(9,14,20),'white_terracotta','ward.partition');u=m.kit(8)
 for x in[11,16]:u.bed(x,8);m.barrel(x,9,5);m.pot(x,10,5)
 for x in[11,16]:u.bed(x,17)
 u.sink(17,21);m.addkit(u);m.use('reception',12,12);m.use('waiting',13,19);m.use('ward',14,13,8)
 return m

def textile():
 m=make('Textile',20,26,2,'紺屋呉服店｜布料店','timber','light_gray_terracotta');k=m.kit(2)
 for x in[8,11,14]:
  m.barrel(x,3,4)
  for y,col in[(4,'white'),(5,'green')]:m.p(x,y,4,col+'_wool','fabric.bolt')
 k.table(8,11,5,2,'cutting','dark_oak');m.p(9,4,11,'green_carpet','fabric');seat(m,8,17,2,3,'brown');m.addkit(k);m.use('cutting',13,14)
 upper_home(m);return m

def residence():
 m=make('Residence',22,28,2,'山手下宿｜住宅','timber','white_terracotta');k=m.kit(2)
 for x in range(8,18):m.barrel(x,3,4)
 k.furnace(8,4);k.sink(11,4);k.table(12,11,4,2,'dining','dark_oak');k.chair(13,9,'south',material='dark_oak');seat(m,8,20,2,4,'green');k.table(8,18,4,1,'living','dark_oak');m.addkit(k);m.use('dining',17,12);m.use('living',13,19);upper_home(m);return m

def bakery():
 m=make('Bakery',18,24,1,'麦穂パン店｜面包房','bakery','white_terracotta');k=m.kit(2)
 for x in range(4,14):m.barrel(x,3,4)
 k.furnace(4,4);k.furnace(5,4);k.sink(8,4)
 for x in range(5,12):m.barrel(x,3,10);m.p(x,4,10,'dark_oak_trapdoor','counter.trim')
 for x in[5,8,11]:m.p(x,4,10,'cake','bread.display')
 k.table(4,15,3,1,'cafe','dark_oak');k.chair(5,13,'south',material='dark_oak');seat(m,4,17,2,3,'brown');m.addkit(k);m.use('order',10,13);m.use('bakery',12,7)
 m.box((13,8,4),(15,17,6),'bricks','oven.chimney');return m

def florist():
 m=make('Florist',16,22,1,'花便り｜花店','florist','white_terracotta');k=m.kit(2)
 for x in[4,7,10]:
  for z in[4,8]:m.barrel(x,3,z);m.pot(x,4,z)
 for x in[4,7,10]:m.p(x,6,4,'dark_oak_slab','hanging.shelf',type='top');m.pot(x,7,4)
 k.table(10,13,2,1,'wrapping','dark_oak');m.p(10,4,13,'white_carpet','wrapping.paper');m.addkit(k);m.use('flowers',8,11);m.use('wrap',11,15)
 for x in[3,4,11,12]:m.p(x,3,20,'terracotta','plant.display');m.pot(x,4,20)
 return m

def sake():
 m=make('Sake',20,25,1,'松葉酒舗｜酒铺与库房','timber');k=m.kit(2)
 for x in[5,6,7,13,14,15]:
  for z in[4,5,6]:m.barrel(x,3,z);m.barrel(x,4,z)
 for x in range(5,15):m.barrel(x,3,12)
 for x in[6,9,12]:m.p(x,4,12,'flower_pot','vessel')
 seat(m,5,17,2,3,'brown');k.table(12,17,3,1,'tasting','dark_oak');m.addkit(k);m.use('counter',10,15);m.use('stock',10,7)
 for x in[3,4,15,16]:m.barrel(x,3,23)
 return m

def workshop():
 m=make('Workshop',24,27,1,'青木工房｜修理与木作','brick','light_gray_terracotta');k=m.kit(2)
 for x in[5,9,13,17]:m.barrel(x,3,4);m.barrel(x,4,4)
 k.table(6,10,5,2,'bench','dark_oak');k.table(15,13,4,2,'assembly','dark_oak');k.furnace(18,4);m.p(10,4,10,'crafting_table','tool.box');k.shelf(4,14,1,3,'parts');m.addkit(k);m.use('workbench',12,11);m.use('assembly',17,16)
 m.box((4,3,23),(7,4,25),'spruce_log','timber.stock',axis='z')
 # Roof monitor: raised clerestory light box distinguishes a production building.
 m.box((9,12,8),(15,15,18),'bricks','monitor.base')
 for x in[9,14]:
  for z in range(9,17):m.p(x,15,z,'white_stained_glass_pane','monitor.glass')
 for x in range(8,16):
  for z in range(7,19):m.p(x,16,z,'deepslate_tile_slab','monitor.roof',type='top')
 return m

def bath():
 m=make('Bath',28,31,1,'松の湯｜公共浴场','timber');k=m.kit(2)
 # A screened bath suite, not an open pool in an empty room.
 m.box((4,3,14),(24,8,15),'white_terracotta','bath.partition');m.door(20,3,14,wood='birch')
 for x in[5,6,7,8,10,11,12]:m.barrel(x,3,22);m.barrel(x,4,22)
 seat(m,5,18,2,5,'brown');m.barrel(23,3,22);m.pot(23,4,22)
 for x in range(6,18):
  for z in range(5,11):m.p(x,2,z,'smooth_quartz','pool.base');m.p(x,3,z,'smooth_quartz'if x in[6,17]or z in[5,10]else'water','pool',**({}if x in[6,17]or z in[5,10]else{'level':0}))
 for z in[5,9]:k.sink(22,z);m.p(22,5,z,'stone_button','tap',face='wall',facing='west')
 m.addkit(k);m.use('changing',16,20);m.use('bath',20,10);m.box((23,8,4),(25,27,6),'bricks','bath.chimney')
 # Smaller entrance gable changes the large roof silhouette.
 gable(m,10,24,19,29,8,'z',wall='white_terracotta');return m

def clock():
 m=Study('Clock',16,18,1,'櫻坂時計塔｜钟楼与导览室');m.seed=141145;m.floors=[2];m.ground();m.upper_start=[4,4]
 m.shell_rect(3,3,13,14,2,9,'bricks','polished_diorite');m.door(8,3,13);m.entry=[8,3,13]
 frame(m,'x',13,4,7,5,3,1,'quartz');frame(m,'x',13,10,12,5,3,1,'quartz')
 for x,z in[(3,3),(12,3),(3,13),(12,13)]:m.box((x,3,z),(x+1,10,z+1),'smooth_quartz','corner.pier')
 for y in[9,18,27]:
  for x in range(2,14):
   for z in range(2,15):
    if x in[2,13]or z in[2,14]:m.p(x,y,z,'quartz_slab','tower.cornice',type='top')
 m.box((5,10,5),(11,28,12),'white_terracotta','tower.shaft')
 for x,z in[(5,5),(10,5),(5,11),(10,11)]:m.box((x,10,z),(x+1,28,z+1),'smooth_quartz','tower.pier')
 m.box((3,19,4),(13,28,14),'white_terracotta','clock.head')
 for axis,c in[('x',3),('x',14),('z',2),('z',13)]:
  for u in range(4,12):
   for y in range(19,27):
    x,z=(u,c)if axis=='x'else(c,u+1)
    m.p(x,y,z,'white_concrete'if 4<u<11 and 19<y<26 else'black_concrete','clock.face')
  for u,y in[(7,23),(7,24),(7,25),(8,23),(9,23)]:
   x,z=(u,c)if axis=='x'else(c,u+1);m.p(x,y,z,'black_concrete','clock.hand')
 for y,a in[(28,3),(29,4),(30,5),(31,6)]:
  for x in range(a,16-a):
   for z in range(a,17-a):m.p(x,y,z,'dark_prismarine_slab','tower.roof',type='top')
 m.p(8,32,8,'dark_oak_fence','finial');m.p(8,33,8,'lantern','finial.light',hanging=False)
 k=m.kit(2);k.table(5,5,5,1,'information','dark_oak');m.p(6,4,5,'white_carpet','map');seat(m,5,9,2,3,'green');m.addkit(k);m.lamp(8,7,9);m.use('info',10,7);m.room('info','导览与休息',4,4,12,13,2,3)
 return m

def station():
 m=Study('Station',36,38,1,'櫻坂駅｜地方车站');m.seed=141145;m.floors=[2];m.ground();m.upper_start=[4,14]
 m.shell_rect(3,12,33,33,2,9,'white_terracotta','polished_diorite');m.door(18,3,32);m.door(18,3,12,'north');m.entry=[18,3,32]
 for c,out in[(32,1),(12,-1)]:
  for a,b in[(5,14),(22,31)]:frame(m,'x',c,a,b,4,4,out,'dark_oak')
 for x in[3,32]:
  for z in[12,22,32]:m.box((x,3,z),(x+1,9,z+1),'stripped_dark_oak_log','station.post',axis='y')
 gable(m,1,10,35,35,9,'x');gable(m,13,28,24,37,10,'z')
 for x in range(1,35):
  for z in range(5,12):m.p(x,2,z,'stone_bricks','platform')
  for z in[2,3,4]:m.p(x,2,z,'gravel','ballast')
  m.p(x,3,3,'rail','track',shape='east_west')
 for x in[3,10,25,32]:
  m.box((x,3,9),(x+1,7,10),'stripped_spruce_log','platform.column',axis='y')
 for x in range(1,35):
  for z in range(7,12):m.p(x,7,z,'dark_oak_slab','platform.canopy',type='top')
 for x in[5,24]:seat(m,x,8,2,5,'brown')
 k=m.kit(2)
 for x in range(5,13):m.barrel(x,3,18);m.p(x,4,18,'dark_oak_trapdoor','ticket.counter')
 for x in[5,24]:seat(m,x,27,2,5,'brown');seat(m,x,23,2,5,'brown')
 k.table(24,15,5,2,'station.office','dark_oak');k.shelf(30,13,1,3,'timetable');m.addkit(k)
 for x,z in[(9,23),(27,23),(18,16),(18,29)]:m.lamp(x,7,z)
 for x in[10,25]:m.lamp(x,5,10)
 sign(m,18,8,34,['櫻 坂 駅','SAKURAZAKA']);m.use('ticket',13,20);m.use('waiting',18,26);m.use('platform',18,8);m.room('concourse','售票、候车与站务',4,13,32,32,2,16)
 return m

def all_types(seed):
 mods=[enrich(bookstore()),enrich(pharmacy()),enrich(inn()),smallshop('Tea',18,22,'tea'),smallshop('Photo',21,24,'photo'),smallshop('Post',20,24,'post'),library(),school(),clinic(),textile(),residence(),bakery(),florist(),sake(),workshop(),bath(),clock(),station()]
 for m in mods:
  m.seed=seed
  # Reinforce selected side facades; gutters read as separate narrow edge components.
  if m.id in ['Bookshop','Pharmacy','Inn','Photo','Post']:
   front=m.entry[2]
   for y in range(4,13):m.p(m.w-3,y,front-2,'iron_bars','rain.pipe')
  # Explicitly separate model height from the old common 28-block canvas.
  m.h=max(28,max(q[1]for q in m.blocks)+2)
 return mods
