"""Qilou03: an authored, open Guangzhou-inspired street district.
A case adapter using verified Qilou02 components; not a measured replica.
"""
from pathlib import Path
import sys,copy,json,math,random,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support')]
import nbtlib as n
import qilou_core as C,qilou_recipes as R
from prototype_base import Study
from detail_lab import states as S
RUN=sys.argv[1];SEED=int(sys.argv[2])if len(sys.argv)>2 else 311145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=True)
C.OUT=R.OUT=OUT;C.SEED=R.SEED=SEED
W,D,H=244,216,58
CONFIG=[]
old={r['id']:r for r in R.CONFIG}
for key,x,z,turn in [('Bookshop',13,78,1),('Grain',43,72,0),('Apothecary',58,72,0),('Post',75,72,0),('Teahouse',120,78,1),('Textile',150,72,0),('Hardware',167,72,0),('Clinic',84,117,2),('Inn',120,117,2),('Grocery',143,117,2),('Barber',158,117,2),('Bakery',173,117,2)]:
 r=copy.deepcopy(old[key]);r.update(origin=[x,0,z],turn=turn,family='qilou');CONFIG.append(r)
# Deliberately varied parcels, heights, setbacks and programmes, with routes fixed before details.
modern=[
 ('V01','榕里冰室',18,117,17,4,2,'cafe','white_terracotta','splay'),
 ('V02','佳宜便利',41,117,19,6,2,'retail','light_gray_concrete','balcony'),
 ('V03','阿华修理',64,117,17,5,2,'repair','white_concrete','screen'),
 ('V04','东榕面馆',201,72,17,5,0,'noodles','white_terracotta','splay'),
 ('V05','益民洗衣',222,72,17,4,0,'laundry','light_gray_concrete','balcony'),
 ('V06','街坊花店',196,117,17,5,2,'florist','white_concrete','screen'),
 ('V07','巷口茶餐室',219,117,19,4,2,'cafe','white_terracotta','balcony'),
 ('V08','榕北一巷 6 号',18,30,17,5,0,'home','white_concrete','balcony'),
 ('V09','榕北二巷 12 号',41,27,19,4,0,'home','white_terracotta','screen'),
 ('V10','邻里裁缝',66,32,19,6,0,'tailor','light_gray_concrete','balcony'),
 ('V11','榕东三巷 8 号',125,29,19,5,0,'home','white_concrete','screen'),
 ('V12','榕东四巷 3 号',151,26,19,4,0,'home','white_terracotta','balcony'),
 ('V13','榕南一巷 2 号',18,163,17,4,2,'home','light_gray_concrete','screen'),
 ('V14','小榕社区阅览室',45,160,19,5,2,'library','white_concrete','balcony'),
 ('V15','榕南三巷 7 号',121,161,19,4,2,'home','white_terracotta','screen'),
 ('V16','榕南四巷 9 号',151,166,19,6,2,'home','light_gray_concrete','balcony')]
for key,name,x,z,w,levels,turn,program,wall,form in modern:CONFIG.append(dict(id=key,name=name,origin=[x,0,z],w=w,levels=levels,turn=turn,program=program,wall=wall,kind=form,family='village'))

