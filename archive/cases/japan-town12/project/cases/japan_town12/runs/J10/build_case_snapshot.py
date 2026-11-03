"""JapanDetail01 -> J10: original, bounded 12-lot town with use-specific interiors.
No video copy, no trained weights. Every selected parameter has an explicit consumer.
"""
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
M=states.make
RUN=sys.argv[1] if len(sys.argv)>1 else 'J10'
SEED=int(sys.argv[2]) if len(sys.argv)>2 else 20261029104
W,D,H=160,128,48
rng=lambda key:random.Random(int.from_bytes(hashlib.sha256(f'{SEED}:{key}'.encode()).digest()[:8],'big'))
b=Builder((W,H,D),SEED);B=b.s.blocks
# Fixed planning envelopes, seeded setback/width choices within each envelope.
rows=[
 ('H01','木格町屋','home',10,46,13,15,4,'S',2,'parallel','smooth_sandstone'),
 ('H02','木匠之家','home',29,43,13,16,5,'S',2,'cross','spruce_planks'),
 ('S01','紫帘和菓子铺','sweets',48,41,15,17,4,'S',2,'parallel','oak_planks'),
 ('S02','山口味噌店','miso',69,42,13,16,4,'S',2,'parallel','smooth_sandstone'),
 ('S03','松影茶屋','tea',89,39,18,20,4,'S',2,'offset','smooth_sandstone'),
 ('P01','灯坂旅馆','inn',115,40,23,22,4,'S',2,'hip','white_concrete'),
 ('H03','巷上平屋','home',23,12,17,18,6,'S',1,'hip','white_concrete'),
 ('H04','竹院旧宅','home',60,11,16,16,6,'S',2,'offset','smooth_sandstone'),
 ('P02','日和汤','bath',20,81,25,22,4,'N',1,'bath','white_concrete'),
 ('S04','赤灯小食堂','tavern',53,77,16,19,4,'N',2,'cross','spruce_planks'),
 ('H05','桥边住家','home',80,80,15,18,4,'N',2,'parallel','smooth_sandstone'),
 ('P03','町会所','community',110,82,23,21,4,'N',1,'hip','smooth_sandstone'),
]
def plan(seed):
 out=[]
 for row in rows:
  h=dict(zip(['id','name','use','x','z','w','d','g','face','floors','roof','wall'],row));rr=rng('layout.'+h['id'])
  h['x']+=rr.choice([0,1]);h['z']+=rr.choice([-1,0,1]);h['w']+=rr.choice([0,1])
  rr=rng('facade.'+h['id']);h.update(timber=rr.choice(['stripped_oak_log','stripped_spruce_log']),bay_step=rr.choice([4,5]),lattice_family=rr.choice(['vertical','screen','framed']),eave_depth=3 if h['use']!='home' else rr.choice([2,3]),maintenance=round(rr.uniform(.66,.91),2),age=rr.randrange(30,75),floor_step=6)
  h['door_u']=h['w']//2-1 if h['use'] in ['inn','bath','community'] else 2
  h['local_width']=h['w'];h['local_depth']=h['d'];h['accent']={'sweets':'purple','miso':'white','tea':'blue','tavern':'red','inn':'blue','bath':'blue','community':'white'}.get(h['use'],'white')
  h['upper_width']=h['w']-4 if h['roof']=='offset' else h['w'];h['upper_depth']=h['d']-2 if h['use']=='inn' else h['d']
  out.append(h)
 return out
buildings=plan(SEED)
roads=[dict(id='main',path=[[0,69],[28,69],[56,65],[98,65],[128,70],[160,71]],width=7,kind='asphalt'),dict(id='north_lane',path=[[8,38],[36,38],[58,33],[96,33],[118,35],[145,43],[145,70]],width=3,kind='stone'),dict(id='south_lane',path=[[8,70],[8,109],[53,112],[95,107],[143,110],[150,73]],width=3,kind='stone')]
def mask(path,width):
 im=Image.new('1',(W,D));ImageDraw.Draw(im).line([tuple(q) for q in path],fill=1,width=width);return np.array(im)
road=np.zeros((D,W),bool);walk=np.zeros_like(road);reserved=np.zeros_like(road);paved=np.zeros_like(road)
for r in roads:
 m=mask(r['path'],r['width']);paved|=m
 if r['kind']=='asphalt':road|=m;walk|=mask(r['path'],r['width']+4)
 else:walk|=m
