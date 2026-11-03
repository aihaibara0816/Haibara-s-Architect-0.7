"""Explicit V09 junction correction in this bounded case, not a generic slope solver."""
def apply(city,height,rawheight):
 changed=[]
 # Ten risers meet the existing west main street at y=34. Keep the doorway
 # landing at y=24 and protect the building's original door/frame geometry.
 for step in range(1,11):
  z=92-step;f=24+step-1
  for x in[60,61,62]:
   old=height[x,z]
   for y in range(min(f,old),max(f,old)+1):city.p(x,y,z,'stone'if y<f else'cobblestone'if y==f else'air','junction.earthwork')
   city.p(x,f,z,'cobblestone','junction.path');height[x,z]=f
   for y in range(f+1,max(f+4,old+2)):city.p(x,y,z,'air')
   city.p(x,f+1,z,'cobblestone_stairs','junction.step',facing='north');changed.append((x,z))
 # Complete the missing lower-road paving cell without touching interiors.
 for z in range(226,233):
  x=144;f=height[x,z];st=city.blocks.get((x,f,z),'minecraft:air')
  if st.startswith('minecraft:grass_block'):city.p(x,f,z,'cobblestone','junction.paving')
 return changed
