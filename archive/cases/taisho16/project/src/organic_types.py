"""Taisho15 building recipes: program-linked footprints, compact clock, reusable wings."""
import copy,random
from quarter_types import all_types as old_types,gable
from prototype_base import Study
from baseline_types import frame,seat,sign

def compact_clock():
 m=Study('Clock',17,19,1,'櫻坂時計会所｜河畔公共钟楼');m.floors=[2];m.seed=151145;m.ground();m.upper_start=[4,5]
 m.shell_rect(3,3,14,16,2,9,'bricks','polished_diorite');m.door(8,3,15);m.entry=[8,3,15]
 for z in[5,10]:
  for x,out in[(3,-1),(13,1)]:frame(m,'z',x,z,z+3,4,3,out,'quartz')
 for x,z in[(3,3),(13,3),(3,15),(13,15)]:m.box((x,3,z),(x+1,10,z+1),'smooth_quartz','base.pier')
 for y,x,z,X,Z in[(9,2,2,15,17),(15,3,4,14,15),(23,3,4,14,15)]:
  for xx in range(x,X):
   for zz in range(z,Z):
    if xx in[x,X-1]or zz in[z,Z-1]:m.p(xx,y,zz,'quartz_slab','cornice',type='top')
 m.box((5,10,5),(12,23,14),'white_terracotta','shaft')
 for x,z in[(5,5),(11,5),(5,13),(11,13)]:m.box((x,10,z),(x+1,23,z+1),'stripped_dark_oak_log','shaft.pier',axis='y')
 # Five-by-five dials with clipped dark corners; a restrained head continues the shaft.
 for z in[4,14]:
  for x in range(6,11):
   for y in range(17,22):m.p(x,y,z,'dark_oak_planks'if x in[6,10]and y in[17,21]else'white_concrete','clock.face')
  for x,y in[(8,19),(8,20),(8,21),(9,19),(10,19)]:m.p(x,y,z,'black_concrete','clock.hand')
  for x in range(5,12):m.p(x,16,z,'dark_oak_slab','clock.sill',type='top');m.p(x,22,z,'dark_oak_slab','clock.head',type='top')
 for x in[4,12]:
  for z in range(7,12):
   for y in range(17,22):m.p(x,y,z,'dark_oak_planks'if z in[7,11]and y in[17,21]else'white_concrete','clock.face')
  for z,y in[(9,19),(9,20),(9,21),(10,19),(11,19)]:m.p(x,y,z,'black_concrete','clock.hand')
 for y,inset in[(24,2),(25,3),(26,4),(27,5),(28,6)]:
  for x in range(inset,17-inset):
   for z in range(inset+1,18-inset):m.p(x,y,z,'dark_prismarine_slab','roof',type='top')
 m.p(8,29,9,'dark_oak_fence','finial');m.p(8,30,9,'lantern','finial',hanging=False)
 k=m.kit(2);k.table(5,4,6,1,'visitor.map','dark_oak');m.p(7,4,4,'white_carpet','map');m.addkit(k);seat(m,5,10,2,3,'green');m.lamp(10,7,11);m.use('info',10,8);m.room('info','广场导览与休息',4,4,13,15,2,4);m.h=32;m.form='clock_hall';return m

