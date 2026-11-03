"""Qilou02: one authored urban block, twelve programmes and four turning arcades.
This is a bounded case adapter, not a general city generator or measured replica.
"""
from pathlib import Path
import sys,json,copy,random,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support')]
import qilou_core as C,nbtlib as n
from detail_lab import states as S
from prototype_base import Study
from vendor.voxel_core import parse_state
RUN=sys.argv[1];SEED=int(sys.argv[2]) if len(sys.argv)>2 else 311145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=True)
S.FULL.update({'red_wool','blue_wool','cyan_wool'})
C.OUT=OUT;C.SEED=SEED
CONFIG=[
 {'id':'Post','name':'惠民邮局','origin':[28,0,24],'turn':2,'w':23,'levels':2,'wall':'bricks','kind':'corner','program':'mail'},
 {'id':'Apothecary','name':'济安药铺','origin':[51,0,24],'turn':2,'w':17,'levels':3,'wall':'white_concrete','kind':'classical','program':'medicine'},
 {'id':'Grain','name':'德昌粮油','origin':[73,0,24],'turn':2,'w':15,'levels':2,'wall':'smooth_sandstone','kind':'plain','program':'grain'},
 {'id':'Bookshop','name':'清和书局','origin':[85,0,28],'turn':3,'w':23,'levels':2,'wall':'white_concrete','kind':'corner','program':'books'},
 {'id':'Barber','name':'松柏理发','origin':[85,0,51],'turn':3,'w':15,'levels':2,'wall':'white_terracotta','kind':'plain','program':'barber'},
 {'id':'Hardware','name':'顺兴五金','origin':[85,0,71],'turn':3,'w':17,'levels':2,'wall':'light_gray_concrete','kind':'plain','program':'hardware'},
 {'id':'Teahouse','name':'榕荫茶楼','origin':[91,0,85],'turn':0,'w':23,'levels':3,'wall':'smooth_sandstone','kind':'corner','program':'tea'},
 {'id':'Textile','name':'永丰布庄','origin':[74,0,85],'turn':0,'w':17,'levels':2,'wall':'white_concrete','kind':'plain','program':'textile'},
 {'id':'Grocery','name':'和顺杂货','origin':[54,0,85],'turn':0,'w':15,'levels':2,'wall':'white_terracotta','kind':'plain','program':'grocery'},
 {'id':'Inn','name':'永安客栈','origin':[24,0,91],'turn':1,'w':23,'levels':3,'wall':'white_terracotta','kind':'corner','program':'inn'},
 {'id':'Clinic','name':'杏林诊所','origin':[24,0,76],'turn':1,'w':15,'levels':3,'wall':'white_concrete','kind':'plain','program':'clinic'},
 {'id':'Bakery','name':'福记饼铺','origin':[24,0,54],'turn':1,'w':17,'levels':2,'wall':'smooth_sandstone','kind':'plain','program':'bakery'},
]

def counter(m,x,z,w,f=2):
 for xx in range(x,x+w):m.barrel(xx,f+1,z);m.p(xx,f+2,z,'dark_oak_trapdoor','service.counter',half='bottom')

def shelf(m,x,z,w,h=2,f=2):
 k=m.kit(f);k.shelf(x,z,w,h,'books');m.addkit(k)

def home(m,f):
 C.bedroom(m,f);C.kitchen(m,7,15,f,5)
 C.bench(m,7,25,f,4,'green');C.table(m,8,22,f,3,1,False,'home.tea')
 m.barrel(m.w-3,f+1,19);m.pot(m.w-3,f+2,19)
 m.use('home.living',6,24,f);m.use('home.kitchen',10,17,f)
 m.room('living','起居、厨房与收纳',5,14,m.w-1,28,f,3)

