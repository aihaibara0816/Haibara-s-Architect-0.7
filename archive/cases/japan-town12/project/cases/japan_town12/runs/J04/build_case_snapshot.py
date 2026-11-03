"""Original 12-building Japanese road town. Case adapter, not a generic style engine."""
from pathlib import Path
import sys,json,math,random,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump
from detail_lab import states
from vendor.voxel_core import parse_state,state
M=states.make
RUN=sys.argv[1] if len(sys.argv)>1 else 'J01'
SEED=2026102912; W,D,H=176,160,48
def rng(key):return random.Random(int.from_bytes(hashlib.sha256(f'{SEED}:{key}'.encode()).digest()[:8],'big'))
b=Builder((W,H,D),SEED);B=b.s.blocks
# Coordinates are authored design values, not measurements from reference videos.
rows=[
 ('H01','庭木之家','home',16,42,18,16,4,'S',2,'gable','white_concrete','gray',28),
 ('H02','坡上赤瓦宅','home',42,13,16,19,6,'E',2,'gable','smooth_sandstone','red',39),
 ('H03','蓝窗之家','home',85,13,19,17,7,'W',2,'gable','white_concrete','gray',12),
 ('H04','旧木庭院宅','home',119,19,20,18,6,'S',2,'hip','smooth_sandstone','gray',46),
 ('H05','街尾青瓦宅','home',139,96,18,20,4,'W',2,'gable','white_concrete','blue',16),
 ('H06','南侧阳台宅','home',125,132,19,17,4,'N',2,'gable','light_gray_concrete','gray',22),
 ('H07','转角小宅','home',77,121,17,21,4,'E',2,'gable','white_concrete','red',9),
 ('S01','日和杂货','grocer',25,100,21,16,4,'N',2,'gable','smooth_sandstone','gray',37),
 ('S02','小麦面包咖啡','cafe',64,97,19,16,4,'N',2,'gable','white_concrete','gray',24),
 ('P01','青叶诊所','clinic',132,47,24,16,4,'S',1,'flat','white_concrete','gray',8),
 ('P02','日和社区会馆','community',17,129,26,19,4,'N',1,'hip','smooth_sandstone','gray',31),
 ('P03','街角交番','koban',84,47,13,14,4,'S',1,'flat','white_concrete','gray',18),
]
buildings=[dict(zip(['id','name','use','x','z','w','d','g','face','floors','roof','wall','roof_color','age'],v)) for v in rows]
roads=[dict(id='main',path=[[0,86],[64,86],[96,73],[176,73]],width=9),dict(id='north',path=[[66,86],[66,0]],width=6),dict(id='south',path=[[108,73],[108,160]],width=6)]
zz,xx=np.mgrid[0:D,0:W]
road=np.zeros((D,W),bool);walk=np.zeros_like(road);reserved=np.zeros_like(road)
def line_mask(path,width):
 im=Image.new('1',(W,D));ImageDraw.Draw(im).line([tuple(v) for v in path],fill=1,width=width);return np.array(im)
for r in roads:
 road|=line_mask(r['path'],r['width']);walk|=line_mask(r['path'],r['width']+6)