def chamfer(m,r):
 # Six-block diagonal corner, continuous through the upper facade and coping.
 # Relocate plant groups before cutting; do not simply delete an occupied room.
 for f in m.floors[1:]:
  for x,z in [(20,24),(20,23)]:
   if (x,f+1,z)in m.blocks:
    for dy in [1,2]:m.p(x,f+dy,z,'air')
  if (19,f+1,20)not in m.blocks:m.barrel(19,f+1,20);m.pot(19,f+2,20)
 for q in list(m.blocks):
  x,y,z=q
  if x+z>44 and (y>=9 or x>=18 and z>=24):m.p(*q,'air')
 top=15 if m.levels==2 else 21
 for x in range(16,23):
  z=44-x
  for f,up in zip(m.floors[1:],m.floors[2:]+[top]):
   for y in range(f+1,up):m.p(x,y,z,r['wall'],'chamfer.wall')
   for y in [f+2,f+3]:
    if x not in [16,19,22]:m.p(x,y,z,'cyan_stained_glass','chamfer.glazing')
   m.p(x,f,z,'smooth_quartz','chamfer.band')
  for y in [9,top]:m.p(x,y,z,'smooth_quartz','chamfer.cornice')
  for y in [top+1,top+2]:m.p(x,y,z,r['wall'],'chamfer.parapet')
  m.p(x,top+3,z,'quartz_slab','chamfer.coping',type='top')
 # Clear obsolete pier and use the diagonal ends as structural piers.
 for x,z in [(20,27),(22,19)]:
  for y in range(3,9):m.p(x,y,z,'air')
 for x,z in [(16,28),(22,22)]:
  m.p(x,3,z,'polished_andesite','chamfer.pier')
  for y in range(4,8):m.p(x,y,z,'quartz_pillar','chamfer.pier',axis='y')
  m.p(x,8,z,'chiseled_quartz_block','chamfer.cap')
 # Recorded lights must remain under a solid soffit.
 for lamp in m.lights:
  x,y,z=lamp['position']
  if x+z>44 and x>=18:
   m.p(x,y,z,'air');m.p(*lamp['support'],'air');lamp['position'][0]-=3;lamp['support'][0]-=3
   m.p(*lamp['position'],'lantern','corner.light',hanging=True);m.p(*lamp['support'],'chain','corner.chain',axis='y')
 m.variation=[q for q in m.variation if sum(q['position'][::2])<44]
 return m

def frame_doors(m):
 for d in m.doors:
  x,y,z=d['pos'];dx,dz=(1,0)if d['facing']in['north','south']else(0,1)
  m.p(x,y+2,z,'smooth_quartz','door.head')
  for sg in[-1,1]:
   for yy in[y,y+1]:m.p(x+sg*dx,yy,z+sg*dz,'smooth_quartz','door.jamb')