def shop(r):
 key=r['id']
 if key=='Grocery':return C.grocery()
 if key=='Apothecary':return C.apothecary()
 if key=='Teahouse':return C.teahouse()
 m=C.build_shell(key,r['w'],r['levels'],r['name'],r['wall'],r['kind'])
 if key=='Textile':
  for z,col in [(16,'white_wool'),(18,'cyan_wool'),(20,'brown_wool')]:
   for x in [13,14]:m.p(x,3,z,col,'fabric.roll');m.p(x,4,z,'dark_oak_slab','fabric.cap',type='bottom')
  for z in [18,20,22]:m.p(1,3,z,'white_wool','fabric.display');m.p(1,4,z,'dark_oak_slab','fabric.shelf',type='bottom')
  C.table(m,7,17,2,4,2,False,'cutting');m.p(8,4,17,'white_carpet','fabric.fold')
  counter(m,8,9,5);m.p(10,4,9,'flower_pot','supplies')
  for x in [6,10,14]:m.barrel(x,3,5)
  m.use('fabric',11,20);m.use('cutting',10,19);m.use('stock',12,6);m.use('counter',10,11)
  m.room('retail','布匹陈列、裁剪与结账',5,14,16,23,2,5);m.room('stock','布料与辅料库',5,4,16,13,2,2);home(m,9)
 elif key=='Grain':
  for x in [5,8,11]:
   for z in [7,10]:m.barrel(x,3,z);m.barrel(x,4,z)
  for x in [5,7,9]:m.barrel(x,3,19);m.p(x,4,19,'flower_pot','grain.measure')
  counter(m,10,16,3);m.p(11,4,16,'flower_pot','oil.jar')
  C.table(m,8,13,2,3,1,False,'packing')
  m.use('browse',7,21);m.use('pay',11,18);m.use('stock',10,9);m.use('pack',10,14)
  m.room('shop','粮油陈列、计量与收银',4,14,14,23,2,4);m.room('stock','袋装与桶装库存',4,4,14,13,2,2);home(m,9)
 elif key=='Barber':
  for z in [16,20]:
   m.p(13,4,z,'cyan_stained_glass','mirror');m.p(13,5,z,'glass','mirror.highlight')
   m.barrel(12,3,z,'west');m.p(12,4,z,'dark_oak_slab','barber.station',type='top')
   k=m.kit(2);k.chair(10,z,'east',material='dark_oak');m.addkit(k)
   m.use('chair.'+str(z),9,z)
  C.bench(m,4,21,2,3,'green');counter(m,5,16,3)
  k=m.kit(2);k.sink(10,5);k.cupboard(6,5,2,'towels');m.addkit(k)
  C.table(m,8,10,2,3,1,False,'cleaning');m.use('wash',10,6);m.use('pay',7,18)
  m.room('salon','理发、镜台与等候',4,15,14,23,2,5);m.room('service','清洗、毛巾与工具',5,4,14,13,2,2);home(m,9)
 elif key=='Hardware':
  for z in [16,18,20]:
   m.barrel(15,3,z,'west');m.p(15,5,z,'dark_oak_slab','tools.wall_shelf',type='top');m.p(15,6,z,'flower_pot','tools.small_parts')
  counter(m,7,17,5);m.p(8,3,8,'crafting_table','workbench');m.p(11,3,8,'anvil','anvil',facing='north')
  for x in[6,10,14]:m.barrel(x,3,5);m.barrel(x,4,5)
  C.table(m,9,12,2,4,1,False,'repair')
  m.use('browse',13,20);m.use('pay',9,19);m.use('repair',11,14);m.use('craft',8,9);m.use('anvil',11,9)
  m.room('shop','五金、零件与收银',5,15,16,23,2,4);m.room('work','维修工作台与备货',5,4,16,14,2,2);home(m,9)
 elif key=='Bakery':
  C.kitchen(m,7,4,2,8);C.table(m,8,8,2,4,1,False,'kneading')
  m.box((5,3,12),(16,9,13),'white_terracotta','back.partition');m.door(10,3,12,wood='dark_oak')
  m.lights=[l for l in m.lights if l['position']!=[13,7,12]];m.lamp(13,7,14)
  counter(m,7,17,7)
  for x in[8,11]:m.p(x,4,17,'cake','pastry',bites=0)
  C.bench(m,3,21,2,3,'brown');C.table(m,4,19,2,3,1,False,'tasting')
  m.use('pay',10,19);m.use('seats',6,20);m.use('oven',8,6);m.use('prep',11,10)
  m.room('shop','糕点展示、点单与小座席',3,14,16,23,2,5);m.room('bake','烘焙、清洗与备料',5,4,16,12,2,2);home(m,9)
 elif key=='Clinic':
  counter(m,8,17,5);C.bench(m,9,21,2,3,'green');C.table(m,8,10,2,3,2,True,'consult')
  m.box((5,3,14),(14,9,15),'white_terracotta','consult.privacy');m.door(7,3,14,wood='dark_oak')
  k=m.kit(2);k.sink(11,5);k.cupboard(7,5,2,'supplies');m.addkit(k)
  m.use('registration',10,19);m.use('consult',11,10);m.use('wash',11,6)
  for x in [6,11]:
   k=m.kit(9);k.bed(x,8);m.addkit(k);m.barrel(x,10,5);m.pot(x,11,5);m.use('rest.'+str(x),x+1,8,9)
  m.box((9,10,4),(10,13,11),'white_terracotta','rest.screen')
  C.table(m,7,19,9,4,2,True,'staff');shelf(m,7,14,3,2,9);m.use('staff',12,19,9)
  m.room('clinic','挂号、等候与诊间',5,4,14,23,2,5);m.room('rest','休息床位、屏风与值班',5,4,14,28,9,4);home(m,15)
 elif key=='Post':
  counter(m,6,17,10)
  for x in[6,9,12,15]:
   for z in[5,8]:m.barrel(x,3,z);m.barrel(x,4,z)
  C.table(m,7,12,2,5,2,False,'sorting');C.table(m,4,20,2,3,1,True,'writing');C.bench(m,11,21,2,4,'green')
  m.use('counter',10,19);m.use('sort',12,14);m.use('postboxes',13,6);m.use('writing',7,20)
  shelf(m,6,4,10,2,9);C.table(m,7,11,9,4,2,True,'clerks');C.table(m,15,18,9,4,2,True,'accounts');C.bench(m,7,25,9,5,'brown')
  m.barrel(20,10,24);m.pot(20,11,24);m.use('office',12,11,9);m.use('accounts',19,18,9);m.use('records',10,5,9)
  m.room('public','邮务柜台、写信与等候',4,15,17,23,2,8);m.room('sort','分拣、信件与包裹柜',5,4,17,15,2,3);m.room('office','邮务办公、账房与档案',5,4,22,28,9,6)
 elif key=='Bookshop':
  shelf(m,6,4,9,3);shelf(m,5,9,3,3);shelf(m,11,9,4,3);counter(m,11,18,4)
  C.table(m,6,18,2,3,2,False,'book.display');m.p(7,3,14,'bookshelf','low.display')
  m.use('browse',9,10);m.use('pay',13,20);m.use('display',8,20)
  shelf(m,6,4,13,3,9);shelf(m,5,10,4,2,9);shelf(m,13,10,5,2,9)
  C.table(m,6,18,9,4,2,True,'reading');C.table(m,15,20,9,4,2,True,'reading');C.bench(m,7,25,9,5,'green')
  for x,z in[(12,18),(19,22),(10,11),(10,5)]:m.use('read.'+str(x)+'.'+str(z),x,z,9)
  m.room('shop','书架、选书与结账',5,4,17,23,2,7);m.room('reading','藏书、阅览与窗边长座',5,4,22,28,9,10)
 elif key=='Inn':
  m.box((5,3,11),(17,9,12),'white_terracotta','kitchen.partition');m.door(13,3,11,wood='dark_oak')
  C.kitchen(m,7,4,2,8);C.table(m,8,8,2,4,1,False,'breakfast.prep');counter(m,8,17,7)
  m.pot(8,4,17);m.picture(10,6,12)
  for x in[7,8,9,10]:m.p(x,5,12,'dark_oak_trapdoor','reception.key_rack',facing='north',open=True)
  C.bench(m,3,21,2,4,'brown');C.table(m,4,19,2,3,1,False,'lobby.tea')
  m.use('reception',10,19);m.use('lobby',7,20);m.use('kitchen',12,7)
  m.room('lobby','客栈前台、等候与早餐后厨',4,4,17,23,2,7)
  for f in[9,15]:
   m.box((5,f+1,4),(6,f+6,14),'white_terracotta','guest.partition')
   m.box((14,f+1,4),(15,f+6,14),'white_terracotta','guest.partition')
   m.box((5,f+1,13),(22,f+6,14),'white_terracotta','guest.partition')
   for x in[9,18]:
    m.door(x,f+1,13,wood='dark_oak');k=m.kit(f);k.bed(x,8);k.cupboard(x+2,5,1,'guest.wardrobe');m.addkit(k)
    m.barrel(x-1,f+1,7);m.pot(x-1,f+2,7);m.use('guest.'+str(f)+'.'+str(x),x+1,8,f)
    m.room('guest.'+str(f)+'.'+str(x),'独立客房',x-3,4,x+4,13,f,1)
   C.bench(m,7,25,f,5,'green');C.table(m,8,22,f,4,1,False,'guest.lounge')
   k=m.kit(f);k.sink(18,17);m.addkit(k);m.barrel(20,f+1,17);m.use('wash.'+str(f),18,18,f);m.use('lounge.'+str(f),13,24,f)
 return with_stairs(m)

