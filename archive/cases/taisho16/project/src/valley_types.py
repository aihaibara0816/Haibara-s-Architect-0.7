"""Preserve 17 improved T15 modules; retire the rejected tower for a village hall."""
from organic_types import all_types as inherited
from prototype_base import Study
from baseline_types import frame,seat,sign
from quarter_types import gable
def hall(seed):
 m=Study('Hall',29,26,1,'溪橋会所｜集会・导览・休憩');m.seed=seed;m.ground();m.floors=[2];m.upper_start=[8,9]
 m.shell_rect(3,3,26,22,2,9,'white_terracotta','spruce_planks')
 for x in[3,10,18,25]:
  for z in[3,21]:m.box((x,3,z),(x+1,10,z+1),'stripped_dark_oak_log','frame',axis='y')
 for z in[3,21]:
  for a,b in[(5,9),(11,15),(19,24)]:frame(m,'x',z,a,b,4,3,-1 if z==3 else 1,'dark_oak')
 for x in[3,25]:frame(m,'z',x,6,17,4,3,-1 if x==3 else 1,'dark_oak')
 m.door(16,3,21);m.entry=[16,3,21];gable(m,1,1,28,24,10,'x');gable(m,13,20,20,25,7,'z')
 k=m.kit(2);k.table(8,10,8,2,'community.meeting','dark_oak')
 for x in[8,11,14]:k.chair(x,8,'south',material='dark_oak');k.chair(x,14,'north',material='dark_oak')
 k.shelf(5,4,7,3,'community.books');k.table(20,16,3,1,'community.info','dark_oak');k.cupboard(22,4,2,'stores');k.sink(21,7)
 m.addkit(k);seat(m,5,18,2,5,'green');m.picture(10,5,20,'north','plant')
 for x,z in[(8,6),(17,9),(20,17)]:m.lamp(x,7,z)
 m.pot(23,3,19);m.pot(5,3,5);sign(m,16,6,22,['溪橋会所'])
 m.room('main','集会、阅读与旅行导览',4,4,25,21,2,12);m.use('entry',16,20);m.use('meeting',17,12);m.use('info',21,18)
 m.h=28;m.form='wide_public_hall';return m
def all_types(seed):return [hall(seed)if m.id=='Clock'else m for m in inherited(seed)]
