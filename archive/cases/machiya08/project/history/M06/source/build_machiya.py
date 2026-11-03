"""Machiya08: original Japanese-style shop-house. Bounded case adapter, not a universal solver."""
from pathlib import Path
import sys,json,hashlib,random,gzip,io,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from detail_lab import states as S
from hafusion.classical import Builder
from vendor.voxel_core import export_structure,parse_state
from vendor.inspect_build import load_build,Limits
from interior_kit import InteriorKit
import nbtlib as n
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--seed',type=int,default=1145);a=ap.parse_args();O=ROOT/'runs'/a.run;O.mkdir(parents=True,exist_ok=False)
B=Builder((34,21,34));bes={};doors=[];uses=[];plants=[];lights=[];floors=[2,7];rooms=[]
def rng(id):return random.Random(int(hashlib.sha256(f'machiya08.1|{a.seed}|{id}'.encode()).hexdigest()[:16],16))
def p(x,y,z,name,owner,**pr):B.put(x,y,z,S.make(name,**{k:str(v).lower() for k,v in pr.items()})if not name.startswith('minecraft:')else name,owner)
def box(lo,hi,name,owner,**pr):
 for x in range(lo[0],hi[0]):
  for y in range(lo[1],hi[1]):
   for z in range(lo[2],hi[2]):p(x,y,z,name,owner,**pr)
def use(id,x,f,z):uses.append({'id':id,'pos':[x,f+1,z],'floor_block_y':f})
def door(x,f,z,face,id,wood='oak',hinge='left'):
 for yy,half in [(f+1,'lower'),(f+2,'upper')]:p(x,yy,z,wood+'_door',id,facing=face,half=half,hinge=hinge)
 p(x,f+3,z,'stripped_spruce_log',id+'.lintel',axis='x'if face in ['north','south']else'z');doors.append({'id':id,'pos':[x,f+1,z],'facing':face,'lintel':[x,f+3,z]})
def pot(x,y,z,id):
 st=rng(id).choice(['potted_fern','potted_bamboo','potted_azalea_bush','potted_flowering_azalea_bush']);p(x,y,z,st,'plant.'+id);plants.append({'id':id,'anchor':[x,y,z],'support':[x,y-1,z],'state':st})
def lantern(x,y,z,id):p(x,y,z,'lantern',id,hanging=True);lights.append({'id':id,'position':[x,y,z],'support':[x,y+1,z]})
def banner(x,y,z,face,color,id):p(x,y,z,color+'_wall_banner',id,facing=face);bes[x,y,z]=n.Compound({'id':n.String('minecraft:banner'),'patterns':n.List[n.Compound]([])})
def sign(x,y,z,face,lines,id):
 p(x,y,z,'oak_wall_sign',id,facing=face);d={'id':n.String('minecraft:sign'),'is_waxed':n.Byte(1)}
 for side,ls in [('front_text',lines),('back_text',['']*4)]:d[side]=n.Compound({'messages':n.List[n.String]([n.String(json.dumps({'text':t},ensure_ascii=False))for t in ls]),'color':n.String('black'),'has_glowing_text':n.Byte(0)})
 bes[x,y,z]=n.Compound(d)
def panel(x,y,z,face,id):p(x,y,z,'dark_oak_trapdoor',id,facing=face,open=True)
# Small street-corner base; exterior public way remains continuous.
box((0,0,0),(34,2,34),'dirt','site.base');box((0,2,0),(34,3,34),'smooth_stone','site.paving')
box((0,2,28),(34,3,34),'gray_concrete','site.road');box((29,2,0),(34,3,34),'gray_concrete','site.road')
for x in range(34):p(x,2,27,'polished_andesite','site.gutter')
for z in range(28):p(28,2,z,'polished_andesite','site.gutter')
for x in [2,8,14,20,26]:box((x,2,31),(x+3,3,32),'white_concrete','site.mark')
for z in [4,10,16,22]:box((31,2,z),(32,3,z+3),'white_concrete','site.mark')
# Timber frame, plaster infill, low plank base and one timber upper-floor separator.
for f in floors:
 box((7,f,7),(24,f+1,23),'spruce_planks'if f==2 else'oak_planks','floor.'+str(f))
 for lo,hi in [((7,f+1,7),(24,f+5,8)),((7,f+1,22),(24,f+5,23)),((7,f+1,7),(8,f+5,23)),((23,f+1,7),(24,f+5,23))]:box(lo,hi,'white_terracotta','shell.plaster')
 for x in [7,13,18,23]:
  for z in [7,22]:box((x,f+1,z),(x+1,f+5,z+1),'stripped_spruce_log','frame.post',axis='y')
 for z in [7,12,17,22]:
  for x in [7,23]:box((x,f+1,z),(x+1,f+5,z+1),'stripped_spruce_log','frame.post',axis='y')
 for y in [f+1,f+4]:
  for z in [7,22]:box((7,y,z),(24,y+1,z+1),'spruce_planks'if y==f+1 else'stripped_spruce_log','frame.horizontal',**({}if y==f+1 else{'axis':'x'}))
  for x in [7,23]:box((x,y,7),(x+1,y+1,23),'spruce_planks'if y==f+1 else'stripped_spruce_log','frame.horizontal',**({}if y==f+1 else{'axis':'z'}))
