def chamfer(m,r):
 # Six-block diagonal corner, continuous through the upper facade and coping.
 # Relocate plant groups before cutting; do not simply delete an occupied room.
 for f in m.floors[1:]:
  for x,z in [(20,24),(20,23)]:
   if (x,f+1,z)in m.blocks:
    for dy in [1,2]:m.p(x,f+dy,z,'air')
  if (19,f+1,20)not in m.blocks:m.barrel(19,f+1,20);m.pot(19,f+2,20)
 for q in list(m.blocks):
  x,y,z=q
  if x+z>44 and (y>=9 or x>=18 and z>=24):m.p(*q,'air')
 top=15 if m.levels==2 else 21
 for x in range(16,23):
  z=44-x
  for f,up in zip(m.floors[1:],m.floors[2:]+[top]):
   for y in range(f+1,up):m.p(x,y,z,r['wall'],'chamfer.wall')
   for y in [f+2,f+3]:
    if x not in [16,19,22]:m.p(x,y,z,'cyan_stained_glass','chamfer.glazing')
   m.p(x,f,z,'smooth_quartz','chamfer.band')
  for y in [9,top]:m.p(x,y,z,'smooth_quartz','chamfer.cornice')
  for y in [top+1,top+2]:m.p(x,y,z,r['wall'],'chamfer.parapet')
  m.p(x,top+3,z,'quartz_slab','chamfer.coping',type='top')
 # Clear obsolete pier and use the diagonal ends as structural piers.
 for x,z in [(20,27),(22,19)]:
  for y in range(3,9):m.p(x,y,z,'air')
 for x,z in [(16,28),(22,22)]:
  m.p(x,3,z,'polished_andesite','chamfer.pier')
  for y in range(4,8):m.p(x,y,z,'quartz_pillar','chamfer.pier',axis='y')
  m.p(x,8,z,'chiseled_quartz_block','chamfer.cap')
 # Recorded lights must remain under a solid soffit.
 for lamp in m.lights:
  x,y,z=lamp['position']
  if x+z>44 and x>=18:
   m.p(x,y,z,'air');m.p(*lamp['support'],'air');lamp['position'][0]-=3;lamp['support'][0]-=3
   m.p(*lamp['position'],'lantern','corner.light',hanging=True);m.p(*lamp['support'],'chain','corner.chain',axis='y')
 m.variation=[q for q in m.variation if sum(q['position'][::2])<44]
 return m