def modern_shop(m,r):
 p=r['program'];w=m.w
 # Independent residential entry and a rear doorway connect to the alley network.
 m.box((4,3,16),(5,9,29),'white_concrete','residential.separation');m.door(4,3,19,'east','birch')
 m.door(2,3,28,wood='birch');m.use('residential.entry',2,26)
 m.door(10,3,28,wood='dark_oak');m.entry=[10,3,28]
 m.door(4,3,3,'north','birch');m.rear_entry=[4,3,3];m.use('rear.entry',4,4)
 if p in ['cafe','noodles']:
  C.kitchen(m,7,5,2,min(7,w-9));m.box((5,3,12),(w-1,9,13),'white_terracotta','kitchen.screen');m.door(10,3,12,wood='birch')
  for x,z in [(7,17),(11,22)]:C.table(m,x,z,2,3,1,True,'guest');m.use('guest.'+str(z),x+3,z)
  C.bench(m,6,25,2,3,'green');R.counter(m,12,15,min(4,w-13));m.use('order',12,17);m.use('cook',10,7)
 elif p=='retail':
  for z in [7,10,18,21]:
   R.shelf(m,w-5,z,3,2);m.use('browse.'+str(z),w-6,z)
  R.counter(m,6,23,5);m.p(8,4,23,'flower_pot','till');m.use('pay',8,25)
  for x in [6,9,12]:m.barrel(x,3,5);m.barrel(x,4,5)
  C.table(m,7,15,2,3,2,False,'stock.sort');m.use('stock',10,15)
 elif p=='repair':
  for x in [6,9,12]:m.barrel(x,3,5);m.barrel(x,4,5)
  for z in [10,15,20]:m.p(w-3,3,z,'crafting_table','repair.work');m.barrel(w-3,3,z+1);m.p(w-3,5,z,'dark_oak_slab','tool.shelf',type='top');m.p(w-3,6,z,'flower_pot','parts');m.use('repair.'+str(z),w-4,z)
  R.counter(m,7,23,5);m.use('pay',9,25);m.p(8,3,14,'anvil','repair.anvil',facing='north');m.use('anvil',8,15)
 elif p=='laundry':
  for z in [7,11,15,19,23]:
   m.p(w-3,3,z,'smooth_quartz','machine');m.p(w-3,4,z,'white_stained_glass','machine.drum');m.p(w-3,5,z,'smooth_quartz','machine.top');m.use('wash.'+str(z),w-4,z)
  C.table(m,7,12,2,4,2,False,'folding');m.p(8,4,12,'white_carpet','towels');C.bench(m,6,25,2,3,'green');m.use('fold',10,14)
  k=m.kit(2);k.sink(8,5);m.addkit(k);m.use('sink',8,6)
 elif p=='florist':
  for x,z in [(7,7),(11,9),(7,17),(13,19),(12,24)]:
   m.barrel(x,3,z);m.pot(x,4,z);m.p(x,3,z+1,'terracotta','planter');m.pot(x,4,z+1)
  R.counter(m,7,23,3);m.use('pay',8,25);C.table(m,10,14,2,4,1,False,'arrange');m.use('arrange',12,15)
  m.room('flowers','盆栽陈列、修剪与包装',5,4,w-1,28,2,4)
 elif p in ['library','tailor']:
  for z in[5,9]:R.shelf(m,6,z,w-8,2)
  C.table(m,7,17,2,4,2,True,'reading'if p=='library'else'cutting');C.bench(m,7,25,2,4,'brown');m.use('work',12,18);m.use('books',10,10)
  if p=='tailor':
   for z in[20,23]:m.p(w-3,3,z,'cyan_wool','fabric');m.p(w-3,4,z,'dark_oak_slab','fabric.cap',type='bottom')
 else:
  C.bench(m,7,25,2,4,'green');C.table(m,8,22,2,3,1,False,'shared.tea');m.use('community.seat',6,24)
  R.shelf(m,7,5,w-9,2);C.table(m,8,12,2,3,2,True,'shared.reading');m.use('reading',12,12)
  for z in[17,19]:m.barrel(w-3,3,z);m.pot(w-3,4,z)
 m.use('shop.entry',10,27);m.room('ground',r['name']+' · 店面与后勤',5,4,w-1,28,2,6)