# First-floor visible beams below the upper floor and ceiling beneath the roof.
box((7,12,7),(24,13,23),'spruce_planks','ceiling.upper')
for y in [6,11]:
 for z in [8,13,18,21]:box((8,y,z),(23,y+1,z+1),'stripped_spruce_log','ceiling.beam',axis='x')
# Exterior windows: recessed pale pane, frame posts, projecting thin lattice rather than fences everywhere.
for f in floors:
 for xs in [[9,10,11],[19,20,21]]:
  for x in xs:
   for y in [f+2,f+3]:p(x,y,22,'white_stained_glass_pane','window.front')
   panel(x,f+2,23,'south','lattice.front')
  for x in [xs[0]-1,xs[-1]+1]:box((x,f+1,22),(x+1,f+4,23),'stripped_oak_log','window.jamb',axis='y')
 for z in [9,10,14,15]:
  for y in [f+2,f+3]:p(23,y,z,'white_stained_glass_pane','window.side')
  panel(24,f+2,z,'east','lattice.side')
 for x in [14,15,20,21]:
  for y in [f+2,f+3]:p(x,y,7,'white_stained_glass_pane','window.garden')
 for z in [10,11]:
  for y in [f+2,f+3]:p(7,y,z,'white_stained_glass_pane','window.stair')
# Stair enclosure and common landing. Ground and upper entrance remain aligned.
for f in floors:
 box((13,f+1,8),(14,f+5,18),'white_terracotta','core.partition');box((7,f+1,17),(14,f+5,18),'white_terracotta','core.front')
 door(11,f,17,'south','stairs.entry.'+str(f),'birch')
 lantern(10,f+3,8,'stairs.light.'+str(f))
 use('stairs.start.'+str(f),8,f,16)
for ff in floors:
 for xx in [7,10,12,13]:box((xx,ff+1,17),(xx+1,ff+5,18),'stripped_oak_log','core.front_posts',axis='y')
# Ground kitchen (west of bathroom) and a screened WC at the rear right.
box((19,3,8),(20,7,13),'white_terracotta','bath.west');box((19,3,12),(24,7,13),'white_terracotta','bath.front');door(21,2,12,'south','bath.door','birch')
box((14,3,13),(19,6,14),'spruce_planks','kitchen.low_partition');door(17,2,13,'south','kitchen.pass','birch')
for xx in [14,15,16]:p(xx,5,13,'bookshelf','kitchen.back_shelf')
# Primary entrance frame is exactly in the facade plane; side entrance offers a second shop approach.
for x in [15,17]:box((x,3,22),(x+1,6,23),'stripped_oak_log','entry.jamb',axis='y')
door(16,2,22,'south','entry.main');door(23,2,19,'east','entry.side');door(15,2,7,'north','entry.garden','birch')
# Low secondary tiled eave, visibly supported rafters and thin roof edge.
for z,y in [(23,7),(24,7),(25,6)]:
 for x in range(6,25):p(x,y,z,'deepslate_tile_stairs','eave.lower.tile',facing='north')
for x in [7,10,13,16,19,22,24]:
 p(x,6,23,'oak_slab','eave.rafter',type='top');p(x,6,24,'oak_slab','eave.rafter_tip',type='top')
# Side eave turns the corner without a second grand roof.
for x in [24,25]:
 for z in range(13,23):p(x,7 if x==24 else 6,z,'deepslate_tile_stairs','eave.side',facing='west')
