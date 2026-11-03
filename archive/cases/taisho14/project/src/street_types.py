from prototype_base import Study
from baseline_types import bookstore,pharmacy,inn,frame,stairs,seat,lamps,beam,sign,picture
SEED=141145
def enrich(m):
 # Whole bays receive joinery; doors, stairs, use points and furniture remain fixed.
 if m.id=='Bookshop':
  for x in [5,9,11,15,17,21]:
   for y in [10,11,12]:m.p(x,y,28,'dark_oak_trapdoor','shutter',facing='south',open=True)
  for x in [7,13,19]:m.p(x,13,28,'quartz_slab','window.crown',type='top')
  for x in [6,8,18,20]:
   m.p(x,3,29,'dark_oak_slab','books.display',type='top');m.p(x,4,29,'white_carpet','paper.stack')
  m.barrel(5,3,25);m.pot(5,4,25)
  for x in [4,22]:m.box((x,4,29),(x+1,6,30),'dark_oak_fence','canopy.bracket')
 if m.id=='Pharmacy':
  # Slim cloth canopy with a continuous supporting upper slab.
  for x in range(7,21):
   for z in [29,30]:
    for y in [5,6,7]:m.p(x,y,z,'air')
    m.p(x,6,z,'dark_oak_slab','awning.frame',type='top');m.p(x,7,z,'green_carpet'if x%4 else'white_carpet','awning.cloth')
  for x in [7,20]:m.p(x,5,29,'quartz_stairs','awning.bracket',half='top',facing='north')
  for x in [8,11,17,20]:
   m.p(x,10,28,'iron_bars','window.guard');m.p(x,11,28,'iron_bars','window.guard')
  for z in [8,11,17,20]:m.p(28,10,z,'iron_bars','window.guard')
 if m.id=='Inn':
  for x in [8,11,15,20,25,28]:
   for y in [10,11]:m.p(x,y,30,'dark_oak_trapdoor','sliding.screen',facing='south',open=True)
  for x in [8,12,25,29]:m.p(x,7,30,'dark_oak_stairs','balcony.bracket',half='top',facing='north')
  for x in [8,29]:m.barrel(x,3,33);m.barrel(x+1,3,33);m.pot(x,4,33)
  # A real alcove wall, picture and low cabinet give the guest room a focal edge.
  for x in range(11,17):m.p(x,9,8,'dark_oak_slab','guest.low.cabinet',type='top')
  for x in [11,16]:m.pot(x,10,8)
  picture(m,14,11,8)
  for x in range(24,29):m.p(x,9,8,'dark_oak_slab','guest.low.cabinet',type='top')
 return m

