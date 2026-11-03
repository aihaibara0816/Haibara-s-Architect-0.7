"""Three authored structure families with program-specific interiors; not an arbitrary solver."""
from pathlib import Path
import sys,copy,json,uuid,random,hashlib,math
import nbtlib as n
import town_states
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
from interior_kit import InteriorKit
ROOT=Path(__file__).resolve().parents[1]
class Module:
 def __init__(self,id,w,d,levels,program,seed):
  self.id=id;self.w=w;self.d=d;self.levels=levels;self.program=program;self.seed=seed
  self.blocks={};self.bes={};self.entities=[];self.uses=[];self.doors=[];self.lights=[];self.stair_paths=[];self.groups=[];self.entry=[w//2,3,d-3]
 def p(self,x,y,z,st,owner='',**pr):
  q=(x,y,z);st=S.make(st,**{k:str(v).lower()for k,v in pr.items()})if not st.startswith('minecraft:')else st
  if st=='minecraft:air':self.blocks.pop(q,None)
  else:self.blocks[q]=st
  self.bes.pop(q,None)
 def box(self,lo,hi,name,owner='',**pr):
  for x in range(lo[0],hi[0]):
   for y in range(lo[1],hi[1]):
    for z in range(lo[2],hi[2]):self.p(x,y,z,name,owner,**pr)
 def use(self,id,x,z,f=2):self.uses.append({'id':self.id+'.'+id,'pos':[x,f+1,z],'floor_block_y':f})
 def barrel(self,x,y,z,face='south'):
  self.p(x,y,z,'barrel',facing=face);self.bes[x,y,z]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])})
 def pot(self,x,y,z):
  rr=random.Random(int(hashlib.sha256(f'{self.seed}/{self.id}/{x},{y},{z}'.encode()).hexdigest()[:16],16));self.p(x,y,z,rr.choice(['potted_fern','potted_bamboo','potted_azalea_bush','potted_flowering_azalea_bush']))
 def lamp(self,x,y,z):
  self.p(x,y+1,z,'stripped_oak_log',axis='x');self.p(x,y,z,'lantern',hanging=True)
  self.lights.append({'position':[x,y,z],'support':[x,y+1,z]})
 def door(self,x,y,z,face='south',wood='oak'):
  for yy,half in [(y,'lower'),(y+1,'upper')]:self.p(x,yy,z,wood+'_door',facing=face,half=half)
  self.p(x,y+2,z,'stripped_spruce_log',axis='x'if face in['north','south']else'z')
  for v in [-1,1]:
   for yy in [y,y+1]:self.p(x+(v if face in['north','south']else 0),yy,z+(v if face in['west','east']else 0),'stripped_oak_log',axis='y')
  self.doors.append({'id':self.id+'.door.'+str(len(self.doors)),'pos':[x,y,z],'lintel':[x,y+2,z],'facing':face})
 def sign(self,x,y,z,face,lines):
  self.p(x,y,z,'oak_wall_sign',facing=face)
  d={'id':n.String('minecraft:sign'),'is_waxed':n.Byte(1)}
  for side,txt in [('front_text',lines),('back_text',[])]:d[side]=n.Compound({'messages':n.List[n.String]([n.String(json.dumps({'text':t},ensure_ascii=False))for t in(txt+['']*4)[:4]]),'color':n.String('black'),'has_glowing_text':n.Byte(0)})
  self.bes[x,y,z]=n.Compound(d)
 def banner(self,x,y,z,color='blue'):
  self.p(x,y,z,color+'_wall_banner',facing='south');self.bes[x,y,z]=n.Compound({'id':n.String('minecraft:banner'),'patterns':n.List[n.Compound]([])})
 def kit(self,f=2):return InteriorKit(self.p,(0,f,0),self.id)
 def addkit(self,k):
  for q,d in k.block_entities.items():
   be=n.Compound({'id':n.String(d['id'])})
   if d['id']in ['minecraft:barrel','minecraft:furnace']:be['Items']=n.List[n.Compound]([])
   if d['id']=='minecraft:furnace':
    for v in ['BurnTime','CookTime','CookTimeTotal']:be[v]=n.Short(d[v])
    be['RecipesUsed']=n.Compound({})
   self.bes[q]=be
  self.groups.extend(k.components)
 def shell(self,wall='white_terracotta',open_shop=True,roof_axis='x'):
  w,d=self.w,self.d;top=2+self.levels*5
  for f in [2+5*i for i in range(self.levels)]:
   self.box((2,f,2),(w-2,f+1,d-2),'spruce_planks'if f==2 else'oak_planks')
   for lo,hi in [((2,f+1,2),(w-2,f+5,3)),((2,f+1,d-3),(w-2,f+5,d-2)),((2,f+1,2),(3,f+5,d-2)),((w-3,f+1,2),(w-2,f+5,d-2))]:self.box(lo,hi,wall)
   for x in [2,w//2,w-3]:
    for z in [2,d-3]:self.box((x,f+1,z),(x+1,f+5,z+1),'stripped_spruce_log',axis='y')
   for z in [2,d//2,d-3]:
    for x in [2,w-3]:self.box((x,f+1,z),(x+1,f+5,z+1),'stripped_oak_log',axis='y')
   for z in [2,d-3]:self.box((2,f+4,z),(w-2,f+5,z+1),'stripped_spruce_log',axis='x')
   for x in [2,w-3]:self.box((x,f+4,2),(x+1,f+5,d-2),'stripped_spruce_log',axis='z')
   for x in list(range(3,w//2-1))+list(range(w//2+2,w-3)):
    for y in [f+2,f+3]:self.p(x,y,d-3,'white_stained_glass_pane')
    if x%3==0:self.p(x,f+2,d-2,'dark_oak_trapdoor',facing='south',open=True)
   for z in [4,5,d-7,d-6]:
    for y in [f+2,f+3]:self.p(w-3,y,z,'white_stained_glass_pane')
   # Side-facing openings give the creek and alleys an inhabited elevation too.
   for z in [4,5,d-8,d-7]:
    for y in [f+2,f+3]:self.p(2,y,z,'white_stained_glass_pane')
   for z in [5,d-7]:self.p(1,f+2,z,'dark_oak_trapdoor',facing='west',open=True)
   for x in range(4,w-5):
    for y in [f+2,f+3]:self.p(x,y,2,'white_stained_glass_pane')
   for z in [6,d-5]:self.box((3,f+4,z),(w-3,f+5,z+1),'stripped_oak_log',axis='x')
   for x,z in [(5,6),(w-6,d-5)]:self.lamp(x,f+3,z)
  self.box((2,top,2),(w-2,top+1,d-2),'spruce_planks')
  # Roof axis changes at family/lot level; no per-block random damage.
  for x in range(0,w):
   for z in range(0,d-1):
    t=min(z,d-2-z)if roof_axis=='x'else min(x,w-1-x);y=top+t//2
    if t%2:self.p(x,y,z,'deepslate_tile_stairs',facing=('south'if z<(d-1)/2 else'north')if roof_axis=='x'else('east'if x<w/2 else'west'))
    else:self.p(x,y,z,'deepslate_tile_slab',type='bottom')
  if roof_axis=='x':
   zz=(d-2)//2;yy=top+zz//2+1
   for x in range(w):self.p(x,yy,zz,'polished_deepslate_slab',type='bottom')
  else:
   xx=w//2;yy=top+(w-1)//4+1
   for z in range(d-1):self.p(xx,yy,z,'polished_deepslate_slab',type='bottom')
  # Enclose the attic at the shell walls under both gable directions.
  for x in range(2,w-2):
   for z in [2,d-3]:
    t=min(z,d-2-z)if roof_axis=='x'else min(x,w-1-x)
    for y in range(top+1,top+t//2):self.p(x,y,z,wall)
  for x in [2,w-3]:
   for z in range(2,d-2):
    t=min(z,d-2-z)if roof_axis=='x'else min(x,w-1-x)
    for y in range(top+1,top+t//2):self.p(x,y,z,wall)
  for x in range(2,w-2):
   self.p(x,6,d-2,'deepslate_tile_stairs',facing='north');self.p(x,5,d-1,'deepslate_tile_slab',type='bottom')
  x=w//2
  if open_shop:
   self.box((x-1,3,d-3),(x+2,6,d-2),'air');self.banner(x-1,5,d-2);self.banner(x+1,5,d-2)
   for xx in [x-2,x+2]:self.box((xx,3,d-3),(xx+1,6,d-2),'stripped_oak_log',axis='y')
   for xx in range(3,x-2):
    self.p(xx,3,d-3,'oak_stairs',facing='north',half='top');self.box((xx,4,d-3),(xx+1,6,d-2),'air')
   # Each high curtain is supported by the existing facade head.
   for xx in [x-1,x+1]:self.p(xx,5,d-3,'stripped_spruce_log',axis='x')
  else:self.door(x,3,d-3)
  self.lamp(x+2,5,d-2)
  self.p(3,3,d-1,'terracotta');self.pot(3,4,d-1)
  self.p(w-4,3,d-1,'oak_slab',type='top');self.p(w-4,4,d-1,'red_carpet')
  self.sign(x,6,d-1,'south',[self.id,self.program])
  # Sign backing and entry pass remain separate.
  self.p(x,6,d-2,'spruce_planks')
  self.entry=[x,3,d-3];self.use('entry',x,d-4)
  if self.levels==2:
   for xx in range(4,w-4):self.p(xx,8,d-2,'oak_slab',type='top')
   self.pot(4,9,d-2);self.pot(w-5,9,d-2)

 def wc(self,x,z):
  # Compact screened service WC at rear right, floor stays continuous.
  self.box((x-1,3,z),(x,7,z+4),'white_terracotta');self.box((x,3,z+3),(self.w-2,7,z+4),'white_terracotta')
  self.door(x+1,3,z+3,wood='birch');self.p(x+1,3,z,'water_cauldron',level=3)
  self.p(x+2,3,z+1,'quartz_stairs',facing='south');self.p(x+2,4,z+1,'white_carpet')
  self.lamp(x+1,5,z+1);self.use('wc',x+1,z+2)

 def sofa(self,x,z,f=2,w=3):
  for xx in range(x,x+w):
   self.p(xx,f+1,z,'quartz_slab',type='bottom');self.p(xx,f+1,z+1,'white_wool');self.p(xx,f+2,z+1,'light_gray_carpet')
  for xx,face in [(x-1,'west'),(x+w,'east')]:self.p(xx,f+1,z,'dark_oak_trapdoor',facing=face,open=True)
  self.p(x+w+1,f+1,z,'barrel',facing='north');self.bes[x+w+1,f+1,z]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])});self.pot(x+w+1,f+2,z)

 def stairs(self):
  # Straight five-step flight; its headroom/upper opening is authored before furniture.
  for x in [3,4]:
   for z in range(10,16):
    for y in range(3,12):self.p(x,y,z,'air')
   for t in range(5):self.p(x,3+t,14-t,'spruce_stairs',facing='north')
  for z in range(11,16):self.p(5,8,z,'spruce_fence')
  for x in [3,4]:self.p(x,7,9,'oak_planks')
  path=[]
  for i in range(49):
   z=15.5-i*.125;delta=15-z;y=3 if z>=15 else min(8,3+math.ceil(delta*2)/2)
   path.append([3.5,y,z])
  self.stair_paths.append(path);self.use('stair_start',3,15);self.use('stair_landing',3,9,7)

def compact(id,program,seed,variant=0):
 m=Module(id,17,21,2,program,seed);m.shell(wall='white_terracotta'if variant%2==0 else'light_gray_terracotta',open_shop=program in ['仕立屋','小さな宿'],roof_axis='x'if variant%2==0 else'z');m.stairs();k=m.kit()
 m.wc(11,3)
 for x in range(6,10):m.barrel(x,3,3);m.p(x,5,3,'oak_slab',type='top')
 k.furnace(6,3);k.sink(9,3);m.pot(8,6,3);m.p(7,4,3,'flower_pot');m.use('kitchen',8,4)
 m.sofa(7,15);k.table(8,12,3,1,'living_table','oak',True);m.p(9,3,11,'brown_carpet');m.use('living',11,13)
 for x in [6,7]:m.p(x,3,7,'bookshelf');m.p(x,4,7,'bookshelf');m.p(x,5,7,'oak_slab',type='bottom')
 m.use('books',7,8)
 if program=='仕立屋':
  for x in range(7,11):
   for z in range(12,17):
    for y in [3,4]:m.p(x,y,z,'air')
  for x,col in [(7,'white_wool'),(8,'red_wool'),(9,'brown_wool')]:m.p(x,3,16,col);m.p(x,4,16,'oak_slab',type='bottom')
  k.table(7,12,3,2,'cutting_table','oak');m.p(7,4,12,'white_carpet');m.p(9,4,13,'flower_pot');m.p(6,3,15,'crafting_table')
 if program=='小さな宿':
  m.sign(8,5,17,'south',['客室','二階']);m.p(8,5,16,'spruce_planks')
 m.addkit(k);u=m.kit(7)
 for x in [8,11]:
  u.bed(x,6);m.p(x,8,4,'stripped_oak_log',axis='x');m.barrel(x-1,8,5);m.pot(x-1,9,5);m.use('bed'+str(x),x+1,6,7)
 for x in range(8,12):
  for z in [8,9]:m.p(x,8,z,'light_gray_carpet')
 u.cupboard(12,10,2);m.use('wardrobe',12,11,7)
 u.table(6,17,2,1,'desk','oak');u.chair(7,16,'south');m.p(6,9,17,'flower_pot');m.use('desk',6,16,7)
 m.sofa(8,15,7,3);u.table(9,12,2,1,'tea','oak',True);m.use('tea',11,13,7)
 m.lamp(9,10,6);m.lamp(9,10,14);m.addkit(u)
 return m

def single(id,program,seed,w=17,d=18,variant=0):
 m=Module(id,w,d,1,program,seed);m.shell(wall='white_terracotta'if variant%3 else'light_gray_terracotta',roof_axis='x'if variant%2 else'z');k=m.kit();m.wc(w-6,3)
 if program=='木葉湯':
  # Low contained basin, tiled coping and dry changing side.
  for x in range(3,9):
   for z in range(3,9):m.p(x,3,z,'polished_andesite')
  for x in range(4,8):
   for z in range(4,8):m.p(x,3,z,'water',level=0)
  for z in [4,6,8]:m.p(10,3,z,'water_cauldron',level=3)
  for x in range(4,8):m.barrel(x,3,11);m.p(x,4,11,'white_carpet')
  m.sofa(5,d-5,w=2);m.use('wash',9,6);m.use('changing',6,10);m.use('basin_edge',6,9)
 elif program=='文庫':
  k.shelf(3,3,w-10,3);m.use('back_books',5,4)
  for z in range(5,10):
   for y in [3,4]:m.p(3,y,z,'bookshelf')
  m.use('wall_books',4,7);k.table(6,8,3,1,'reading','oak');k.chair(6,10,'north');k.chair(8,10,'north');m.use('reading',7,10)
  k.counter(4,d-5,3);m.use('borrow',5,d-6);m.p(5,4,d-5,'flower_pot');m.pot(3,3,d-5)
 else:
  for x in range(3,w-8):
   m.barrel(x,3,3);m.p(x,5,3,'oak_slab',type='top');m.p(x,6,3,'flower_pot')
  m.use('stock',5,4);k.counter(4,8,min(5,w-9));m.use('serve',6,10);m.use('work',6,7)
  k.table(4,d-5,2,1,'side_table','oak');k.chair(3,d-5,'east');m.use('side_table',6,d-5)
  if program in ['茶と菓子','干物店']:
   k.furnace(3,6);k.sink(3,7);k.cake(5,4,8);m.p(7,4,8,'flower_pot');m.p(4,4,3,'sea_pickle',pickles=3,waterlogged=False)
  elif program=='八百屋':
   for x in [4,5,6]:m.p(x,4,8,'melon'if x%2 else'pumpkin');m.p(x,4,3,'hay_block',axis='y')
  elif program=='花屋':
   for x in [4,5,6,7]:m.pot(x,4,8)
   for z in [5,6,7]:m.p(3,3,z,'terracotta');m.pot(3,4,z)
  elif program=='木工房':
   for x in [4,6]:m.p(x,4,8,'crafting_table')
   for z in [5,6]:m.p(3,3,z,'stripped_spruce_log',axis='z');m.p(3,4,z,'oak_trapdoor',half='top',open=False)
  elif program=='陶器店':
   for x in range(4,8):m.p(x,4,8,'flower_pot')
   for z in [5,6,7]:m.p(3,3,z,'terracotta');m.p(3,4,z,'flower_pot')
  m.pot(w-4,3,d-5)
 m.addkit(k);m.lamp(w-6,5,d-6)
 return m

def machiya(id,program,seed,variant=0):
 p=ROOT/'input/Machiya08_M08.nbt';b=load_build(p,Limits(cells=1000000,nodes=3000000));f=n.load(p);sp=json.loads((ROOT/'input/Machiya08_spec.json').read_text());owners=json.loads((ROOT/'input/Machiya08_owners.json').read_text())
 m=Module(id,21,24,2,program,seed);offset=(-5,0,-2)
 def q(v):return tuple(v[i]+offset[i]for i in range(3))
 for pos,st in b.blocks.items():
  if 5<=pos[0]<=25 and 2<=pos[2]<=25 and pos[1]>=2 and not owners.get(','.join(map(str,pos)),'').startswith('site.')and st!='minecraft:air':m.blocks[q(pos)]=st
 for e in f['blocks']:
  pos=tuple(map(int,e['pos']))
  if 'nbt'in e and q(pos)in m.blocks:m.bes[q(pos)]=copy.deepcopy(e['nbt'])
 for e in f['entities']:
  ent=copy.deepcopy(e['nbt']);pos=q(list(map(float,ent['Pos'])));ent['Pos']=n.List[n.Double](map(n.Double,pos))
  for i,key in enumerate(['TileX','TileY','TileZ']):ent[key]=n.Int(int(ent[key])+offset[i])
  uid=uuid.uuid5(uuid.NAMESPACE_URL,id+str(ent['UUID']));ent['UUID']=n.IntArray([int.from_bytes(uid.bytes[i:i+4],'big',signed=True)for i in range(0,16,4)]);m.entities.append(ent)
 for d in sp['doors']:m.doors.append({**d,'id':id+'.'+d['id'],'pos':q(d['pos']),'lintel':q(d['lintel'])})
 for u in sp['use_points']:
  if u['id']=='G.front_waiting':continue
  m.uses.append({**u,'id':id+'.'+u['id'],'pos':q(u['pos'])})
 for l in sp['lights']:m.lights.append({'position':q(l['position']),'support':q(l['support'])})
 # Source stairs traced at fractional positions; actual support is computed in the audit.
 path=[[3.5,0,14.5-i*.125]for i in range(33)]+[[3.5+i*.125,0,10.5]for i in range(25)]+[[6.5,0,10.5+i*.125]for i in range(33)]
 m.stair_paths=[path];m.entry=list(q([16,3,22]))
 m.sign(5,6,22,'south',[program,id]);m.p(5,6,21,'spruce_planks')
 if program in ['古本と茶','米と雑貨']:
  # Preserve seating and complete back-of-house, change a real wall bay to program storage.
  for x in [3,4,5]:
   for y in [3,4,5]:m.p(x,y,16,'bookshelf'if program=='古本と茶'else'spruce_planks')
  if program=='米と雑貨':
   for x in [3,4,5]:m.barrel(x,3,16);m.p(x,4,16,'hay_block',axis='y')
  m.use('display',6,16)
  # Any source approach intersecting changed shelf is removed in favor of the new bay approach.
 # Vary curtain colour per entire building, while preserving attachment and opening.
 if variant%2:
  for pos,st in list(m.blocks.items()):
   if st.startswith('minecraft:blue_wall_banner'):m.blocks[pos]=st.replace('blue_wall_banner','purple_wall_banner')
 if variant in [1,2]:
  for pos,st in list(m.blocks.items()):
   if st=='minecraft:white_terracotta':m.blocks[pos]='minecraft:light_gray_terracotta'if variant==1 else'minecraft:white_terracotta'
 return m