for z in [14,17,20,22]:p(24,6,z,'oak_slab','eave.side_rafter',type='top')
# Main simple gable, ridge along X; half-step slope with two- to three-block overhang.
for z in range(5,26):
 inset=min(z-5,25-z);y=12+inset//2
 for x in range(5,26):
  if inset%2:p(x,y,z,'deepslate_tile_stairs','roof.slope',facing='south'if z<15 else'north')
  else:p(x,y,z,'deepslate_tile_slab','roof.slope',type='bottom')
 for x in [7,23]:
  for yy in range(13,y):p(x,yy,z,'white_terracotta','gable.infill')
for x in range(5,26):p(x,17,15,'deepslate_bricks','roof.ridge')
for x in [7,10,13,16,19,22,24]:
 for z in [5,6,24,25]:p(x,11,z,'oak_slab','roof.rafter_end',type='top')
for z in [6,24]:box((7,11,z),(24,12,z+1),'stripped_oak_log','roof.eave_beam',axis='x')
# Lower shop front: sign / split noren / recessed counter, then grouped ground props.
box((14,6,23),(19,7,24),'spruce_planks','shop.sign_back');sign(16,6,24,'south',['日和小食','酒とごはん','',''],'shop.name')
for x in [15,17]:banner(x,5,23,'south','blue','shop.noren')
for x in [13,19]:p(x,6,24,'stripped_oak_log','entry.light_support',axis='z');lantern(x,5,24,'entry.lantern.'+str(x))
p(9,3,24,'barrel','front.supply',facing='south',open=False);bes[9,3,24]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])});pot(9,4,24,'front.high')
p(10,3,25,'terracotta','front.low_base');pot(10,4,25,'front.low');p(8,3,25,'oak_slab','front.bench',type='bottom')
p(21,3,24,'spruce_planks','front.menu_base');sign(21,4,24,'south',['本日のおすすめ','焼き魚 · 小鉢','温かいお茶',''],'front.menu')
# Sign requires a real rear support, grouped deliberately at right jamb.
p(21,4,23,'spruce_planks','front.menu_support')
for y in range(3,7):p(6,y,25,'chain','front.rain_chain',axis='y')
p(6,7,25,'deepslate_tile_slab','front.rain_chain_mount',type='bottom')
p(6,2,25,'water_cauldron','front.rain_basin',level=3)
# Ground furniture: cooking -> prep -> serving, with three counter stools and two small table groups.
K=InteriorKit(B.put,(0,2,0),'shop')
K.furnace(14,8,'stove');K.sink(16,8,'sink');p(17,3,8,'crafting_table','kitchen.prep');K.barrel(18,1,8,'south','stock')
for x in [14,16,18]:p(x,5,8,'spruce_planks','kitchen.upper');panel(x,5,9,'south','kitchen.cabinet_front')
p(14,5,9,'polished_andesite_slab','kitchen.hood',type='top')
for x in [14,15,16]:p(x,3,14,'spruce_stairs'if x in [14,16]else'spruce_slab','bar.counter',**({'half':'top','facing':'east'if x==14 else'west'}if x in [14,16]else{'type':'top'}));p(x,3,15,'oak_trapdoor','bar.counter_edge',facing='south',open=True)
for z in [14,15,16,17]:p(18,3,z,'spruce_planks','bar.return')
K.barrel(18,1,16,'west','bar.under_storage');use('G.bar_storage',17,2,16)
for x in [14,16]:p(x,4,14,'flower_pot','bar.cups')
p(15,4,14,'cake','bar.food',bites=3)
for x in [14,15,16]:K.chair(x,16,'north','spruce','bar.seat.'+str(x))
for x,z in [(10,19),(20,20)]:
 K.table(x,z,2,1,'table.'+str(x),'oak');p(x,4,z,'flower_pot','dining.cup');p(x+1,4,z,'cake','dining.small_plate',bites=4)
 K.chair(x-1,z,'east','spruce','dining.left.'+str(x));K.chair(x+2,z,'west','spruce','dining.right.'+str(x))
 panel(x-1,3,z-1,'north','dining.thin_arm');panel(x+2,3,z-1,'north','dining.thin_arm')
