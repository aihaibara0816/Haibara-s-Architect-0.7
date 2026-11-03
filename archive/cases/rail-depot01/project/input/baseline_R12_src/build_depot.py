"""RailDepot01: original railway campus, actual Create tracks/targets. Not game-tested."""
from pathlib import Path
import sys,json,math,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'src'),str(ROOT/'support')]
import numpy as np,create_states
from detail_lab import states as S
from vendor.voxel_core import Scene,parse_state
from vendor.inspect_build import load_build,Limits,read_nbt
from rail_nbt import *
R=ROOT/'runs'/sys.argv[1];R.mkdir(parents=True,exist_ok=False)
SIZE=(480,104,240);sc=Scene(SIZE,max_cells=12_000_000);owner='site';components={};rooms=[];doors=[];beds=[];stair_routes=[];bes={};curves=[];stations=[];signals=[];walks=[]
exec((ROOT/'src/primitives_fragment.txt').read_text())
# Site datum: finished outside surface Y=7; rail base Y=7; room floors Y=7.
group('site','01 · 场地、道路与步行系统')
box(0,3,0,480,6,240,'stone');box(0,6,0,480,7,240,'grass_block')
for b in [(8,6,149,472,7,160),(8,6,227,472,7,237),(8,6,23,23,7,227),(461,6,23,472,7,227),(184,6,160,198,7,227)]:box(*b,'gray_concrete')
for x in range(28,459,15):
 for z in [154,232]:box(x,6,z,x+7,7,z+1,'white_concrete')
for z in range(168,225,15):box(190,6,z,191,7,z+7,'white_concrete')
for x in range(10,472,24):
 for z in [6,238]:box(x,7,z,x+1,10,z+1,'light_gray_concrete')
for x in range(10,472):
 for z in [5,238]:
  if not(z==238 and 177<x<204):put(x,8,z,'iron_bars')
for z in range(5,238):
 for x in [5,474]:
  if not(x==5 and (74<=z<=86 or 94<=z<=106)):put(x,8,z,'iron_bars')
for x in range(30,458,38):
 for z in [27,146,224]:
  box(x,7,z,x+1,17,z+1,'light_gray_concrete');box(x-2,17,z,x+3,18,z+1,'light_gray_concrete')
  for xx in [x-2,x+2]:put(xx,16,z,'sea_lantern')
# Railway formation. Tracks added LAST, keeping exact Create identities and BEs.
group('railway','02 · Create 双线接入与十股道咽喉')
# Main approach: two external interfaces 6 blocks apart; six and four track ladders.
tracklines=[(0,19,87),(0,19,93),(70,457,80),(70,457,100),(126,457,68),(126,457,112),(182,457,56),(182,457,124),(238,457,44),(238,457,136),(294,457,32),(350,457,20),(40,181,135)]
curve_pairs=[((18,7,87),(70,7,80)),((18,7,93),(70,7,100)),((74,7,80),(126,7,68)),((74,7,100),(126,7,112)),((130,7,68),(182,7,56)),((130,7,112),(182,7,124)),((186,7,56),(238,7,44)),((186,7,124),(238,7,136)),((242,7,44),(294,7,32)),((298,7,32),(350,7,20))]
trackcells=set();corridor={};bed_cells=set()
for a,b,z in tracklines:
 for x in range(a,b):
  trackcells.add((x,7,z));
  if z!=135:corridor.setdefault(x,[]).append(z+.5)
for p,q in curve_pairs:
 pts=curve_points(p,q);length=float(np.linalg.norm(np.diff(pts,axis=0),axis=1).sum());assert 50<=length<=60,length
 curves.append({'a':list(p),'b':list(q),'length_blocks':length,'projected_endpoint_distance_x':q[0]-p[0]})
 for xx,yy,zz in pts:corridor.setdefault(int(xx),[]).append(float(zz))