height=np.full((D,W),4,int)
# Gentle north hillside, bounded terraces and flat public frontage.
for z in range(D):
 for x in range(W):
  if z<42:height[z,x]=4+min(3,max(0,(41-z)//10))
  if x<10 or x>166:height[z,x]+=min(2,abs(x-88)//80)
height[walk]=4
for h in buildings:
 x,z,w,d,g=[h[k] for k in ['x','z','w','d','g']]
 height[max(0,z-3):z+d+3,max(0,x-3):x+w+3]=g
 reserved[max(0,z-5):z+d+5,max(0,x-5):x+w+5]=True
print('terrain / roads',flush=True)
for z in range(D):
 for x in range(W):
  g=int(height[z,x]);b.box((x,0,z),(x+1,g,z+1),'dirt','site.terrain');b.put(x,g,z,'grass_block','site.surface')
for z,x in zip(*np.where(walk)):
 b.put(int(x),4,int(z),'smooth_stone','street.sidewalk')
for z,x in zip(*np.where(road)):
 b.put(int(x),4,int(z),'gray_concrete','street.asphalt')
# White edge lines follow the main bend; no random road markings.
for dz in [-3,3]:
 for (ax,az),(bx,bz) in zip(roads[0]['path'],roads[0]['path'][1:]):
  for t in np.linspace(0,1,max(abs(bx-ax),abs(bz-az))+1):
   x,z=round(ax+(bx-ax)*t),round(az+(bz-az)*t)+dz
   if 0<=x<W and 0<=z<D and road[z,x] and abs(x-66)>5 and abs(x-108)>5:b.put(x,4,z,'white_concrete','street.edge_line')
for x in range(3,173):
 if x%9<4 and abs(x-66)>6 and abs(x-108)>6:
  z=86 if x<64 else round(86-(x-64)*13/32) if x<96 else 73
  b.put(x,4,z,'white_concrete','street.center_dash')
for x,z0 in [(55,82),(119,69)]:
 for dx in [0,2,4]:b.box((x+dx,4,z0),(x+dx+1,5,z0+9),'white_concrete','street.crossing')
# Linear drain, covered by safe crossings where paths will cross it.
for z in range(91,153):
 b.box((115,2,z),(119,5,z+1),'stone_bricks','drain.lining')
 b.put(116,3,z,'water','drain.water');b.put(117,3,z,'water','drain.water')
 b.put(116,4,z,'air','drain.open');b.put(117,4,z,'air','drain.open')
for z in [101,139]:b.box((114,4,z-2),(120,5,z+3),'smooth_stone','drain.bridge')
entrances=[];stairs=[];zones=[];details=[]
def world(h,u,y,v):
 x,z,w,d=h['x'],h['z'],h['w'],h['d'];f=h['face']
 return (x+u,y,z+d-1-v) if f=='S' else (x+w-1-u,y,z+v) if f=='N' else (x+w-1-v,y,z+d-1-u) if f=='E' else (x+v,y,z+u)
def rotated(mat,h):
 st=M(mat) if not mat.startswith('minecraft:') else mat
 turns={'S':0,'W':1,'N':2,'E':3}[h['face']]
 for _ in range(turns):st=states.rotate_state(st)
 return st
def P(h,u,y,v,mat,part,empty=False):
 return b.put(*world(h,u,y,v),rotated(mat,h),h['id']+'.'+part,empty)
def box(h,u0,u1,y0,y1,v0,v1,mat,part):
 for u in range(u0,u1):
  for y in range(y0,y1):
   for v in range(v0,v1):P(h,u,y,v,mat,part)
def window(h,u0,u1,y,v,face='front'):
 for u in range(u0,u1):
  for yy in [y,y+1]:
   if face=='front':P(h,u,yy,v,'light_blue_stained_glass_pane','window')
   else:P(h,v,yy,u,'light_blue_stained_glass_pane','window')
 if face=='front':
  for u in range(u0-1,u1+1):P(h,u,y-1,v-1,M('dark_oak_slab',type='top'),'sill')
 b.windows.append(dict(id=h['id']+f'.window.{len(b.windows)}',anchor=list(world(h,u0,y,v)),size=[u1-u0,2]))
def stair(h,u,v,g,steps=7):
 for i in range(steps):
  for du in [0,1]:
   for yy in range(g+i+2,g+11):P(h,u+du,yy,v+i,'air','stairs.clearance')
   P(h,u+du,g+i+1,v+i,M('oak_stairs',facing='north'),'stairs')
   for yy in range(g+1,g+i+1):P(h,u+du,yy,v+i,'oak_planks','stairs.support')
   stairs.append(list(world(h,u+du,g+i+2,v+i)))
def furniture(h,w,d,g,level):
 use=h['use'];owner=h['id']; cy=g+1
 # Center aisle and left stair lane remain clear; furniture sits in bounded groups.
 if use=='home':
  if level==0:
   box(h,w-5,w-2,cy,cy+1,3,4,'oak_planks','kitchen.counter');P(h,w-3,cy+1,3,'iron_trapdoor','kitchen.hob')
   box(h,5,8,cy,cy+1,d-5,d-4,'oak_slab','table');P(h,5,cy,d-3,M('oak_stairs',facing='south'),'chair')
   box(h,w-5,w-2,cy,cy+1,d-3,d-2,'white_concrete','sofa')
  else:
   box(h,w-5,w-2,cy,cy+1,d-5,d-2,'white_concrete','bed.decorative');box(h,w-5,w-2,cy,cy+1,d-3,d-2,'blue_concrete','bed.cover')
   box(h,5,8,cy,cy+2,d-2,d-1,'bookshelf','bedroom.shelf');P(h,w-3,cy,3,'oak_planks','desk')
 elif use=='grocer':
  if level==0:
   for v in [5,d-4]:box(h,6,w-3,cy,cy+2,v,v+1,'bookshelf','shelves.decorative')
   box(h,w-5,w-2,cy,cy+1,2,3,'dark_oak_planks','checkout');P(h,w-3,cy+1,2,'black_concrete','till')
  else:
   box(h,5,w-3,cy,cy+1,d-3,d-2,'oak_planks','stock.storage');P(h,w-4,cy,3,'oak_planks','stock.desk')
 elif use=='cafe':
  box(h,w-4,w-2,cy,cy+1,3,d-3,'dark_oak_planks','counter' if level==0 else 'reading.bar')
  for u,v in [(6,5),(7,d-4)]:
   P(h,u,cy,v,'oak_slab','table');P(h,u+1,cy,v,M('oak_stairs',facing='west'),'seat')
  if level==1:box(h,5,w-4,cy,cy+2,d-2,d-1,'bookshelf','reading.shelves')
 elif use=='clinic':
  box(h,w-6,w-2,cy,cy+1,3,4,'white_concrete','reception');box(h,2,6,cy,cy+1,3,4,'oak_stairs','waiting')
  for u in [4,12,18]:box(h,u,u+2,cy,cy+1,d-5,d-2,'white_concrete','exam.bed')
  box(h,8,9,cy,cy+3,d-6,d-1,'light_blue_stained_glass_pane','exam.screen')
 elif use=='community':
  box(h,2,w-2,cy,cy+2,d-2,d-1,'bookshelf','community.library')
  for u in [5,10,15,20]:
   P(h,u,cy,7,'oak_slab','activity.table');P(h,u,cy,9,M('oak_stairs',facing='north'),'activity.chair')
  box(h,2,5,cy,cy+1,3,4,'dark_oak_planks','welcome')
 elif use=='koban':
  box(h,w-5,w-2,cy,cy+1,4,5,'oak_planks','desk');P(h,w-3,cy+1,4,'black_concrete','screen')
  box(h,2,4,cy,cy+2,d-3,d-2,'bookshelf','records');P(h,3,cy,3,M('oak_stairs',facing='north'),'visitor.seat')

print('12 distinct buildings / interiors',flush=True)
for h in buildings:
 w,d=(h['w'],h['d']) if h['face'] in ['S','N'] else (h['d'],h['w']);g=h['g'];f=h['floors'];rr=rng(h['id']+'.facade');door=w//2
 h.update(local_width=w,local_depth=d,door_u=door,maintenance=.86,material_seed=int(rr.random()*1e8),interior_level='L2; decorative furniture')
 box(h,-1,w+1,g-2,g, -1,d+1,'stone_bricks','foundation')
 for k in range(f):
  fy=g+7*k;box(h,0,w,fy,fy+1,0,d,'oak_planks','floor')
  box(h,0,w,fy+1,fy+6,0,d,h['wall'],'wall');box(h,1,w-1,fy+1,fy+6,1,d-1,'air','rooms')
  box(h,0,w,fy+6,fy+7,0,d,'white_concrete','ceiling')
  for u in [0,w-1]:
   for v in [0,d-1]:box(h,u,u+1,fy+1,fy+6,v,v+1,'dark_oak_planks','timber.corner')
  # Authored, unequal window groups; random channel chooses glazing accent only.
  groups=[(2,min(6,door-1)),(door+2,w-2)] if k==0 else ([(2,5),(8,11),(w-5,w-2)] if w>=18 else [(3,7),(w-5,w-2)])
  for a,bb in groups:
   if bb>a:window(h,a,bb,fy+2,0)
  window(h,3,w-3,fy+2,d-1)
  for side in [0,w-1]:
   for a in [3,d-6]:window(h,a,min(a+3,d-2),fy+2,side,'side')
  # Every occupied floor lit; shade variation doesn't turn functional rooms off.
  for u,v in [(w//3,d//3),(2*w//3,2*d//3),(3,3)]:P(h,u,fy+6,v,'sea_lantern' if h['use'] in ['clinic','koban'] else 'glowstone','light.ceiling')
  furniture(h,w,d,fy,k)
  zones.append(dict(id=h['id']+f'.F{k+1}',building=h['id'],use=h['use'],floor_block_y=fy,standing_y=fy+1,ceiling_y=fy+6,clear_height=5,lighting='all functional floors',bounds_xyz=[h['x']+1,fy+1,h['z']+1,h['x']+h['w']-1,fy+6,h['z']+h['d']-1]))
 if f==2:stair(h,2,3,g)
 # Entrance two leaves; door state is part of the actual NBT, not paint.
 for i in [0,1]:
  for half,dy in [('lower',1),('upper',2)]:P(h,door+i,g+dy,0,M('oak_door',facing='south',half=half,hinge='left' if i==0 else 'right'),'door')
 for v in [-1,-2]:box(h,door-1,door+3,g,g+1,v,v+1,'smooth_stone','porch')
 for i in [0,1]:entrances.append(dict(building=h['id'],inside=list(world(h,door+i,g+1,1)),door=list(world(h,door+i,g+1,0)),outside=list(world(h,door+i,g+1,-1))))
 # Clear central entrance corridor on both floors, avoiding side stairs/furniture.
 for k in range(f):box(h,door,door+2,g+7*k+1,g+7*k+4,1,min(5,d-1),'air','circulation')
 # Continuous mid eave is local, not wrapped identically on all four sides.
 if f==2:
  for u in range(-1,w+1):
   P(h,u,g+6,-1,'polished_deepslate_slab','lower_eave')
   if h['id'] in ['H01','H04','H05','H06']:P(h,u,g+7,-2,'polished_deepslate_slab','lower_eave')
 eave=g+7*f
 roofmat={'gray':'polished_deepslate','red':'bricks','blue':'oxidized_copper'}[h['roof_color']]
 if h['roof']=='flat':
  box(h,-1,w+1,eave,eave+1,-1,d+1,'smooth_stone','roof')
  for u in range(-1,w+1):
   for v in [-1,d]:P(h,u,eave+1,v,'smooth_stone_slab','parapet')
  box(h,w-6,w-3,eave+1,eave+2,d-5,d-3,'iron_block','roof.ac');box(h,w-6,w-3,eave+2,eave+3,d-5,d-3,'iron_trapdoor','roof.ac_grille')
 else:
  ridge_axis='u' if h['id'] not in ['H02','H05','H07'] else 'v';h['ridge_axis']=ridge_axis
  for u in range(-2,w+2):
   for v in range(-2,d+2):
    a=min(v+2,d+1-v) if ridge_axis=='u' else min(u+2,w+1-u)
    if h['roof']=='hip':a=min(a,u+2,w+1-u,v+2,d+1-v)
    y=eave+max(0,a//2)
    P(h,u,y,v,roofmat,'roof.tile')
    if a%2==0 and roofmat=='polished_deepslate':P(h,u,y+1,v,'polished_deepslate_slab','roof.tile_half')
    if 0<=u<w and 0<=v<d and (u in [0,w-1] or v in [0,d-1]):
     for yy in range(eave,y):P(h,u,yy,v,h['wall'],'gable_wall')
  # Fine eave lip, wider than the plaster walls.
  for u in range(-2,w+2):
   for v in [-2,d+1]:P(h,u,eave,v,M('dark_oak_slab',type='top'),'fascia')
 # Case-specific facades and supported balconies break the repeated shell.
 if h['id'] in ['H02','H04','S01']:
  for u in range(1,w-1):P(h,u,g+1,0,'dark_oak_planks','lower_siding')
  for u in range(2,w-1,3):
   for yy in [g+9,g+10]:P(h,u,yy,-1,M('dark_oak_trapdoor',facing='south',open='true'),'upper.shutter')
 if h['id'] in ['H01','H05','H06']:
  for u in range(1,w//2):
   for v in [-3,-2,-1]:P(h,u,g+7,v,'oak_planks','balcony.floor')
   P(h,u,g+8,-3,'iron_bars','balcony.rail')
  for u in [1,w//2-1]:
   for v in [-2,-1]:P(h,u,g+8,v,'iron_bars','balcony.side')
   for yy in range(g+1,g+7):P(h,u,yy,-3,'dark_oak_planks','balcony.support')
  if h['id']=='H06':
   for u in [3,4,6]:P(h,u,g+10,-2,'white_concrete','balcony.laundry')
 if h['id']=='H03':
  for u in range(w-5,w-1):
   for yy in range(g+1,g+6):P(h,u,yy,0,'light_gray_concrete','accent.panel')
  window(h,w-4,w-2,g+2,0)
 # Air-con and meter are supported, on service side not every frontage.
 box(h,w,w+1,g+2,g+3,d-5,d-3,'iron_block','service.ac');P(h,w,g+3,d-4,'iron_trapdoor','service.ac_grille')
 for yy in range(g+1,eave):P(h,-1,yy,d-1,M('chain',axis='y'),'service.downpipe')
 # Shops have distinct street-facing identities.
 if h['use'] in ['grocer','cafe']:
  col='green_concrete' if h['use']=='grocer' else 'orange_concrete'
  for u in range(1,w-1):
   for v in [-3,-2,-1]:P(h,u,g+4,v,col if (u//2)%2==0 else 'white_concrete','awning')
  for u in [1,w-2]:box(h,u,u+1,g+1,g+4,-3,-2,'dark_oak_planks','awning.post')
  for u in range(2,door-1):P(h,u,g+1,-2,'oak_planks','street.display');P(h,u,g+2,-2,'red_terracotta' if h['use']=='grocer' else 'smooth_sandstone','street.goods')
 elif h['use']=='clinic':
  for du,dy in [(0,0),(1,0),(2,0),(1,1),(1,-1)]:P(h,w-5+du,g+4+dy,-1,'green_concrete','clinic.cross')
 elif h['use']=='koban':
  box(h,1,w-1,g+4,g+5,-1,0,'blue_concrete','koban.band');P(h,door,g+6,-1,'redstone_torch','koban.red_light')
 # Entry light supported below small canopy.
 P(h,door+3,g+4,-1,'dark_oak_slab','entry.canopy');P(h,door+3,g+3,-1,M('lantern',hanging='true'),'light.entry')

# Door-to-street routes adapt to setbacks and stepped plots. Three cells wide.
routes=[]
for h in buildings:
 u=h['door_u'];sx,_,sz=world(h,u,h['g'], -3)
 choices=np.argwhere(walk & ~road);j=np.argmin((choices[:,1]-sx)**2+(choices[:,0]-sz)**2);tz,tx=map(int,choices[j]);steps=max(abs(tx-sx),abs(tz-sz),1)
 path=[]
 for i in range(steps+1):
  t=i/steps;x=round(sx+(tx-sx)*t);z=round(sz+(tz-sz)*t);y=round(h['g']+(4-h['g'])*t)
  for a in [-1,0,1]:
   dx,dz=(a,0) if abs(tz-sz)>=abs(tx-sx) else (0,a)
   if 0<=x+dx<W and 0<=z+dz<D:
    for yy in range(0,y):b.put(x+dx,yy,z+dz,'stone_bricks','path.support')
    b.put(x+dx,y,z+dz,'smooth_stone','path.surface')
    for yy in range(y+1,max(h['g']+2,y+4)):b.put(x+dx,yy,z+dz,'air','path.clear')
    reserved[z+dz,x+dx]=True
  path.append([x,y+1,z])
 routes.append(dict(building=h['id'],width=3,path=path))

print('gardens / public street',flush=True)
def tree(x,z,h,r,key,cherry=False):
 rr=rng('tree.'+key);y=int(height[z,x])+1
 b.box((x,y,z),(x+1,y+h,z+1),'oak_log','trees.'+key+'.trunk')
 for dx,dz in [(-2,0),(2,1),(0,-2)]:b.line((x,y+h-3,z),(x+dx,y+h-1,z+dz),'oak_log','trees.'+key+'.branch')
 for yy in range(y+h-4,y+h+3):
  for xx0 in range(x-r,x+r+1):
   for zz0 in range(z-r,z+r+1):
    if 0<=xx0<W and 0<=zz0<D and 0<=yy<H and ((xx0-x)/r)**2+((zz0-z)/r)**2+((yy-y-h+1)/3.5)**2 < 1+rr.uniform(-.13,.13):
     if not road[zz0,xx0]:b.put(xx0,yy,zz0,'cherry_leaves' if cherry else 'oak_leaves','trees.'+key+'.leaves',empty=True)
treerecs=[]
for x,z,h,r,key,ch in [(20,14,9,5,'park',True),(8,29,8,4,'park2',False),(32,23,7,4,'park3',False),(12,64,8,4,'H01',False),(41,64,7,3,'H01b',False),(29,41,7,3,'H01c',False),(44,8,8,4,'H02',False),(103,9,9,4,'H03',False),(129,9,10,5,'H04',False),(159,24,10,5,'H04b',False),(153,39,7,3,'clinic',False),(127,93,8,4,'pocket',True),(152,122,8,4,'H05',False),(160,142,9,4,'H06',False),(89,153,9,5,'H07',False),(55,132,9,4,'hall',True),(9,117,7,3,'hall2',False),(24,93,6,3,'shop',False)]:
 tree(x,z,h,r,key,ch);treerecs.append(dict(x=x,z=z,height=h,radius=r,id=key,cherry=ch))
# Irregular edge planting; exclude built plots, pavement and frontage sight lines.
rr=rng('planting.edge');chosen=[]
for i in range(120):
 x,z=rr.randrange(4,W-4),rr.randrange(4,D-4)
 if min(x,W-x,z,D-z)>13 or reserved[z,x] or walk[z,x] or any((x-a)**2+(z-c)**2<70 for a,c in chosen):continue
 tree(x,z,rr.randint(6,10),rr.randint(3,5),'edge'+str(i));chosen.append((x,z));treerecs.append(dict(x=x,z=z,id='edge'+str(i)))
# Domestic gardens: variable hedges, low walls and flower groups, leaving gate gaps.
for h in buildings:
 if h['use']!='home':continue
 w,d=h['local_width'],h['local_depth'];g=h['g'];door=h['door_u'];rr=rng(h['id']+'.garden')
 for u in range(-2,w+2):
  if door-2<=u<=door+3:continue
  P(h,u,g,-5,'stone_bricks','garden.wall_base');P(h,u,g+1,-5,'oak_leaves' if rr.random()<.70 else 'stone_brick_slab','garden.hedge')
 for u in [1,w-3]:
  for v in [-3,-4]:P(h,u,g,v,'dirt','garden.soil');P(h,u,g+1,v,rr.choice(['poppy','oxeye_daisy']),'garden.flower',empty=True)
 # Mail box and front boundary light.
 P(h,door-3,g+1,-4,'dark_oak_planks','mailbox.post');P(h,door-3,g+2,-4,'iron_block','mailbox')
 P(h,door+4,g+1,-4,'lantern','light.gate')
# Authored lot boundaries and small domestic service courts, with independent garden seeds.
for h in buildings:
 if h['use']!='home':continue
 w,d,g=h['local_width'],h['local_depth'],h['g'];rr=rng(h['id']+'.courtyard')
 # Rear / left boundaries define individual parcels without closing the entrance.
 for u in range(-3,w+3):
  P(h,u,g,d+3,'stone_bricks','yard.boundary_base')
  P(h,u,g+1,d+3,'oak_leaves' if (u+3)%5<3 else 'stone_brick_slab','yard.boundary')
 for v in range(-3,d+3):
  P(h,-3,g,v,'stone_bricks','yard.side_base')
  if v%7<5:P(h,-3,g+1,v,'oak_leaves','yard.side_hedge')
 # Terraces at the rear and stepping strips at the side; grass remains in pockets.
 for u in range(2,w-2):
  for v in range(d,d+3):P(h,u,g,v,'oak_slab' if h['id'] in ['H01','H04'] else 'gravel','yard.terrace')
 for v in range(1,d-1):
  P(h,w+1,g,v,'smooth_stone','yard.service_path')
  if v%4<2:P(h,w+2,g,v,'gravel','yard.service_gravel')
 for u in [2,w-4]:
  P(h,u,g,d+2,'dirt','yard.planter_base');P(h,u,g+1,d+2,'oak_leaves','yard.shrub')
 if h['id'] in ['H02','H04','H07']:
  for u in range(w-6,w-2):
   for v in [-6,-7]:
    P(h,u,g,v,'farmland','garden.vegetable_soil');P(h,u,g+1,v,M('carrots',age=rr.choice([4,5,7])),'garden.vegetable')
# Widen the two shop forecourts to make a small commercial cluster.
for a,c,u,v in [(23,91,49,99),(61,89,85,96)]:
 for z in range(c,v):
  for x in range(a,u):
   if not road[z,x] and not any(h['x']<=x<h['x']+h['w'] and h['z']<=z<h['z']+h['d'] for h in buildings):
    b.put(x,4,z,'smooth_stone','shops.forecourt')
# Public pocket green has defined low walls, flower groups and a clear street connection.
for x in range(120,133):
 for z in [89,115]:
  b.put(x,4,z,'stone_bricks','pocket.border');b.put(x,5,z,'oak_leaves' if x%4<3 else 'stone_brick_slab','pocket.hedge')
# Public park loop, green center and seating. No obligation to fill its gathering lawn.
parkpath=[[10,9],[29,8],[39,16],[36,30],[21,34],[10,25],[10,9]]
pm=line_mask(parkpath,3)
for z,x in zip(*np.where(pm)):
 y=int(height[z,x]);b.put(int(x),y,int(z),'dirt_path','park.loop')
for x,z in [(14,24),(29,30),(126,113),(51,127)]:
 y=int(height[z,x])+1
 for dx in range(4):b.put(x+dx,y,z,M('oak_stairs',facing='north'),'public.bench')
# Bus shelter north side of the main street, signs/bench/back pane, boarding clear.
for x in [43,57]:b.box((x,5,76),(x+1,9,77),'iron_bars','bus.post')
b.box((42,9,75),(59,10,79),'green_concrete','bus.roof')
b.box((44,6,76),(56,8,77),'light_blue_stained_glass_pane','bus.back')
for x in range(46,54):b.put(x,5,77,M('oak_stairs',facing='north'),'bus.bench')
b.box((59,5,76),(60,9,77),'iron_bars','bus.stop.post');b.box((58,8,76),(61,10,77),'white_concrete','bus.stop.board');b.put(59,9,75,'blue_concrete','bus.stop.symbol')
b.put(47,8,77,'end_rod','bus.light');b.put(54,8,77,'end_rod','bus.light')
# Community notice board and vending machines as explicit decorative props.
for x,z in [(12,128),(80,64)]:
 b.box((x,5,z),(x+1,8,z+1),'dark_oak_planks','notice.post');b.box((x+4,5,z),(x+5,8,z+1),'dark_oak_planks','notice.post');b.box((x,7,z),(x+5,9,z+1),'oak_planks','notice.board');b.box((x-1,9,z),(x+6,10,z+2),'dark_oak_slab','notice.cap')
for x,z,col in [(49,100,'red_concrete'),(88,96,'white_concrete')]:
 b.box((x,5,z),(x+2,8,z+1),col,'vending.body');b.put(x,7,z-1,'light_blue_stained_glass_pane','vending.panel');b.put(x+1,6,z-1,'black_concrete','vending.slot')
# Utility wires have stable span endpoints and a sag; not scattered decorative poles.
polepoints=[(11,79),(40,79),(76,72),(113,65),(160,65)]
for x,z in polepoints:
 b.box((x,5,z),(x+1,21,z+1),'dark_oak_planks','utility.pole');b.box((x-1,18,z),(x+2,19,z+1),'iron_bars','utility.arm')
 b.put(x,17,z+1,'glowstone','street.light');b.put(x,18,z+1,'polished_deepslate_slab','street.light.cap')
for (ax,az),(cx,cz) in zip(polepoints,polepoints[1:]):
 for dx in [-1,1]:
  for t in np.linspace(0,1,max(abs(cx-ax),abs(cz-az))*2):
   b.put(round(ax+(cx-ax)*t)+dx,round(19-2*math.sin(math.pi*t)),round(az+(cz-az)*t),M('chain',axis='x'),'utility.wire')
# Warm, sparse lane lamps; all houses' interiors remain lit.
for x,z in [(71,17),(71,49),(113,119),(102,146),(50,119),(119,88)]:
 b.box((x,5,z),(x+1,11,z+1),'iron_bars','street.lamp.post');b.put(x,11,z,'lantern','street.lamp')
# Parking bays and two compact decorative cars at the clinic/community uses.
for a,c in [(139,39),(42,120)]:
 b.box((a-2,4,c-2),(a+14,5,c+5),'gray_concrete','parking')
 for x in [a-1,a+6,a+13]:b.box((x,4,c-2),(x+1,5,c+4),'white_concrete','parking.line')
 for u,col in [(a,'white_concrete'),(a+7,'blue_concrete')]:
  b.box((u,5,c),(u+4,6,c+3),col,'car.body');b.box((u+1,6,c),(u+3,7,c+3),'light_blue_stained_glass','car.glass');b.box((u+1,7,c),(u+3,8,c+3),col,'car.roof')
  for x in [u,u+3]:
   for z in [c,c+2]:b.put(x,5,z,'black_concrete','car.wheel')
# Final protected route pass: details cannot occupy full-width paths or door approaches.
for h in buildings:
 for v in [-1,-2]:
  box(h,h['door_u']-1,h['door_u']+3,h['g']+1,h['g']+3,v,v+1,'air','protected.porch')
for r in routes:
 path=r['path'];dx=abs(path[-1][0]-path[0][0]);dz=abs(path[-1][2]-path[0][2])
 for x,y,z in path:
  for a in [-1,0,1]:
   qx=x+(a if dz>=dx else 0);qz=z+(a if dx>dz else 0)
   for yy in range(y,y+3):b.put(qx,yy,qz,'air','protected.path')
# Raised garden boundaries and terraces receive continuous support down to terrain.
for q,st in list(B.items()):
 own=b.s.owners[q]
 if any(tag in own for tag in ['.garden.wall_base','.yard.boundary_base','.yard.side_base','.yard.terrace','.yard.service_path','.yard.service_gravel','.garden.vegetable_soil','.garden.soil']):
  x,y,z=q
  for yy in range(y):
   if (x,yy,z) not in B:b.put(x,yy,z,'dirt',own+'.support')
for (x,y,z),st in list(B.items()):
 if states.family(st) in ['flower','crop']:
  if (x,y-1,z) not in B:
   for yy in range(y):
    if (x,yy,z) not in B:b.put(x,yy,z,'dirt','plant.support')
sp=dict(buildings=buildings,rooms=zones,roads=roads,entrances=entrances,connections=routes,stair_clearance_samples=stairs,trees=treerecs,site=dict(size_xyz=[W,H,D],base=4,north_terraces=[4,6,7]),protected_regions=['street','entries','stairs','bus.boarding'])
spec=dict(schema_version='japan-town12-1.0',design_brief=dict(case_id='japan_town12',version=RUN.replace('_replay',''),route='original',seed=SEED,units='integer Minecraft blocks; conceptual 1 block ~ 1 m',coordinates='Y up; east +X; north -Z',hard_constraints=['12 buildings','7 homes + 2 shops + 3 civic','asphalt streets','bus stop','low-rise active rooms lit'],assumptions=['Original anime-inspired road town, not reconstruction','Decorative furniture/vehicles; game interactions pending'],source_report='JapanTown01.html; only recorded sampled video moments'),spatial_spec=sp,facade_spec=dict(primary='plaster and restrained timber; mixed pitched and flat roofs',variation='stable per-building namespaces; no independent pixel noise',seed_channels=['facade','garden','planting.edge','tree'],roof_palette=['gray tile','limited red tile','one blue-green roof'],lighting='functional floors all lit; ceiling-recessed lights; entry lanterns',age_is_design_assumption=True))
dump(C/'input/design.json',spec)
out=save_run(C,RUN,spec,b,__file__,extra={'adapter':'japan_town12/1.0','building_count':12,'not_model_training':True,'origin':'original design informed by JapanTown01 research','light_policy':'all functional rooms; preview light approximation'})
dump(out/'site_records.json',sp)
print('DONE',out,flush=True)
