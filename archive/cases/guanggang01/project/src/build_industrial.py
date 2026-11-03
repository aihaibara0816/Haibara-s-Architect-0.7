"""Guanggang-inspired original steelworks, bounded case adapter on HAF voxel core."""
from pathlib import Path
import sys,json,math,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT/'deps')]
import numpy as np,industrial_states
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build,Limits
RUN=sys.argv[1] if len(sys.argv)>1 else 'G01';R=ROOT/'runs'/RUN;R.mkdir(parents=True,exist_ok=False)
sc=Scene((240,88,192),max_cells=12_000_000);owner='site';components={}
def m(s,**p):return S.make(s,**p)
def setb(x,y,z,s,**p):sc.set((int(x),int(y),int(z)),m(s,**p),owner)
def box(x0,y0,z0,x1,y1,z1,s):sc.fill((x0,y0,z0),(x1,y1,z1),m(s),owner)
def clear(x0,y0,z0,x1,y1,z1):sc.fill((x0,y0,z0),(x1,y1,z1),'minecraft:air',owner)
def group(id,name):
 global owner;owner=id;components[id]={'id':id,'name':name}
def line(a,b,s,r=0):
 n=max(abs(b[i]-a[i]) for i in range(3))*2+1
 for t in np.linspace(0,1,int(n)):
  q=[round(a[i]+(b[i]-a[i])*t) for i in range(3)]
  for dx in range(-r,r+1):
   for dy in range(-r,r+1):
    for dz in range(-r,r+1):
     if dx*dx+dy*dy+dz*dz<=r*r+0.2:setb(q[0]+dx,q[1]+dy,q[2]+dz,s)
def disk(cx,cz,r,y,s,inner=-1):
 for x in range(math.floor(cx-r),math.ceil(cx+r)+1):
  for z in range(math.floor(cz-r),math.ceil(cz+r)+1):
   d=(x-cx)**2+(z-cz)**2
   if inner*inner<d<=r*r if inner>=0 else d<=r*r:setb(x,y,z,s)
def cyl(cx,cz,r,y0,y1,s,hollow=False):
 for y in range(y0,y1):disk(cx,cz,r,y,s,r-1.3 if hollow else -1)
def dome(cx,cz,r,y0,s):
 for dy in range(math.ceil(r)):
  rr=math.sqrt(max(0,r*r-dy*dy));disk(cx,cz,rr,y0+dy,s,max(-1,rr-1.4))
def rim(cx,cz,r,y,s='iron_bars'):
 for a in np.linspace(0,2*math.pi,math.ceil(r*10)):
  setb(round(cx+r*math.cos(a)),y,round(cz+r*math.sin(a)),s)
def railrect(x0,z0,x1,z1,y):
 for x in range(x0,x1+1):setb(x,y,z0,'iron_bars');setb(x,y,z1,'iron_bars')
 for z in range(z0,z1+1):setb(x0,y,z,'iron_bars');setb(x1,y,z,'iron_bars')
def platform(x0,z0,x1,z1,y,void=None):
 for x in range(x0,x1+1):
  for z in range(z0,z1+1):
   if not void or not(void[0]<=x<=void[2] and void[1]<=z<=void[3]):setb(x,y,z,'smooth_stone_slab',type='top')
 railrect(x0,z0,x1,z1,y+1)
def lamp(x,y,z):
 box(x,3,z,x+1,y,z+1,'polished_deepslate');box(x-1,y,z,x+2,y+1,z+1,'gray_concrete');setb(x-1,y-1,z,'sea_lantern');setb(x+1,y-1,z,'sea_lantern')
def ladder(x,z,y0,y1):
 for y in range(y0,y1):setb(x,y,z,'gray_concrete');setb(x,y,z+1,'ladder',facing='south')
def pipe(points,s='light_gray_concrete',r=1):
 for a,b in zip(points,points[1:]):line(a,b,s,r)