# A single stone-filled operating formation follows the narrowing track envelope.
# Coarse deterministic material patches avoid both large lawns and per-block white noise.
for x,axes in sorted(corridor.items()):
 lo=math.floor(min(axes)-5);hi=math.ceil(max(axes)+5)
 for z in range(lo,hi):
  tile=((x//5)*13+(z//4)*7+((x//13)^(z//11))*3)%20
  mat='cobblestone' if tile<14 else 'stone' if tile<19 else 'andesite'
  put(x,6,z,mat);bed_cells.add((x,z))
 for z in [lo,hi-1]:put(x,6,z,'cobblestone')
# Clear maintenance strips and a shallow-looking perimeter drain outside both shoulders.
for x,axes in sorted(corridor.items()):
 for z in [math.floor(min(axes)-6),math.ceil(max(axes)+5)]:
  put(x,6,z,'cobblestone_slab')
# Narrow pedestrian path links the shortened footbridge back to the perimeter road.
box(253,6,140,268,7,149,'smooth_stone')
# Two long, low maintenance volumes: usable work range 312..432 = 120 blocks.
def shed(id,name,x0,z0,x1,z1,axes,roof=21):
 group(id,name);box(x0,6,z0,x1,7,z1,'smooth_stone')
 for z in [z0,z1-1]:
  box(x0,7,z,x1,roof,z+1,'light_gray_concrete');box(x0,15,z,x1,18,z+1,'light_blue_stained_glass_pane');box(x0,roof-3,z,x1,roof-1,z+1,'blue_concrete')
 for x in [x0,x1-1]:
  box(x,7,z0,x+1,roof,z1,'white_concrete')
  for z in axes:air(x,7,z-3,x+1,15,z+4)
 for x in range(x0+4,x1-2,14):
  for z in [z0+1,z1-2]:box(x,7,z,x+1,roof,z+1,'gray_concrete')
  box(x,roof-2,z0+1,x+1,roof-1,z1-1,'light_gray_concrete')
  for z in range(z0+7,z1-5,12):box(x,roof-3,z-2,x+1,roof-2,z+3,'sea_lantern')
 box(x0-1,roof,z0-1,x1+1,roof+1,z1+1,'white_concrete')
 for z in axes:box(x0+4,roof,z-1,x1-4,roof+1,z+2,'light_blue_stained_glass')
 for x in range(x0+7,x1-4,10):box(x,roof+1,z0,x+1,roof+2,z1,'light_gray_concrete')
 for x in [x0+30,x1-30]:air(x,7,z1-1,x+3,10,z1)
 rooms.append({'id':id,'bounds':[x0,7,z0,x1,roof,z1],'use':name,'work_length':120,'doors':'rail openings 7 wide x 8 high'})
shed('stabling','03 · 四线停放与日常整备库',304,36,454,88,[44,56,68,80],19)
shed('maintenance','04 · 双线检修、车底坑与车顶平台',304,92,454,132,[100,112,124],23)
# Service slabs: low door access for stabling; all outside 5-block car envelope.
group('stabling','03 · 四线停放与日常整备库')
for z in [44,56,68,80]:
 for side in [-1,1]:
  zz=z+side*4;box(312,7,zz,432,9,zz+2,'smooth_stone');box(312,8,zz,432,9,zz+1,'yellow_concrete')
  for k in range(2):
   for dz in range(2):put(310+k,7+k,zz+dz,'smooth_quartz_stairs',facing='east')
 for x in [316,426]:put(x,9,z+5,'barrel',facing='north')
group('maintenance','04 · 双线检修、车底坑与车顶平台')
for z in [100,112]:
 # 120 clear usable blocks, both escape stairs beyond effective length.
 box(301,4,z-1,441,5,z+2,'stone_bricks');air(301,5,z,441,7,z+1)
 for zz in [z-1,z+1]:box(301,5,zz,441,7,zz+1,'light_gray_concrete')
 for x in range(312,432,8):
  for zz in [z-1,z+1]:put(x,5,zz,'sea_lantern')
 # Side exits avoid walking upward into the rail directly overhead.
 for xx in [302,433]:
  box(xx,4,z,xx+2,5,z+4,'stone_bricks');air(xx,5,z+1,xx+2,7,z+4)
  for xxx in range(xx,xx+2):
   put(xxx,5,z+2,'smooth_quartz_stairs',facing='south');put(xxx,6,z+3,'smooth_quartz_stairs',facing='south')
 for side in [-1,1]:
  zz=z+side*4
  box(312,11,zz,432,12,zz+2,'smooth_stone');box(312,11,zz,432,12,zz+1,'yellow_concrete')
  outer=zz if side<0 else zz+1
  for x in range(312,432):put(x,12,outer,'iron_bars')
  for x in range(316,432,12):box(x,7,outer,x+1,11,outer+1,'gray_concrete');put(x,10,outer,'sea_lantern')
  for i in range(5):
   for dz in range(2):put(307+i,7+i,zz+dz,'smooth_quartz_stairs',facing='east')
  walks += [(x,12,zz+(1 if side<0 else 0)) for x in range(312,432)]
 # door-height short side access at rear of the work zone.
 box(436,7,z+3,447,9,z+6,'smooth_stone')
# Heavy work lane: crane, jacks and bogie/parts bench, open upper clearance.
group('heavy','05 · 轮对、转向架与重修工位')
for x in range(315,432,24):
 for z in [121,128]:box(x,7,z,x+2,10,z+1,'orange_concrete')
for z in [94,130]:box(306,19,z,447,20,z+1,'gray_concrete')
for x in [338,412]:
 box(x,19,94,x+2,21,131,'yellow_concrete');box(x,18,122,x+2,19,126,'gray_concrete');box(x,15,124,x+1,18,125,'chain')
for x in [318,345,376,405]:
 box(x,7,128,x+8,8,131,'gray_concrete')
 for xx in [x+1,x+5]:put(xx,8,129,'anvil',facing='east')
# Exterior wash lane and adjacent recirculation tanks; portal over the actual rail.
group('wash','06 · 洗车线与循环水')
for x in [304,314,324,334,344]:
 for z in [132,140]:box(x,7,z,x+2,15,z+1,'white_concrete')
 box(x,15,132,x+2,17,141,'blue_concrete')
 for z in [133,139]:box(x,8,z,x+1,13,z+1,'cyan_concrete')
box(298,6,133,350,7,140,'smooth_stone')
for x in [366,389]:
 box(x,7,140,x+18,9,148,'light_gray_concrete');box(x+1,8,141,x+17,9,147,'water')
# Turn the eight bay ends into clearly visible buffer stops outside vehicle station envelope.
group('railway','02 · Create 双线接入与十股道咽喉')
for z in [44,56,68,80,100,112,124,136]:
 box(457,7,z-1,459,9,z+2,'gray_concrete');box(457,9,z-2,458,10,z+3,'red_concrete')
# Front buildings. Every floor has a usable perimeter, corridors and internal stairs.
def building(id,name,x0,z0,w,d,levels,accent='blue_concrete',kind='office'):
 group(id,name);x1=x0+w;z1=z0+d;top=7+levels*6
 box(x0,6,z0,x1,top,z1,'white_concrete');air(x0+1,7,z0+1,x1-1,top-1,z1-1)
 for f in range(levels):
  fy=7+f*6;box(x0+1,fy-1,z0+1,x1-1,fy,z1-1,'smooth_stone')
  # Deliberately solid western core; grouped glazing on three working facades.
  for x in range(x0+9,x1-4,8):
   for z in [z0,z1-1]:box(x,fy+1,z,min(x+5,x1-2),fy+4,z+1,'light_blue_stained_glass_pane')
  for z in range(z0+5,z1-3,8):box(x1-1,fy+1,z,x1,fy+4,min(z+5,z1-2),'gray_stained_glass_pane')
  for z in [z0,z1-1]:box(x0,fy+4,z,x1,fy+5,z+1,accent)
  for x in range(x0+12,x1-3,10):
   for z in range(z0+4,z1-3,10):box(x,fy+4,z,x+3,fy+5,z+1,'sea_lantern')
  rooms.append({'id':id+'_F'+str(f+1),'floor':f+1,'floor_y':fy,'bounds':[x0+1,fy,z0+1,x1-1,fy+5,z1-1],'use':('接待与公共服务' if f==0 else '会议与休息' if f%3==0 else '办公研发') if kind=='office' else kind,'core':[x0+1,z0+2,x0+9,z0+13],'clear_corridor':[x0+9,z0+1,x0+12,z1-1]})
  if kind=='office':
   if f==0:
    box(x0+14,fy,z0+5,x0+26,fy+1,z0+7,'smooth_quartz');sofa(x0+17,fy,z1-5,8)
   elif f%3==0:table(x0+17,fy,z0+9,'meeting');sofa(x0+17,fy,z1-5,8);box(x1-3,fy,z0+5,x1-2,fy+3,z0+14,'bookshelf')
   else:
    for x in range(x0+15,x1-5,8):
     for z in range(z0+6,z1-5,9):
      box(x,fy,z,x+4,fy+1,z+2,'dark_oak_planks');box(x+1,fy+1,z,x+3,fy+2,z+1,'black_concrete');put(x+1,fy,z+3,'dark_oak_stairs',facing='north')
  elif kind=='canteen':
   if f==0:
    box(x0+13,fy,z0+2,x1-2,fy+1,z0+5,'smooth_quartz')
    for x in range(x0+15,x1-3,5):put(x,fy,z0+2,'furnace',facing='south')
   for x in range(x0+14,x1-6,9):
    for z in range(z0+10,z1-4,8):table(x,fy,z)
  elif kind=='dorm':
   # Central corridor Z+14..17; repeat compact double rooms with real paired doors.
   for x in range(x0+13,x1-8,10):
    for z in [z0+1,z0+18]:
     box(x,fy,z,x+1,fy+5,z+12,'light_gray_concrete');bed(x+3,fy,z+4);bed(x+6,fy,z+4);put(x+7,fy,z+8,'barrel',facing='west');box(x+2,fy,z+10,x+7,fy+1,z+11,'dark_oak_planks')
    box(x,fy,z0+12,x+10,fy+5,z0+13,'white_concrete');box(x,fy,z0+18,x+10,fy+5,z0+19,'white_concrete')
    for zz,face in [(z0+12,'south'),(z0+18,'north')]:air(x+3,fy,zz,x+4,fy+2,zz+1);door(x+3,fy,zz,face)
  elif kind=='dispatch':
   for x in range(x0+14,x1-4,8):
    for z in [z0+7,z0+15]:box(x,fy,z,x+5,fy+1,z+2,'gray_concrete');box(x,fy+1,z,x+5,fy+2,z+1,'cyan_stained_glass');put(x+2,fy,z+3,'dark_oak_stairs',facing='north')
   box(x0+13,fy+1,z0+1,x1-2,fy+4,z0+2,'black_concrete')
   for x in range(x0+14,x1-3,4):box(x,fy+2,z0+2,x+2,fy+3,z0+3,'cyan_concrete')
 # Stairs added after all slabs. Six risers + side landing; no plate over heads.
 for f in range(levels-1):
  fy=7+f*6;x=x0+3;z=z0+11
  air(x,fy+4,z-5,x+3,fy+6,z+2)
  for i in range(6):
   for xx in range(x,x+3):put(xx,fy+i,z-i,'smooth_quartz_stairs',facing='north')
  # Exit landing beside stair, and longitudinal return walkway.
  box(x+3,fy+5,z-5,x+6,fy+6,z+2,'smooth_stone')
  stair_routes.append({'x':x,'z':z,'floor_y':fy,'upper_floor_y':fy+6,'width':3,'component':id,'rise':6})
 box(x0-1,top,z0-1,x1+1,top+1,z1+1,'light_gray_concrete')
 for x in [x0,x1-1]:box(x,top+1,z0,x+1,top+2,z1,'white_concrete')
 for z in [z0,z1-1]:box(x0,top+1,z,x1,top+2,z+1,'white_concrete')
 for x in range(x0+12,x1-5,10):box(x,top+1,z0+5,x+6,top+3,z0+10,'gray_concrete')
 air(x0+10,7,z1-1,x0+15,11,z1);box(x0+9,11,z1-1,x0+17,12,z1+4,'blue_concrete')
 components[id].update(levels=levels,floors=[6+i*6 for i in range(levels)])
 return (x0,z0,x1,z1,top)
building('tower','07 · 十五层铁路研发综合楼',64,174,40,42,15)
building('research','08 · 试验室与技术培训楼',120,176,58,40,3,kind='office')
building('dispatch','09 · 调度与运行控制中心',206,161,40,27,3,kind='dispatch')
building('canteen','10 · 两层食堂与员工活动',204,195,54,31,2,'cyan_concrete','canteen')
building('dorm','11 · 四层乘务宿舍',282,195,68,31,4,'light_gray_concrete','dorm')
# Energy centre and spare-parts warehouse are low, function-specific buildings.
shed('energy','12 · 能源、压缩空气与消防水',369,165,450,188,[],14)
group('energy','12 · 能源、压缩空气与消防水')
air(369,7,171,370,11,177)
for x in range(379,442,10):
 box(x,7,169,x+6,11,174,'gray_concrete');box(x,7,180,x+6,10,184,'white_concrete');box(x,11,169,x+6,12,174,'iron_trapdoor')
for x in [356,364]:cyl(x,170,3,7,18,'white_concrete',True);disk(x,170,3,18,'light_gray_concrete');ring(x,170,3,14,'blue_concrete')
shed('parts','13 · 备件库、材料与设备场',370,199,451,226,[],16)
group('parts','13 · 备件库、材料与设备场');air(370,7,208,371,13,216)
for x in range(383,444,12):
 for y in [8,11]:
  box(x,y,203,x+4,y+1,221,'gray_concrete')
  for z in range(204,220,4):box(x,y+1,z,x+3,y+3,z+3,'dark_oak_planks')
for x in [293,314,335]:
 box(x,7,164,x+15,8,173,'smooth_stone')
 for z in range(165,172,2):box(x+1,8,z,x+14,10,z+1,'dark_oak_planks')
for x in [294,315,336]:
 for z in [179,182,185]:box(x,7,z,x+17,8,z+1,'iron_block')
# A separate pedestrian bridge across the throat approach. Deck underside 17 > roof envelope 13.
group('bridges','14 · 员工连廊与跨线步桥')
box(262,17,10,268,18,140,'smooth_stone')
for x in [262,267]:
 box(x,18,10,x+1,21,140,'light_blue_stained_glass_pane')
box(262,21,10,268,22,140,'white_concrete')
for z in [12,88,138]:
 for x in [262,267]:box(x,7,z,x+1,17,z+1,'gray_concrete')
for z in [10,136]:
 # Stair west of deck, ascent along X; 11 risers yields feet 18.
 for i in range(11):
  for zz in range(z,z+4):put(251+i,7+i,zz,'smooth_quartz_stairs',facing='east')
# Low front corridor connects second-floor research, canteen and dorm; crossings clear for people.
box(174,12,190,350,13,194,'smooth_stone');box(174,16,190,350,17,194,'white_concrete')
for z in [190,193]:box(174,13,z,350,16,z+1,'light_blue_stained_glass_pane')
for x in range(182,347,22):box(x,7,190,x+1,12,191,'gray_concrete');put(x,15,191,'sea_lantern')
for x0,x1,z0,z1 in [(174,178,190,216),(218,223,188,196),(296,301,193,196)]:
 box(x0,12,z0,x1,13,z1,'smooth_stone');box(x0,16,z0,x1,17,z1,'white_concrete')
 for x in [x0,x1-1]:box(x,13,z0,x+1,16,z1,'light_blue_stained_glass_pane')
 # openings at attached building walls, stairs/clear space checked separately.
for x0,x1,z0,z1 in [(175,177,176,216),(219,222,187,189),(219,222,195,196),(297,300,195,196)]:air(x0,13,z0,x1,16,z1)
# Fix corridor junctions and keep walkable strips at least two blocks wide.
for x0,x1,z0,z1 in [(175,177,190,194),(218,223,190,194),(296,301,190,194)]:air(x0,13,z0,x1,16,z1)
walks += [(x,13,191) for x in range(178,350)]
# Entrance, local landscaping and public edge.
group('entry','15 · 门卫、入口与员工庭院')
box(178,6,226,204,7,240,'smooth_stone')
for x in [178,202]:box(x,7,234,x+2,15,236,'white_concrete')
box(178,15,234,204,17,237,'white_concrete');box(181,15,237,201,16,238,'blue_concrete')
box(160,7,222,175,14,232,'white_concrete');air(161,7,223,174,13,231);box(161,9,222,173,12,223,'light_blue_stained_glass_pane');air(174,7,225,175,10,229);put(167,12,227,'sea_lantern')
for x,z in [(45,178),(45,211),(111,171),(113,221),(265,203),(267,220),(355,214),(358,233)]:
 box(x-2,7,z-2,x+3,8,z+3,'white_concrete');box(x,8,z,x+1,14,z+1,'oak_log')
 for y,r in [(12,2),(13,3),(14,3),(15,2)]:disk(x,z,r,y,'oak_leaves')
for x,z in [(110,218),(204,222),(266,219),(353,224)]:bench(x,7,z,8)
# Apply site relief, facilities and facade redesign before rail objects.
exec((ROOT/'src/revise_r10_fragment.py').read_text())
# Railway objects written after all architecture. No imported orphan carriage entities.
group('railway','02 · Create 双线接入与十股道咽喉')
for p in trackcells:sc.set(p,m('create:track'),'testline' if p[2]==135 else owner)
for p,q in curve_pairs:
 for a,b,primary in [(p,q,True),(q,p,False)]:
  sc.set(a,m('create:track',turn='true'),owner)
  be=bes.setdefault(a,{'id':T('create:track'),'AlternateModel':B(0),'Connections':L(10,[])})
  be['Connections'][1][1].append(conn(a,b,primary))
def station(name,x,z,positive=True):
 pos=(x,9,z+5);target=(x,7,z);box(x-1,7,z+4,x+2,9,z+7,'smooth_stone');put(*pos,'create:track_station')
 q={'id':T('create:track_station'),**targeting(name,pos,target,positive),'DoorControl':T('ALL'),'PrevTrainColor':I(0),'FailedCarriageIndex':I(-1),'OutputBuffer':CO({'Size':I(8),'Items':L(10,[])}),'Migrate':CO({'Name':T(name),'Assembling':B(0),'Ports':L(10,[]),'DimensionPalette':L(10,[])})};bes[pos]=q;stations.append({'name':name,'pos':list(pos),'target':list(target),'direction':1 if positive else -1})
station('RD-TEST-W',48,135,False);station('RD-TEST-E',168,135,True)
station('RD-OUTDOOR-01',440,32);station('RD-OUTDOOR-02',440,20)
for name,z in [('STABLE-01',44),('STABLE-02',56),('STABLE-03',68),('STABLE-04',80),('INSPECT-01',100),('INSPECT-02',112),('HEAVY-01',124),('WASH-01',136)]:station('RD-'+name,420,z)
def signal(x,z,positive,kind):
 zz=z+(4 if positive else -4);pos=(x,7,zz);name=f'S{x}-{z}-{positive}';put(*pos,'create:track_signal',type=kind)
 bes[pos]={'id':T('create:track_signal'),**targeting(name,pos,(x,7,z),positive),'State':T('INVALID'),'Overlay':T('RENDER'),'Power':B(0)}
 signals.append({'pos':list(pos),'target':[x,7,z],'direction':1 if positive else -1,'type':kind})
signal(10,87,False,'entry_signal');signal(10,93,True,'cross_signal')
signal(60,135,False,'entry_signal');signal(156,135,True,'entry_signal')
signal(354,20,False,'cross_signal');signal(354,20,True,'entry_signal');signal(300,32,False,'cross_signal');signal(300,32,True,'entry_signal')
for z in [44,56,68,80,100,112,124,136]:signal(300,z,False,'cross_signal');signal(300,z,True,'entry_signal')
# One source-format schedule item; driver/conductor and assembled train supplied in game.
group('dispatch','09 · 调度与运行控制中心')
route=['RD-TEST-W','RD-TEST-E']
entries=[]
for name in route:
 entries.append({'Instruction':CO({'Id':T('create:destination'),'Data':CO({'Text':T(name)})}),'Conditions':L(9,[(10,[{'Id':T('create:delay'),'Data':CO({'Value':I(20),'TimeUnit':I(1)})}])])})
schedule={'Cyclic':B(1),'Entries':L(10,entries)}
pos=(222,7,182);put(*pos,'barrel',facing='north');bes[pos]={'id':T('minecraft:barrel'),'Items':L(10,[{'Slot':B(0),'id':T('create:schedule'),'count':I(1),'components':CO({'create:train_schedule':CO(schedule)})}])}
# User revision: industrial land is paved; vegetation is confined to small accents.
green_pockets=[(37,175,51,190),(37,203,51,218),(108,170,115,224),(260,202,275,223)]
ground_changed=0
for (x,y,z),st in list(sc.blocks.items()):
 if y!=6 or not st.startswith('minecraft:grass_block'):continue
 keep=x<5 or x>=475 or z<4 or z>=237 or any(a<=x<c and b<=z<d for a,b,c,d in green_pockets)
 if keep:continue
 if z<149:
  k=((x//5)*13+(z//4)*7)%20;mat='cobblestone' if k<14 else 'stone' if k<19 else 'andesite'
 else:mat='light_gray_concrete'
 sc.set((x,y,z),m(mat),sc.owners[(x,y,z)]);ground_changed+=1
(R/'surface_revision.json').write_text(json.dumps({'baseline':'R05','scope':'yard expansion, double-track interface, lighting and surface articulation','grass_cells_replaced':ground_changed,'grass_cells_remaining_at_ground':sum(y==6 and st.startswith('minecraft:grass_block') for (x,y,z),st in sc.blocks.items()),'site_cells_xz':SIZE[0]*SIZE[2],'green_pockets':green_pockets,'not_a_regulatory_green_ratio':True},indent=2))
S.connect(sc)
for st in set(sc.blocks.values()):S.validate(st)
# Path/clearance checks are geometric only; do not call them game validation.
errors=[]
for z in [44,56,68,80,100,112,124,136]:
 for x in range(304,453):
  for y in range(8,13):
   for zz in range(z-2,z+3):
    st=sc.blocks.get((x,y,zz))
    if st:errors.append([x,y,zz,st])
assert not errors,errors[:12]
for item in stations+signals:assert sc.blocks[tuple(item['target'])].startswith('create:track[')
assert len(stations)==12 and len(signals)==24
stairbad=[]
for st in stair_routes:
 for i in range(6):
  for x in range(st['x'],st['x']+st['width']):
   y,z=st['floor_y']+i,st['z']-i
   if 'stairs' not in sc.blocks.get((x,y,z),'') or any((x,y+dy,z) in sc.blocks for dy in [1,2]):stairbad.append([x,y,z])
assert not stairbad,stairbad[:20]
walkbad=[p for p in walks if any((p[0],p[1]+dy,p[2]) in sc.blocks for dy in [0,1]) or (p[0],p[1]-1,p[2]) not in sc.blocks]
assert not walkbad,walkbad[:20]
hash=export(sc,bes,R/'RailDepot01.nbt');lim=Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024);rb=load_build(R/'RailDepot01.nbt',lim);assert rb.blocks==sc.blocks
names=list(components);ids={id:i+1 for i,id in enumerate(names)};owners=np.zeros((SIZE[1],SIZE[2],SIZE[0]),np.uint8)
for (x,y,z),id in sc.owners.items():owners[y,z,x]=ids[id]
np.savez_compressed(R/'owners.npz',owners=owners)
for id in names:
 pts=np.argwhere(owners==ids[id]);lo=pts.min(0);hi=pts.max(0)+1
 components[id].update(w=int(hi[2]-lo[2]),d=int(hi[1]-lo[1]),geometry_bounds=[[int(lo[2]),int(hi[2])],[int(lo[0]),int(hi[0])],[int(lo[1]),int(hi[1])]],blocks=len(pts));components[id].setdefault('levels',1);components[id].setdefault('floors',list(range(int(lo[0]),int(hi[0]),4)))
sp={'id':'RailDepot01','title':'新港列车所 · 检修与研发基地','size_xyz':SIZE,'spawn_local':[190,7,231],'world_y_offset':58,'source_nbt_sha256':hash,'buildings':list(components.values()),'revision':R.name+' twin-track interface, ten depot tracks, relocated independent lane and yard lighting','throat_topology':'six-track north ladder and four-track south ladder; separate double-track interfaces at Z87/Z93; independent maintenance track at Z135','rail_ground':'raised cobblestone formation at Y7, stepped shoulders at Y6, service basins at Y5; equipment platforms and roads at Y7','shed_start_x':304,'tower_storeys':15,'inspection_effective_length':120,'work_interval_x':[312,432],'track_base_y':7,'car_envelope_width':5,'car_envelope_top_y':13,'pit_foot_y':5,'roof_platform_foot_y':12,'front_floor_pitch':6,'source_consist':'two cab-ended cars plus one centre car; approximately 68 blocks cell envelope','design_consist_max_length':90,'curve_lengths':[round(c['length_blocks'],3) for c in curves],'server_max_placement_user_report':256,'design_curve_target':[50,60],'mod_versions':{'minecraft':'1.21.1','neoforge':'21.1.244 (user target)','create':'6.0.10'},'game':'not_run','limitations':['Authored Create block states, reciprocal curves, targeted signals/stations, and schedule item; runtime graph and dispatch pending game','No active train entities copied; original carriage entities depend on additional mods and external TrainId graph','Offline preview approximates materials and Create meshes; no game collision certification']}
for file,data in [('spec.json',sp),('rooms.json',rooms),('access.json',{'doors':doors,'beds':beds,'stairs':stair_routes}),('rail_network.json',{'topology':'20->32->44->56->68->80->87 and 136->124->112->100->93; independent maintenance track Z135','stone_formation_cells':len(bed_cells),'straight_lines':tracklines,'curves':curves,'stations':stations,'signals':signals,'schedule_route':route,'schedule_barrel_local':list(pos),'railway_status':'authored, not game-run'}),('check.json',{'source_nbt_sha256':hash,'blocks':len(sc.blocks),'palette':len(set(sc.blocks.values())),'independent_nbt_equal':True,'car_corridor_errors':errors,'stair_headroom_errors':stairbad,'walk_errors':walkbad,'stairs':len(stair_routes),'beds':len(beds),'curve_length_range':[min(sp['curve_lengths']),max(sp['curve_lengths'])],'game':'not_run'})]:
 (R/file).write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({'blocks':len(sc.blocks),'sha':hash,'curve_lengths':sp['curve_lengths'],'BEs':len(bes),'stairs':len(stair_routes)},ensure_ascii=False))
