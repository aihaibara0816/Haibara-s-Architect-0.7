"""Freedom-informed original old town. Fixed layout; seeded details. J05 retained."""
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
RUN=sys.argv[1] if len(sys.argv)>1 else 'J06'
SEED=2026102912;W,D,H=160,128,48
rng=lambda key:random.Random(int.from_bytes(hashlib.sha256(f'{SEED}:{key}'.encode()).digest()[:8],'big'))
b=Builder((W,H,D),SEED);B=b.s.blocks
rows=[
 ('H01','格子町屋','home',12,40,15,21,4,'S',2,'gable','smooth_sandstone',28),
 ('H02','木匠之家','home',32,39,17,22,5,'S',2,'gable','spruce_planks',39),
 ('S01','紫帘和菓子铺','grocer',54,35,18,22,4,'S',2,'gable','oak_planks',37),
 ('H03','白壁旧宅','home',77,39,14,18,5,'S',2,'gable','white_concrete',42),
 ('P03','木造交番','koban',96,45,11,12,4,'S',1,'gable','smooth_sandstone',38),
 ('P01','青叶老诊所','clinic',113,35,24,22,4,'S',1,'hip','smooth_sandstone',46),
 ('S02','松影茶屋','cafe',15,78,23,22,4,'N',2,'gable','smooth_sandstone',44),
 ('H04','转角切妻宅','home',43,78,16,21,4,'N',2,'gable','spruce_planks',32),
 ('P02','日和会所','community',65,73,27,27,4,'N',1,'hip','smooth_sandstone',55),
 ('H05','退台木宅','home',97,74,15,23,4,'N',2,'gable','oak_planks',35),
 ('H06','平屋茶庭','home',117,79,17,18,4,'N',1,'hip','smooth_sandstone',49),
 ('H07','巷尾庭院宅','home',126,104,19,17,5,'E',2,'gable','spruce_planks',48),
]
buildings=[dict(zip(['id','name','use','x','z','w','d','g','face','floors','roof','wall','age'],r)) for r in rows]
roads=[dict(id='main',path=[[0,68],[47,68],[79,64],[121,64],[160,72]],width=7),dict(id='east_lane',path=[[150,70],[150,128]],width=5)]
def line_mask(path,width):
 im=Image.new('1',(W,D));ImageDraw.Draw(im).line([tuple(v) for v in path],fill=1,width=width);return np.array(im)
