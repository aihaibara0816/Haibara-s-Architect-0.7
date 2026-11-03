"""New-port integrated materials campus: original industrial and living program."""
from pathlib import Path
import sys,json,math,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT/'deps')]
import numpy as np,industrial_states
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state
from vendor.inspect_build import load_build,read_nbt,Limits
RUN=sys.argv[1];R=ROOT/'runs'/RUN;R.mkdir(parents=True,exist_ok=False)
SIZE=(448,72,336);sc=Scene(SIZE,max_cells=12_000_000);owner='site';components={};rooms=[];doors=[];beds=[];stair_routes=[];tree_centres=[]
def m(s,**p):return S.make(s,**p)
def put(x,y,z,s,**p):sc.set((int(x),int(y),int(z)),m(s,**p),owner)
def box(x0,y0,z0,x1,y1,z1,s):
 if x0<x1 and y0<y1 and z0<z1:sc.fill((x0,y0,z0),(x1,y1,z1),m(s),owner)
def air(x0,y0,z0,x1,y1,z1):sc.fill((x0,y0,z0),(x1,y1,z1),'minecraft:air',owner)
def group(id,name):
 global owner;owner=id;components.setdefault(id,{'id':id,'name':name})
def line(a,b,s,r=0):
 for t in np.linspace(0,1,int(max(abs(b[i]-a[i]) for i in range(3))*2+1)):
  q=[round(a[i]+(b[i]-a[i])*t) for i in range(3)]
  for dx in range(-r,r+1):
   for dy in range(-r,r+1):
    for dz in range(-r,r+1):
     if dx*dx+dy*dy+dz*dz<=r*r:put(q[0]+dx,q[1]+dy,q[2]+dz,s)
def disk(cx,cz,r,y,s,inner=-1):
 for x in range(math.floor(cx-r),math.ceil(cx+r)+1):
  for z in range(math.floor(cz-r),math.ceil(cz+r)+1):
   ds=(x-cx)**2+(z-cz)**2
   if ds<=r*r and (inner<0 or ds>inner*inner):put(x,y,z,s)
def cyl(cx,cz,r,y0,y1,s,hollow=False):
 for y in range(y0,y1):disk(cx,cz,r,y,s,r-1.2 if hollow else -1)
def dome(cx,cz,r,y,s):
 for dy in range(math.ceil(r)):
  rr=math.sqrt(max(0,r*r-dy*dy));disk(cx,cz,rr,y+dy,s,max(0,rr-1.3))
def ring(cx,cz,r,y,s='iron_bars'):
 for a in np.linspace(0,math.pi*2,math.ceil(r*12)):put(round(cx+r*math.cos(a)),y,round(cz+r*math.sin(a)),s)
def rail(x0,z0,x1,z1,y):
 for x in range(x0,x1+1):put(x,y,z0,'iron_bars');put(x,y,z1,'iron_bars')
 for z in range(z0,z1+1):put(x0,y,z,'iron_bars');put(x1,y,z,'iron_bars')
def tree(x,z,r=3):
 tree_centres.append((x,z))
 box(x-2,2,z-2,x+3,3,z+3,'grass_block');box(x,3,z,x+1,9,z+1,'oak_log')
 for y,rr in [(7,r-1),(8,r),(9,r),(10,r-1)]:disk(x,z,rr,y,'oak_leaves')
def lamp(x,z,h=11):
 box(x,3,z,x+1,h,z+1,'light_gray_concrete');box(x-1,h,z,x+2,h+1,z+1,'light_gray_concrete')
 for xx in [x-1,x+1]:put(xx,h-1,z,'sea_lantern')
def planter(x,y,z,w,d):
 box(x,y,z,x+w,y+1,z+d,'white_concrete');box(x+1,y+1,z+1,x+w-1,y+2,z+d-1,'azalea_leaves')
def bench(x,y,z,w=5):
 for xx in range(x,x+w):put(xx,y,z,'dark_oak_slab',type='top');put(xx,y+1,z+1,'dark_oak_trapdoor',facing='south',open='true')
def table(x,y,z,kind='dining'):
 # Six seats, a thin supported tabletop and occasional tableware.
 for xx in [x,x+4]:put(xx,y,z+1,'iron_bars')
 for xx in range(x,x+5):put(xx,y+1,z+1,'dark_oak_slab' if kind=='dining' else 'smooth_quartz_slab')
 for xx in [x,x+2,x+4]:put(xx,y,z-1,'dark_oak_stairs',facing='north');put(xx,y,z+3,'dark_oak_stairs',facing='south')
 if kind=='dining':put(x+2,y,z+1,'dark_oak_planks');put(x+2,y+1,z+1,'cake',bites='0')
def sofa(x,y,z,w=5):
 box(x,y,z,x+w,y+1,z+2,'blue_wool');box(x,y+1,z+1,x+w,y+2,z+2,'blue_wool')
 for xx in [x-1,x+w]:put(xx,y,z,'smooth_quartz_slab',type='top')
def door(x,y,z,facing='east'):
 for half,dy in [('lower',0),('upper',1)]:put(x,y+dy,z,'birch_door',facing=facing,half=half,hinge='left',open='false',powered='false')
 doors.append({'pos':[x,y,z],'facing':facing,'component':owner})