def village(r):
 w=r['w'];m=Study(r['id'],w,33,r['levels'],r['name']);m.seed=SEED;m.h=H;m.kind=r['kind'];m.floors=[2+7*i for i in range(r['levels'])];m.variation=[];m.facade_choice={};m.source=['User: Rongyinli V4 urban-village reference; adapted new geometry']
 wall=r['wall'];top=m.floors[-1]+7;split=r['kind']=='splay';cut=w+22
 def inside(x,z):return not(split and x+z>cut)
 m.box((0,0,0),(w,2,33),'dirt','base');m.box((0,2,0),(w,3,33),'smooth_stone','paving')
 for f,ceiling in zip(m.floors,m.floors[1:]+[top]):
  for x in range(w):
   for z in range(3,29):
    if not inside(x,z):continue
    m.p(x,f,z,'oak_planks'if f>2 else'polished_andesite','floor')
    for y in[ceiling-1,ceiling]:m.p(x,y,z,'smooth_stone','ceiling')
    if x in[0,w-1]or z in[3,28]or split and x+z==cut:
     for y in range(f+1,ceiling-1):m.p(x,y,z,wall,'wall')
  # Wide grouped windows; framing and sill work in the actual wall plane.
  for z,out in [(3,-1),(28,1)]:
   for a,b in[(5,9),(11,w-2)]:
    if b>a:
     for x in range(a,b):
      if inside(x,z):
       for y in[f+2,f+3]:m.p(x,y,z,'white_stained_glass_pane'if x%3 else'gray_stained_glass_pane','window')
       m.p(x,f+1,z,'smooth_quartz','sill');m.p(x,f+4,z,'smooth_stone','lintel')
  # Both exposed side facades address alleys with actual windows and tile bands.
  for side in [0,w-1]:
   for z in [5,6,7,18,19,20,24,25,26]:
    if not inside(side,z):continue
    for y in [f+2,f+3]:m.p(side,y,z,'white_stained_glass_pane','side.window')
    m.p(side,f+1,z,'smooth_quartz','side.sill');m.p(side,f+4,z,'smooth_quartz','side.head')
   for z in range(3,29):
    if inside(side,z):m.p(side,f,z,'smooth_stone','side.floor_band')
   for y in range(f+1,ceiling-1):m.p(side,y,16,'smooth_quartz','side.pier')
  if split:
   for x in range(w-6,w):
    z=cut-x
    if 3<=z<=28:
     for y in[f+2,f+3]:m.p(x,y,z,'cyan_stained_glass','corner.window')
     m.p(x,f,z,'smooth_quartz','corner.band');m.p(x,f+4,z,'smooth_quartz','corner.lintel')
  for x,z in[(9,8),(10,19),(6,24)]:
   m.p(x,ceiling-1,z,'sea_lantern','embedded.light');m.lights.append({'position':[x,ceiling-1,z],'support':[x,ceiling,z],'type':'sea_lantern'})
  for x in range(w):
   if inside(x,28):m.p(x,f,29,'smooth_stone_slab','slab.edge',type='top')
  if f>2:
   R.home(m,f);C.table(m,7,18,f,3,1,True,'home.dining');m.use('home.dining.'+str(f),11,19,f)
   if w>=19:
    R.shelf(m,w-5,14,3,2,f);m.use('books.'+str(f),w-6,14,f)
   # Distinct balcony versus recessed-window families. Balcony is a usable extension.
   if r['kind']=='balcony':
    for x in range(10,w-1):
     for z in[29,30,31]:m.p(x,f,z,'smooth_stone','balcony.slab')
     m.p(x,f+1,31,'iron_bars','balcony.guard')
    for z in[29,30]:m.p(10,f+1,z,'iron_bars','balcony.return');m.p(w-2,f+1,z,'iron_bars','balcony.return')
    m.door(12,f+1,28,wood='birch');m.use('balcony.'+str(f),12,30,f)
    m.p(w-3,f+1,30,'terracotta','balcony.pot');m.pot(w-3,f+2,30)
   else:
    for x in range(5,9):
     if inside(x,28):m.p(x,f+2,29,'iron_bars','window.cage')
   # Exterior equipment grouped on solid bays rather than windows.
   m.p(3,f+2,29,'smooth_quartz','ac.unit');m.p(3,f+2,30,'iron_trapdoor','ac.grille',facing='north',open=True)
 modern_shop(m,r);C.circulation(m);frame_doors(m)
 # Remove hanging stair lights in favor of small inset landings.
 for l in m.lights:
  if l.get('type')!='sea_lantern':m.p(*l['support'],'chain','stair.chain',axis='y')
 # Roof with access headhouse, water tank, drying rack and planted service edge.
 for x in range(w):
  for z in[3,28]:
   if inside(x,z):m.p(x,top+1,z,'diorite_wall','roof.guard',up=True)
 for z in range(4,28):
  for x in[0,w-1]:
   if inside(x,z):m.p(x,top+1,z,'diorite_wall','roof.guard',up=True)
 m.box((1,top+1,6),(6,top+4,12),'white_concrete','roof.headhouse');m.box((1,top+4,6),(6,top+5,12),'smooth_stone_slab','roof.headhouse_cap',type='bottom')
 m.box((w-7,top+1,6),(w-3,top+4,10),'light_gray_concrete','tank');m.box((w-7,top+4,6),(w-3,top+5,10),'smooth_stone_slab','tank.cap',type='bottom')
 for z in[17,23]:
  for y in range(top+1,top+4):m.p(w-3,y,z,'iron_bars','drying.rack')
 for z in range(17,24):m.p(w-3,top+4,z,'iron_bars','drying.rail')
 for z in[18,20,22]:m.p(w-3,top+3,z,'white_wool','drying.cloth')
 for x in[7,9]:m.p(x,top+1,24,'terracotta','roof.planter');m.pot(x,top+2,24)
 for y in range(3,top+2):m.p(w-2,y,2,'diorite_wall','rear.pipe',up=True)
 # Storefront band and modest rain canopy, outside the public walking reserve.
 accent={'cafe':'green_wool','noodles':'red_wool','retail':'cyan_wool','laundry':'blue_wool','florist':'green_wool','repair':'gray_wool','tailor':'brown_wool','library':'cyan_wool','home':'gray_wool'}[r['program']]
 for x in range(5,w-1):
  if inside(x,28):m.p(x,7,29,accent,'shop.signband');m.p(x,8,30,'smooth_stone_slab','shop.awning',type='top')
 # An asymmetric side drain and two wall lights add service scale without filling the alley.
 for y in range(3,top+1):m.p(0,y,10,'light_gray_concrete','side.drain')
 for z in [17,25]:
  m.p(0,7,z,'sea_lantern','side.wall_light');m.lights.append({'position':[0,7,z],'support':[0,8,z],'type':'sea_lantern'})
 m.sign(10,7,30,'south',[r['name'],'街坊生活・楼上住家'])
 m.barrel(6,3,27);m.pot(6,4,27)
 for f in m.floors[1:]:m.picture(7,f+3,4,'south','aztec');m.p(7,f+3,3,'dark_oak_planks','art.back')
 m.facade_choice={'family':r['kind'],'levels':r['levels'],'wall':wall,'accent':accent,'variation':'Fixed programme and massing; bounded potted species by seed'}
 return m