def frame(x0,z0,x1,z1,y0,y1,spacing=10,braces=True):
 for x in [x0,x1]:
  for z in range(z0,z1+1,spacing):box(x,y0,z,x+1,y1+1,z+1,'gray_concrete')
 for y in range(y0+spacing,y1+1,spacing):
  line((x0,y,z0),(x1,y,z0),'gray_concrete');line((x0,y,z1),(x1,y,z1),'gray_concrete')
  for x in [x0,x1]:
   line((x,y,z0),(x,y,z1),'gray_concrete')
   if braces:
    for z in range(z0,z1,spacing):line((x,y-spacing,z),(x,y,min(z+spacing,z1)),'polished_deepslate')
group('site','场地、道路与边界')
box(0,0,0,240,2,192,'stone');box(0,2,0,240,3,192,'stone_bricks')
# Large coherent repair plates, never per-block random color noise.
for x in range(28,232,17):
 for z in range(8,183,17):box(x,2,z,min(x+15,239),3,min(z+15,191),'polished_andesite')
box(26,2,109,234,3,121,'gray_concrete');box(124,2,109,139,3,191,'gray_concrete')
for x in range(32,230,12):box(x,2,114,x+5,3,115,'yellow_concrete')
for z in range(126,184,12):box(131,2,z,132,3,z+5,'yellow_concrete')
for x0,z0,x1,z1 in [(27,5,236,8),(27,183,121,187),(143,183,236,187),(233,8,236,183)]:box(x0,2,z0,x1,3,z1,'grass_block')
for x in range(28,237,8):
 for z in [5,188]:box(x,3,z,x+1,6,z+1,'stone_bricks')
for x0,x1,z in [(28,123,188),(140,237,188),(28,237,5)]:
 for x in range(x0,x1):setb(x,4,z,'iron_bars')
for z in range(5,189):setb(237,4,z,'iron_bars')
for x,z in [(31,108),(72,118),(119,118),(142,118),(190,118),(229,108),(126,178),(140,178),(230,50),(28,45)]:lamp(x,10,z)
group('rail','铁路侧线与矿料车')
box(5,2,0,25,3,192,'polished_deepslate')
for x in [11,20]:
 for z in range(192):
  setb(x,3,z,'rail')
  if z%3==0:box(x-1,2,z,x+2,3,z+1,'dark_oak_planks')
# Broad-gauge-looking wagons centered on a genuine single vanilla rail.
for z0 in [25,42,59,76]:
 for z in [z0+2,z0+10]:
  for x in [18,22]:setb(x,4,z,'polished_deepslate');setb(x,5,z,'polished_deepslate')
 box(18,6,z0,23,7,z0+13,'gray_concrete');box(18,7,z0,19,10,z0+13,'red_terracotta');box(22,7,z0,23,10,z0+13,'red_terracotta')
 box(18,7,z0,23,10,z0+1,'red_terracotta');box(18,7,z0+12,23,10,z0+13,'red_terracotta');box(19,7,z0+1,22,10,z0+12,'coal_block')
 box(20,6,z0+13,21,7,z0+16,'iron_block')
box(8,5,139,15,9,154,'red_concrete');box(8,9,148,15,13,154,'red_terracotta');box(8,11,148,15,12,149,'gray_stained_glass');box(8,11,153,15,12,154,'gray_stained_glass');box(7,13,147,16,14,155,'gray_concrete')
for z in [141,151]:
 for x in [8,14]:box(x,4,z,x+1,6,z+2,'polished_deepslate')
group('stock','料仓与上料斜廊')
for z0,mat in [(15,'coal_block'),(33,'raw_iron_block'),(51,'brown_concrete')]:
 box(30,3,z0,53,5,z0+14,'stone_bricks');box(30,5,z0,31,10,z0+14,'gray_concrete');box(52,5,z0,53,10,z0+14,'gray_concrete');box(30,5,z0+13,53,10,z0+14,'gray_concrete')
 for y in range(5,12):box(33+y-5,y,z0+3,50-(y-5),y+1,z0+11,mat)