def smallshop(id,w,d,kind):
 m=Study(id,w,d,1 if kind=='tea'else 2,{'tea':'山茶屋｜小茶食店','photo':'光映写真館｜照相馆','post':'坂道郵便局｜小邮便局'}[kind]);m.seed=SEED;m.ground();m.source=['BV1Dx41187iG'];m.floors=[2] if kind=='tea'else[2,8]
 wall={'tea':'white_terracotta','photo':'light_gray_terracotta','post':'white_terracotta'}[kind]
 for f in m.floors:
  m.shell_rect(2,2,w-2,d-2,f,f+6,wall,'spruce_planks'if kind!='post'else'birch_planks')
  for x in [2,w-3]:
   for z in [2,d-3]:m.box((x,f+1,z),(x+1,f+6,z+1),'stripped_dark_oak_log','post',axis='y')
  beam(m,2,w-2,d-3,f+5);frame(m,'z',w-3,7,d-6,f+2,3,1,'dark_oak');frame(m,'z',2,7,d-6,f+2,3,-1,'dark_oak')
  for z in [2,d//2,d-3]:
   for y in range(f+1,f+6):m.p(2,y,z,'stripped_spruce_log','side.post',axis='y')
  for z in range(2,d-2):m.p(1,f+5,z,'dark_oak_slab','side.band',type='top')
  for a,b in [(3,7),(w-7,w-3)]:frame(m,'x',d-3,a,b,f+2,3,1,'dark_oak')
  frame(m,'x',2,8,w-4,f+2,3,-1,'dark_oak')
 top=8 if kind=='tea'else 14
 # Continuous timber backing, with a crosswise gable skin and side bargeboards.
 for x in range(0,w):
  for z in range(0,d-1):
   t=min(z,d-2-z);yy=top+t//2
   for y in range(top,yy):m.p(x,y,z,'dark_oak_planks','roof.board')
   m.p(x,yy,z,'deepslate_tile_slab','roof.skin',type='top'if t%2 else'bottom')
 for x in range(w):m.p(x,top+(d-2)//4+1,(d-2)//2,'polished_deepslate_slab','roof.ridge',type='bottom')
 # Storefront transom, offset display, a central door and a thin projecting canopy.
 m.door(w//2,3,d-3,wood='oak');m.entry=[w//2,3,d-3]
 for x in range(2,w-2):
  m.p(x,6,d-2,'dark_oak_slab','canopy.back',type='top');m.p(x,5,d-1,'dark_oak_slab','canopy.edge',type='top')
 for x in [3,w-4]:m.p(x,5,d-2,'dark_oak_stairs','bracket',facing='north',half='top')
 sign(m,w//2,7,d-2,[{'tea':'山 茶 屋','photo':'光 映 写 真 館','post':'坂 道 郵 便 局'}[kind],{'tea':'茶・甘味','photo':'記念写真・肖像','post':'郵便・電信'}[kind]])
 m.p(w//2,3,d-2,'air');m.p(w//2,4,d-2,'air')
 k=m.kit(2)
 if kind=='tea':
  # Working rear kitchen, front counter and two actual dining groups.
  for x in range(3,w-3):m.barrel(x,3,3)
  k.furnace(3,3);k.sink(5,3)
  for x in range(3,w-3):m.p(x,5,3,'dark_oak_slab','kitchen.shelf',type='top')
  for x in [4,7,11]:m.p(x,6,3,'flower_pot','tea.jar')
  for x in range(3,10):m.barrel(x,3,7);m.p(x,4,7,'dark_oak_trapdoor','counter.trim')
  m.p(4,4,7,'cake','food');m.p(7,4,7,'flower_pot','cup')
  for z in [12,17]:
   seat(m,4,z+1,2,3,'green');k.table(4,z-1,3,1,'tea.table','dark_oak');m.p(5,4,z-1,'flower_pot','tea.cup')
   k.chair(5,z-3,'south',material='dark_oak')
  seat(m,12,15,2,2,'brown');k.table(12,13,2,1,'window.table','dark_oak');m.p(12,4,13,'flower_pot','tea.cup')
  m.barrel(14,3,18);m.pot(14,4,18);picture(m,12,6,3)
  m.use('order',9,9);m.use('table',9,15);m.use('kitchen',10,5)
  m.room('tea','茶食、柜台与后厨',3,3,w-3,d-3,2,8);m.upper_start=[3,3]
  for x in [4,5,13,14]:m.p(x,3,d-1,'dark_oak_slab','outside.bench',type='bottom')
  m.banner(7,5,d-2,'green');m.p(7,5,d-3,'dark_oak_planks','curtain.back')
  lamps(m,[(9,6,12),(12,6,6),(5,6,17),(w//2,5,d-2)])
 else:
  stairs(m,3,4)
  # Front room stays separate from working service/storage band.
  m.box((6,3,10),(w-3,8,11),wall,'back.room.wall');m.door(w-6,3,10,wood='birch')
  for x in range(8,w-4):m.barrel(x,3,3)
  if kind=='photo':
   for x in range(8,15):
    for y in range(4,7):m.p(x,y,3,'white_wool','portrait.backdrop')
   seat(m,9,5,2,3,'red');m.p(11,3,8,'dark_oak_fence','camera.tripod');m.p(11,4,8,'black_concrete','camera.body');m.p(11,4,9,'stone_button','camera.lens',face='wall',facing='south')
   seat(m,8,17,2,4,'brown');k.table(8,15,4,1,'waiting.table','dark_oak');m.p(10,4,15,'white_carpet','album')
   for x in [7,11,15]:picture(m,x,5,11)
   for z in [13,14,15]:m.barrel(w-4,3,z,'west')
   sign(m,5,11,d-2,['PHOTOGRAPH','写真・肖像'])
   m.use('portrait',15,7);m.use('waiting',13,17);m.use('desk',w-5,14)
  else:
   for x in range(8,w-4):m.barrel(x,4,3)
   for x in range(8,w-4):m.barrel(x,3,14);m.p(x,4,14,'dark_oak_trapdoor','counter.trim')
   m.p(10,4,14,'white_carpet','letters');m.p(13,4,14,'flower_pot','ink');seat(m,7,18,2,3,'green')
   for x in [8,12,16]:picture(m,x,5,11)
   m.use('counter',12,16);m.use('sorting',12,7)
   # Public post box outside; clear of the main entrance.
   m.barrel(3,3,d-1);m.p(3,4,d-1,'red_terracotta','postbox');m.p(3,5,d-1,'dark_oak_slab','postbox.lid',type='bottom')
  # Upstairs includes an inhabited room instead of another empty hall.
  m.box((11,9,3),(12,14,12),wall,'private.wall');m.box((12,9,11),(w-3,14,12),wall,'private.wall');m.door(w-6,9,11,wood='birch')
  u=m.kit(8);u.bed(14,6);u.cupboard(w-5,3,1,'wardrobe');m.barrel(13,9,4);m.pot(13,10,4)
  u.shelf(7,3,3,3,'archive');u.table(8,15,4,2,'work','dark_oak');u.chair(9,13,'south',material='dark_oak');m.p(9,10,15,'white_carpet','work.paper')
  seat(m,8,19,8,3,'green');m.barrel(13,9,19);m.pot(13,10,19);picture(m,16,11,12)
  m.addkit(u);m.use('upstairs.work',13,16,8);m.use('upstairs.bed',15,7,8)
  m.room('public','营业、等候与柜台',6,11,w-3,d-3,2,6);m.room('service','摄影／分拣与储存',6,3,w-3,10,2,2)
  m.room('work','楼上工作与休息',6,12,w-3,d-3,8,3);m.room('bed','店主卧室',12,3,w-3,11,8,1)
  lamps(m,[(10,6,18),(15,6,13),(14,6,7),(7,6,9),(9,12,15),(14,12,6),(6,12,10),(w//2,5,d-2)])
  if kind=='photo':
   # Flat parapet hides only the front roof edge, with paired tall windows.
   m.box((2,14,d-3),(w-2,17,d-2),'light_gray_terracotta','kanban.parapet')
   for x in range(2,w-2):m.p(x,17,d-2,'quartz_slab','cornice',type='top')
   for x in [2,7,13,w-3]:
    for y in range(9,17):m.p(x,y,d-2,'bricks','pilaster')
   for x in [4,5,15,16]:
    for y in [10,11,12]:m.p(x,y,d-2,'dark_oak_trapdoor','window.shutter',facing='south',open=True)
  else:
   for y in [8,14]:
    for x in range(2,w-2):m.p(x,y,d-2,'quartz_slab','cornice',type='top')
   for x in [2,w-3]:
    for y in range(9,14):m.p(x,y,d-2,'oxidized_copper','pilaster')
  # Two planters are attached to a real sill, not floating against glass.
  for x in [5,w-6]:m.p(x,8,d-2,'dark_oak_slab','window.sill',type='top');m.pot(x,9,d-2)
 m.addkit(k)
 for x in [3,w-4]:
  m.barrel(x,3,d-4);m.pot(x,4,d-4)
 return m
