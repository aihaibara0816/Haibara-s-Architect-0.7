from pathlib import Path
import sys,json,hashlib,random,gzip,io,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from detail_lab import states as S
from hafusion.classical import Builder
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build,Limits
from interior_kit import InteriorKit
import nbtlib as n
a=argparse.ArgumentParser();a.add_argument('run');a.add_argument('--seed',type=int,default=1145);a.add_argument('--without-plants',action='store_true');a=a.parse_args()
O=ROOT/'runs'/a.run;O.mkdir(parents=True,exist_ok=False)
B=Builder((18,9,20));K=InteriorKit(B.put,(0,2,0),'unit');bes=K.block_entities
def p(x,y,z,name,part,**props):B.put(x,y,z,S.make(name,**{k:str(v).lower() for k,v in props.items()}),part)
def box(lo,hi,name,part,**props):
 for x in range(lo[0],hi[0]):
  for y in range(lo[1],hi[1]):
   for z in range(lo[2],hi[2]):p(x,y,z,name,part,**props)
def panel(x,y,z,facing,part,wood='oak'):p(x,y,z,wood+'_trapdoor',part,facing=facing,half='bottom',open=True)
def point(id,x,z):return {'id':id,'pos':[x,3,z]}
uses=[];doors=[];plants=[];lights=[]
# Fixed shell, ground and finishes. World y offset +62 brings floor top to 65.
box((0,0,0),(18,2,20),'dirt','site.base')
box((0,2,0),(18,3,20),'smooth_stone','site.paving')
box((3,2,4),(13,3,14),'smooth_stone','unit.floor')
box((8,2,5),(12,3,8),'oak_planks','sleep.floor')
box((4,2,10),(7,3,13),'light_gray_concrete','bath.floor')
box((10,2,10),(12,3,13),'polished_andesite','kitchen.floor')
for lo,hi in [((3,3,4),(13,6,5)),((3,3,13),(13,6,14)),((3,3,4),(4,6,14)),((12,3,4),(13,6,14))]:box(lo,hi,'white_concrete','shell.wall')
# Low green tiled band: exterior identity carried from the urban-village vocabulary.
for x in range(3,13):p(x,3,13,'green_terracotta','facade.tile_band')
for z in range(4,14):p(12,3,z,'green_terracotta','facade.tile_band')
box((3,6,4),(13,7,14),'white_concrete','shell.ceiling')
box((3,7,4),(13,8,14),'smooth_stone','shell.upper_floor')
for x,z in [(6,8),(9,9),(5,11),(11,11)]:p(x,6,z,'sea_lantern','light.flush');lights.append([x,6,z])
for x in [5,6,7]:
 for y in [4,5]:p(x,y,4,'light_blue_stained_glass_pane','window.desk')
for z in [6,7]:
 for y in [4,5]:p(3,y,z,'glass_pane','window.sofa')
for z in [5,6]:
 for y in [4,5]:p(12,y,z,'light_blue_stained_glass_pane','window.sleep')
# Interior privacy wall; full-height leaf with its own lintel and frame.
box((3,3,9),(8,6,10),'white_concrete','bath.partition')
box((7,3,9),(8,6,14),'white_concrete','bath.partition')
def door(x,z,facing,id,material='birch',hinge='left'):
 K.door(x,z,id,material,facing,hinge)
 doors.append({'id':id,'pos':[x,3,z],'facing':facing,'frame_plane':z if facing in ['north','south'] else x,'leaf_plane':z if facing in ['north','south'] else x,'lintel':[x,5,z]})
door(9,13,'north','entry','oak','left');door(7,11,'east','bath','birch','right')
# Sofa: two seats, separate soft back, low seat, thin wooden arms, top cloth trim.
for z in [6,7]:
 p(4,3,z,'white_wool','sofa.upholstered_back');p(4,4,z,'light_gray_carpet','sofa.back_trim')
 p(5,3,z,'quartz_slab','sofa.low_cushion',type='bottom')
for z,face in [(5,'north'),(8,'south')]:panel(5,3,z,face,'sofa.thin_arm')
# Front remains open so the low cushion stays visible.
# Rug follows the seating group, with a low coffee tray and no floating tabletop props.
for x in [6,7,8]:
 for z in [7,8]:p(x,3,z,'light_gray_carpet' if x!=8 else 'brown_carpet','living.rug')
