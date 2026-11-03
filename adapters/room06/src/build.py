from pathlib import Path
import sys,json,gzip,io,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states,japanese_detail_states,corner_states
from detail_lab import states
from hafusion.classical import Builder
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build,Limits
from furniture_detail_kit import FurnitureDetailKit
import nbtlib as n
mode=sys.argv[1];assert mode in ('before','after')
O=ROOT/'runs'/mode;O.mkdir(parents=True,exist_ok=True)
B=Builder((30,8,30));bes={};components=[];rooms=[]
for i,(ox,oz,title) in enumerate([(1,1,'木框软垫起居组'),(16,1,'卧室床头组'),(1,16,'紧凑木作厨房'),(16,16,'日式食铺吧台')]):
 k=FurnitureDetailKit(B.put,(ox,1,oz),f'R{i+1}')
 def p(x,y,z,name,part='finish',**props):return k.put(x,y,z,states.make(name,**{k:str(v).lower() for k,v in props.items()}),part)
 def box(lo,hi,name,part='finish',**props):
  for x in range(lo[0],hi[0]):
   for y in range(lo[1],hi[1]):
    for z in range(lo[2],hi[2]):p(x,y,z,name,part,**props)
 box((0,0,0),(12,1,12),'oak_planks' if i!=1 else 'light_gray_concrete','floor')
 box((0,1,0),(12,5,1),'white_terracotta','northwall')
 box((0,1,0),(1,5,12),'white_terracotta','westwall')
 box((11,1,0),(12,5,12),'white_terracotta','eastwall')
 box((0,1,11),(12,5,12),'white_terracotta','southwall')
 box((5,1,11),(7,4,12),'air','doorway')
 box((0,5,0),(12,6,12),'spruce_planks' if i>1 else 'white_concrete','ceiling')
 for x in [3,8]:p(x,5,6,'glowstone' if i>1 else 'sea_lantern','flushlight')
 for z in range(4,8):
  for y in [2,3]:p(11,y,z,'white_stained_glass_pane','window')
 if mode=='before':
  if i==0:
   for x in [3,4,5]:k.chair(x,3,'south',id='placeholder_sofa')
   k.table(4,6,3,1,low=True);k.barrel(8,1,2);k.potted(8,2,2)
  elif i==1:k.bed(4,3);k.bed(5,3);k.barrel(8,1,2);k.potted(8,2,2)
  elif i==2:k.furnace(3,1);k.sink(5,1);k.barrel(7,1,1);k.table(4,6,3,1);k.chair(4,7)
  else:
   k.counter(3,4,5)
   for x in [3,5,7]:k.chair(x,6,'north')
   k.furnace(3,1);k.barrel(7,1,1)
 else:
  # The same shell/camera as before. Detail is authored, never random filler.
  if i==0:
   k.framed_daybed(3,3)
   k.mixed_cabinet(6,1)
   k.table(3,6,3,1,id='coffee',material='oak',low=True)
   p(6,1,6,'oak_stairs','side_tray',facing='west',half='top')
   p(6,2,6,'flower_pot','cup')
   for x in range(2,8):
    for z in range(5,9):
     if z!=6:p(x,1,z,'light_gray_carpet','rug')
   # One framed armchair, distinct from daybed; thin sides bound the seat.
   p(8,1,7,'quartz_stairs','armchair',facing='east')
   k.panel(8,1,6,'north','armchair_side');k.panel(8,1,8,'south','armchair_side')
   p(1,1,2,'oak_stairs','side_table',facing='west',half='top')
   p(1,2,2,'lantern','side_lamp',hanging=False)
   p(2,4,1,'oak_slab','wall_shelf',type='top');p(3,4,1,'oak_slab','wall_shelf',type='top')
   # Deliberately no plant in every corner.
  elif i==1:
   k.bed_wall(4,3)
   for x in [8,9]:
    for y in [1,2,3]:p(x,y,1,'spruce_planks','wardrobe')
    for y in [1,2,3]:k.panel(x,y,2,'south','wardrobe_front')
   k.barrel(1,1,7,'east',id='linen_storage');k.barrel(1,2,7,'east',id='linen_storage')
   for z in [3,8]:
    for y in [2,3,4]:k.panel(10,y,z,'east','curtain_slat','dark_oak')
   # Writing corner, rather than identical end tables all around the bed.
   k.table(7,8,3,1,id='desk',material='oak');k.chair(8,9,'north','oak','desk_chair')
   p(9,2,8,'lantern','desk_lamp',hanging=False)
  elif i==2:
   k.kitchen_band(2,1)
   for x in [2,8]:box((x,1,0),(x+1,5,1),'stripped_spruce_log','beam')
   for x in range(1,10):p(x,4,3,'stripped_spruce_log','crossbeam',axis='x')
   p(5,3,3,'lantern','task_light',hanging=True)
   k.table(3,6,4,2,id='worktable',material='oak');k.cake(3,2,6,id='table_food')
   k.chair(3,8,'north','oak','seat_a');k.chair(6,8,'north','oak','seat_b')
   for x in [3,6]:
    k.panel(x-1,1,8,'west','seat_side');k.panel(x+1,1,8,'east','seat_side')
   for x in range(2,9):
    for z in range(2,5):p(x,0,z,'white_concrete' if (x+z)%2 else 'gray_concrete','tile_floor')
   k.barrel(1,1,9,'east',id='pantry');k.barrel(1,2,9,'east',id='pantry')
  else:
   # Residential Japanese / shop recipes stay separate. This is a food-service study.
   k.kitchen_band(2,1,id='back_work')
   k.counter(2,5,7,id='customer_counter',material='spruce_planks')
   for x in [3,5,7]:
    p(x,1,7,'oak_stairs','stool',facing='north',half='top')
    k.panel(x,1,8,'south','stool_back')
   for x in [3,7]:p(x,2,5,'flower_pot','cup')
   # Customer/staff lanes remain distinct: z=7 vs z=3..4, opening at x=9.
   for x in range(2,9):p(x,4,5,'stripped_spruce_log','header',axis='x')
   for x in [2,8]:
    for y in [1,2,3]:p(x,y,5,'stripped_spruce_log','endpost')
   for x in range(2,9):p(x,3,4,'stripped_spruce_log','banner_mount',axis='x')
   for x in [3,5,7]:p(x,3,5,'blue_wall_banner','noren',facing='south');bes[(ox+x,4,oz+5)]={'id':'minecraft:banner'}
   for x in [3,7]:p(x,3,3,'lantern','task_lamp',hanging=True);p(x,4,3,'spruce_planks','lamp_mount')
   # Entrance service ledge and a single seasonal plant.
   k.barrel(9,1,9,'west',id='entry_store');k.potted(9,2,9,id='entry_plant')
 components+=k.components;bes.update(k.block_entities)
 rooms.append(dict(id=f'R{i+1}',title=title,origin=[ox,1,oz],bounds=[ox,oz,ox+12,oz+12],entry=[ox+5,2,oz+11],floor_y=1))