def with_stairs(m):C.circulation(m);return m

def decorate(m,r):
 # A front-to-back public lane never depends on independent random block choices.
 C.interior_finish(m);C.finish(m)
 signs={'Post':'邮务・信件','Bookshop':'书籍・阅览','Inn':'住宿・茶点','Teahouse':'茶・点心','Bakery':'糕点・烘焙','Clinic':'问诊・等候','Barber':'理发・修面','Grain':'粮食・油米','Hardware':'五金・修理','Textile':'布匹・裁剪','Apothecary':'药材・咨询','Grocery':'日用・杂货'}
 m.sign(m.entry[0],7,24,'south',[r['name'],signs[m.id]])
 # Corner two-storey variants do not inherit the third-storey round-window motif.
 if r['kind']=='corner' and r['levels']==2:
  for q in list(m.blocks):
   if q[2]==29 and 16<=q[1]<=20 and 9<=q[0]<=13:m.p(*q,'air')
  # Restore the two-storey parapet plane where the base motif would otherwise sit.
  for x in range(9,14):
   for y in range(16,21):
    if (x,y,28)in m.blocks:m.p(x,y,28,r['wall'],'two_storey.parapet')
 # Relocate inherited small artwork if a programme-specific cabinet occupies its anchor.
 for e in m.entities:
  q=tuple(int(e[k])for k in ['TileX','TileY','TileZ'])
  if q in m.blocks:
   f=max(m.floors);chosen=None
   for x in range(m.w-3,4,-1):
    p=(x,f+3,4)
    if p not in m.blocks and S.support_cube(m.blocks.get((x,f+3,3),'minecraft:air')):chosen=p;break
   assert chosen is not None,(m.id,'art anchor')
   for k,v in zip(['TileX','TileY','TileZ'],chosen):e[k]=n.Int(v)
   e['Pos']=n.List[n.Double]([n.Double(chosen[0]+.5),n.Double(chosen[1]+.5),n.Double(chosen[2]+.03125)])
 # Rear downpipes at corners would clash with the perpendicular neighbour.
 for q,owner in list(m.owners.items()):
  if owner.endswith('rear.downpipe'):m.p(*q,'air')
 if r['kind']=='corner':
  for q in list(m.blocks):
   if q[2]==2 and q[1]>2:m.p(*q,'air')
  for i,f in enumerate(m.floors):
   top=m.floors[i+1] if i+1<len(m.floors) else (15 if m.levels==2 else 21)
   for x in range(m.w if f>2 else 18):
    for y in range(f+1,top):m.p(x,y,3,r['wall'],'party.rear')
 else:
  for y in range(3,16 if m.levels==2 else 22):m.p(5,y,2,'diorite_wall','rear.downpipe',up=True)
 # Back doors of mid-block shops face the courtyard service lane, with their own clear frame.
 if r['kind']!='corner':
  m.door(4,3,3,'north','dark_oak');m.use('rear_entry',4,4);m.rear_entry=[4,3,3]
 else:m.rear_entry=None
 # Windows are kept fixed; shutters and cornice treatment vary by whole building.
 rng=random.Random(f'{SEED}/facade/{m.id}');shutters=rng.choice([False,True]);trim=rng.choice(['quartz','smooth_sandstone'])
 if shutters:
  for f in m.floors[1:]:
   z=26 if m.kind=='classical' else 29
   for x in ([1,6,9,14] if m.w>=17 else[1,6,8,13]):
    if x<m.w:
     for y in[f+2,f+3]:
      if (x,y,z)not in m.blocks:m.p(x,y,z,'dark_oak_trapdoor','shutter',facing='north',open=True)
 # Replace only selected cornice slabs, keeping profiles and collision unchanged.
 if trim=='smooth_sandstone':
  for q,owner in list(m.owners.items()):
   if 'coping' in owner and m.blocks.get(q,'').startswith('minecraft:quartz_slab'):m.p(*q,'smooth_sandstone_slab','coping.variant',type='top')
 m.facade_choice={'shutters':shutters,'coping':trim,'seed':f'{SEED}/facade/{m.id}'}
 # Distinct indoor colour accents and grouping, without changing the functional route.
 if m.id not in ['Grocery','Apothecary','Teahouse']:
  f=max(m.floors)
  for x,z in[(m.w-3,24),(m.w-3,15)]:
   if (x,f+1,z)not in m.blocks:m.barrel(x,f+1,z);m.pot(x,f+2,z)
 for d in m.doors:
  x,y,z=d['pos'];dx,dz=(1,0)if d['facing']in['north','south']else(0,1)
  m.p(x,y+2,z,'dark_oak_planks','door.head')
  for sg in[-1,1]:
   for yy in[y,y+1]:m.p(x+sg*dx,yy,z+sg*dz,'dark_oak_planks','door.jamb')
 return m

def rotq(q,w,d,k,point=False):
 x,y,z=q
 for _ in range(k):x,z=(d if point else d-1)-z,x;w,d=d,w
 return [x,y,z]
def rotate(st,k):
 for _ in range(k):st=S.rotate_state(st)
 return st
def translated(q,r,point=False):
 q=rotq(q,r['w'],33,r['turn'],point);return [q[i]+r['origin'][i]for i in range(3)]
def arcade(m):
 cells={(x,z)for x in range(m.w if m.kind!='corner'else 20)for z in range(24,28)}
 if m.kind=='corner':cells|={(x,z)for x in range(18,22)for z in range(3,27)}
 return sorted(cells)