# A low waiting seat, shoe/storage wall and shelves make the entrance useful.
for z in [18,19]:p(8,3,z,'white_wool','waiting.back');p(9,3,z,'quartz_slab','waiting.cushion',type='bottom')
p(8,4,18,'light_gray_carpet','waiting.soft_top');K.barrel(12,1,21,'west','entry.shoes');pot(12,4,21,'entry.shoes')
p(22,3,16,'oak_planks','service.cabinet');K.barrel(22,2,16,'west','service.upper');p(22,5,16,'oak_slab','service.cap',type='top');pot(22,4,17,'service.plant')
p(22,3,17,'oak_planks','service.plant_stand')
# WC: opaque walls, basin, decorative toilet and ventilation window.
p(20,3,9,'water_cauldron','bath.sink',level=3);p(22,3,9,'quartz_stairs','bath.toilet',facing='north');panel(22,4,8,'north','bath.back');p(20,4,8,'white_stained_glass','bath.mirror')
for x,z in [(16,10),(21,10),(16,18),(10,21),(21,21)]:lantern(x,5,z,'shop.lantern.'+str(x)+'.'+str(z));p(x,6,z,'stripped_spruce_log','shop.light_mount',axis='x')
for id,x,z in [('main',16,21),('side',22,19),('garden',15,8),('stove',14,9),('sink',16,9),('stock',18,9),('counter',17,15),('counter_customer',15,17),('table_west',10,20),('table_east',20,21),('return',21,16),('wc_sink',20,10),('wc_toilet',22,10)]:use('G.'+id,x,2,z)
# Upper floor: one framed bedroom partition, lounge / tea / study, alcove and balcony window.
box((14,8,15),(23,12,16),'white_terracotta','upper.bedroom_partition');door(17,7,15,'south','bedroom.door','birch')
for x in [14,15,19,20,21,22]:
 for y in [9,10]:p(x,y,15,'white_stained_glass_pane','upper.shoji_screen')
for x in [14,18,22]:box((x,8,15),(x+1,12,16),'stripped_oak_log','upper.screen_post',axis='y')
U=InteriorKit(B.put,(0,7,0),'home');U.bed(16,10,'bed.left');U.bed(17,10,'bed.right')
for x in [16,17]:p(x,8,8,'oak_planks','bed.headboard');p(x,9,8,'oak_slab','bed.headboard_cap',type='bottom')
U.barrel(15,1,9,'south','bedside');p(15,9,9,'lantern','bedside.lamp',hanging=False);lights.append({'id':'bedside','position':[15,9,9],'support':[15,8,9]})
for z in [9,10]:p(21,8,z,'spruce_planks','wardrobe.lower');U.barrel(21,2,z,'west','wardrobe');p(21,10,z,'oak_slab','wardrobe.cap',type='top')
U.table(20,13,3,1,'window_desk','oak');U.chair(21,12,'south','spruce','desk.seat');pot(22,9,13,'desk');p(20,9,13,'flower_pot','desk.cup');p(20,10,14,'bookshelf','desk.wall_books');p(20,9,14,'oak_slab','desk.shelf_support',type='top')
# Low tea room has woven-floor intent, timber borders, cushions and a slim sofa at the window.
for x in range(14,23):
 for z in range(17,22):
  p(x,7,z,'oak_planks','living.timber_floor');p(x,8,z,'brown_carpet'if x in [14,22]or z in [17,21]else'white_carpet','living.mat_intent')
U.table(17,19,2,1,'tea_table',material='oak',low=True)
for x,z in [(16,19),(19,19),(17,18),(18,20)]:p(x,8,z,'white_carpet','living.floor_cushion')
for z in [19,20]:p(22,8,z,'white_wool','sofa.back');p(21,8,z,'quartz_slab','sofa.cushion',type='bottom');p(22,9,z,'light_gray_carpet','sofa.back_trim')
for z,face in [(18,'north'),(21,'south')]:panel(21,8,z,face,'sofa.arm')
p(14,8,21,'oak_planks','alcove.platform');pot(14,9,21,'alcove');banner(14,10,21,'north','white','alcove.scroll')
p(19,8,20,'flower_pot','living.floor_tea_cup')
U.barrel(18,1,9,'south','bed.second_side');pot(18,9,9,'bedside')
for xx in [15,16,17,18]:
 for zz in [11,12]:p(xx,8,zz,'white_carpet','bed.foot_mat')