frame(56,30,66,61,3,14,10)
box(55,14,29,68,15,64,'waxed_weathered_cut_copper')
for z in [34,46,57]:
 box(57,8,z,66,13,z+5,'light_gray_concrete');box(59,5,z+1,64,8,z+4,'gray_concrete')
# Enclosed incline and a clearly supported parallel catwalk.
for t in range(45):
 x=60+t;z=58; y=12+round(t*.99)
 box(x,y,z-2,x+1,y+1,z+3,'polished_deepslate');box(x,y+1,z-2,x+1,y+4,z-1,'waxed_exposed_cut_copper');box(x,y+1,z+2,x+1,y+4,z+3,'waxed_exposed_cut_copper');box(x,y+4,z-2,x+1,y+5,z+3,'gray_concrete')
 setb(x,y,z+3,'smooth_stone_slab',type='top');setb(x,y,z+4,'smooth_stone_slab',type='top');setb(x,y+1,z+4,'iron_bars')
for x in [63,76,89,102]:
 y=12+round((x-60)*.99);frame(x-1,55,x+1,62,3,y,8,False)
 for a,b in [(x-1,x+1)]:line((a,3,55),(b,y,55),'gray_concrete');line((a,3,62),(b,y,62),'gray_concrete')
group('furnace','一号高炉与检修塔架')
cx,cz=101,78
box(84,3,62,119,5,95,'stone_bricks')
for y in range(5,57):
 r=8 if y<13 else 12-(y-13)*.20 if y<38 else 7-(y-38)*.17
 cyl(cx,cz,r,y,y+1,'red_terracotta' if y<18 else 'gray_concrete',True)
 if y in [13,18,24,31,38,45,52]:rim(cx,cz,r+0.7,y,'polished_deepslate')
disk(cx,cz,7,55,'polished_deepslate');cyl(cx,cz,4,56,63,'light_gray_concrete',True);dome(cx,cz,4,63,'gray_concrete')
# Four open corner legs and trussed staging, visually separate from vessel.
for x in [85,116]:
 for z in [63,93]:box(x,4,z,x+2,66,z+2,'gray_concrete')
for y in [17,30,44,57,65]:
 platform(84,62,118,95,y,(88,66,114,91))
 for x in [85,117]:
  line((x,y,63),(x,y,94),'gray_concrete')
 for z in [63,94]:line((85,y,z),(117,y,z),'gray_concrete')
 if y>17:
  for z in [63,94]:line((86,y-12,z),(116,y,z),'gray_concrete')
for y in [30,44,57,65]:
 box(119,y,82,126,y+1,88,'smooth_stone');railrect(119,82,125,87,y+1)
frame(124,80,130,89,3,67,8)
ladder(126,85,3,67)
for y in [17,30,44,57,65]:
 platform(124,81,130,89,y);clear(126,y,86,127,y+2,87)
setb(101,68,78,'redstone_torch');setb(85,67,63,'redstone_torch');setb(117,67,94,'redstone_torch')
for a in np.linspace(0,2*math.pi,12,endpoint=False):
 x=round(cx+10*math.cos(a));z=round(cz+10*math.sin(a));pipe([(x,10,z),(x,13,z)],'orange_concrete',0)
rim(cx,cz,12,11,'light_gray_concrete')
for x,z in [(86,64),(116,64),(86,93),(116,93)]:setb(x,16,z,'sea_lantern');setb(x,43,z,'sea_lantern')
# Large off-take / downcomer, not a decorative disconnected pipe.
pipe([(102,61,78),(111,64,78),(140,38,78),(140,20,78)],'light_gray_concrete',2)
group('casting','出铁场与敞开铸造棚')
box(71,3,96,122,4,107,'stone_bricks')
for x in range(72,122,10):box(x,4,105,x+1,17,106,'gray_concrete');box(x,4,96,x+1,19,97,'gray_concrete')
for z in range(95,108):
 y=20-(z-95)//4;box(70,y,z,123,y+1,z+1,'waxed_exposed_cut_copper')
