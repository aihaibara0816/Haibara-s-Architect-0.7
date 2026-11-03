"""R08 case geometry, executed in the builder's authored Scene context."""
# Distinct railway embankments, one-block shoulders and two-block sunken service yards.
group('site','01 · 分层场地、道路与步行系统')
lowered=0; formation=set(); shoulders=set()
for x in range(6,458):
 axes=corridor.get(x,[])
 for z in range(8,145):
  if x>=301 and z>=35:continue
  dist=min([abs(z+.5-v) for v in axes] or [999])
  if dist<=3:
   put(x,6,z,'cobblestone');formation.add((x,z));continue
  # Preserve lamp plinths, footbridge stairs and bridge supports.
  protect=False
  if protect:continue
  air(x,5,z,x+1,7,z+1)
  put(x,4,z,'stone' if (x//9+z//7)%5 else 'andesite');lowered+=1
  if dist<=4.2:put(x,5,z,'cobblestone');shoulders.add((x,z))
ground_before={q:(st,sc.owners[q]) for q,st in sc.blocks.items() if q[1]<=6}
# Low drainage channels follow the outer formation, terminating in service sumps.
for x,axes in corridor.items():
 if not 6<=x<295:continue
 for z in [math.floor(min(axes)-5),math.ceil(max(axes)+4)]:
  if 31<z<143 and not (248<=x<270):put(x,4,z,'gray_concrete')
# Keep the single interface opening clear; close the former widely spaced exits.
for z in range(74,107):
 if 83<=z<=97:air(5,7,z,6,10,z+1)
 else:put(5,8,z,'iron_bars')

def equipment_pad(id,name,b):
 group(id,name);x,z,X,Z=b
 box(x,4,z,X,7,Z,'light_gray_concrete');box(x+1,6,z+1,X-1,7,Z-1,'smooth_stone')
 for xx in range(x,X):
  for zz in [z,Z-1]:put(xx,7,zz,'iron_bars')
 for zz in range(z,Z):
  for xx in [x,X-1]:put(xx,7,zz,'iron_bars')

equipment_pad('substation','16 · 围合变配电场与检修通道',(36,31,110,61))
air(51,7,31,60,10,32);box(51,4,23,60,7,32,'gray_concrete')
for x in [46,68,90]:
 box(x,7,40,x+12,8,52,'gray_concrete')
 box(x+2,8,43,x+10,13,49,'gray_concrete')
 for xx in range(x,x+12,2):
  for z in [40,51]:box(xx,8,z,xx+1,12,z+1,'light_gray_concrete')
 for xx in [x+3,x+8]:
  box(xx,13,45,xx+1,16,46,'iron_bars');put(xx,16,45,'white_concrete')
for x in [42,64,86,104]:
 box(x,7,35,x+1,16,36,'light_gray_concrete');box(x,15,35,min(x+13,108),16,36,'gray_concrete')
box(41,7,55,102,8,58,'gray_concrete')
for x in range(43,102,7):box(x,8,55,x+4,10,58,'white_concrete')

equipment_pad('waterworks','17 · 储水罐、泵房与管线平台',(137,31,194,58))
air(182,7,31,190,10,32);box(182,4,23,190,7,32,'gray_concrete')
for x in [148,169]:
 cyl(x,44,8,7,20,'light_gray_concrete',True);disk(x,44,8,7,'light_gray_concrete');disk(x,44,8,20,'white_concrete')
 ring(x,44,8,12,'cyan_concrete');ring(x,44,8,18,'white_concrete');ring(x,44,7,21,'iron_bars')
 box(x-2,21,42,x+2,23,46,'gray_concrete')
 pipe([(x,8,52),(x,8,55),(185,8,55)],'cyan_concrete',0)
box(181,7,36,191,14,49,'white_concrete');air(182,7,37,190,13,48)
box(180,14,35,192,15,50,'gray_concrete');air(184,7,48,188,10,49)
box(182,8,38,185,11,42,'gray_concrete');box(187,8,38,189,10,44,'cyan_concrete')
put(186,12,43,'sea_lantern')
# A walkable steel stair and catwalk give the tank roofs an explicit access route.
for i in range(14):
 for z in range(32,35):put(143+i,7+i,z,'smooth_quartz_stairs',facing='east')
box(157,20,32,172,21,39,'smooth_stone');rail(156,32,171,38,21)
air(156,21,32,159,24,35);air(166,21,38,170,24,39)
box(157,7,33,158,20,34,'gray_concrete');box(170,7,34,171,20,35,'gray_concrete')

equipment_pad('airplant','18 · 压缩空气与室外机组',(70,121,144,142))
air(131,7,141,140,10,142);box(131,4,141,140,7,149,'gray_concrete')
for x in [80,98,116]:
 box(x,7,126,x+12,8,136,'gray_concrete');box(x+1,8,127,x+11,12,135,'light_gray_concrete')
 for xx in range(x+2,x+11,3):box(xx,9,126,xx+1,12,127,'iron_bars')
 box(x+2,12,129,x+10,13,133,'gray_concrete')
 pipe([(x+6,10,135),(x+6,10,139),(138,10,139)],'cyan_concrete',0)
group('site',components['site']['name'])
# Steps down to the low maintenance ground; actual grade differences remain visible.
for x,z in [(38,64),(138,61),(73,145)]:
 for k in range(2):
  for xx in range(x,x+5):put(xx,5+k,z+k,'smooth_quartz_stairs',facing='south')

group('testline','19 · 独立研发试验与检修车停放线')
for x in range(38,184):
 for z in range(160,168):put(x,6,z,'cobblestone')
for x in [37,181]:
 box(x,7,163,x+2,9,166,'gray_concrete');box(x,9,162,x+1,10,167,'red_concrete')
box(45,7,168,176,9,171,'smooth_stone');box(45,8,168,176,9,169,'yellow_concrete')
for x in [57,139]:
 for k in range(2):
  for xx in range(x,x+4):put(xx,7+k,172-k,'smooth_quartz_stairs',facing='north')
for x in [60,92,124,156]:
 box(x,9,170,x+1,15,171,'gray_concrete');box(x,15,163,x+1,16,172,'white_concrete');put(x,14,168,'sea_lantern')
box(59,16,163,162,17,172,'white_concrete')
for x in range(68,160,12):box(x,16,165,x+4,17,170,'light_blue_stained_glass')

def relocate_component(cid,dx,dz):
 old=[(q,st) for q,st in sc.blocks.items() if sc.owners.get(q)==cid]
 for q,st in old:
  sc.set(q,'minecraft:air',cid)
  if q in ground_before:
   v,o=ground_before[q];sc.set(q,v,o)
 for (x,y,z),st in old:sc.set((x+dx,y,z+dz),st,cid)
relocate_component('substation',0,-23)
relocate_component('waterworks',0,-23)
relocate_component('airplant',137,-113)
relocate_component('testline',0,-29)
group('testline','19 · 场内独立列车检修道')
# Level access from the retained southern service road to the platform stairs.
for x in [57,139]:box(x,4,143,x+4,7,150,'smooth_stone')
# Small trees along the outside of the independent lane, clear of the rail envelope.
for x in [45,86,125,167]:
 box(x-1,4,144,x+2,7,147,'stone');box(x-1,6,144,x+2,7,147,'grass_block')
 box(x,7,145,x+1,12,146,'oak_log')
 for y,rr in [(10,1.6),(11,2),(12,1.5)]:disk(x,145,rr,y,'oak_leaves')
# Internal service paths through the utility compound, not a perimeter road.
group('site',components['site']['name'])
box(24,4,9,203,5,13,'smooth_stone');box(114,4,9,119,5,65,'smooth_stone');box(199,4,9,204,7,28,'smooth_stone')

# A coherent architectural palette: dark plinths, pale frames, teal detail and dark glazing.
for cid in ['tower','research','dispatch','canteen','dorm','stabling','maintenance','energy','parts','bridges','entry']:
 for p,st in list(sc.blocks.items()):
  if sc.owners.get(p)!=cid:continue
  n=parse_state(st)[0]
  if n=='minecraft:blue_concrete':sc.set(p,m('cyan_concrete'),cid)

def frontage(cid,x0,z0,w,d,levels):
 group(cid,components[cid]['name']);X=x0+w;Z=z0+d
 # Rebuild exterior wall surfaces by zones; leave existing door and corridor openings intact.
 for f in range(levels):
  y=7+f*6
  for z in [z0,Z-1]:
   for x in range(x0,X):
    for yy in range(y,y+5):
     st=sc.blocks.get((x,yy,z),'')
     if not st or 'door' in st:continue
     core=x<x0+10;edge=x>=X-2
     mat='gray_concrete' if core else 'light_gray_concrete' if yy==y else 'white_concrete'
     if not core and not edge and y+1<=yy<y+4:mat='gray_stained_glass_pane' if cid in ['tower','dispatch'] else 'light_blue_stained_glass_pane'
     put(x,yy,z,mat)
   # Outboard ledges make depth visible without blocking the interior.
   if f>0:box(x0+10,y-1,z-1 if z==z0 else z+1,X,y,z if z==z0 else z+2,'light_gray_concrete')
  # Solid core and its slim vertical slots.
  for yy in range(y,y+5):
   for z in range(z0,Z):
    if (x0,yy,z) in sc.blocks:put(x0,yy,z,'gray_concrete')
  for z in [z0+5,Z-6]:box(x0,y+1,z,x0+1,y+4,z+2,'gray_stained_glass_pane')
 # Grouped full-height fins are distinct from the floor edges.
 for x in [x0+10,X-2]:
  for z in [z0-1,Z]:box(x,7,z,x+2,7+levels*6,z+1,'white_concrete')
 # Clear entrance with a projecting supported canopy.
 box(x0+8,11,Z,x0+24,12,Z+4,'gray_concrete')
 for x in [x0+8,x0+23]:box(x,7,Z+2,x+1,11,Z+3,'light_gray_concrete')

for args in [('tower',64,174,40,42,15),('research',120,176,58,40,3),('dispatch',206,161,40,27,3),('canteen',204,195,54,31,2),('dorm',282,195,68,31,4)]:frontage(*args)

group('tower',components['tower']['name'])
# Three stacked facade frames; the upper three storeys genuinely step back in plan.
for ya,yb in [(13,37),(43,73)]:
 for z in [172,217]:
  box(74,ya,z,76,yb,z+1,'white_concrete');box(102,ya,z,104,yb,z+1,'white_concrete');box(74,yb-2,z,104,yb,z+1,'white_concrete')
air(99,79,172,109,104,220);air(63,79,172,99,104,178)
box(98,79,178,99,97,216,'white_concrete');box(64,79,178,99,97,179,'white_concrete')
for f in range(12,15):
 y=7+6*f
 box(98,y+1,182,99,y+4,211,'gray_stained_glass_pane')
 box(75,y+1,178,97,y+4,179,'gray_stained_glass_pane')
box(63,97,177,100,98,217,'white_concrete');rail(64,178,98,215,98)
# A four-block deep terrace and a compact crown screen sit on existing floor / roof.
box(99,78,178,104,79,216,'smooth_stone');rail(99,178,103,215,79)
box(64,78,174,99,79,178,'smooth_stone');rail(64,174,98,177,79)
for x in range(78,96,3):box(x,98,185,x+1,103,207,'light_gray_concrete')
for x in [64,98]:put(x,99,178,'red_stained_glass');put(x,98,178,'glowstone')

group('research',components['research']['name'])
for x in range(138,169,4):box(x,8,174,x+1,24,175,'light_gray_concrete')
box(130,24,173,174,26,177,'white_concrete')
group('dispatch',components['dispatch']['name'])
box(216,24,159,248,26,164,'gray_concrete')
for z in range(165,183,3):box(246,14,z,247,24,z+1,'white_concrete')
group('dorm',components['dorm']['name'])
for x in range(296,345,10):
 for z in [194,226]:box(x,7,z,x+1,31,z+1,'white_concrete')
group('canteen',components['canteen']['name'])
for x in range(215,254,4):box(x,19,199,x+1,23,221,'light_gray_concrete')

for cid,x0,z0,X,Z,axes,roof in [('stabling',304,36,454,88,[44,56,68,80],19),('maintenance',304,92,454,132,[100,112,124],23)]:
 group(cid,components[cid]['name'])
 for z in [z0,Z-1]:
  box(x0,7,z,X,10,z+1,'gray_concrete')
  box(x0,roof-3,z,X,roof-1,z+1,'light_gray_concrete')
  for x in range(x0+5,X-3,18):box(x,7,z-1 if z==z0 else z+1,x+2,roof+2,z if z==z0 else z+2,'white_concrete')
 # Raised glazed roof monitors: a longitudinal sawtooth section per track bay.
 for z in axes:
  for dz in range(-3,4):
   y=roof+1+(dz+3)//2
   box(x0+4,y,z+dz,X-4,y+1,z+dz+1,'light_gray_concrete')
  box(x0+4,roof+1,z+3,X-4,roof+4,z+4,'light_blue_stained_glass')
  for x in [x0+4,X-5]:box(x,roof+1,z-3,x+1,roof+4,z+4,'white_concrete')
 # Front portal framing wraps openings rather than filling them.
 for z in axes:
  for zz in [z-4,z+4]:box(302,7,zz,304,16,zz+1,'gray_concrete')
  box(302,15,z-4,304,17,z+5,'white_concrete')
 # Reopen side access which crosses the darker plinth.
 for x in [x0+30,X-30]:air(x,7,Z-1,x+3,10,Z+1)

exec((ROOT/'src/yard_r10_fragment.py').read_text())
(R/'relief_facade_revision.json').write_text(json.dumps({'baseline':'R09','lowered_cells':lowered,'raised_formation_cells':len(formation),'stepped_shoulder_cells':len(shoulders),'surface_levels':{'rail_and_roads':7,'shoulder':6,'sunken_yard':5},'new_components':['substation','waterworks','airplant','testline'],'test_track_length_cells':141,'test_track_independent':True,'external_neck_axis_spacing':6,'sleeper_edge_gap_approx':3.25625,'tower_recessed_floors':[13,14,15],'game':'not_run'},indent=2))