for z in [8]:p(7,3,z,'oak_slab','living.low_table',type='bottom')
uses += [point('sofa_front',6,8),point('coffee_side',8,8)]
# Three-wide desk with visible undercut supports, one wooden chair with side rail.
for x in [6,7,8]:p(x,3,5,'oak_stairs' if x in [6,8] else 'oak_slab','desk.surface',**({'facing':'east' if x==6 else 'west','half':'top'} if x in [6,8] else {'type':'top'}))
K.chair(7,6,'north','oak','desk_chair');panel(8,3,6,'east','desk.chair_side')
p(8,4,5,'lantern','desk.task_lamp',hanging=False);lights.append([8,4,5]);uses.append(point('desk_approach',8,6))
# Two actual beds, a designed headboard in the wall, a bedside surface.
K.bed(9,6,'sleep.left');K.bed(10,6,'sleep.right')
for x in [9,10]:
 p(x,3,4,'stripped_oak_log','sleep.headboard',axis='y');p(x,4,4,'oak_planks','sleep.headboard_cap')
 p(x,3,7,'white_carpet','sleep.foot_rug')
K.barrel(11,1,5,'south','sleep.bedside');p(11,4,5,'flower_pot','sleep.cup')
uses += [point('bed_left',8,6),point('bed_right',11,6),point('bedside',11,6)]
# Wardrobe: a closed portion and two accessible storage faces, no wall of barrels.
for z in [8]:
 p(11,3,z,'oak_planks','wardrobe.base');K.barrel(11,2,z,'west','wardrobe.storage');p(11,5,z,'oak_slab','wardrobe.cap',type='top')
uses += [point('wardrobe',10,8)]
# Compact kitchen on the east wall. Each appliance retains its west approach.
p(11,3,10,'water_cauldron','kitchen.sink',level=3)
p(11,3,11,'furnace','kitchen.stove',facing='west',lit=False);bes[(11,3,11)]={'id':'minecraft:furnace','BurnTime':0,'CookTime':0,'CookTimeTotal':200}
K.barrel(11,1,12,'west','kitchen.storage')
for z in [10,12]:
 p(11,5,z,'oak_planks','kitchen.upper');panel(10,5,z,'west','kitchen.upper_front')
p(11,5,11,'polished_andesite_slab','kitchen.hood',type='top')
p(11,3,9,'crafting_table','kitchen.prep');p(11,4,9,'flower_pot','kitchen.cup')
uses += [point('sink',10,10),point('stove',10,11),point('kitchen_storage',10,12),point('prep',10,9)]
p(7,4,10,'bookshelf','entry.inset_books')
# Entry shoes/keys cabinet and an asymmetrical decorative shelf.
K.barrel(8,1,12,'east','entry.shoes');uses.append(point('shoes',9,12))
p(8,5,12,'oak_slab','entry.shelf',type='top')
# Bathroom: real water basin; shower and toilet are explicitly decorative.
p(4,3,10,'water_cauldron','bath.basin',level=3)
p(4,4,9,'light_blue_stained_glass','bath.mirror');uses.append(point('bath_basin',5,10))
p(4,3,12,'quartz_stairs','bath.toilet',facing='south')
p(4,4,12,'iron_trapdoor','bath.toilet_back',facing='south',open=True);uses.append(point('bath_toilet',4,11))
p(6,5,12,'end_rod','bath.shower',facing='west');lights.append([6,5,12]);uses.append(point('shower',6,12))
p(5,3,12,'light_blue_stained_glass_pane','bath.splash_screen')
# Supported folded-curtain representation at window edges; real banners, no custom entity heads.
for x,z,facing in [(4,5,'south'),(11,5,'north')]:
 # First curtain hangs on the north wall. East bedside retains its cup and approach.
 if x==11:continue
 p(x,5,z,'white_wall_banner','curtain',facing=facing);bes[(x,5,z)]={'id':'minecraft:banner'}
# External tile patch, pipes, AC and an entry lamp tie this one room to an older village facade.
for z in [10,11]:
 for y in [4,5]:p(12,y,z,'polished_diorite','facade.repair_patch')