def arcade(m):
 if m.id.startswith('V'):return []
 if m.kind!='corner':return [(x,z)for x in range(m.w)for z in range(24,28)]
 return [(x,z)for x in range(m.w)for z in range(3,29)if (z>=24 or x>=18)and x+z<=43 and (x,z)not in[(22,3),(22,11),(22,22),(16,28)] and x<22 and z<28]

mods=[]
for r in CONFIG:
 m=village(r)if r['family']=='village'else R.decorate(R.shop(r),r)
 if r['family']=='qilou'and r['kind']=='corner':chamfer(m,r)
 mods.append(m)
 sp=m.stats();sp.update(levels=m.levels,kind=m.kind,family=r['family'],program=r['program'],upper_starts=m.upper_starts,stair_runs=m.stair_runs,spawn_local=[m.w//2,3,32],arcade_cells_local=arcade(m),variation=m.variation,facade_choice=m.facade_choice,rear_entry=m.rear_entry,placement=r)
 C.save(m,m.id,sp,(m.w,m.h,m.d))
 print('module',m.id,len(m.blocks),flush=True)
city=Study('Qilou03',W,D,1,'檐下榕里 · 广州街巷试作');city.seed=SEED
city.box((0,0,0),(W,2,D),'dirt','urban.base');city.box((0,2,0),(W,3,D),'smooth_stone','urban.ground')
roads=[{'id':'east_west_main','bounds':[0,104,W,116],'width':12}, {'id':'north_south','bounds':[103,0,113,D],'width':10}, {'id':'east_T','bounds':[187,0,196,104],'width':9}]
road=set();lane=set();public_arcade=set();records=[];overwrites=[]
for rr in roads:
 x,z,X,Z=rr['bounds']
 for xx in range(x,X):
  for zz in range(z,Z):city.p(xx,2,zz,'gray_concrete','road');road.add((xx,zz))
# Restrained markings are coherent patches; no random speckled asphalt.
for x in range(4,W-3,10):
 for dx in range(4):
  if not 98<=x+dx<=119 and not 183<=x+dx<=200:city.p(x+dx,2,110,'yellow_concrete','road.center')
for z in range(3,D-3,10):
 if not 98<=z<=121:
  for dz in range(4):city.p(108,2,z+dz,'yellow_concrete','road.center')
for z in[99,118]:
 for x in range(103,113,2):
  for zz in range(z,z+3):city.p(x,2,zz,'white_concrete','crosswalk')
for x in[98,116,182]:
 for z in range(104,116,2):
  for xx in range(x,x+3):city.p(xx,2,z,'white_concrete','crosswalk')
# Narrow service streets and offset passages; they connect to main roads rather than form a court ring.
alleys=[{'id':'north_back','bounds':[8,66,187,72]}, {'id':'north_east_back','bounds':[196,64,244,70]}, {'id':'south_west_back','bounds':[8,151,103,157]}, {'id':'south_east_back','bounds':[113,151,194,157]}, {'id':'south_jog','bounds':[190,151,196,165]}, {'id':'park_lane','bounds':[190,159,244,165]}]
for x,X in [(10,15),(35,41),(60,64),(86,94),(171,180)]:alleys.append({'id':'north_cross_'+str(x),'bounds':[x,24,X,66]})
for x,X in[(36,41),(66,71),(80,84),(173,181),(214,219)]:alleys.append({'id':'south_cross_'+str(x),'bounds':[x,150,X,200]})
for rr in alleys:
 x,z,X,Z=rr['bounds']
 for xx in range(x,X):
  for zz in range(z,Z):
   if (xx,zz)not in road:city.p(xx,2,zz,'stone_bricks'if (xx//4+zz//5)%6 else'andesite','lane');lane.add((xx,zz))
for r,m in zip(CONFIG,mods):
 occupied=[]
 for q,st in m.blocks.items():
  if q[1]<=2 and not 3<=q[2]<=28:continue
  p=R.translated(q,r);ss=R.rotate(st,r['turn']);oldst=city.blocks.get(tuple(p))
  if p[1]>2 and oldst and oldst!=ss:overwrites.append({'at':p,'old':oldst,'new':ss,'incoming':m.id})
  city.p(*p,ss,m.owners.get(q,'building'));occupied.append(p)
 for q,be in m.bes.items():city.bes[tuple(R.translated(q,r))]=copy.deepcopy(be)
 for e in m.entities:
  ee=copy.deepcopy(e);ee['Pos']=n.List[n.Double]([n.Double(v)for v in R.translated(list(map(float,e['Pos'])),r,True)])
  q=R.translated([int(e[k])for k in['TileX','TileY','TileZ']],r)
  for k,v in zip(['TileX','TileY','TileZ'],q):ee[k]=n.Int(v)
  face=['south','west','north','east'][int(e['facing'])]
  for _ in range(r['turn']):face=S.TURN[face]
  ee['facing']=n.Byte(['south','west','north','east'].index(face));city.entities.append(ee)
 for x,z in arcade(m):q=R.translated([x,3,z],r);public_arcade.add((q[0],q[2]))
 records.append({**r,'floors':m.floors,'entry':R.translated(m.entry,r),'side_entry':R.translated([17,3,16],r)if m.kind=='corner'else R.translated([2,3,28],r)if r['family']=='village'else None,'rear_entry':R.translated(m.rear_entry,r)if m.rear_entry else None,'source_nbt_sha256':hashlib.sha256((OUT/(m.id+'.nbt')).read_bytes()).hexdigest(),'geometry_bounds':[[min(p[i]for p in occupied),max(p[i]for p in occupied)+1]for i in range(3)]})
assert not overwrites,overwrites[:20]
# Reserve the actual pedestrian route surface; road and alley masks must never cross a building.
for xx,zz in list(lane):
 if (xx,3,zz)in city.blocks:raise AssertionError(('lane/building overlap',xx,zz,city.owners.get((xx,3,zz))))
trees=[];protected=set(city.blocks)
# Protect room air, balconies and functional approaches as well as their enclosing blocks.
for r,m in zip(CONFIG,mods):
 roof_y=max(q[1]for q in m.blocks)
 for x in range(m.w):
  for z in range(3,32):
   for y in range(3,roof_y+1):protected.add(tuple(R.translated([x,y,z],r)))
def tree(x,z,height,radius,id):
 rng=random.Random(f'{SEED}/tree/{id}');h=height+rng.choice([-1,0,1]);actual=[]
 # Only the center is a ground obstacle; tree pits are outside the carriageways and reserved lanes.
 assert (x,z)not in road|lane|public_arcade,(id,x,z)
 for xx in range(x-1,x+2):
  for zz in range(z-1,z+2):
   if (xx,zz)not in road|lane|public_arcade and (xx,3,zz)not in city.blocks:
    city.p(xx,2,zz,'grass_block','tree.pit')
    if rng.random()<.25 and (xx,zz)!=(x,z):city.p(xx,3,zz,rng.choice(['fern','short_grass','azure_bluet']),'tree.groundcover')
 for y in range(3,3+h):
  if (x,y,z)not in city.blocks:city.p(x,y,z,'oak_log','tree.trunk',axis='y')
 crown=3+h-1
 for dx,dz,dy,rad in[(0,0,0,radius),(-2,1,-1,max(3,radius-1)),(2,-2,1,max(3,radius-1))]:
  for xx in range(max(0,x+dx-rad),min(W,x+dx+rad+1)):
   for zz in range(max(0,z+dz-rad),min(D,z+dz+rad+1)):
    for yy in range(crown+dy-2,crown+dy+3):
     q=(xx,yy,zz)
     if ((xx-x-dx)/rad)**2+((zz-z-dz)/rad)**2+((yy-crown-dy)/2.25)**2<=1 and q not in city.blocks and rng.random()>.025:
      # Keep a two-cell buffer to every existing architectural solid/window.
      if any((xx+a,yy,zz+b)in protected for a,b in[(0,0),(1,0),(-1,0),(0,1),(0,-1)]):continue
      city.p(*q,'oak_leaves','tree.crown');actual.append(q)
 trees.append({'id':id,'anchor':[x,3,z],'height':h,'radius':radius,'leaf_blocks':len(actual),'seed':f'{SEED}/tree/{id}'})
# Banyan-like broad crowns used as a voxel abstraction, not botanical replicas.
for i,(x,z,h,rad)in enumerate([(28,102,10,6),(55,102,10,6),(80,102,11,6),(138,102,11,6),(164,102,10,6),(205,102,10,6),(231,102,10,6),(28,118,10,6),(53,118,11,6),(79,118,10,5),(138,118,10,6),(161,118,11,6),(185,118,10,5),(210,118,10,6),(234,118,10,5),(100,45,11,6),(115,59,11,6),(100,177,12,7),(115,193,10,6),(181,41,11,6),(207,181,10,7),(225,184,12,7),(217,201,10,6),(8,191,11,6),(8,36,11,6),(73,199,11,6),(88,15,12,7),(142,14,11,7)]):tree(x,z,h,rad,'street.'+str(i))
# Small public garden and service corners, separated from the street chain.
for x in range(198,240):
 for z in range(169,207):
  if (x,3,z)not in city.blocks:city.p(x,2,z,'grass_block','pocket.garden')
for x in range(198,239):
 for z in range(190,195):city.p(x,2,z,'stone_bricks','garden.walk');lane.add((x,z))
for x in range(198,203):
 for z in range(165,195):city.p(x,2,z,'stone_bricks','garden.link');lane.add((x,z))
for x,z in [(207,187),(224,197),(72,171),(94,57)]:
 C.bench(city,x,z,2,4,'green');city.barrel(x+6,3,z);city.pot(x+6,4,z)
# Small rear gardens give the peripheral hardscape a domestic boundary.
for x,z,X,Z in [(18,16,35,28),(42,12,60,25),(67,16,85,30),(126,13,145,27),(152,10,170,24),(18,199,35,211),(45,196,64,209),(122,197,140,210),(152,202,170,213)]:
 for xx in range(x,X):
  for zz in range(z,Z):
   if (xx,zz)not in lane|road and (xx,3,zz)not in city.blocks:city.p(xx,2,zz,'grass_block','rear.garden')
 for xx in range(x,X):
  if abs(xx-(x+X)//2)>1:
   for zz in[z,Z-1]:city.p(xx,3,zz,'cobblestone_wall','yard.boundary',up=True)
 for zz in range(z,Z):
  for xx in[x,X-1]:city.p(xx,3,zz,'cobblestone_wall','yard.boundary',up=True)
 for xx,zz in[(x+2,z+2),(X-3,Z-3)]:city.p(xx,3,zz,'terracotta','garden.planter');city.pot(xx,4,zz)
# Paved service edge to the east, with planted strips rather than a featureless apron.
for x,z,X,Z in [(201,10,239,14),(201,24,205,55),(234,24,239,55),(2,4,7,207)]:
 for xx in range(x,X):
  for zz in range(z,Z):
   if (xx,zz)not in road|lane and (xx,3,zz)not in city.blocks:
    city.p(xx,2,zz,'grass_block','edge.planting')
    if (xx*7+zz*3)%13==0:city.p(xx,3,zz,'fern','edge.fern')
# Slim street lights and bus shelter: furnish the edge, leave the path continuous.
for x,z in[(14,102),(69,102),(151,102),(218,102),(40,118),(114,136),(114,38),(101,83),(186,28),(101,194)]:
 for y in range(3,8):city.p(x,y,z,'iron_bars','street.lamp_pole')
 city.p(x,8,z,'sea_lantern','street.lamp');city.p(x,9,z,'smooth_stone_slab','street.lampcap',type='bottom')
for x in range(54,65):
 city.p(x,7,118,'green_wool','bus.canopy');city.p(x,7,119,'green_wool','bus.canopy')
for x in[54,64]:
 for y in range(3,7):city.p(x,y,119,'iron_bars','bus.post')
C.bench(city,57,119,2,4,'green')
# Preserve every block of the modules; future fixtures must avoid architecture.
for r,m in zip(CONFIG,mods):
 for q,st in m.blocks.items():
  if q[1]<=2 and not 3<=q[2]<=28:continue
  p=tuple(R.translated(q,r));ss=R.rotate(st,r['turn']);assert city.blocks.get(p)==ss,('architecture overwritten',m.id,p,ss,city.blocks.get(p))
spec={'case_id':'Qilou03','run':RUN,'mainline':'HAF 0.4','seed':SEED,'scope':'28 authored buildings: 12 arcade houses + 16 urban-village buildings, connected open streets','coordinates':{'X':'east','Y':'up','Z':'south','front_of_local_samples':'south'},'spawn_local':[88,3,108],'size_xyz':[W,H,D],'buildings':records,'arcade_cells':[list(p)for p in sorted(public_arcade)],'lane_cells':[list(p)for p in sorted(lane)],'road_cells':[list(p)for p in sorted(road)],'roads':roads,'alleys':alleys,'court_bounds':[198,169,240,207],'court_approaches':[[204,3,192],[110,3,62],[99,3,154],[190,3,95]],'trees':trees,'status':{'game':'pending','aesthetic':'pending user review'},'variation_scope':'Fixed street topology, lots, heights and programmes. Seeded component-level potted plants, shutters/coping and tree crowns; no generic urban generator.'}
C.save(city,'Qilou03',spec,(W,H,D));(OUT/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2));(OUT/'placement_conflicts.json').write_text(json.dumps(overwrites))
print(json.dumps({'run':RUN,'buildings':len(records),'corners':6,'blocks':len(city.blocks),'trees':len(trees),'sha256':spec['source_nbt_sha256']},ensure_ascii=False))