def wing(m,length,z,Z,purpose,roof='deepslate_tile',glass=False):
 """One-floor occupied side wing. Existing traffic core stays in the parent body."""
 oldw=m.w;x=oldw-4;X=oldw+length;old_d=m.d;m.w=X+3;m.d=max(m.d,Z+3)
 for xx in range(oldw,m.w):
  for zz in range(m.d):
   for y in range(3):m.p(xx,y,zz,'grass_block'if y==2 else'dirt','site')
 m.box((x,3,z),(X,8,Z),'air');m.shell_rect(x,z,X,Z,2,8,'white_terracotta','spruce_planks','wing')
 for xx in [x,X-1]:
  for zz in[z,Z-1]:m.box((xx,3,zz),(xx+1,8,zz+1),'stripped_dark_oak_log','wing.pier',axis='y')
 frame(m,'x',Z-1,x+2,X-2,4,2,1,'dark_oak');frame(m,'z',X-1,z+2,Z-2,4,2,1,'dark_oak')
 if glass:
  for xx in range(x+1,X-1):
   for zz in[z,Z-1]:
    for y in[4,5,6]:m.p(xx,y,zz,'white_stained_glass_pane','conservatory.glass')
  for xx in range(x-1,X+1):
   for zz in range(z-1,Z+1):m.p(xx,8,zz,'dark_oak_slab','conservatory.roof',type='top')
 else:gable(m,x-1,z-1,X+1,Z+1,9,'x',skin=roof)
 # New east-west connection goes through the old sidewall at a deliberately free bay.
 mid=(z+Z)//2;m.door(x,3,mid,'east');m.p(x-1,3,mid,'air');m.p(x-1,4,mid,'air');m.p(x-1,2,mid,'spruce_planks','wing.connection')
 k=m.kit(2)
 if purpose=='reading':
  k.shelf(x+3,z+1,5,3,'wing.books');k.table(x+3,Z-4,5,1,'wing.reading','dark_oak');k.chair(x+4,Z-6,'south',material='dark_oak')
 elif purpose=='bedroom':
  k.bed(x+4,z+3);k.cupboard(X-3,z+1,1,'wardrobe');seat(m,x+3,Z-4,2,3,'brown');k.table(x+3,Z-6,3,1,'private.tea','dark_oak')
 elif purpose=='classroom':
  m.box((x+2,4,z),(X-2,7,z+1),'green_wool','wing.blackboard')
  for xx in range(x+3,X-3,5):
   for zz in range(z+4,Z-3,5):k.table(xx,zz,3,1,'wing.desk','oak');k.chair(xx+1,zz+2,'north',material='oak')
 elif purpose=='greenhouse':
  for xx in range(x+3,X-2,3):
   for zz in[z+2,Z-3]:m.barrel(xx,3,zz);m.pot(xx,4,zz)
  k.table(x+3,z+5,4,1,'potting','dark_oak')
 elif purpose=='laundry':
  k.sink(x+3,z+2)
  for xx in range(x+3,X-2,3):m.barrel(xx,3,Z-3);m.p(xx,4,Z-3,'white_wool','clean.linen')
 elif purpose=='workshop':
  for xx in range(x+2,X-2,4):m.barrel(xx,3,z+1);m.barrel(xx,4,z+1)
  k.table(x+4,Z-5,7,2,'assembly','dark_oak');m.p(X-3,3,Z-3,'crafting_table','repair.station')
 elif purpose=='stock':
  for xx in range(x+3,X-2,3):
   for zz in[z+2,Z-3]:m.barrel(xx,3,zz);m.barrel(xx,4,zz)
 m.addkit(k);m.lamp((x+X)//2,6,mid);m.use('wing.'+purpose,x+2,mid);m.room('wing',purpose,x+1,z+1,X-1,Z-1,2,4);m.form='L_wing'if z<6 else'T_wing';return m

def all_types(seed):
 mods=old_types(seed);out=[]
 for m in mods:
  m.form={'Bookshop':'narrow_deep','Pharmacy':'corner_recess','Inn':'recessed_court','Station':'wide_shallow'}.get(m.id,'compact_street_house')
  if m.id=='Clock':m=compact_clock()
  elif m.id=='School':m=wing(m,16,10,25,'classroom')
  elif m.id=='Library':m=wing(m,10,3,17,'reading',roof='dark_prismarine')
  elif m.id=='Residence':m=wing(m,10,3,16,'bedroom')
  elif m.id=='Workshop':m=wing(m,17,7,20,'workshop')
  elif m.id=='Bath':m=wing(m,10,3,16,'laundry')
  elif m.id=='Sake':m=wing(m,12,3,15,'stock')
  elif m.id=='Florist':m=wing(m,8,3,16,'greenhouse',glass=True)
  # Building-level palette and opening emphasis, independent from placement and plants.
  rr=random.Random(str(seed)+'/facade/'+m.id)
  if m.id in['Textile','Photo','Residence','Tea','Sake']:
   palette={'Textile':'light_gray_terracotta','Photo':'yellow_terracotta','Residence':'white_terracotta','Tea':'white_terracotta','Sake':'brown_terracotta'}
   for q,st in list(m.blocks.items()):
    if st=='minecraft:white_terracotta'and 'wall'in m.owners.get(q,''):m.p(*q,palette[m.id],'facade.palette')
  if m.id=='Photo':m.program='写真師の家｜前店后院与主人住宅'
  m.seed=seed;m.h=max(28,max(q[1]for q in m.blocks)+2);out.append(m)
 return out