banner(22,10,8,'south','white','bed.curtain')
# A narrow study/reading nook beside the stair has its own group, not a second empty hall.
U.table(8,19,2,1,'study_table','oak');U.chair(8,20,'north','spruce','study_chair');p(8,9,19,'flower_pot','study.cup');pot(9,9,19,'study.plant')
for x in [8,9]:p(x,8,21,'bookshelf','study.lower_books');p(x,9,21,'oak_slab','study.book_cap',type='top')
U.barrel(12,1,21,'west','study.closed_storage');p(12,9,21,'white_carpet','study.folded_linen')
for x,z in [(17,11),(21,11),(17,18),(10,18),(20,21)]:p(x,11,z,'stripped_spruce_log','home.light_mount',axis='x');lantern(x,10,z,'home.lantern.'+str(x)+'.'+str(z))
for id,x,z in [('landing',11,16),('bedroom_entry',17,14),('bed_left',15,10),('bed_right',18,10),('wardrobe',20,10),('desk',20,12),('sofa',20,20),('tea',19,19),('study',11,19),('books',9,20),('storage',11,21)]:use('U.'+id,x,7,z)
# Garden: a small planted end-view, ground/low/vertical layers and a clear path from the rear door.
for x in range(7,24):p(x,3,2,'spruce_fence','garden.boundary')
for z in range(3,7):
 for x in [7,23]:p(x,3,z,'spruce_fence','garden.boundary')
box((8,2,3),(13,3,6),'moss_block','garden.ground');box((14,2,5),(22,3,7),'oak_planks','garden.engawa')
for x,z in [(9,4),(11,3),(12,5)]:
 p(x,2,z,'dirt','plant.garden.soil');h=rng(f'garden.{x}.{z}').choice([2,3,4])
 for dy in range(h):p(x,3+dy,z,'bamboo','plant.garden.tall',age=1,leaves='large'if dy==h-1 else'small',stage=1)
 plants.append({'id':f'garden.{x}.{z}','anchor':[x,3,z],'height':h,'support':[x,2,z]})
p(10,3,5,'mossy_stone_brick_slab'if False else'stone_brick_slab','garden.rock',type='bottom');p(20,3,4,'water_cauldron','garden.basin',level=3)
p(21,3,3,'terracotta','garden.pot_base');pot(21,4,3,'garden.low');p(19,3,3,'stone_bricks','garden.lamp_base');p(19,4,3,'lantern','garden.lamp',hanging=False);lights.append({'id':'garden','position':[19,4,3],'support':[19,3,3]})
use('garden.path',17,2,5);use('garden.basin',20,2,5)
# Sparse front and lounge potted groups soften the edges without occupying activity points.
p(22,7,18,'dirt','plant.sofa.soil');h=rng('sofa.tall').choice([2,3])
for dy in range(h):p(22,8+dy,18,'bamboo','plant.sofa.tall',age=1,leaves='large'if dy==h-1 else'small',stage=1)
plants.append({'id':'sofa.tall','anchor':[22,8,18],'support':[22,7,18],'height':h})
# Protected two-flight stair, completed after the upper slab. Rise five blocks.
box((8,7,10),(13,8,16),'air','core.floor_void')
for t in range(3):
 for x in [8,9]:p(x,3+t,15-t,'spruce_stairs','core.lower',facing='north')
box((8,5,11),(13,6,13),'spruce_planks','core.midlanding')
for t in range(2):
 for x in [11,12]:p(x,6+t,13+t,'spruce_stairs','core.upper',facing='south')
box((11,7,15),(13,8,17),'spruce_planks','core.landing')
for z in [13,14,15]:p(10,6,z,'spruce_fence','core.guard')
# Remove low decorative beam at this stair's overhead path; the load-bearing upper floor remains.
box((8,6,11),(13,7,14),'air','core.headroom')
# Restore stair pieces affected by that headroom volume only.
for x in [11,12]:p(x,6,13,'spruce_stairs','core.upper',facing='south')
# Stair top / study are joined by the framed opening at z17.
for kit in [K,U]:
 for q,d in kit.block_entities.items():
  be=n.Compound({'id':n.String(d['id'])})
  if d['id']in ['minecraft:barrel','minecraft:furnace']:be['Items']=n.List[n.Compound]([])
  if d['id']=='minecraft:furnace':
   for key in ['BurnTime','CookTime','CookTimeTotal']:be[key]=n.Short(d[key])
   be['RecipesUsed']=n.Compound({})
  bes[q]=be
# Resolve fence rails from final occupied neighbours, as distinct from preview-only posts.
for q,st in list(B.s.blocks.items()):
 name,pr=parse_state(st)
 if name.endswith('_fence'):
  for face,delta in S.DIRS.items():
   near=B.s.blocks.get(tuple(q[i]+delta[i]for i in range(3)),'minecraft:air');pr[face]=str(near.split('[')[0].endswith('_fence')or S.support_cube(near)).lower()
  p(*q,S.make(name,**pr),B.s.owners[q])