height=np.fromfunction(lambda z,x:4+np.clip((35-z)//10,0,2),(D,W),dtype=int).astype(int)
height[road]=4
for h in buildings:
 x,z,w,d,g=(h[k] for k in ['x','z','w','d','g'])
 height[z-2:z+d+3,x-2:x+w+3]=g;reserved[z-4:z+d+5,x-4:x+w+5]=True
print('terrain / irregular lanes',flush=True)
for z in range(D):
 for x in range(W):
  y=int(height[z,x]);b.box((x,0,z),(x+1,y,z+1),'dirt','site.terrain');b.put(x,y,z,'grass_block','site.surface')
  if walk[z,x]:b.put(x,y,z,'stone_bricks' if (x+z)%9 else 'gravel','lane.paving')
  if road[z,x]:b.put(x,4,z,'gray_concrete','street.asphalt')
reserved|=walk
entrances=[];stairs=[];zones=[];spaces=[];furniture_records=[];detail_records=[];route_keepouts=[]
def world(h,u,y,v):
 x,z,w,d=h['x'],h['z'],h['w'],h['d']
 return (x+u,y,z+d-1-v) if h['face']=='S' else (x+w-1-u,y,z+v)
def mat(h,s):
 s=M(s) if not s.startswith('minecraft:') else s
 if h['face']=='N':s=states.rotate_state(states.rotate_state(s))
 return s
def P(h,u,y,v,s,part,empty=False):return b.put(*world(h,u,y,v),mat(h,s),h['id']+'.'+part,empty)
def box(h,u0,u1,y0,y1,v0,v1,s,part):
 for u in range(u0,u1):
  for y in range(y0,y1):
   for v in range(v0,v1):P(h,u,y,v,s,part)
def clear(h,u0,u1,y0,y1,v0,v1,part='void'):box(h,u0,u1,y0,y1,v0,v1,'air',part)
def slab(h,u,y,v,s='spruce_slab',top=False,part='trim'):P(h,u,y,v,M(s,type='top' if top else 'bottom'),part)
def lamp(h,u,y,v,part='light'):
 P(h,u,y,v,M('lantern',hanging='true'),part)
 # Hanging anchor is always designed rather than filled to an unknown surface.
 P(h,u,y+1,v,M(h['timber'],axis='x'),part+'.anchor')
def flowerpot(h,u,y,v):
 P(h,u,y,v,'flower_pot','decor.flowerpot')
def planter(h,u,v,g,size=1):
 box(h,u,u+size,g+1,g+2,v,v+size,'terracotta','planter')
 box(h,u,u+size,g+2,g+3,v,v+size,'azalea_leaves','plant')
def bench(h,u,v,g,n=3,facing='south'):
 for k in range(n):P(h,u+k,g+1,v,M('spruce_stairs',facing=facing),'seat')
def table(h,u,v,g,w=2,d=2):
 for x in range(u,u+w):
  for z in range(v,v+d):slab(h,x,g+1,z,'dark_oak_slab',part='table')
 furniture_records.append(dict(building=h['id'],kind='low_table',anchor=list(world(h,u,g+1,v)),decorative=True))
def shoji(h,u0,u1,y,v,family='vertical',high=3):
 for u in range(u0,u1):
  for yy in range(y,y+high):P(h,u,yy,v,'white_stained_glass_pane','window.backing')
  slab(h,u,y-1,v-1,'spruce_slab',True,'window.sill');slab(h,u,y+high,v-1,'spruce_slab',False,'window.head')
  if family=='vertical' and (u-u0)%2==1:
   for yy in range(y,y+high):P(h,u,yy,v-1,M('oak_fence'),'window.slats')
  elif family=='screen' and u in [u0,u1-1]:
   for yy in range(y,y+high):P(h,u,yy,v-1,M('oak_trapdoor',facing='south',open='true'),'window.shutter')
 b.windows.append(dict(id=h['id']+'.window.'+str(len(b.windows)),anchor=list(world(h,u0,y,v)),size=[u1-u0,high],family=family,recess=1))
def roof(h,u0,u1,v0,v1,eave,axis='u',hip=False):
 # Separate continuous tile field, verge, ridge, and eave timber; no random holes.
 rr=rng(h['id']+f'.roof.{u0}.{v0}.{eave}')
 for u in range(u0-2,u1+2):
  for v in range(v0-2,v1+2):
   dn={'north':v-v0+2,'south':v1+1-v};de={'east':u-u0+2,'west':u1+1-u}
   choices={**dn,**de} if hip else dn if axis=='u' else de
   c=min(choices.values());fd=min(choices,key=choices.get);y=eave+c//2
   # Color repairs are sparse and clustered by row; every block remains a complete roof part.
   typ='deepslate_brick' if c==1 and u%9==int(rr.random()*9) else 'deepslate_tile'
   P(h,u,y,v,M(typ+'_slab') if c%2==0 else M(typ+'_stairs',facing=fd),'roof.tile')
   if u0<=u<u1 and v0<=v<v1 and (u in [u0,u1-1] or v in [v0,v1-1]):
    for yy in range(eave,y):P(h,u,yy,v,h['wall'],'gable.infill')
   # a thin dark underside under the outside rim only
   if c==0:slab(h,u,eave-1,v,'dark_oak_slab',True,'roof.edge_wood')
 if not hip:
  mid=(v0+v1-1)//2 if axis=='u' else (u0+u1-1)//2
  for t in range((u0-2 if axis=='u' else v0-2),(u1+2 if axis=='u' else v1+2)):
   u,v=(t,mid) if axis=='u' else (mid,t);c=min(v-v0+2,v1+1-v) if axis=='u' else min(u-u0+2,u1+1-u)
   slab(h,u,eave+c//2+1,v,'deepslate_tile_slab',False,'roof.ridge')
  # Capped gable ends, not exaggerated temple corners.
  for t in [(u0-2 if axis=='u' else v0-2),(u1+1 if axis=='u' else v1+1)]:
   u,v=(t,mid) if axis=='u' else (mid,t);c=min(v-v0+2,v1+1-v) if axis=='u' else min(u-u0+2,u1+1-u)
   P(h,u,eave+c//2+1,v,'deepslate_tiles','roof.ridge_end')
 # Repeated short rafter ends have free gaps rather than a solid decorative wall.
 for u in range(u0,u1,2):
  for v in [v0-1,v1]:
   P(h,u,eave-1,v,M('spruce_stairs',facing='north' if v==v0-1 else 'south',half='top'),'roof.rafter')
 detail_records.append(dict(building=h['id'],kind='layered_roof',eave_y=eave,axis=axis,hip=hip,bounds_local=[u0,v0,u1,v1]))
def canopy(h,w,g,depth,wrap=False):
 for u in range(-1,w+1):
  for v in range(-depth,0):
   c=v+depth;y=g+5+c//2
   P(h,u,y,v,M('deepslate_tile_slab') if c%2==0 else M('deepslate_tile_stairs',facing='north'),'canopy.tile')
  slab(h,u,g+4,-depth,'dark_oak_slab',True,'canopy.fascia')
  if u%2==0:P(h,u,g+4,-depth+1,M('spruce_stairs',facing='north',half='top'),'canopy.rafter')
 for u in [0,w-1]:
  P(h,u,g+4,-1,M(h['timber'],axis='z'),'canopy.beam_end')
  if h['use']!='home':
   box(h,u,u+1,g+1,g+4,-depth+1,-depth+2,h['timber'],'canopy.post')
   P(h,u,g+3,-1,M('spruce_stairs',facing='north',half='top'),'canopy.brace')
 if wrap:
  for u in [-2,-1]:
   for v in range(1,6):slab(h,u,g+5,v,'deepslate_tile_slab',False,'canopy.side_wrap')
def wall_screen(h,u0,u1,y0,y1,v,opening=()):
 for u in range(u0,u1):
  if u in opening:continue
  for y in range(y0,y1):P(h,u,y,v,'white_stained_glass_pane' if y>y0 else 'spruce_planks','interior.screen')
 for u in range(u0,u1):P(h,u,y1,v,M(h['timber'],axis='x'),'interior.screen_head')
def tatami(h,u0,u1,v0,v1,g):
 for u in range(u0,u1):
  for v in range(v0,v1):
   # colored inset and carpet border: visual tatami, not custom block or historical measurement
   P(h,u,g,v,'green_wool' if (u-u0)%4!=3 else 'brown_wool','tatami.inset')
   if (v-v0)%5==0:P(h,u,g+1,v,'brown_carpet','tatami.binding')
def cabinets(h,u0,u1,v,g,kind='storage'):
 for u in range(u0,u1):
  P(h,u,g+1,v,'bookshelf' if kind=='books' else 'spruce_planks','furniture.'+kind)
  P(h,u,g+2,v,M('oak_trapdoor',facing='south',open='true'),'furniture.cabinet_face')
  slab(h,u,g+3,v,'spruce_slab',False,'furniture.shelf')
def bedroll(h,u,v,g,color='white'):
 for x in range(u,u+2):
  for z in range(v,v+3):P(h,x,g+1,z,'white_carpet' if z==v else color+'_carpet','bedroll.decorative')
 furniture_records.append(dict(building=h['id'],kind='futon_decorative',anchor=list(world(h,u,g+1,v)),interactive=False))
def roomrec(h,k,name,u0,u1,v0,v1,fy):
 a=world(h,u0,fy+1,v0);z=world(h,u1-1,fy+5,v1-1);bounds=[min(a[0],z[0]),fy+1,min(a[2],z[2]),max(a[0],z[0])+1,fy+6,max(a[2],z[2])+1]
 rr=dict(id=h['id']+f'.F{k+1}.{name}',building=h['id'],floor=k+1,function=name,bounds_xyz=bounds,lighting='supported warm lantern; game illuminance pending')
 spaces.append(rr)
def interiors(h,w,d,g,k):
 use=h['use'];fy=g+k*6;door=h['door_u'];middle=d//2
 # Side passage to the stair and a front cross-route remain continuous.
 if use=='home':
  if k==0:
   for u in range(1,5):
    for v in range(1,d-1):P(h,u,fy,v,'stone_bricks' if v<4 else 'spruce_planks','interior.entry_strip')
   cabinets(h,6,w-2,2,fy,'kitchen');P(h,w-3,fy+2,2,'iron_trapdoor','interior.hob')
   wall_screen(h,5,w-1,fy+1,fy+4,middle,opening=[5,6])
   tatami(h,6,w-1,middle+1,d-2,fy);table(h,8,min(d-5,middle+3),fy)
   cabinets(h,w-3,w-2,d-3,fy,'shrine_alcove');flowerpot(h,w-3,fy+4,d-3)
   roomrec(h,k,'entry_kitchen',1,w-1,1,middle,fy);roomrec(h,k,'tatami_living',5,w-1,middle+1,d-1,fy)
  else:
   tatami(h,6,w-1,2,d-2,fy);wall_screen(h,5,w-1,fy+1,fy+4,middle,opening=[5,6])
   bedroll(h,8,2,fy,'white');bedroll(h,8,middle+2,fy,'light_gray')
   cabinets(h,w-3,w-2,d-2,fy,'wardrobe');table(h,6,d-4,fy,1,1)
   roomrec(h,k,'sleeping',5,w-1,1,d-1,fy)
 elif use in ['sweets','miso','tea','tavern']:
  if k==0:
   # street -> display -> work side, with side circulation to the rear
   for u in range(6,w-2):
    P(h,u,fy+1,4,'smooth_sandstone' if use=='sweets' else 'dark_oak_planks','shop.counter')
    slab(h,u,fy+2,4,'spruce_slab',False,'shop.counter_top')
    if u%2==0:P(h,u,fy+3,4,M({'sweets':'purple_candle','miso':'yellow_candle','tea':'green_candle','tavern':'red_candle'}[use],candles=str(1+u%3)),'shop.goods')
   cabinets(h,6,w-2,7,fy,'goods');wall_screen(h,5,w-1,fy+1,fy+4,d-6,opening=[5,6])
   if use=='miso':
    for u in range(7,w-1,3):
     for v in [d-4,d-2]:
      P(h,u,fy+1,v,'spruce_planks','stock.tub');slab(h,u,fy+2,v,'dark_oak_slab',False,'stock.lid')
   else:
    tatami(h,6,w-1,d-5,d-1,fy);table(h,7,d-4,fy)
   if use=='tavern':
    for u in range(7,w-2,2):P(h,u,fy+1,3,M('spruce_stairs',facing='north'),'shop.bar_seat')
   roomrec(h,k,'sales_and_service',5,w-1,1,d-6,fy);roomrec(h,k,'stock' if use=='miso' else 'rear_rest',5,w-1,d-5,d-1,fy)
  else:
   tatami(h,5,w-1,2,d-2,fy)
   if use in ['tea','tavern']:
    for u,v in [(7,3),(w-5,d-5)]:table(h,u,v,fy,2,2)
    cabinets(h,w-3,w-2,d-3,fy,'tea_ware')
   else:bedroll(h,7,3,fy,'white');cabinets(h,6,w-2,d-2,fy,'stock')
   roomrec(h,k,'tea_room' if use in ['tea','tavern'] else 'shopkeeper_home',5,w-1,1,d-1,fy)
 elif use=='inn':
  if k==0:
   cabinets(h,3,7,3,fy,'reception');bench(h,w-7,3,fy,4,'north')
   wall_screen(h,1,w-1,fy+1,fy+4,7,opening=[door,door+1])
   # timber walkway and a small contained planted-water alcove
   tatami(h,6,door-1,9,d-2,fy);table(h,7,11,fy)
   for u in range(w-7,w-2):
    for v in range(d-7,d-2):
     P(h,u,fy,v,'stone_bricks','inn.garden.bottom');P(h,u,fy+1,v,'stone_bricks' if u in [w-7,w-3] or v in [d-7,d-3] else 'water','inn.garden.basin')
   for u,v in [(w-6,d-6),(w-4,d-4)]:
    P(h,u,fy+1,v,'moss_block','inn.garden.island')
    for dy in [2,3,4]:P(h,u,fy+dy,v,M('bamboo',leaves='small' if dy==4 else 'none'),'inn.garden.bamboo')
   roomrec(h,k,'reception',1,w-1,1,7,fy);roomrec(h,k,'lounge_garden',5,w-1,8,d-1,fy)
  else:
   for v in range(2,d-2,7):
    wall_screen(h,5,w-1,fy+1,fy+4,v,opening=[door,door+1])
    for u0,u1 in [(5,door-1),(door+3,w-1)]:
     tatami(h,u0,u1,v+1,min(v+6,d-1),fy)
     bedroll(h,u0+1,v+2,fy,'white');table(h,u1-2,v+2,fy,1,1)
   roomrec(h,k,'guest_rooms_and_corridor',1,w-1,1,d-1,fy)
 elif use=='bath':
  # Different program: shoes -> reception -> changing -> two screened washing/pool zones.
  cabinets(h,2,7,2,fy,'shoe_lockers');cabinets(h,w-7,w-2,2,fy,'reception')
  wall_screen(h,1,w-1,fy+1,fy+4,6,opening=[door,door+1])
  for u in range(2,w-2):
   if u not in [door,door+1]:P(h,u,fy+1,8,'spruce_planks','bath.changing_cabinet')
  for u0,u1 in [(2,door-1),(door+3,w-2)]:
   for u in range(u0,u1):
    for v in range(12,d-2):
     P(h,u,fy,v,'smooth_stone','bath.pool_bottom')
     P(h,u,fy+1,v,'smooth_stone' if u in [u0,u1-1] or v in [12,d-3] else 'water','bath.pool')
   for u in range(u0+1,u1-1,2):P(h,u,fy+1,10,M('smooth_stone_slab'),'bath.wash_seat')
  box(h,door-1,door,fy+1,fy+4,9,d-1,'white_concrete','bath.privacy_wall')
  box(h,door+2,door+3,fy+1,fy+4,9,d-1,'white_concrete','bath.privacy_wall')
  roomrec(h,k,'entry_changing',1,w-1,1,9,fy);roomrec(h,k,'washing_pools',1,w-1,10,d-1,fy)
 elif use=='community':
  cabinets(h,2,7,2,fy,'welcome');cabinets(h,2,5,d-2,fy,'books');cabinets(h,w-5,w-2,d-2,fy,'books')
  tatami(h,4,w-4,7,d-3,fy)
  for u,v in [(6,9),(w-8,9),(6,d-6),(w-8,d-6)]:table(h,u,v,fy,3,2)
  wall_screen(h,2,w-2,fy+1,fy+4,5,opening=[door,door+1])
  roomrec(h,k,'foyer',1,w-1,1,5,fy);roomrec(h,k,'meeting_reading',1,w-1,6,d-1,fy)
 # Functional and circulation lighting; not random dark rooms.
 positions={(max(2,door),3),(max(6,w//2),d//2),(w-4,d-4),(3,d-4)}
 for u,v in sorted(positions):lamp(h,u,fy+5,v,'interior.lamp')
 a=world(h,1,fy+1,1);z=world(h,w-2,fy+5,d-2)
 zones.append(dict(id=h['id']+f'.F{k+1}',building=h['id'],use=use,floor_block_y=fy,standing_y=fy+1,ceiling_y=fy+6,clear_height=5,bounds_xyz=[min(a[0],z[0]),fy+1,min(a[2],z[2]),max(a[0],z[0])+1,fy+6,max(a[2],z[2])+1]))
def staircase(h,w,d,g):
 # Six rises, protected 2-wide side stair. A gap in the intermediate floor is real.
 v0=max(7,d-9)
 for i in range(6):
  for u in [2,3]:
   clear(h,u,u+1,g+i+2,g+10,v0+i,v0+i+1,'stairs.headroom')
   for yy in range(g+1,g+i+1):P(h,u,yy,v0+i,'spruce_planks','stairs.support')
   P(h,u,g+i+1,v0+i,M('spruce_stairs',facing='north'),'stairs')
   stairs.append(list(world(h,u,g+i+2,v0+i)))
 h['stair_local']=[2,v0,2,6]

print('twelve building families / interiors',flush=True)
for h in buildings:
 w,d,g=h['w'],h['d'],h['g'];door=h['door_u'];use=h['use']
 box(h,-1,w+1,g-2,g,-1,d+1,'stone_bricks','foundation')
 for k in range(h['floors']):
  fy=g+k*6;uw=w if k==0 else h['upper_width'];ud=d if k==0 else h['upper_depth']
  box(h,0,uw,fy,fy+1,0,ud,'spruce_planks','floor')
  box(h,0,uw,fy+1,fy+6,0,ud,h['wall'],'wall');clear(h,1,uw-1,fy+1,fy+6,1,ud-1)
  box(h,0,uw,fy+6,fy+7,0,ud,'dark_oak_planks','ceiling')
  bays=sorted(set([0,uw-1]+list(range(h['bay_step'],uw-1,h['bay_step']))))
  for u in bays:
   for v in [0,ud-1]:box(h,u,u+1,fy+1,fy+6,v,v+1,h['timber'],'frame.post')
  for v in [0,ud-1]:box(h,0,uw,fy+5,fy+6,v,v+1,M(h['timber'],axis='x'),'frame.beam')
  for u in [0,uw-1]:
   for v in range(4,ud-1,5):box(h,u,u+1,fy+1,fy+6,v,v+1,h['timber'],'frame.side')
  for a,z in zip(bays,bays[1:]):
   if z-a<3:continue
   if k==0 and (a<=door+1 and z>=door):continue
   if k==0 and use in ['sweets','miso','tea','tavern'] and z>5:continue
   fam=h['lattice_family'] if k else 'framed'
   shoji(h,a+1,z,fy+2,0,fam,2)
  # Rear window groups are narrower, alternate with storage walls.
  for a in [2,max(3,uw-6)]:shoji(h,a,min(a+3,uw-1),fy+2,ud-1,'framed',2)
  for u in [0,uw-1]:
   for v in [3,ud-5]:
    for dv in [0,1]:
     for y in [fy+2,fy+3]:P(h,u,y,v+dv,'white_stained_glass_pane','side.window')
  interiors(h,uw,ud,g,k)
 # Different volumetric families, plus low wing for offset homes/tea house.
 if h['floors']==2 and h['upper_width']<w:roof(h,h['upper_width']-1,w,0,d,g+6,axis='v')
 roof(h,0,h['upper_width'] if h['floors']==2 else w,0,h['upper_depth'] if h['floors']==2 else d,g+h['floors']*6,axis='v' if h['roof']=='cross' else 'u',hip=h['roof'] in ['hip','bath'])
 canopy(h,w,g,h['eave_depth'],wrap=use=='sweets')
 if use=='bath':roof(h,door-3,door+5,-3,3,g+6,axis='v')
 # Recessed entry; door is one block behind the facade plane.
 clear(h,door,door+2,g+1,g+5,-1,3,'entry.recess')
 for u in [door,door+1]:
  for half,dy in [('lower',1),('upper',2)]:P(h,u,g+dy,1,M('oak_door',half=half,hinge='left' if u==door else 'right',facing='south'),'entry.door')
  entrances.append(dict(building=h['id'],inside=list(world(h,u,g+1,2)),door=list(world(h,u,g+1,1)),outside=list(world(h,u,g+1,0))))
 # The old shell becomes an occupied building before frontage props are added.
 if h['floors']==2:staircase(h,w,d,g)
 for k in range(h['floors']):
  fy=g+k*6;uw=w if k==0 else h['upper_width'];ud=d if k==0 else h['upper_depth']
  clear(h,2,4,fy+1,fy+3,2,max(7,ud-9),'circulation.side')
  clear(h,2,min(door+2,uw-1),fy+1,fy+3,3,5,'circulation.cross')
  if use in ['inn','bath','community']:clear(h,door,door+2,fy+1,fy+3,2,ud-1,'circulation.central')
 # Apron, then one clear entrance lane. Streetside display does not block entry.
 for u in range(-1,w+1):
  for v in range(-4,0):
   x,y,z=world(h,u,g,v)
   for yy in range(g):b.put(x,yy,z,'dirt',h['id']+'.apron.support')
   P(h,u,g,v,'stone_bricks' if u%7 else 'gravel','apron')
 if use in ['sweets','miso','tea','tavern']:
  clear(h,6,w-2,g+2,g+5,0,1,'shop.opening')
  for u in range(6,w-2):
   P(h,u,g+1,0,'spruce_planks','shop.front_counter');slab(h,u,g+2,-1,'spruce_slab',False,'shop.display_lip')
   if u%3==0:P(h,u,g+3,0,M('yellow_candle',candles='3'),'shop.front_goods')
  for u in range(5,w-1):
   P(h,u,g+4,0,M(h['timber'],axis='x'),'noren.rail')
   if u%3!=0:P(h,u,g+4,-1,M(h['accent']+'_wall_banner',facing='south'),'noren')
  # Sign is a low, supported wood fascia, not giant generated text.
  box(h,5,min(w-2,11),g+6,g+7,-1,0,'smooth_sandstone' if use=='sweets' else 'spruce_planks','shop.signboard')
  bench(h,max(7,w-6),-3,g,3,'south')
  if use=='sweets':table(h,6,-3,g,1,1)
  if use=='miso':
   for u in [6,w-2]:P(h,u,g+1,-2,'spruce_planks','shop.tub');slab(h,u,g+2,-2,'dark_oak_slab',False,'shop.tub_lid')
 elif use in ['inn','bath','community']:
  for u in [door-1,door+2]:
   P(h,u,g+4,0,h['timber'],'entry.curtain_rail');P(h,u,g+4,-1,M(h['accent']+'_wall_banner',facing='south'),'entry.curtain')
  bench(h,w-6,-3,g,3,'south')
 else:
  box(h,w-4,w-2,g+1,g+2,-2,-1,'spruce_planks','entry.storage');slab(h,w-3,g+2,-2,'spruce_slab',False,'entry.shelf')
 for u in sorted(set([door-1,w-2])):lamp(h,u,g+4,-2,'eave.lamp')
 planter(h,w-2,-3,g)
 # One rain chain per large frontage, connected to the canopy and a stone catch basin.
 if use!='home':
  u=-1;v=-2
  for y in range(g+2,g+5):P(h,u,y,v,M('chain',axis='y'),'rain_chain')
  P(h,u,g+1,v,'stone_brick_slab','rain_chain.catch');P(h,u,g+5,v,'deepslate_tiles','rain_chain.anchor')
 # A defined rear service terrace, varied by building program.
 for u in range(1,w-1):
  for v in [d,d+1]:P(h,u,g,v,'stone_bricks' if use in ['bath','miso'] else 'spruce_planks','rear.terrace')
 for u in [1,w-2]:planter(h,u,d+1,g)

# Routes select the closest connected lane, with gentle authored step transitions.
routes=[];choices=np.argwhere(walk)
for h in buildings:
 sx,_,sz=world(h,h['door_u'],h['g'],-3);j=np.argmin((choices[:,1]-sx)**2+(choices[:,0]-sz)**2);tz,tx=map(int,choices[j]);n=max(abs(tx-sx),abs(tz-sz),1);path=[]
 for i in range(n+1):
  t=i/n;x=round(sx+(tx-sx)*t);z=round(sz+(tz-sz)*t);y=round(h['g']+(int(height[tz,tx])-h['g'])*t)
  for a in [-1,0,1]:
   xx=x+(a if abs(tz-sz)>=abs(tx-sx) else 0);zz=z+(a if abs(tx-sx)>abs(tz-sz) else 0)
   for yy in range(y):b.put(xx,yy,zz,'stone_bricks','paths.support')
   b.put(xx,y,zz,'stone_bricks','paths.surface');reserved[zz,xx]=True
   for yy in range(y+1,max(y+4,h['g']+3)):b.put(xx,yy,zz,'air','paths.clear')
  if not path or path[-1]!=[x,y+1,z]:path.append([x,y+1,z])
 routes.append(dict(building=h['id'],width=3,path=path))

print('gardens / connected canal / public facilities',flush=True)
# Lined water channel with closed ends; no loose water sources in grass.
for x in range(152,157):
 for z in range(25,121):
  b.put(x,2,z,'stone_bricks','canal.bottom')
  edge=x in [152,156] or z in [25,120]
  b.put(x,3,z,'stone_bricks' if edge else 'water','canal.wall_water')
  b.put(x,4,z,'stone_bricks' if edge else 'air','canal.rim')
  for y in [5,6]:b.put(x,y,z,'air','canal.clear')
for z in [44,72,109]:
 b.box((151,4,z-1),(158,5,z+2),'spruce_planks','bridge.deck')
 for zz in [z-2,z+2]:
  for x in range(151,158):b.put(x,5,zz,M('oak_fence',east='true',west='true'),'bridge.rail')
trees=[]
def tree(x,z,key,hh=8,rad=3):
 if reserved[z,x]:return
 rr=rng('tree.'+key);g=int(height[z,x]);hh+=rr.choice([-1,0,1]);rad+=rr.choice([0,1])
 b.box((x,g+1,z),(x+1,g+hh,z+1),'oak_log','tree.'+key+'.trunk')
 for yy in range(g+hh-4,g+hh+2):
  for xx in range(max(0,x-rad),min(W,x+rad+1)):
   for zz in range(max(0,z-rad),min(D,z+rad+1)):
    if ((xx-x)/rad)**2+((zz-z)/rad)**2+((yy-g-hh+1)/3)**2 < 1+rr.uniform(-.12,.12) and not walk[zz,xx]:
     b.put(xx,yy,zz,'cherry_leaves' if key in ['south2','garden2'] else 'oak_leaves','tree.'+key+'.leaves',empty=True)
 trees.append(dict(id=key,x=x,z=z,height=hh,radius=rad))
for x,z,key,hh,r in [(8,15,'north1',8,3),(48,13,'north2',9,3),(87,11,'north3',8,4),(108,17,'garden1',8,3),(132,19,'garden2',9,4),(143,27,'east1',8,3),(11,92,'south1',8,3),(39,116,'south2',8,4),(71,113,'south3',8,3),(101,115,'south4',9,3),(141,97,'east2',8,3)]:tree(x,z,key,hh,r)
# Smaller garden clusters are constrained by paths/buildings instead of filling every vacancy.
rr=rng('garden.cluster')
for ax,az in [(99,17),(91,25),(47,27),(12,28),(99,99),(139,113)]:
 for i in range(7):
  x,z=ax+rr.randint(-3,3),az+rr.randint(-3,3)
  if not (2<x<W-3 and 2<z<D-3) or reserved[z,x]:continue
  g=int(height[z,x]);b.put(x,g+1,z,'azalea_leaves','garden.shrub')
  if i%3==0:b.put(x,g+2,z,'oak_leaves','garden.shrub_high')
for ax,az,ww,dd in [(82,19,5,7),(13,15,4,8),(102,111,5,9)]:
 rr=rng(f'crop.{ax}.{az}')
 for x in range(ax,ax+ww):
  for z in range(az,az+dd):
   if reserved[z,x]:continue
   g=int(height[z,x]);b.put(x,g,z,'farmland','kitchen_garden.soil');b.put(x,g+1,z,M('carrots',age=rr.choice([4,6,7])),'kitchen_garden.crop')
# Western stop, not counted as one of the twelve buildings.
for x in [3,10]:b.box((x,5,61),(x+1,9,62),'stripped_oak_log','bus.post')
for x in range(2,12):
 for z in range(59,64):b.put(x,9+min(z-59,63-z)//2,z,'deepslate_tile_slab','bus.roof')
for x in range(4,10):b.put(x,5,61,M('spruce_stairs',facing='south'),'bus.bench')
for x in [4,9]:b.put(x,8,61,M('lantern',hanging='true'),'bus.lantern')
b.box((3,5,65),(4,10,66),'spruce_log','bus.sign.post');b.box((2,9,65),(5,11,66),'spruce_planks','bus.sign')
# Public notice board and small well in the gap between south houses and meeting hall.
for x in [100,106]:b.box((x,5,91),(x+1,9,92),'spruce_log','public.notice.post')
b.box((100,7,91),(107,10,92),'oak_planks','public.notice.board');b.box((99,10,90),(108,11,93),'deepslate_tile_slab','public.notice.roof')
for x in range(101,106):
 for z in range(97,102):
  b.put(x,4,z,'stone_bricks','well.bottom');b.put(x,5,z,'stone_bricks' if x in [101,105] or z in [97,101] else 'water','well.basin')
for x in [101,105]:b.box((x,6,99),(x+1,10,100),'oak_log','well.post')
b.box((100,10,96),(107,11,103),'deepslate_tile_slab','well.roof')
for x,z in [(42,65),(85,68),(111,72),(142,76),(12,106),(49,110),(96,104),(12,38),(80,33)]:
 g=int(height[z,x]);b.box((x,g+1,z),(x+1,g+6,z+1),'spruce_log','lane.lamp.post')
 b.put(x,g+6,z,'spruce_slab','lane.lamp.cap');b.put(x+1,g+6,z,'spruce_slab','lane.lamp.arm');b.put(x+1,g+5,z,M('lantern',hanging='true'),'lane.lamp')
# Final protected routes. Props and vegetation never win over streets/entrances.
for z,x in zip(*np.where(road)):
 for y in [5,6,7]:b.put(int(x),y,int(z),'air','street.clearance')
for r in routes:
 path=r['path'];dx=abs(path[-1][0]-path[0][0]);dz=abs(path[-1][2]-path[0][2])
 for x,y,z in path:
  for a in [-1,0,1]:
   xx=x+(a if dz>=dx else 0);zz=z+(a if dx>dz else 0)
   for yy in range(y,y+2):b.put(xx,yy,zz,'air','protected.route')
for h in buildings:
 clear(h,h['door_u'],h['door_u']+2,h['g']+1,h['g']+3,-3,1,'protected.entry')
# Fill short support gaps under fixed hanging lights (never across whole rooms).
for (x,y,z),st in list(B.items()):
 if 'minecraft:lantern[hanging=true' in st and (x,y+1,z) not in B:
  top=next((yy for yy in range(y+2,min(y+5,H)) if (x,yy,z) in B),None)
  if top is None:raise ValueError(('lamp no support',x,y,z))
  for yy in range(y+1,top):b.put(x,yy,z,M('chain',axis='y'),'lighting.support_chain')
sp=dict(buildings=buildings,rooms=zones,interior_zones=spaces,roads=roads,entrances=entrances,connections=routes,stair_clearance_samples=stairs,trees=trees,furniture=furniture_records,details=detail_records,site=dict(size_xyz=[W,H,D],base=4),protected_regions=['road','entrance','two-wide stairs','side passage','central passage','bus boarding'])
spec=dict(schema_version='japan-town12-3.0',design_brief=dict(case_id='japan_town12',version=RUN.replace('_replay',''),route='original',seed=SEED,units='integer Minecraft blocks; original design, not measured',coordinates='Y up; east +X; north -Z',hard_constraints=['12 main buildings','5 homes + 4 shops + inn + bath + community','old Japanese town','asphalt main road and bus stop','all functional floors lit'],source_report='JapanDetail01.html / 10 sampled observations; proposals are original'),spatial_spec=sp,facade_spec=dict(primary='layered grey tile eaves, exposed rafter ends, framed and sparse vertical windows, recessed entries, use-specific fronts',seed_channels=['layout','facade','roof','tree','garden.cluster','crop'],layout='fixed 12 envelopes and street skeleton; seeded width and setback inside envelope',roof_palette=['deepslate tiles','sparse deepslate bricks'],lighting='all functional floors; supported lanterns; no random blackout'),evidence_consumers=[dict(id='E01',consumer='roof/canopy',source=['O01','O03'],status='case_specific'),dict(id='F01',consumer='shop/opening/noren/sign/display/bench',source=['O09','O10'],status='case_specific'),dict(id='F02',consumer='shoji',source=['O02','O03'],status='case_specific'),dict(id='I01',consumer='interiors',source=['O04','O07','O08'],status='case_specific; original spatial proposals'),dict(id='R01',consumer='plan/rng keyed channels',status='bounded parametric variation; not free layout solver')])
dump(C/'input/design_detailtown.json',spec)
out=save_run(C,RUN,spec,b,__file__,extra={'adapter':'japan_town12/3.0','building_count':12,'not_model_training':True,'origin':'JapanDetail01-informed original rebuild','light_policy':'all functional floors, supported warm lanterns'})
dump(out/'site_records.json',sp)
print('DONE',out,flush=True)