for y in range(3,8):p(13,y,11,'diorite_wall','facade.pipe')
p(13,5,8,'iron_block','facade.air_conditioner');panel(14,5,8,'east','facade.ac_grille','iron')
p(9,5,14,'lantern','entry.porch_light',hanging=True);p(9,6,14,'smooth_stone_slab','entry.canopy',type='top');lights.append([9,5,14])
for x in [8,10]:p(x,6,14,'smooth_stone_slab','entry.canopy',type='top')
for x in range(3,13):p(x,2,15,'polished_andesite','site.drain_edge')
# Reproducible plant groups: independent channels; fixed shell, furniture and lights.
def rng(group):return random.Random(int(hashlib.sha256(f'plant-0.1|{a.seed}|{group}'.encode()).hexdigest()[:16],16))
if not a.without_plants:
 r=rng('sofa_planter');height=r.choice([2,3]);p(4,2,8,'dirt','plant.sofa.soil')
 for y in range(3,3+height):p(4,y,8,'bamboo','plant.sofa.stem',age=1,leaves='large' if y==2+height else 'small',stage=1)
 plants.append({'id':'sofa_planter','anchor':[4,3,8],'height':height,'support':[4,2,8],'role':'沙发端部竖向绿植','bounds_xyz':[4,3,8,5,3+height,9]})
 for group,xyz,support in [('desk',(6,4,5),(6,3,5)),('entry',(8,4,12),(8,3,12))]:
  choice=rng(group).choice(['potted_fern','potted_azalea_bush','potted_flowering_azalea_bush','potted_bamboo']);p(*xyz,choice,'plant.'+group)
  plants.append({'id':group,'anchor':list(xyz),'support':list(support),'state':choice,'role':'窗边小盆' if group=='desk' else '入口柜面小盆','bounds_xyz':[*xyz,*[v+1 for v in xyz]]})
B.finish();src=O/'Room06.nbt';export_structure(B.s,src,include_air=True);f=n.load(src)
for block in f['blocks']:
 pos=tuple(map(int,block['pos']))
 if pos not in bes:continue
 d=bes[pos];be=n.Compound({'id':n.String(d['id'])})
 if d['id'] in ['minecraft:barrel','minecraft:furnace']:be['Items']=n.List[n.Compound]([])
 if d['id']=='minecraft:furnace':
  for k in ['BurnTime','CookTime','CookTimeTotal']:be[k]=n.Short(d[k])
  be['RecipesUsed']=n.Compound({})
 if d['id']=='minecraft:banner':be['patterns']=n.List[n.Compound]([])
 block['nbt']=be
buf=io.BytesIO();f.write(buf);src.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
rb=load_build(src,Limits(cells=1000000,nodes=3000000));assert {q:s for q,s in rb.blocks.items() if s!='minecraft:air'}==B.s.blocks
spec={'case_id':'Room06','run':a.run,'title':'榕角里 · 单间试住','mainline':'HAF 0.4','rules':'0.4.3','route':'authored room sample, not a modification to Corner01','seed':a.seed,'plant_algorithm':'plant-0.1','plants_enabled':not a.without_plants,'room_bounds':[4,3,5,12,6,13],'floor_block_y':2,'eye_y':4.62,'interior_size_xz':[8,8],'scale_note':'原版家具与通行量化后的样板，8×8格含独卫；不冒称现实小单间面积','doors':doors,'use_points':uses,'plants':plants,'lights':lights,'components':K.components,'protected_regions':[[8,3,8,10,5,12]],'non_air':len(B.s.blocks),'block_entities':len(bes),'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'status':{'game':'pending','aesthetic':'pending','Corner01':'needs_revision'},'limitations':['单间脱离整栋的小样；未重做原街角楼','沙发/椅/淋浴/坐便/空调是装饰','杯具为花盆符号；空容器不代表已有生活用品','离线状态盒预览并非原版贴图或实机截图']}
(O/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2));(O/'owners.json').write_text(json.dumps({','.join(map(str,q)):v for q,v in B.s.owners.items()}));print(json.dumps({'run':a.run,'non_air':len(B.s.blocks),'plants':plants},ensure_ascii=False))