from izakaya_revision import refit
refit(globals())
from under_stair_revision import refit_under_stair
refit_under_stair(globals())
B.finish();src=O/'Machiya08.nbt';base=O/'geometry_base.nbt';export_structure(B.s,base,include_air=True);fn=n.load(base)
fn['entities']=n.List[n.Compound](art_entities)
for e in fn['blocks']:
 q=tuple(map(int,e['pos']))
 if q in bes:e['nbt']=n.Compound(bes[q])
buf=io.BytesIO();fn.write(buf);temp=O/'complete_structure.tmp';temp.write_bytes(gzip.compress(buf.getvalue(),mtime=0));temp.replace(src);base.unlink();rb=load_build(src,Limits(cells=2_000_000,nodes=6_000_000));assert {q:s for q,s in rb.blocks.items()if s!='minecraft:air'}==B.s.blocks
sp={'case_id':'Machiya08','run':a.run,'title':'日和小食 · 老式日式町屋','mainline':'HAF 0.4','seed':a.seed,'algorithm':'machiya08.1','size_xyz':list(B.s.size),'floor_blocks':floors,'building_bounds':[7,2,7,24,18,23],'doors':doors,'use_points':uses,'plants':plants,'lights':lights,'stairs':[{'floor':2,'rise':5,'id':'main_stair','lower_x':8.5,'upper_x':11.5,'start_z':16.5,'turn_z':12.5,'end_z':16.5}],'floor_starts':{'2':[16,24],'7':[11,16]},'rooms':[{'id':'shop','name':'居酒屋客席与吧台','floor':2,'bounds':[8,14,23,22]},{'id':'kitchen','name':'后厨','floor':2,'bounds':[14,8,19,13]},{'id':'bath','name':'卫浴','floor':2,'bounds':[20,8,23,12]},{'id':'bed','name':'起居卧室','floor':7,'bounds':[14,8,23,15]},{'id':'tea','name':'茶席与沙发','floor':7,'bounds':[14,16,23,22]},{'id':'study','name':'书桌与收纳','floor':7,'bounds':[8,18,13,22]}],'non_air':len(B.s.blocks),'block_entities':len(bes),'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'design_brief':{'route':'original inspired by previously recorded observations; not a Freedom replica','scope':'One 2-storey old Japanese-style shop-house, ground izakaya and upper residence, small rear courtyard','units':'Minecraft blocks; authored furniture-scale compromise, not measured historic machiya','coordinates':'+X east, +Z south, front south','capacity':'7 decorative dining positions (3 bar + 4 table), 2 actual beds','constraints':['same-plane door frames','full roof/ceilings on eye views','wood and white-plaster frame','layered eaves','fixed activity paths','plant groups with explicit support']},'reference_scope':'Re-read JapanDetail01 research record. No newly watched video; exact Freedom block recipes were not established by that record.','randomness':{'channels':['plant.<group>'],'fixed':['roof','windows','furniture','stairs','doors','lights'],'scope':'species and bamboo height only; authored asymmetric storefront arrangement is not randomized layout'},'status':{'game':'pending','aesthetic':'pending','prior_town_interiors':'needs_revision'},'limitations':['Original functional reinterpretation, not a measured reproduction','Tatami/shoji/bedding are vanilla material approximations','Seating, shower/toilet and cups are decorative; cups use flower pots','Offline textured models are not game footage; banner/sign/bed models approximate']}
sp.update(algorithm='machiya08.3-understair',paintings=paintings,entities=len(art_entities),refit_groups=refit_groups,under_stair=under_stair)
sp['design_brief']['capacity']='11 decorative dining places: 3 bar + 4 west booth + 4 east table; 2 actual beds'
sp['status']['previous_M03_first_floor']='needs_revision: user found sparse furnishings and underused walls/landing'
sp['limitations']+=['Sea pickles stand for grouped bottles; unlit candles for small table objects; not new gameplay objects','Paintings are actual vanilla entities; their persistence is checked offline, client behavior pending']
(O/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(O/'owners.json').write_text(json.dumps({','.join(map(str,q)):v for q,v in B.s.owners.items()}));print(json.dumps({k:sp[k]for k in ['run','non_air','block_entities','source_nbt_sha256']},ensure_ascii=False))