for x in [79,96,113]:
 box(x,3,97,x+2,4,105,'black_concrete');box(x,3,98,x+1,4,104,'orange_concrete');setb(x,4,102,'iron_trapdoor');setb(x,15,105,'sea_lantern')
group('stoves','热风炉组、烟囱与除尘器')
for z in [35,53,71]:
 cyl(147,z,6,3,30,'light_gray_concrete',True);disk(147,z,6,3,'stone_bricks');dome(147,z,6,30,'light_gray_concrete')
 for y in [10,21,29]:rim(147,z,6.8,y,'gray_concrete')
 disk(147,z,8,25,'smooth_stone_slab',6.2);rim(147,z,8,26);ladder(139,z,3,27)
 pipe([(147,8,z),(158,8,z)],'brown_concrete',1)
pipe([(158,8,35),(158,8,88),(114,8,88)],'brown_concrete',1)
pipe([(147,24,35),(135,24,35),(135,24,71),(135,13,88),(113,13,88)],'light_gray_concrete',1)
cyl(166,91,4,3,58,'bricks',True)
for y in [45,51]:cyl(166,91,4,y,y+3,'light_gray_concrete',True)
rim(166,91,4,58,'polished_deepslate');setb(166,60,94,'redstone_torch');ladder(166,86,3,58)
pipe([(158,8,88),(166,8,88)],'gray_concrete',1)
cyl(140,82,5,11,25,'gray_concrete',True);dome(140,82,5,25,'gray_concrete')
for x in [136,144]:
 for z in [78,86]:box(x,3,z,x+1,12,z+1,'gray_concrete')
for y in range(6,12):disk(140,82,2+(y-6)*.5,y,'gray_concrete',max(-1,1+(y-6)*.5))
pipe([(140,22,82),(174,22,82),(174,13,52),(182,13,52)],'light_gray_concrete',1)
for z in [57,71,83]:frame(171,z,177,z+1,3,13,10,False)
group('gas','大型煤气柜及环形检修道')
cx,cz=205,38
cyl(cx,cz,21,3,5,'stone_bricks');cyl(cx,cz,18,5,32,'light_gray_concrete',True)
for y in [6,15,24,31]:rim(cx,cz,18.8,y,'gray_concrete')
disk(cx,cz,18,32,'gray_concrete')
for y in range(33,37):disk(cx,cz,18-(y-32)*4,y,'gray_concrete')
for a in np.linspace(0,2*math.pi,12,endpoint=False):
 x=round(cx+20*math.cos(a));z=round(cz+20*math.sin(a));box(x,4,z,x+1,39,z+1,'gray_concrete')
 for y in [13,25,37]:
  b=a+math.pi/6;x2=round(cx+20*math.cos(b));z2=round(cz+20*math.sin(b));line((x,y,z),(x2,y,z2),'gray_concrete')
  if y>13:line((x,y-12,z),(x2,y,z2),'gray_concrete')
disk(cx,cz,21,31,'smooth_stone_slab',18.5);rim(cx,cz,21,32);ladder(226,38,3,33)
pipe([(182,13,52),(187,13,52),(190,13,50)],'light_gray_concrete',1)
setb(205,38,38,'redstone_torch')
group('cooling','循环水池与泵房')
box(188,3,73,225,5,101,'stone_bricks');box(190,4,75,223,5,99,'water')
for x in [194,206,218]:
 box(x-3,5,79,x+4,7,92,'light_gray_concrete');box(x-3,7,79,x+4,14,80,'gray_concrete');box(x-3,7,91,x+4,14,92,'gray_concrete')
 for z in range(81,91,2):box(x-3,7,z,x+4,8,z+1,'iron_trapdoor')
 cyl(x,85,3,14,16,'gray_concrete',True);disk(x,85,2,14,'iron_bars')
