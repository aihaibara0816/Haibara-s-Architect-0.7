"""Original industrial substation; vanilla architectural representation, no power simulation."""
from pathlib import Path
import sys,json,math,hashlib,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'deps'),str(ROOT/'src'),str(ROOT/'support')]
import numpy as np,industrial_states
from detail_lab import states as S
from vendor.voxel_core import Scene,parse_state
from vendor.inspect_build import load_build,Limits
from rail_nbt import export
R=ROOT/'runs'/sys.argv[1];R.mkdir(exist_ok=False)
SIZE=(256,64,240);sc=Scene(SIZE,max_cells=12_000_000)
owner='site';components={};rooms=[];doors=[];beds=[];stair_routes=[];walks=[];devices=[];wires=[];roads=[];equipment_pads=[]
exec((ROOT/'src/primitives_fragment.txt').read_text())
def wire(points,axis='x'):
 for a,b in zip(points,points[1:]):
  segment_axis='xyz'[max(range(3),key=lambda i:abs(b[i]-a[i]))]
  n=max(abs(b[i]-a[i]) for i in range(3))*3+1
  for t in np.linspace(0,1,int(n)):
   p=[int(round(a[i]*(1-t)+b[i]*t)) for i in range(3)]
   put(*p,'chain',axis=segment_axis)
 wires.append({'component':owner,'points':points})
def sag(a,b,drop=2):
 pts=[]
 for t in np.linspace(0,1,41):
  p=[a[i]*(1-t)+b[i]*t for i in range(3)];p[1]-=4*drop*t*(1-t);pts.append(p)
 wire(pts,'x')
def ins(x,z,y,h,tone='smooth_quartz_slab'):
 # Full-height thin stems join the wider ceramic ribs; no floating half-slab gaps.
 rib='smooth_quartz' if tone=='smooth_quartz_slab' else 'polished_andesite'
 for k in range(h):put(x,y+k,z,rib if k%2==0 else 'iron_bars')
 put(x,y+h,z,'iron_block')
 return y+h
def pad(x,z,w,d):
 box(x,4,z,x+w,7,z+d,'light_gray_concrete');equipment_pads.append([x,z,x+w,z+d])