def bed(x,y,z):
 put(x,y,z,'white_bed',part='foot',facing='north',occupied='false');put(x,y,z-1,'white_bed',part='head',facing='north',occupied='false');beds.append([x,y,z])
def stairs(x,z,fy,width=3):
 # Eight risers, side landing at x+width, continuous 8-block storey pitch.
 air(x,fy+6,z-8,x+width,fy+8,z+2)
 for i in range(8):
  for xx in range(x,x+width):
   if i:put(xx,fy+i-1,z-i,'smooth_stone')
   put(xx,fy+i,z-i,'smooth_quartz_stairs',facing='north')
 stair_routes.append({'x':x,'z':z,'floor_y':fy,'upper_floor_y':fy+8,'width':width,'component':owner})
def pipe(points,s='light_gray_concrete',r=1):
 for a,b in zip(points,points[1:]):line(a,b,s,r)
def pipe_rack(x0,x1,z,y):
 for x in range(x0,x1+1,12):
  for zz in [z-4,z+4]:box(x,3,zz,x+1,y,zz+1,'gray_concrete')
  box(x,y-1,z-4,x+1,y,z+5,'gray_concrete')
 for dz,mat in [(-2,'light_gray_concrete'),(1,'blue_concrete'),(3,'white_concrete')]:pipe([(x0,y,z+dz),(x1,y,z+dz)],mat,0)