road=np.zeros((D,W),bool);walk=np.zeros_like(road);reserved=np.zeros_like(road)
for r in roads:road|=line_mask(r['path'],r['width']);walk|=line_mask(r['path'],r['width']+4)
height=np.full((D,W),4,int)
for z in range(D):
 for x in range(W):
  if z<26:height[z,x]=4+min(3,(26-z)//8)
for h in buildings:
 x,z,w,d,g=[h[k] for k in ['x','z','w','d','g']]
 height[max(0,z-3):min(D,z+d+4),max(0,x-3):min(W,x+w+4)]=g
 reserved[max(0,z-5):min(D,z+d+6),max(0,x-5):min(W,x+w+6)]=True
height[walk]=4
print('old street terrain',flush=True)
for z in range(D):
 for x in range(W):
  g=int(height[z,x]);b.box((x,0,z),(x+1,g,z+1),'dirt','site.terrain');b.put(x,g,z,'grass_block','site.surface')
for z,x in zip(*np.where(walk)):b.put(int(x),4,int(z),'stone_bricks','street.edge')
for z,x in zip(*np.where(road)):b.put(int(x),4,int(z),'gray_concrete','street.asphalt')
# A small crossing near public services; the main street has no center dash.
for x in [102,104,106]:b.box((x,4,62),(x+1,5,67),'white_concrete','street.crossing')
# Back lane, lined drain and bridged entrances are connected landscape, not loose props.
for x in range(8,121):
 for z in range(108,111):b.put(x,int(height[z,x]),z,'gravel','rear.lane')
for z in range(82,124):
 b.box((154,2,z),(158,5,z+1),'stone_bricks','drain.lining')
 for x in [155,156]:b.put(x,3,z,'water','drain.water');b.put(x,4,z,'air','drain.open')
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
   if face=='front':P(h,u,yy,v,'white_stained_glass_pane','window')
   else:P(h,v,yy,u,'white_stained_glass_pane','window')
 if face=='front':
  for u in range(u0-1,u1+1):P(h,u,y-1,v-1,M('dark_oak_slab',type='top'),'sill')
 b.windows.append(dict(id=h['id']+f'.window.{len(b.windows)}',anchor=list(world(h,u0,y,v)),size=[u1-u0,2]))
def stair(h,u,v,g,steps=6):
 for i in range(steps):
  for du in [0,1]:
   for yy in range(g+i+2,g+10):P(h,u+du,yy,v+i,'air','stairs.clearance')
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
  box(h,8,9,cy,cy+3,d-6,d-1,'white_stained_glass_pane','exam.screen')
 elif use=='community':
  box(h,2,w-2,cy,cy+2,d-2,d-1,'bookshelf','community.library')
  for u in [5,10,15,20]:
   P(h,u,cy,7,'oak_slab','activity.table');P(h,u,cy,9,M('oak_stairs',facing='north'),'activity.chair')
  box(h,2,5,cy,cy+1,3,4,'dark_oak_planks','welcome')
 elif use=='koban':
  box(h,w-5,w-2,cy,cy+1,4,5,'oak_planks','desk');P(h,w-3,cy+1,4,'black_concrete','screen')
  box(h,2,4,cy,cy+2,d-3,d-2,'bookshelf','records');P(h,3,cy,3,M('oak_stairs',facing='north'),'visitor.seat')


def lattice(h,a,bb,y,v=0):
 for u in range(a,bb):
  for yy in [y,y+1]:
   P(h,u,yy,v,'white_stained_glass_pane','shoji.glass')
   P(h,u,yy,v-1,M('dark_oak_fence',east='true',west='true'),'wood.lattice')
 b.windows.append(dict(id=h['id']+f'.window.{len(b.windows)}',anchor=list(world(h,a,y,v)),size=[bb-a,2],type='wood lattice over pale glazing'))
def roof(h,u0,u1,v0,v1,eave,axis='u',hip=False):
 # Broad grey tiled 1:2 slope, built with true half slabs and stairs.
 for u in range(u0-2,u1+2):
  for v in range(v0-2,v1+2):
   c=min(v-v0+2,v1+1-v) if axis=='u' else min(u-u0+2,u1+1-u)
   if hip:c=min(c,u-u0+2,u1+1-u,v-v0+2,v1+1-v)
   y=eave+c//2
   fd=('north' if v<(v0+v1)/2 else 'south') if axis=='u' else ('east' if u<(u0+u1)/2 else 'west')
   P(h,u,y,v,'polished_deepslate_slab' if c%2==0 else M('polished_deepslate_stairs',facing=fd),'roof.tile')
   if u0<=u<u1 and v0<=v<v1 and (u in [u0,u1-1] or v in [v0,v1-1]):
    for yy in range(eave,y):P(h,u,yy,v,h['wall'],'gable.infill')
 # Eave timber face under the outermost course; ridge has a narrow cap.
 for u in range(u0-1,u1+1):
  for v in [v0-1,v1]:P(h,u,eave-1,v,M('dark_oak_slab',type='top'),'roof.soffit')
 ridge=(v0+v1-1)//2 if axis=='u' else (u0+u1-1)//2
 if not hip:
  for t in range((u0-2 if axis=='u' else v0-2),(u1+2 if axis=='u' else v1+2)):
   u,v=(t,ridge) if axis=='u' else (ridge,t)
   c=min(v-v0+2,v1+1-v) if axis=='u' else min(u-u0+2,u1+1-u)
   P(h,u,eave+c//2+1,v,'polished_deepslate_slab','roof.ridge')
def lower_eave(h,w,g):
 for u in range(-2,w+2):
  for v in [-3,-2,-1]:
   P(h,u,g+5+(v+3)//2,v,'polished_deepslate_slab' if v%2 else M('polished_deepslate_stairs',facing='north'),'shop.deep_eave')
  P(h,u,g+4,-2,M('dark_oak_slab',type='top'),'eave.timber')
 for u in [0,w-1]:
  P(h,u,g+4,-1,M('oak_stairs',facing='north',half='top'),'eave.bracket')
print('timber frames / tiled roofs / lattice',flush=True)
for h in buildings:
 w,d=(h['w'],h['d']) if h['face'] in ['S','N'] else (h['d'],h['w']);g=h['g'];f=h['floors'];door=4 if h['id']=='S01' else w//2
 rr=rng(h['id']+'.facade');timber=rr.choice(['stripped_oak_log','stripped_spruce_log'])
 h.update(local_width=w,local_depth=d,door_u=door,floor_step=6,roof_color='gray',maintenance=.78,interior_level='L2 initial decorative furnishing',timber=timber)
 upper_u1=w-5 if h['id'] in ['H04','H07'] else w
 upper_v0=2 if h['id']=='H05' else 0
 h.update(upper_local_bounds=[0,upper_v0,upper_u1,d])
 box(h,-1,w+1,g-2,g,-1,d+1,'stone_bricks','foundation')
 for k in range(f):
  fy=g+6*k;u1=w if k==0 else upper_u1;v0=0 if k==0 else upper_v0
  box(h,0,u1,fy,fy+1,v0,d,'spruce_planks','floor')
  box(h,0,u1,fy+1,fy+5,v0,d,h['wall'],'wall');box(h,1,u1-1,fy+1,fy+5,v0+1,d-1,'air','room')
  box(h,0,u1,fy+5,fy+6,v0,d,'dark_oak_planks','ceiling')
  # The visible structural bay rhythm determines window groups.
  bays=sorted(set([0,u1-1]+list(range(4,u1-1,4))))
  for u in bays:
   for v in [v0,d-1]:box(h,u,u+1,fy+1,fy+5,v,v+1,timber,'timber.post')
  for v in range(v0+4,d-1,4):
   for u in [0,u1-1]:box(h,u,u+1,fy+1,fy+5,v,v+1,timber,'timber.side')
  for v in [v0,d-1]:box(h,0,u1,fy+4,fy+5,v,v+1,M(timber,axis='x'),'timber.beam')
  for a,bb in zip(bays,bays[1:]):
   if k==0 and not (bb<=door or a>door+1):continue
   if bb-a>1:lattice(h,a+1,bb,fy+2,v0)
  for side in [0,u1-1]:
   for a in [3,d-6]:window(h,a,min(a+2,d-2),fy+2,side,'side')
  window(h,3,u1-3,fy+2,d-1)
  furniture(h,u1,d,fy,k)
  # Warm hanging lamps, held by solid ceiling and chain. Every functional floor lit.
  for u,v in [(u1//2,d//2),(u1-4,d-4),(3,d//2+2)]:
   P(h,u,fy+4,v,M('lantern',hanging='true'),'light.interior')
  corners=[world(h,1,fy+1,v0+1),world(h,u1-2,fy+5,d-2)]
  bounds=[min(q[0] for q in corners),fy+1,min(q[2] for q in corners),max(q[0] for q in corners)+1,fy+5,max(q[2] for q in corners)+1]
  zones.append(dict(id=h['id']+f'.F{k+1}',building=h['id'],use=h['use'],floor_block_y=fy,standing_y=fy+1,ceiling_y=fy+5,clear_height=4,lighting='supported hanging lanterns',bounds_xyz=bounds))
 if f==2:stair(h,2,3,g,6)
 for k in range(f):box(h,door,door+2,g+6*k+1,g+6*k+4,1,min(5,d-1),'air','circulation')
 for i in [0,1]:
  for half,dy in [('lower',1),('upper',2)]:P(h,door+i,g+dy,0,M('oak_door',facing='south',half=half,hinge='left' if i==0 else 'right'),'door')
  entrances.append(dict(building=h['id'],inside=list(world(h,door+i,g+1,1)),door=list(world(h,door+i,g+1,0)),outside=list(world(h,door+i,g+1,-1))))
 for v in [-1,-2]:box(h,door-1,door+3,g,g+1,v,v+1,'stone_bricks','entry.step')
 # Smaller upper volume and genuine low side wing on selected houses.
 if f==2 and upper_u1<w:roof(h,upper_u1,w,0,d,g+6,axis='v')
 if f==2 and upper_v0:roof(h,0,w,0,upper_v0+2,g+6,axis='u')
 axis='v' if h['id'] in ['H04','H07'] else 'u';h['ridge_axis']=axis
 roof(h,0,upper_u1 if f==2 else w,upper_v0 if f==2 else 0,d,g+6*f,axis,h['roof']=='hip')
 lower_eave(h,w,g)
 # Two lantern bands express the deep lower and upper eaves.
 for u in sorted(set([1,w-2,door+3])):
  if u<w:
   P(h,u,g+4,-1,M('lantern',hanging='true'),'light.eave')
 if f==2:
  for u in [1,upper_u1-2]:
   P(h,u,g+11,upper_v0-1,M('dark_oak_slab',type='top'),'light.support')
   P(h,u,g+10,upper_v0-1,M('lantern',hanging='true'),'light.upper_eave')
 # No front lawn: hard apron ends at the existing street edge.
 for u in range(-1,w+1):
  for v in [-1,-2,-3,-4]:
   x,y,z=world(h,u,g,v)
   if not road[z,x]:
    for yy in range(g):b.put(x,yy,z,'dirt',h['id']+'.apron.support')
    b.put(x,g,z,'gravel' if u in [-1,w] else 'stone_bricks',h['id']+'.apron')
 # Asymmetric working storefront and cloth below the timber lintel.
 if h['use'] in ['grocer','cafe']:
  cloth='purple_wall_banner' if h['use']=='grocer' else 'blue_wall_banner'
  if h['use']=='grocer':
   for u in range(8,w-2):
    for yy in [g+2,g+3]:P(h,u,yy,0,'air','shop.open_counter');P(h,u,yy,-1,'air','shop.open_counter')
    P(h,u,g+1,-1,'dark_oak_slab','shop.stall');P(h,u,g+2,-1,'smooth_sandstone_slab' if u%3 else 'red_terracotta','shop.goods')
  for u in range(door-1,min(w-2,door+4)):
   P(h,u,g+4,0,M(timber,axis='x'),'noren.rail');P(h,u,g+4,-1,M(cloth,facing='south'),'noren.cloth')
  P(h,w-2,g+3,-2,M('red_wall_banner',facing='south'),'shop.banner');P(h,w-2,g+3,-1,'dark_oak_planks','shop.sign_support')
 elif h['use']=='clinic':
  box(h,w-5,w-2,g+3,g+4,-1,0,'oak_planks','clinic.nameboard');P(h,w-4,g+3,-2,'white_wall_banner','clinic.cloth')
 elif h['use']=='koban':P(h,w-2,g+3,-1,'redstone_torch','koban.red_marker')
 elif h['use']=='community':
  for u in [door-2,door+3]:
   P(h,u,g+4,0,'dark_oak_planks','hall.banner_rail');P(h,u,g+4,-1,'blue_wall_banner','hall.cloth')
 # Shutters and pots repeat by bay, with variation at the building level.
 for u in [1,w-3]:
  if door-1<=u<=door+2:continue
  P(h,u,g+1,-2,'terracotta','plant.pot');P(h,u,g+2,-2,'azalea_leaves','plant.shrub')
 for v in range(2,d-2,5):P(h,-1,g+2,v,M('dark_oak_trapdoor',facing='west',open='true'),'shutter.side')
 # Defined rear plots, compact walled service courts.
 for u in range(-1,w+1):
  for v in [d,d+1,d+2]:P(h,u,g,v,'gravel' if v==d+2 else 'oak_slab','yard.terrace')
  P(h,u,g+1,d+3,'dark_oak_planks','yard.fence');P(h,u,g+2,d+3,'dark_oak_slab','yard.cap')
 for u in [2,w-4]:P(h,u,g+1,d+2,'oak_leaves','yard.shrub')

# Short connecting paths. Fixed entrances survive all random detail passes.
routes=[]
for h in buildings:
 sx,_,sz=world(h,h['door_u'],h['g'],-1);choices=np.argwhere(walk&~road)
 j=np.argmin((choices[:,1]-sx)**2+(choices[:,0]-sz)**2);tz,tx=map(int,choices[j]);n=max(abs(tx-sx),abs(tz-sz),1);path=[]
 for i in range(n+1):
  t=i/n;x=round(sx+(tx-sx)*t);z=round(sz+(tz-sz)*t);y=round(h['g']+(4-h['g'])*t)
  for a in [-1,0,1]:
   dx,dz=(a,0) if abs(tz-sz)>=abs(tx-sx) else (0,a)
   for yy in range(y):b.put(x+dx,yy,z+dz,'stone_bricks','path.support')
   b.put(x+dx,y,z+dz,'stone_bricks','path.surface');reserved[z+dz,x+dx]=True
   for yy in range(y+1,max(h['g']+3,y+4)):b.put(x+dx,yy,z+dz,'air','path.clear')
  path.append([x,y+1,z])
 routes.append(dict(building=h['id'],width=3,path=path))
print('rear gardens / bus / lanterns',flush=True)
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
# Cluster greenery behind the street frontage; no identical lawn in front of every home.
for x,z,hh,r,key,ch in [(12,17,8,4,'north1',False),(29,19,9,4,'north2',False),(52,19,8,4,'north3',False),(78,17,8,4,'north4',False),(101,20,8,4,'north5',False),(125,18,9,5,'north6',False),(143,27,8,4,'north7',False),(7,110,8,4,'south1',False),(22,117,8,4,'south2',False),(46,118,9,5,'south3',True),(71,117,8,4,'south4',False),(99,117,8,4,'south5',False),(115,116,7,3,'south6',False)]:
 tree(x,z,hh,r,key,ch);treerecs.append(dict(x=x,z=z,height=hh,radius=r,id=key,cherry=ch))
rr=rng('planting.edge')
for i in range(35):
 x,z=rr.randrange(4,W-4),rr.randrange(3,25)
 if reserved[z,x] or any((x-t['x'])**2+(z-t['z'])**2<65 for t in treerecs):continue
 hh=rr.randint(6,9);r=rr.randint(3,4);tree(x,z,hh,r,'edge'+str(i));treerecs.append(dict(x=x,z=z,height=hh,radius=r,id='edge'+str(i)))
# Pocket orchard and kitchen gardens are irregular groups in rear courts.
for ax,az,ww,dd in [(58,113,7,5),(83,115,8,6),(108,104,8,7),(8,27,7,5)]:
 rr=rng(f'patch.{ax}.{az}')
 for x in range(ax,ax+ww):
  for z in range(az,az+dd):
   y=int(height[z,x]);b.put(x,y,z,'farmland' if (x-ax)%3 else 'dirt_path','rear.garden')
   if (x-ax)%3:b.put(x,y+1,z,M('carrots',age=rr.choice([4,6,7])),'rear.crop')
# Wood and tile bus shelter: near the western approach, with unobstructed boarding.
for x in [4,12]:b.box((x,5,59),(x+1,9,60),'stripped_oak_log','bus.post')
for x in range(3,14):
 for z in range(57,62):b.put(x,9+min(z-57,61-z)//2,z,'polished_deepslate_slab','bus.tile')
for x in range(5,12):b.put(x,5,59,M('oak_stairs',facing='north'),'bus.bench')
for x in [6,10]:b.put(x,8,59,M('lantern',hanging='true'),'bus.light')
b.box((4,5,63),(5,9,64),'spruce_log','bus.stop.post');b.box((3,8,63),(6,10,64),'oak_planks','bus.stop.board')
# A community well, wash-basin court and notice board beside the rear lane.
for x in range(67,72):
 for z in range(103,108):
  b.put(x,4,z,'stone_bricks','well.base')
  b.put(x,5,z,'stone_bricks' if x in [67,71] or z in [103,107] else 'water','well.basin')
for x in [67,71]:b.box((x,6,105),(x+1,10,106),'stripped_oak_log','well.post')
b.box((66,10,103),(73,11,108),'dark_oak_slab','well.roof')
for x in [75,81]:b.box((x,5,104),(x+1,9,105),'spruce_log','notice.post')
b.box((75,7,104),(82,10,105),'oak_planks','notice.board');b.box((74,10,103),(83,11,106),'polished_deepslate_slab','notice.cap')
for x,z in [(42,69),(93,69),(140,72),(145,98),(24,110)]:
 b.box((x,5,z),(x+1,10,z+1),'spruce_log','street.lamp.post');b.put(x,10,z,'oak_slab','street.lamp.cap');b.put(x,9,z+1,M('lantern',hanging='true'),'street.lamp');b.put(x,10,z+1,'oak_slab','street.lamp.arm')
# A few supported shop seats, not a parking lot.
for x,z in [(16,75),(29,75),(84,70)]:
 for dx in range(3):b.put(x+dx,5,z,M('oak_stairs',facing='north'),'street.bench')
# Protect path width and support all yard paving / boundary bases.
for h in buildings:
 for v in [-1,-2]:box(h,h['door_u']-1,h['door_u']+3,h['g']+1,h['g']+3,v,v+1,'air','protected.entry')
for r in routes:
 path=r['path'];dx=abs(path[-1][0]-path[0][0]);dz=abs(path[-1][2]-path[0][2])
 for x,y,z in path:
  for a in [-1,0,1]:
   qx=x+(a if dz>=dx else 0);qz=z+(a if dx>dz else 0)
   for yy in range(y,y+2):b.put(qx,yy,qz,'air','protected.path')
for (x,y,z),st in list(B.items()):
 own=b.s.owners[x,y,z]
 if any(tag in own for tag in ['.yard.fence','.yard.terrace']):
  for yy in range(y):
   if (x,yy,z) not in B:b.put(x,yy,z,'dirt',own+'.support')
sp=dict(buildings=buildings,rooms=zones,roads=roads,entrances=entrances,connections=routes,stair_clearance_samples=stairs,trees=treerecs,site=dict(size_xyz=[W,H,D],base=4),protected_regions=['street','entries','stairs','bus.boarding'])
spec=dict(schema_version='japan-town12-2.0',design_brief=dict(case_id='japan_town12',version=RUN.replace('_replay',''),route='original',seed=SEED,units='integer Minecraft blocks; authored not measured',coordinates='Y up; east +X; north -Z',hard_constraints=['12 buildings','7 homes + 2 shops + 3 civic','old timber street','asphalt road and bus stop','all functional floors lit'],assumptions=['Original design based on sampled Freedom references, not tutorial copy','Furniture decorative; actual game pending'],source_report='JapanTown01.html; shop #104 replayed this revision'),spatial_spec=sp,facade_spec=dict(primary='old machiya timber structure / grey tiled double eaves / pale lattice / noren / supported warm lanterns',variation='fixed town layout; stable keyed choice of timber shade, tree crown and crop growth',seed_channels=['facade','tree','planting.edge','patch'],roof_palette=['grey tiles'],lighting='all functional floors, hanging lanterns supported by ceilings',age_is_design_assumption=True))
dump(C/'input/design_oldtown.json',spec)
out=save_run(C,RUN,spec,b,__file__,extra={'adapter':'japan_town12/2.0','building_count':12,'not_model_training':True,'origin':'Freedom-informed original old street','light_policy':'all functional floors; hanging lamps; simplified preview'})
dump(out/'site_records.json',sp)
print('DONE',out,flush=True)