B.finish();src=O/'InteriorDetail05.nbt';export_structure(B.s,src,include_air=True);f=n.load(src)
for block in f['blocks']:
 pos=tuple(map(int,block['pos']))
 if pos not in bes:continue
 d=bes[pos];be=n.Compound({'id':n.String(d['id'])})
 if d['id'] in ['minecraft:barrel','minecraft:furnace']:be['Items']=n.List[n.Compound]([])
 if d['id']=='minecraft:furnace':
  for key in ['BurnTime','CookTime','CookTimeTotal']:be[key]=n.Short(d[key])
  be['RecipesUsed']=n.Compound({})
 if d['id']=='minecraft:banner':be['patterns']=n.List[n.Compound]([])
 block['nbt']=be
buf=io.BytesIO();f.write(buf);src.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
b=load_build(src,Limits(cells=1000000,nodes=5000000));assert {p:s for p,s in b.blocks.items() if s!='minecraft:air'}==B.s.blocks
spec=dict(case_id='InteriorDetail05',mode=mode,rooms=rooms,components=components,size_xyz=list(B.s.size),non_air=len(B.s.blocks),source_nbt_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),verification={'nbt_exact':True,'game':'pending','user_aesthetic':'pending','Corner01':'needs_revision'},dependencies='Java 1.21.1 vanilla block study; no texture pack required; previews approximate')
(O/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2));print(mode,len(B.s.blocks))