def frame(x,z,h,w=18):
 for zz in [z-w//2,z+w//2]:
  box(x-1,5,zz-1,x+2,8,zz+2,'smooth_stone')
  box(x,8,zz,x+1,h,zz+1,'light_gray_concrete')
  for y in range(9,h-4,5):line((x,y,zz-1),(x,y+4,zz+1),'iron_bars')
 box(x,h,z-w//2,x+1,h+2,z+w//2+1,'gray_concrete')
 for zz in range(z-w//2+1,z+w//2,3):put(x,h+2,zz,'iron_bars')
def breaker(x,z,h=6):
 pad(x-2,z-8,5,17)
 for zz in [z-6,z,z+6]:
  box(x-1,7,zz-1,x+2,9,zz+2,'gray_concrete')
  ins(x,zz,9,h,'polished_andesite_slab')
  box(x-2,9+h,zz-1,x+3,10+h,zz+2,'light_gray_concrete')
  ins(x-2,zz,10+h,2);ins(x+2,zz,10+h,2)
 box(x-2,7,z+10,x+2,10,z+12,'light_gray_concrete')
 devices.append({'id':owner+'_CB_'+str(len(devices)),'kind':'three-pole circuit breaker','center':[x,7,z]})
def disconnect(x,z,y=15,opened=False):
 for zz in [z-6,z,z+6]:
  pad(x-3,zz-1,7,3)
  ins(x-2,zz,7,y-7);ins(x+2,zz,7,y-7)
  if opened:line((x-2,y+1,zz),(x,y+4,zz),'iron_bars')
  else:wire([(x-2,y+1,zz),(x+2,y+1,zz)])
 box(x-3,7,z+9,x,10,z+11,'gray_concrete')
 devices.append({'id':owner+'_DS_'+str(len(devices)),'kind':'three-phase disconnector','open_display':opened,'center':[x,7,z]})
def instruments(x,z,h=8):
 for zz in [z-6,z,z+6]:
  pad(x-1,zz-1,3,3);ins(x,zz,7,h)
  box(x-1,7+h,zz-1,x+2,9+h,zz+2,'gray_concrete')
 devices.append({'id':owner+'_IT_'+str(len(devices)),'kind':'measurement / surge protection group','center':[x,7,z]})

group('site','01 · 碎石场地、道路与电缆沟')
box(0,3,0,256,6,240,'stone')
for x in range(256):
 for z in range(240):
  k=(x//7*11+z//5*17)%19
  put(x,6,z,'cobblestone' if k<12 else 'andesite' if k<16 else 'stone')
for b in [(28,28,38,234),(236,28,246,234),(28,28,246,34),(28,174,246,182),(28,228,246,234),(114,36,122,174),(160,36,168,174),(96,180,108,240)]:
 x,z,X,Z=b;box(x,6,z,X,7,Z,'gray_concrete');roads.append(b)
for x in range(40,236,16):
 for z in [31,177,231]:box(x,6,z,x+6,7,z+1,'white_concrete')
for z in range(40,226,16):
 for x in [32,240]:box(x,6,z,x+1,7,z+6,'white_concrete')
# Covered trench grid; a short inspection opening exposes the two-cell-deep channel.
trenches=[(108,38,111,173),(169,38,172,173),(108,170,198,173),(140,75,143,189),(140,133,143,170),(51,170,54,190)]
for x,z,X,Z in trenches:
 box(x,3,z,X,4,Z,'stone_bricks');air(x,4,z,X,7,Z)
 for xx in range(x,X):
  for zz in range(z,Z):put(xx,6,zz,'smooth_stone_slab',type='top')
 for xx in [x-1,X]:box(xx,4,z,xx+1,7,Z,'light_gray_concrete')
air(108,6,150,111,7,162)
for z in range(151,161,3):put(109,4,z,'waxed_exposed_cut_copper')
for x in [107,111]:
 for z in range(149,163):put(x,7,z,'iron_bars')
for z in [149,162]:box(107,7,z,112,8,z+1,'iron_bars')

group('boundary','02 · 围栏、门卫与入口')
for z in [24,235]:
 for x in range(26,249):
  if z==235 and 95<=x<=109:continue
  put(x,7,z,'light_gray_concrete');box(x,8,z,x+1,10,z+1,'iron_bars')
for x in [26,248]:
 for z in range(24,236):put(x,7,z,'light_gray_concrete');box(x,8,z,x+1,10,z+1,'iron_bars')
for x in [94,109]:box(x,7,234,x+2,12,237,'white_concrete')
# Sliding gate parked open beside the gatehouse, leaving the 12-block entry clear.
box(79,8,235,93,10,236,'iron_bars')
box(109,6,222,122,13,228,'white_concrete');air(110,7,223,121,12,227)
box(121,9,223,122,12,227,'gray_stained_glass_pane');box(111,9,227,120,12,228,'light_blue_stained_glass_pane')
air(109,7,224,110,10,227);box(108,13,221,123,14,229,'gray_concrete');put(115,12,225,'sea_lantern')
box(113,7,223,119,8,225,'smooth_quartz');box(115,8,223,118,9,224,'black_concrete')

group('incoming','03 · 双回进线与钢构塔架')
for cz in [50,110]:
 # Four-leg tapering lattice tower, all foundations remain in the delivered site.
 for dx in [-5,5]:
  for dz in [-5,5]:box(12+dx-1,4,cz+dz-1,12+dx+2,8,cz+dz+2,'light_gray_concrete')
 for y in range(8,45):
  r=max(2,5-(y-8)//12)
  for dx in [-r,r]:
   for dz in [-r,r]:put(12+dx,y,cz+dz,'gray_concrete')
 for y in range(9,40,6):
  r=max(2,5-(y-8)//12)
  for dz in [-r,r]:line((12-r,y,cz+dz),(12+r,y+5,cz+dz),'iron_bars');line((12+r,y,cz+dz),(12-r,y+5,cz+dz),'iron_bars')
  for dx in [-r,r]:line((12+dx,y,cz-r),(12+dx,y+5,cz+r),'iron_bars');line((12+dx,y,cz+r),(12+dx,y+5,cz-r),'iron_bars')
 box(11,43,cz-11,14,45,cz+12,'gray_concrete');box(12,45,cz,13,51,cz+1,'iron_bars')
 frame(40,cz,26,22)
 for zz in [cz-6,cz,cz+6]:
  ins(12,zz,39,4);ins(40,zz,21,4)
  sag([12,39,zz],[40,21,zz],1.8)
  sag([0,43,zz],[12,39,zz],.8)

group('hv220','04 · 220 kV 进线开关场')
for cz in [50,110]:
 instruments(47,cz,9);disconnect(59,cz,16);breaker(73,cz,6);instruments(85,cz,8)
 for zz in [cz-6,cz,cz+6]:
  wire([(40,21,zz),(47,18,zz),(57,17,zz)])
  wire([(61,17,zz),(71,18,zz)]);wire([(75,18,zz),(85,17,zz)])
# Three phase longitudinal busbars, split visually at the middle coupling area.
group('bus220','05 · 220 kV 母线与预留间隔')
for bx in [94,100,106]:
 wire([(bx,23,40),(bx,23,163)],'z')
 for zz in [40,82,126,163]:
  pad(bx-1,zz-1,3,3);box(bx,7,zz,bx+1,14,zz+1,'gray_concrete');ins(bx,zz,14,8)
for cz in [50,110]:
 for j,zz in enumerate([cz-6,cz,cz+6]):wire([(85,17,zz),(94+6*j,17,zz),(94+6*j,23,zz)])
disconnect(78,143,15,True);breaker(57,143,5)

def transformer(cid,cz):
 group(cid,'06 · 一号主变压器' if cid=='T1' else '07 · 二号主变压器')
 # Gravel-filled oil containment basin, two visible rails and a continuous concrete rim.
 box(124,3,cz-14,157,4,cz+15,'stone_bricks');air(124,4,cz-14,157,7,cz+15)
 box(125,4,cz-13,156,5,cz+14,'cobblestone')
 for x in [124,156]:box(x,4,cz-14,x+1,7,cz+15,'light_gray_concrete')
 for z in [cz-14,cz+14]:box(124,4,z,157,7,z+1,'light_gray_concrete')
 for x in [137,144]:box(x,5,cz-12,x+1,8,cz+13,'gray_concrete')
 box(134,7,cz-9,147,16,cz+10,'light_gray_concrete');box(133,16,cz-10,148,17,cz+11,'gray_concrete')
 for z in range(cz-9,cz+10,2):
  for x in [128,149]:box(x,8,z,x+5,15,z+1,'light_gray_concrete');box(x+1,15,z,x+4,16,z+1,'gray_concrete')
 # Conservator cylinder along Z, supported by two brackets.
 for z in range(cz-8,cz+9):
  for x in range(139,144):
   for y in range(19,24):
    if (x-141)**2+(y-21)**2<=4:put(x,y,z,'light_gray_concrete')
 for z in [cz-6,cz+6]:box(140,17,z,143,19,z+1,'gray_concrete')
 for z in [cz-5,cz,cz+5]:ins(132,z,16,8);ins(150,z,16,5)
 # Third winding terminates in a low-voltage cable box, then a buried duct to the hall.
 box(137,8,cz+10,144,13,cz+13,'gray_concrete');wire([(140,9,cz+13),(140,5,cz+14)],'y')
 for z in [cz-16,cz+16]:box(122,7,z,159,23,z+1,'stone_bricks');box(122,23,z,159,24,z+1,'light_gray_concrete')
 box(153,7,cz+6,155,11,cz+10,'gray_concrete');box(154,9,cz+7,155,10,cz+9,'cyan_stained_glass')
 # External gauge and an access ladder with fixed backing.
 for y in range(8,17):put(147,y,cz+8,'ladder',facing='east')
 for j,z in enumerate([cz-5,cz,cz+5]):
  bx=94+6*j;hy=28+2*j
  wire([(bx,23,z),(bx,hy,z),(128,hy,z),(132,24,z)])
  bx=176+6*j;hy=26+2*j
  wire([(150,21,z),(154,hy,z),(bx,hy,z),(bx,20,z)])
 devices.append({'id':cid,'kind':'three-winding main transformer','center':[141,7,cz],'basin':[124,cz-14,157,cz+15],'firewalls_z':[cz-16,cz+16]})
transformer('T1',64);transformer('T2',122)

group('bus110','08 · 110 kV 母线与主变接口')
for bx in [176,182,188]:
 wire([(bx,20,40),(bx,20,143)],'z')
 for z in [40,89,143]:pad(bx-1,z-1,3,3);box(bx,7,z,bx+1,12,z+1,'gray_concrete');ins(bx,z,12,7)
group('outgoing110','09 · 四回 110 kV 出线间隔')
for cz in [46,74,102,130]:
 disconnect(195,cz,14);breaker(209,cz,4);instruments(221,cz,6);frame(233,cz,23,20)
 for j,zz in enumerate([cz-6,cz,cz+6]):
  wire([(176+6*j,20,zz),(193,15,zz)])
  wire([(197,15,zz),(207,16,zz)]);wire([(211,16,zz),(221,15,zz),(233,20,zz)])
  ins(233,zz,18,4);sag([233,20,zz],[255,24,zz],1)

group('compensation','10 · 电容器组与电抗器')
pad(177,149,57,22)
rail(177,149,233,170,7)
for x in [182,199]:
 for z in [153,160]:
  box(x,7,z,x+12,8,z+6,'gray_concrete')
  for y in [9,12]:
   box(x, y-1,z,x+12,y,z+6,'gray_concrete')
   for xx in range(x+1,x+11,3):box(xx,y,z+1,xx+2,y+2,z+5,'white_concrete');put(xx,y+2,z+2,'iron_bars')
for z in [154,161,168]:
 cyl(224,z,3,8,12,'waxed_exposed_cut_copper',True);disk(224,z,2,7,'smooth_stone')
air(177,7,157,178,10,162)

group('services','11 · 消防水、泵房与事故集油设施')
pad(124,150,33,21)
for x in [132,148]:
 cyl(x,160,5,7,16,'white_concrete',True);disk(x,160,5,7,'light_gray_concrete');disk(x,160,5,16,'white_concrete');ring(x,160,5,11,'cyan_concrete')
box(42,7,157,61,14,171,'white_concrete');air(43,7,158,60,13,170);box(41,14,156,62,15,172,'gray_concrete')
air(48,7,170,52,10,171);put(50,13,164,'sea_lantern')
box(46,7,160,50,10,164,'cyan_concrete');box(54,7,160,58,10,164,'gray_concrete')
box(68,4,154,98,7,171,'light_gray_concrete')
for x in [73,84,93]:box(x,6,159,x+3,7,165,'iron_trapdoor')

def hall(cid,title,x,z,w,d,levels=1):
 group(cid,title);X=x+w;Z=z+d;top=7+levels*6
 box(x,4,z,X,top,Z,'white_concrete');air(x+1,7,z+1,X-1,top-1,Z-1)
 for f in range(levels):
  fy=7+f*6;box(x+1,fy-1,z+1,X-1,fy,Z-1,'smooth_stone')
  if f:box(x+1,fy-2,z+1,X-1,fy-1,Z-1,'white_concrete')
  for zz in [z,Z-1]:
   for a,b in [(x+10,X-16),(X-11,X-3)]:box(a,fy+1,zz,b,fy+4,zz+1,'gray_stained_glass_pane')
   box(x,fy+4,zz,X,fy+5,zz+1,'light_gray_concrete')
  for xx in range(x+6,X-4,9):
   for zz in range(z+5,Z-4,10):box(xx,fy+4,zz,xx+3,fy+5,zz+2,'sea_lantern')
  rooms.append({'id':cid+'_F'+str(f+1),'floor_y':fy,'bounds':[x,fy,z,X,fy+5,Z],'use':title})
 box(x-1,top,z-1,X+1,top+1,Z+1,'white_concrete')
 for xx in [x,X-1]:box(xx,7,z,xx+1,top,Z,'gray_concrete')
 for xx in [x+9,X-3]:box(xx,7,Z,xx+2,top,Z+1,'white_concrete')
 # Main entrance and an exit toward the yard; all have fixed supported walkways.
 for zz in [z,Z-1]:
  air(X-13,7,zz,X-8,11,zz+1)
  box(X-14,11,zz-2,X-6,12,zz+3,'cyan_concrete')
 for xx in range(X-13,X-8):
  for zz in range(Z-2,Z+5):box(xx,6,zz,xx+1,7,zz+1,'smooth_stone');walks.append((xx,7,zz))
 for f in range(levels-1):
  fy=7+f*6
  air(x+3,fy+3,z+4,x+6,fy+7,z+13)
  for i in range(6):
   for xx in range(x+3,x+6):
    if i:box(xx,fy,z+11-i,xx+1,fy+i,z+12-i,'smooth_stone')
    put(xx,fy+i,z+11-i,'smooth_quartz_stairs',facing='north')
  box(x+3,fy+5,z+4,x+6,fy+6,z+6,'smooth_stone')
  box(x+6,fy+5,z+5,x+9,fy+6,z+13,'smooth_stone')
  stair_routes.append({'x':x+3,'z':z+11,'floor_y':fy,'width':3,'component':cid})
 components[cid].update(levels=levels,floors=[6+6*f for f in range(levels)])

hall('control','12 · 两层主控、继保与值班楼',40,185,54,37,2)
group('control',components['control']['name'])
# Downstairs: control desks and wall diagram, separated battery/service room.
box(66,7,186,67,12,210,'light_gray_concrete');air(66,7,205,67,10,209)
for x in [72,81]:
 for z in [193,202]:
  box(x,7,z,x+6,8,z+2,'gray_concrete');box(x,8,z,x+5,9,z+1,'black_concrete')
  put(x+2,7,z+3,'dark_oak_stairs',facing='north')
box(70,8,186,80,11,187,'black_concrete')
for x in range(72,80,4):box(x,9,187,x+2,10,188,'cyan_concrete')
for x in [53,58]:
 for z in range(190,204,4):box(x,7,z,x+3,9,z+3,'gray_concrete');put(x+1,9,z+1,'red_concrete')
# Upstairs: relay panel room with walkable central and end aisles.
for x in range(54,86,4):
 for z in [190,201]:
  box(x,13,z,x+3,17,z+2,'light_gray_concrete');box(x,14,z+2,x+2,16,z+3,'black_concrete');put(x+2,15,z+2,'cyan_concrete')
bench(57,13,216,10);box(76,13,214,84,14,217,'dark_oak_planks')
for x in [51,89]:
 for z in range(188,219):walks.append((x,13,z))

hall('mv_hall','13 · 10 kV 配电与十二回出线柜',112,185,82,37,1)
group('mv_hall',components['mv_hall']['name'])
for j in range(12):
 x=119+(j%6)*11;z=191+(j//6)*14
 box(x,7,z,x+7,11,z+3,'light_gray_concrete');box(x,8,z+3,x+5,10,z+4,'black_concrete');put(x+5,9,z+3,'cyan_concrete')
 box(x,11,z,x+7,12,z+3,'gray_concrete')
 devices.append({'id':'MV'+str(j+1).zfill(2),'kind':'10 kV feeder cabinet architectural proxy','center':[x,7,z]})
for x in range(116,191):
 for z in [198,199,214,215]:walks.append((x,7,z))
for x in [132,175]:box(x,14,194,x+8,16,199,'gray_concrete')

hall('workshop','14 · 检修工器具与备品库',204,185,32,37,1)
group('workshop',components['workshop']['name'])
for z in range(190,211,7):
 box(207,7,z,214,8,z+3,'gray_concrete');box(207,9,z,214,10,z+3,'gray_concrete')
 for x in [208,211]:box(x,8,z,x+2,9,z+2,'dark_oak_planks')
box(222,7,190,232,8,193,'dark_oak_planks');put(225,8,191,'anvil',facing='east');put(230,8,191,'barrel',facing='south')

group('lighting','15 · 道路低灯、工作照明与避雷针')
# Low path lights and work lighting on the equipment-facing building eaves.
lightpoints=[]
for x in [30,120,162,244]:
 for z in range(38,174,18):
  put(x,6,z,'sea_lantern');lightpoints.append([x,6,z])
for x in range(40,238,16):
 for z in [180,228]:put(x,6,z,'sea_lantern');lightpoints.append([x,6,z])
for x,z in [(24,30),(250,30),(24,173),(250,173)]:
 box(x,7,z,x+1,31,z+1,'gray_concrete');box(x,31,z,x+1,42,z+1,'iron_bars');put(x,41,z,'iron_block')
 for xx in [x-2,x+2]:box(xx,19,z,xx+1,20,z+1,'sea_lantern')
 box(x-2,20,z,x+3,21,z+1,'gray_concrete')

group('landscape','16 · 入口树池与员工休息点')
for x in [47,65,219]:
 box(x-2,6,224,x+3,7,228,'smooth_stone');box(x-1,7,225,x+2,8,228,'grass_block');box(x,8,225,x+1,13,226,'oak_log')
 for y,r in [(11,2),(12,3),(13,2),(14,1)]:disk(x,225,r,y,'oak_leaves')
bench(52,7,224,8)

S.connect(sc)
for st in set(sc.blocks.values()):S.validate(st)
sha=export(sc,{},R/'Substation01.nbt')
rb=load_build(R/'Substation01.nbt',Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024));assert rb.blocks==sc.blocks
names=list(components);ids={n:i+1 for i,n in enumerate(names)};owners=np.zeros((SIZE[1],SIZE[2],SIZE[0]),np.uint8)
for (x,y,z),cid in sc.owners.items():owners[y,z,x]=ids[cid]
np.savez_compressed(R/'owners.npz',owners=owners)
for cid in names:
 a=np.argwhere(owners==ids[cid]);lo=a.min(0);hi=a.max(0)+1
 components[cid].update(w=int(hi[2]-lo[2]),d=int(hi[1]-lo[1]),geometry_bounds=[[int(lo[2]),int(hi[2])],[int(lo[0]),int(hi[0])],[int(lo[1]),int(hi[1])]],blocks=len(a));components[cid].setdefault('levels',1);components[cid].setdefault('floors',[6])
sp={'id':'Substation01','title':'新港枢纽变电站','size_xyz':SIZE,'source_nbt_sha256':sha,'spawn_local':[102,7,238],'world_y_offset':58,'buildings':list(components.values()),'main_transformers':2,'voltage_theme':'220 / 110 / 10 kV','vanilla_only':True,'power_simulation':False,'game':'not_run','revision':R.name}
for name,obj in [('spec.json',sp),('rooms.json',rooms),('access.json',{'stairs':stair_routes,'walks':walks,'roads':roads}),('equipment.json',{'devices':devices,'conductors':wires,'pads':equipment_pads,'trenches':trenches,'lightpoints':lightpoints}),('check.json',{'source_nbt_sha256':sha,'independent_nbt_equal':True,'blocks':len(sc.blocks),'palette':len(set(sc.blocks.values())),'vanilla_only':all(s.startswith('minecraft:') for s in sc.blocks.values()),'game':'not_run'})]:
 (R/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
print(json.dumps({'blocks':len(sc.blocks),'sha':sha,'components':len(components),'devices':len(devices)},ensure_ascii=False))