pipe([(189,7,97),(178,7,97),(178,7,75),(153,7,75)],'waxed_weathered_cut_copper',1)
group('workshop','锯齿顶机修车间')
def hall(x0,z0,w,d,eave,roofmode):
 x1=x0+w;z1=z0+d;box(x0,3,z0,x1,4,z1,'smooth_stone')
 for z in [z0,z1-1]:
  box(x0,4,z,x1,eave,z+1,'bricks')
  for x in range(x0+3,x1-2,8):box(x,eave-6,z,x+5,eave-2,z+1,'gray_stained_glass_pane')
 for x in [x0,x1-1]:
  box(x,4,z0,x+1,eave,z1,'bricks')
  for z in range(z0+4,z1-3,8):box(x,eave-6,z,x+1,eave-2,z+5,'gray_stained_glass_pane')
 for x in range(x0,x1,10):
  for z in [z0,z1-1]:box(x,4,z,x+1,eave+1,z+1,'gray_concrete')
 for z in range(z0+1,z1-1,10):
  for x in [x0+1,x1-2]:box(x,4,z,x+1,eave,z+1,'gray_concrete')
  line((x0+1,eave-1,z),(x1-2,eave-1,z),'gray_concrete')
 # Doors leave real air; openings face the common cross street.
 clear(x0+6,4,z0,x0+14,12,z0+1);clear(x1-16,4,z0,x1-8,12,z0+1)
 for x in list(range(x0+6,x0+14))+list(range(x1-16,x1-8)):setb(x,3,z0-1,'smooth_stone_slab')
 for x in range(x0,x1):
  if roofmode=='saw':y=eave+((x-x0)%16)//3
  else:y=eave+min(x-x0,x1-1-x)//5
  mat='waxed_weathered_cut_copper' if ((x-x0)//5)%4 else 'waxed_exposed_cut_copper'
  box(x,y,z0-1,x+1,y+1,z1+1,mat)
  if roofmode=='saw' and (x-x0)%16==15:box(x,eave+1,z0,x+1,y,z1,'gray_stained_glass_pane')
 # Long crane runway, bridge, hoist and suspended hook.
 for x in [x0+3,x1-4]:box(x,eave-3,z0+1,x+1,eave-2,z1-1,'yellow_concrete')
 box(x0+3,eave-2,z0+d//2,x1-3,eave-1,z0+d//2+2,'yellow_concrete');box(x0+w//2,eave-3,z0+d//2,x0+w//2+3,eave-1,z0+d//2+3,'gray_concrete')
 for y in range(7,eave-3):setb(x0+w//2+1,y,z0+d//2+1,'chain')
 setb(x0+w//2+1,6,z0+d//2+1,'anvil')
 for x in range(x0+8,x1-5,12):
  for z in range(z0+8,z1-4,12):
   setb(x,eave-2,z,'sea_lantern')
   roof_y=eave+(((x-x0)%16)//3 if roofmode=='saw' else min(x-x0,x1-1-x)//5)
   for yy in range(eave-1,roof_y):setb(x,yy,z,'chain')
 for x in range(x0+5,x1-8,12):
  box(x,4,z1-10,x+7,5,z1-6,'gray_concrete');box(x+1,5,z1-9,x+6,7,z1-7,'waxed_exposed_cut_copper');setb(x+2,7,z1-8,'anvil')
hall(42,125,78,43,17,'saw')
for x in [46,64,82,100]:
 for z in [145,151]:box(x,4,z,x+10,5,z+1,'iron_block');box(x+1,5,z,x+9,6,z+1,'gray_concrete')
group('rolling','轧钢厂房与天车')
hall(153,125,75,49,21,'ridge')
box(180,28,130,201,30,169,'gray_stained_glass_pane');box(179,30,129,202,31,170,'waxed_exposed_cut_copper')
for x in range(164,220,6):
 box(x,4,143,x+3,8,150,'gray_concrete');box(x,6,142,x+3,7,151,'iron_block')
box(160,5,146,223,6,147,'orange_concrete')
group('gate','入口、值班室与办公小楼')
box(105,3,173,123,12,185,'bricks');clear(106,4,174,122,11,184);box(104,12,172,124,13,186,'smooth_stone')
for x in [107,114,120]:box(x,7,173,x+2,10,174,'light_blue_stained_glass_pane')
clear(115,4,184,118,8,185);box(108,4,177,114,5,179,'dark_oak_planks');box(108,5,177,112,6,178,'black_concrete');setb(110,10,178,'sea_lantern')
for x in [123,139]:box(x,3,185,x+2,10,187,'stone_bricks')
box(123,10,185,141,12,187,'red_terracotta');box(125,10,187,139,11,188,'yellow_concrete')
# Sparse maintained boundary trees.
group('site','场地、道路与边界')
for x,z in [(35,179),(55,179),(77,179),(95,179),(149,181),(171,181),(194,181),(217,181),(232,20),(232,65)]:
 box(x-2,2,z-2,x+3,3,z+3,'grass_block');box(x,3,z,x+1,8,z+1,'oak_log')
 for y,r in [(7,3),(8,3),(9,2),(10,1)]:disk(x,z,r,y,'oak_leaves')
S.connect(sc)
states=sorted(set(sc.blocks.values()))
for st in states:S.validate(st)
path=R/'Guanggang01.nbt';ex=export_structure(sc,path,data_version=3955,include_air=False)
rb=load_build(path,Limits(cells=12_000_000,nodes=30_000_000,decoded_bytes=128*1024*1024));assert rb.blocks==sc.blocks
owner_names=list(components);owners=np.zeros((88,192,240),np.uint8)
for q,id in sc.owners.items():owners[q[1],q[2],q[0]]=owner_names.index(id)+1
np.savez_compressed(R/'owners.npz',owners=owners)
records=[]
for i,id in enumerate(owner_names,1):
 pts=np.argwhere(owners==i);lo=pts.min(0);hi=pts.max(0)+1;c=components[id]
 c.update(w=int(hi[2]-lo[2]),d=int(hi[1]-lo[1]),levels=1,floors=[int(lo[0]),int(hi[0])],geometry_bounds=[[int(lo[2]),int(hi[2])],[int(lo[0]),int(hi[0])],[int(lo[1]),int(hi[1])]],blocks=len(pts));records.append(c)
spec={'id':'Guanggang01','title':'广钢式工业区 · 一号钢厂','scope':'原创场景；借鉴广钢工业遗存，不是实测复原','size_xyz':list(sc.size),'spawn_local':[132,3,179],'source_nbt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'buildings':records,'scale':'约 1 方块/米的创作尺度；设备为可辨识造型，不作工程参数','orientation':'z+ 为模型入口方向；不代表广钢真实地理方位','operational_status':'仍在使用的老钢厂，局部有维护修补','limitations':['未运行 Minecraft 客户端','非 Create 生产系统；车辆、设备和生产线为静态造型','离线预览没有资源包纹理，灯光近似','没有实测尺寸、历史时期或厂区布局精确复原承诺']}
(R/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
# Walkable common road: confirm 2-block head clearance and actual ground support.
route=[(132,3,z) for z in range(121,180)]+[(x,3,115) for x in range(29,233)]
blocked=[p for p in route if any((p[0],p[1]+dy,p[2]) in rb.blocks for dy in [0,1]) or (p[0],p[1]-1,p[2]) not in rb.blocks]
check={'source_nbt_sha256':spec['source_nbt_sha256'],'size_xyz':list(sc.size),'blocks':len(rb.blocks),'palette':len(states),'independent_nbt_equal':True,'state_subset_valid':True,'main_road_clearance_2_blocks':not blocked,'blocked_route_cells':blocked,'game_test':'not_run','renderer':'NBT-readback approximate block shapes and colors','data_version':3955}
(R/'check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2));assert not blocked,blocked
print(json.dumps(check,ensure_ascii=False),flush=True)