def conveyor(a,b,w=5):
 n=max(abs(b[i]-a[i]) for i in range(3));pts=[]
 for t in np.linspace(0,1,n+1):
  x,y,z=[round(a[i]+(b[i]-a[i])*t) for i in range(3)];pts.append((x,y,z))
  if abs(b[0]-a[0])>=abs(b[2]-a[2]):
   box(x,y,z-w//2,x+1,y+1,z+w//2+1,'gray_concrete');box(x,y+1,z-w//2,x+1,y+3,z-w//2+1,'light_gray_concrete');box(x,y+1,z+w//2,x+1,y+3,z+w//2+1,'light_gray_concrete');box(x,y+3,z-w//2,x+1,y+4,z+w//2+1,'blue_concrete')
  else:
   box(x-w//2,y,z,x+w//2+1,y+1,z+1,'gray_concrete');box(x-w//2,y+1,z,x-w//2+1,y+3,z+1,'light_gray_concrete');box(x+w//2,y+1,z,x+w//2+1,y+3,z+1,'light_gray_concrete');box(x-w//2,y+3,z,x+w//2+1,y+4,z+1,'blue_concrete')
 for i,(x,y,z) in enumerate(pts):
  if i%12==0 and not 114<=z<133:
   for dx in [-3,3]:box(x+dx,3,z,x+dx+1,y,z+1,'gray_concrete')
group('site','园区道路、边界与绿化')
box(0,0,0,448,2,336,'stone');box(0,2,0,448,3,336,'grass_block')
for b in [(8,2,8,440,3,23),(8,2,23,23,3,329),(425,2,23,440,3,329),(8,2,216,440,3,235),(8,2,315,440,3,329),(217,2,23,235,3,216),(23,2,114,425,3,133)]:box(*b,'gray_concrete')
for x in range(30,420,16):
 for z in [15,123,227,322]:box(x,2,z,x+7,3,z+1,'white_concrete')
for z in range(30,310,16):
 for x in [15,432]:box(x,2,z,x+1,3,z+7,'white_concrete')
for z in range(29,212,15):box(226,2,z,227,3,z+6,'white_concrete')
for b in [(28,2,28,211,3,110),(244,2,28,420,3,110),(28,2,139,211,3,213),(244,2,139,420,3,213),(29,2,246,130,3,312),(143,2,251,231,3,310),(263,2,249,356,3,313)]:box(*b,'smooth_stone')
for x in range(6,443,10):
 for z in [5,331]:box(x,3,z,x+1,6,z+1,'light_gray_concrete')
for x in range(5,443):
 for z in [5,332]:
  if not(z==332 and 206<x<250):put(x,4,z,'iron_bars')
for z in range(5,332):
 for x in [5,443]:
  if not(x==443 and 114<z<134):put(x,4,z,'iron_bars')
for x in range(35,421,32):
 tree(x,238,2)
 for z in [7,332]:
  if not(z==332 and 200<x<255):tree(x,z,2)
for x,z in [(25,112),(92,112),(158,112),(215,112),(237,112),(308,112),(420,112),(25,213),(94,213),(165,213),(238,213),(310,213),(420,213),(141,312),(257,312),(358,312),(420,312)]:lamp(x,z)
group('rawyard','01 · 原料堆场与卸料区')
for k,(x,z,mat) in enumerate([(35,34,'sandstone'),(87,34,'gravel'),(35,76,'calcite'),(87,76,'raw_iron_block')]):
 box(x,3,z,x+44,4,z+29,'stone_bricks');box(x,4,z,x+1,10,z+29,'light_gray_concrete');box(x+43,4,z,x+44,10,z+29,'light_gray_concrete');box(x,4,z,x+44,10,z+1,'light_gray_concrete')
 for y in range(4,13):box(x+4+(y-4)*2,y,z+4+(y-4)//2,x+40-(y-4)*2,y+1,z+25-(y-4)//2,mat)
 box(x+1,9,z,x+43,10,z+1,'blue_concrete')
# Wheeled loader, bucket and a parked raw-material tipper.
box(30,4,105,38,7,111,'yellow_concrete');box(32,7,106,36,10,110,'gray_stained_glass');box(31,10,105,37,11,111,'yellow_concrete')
for x in [30,37]:
 for z in [105,109]:box(x,3,z,x+1,5,z+2,'polished_deepslate')
line((35,6,109),(42,5,109),'yellow_concrete');box(40,3,107,45,4,112,'gray_concrete');box(44,4,107,45,6,112,'gray_concrete')
group('silos','02 · 筒仓与定量给料')
for cx in [161,190]:
 for cz in [45,74,99]:
  for x,z in [(cx-5,cz-5),(cx+5,cz-5),(cx-5,cz+5),(cx+5,cz+5)]:box(x,3,z,x+1,13,z+1,'gray_concrete')
  for y in range(7,14):disk(cx,cz,2+(y-7)*.8,y,'white_concrete',max(-1,1+(y-7)*.8))
  cyl(cx,cz,7,14,34,'white_concrete',True);disk(cx,cz,7,34,'white_concrete');dome(cx,cz,7,34,'light_gray_concrete')
  for y in [17,30]:ring(cx,cz,7.3,y,'blue_concrete')
  disk(cx,cz,9,29,'smooth_stone_slab',7.2);ring(cx,cz,9,30)
  for y in range(4,32):put(cx+9,y,cz,'gray_concrete');put(cx+9,y,cz+1,'ladder',facing='south')
  pipe([(cx,7,cz),(cx,7,108)],'gray_concrete',0)
box(150,30,36,201,31,39,'smooth_stone');rail(150,36,200,38,31)
conveyor((112,10,100),(161,30,99));conveyor((176,23,99),(176,20,151))
group('process','03 · 露天加工塔架与罐式设备')
for cx,cz,rad,top in [(261,48,7,35),(289,48,9,43),(320,48,7,33),(261,86,6,30),(291,86,8,36),(319,86,6,28)]:
 cyl(cx,cz,rad+2,3,5,'smooth_stone');cyl(cx,cz,rad,7,top,'light_gray_concrete',True);dome(cx,cz,rad,top,'white_concrete')
 for y in [10,top-4]:ring(cx,cz,rad+1,y,'blue_concrete')
 for x in [cx-rad-3,cx+rad+3]:
  for z in [cz-rad-3,cz+rad+3]:box(x,3,z,x+1,top+4,z+1,'gray_concrete')
 for y in [15,27]:
  if y<top:
   for z in [cz-rad-3,cz+rad+3]:box(cx-rad-3,y,z,cx+rad+4,y+1,z+2,'smooth_stone');rail(cx-rad-3,z,cx+rad+3,z+1,y+1)
   for x in [cx-rad-3,cx+rad+3]:box(x,y,cz-rad-3,x+2,y+1,cz+rad+4,'smooth_stone')
 for y in range(3,top+2):put(cx+rad+4,y,cz,'gray_concrete');put(cx+rad+4,y,cz+1,'ladder',facing='south')
 pipe([(cx,12,cz+rad),(cx,12,109)],'white_concrete',1)
put(289,53,48,'redstone_torch')
pipe_rack(244,418,109,16);pipe([(261,16,109),(261,16,148)],'white_concrete',1)
for z in [113,134]:
 for x in [257,265]:box(x,3,z,x+1,15,z+1,'gray_concrete')
group('tankfarm','04 · 液体储罐区')
box(351,3,29,419,4,108,'smooth_stone');rail(351,29,418,107,5)
for x in [365,400]:
 for z in [45,78]:
  cyl(x,z,11,4,6,'light_gray_concrete');cyl(x,z,9,6,28,'white_concrete',True);disk(x,z,9,28,'white_concrete');dome(x,z,9,28,'white_concrete')
  ring(x,z,9.3,8,'blue_concrete');ring(x,z,9.3,24,'light_gray_concrete');disk(x,z,11,26,'smooth_stone_slab',9.2);ring(x,z,11,27)
  for y in range(5,28):put(x+11,y,z,'gray_concrete');put(x+11,y,z+1,'ladder',facing='south')
  pipe([(x,8,z+9),(x,8,102),(381,8,102)],'blue_concrete',1)
pipe([(381,8,102),(381,16,109)],'blue_concrete',1)
group('production','05 · 连续生产主厂房')
def hall(x0,z0,x1,z1,roof,accent='blue_concrete',open_east=False):
 box(x0,3,z0,x1,4,z1,'smooth_stone')
 for x in [x0,x1-1]:box(x,4,z0,x+1,roof,z1,'white_concrete')
 for z in [z0,z1-1]:box(x0,4,z,x1,roof,z+1,'light_gray_concrete')
 for z in [z0,z1-1]:
  for x in range(x0+5,x1-8,20):box(x,11,z,x+14,15,z+1,'light_blue_stained_glass_pane')
  box(x0,roof-3,z,x1,roof-1,z+1,accent)
 for x in [x0,x1-1]:
  for z in range(z0+5,z1-8,14):box(x,11,z,x+1,15,z+9,'light_blue_stained_glass_pane')
  box(x,roof-3,z0,x+1,roof-1,z1,accent)
 for z in range(z0+4,z1-1,12):
  for x in [x0+1,x1-2]:box(x,4,z,x+1,roof,z+1,'gray_concrete')
  box(x0+1,roof-2,z,x1-1,roof-1,z+1,'light_gray_concrete')
  for x in range(x0+8,x1-7,16):box(x,roof-3,z,x+7,roof-2,z+1,'sea_lantern');put(x,roof-1,z,'chain')
 box(x0-1,roof,z0-1,x1+1,roof+1,z1+1,'white_concrete')
 for x in range(x0+3,x1-1,8):box(x,roof,z0,x+1,roof+1,z1,'light_gray_concrete')
 for z in [z0+18,z1-18]:box(x0+6,roof,z,x1-6,roof+1,z+3,'light_blue_stained_glass')
 for x in [x0,x1-1]:box(x,roof+1,z0,x+1,roof+2,z1,'light_gray_concrete')
 if open_east:
  for z in range(z0+4,z1-10,15):air(x1-1,4,z,x1,12,z+10)
 else:
  air(x1-1,4,z1-18,x1,12,z1-8)
 for x in [x0+14,x1-18]:air(x,4,z1-1,x+6,10,z1)
hall(31,143,210,207,25)
air(173,19,143,180,25,144)
for z in [162,185]:
 box(42,4,z,193,5,z+3,'gray_concrete');box(42,5,z+1,193,6,z+2,'polished_andesite')
 for x in range(49,183,18):
  box(x,4,z-6,x+9,5,z+9,'light_gray_concrete');box(x,5,z-6,x+2,14,z-3,'white_concrete');box(x+7,5,z+6,x+9,14,z+9,'white_concrete');box(x,13,z-6,x+9,15,z+9,'blue_concrete')
  box(x+2,8,z-5,x+7,12,z-4,'cyan_stained_glass_pane');box(x+2,8,z+7,x+7,12,z+8,'cyan_stained_glass_pane')
  box(x+2,5,z-3,x+7,8,z+6,'iron_block');put(x+7,8,z-7,'black_concrete')
 for zz in [z-8,z+11]:box(40,3,zz,195,4,zz+1,'yellow_concrete')
for x in [58,96,134]:
 box(x,26,174,x+18,28,179,'light_gray_concrete');box(x+2,28,175,x+16,31,178,'gray_concrete');box(x+1,31,174,x+17,32,179,'white_concrete')
# Control mezzanine with proper floor connection to the employee bridge.
box(179,10,193,210,12,207,'smooth_stone');box(179,12,193,210,17,194,'light_blue_stained_glass_pane');box(179,17,193,210,18,207,'white_concrete')
for x in [188,199]:box(x,12,196,x+9,13,198,'smooth_quartz');put(x+3,13,196,'black_concrete');put(x+4,17,201,'sea_lantern')
for x in [180,207]:box(x,4,194,x+1,10,195,'gray_concrete')
stairs(181,203,4);air(189,12,206,197,17,207)
group('packing','06 · 包装、检测与码垛车间')
hall(246,144,322,207,22,'cyan_concrete',True)
for z in [160,182]:
 box(253,4,z,314,5,z+3,'gray_concrete');box(253,5,z+1,314,6,z+2,'iron_block')
 for x in [260,278,296]:
  box(x,5,z-4,x+9,9,z+7,'white_concrete');air(x+2,5,z,x+7,8,z+3);box(x,9,z-4,x+9,10,z+7,'cyan_concrete');box(x+7,7,z+6,x+9,9,z+7,'black_concrete')
for x in [251,267,283,303]:
 for z in [149,197]:box(x,4,z,x+7,5,z+6,'dark_oak_planks');box(x+1,5,z+1,x+6,9,z+5,'white_terracotta')
conveyor((294,17,105),(294,17,148));air(291,16,144,298,22,145)
group('warehouse','07 · 成品库与货运月台')
hall(339,143,417,207,26)
for x in [350,365,380,395,409]:
 air(x-3,4,206,x+4,13,207);box(x-4,13,207,x+5,14,211,'blue_concrete');box(x-4,3,207,x+5,5,211,'smooth_stone')
 for xx in [x-4,x+4]:box(xx,3,211,xx+1,6,212,'yellow_concrete')
for x in [348,367,386,403]:
 for z in [151,166,181]:
  for xx in [x,x+7]:
   for zz in [z,z+9]:box(xx,4,zz,xx+1,21,zz+1,'blue_concrete')
  for y in [5,10,15]:box(x,y,z,x+8,y+1,z+10,'orange_concrete');box(x+1,y+1,z+1,x+7,y+4,z+9,'white_terracotta')
def truck(cx,z):
 box(cx-3,5,z,cx+4,11,z+10,'white_concrete');box(cx-3,5,z+10,cx+4,9,z+15,'blue_concrete');box(cx-2,8,z+14,cx+3,10,z+15,'light_blue_stained_glass');box(cx-2,10,z+11,cx+3,11,z+15,'blue_concrete');box(cx-2,4,z,cx+3,5,z+15,'gray_concrete')
 for zz in [z+1,z+7,z+12]:
  for xx in [cx-3,cx+3]:box(xx,3,zz,xx+1,5,zz+2,'polished_deepslate')
for x in [350,380,409]:truck(x,210)
group('office','08 · 八层独立办公与研发楼')
def office_floor(x0,z0,x1,z1,fy,kind,atrium=False):
 box(x0,fy-1,z0,x1,fy,z1,'smooth_quartz');box(x0,fy+6,z0,x1,fy+8,z1,'white_concrete')
 for x in [x0,x1-1]:box(x,fy,z0,x+1,fy+6,z1,'white_concrete')
 for z in [z0,z1-1]:
  box(x0,fy,z,x1,fy+6,z+1,'white_concrete')
  for x in range(x0+4,x1-8,12):box(x,fy+1,z,x+8,fy+5,z+1,'light_blue_stained_glass_pane')
 for x in [x0,x1-1]:box(x,fy+1,z0+4,x+1,fy+5,z1-4,'gray_stained_glass_pane')
 for x in range(x0+9,x1-10,16):
  for z in [z0+7,z1-7]:put(x,fy+6,z,'sea_lantern')
 if kind=='office':
  for x in range(x0+8,x1-21,13):
   for z in [z0+5,z1-8]:
    box(x,fy,z,x+7,fy+1,z+3,'smooth_quartz');put(x+2,fy+1,z+1,'black_concrete');put(x+5,fy+1,z+1,'black_concrete')
    for xx in [x+2,x+5]:put(xx,fy,z+4,'dark_oak_stairs',facing='south')
 elif kind=='meeting':
  for x in range(x0+7,x1-22,20):table(x,fy,z0+9,'meeting');box(x,fy,z1-3,x+10,fy+3,z1-2,'bookshelf')
 else:
  for x in range(x0+8,x1-23,19):sofa(x,fy,z0+8,7);bench(x,fy,z1-6,7)
 rooms.append({'component':owner,'floor_y':fy,'function':kind,'bounds_xyz':[x0,fy,z0,x1,fy+6,z1]})
for f in range(8):
 fy=4+8*f;x0,x1=(32,127) if f<6 else (42,119)
 office_floor(x0,249,x1,275,fy,'lobby' if f==0 else 'meeting' if f in [2,5,7] else 'office')
for f in range(5):office_floor(32,275,62,309,4+8*f,'meeting' if f in [0,2] else 'office')
for f in range(5):air(48,4+8*f,274,55,9+8*f,277)
# Open first three levels at the main entrance; upper galleries remain intact.
air(73,10,264,100,26,274);box(73,4,274,100,26,275,'light_blue_stained_glass_pane');air(84,4,274,92,11,275)
for fy in [12,20]:
 for x in range(72,101):put(x,fy,263,'iron_bars')
 for x in [72,100]:
  for z in range(264,274):put(x,fy,z,'iron_bars')
box(73,10,275,101,11,282,'white_concrete');box(78,4,269,84,5,272,'smooth_quartz');box(78,5,269,83,6,270,'dark_oak_slab')
for x in [76,95]:planter(x,4,265,3,3);put(x,9,274,'sea_lantern')
# Upper setback has a side landing against the unchanged stair core.
for f in range(8):
 fy=4+8*f;air(111,fy,253,119,fy+5,267)
 if f<7:stairs(112,264,fy)
for fy in [52]:rail(32,249,126,274,fy)
air(112,12,249,121,17,250)
# South plaza and sheltered seating.
box(64,2,280,128,3,311,'smooth_stone')
for x in [67,111]:planter(x,3,301,13,5);bench(x+3,3,298,8)
group('canteen','09 · 两层食堂与员工活动中心')
x0,z0,x1,z1=147,255,231,307
for fy in [4,12]:
 box(x0,fy-1,z0,x1,fy,z1,'smooth_quartz');box(x0,fy+6,z0,x1,fy+8,z1,'white_concrete')
 for x in [x0,x1-1]:box(x,fy,z0,x+1,fy+6,z1,'white_concrete')
 for z in [z0,z1-1]:box(x0,fy,z,x1,fy+6,z+1,'white_concrete')
 for x in range(x0+5,x1-7,12):box(x,fy+1,z1-1,x+8,fy+5,z1,'light_blue_stained_glass_pane')
 for z in range(z0+6,z1-6,10):box(x0,fy+1,z,x0+1,fy+5,z+6,'light_blue_stained_glass_pane');box(x1-1,fy+1,z,x1,fy+5,z+6,'light_blue_stained_glass_pane')
 for x in range(x0+8,x1-5,12):
  for z in range(z0+7,z1-3,10):put(x,fy+6,z,'sea_lantern')
# Ground floor: cold/dry store, cooking, washing, serving and 144 seats.
box(148,4,274,230,9,275,'white_concrete');air(160,4,274,164,8,275);air(218,4,274,223,8,275)
for x in range(153,226,9):
 put(x,4,259,'barrel',facing='south');put(x+1,4,259,'barrel',facing='south');put(x,5,259,'barrel',facing='south')
 put(x,4,266,'furnace',facing='south',lit='false');put(x+1,4,266,'furnace',facing='south',lit='false');box(x,7,265,x+3,8,268,'iron_block')
 put(x+4,4,269,'water_cauldron',level='3');box(x+3,4,268,x+7,5,269,'smooth_quartz')
for x in [152,171,190,209]:box(x,4,276,x+14,5,278,'smooth_quartz');box(x,5,276,x+14,6,277,'light_gray_concrete');put(x+5,5,277,'cake',bites='0')
for x in range(153,222,9):
 for z in [282,291,300]:table(x,4,z)
box(222,4,286,230,5,289,'smooth_quartz');put(228,4,290,'water_cauldron',level='3')
air(183,4,306,193,10,307);box(180,10,307,196,11,312,'white_concrete')
# Upper floor: additional dining, lounge, reading and training rooms.
box(147,12,278,231,17,279,'white_concrete');air(184,12,278,191,16,279)
for x in [153,169,185,201]:
 for z in [262,271]:table(x,12,z,'meeting')
for x in [154,177,201]:
 sofa(x,12,285,9);bench(x,12,292,9);box(x,12,302,x+13,15,303,'bookshelf')
for x in [149,225]:planter(x,12,281,4,4)
stairs(224,272,4);air(178,12,255,186,17,256)
rooms.extend([{'component':'canteen','function':'kitchen_serving_washing','floor_y':4,'bounds_xyz':[148,4,256,230,10,279]},{'component':'canteen','function':'dining','floor_y':4,'capacity':144,'bounds_xyz':[148,4,279,230,10,306]},{'component':'canteen','function':'dining_training_lounge','floor_y':12,'capacity':48,'bounds_xyz':[148,12,256,230,18,306]}])
def dorm(id,x0):
 group(id,'10 · 员工宿舍 A' if id=='dormA' else '11 · 员工宿舍 B');z0,z1=253,313;x1=x0+24
 for f in range(6):
  fy=4+8*f;box(x0,fy-1,z0,x1,fy,z1,'smooth_stone');box(x0,fy+6,z0,x1,fy+8,z1,'white_concrete')
  for x in [x0,x1-1]:box(x,fy,z0,x+1,fy+6,z1,'white_concrete')
  for z in [z0,z1-1]:box(x0,fy,z,x1,fy+6,z+1,'white_concrete')
  # A real double-loaded corridor and rooms with a privacy wall.
  for x in [x0+9,x0+14]:box(x,fy,z0+14,x+1,fy+6,z1-1,'white_concrete')
  for k,z in enumerate(range(269,309,8)):
   for x,side in [(x0+1,'west'),(x0+15,'east')]:
    box(x,fy,z-1,x+8,fy+6,z,'white_concrete')
    outer=x0 if side=='west' else x1-1;box(outer,fy+1,z+1,outer+1,fy+5,z+6,'light_blue_stained_glass_pane')
    dx=x0+9 if side=='west' else x0+14;air(dx,fy,z+3,dx+1,fy+2,z+4);door(dx,fy,z+3,'east' if side=='west' else 'west')
    bed(x+1,fy,z+3);bed(x+5,fy,z+3);put(x+2,fy,z,'barrel',facing='south');box(x+1,fy,z+6,x+6,fy+1,z+7,'dark_oak_slab');put(x+4,fy,z+5,'dark_oak_stairs',facing='north');put(x+3,fy+6,z+4,'sea_lantern')
    rooms.append({'id':f'{id}_{f}_{side}_{k}','component':id,'function':'bedroom','floor_y':fy,'capacity':2,'bounds_xyz':[x,fy,z,x+8,fy+6,min(z+7,z1-1)],'entrance':[dx,fy,z+3]})
  # North common utility / sanitary room and a stair vestibule.
  box(x0+15,fy,264,x1-1,fy+6,265,'white_concrete');air(x0+15,fy,264,x0+18,fy+3,265)
  for z in [256,260]:put(x0+20,fy,z,'water_cauldron',level='3');put(x0+16,fy,z,'barrel',facing='west')
  for z in range(258,311,10):put(x0+11,fy+6,z,'sea_lantern')
  if f<2:air(x0+10,fy,253,x0+14,fy+4,254)
  else:box(x0+10,fy+1,253,x0+14,fy+4,254,'light_blue_stained_glass_pane')
  # Individual projecting sunshades give the dorms a domestic rhythm.
  for z in range(270,310,8):
   box(x0-1,fy+5,z,x0,fy+6,z+6,'light_gray_concrete');box(x1,fy+5,z,x1+1,fy+6,z+6,'light_gray_concrete')
 for f in range(5):stairs(x0+2,264,4+8*f)
 air(x0+9,4,312,x0+15,10,313);box(x0+7,10,313,x0+17,11,317,'blue_concrete')
 rail(x0,253,x1-1,312,52)
dorm('dormA',268);dorm('dormB',328)
group('bridges','12 · 二层员工步行廊网')
def bridge(x0,z0,x1,z1):
 box(x0,10,z0,x1,12,z1,'white_concrete');box(x0,17,z0,x1,18,z1,'white_concrete')
 if x1-x0>z1-z0:
  for z in [z0,z1-1]:box(x0,12,z,x1,17,z+1,'light_blue_stained_glass_pane')
  for x in range(x0+6,x1-3,16):put(x,17,(z0+z1)//2,'sea_lantern')
 else:
  for x in [x0,x1-1]:box(x,12,z0,x+1,17,z1,'light_blue_stained_glass_pane')
  for z in range(z0+4,z1-2,12):put((x0+x1)//2,17,z,'sea_lantern')
bridge(112,240,348,248)
for x0,z0,x1,z1 in [(112,247,121,250),(178,247,186,256),(278,247,282,254),(338,247,342,254),(189,204,197,248)]:bridge(x0,z0,x1,z1)
# Real openings at junctions and building ends, without removing the deck.
for x0,z0,x1,z1 in [(113,240,120,250),(179,241,185,256),(279,241,282,254),(339,241,342,254),(190,204,196,247)]:air(x0,12,z0,x1,17,z1)
air(188,12,241,198,17,247)
for x in range(128,347,24):
 for z in [241,246]:box(x,3,z,x+1,10,z+1,'light_gray_concrete')
for z in [210,236]:
 for x in [189,196]:box(x,3,z,x+1,10,z+1,'light_gray_concrete')
group('amenities','13 · 员工庭院、运动场和服务配套')
box(233,2,251,264,3,313,'smooth_stone');box(296,2,253,324,3,311,'smooth_stone');box(363,2,251,419,3,311,'smooth_stone')
for x,z in [(242,263),(242,294),(301,260),(317,303),(369,257),(411,305)]:tree(x,z,3)
for x,z in [(238,276),(299,278),(301,298),(366,290),(397,307)]:bench(x,3,z,9)
# Full half-court markings, hoops and a second quiet seating lawn.
box(365,2,268,415,3,296,'cyan_concrete')
for x in range(367,414):put(x,2,270,'white_concrete');put(x,2,294,'white_concrete')
for z in range(270,295):put(367,2,z,'white_concrete');put(413,2,z,'white_concrete');put(390,2,z,'white_concrete')
ring(390,282,4,2,'white_concrete')
for x in [366,414]:box(x,3,281,x+1,8,282,'gray_concrete');box(x,7,279,x+1,10,284,'white_concrete')
# Employee service kiosk with first-aid/lockers, separate from the canteen kitchen.
box(365,3,251,393,4,263,'smooth_stone');box(365,4,251,393,10,263,'white_concrete');air(366,4,252,392,9,262);box(364,10,250,394,11,264,'blue_concrete');air(375,4,262,381,8,263)
for x in [368,373,386]:put(x,4,253,'barrel',facing='south');put(x,9,257,'sea_lantern')
bed(386,4,260);box(368,4,259,375,5,261,'smooth_quartz')
group('utilities','14 · 动力、循环水与环保设施')
# Small service island between staff spaces and the western production gate.
box(31,3,23,129,4,28,'smooth_stone')
for x in [40,57,74,91,108]:box(x,4,24,x+10,8,28,'light_gray_concrete');box(x+2,8,24,x+8,10,28,'gray_concrete')
# Water treatment outside the tank bund, separate open volumes.
for x0,z0,x1,z1 in [(351,92,376,107),(387,92,418,107)]:
 box(x0,3,z0,x1,5,z1,'light_gray_concrete');box(x0+1,4,z0+1,x1-1,5,z1-1,'water')
 for x in range(x0+3,x1-2,7):box(x,5,z0+1,x+1,6,z1-1,'iron_trapdoor')
group('entry','15 · 门卫与主入口')
box(207,2,329,249,3,336,'smooth_stone')
for x in [207,247]:box(x,3,329,x+2,12,332,'white_concrete')
box(207,12,329,249,14,333,'white_concrete');box(214,12,333,242,13,334,'blue_concrete')
box(233,3,304,246,10,314,'white_concrete');air(234,4,305,245,9,313);box(234,6,304,244,9,305,'light_blue_stained_glass_pane');air(233,3,307,234,8,311);box(232,10,303,247,11,315,'blue_concrete');put(240,9,308,'sea_lantern')
box(217,2,235,233,3,329,'smooth_stone')
for z in range(316,329,2):box(214,2,z,235,3,z+1,'white_concrete')
for x in [71,87,103,119]:
 box(x,2,318,x+1,3,328,'white_concrete')
for x in [75,91,107]:box(x,3,320,x+5,5,327,'blue_concrete');box(x+1,5,322,x+4,6,326,'gray_stained_glass')
for x0,x1,z in [(84,92,275),(183,193,307),(277,283,313),(337,343,313)]:
 for x in range(x0,x1):put(x,3,z,'smooth_stone_slab')
# Industrial ground revision: open operation/service surfaces replace residual lawns.
changed=0;tree_beds={(x+dx,z+dz) for x,z in tree_centres for dx in range(-2,3) for dz in range(-2,3)}
for (x,y,z),st in list(sc.blocks.items()):
 if y!=2 or not st.startswith('minecraft:grass_block'):continue
 keep=x<5 or x>=443 or z<5 or z>=331 or (x,z) in tree_beds
 if keep:continue
 # Employee and traffic frontage is paved; production interstices use stone/crushed-stone expression.
 mat='light_gray_concrete' if z>=216 else ('stone' if ((x//5)*13+(z//4)*7)%5 else 'gravel')
 sc.set((x,y,z),m(mat),sc.owners[(x,y,z)]);changed+=1
(R/'surface_revision.json').write_text(json.dumps({'baseline':'E06','scope':'ground materials; buildings, routes and industrial equipment retained','grass_cells_replaced':changed,'grass_cells_remaining_at_ground':sum(y==2 and st.startswith('minecraft:grass_block') for (x,y,z),st in sc.blocks.items()),'site_cells_xz':SIZE[0]*SIZE[2],'tree_beds':len(tree_centres),'not_a_regulatory_green_ratio':True},indent=2))
S.connect(sc)
palette=sorted(set(sc.blocks.values()))
for st in palette:S.validate(st)
nbt=R/'ModernFactory01.nbt';export_structure(sc,nbt,data_version=3955,include_air=False)
limits=Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024)
rb=load_build(nbt,limits);assert rb.blocks==sc.blocks
names=list(components);ids={id:i+1 for i,id in enumerate(names)};owners=np.zeros((72,336,448),np.uint8)
for (x,y,z),id in sc.owners.items():owners[y,z,x]=ids[id]
np.savez_compressed(R/'owners.npz',owners=owners)
for id in names:
 pts=np.argwhere(owners==ids[id]);lo=pts.min(0);hi=pts.max(0)+1
 components[id].update(w=int(hi[2]-lo[2]),d=int(hi[1]-lo[1]),levels=1,floors=list(range(int(lo[0]),int(hi[0]),4)),geometry_bounds=[[int(lo[2]),int(hi[2])],[int(lo[0]),int(hi[0])],[int(lo[1]),int(hi[1])]],blocks=len(pts))
spec={'id':'ModernFactory01','revision':'V3 paved working ground and accent planting','title':'新港制造园 · 综合生产基地','size_xyz':list(SIZE),'spawn_local':[226,3,329],'source_nbt_sha256':hashlib.sha256(nbt.read_bytes()).hexdigest(),'buildings':list(components.values()),'scope':'原创综合新材料工厂，场景组织而非工程施工设计','office_storeys':8,'dorm_storeys':6,'dorm_buildings':2,'canteen_storeys':2,'dining_seats':192,'dorm_beds':len(beds)-1,'comparison':{'baseline_size_xz':[272,224],'new_size_xz':[448,336],'area_ratio':448*336/(272*224),'baseline_feedback':'warehouse-dominant and underscaled; needs process plant and employee amenities'},'production_sequence':['原料堆场','定量筒仓','露天加工设备与罐区','连续成型生产线','检测包装','成品仓储'],'material_status':'新建维护状态，罐体白灰、钢架深灰、蓝色统一标识','game':'not_run','limitations':['原版静态工厂设备，不是 Create 生产系统','工艺顺序为建筑场景组织，不对应真实工程设计','预览是近似材质的 NBT 几何渲染','原版家具数据已写入，互动仍待实机验证']}
(R/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2));(R/'rooms.json').write_text(json.dumps(rooms,ensure_ascii=False,indent=2));(R/'access.json').write_text(json.dumps({'doors':doors,'beds':beds,'stairs':stair_routes},indent=2))
road=[(226,3,z) for z in range(24,214)]+[(x,3,227) for x in range(24,425)]+[(x,3,123) for x in range(24,443)]
bad=[p for p in road if any((p[0],p[1]+dy,p[2]) in rb.blocks for dy in [0,1]) or (p[0],p[1]-1,p[2]) not in rb.blocks]
walk=[(x,12,244) for x in range(113,347)]+[(193,12,z) for z in range(205,245)]+[(117,12,z) for z in range(244,252)]+[(182,12,z) for z in range(244,258)]+[(280,12,z) for z in range(244,258)]+[(340,12,z) for z in range(244,258)]
walkbad=[p for p in walk if any((p[0],p[1]+dy,p[2]) in rb.blocks for dy in [0,1]) or (p[0],p[1]-1,p[2]) not in rb.blocks]
bedbad=[]
for x,y,z in beds:
 for zz,part in [(z,'foot'),(z-1,'head')]:
  name,pr=parse_state(rb.blocks.get((x,y,zz),'minecraft:air'))
  if not name.endswith('_bed') or pr.get('part')!=part or (x,y-1,zz) not in rb.blocks:bedbad.append([x,y,zz])
doorbad=[]
for d in doors:
 x,y,z=d['pos'];a=parse_state(rb.blocks[(x,y,z)])[1];b=parse_state(rb.blocks[(x,y+1,z)])[1]
 if a.get('half')!='lower' or b.get('half')!='upper' or (x,y+2,z) not in rb.blocks:doorbad.append(d)
bridgegap=[(x,y,z) for x in range(190,196) for y in range(3,10) for z in range(216,235) if (x,y,z) in rb.blocks]
stairbad=[]
for st in stair_routes:
 for i in range(8):
  for x in range(st['x'],st['x']+st['width']):
   y,z=st['floor_y']+i,st['z']-i
   if 'stairs' not in rb.blocks.get((x,y,z),'') or any((x,y+j,z) in rb.blocks for j in [1,2]):stairbad.append([x,y,z])
 for x in [st['x']+st['width']]:
  y,z=st['upper_floor_y'],st['z']-7
  if (x,y-1,z) not in rb.blocks or any((x,y+j,z) in rb.blocks for j in [0,1]):stairbad.append([x,y,z])
check={'stair_routes':len(stair_routes),'stair_headroom_errors':stairbad,'source_nbt_sha256':spec['source_nbt_sha256'],'size_xyz':list(SIZE),'blocks':len(rb.blocks),'palette':len(palette),'independent_nbt_equal':True,'main_road_clear':not bad,'road_errors':bad,'bridge_network_clear':not walkbad,'bridge_errors':walkbad,'bridge_vehicle_clearance_7':not bridgegap,'beds':len(beds),'bed_pair_support_errors':bedbad,'doors':len(doors),'door_pair_frame_errors':doorbad,'game':'not_run'}
(R/'check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2));print(json.dumps(check,ensure_ascii=False),flush=True)
assert not stairbad,stairbad;assert not bad,bad;assert not walkbad,walkbad;assert not bridgegap;assert not bedbad,bedbad;assert not doorbad,doorbad
