"""Small HAF interior recipe consumer, v0.2. Callback must accept x,y,z,state,owner.
Authored recipes, not arbitrary room layout. Coordinates: floor block y=0, first air y=1.
All interaction labels remain vanilla_unverified until an actual client test.
"""
from dataclasses import dataclass,field

def state(name,**props):
 return 'minecraft:'+name+('['+','.join(k+'='+str(v).lower() for k,v in sorted(props.items()))+']' if props else '')
@dataclass
class InteriorKit:
 emit:object
 origin:tuple=(0,0,0)
 prefix:str='room'
 components:list=field(default_factory=list)
 block_entities:dict=field(default_factory=dict)
 def put(self,x,y,z,name,owner_part,**props):
  q=tuple(a+b for a,b in zip((x,y,z),self.origin));s=name if name.startswith('minecraft:') else state(name,**props)
  self.emit(*q,s,self.prefix+'.'+owner_part);return q
 def cube(self,lo,hi,name,part,**props):
  for x in range(lo[0],hi[0]):
   for y in range(lo[1],hi[1]):
    for z in range(lo[2],hi[2]):self.put(x,y,z,name,part,**props)
 def record(self,id,kind,bounds,use_points=(),interaction='decorative'):
  o=self.origin;self.components.append(dict(id=self.prefix+'.'+id+'.'+kind+'.'+'_'.join(map(str,bounds[:3])),recipe=kind,bounds_xyz=[bounds[i]+o[i%3] for i in range(6)],use_points=[[a+b for a,b in zip(p,o)] for p in use_points],interaction=interaction))
 def barrel(self,x,y,z,facing='south',id='storage'):
  q=self.put(x,y,z,'barrel',id,facing=facing,open=False);self.block_entities[q]={'id':'minecraft:barrel','Items':[]}
  dx,dz={'south':(0,1),'north':(0,-1),'east':(1,0),'west':(-1,0)}[facing]
  self.record(id,'storage_container',[x,y,z,x+1,y+1,z+1],[(x+dx,1,z+dz)],'vanilla_unverified')
 def cupboard(self,x,z,w=3,id='cupboard'):
  for xx in range(x,x+w):
   for y in [1,2]:self.barrel(xx,y,z,id=id)
   self.put(xx,3,z,'spruce_slab',id,type='bottom',waterlogged=False)
  self.record(id,'storage_wall',[x,1,z,x+w,4,z+1],[(x+i,1,z+1) for i in range(w)],'vanilla_unverified')
 def shelf(self,x,z,w=4,h=3,id='books'):
  self.cube((x,1,z),(x+w,1+h,z+1),'bookshelf',id)
  for xx in range(x,x+w):self.put(xx,h+1,z,'oak_slab',id,type='bottom',waterlogged=False)
  self.record(id,'bookshelf_group',[x,1,z,x+w,h+2,z+1],[(xx,1,z+1) for xx in range(x,x+w)])
 def counter(self,x,z,w=5,id='counter',material='spruce_planks'):
  self.cube((x,1,z),(x+w,2,z+1),material,id)
  for xx in range(x,x+w):self.put(xx,1,z+1,'oak_trapdoor',id,facing='north',half='bottom',open=True,powered=False,waterlogged=False)
  self.record(id,'service_counter',[x,1,z,x+w,2,z+2],[(x,1,z+2),(x+w-1,1,z-1)])
 def table(self,x,z,w=3,d=2,id='table',material='spruce',low=False):
  for xx in range(x,x+w):
   for zz in range(z,z+d):
    if not low and xx in [x,x+w-1]:self.put(xx,1,zz,material+'_stairs',id,facing='east' if xx==x else 'west',half='top',shape='straight',waterlogged=False)
    else:self.put(xx,1,zz,material+'_slab',id,type='bottom' if low else 'top',waterlogged=False)
  self.record(id,'low_table' if low else 'dining_table',[x,1,z,x+w,2,z+d])
 def chair(self,x,z,facing='north',material='spruce',id='chair'):
  # Semantic facing is the seated person's gaze; stair high half is the back.
  stair_facing={'north':'south','south':'north','east':'west','west':'east'}[facing]
  self.put(x,1,z,material+'_stairs',id,facing=stair_facing,half='bottom',shape='straight',waterlogged=False)
  self.record(id,'seat',[x,1,z,x+1,2,z+1],interaction='decorative')
 def bed(self,x,z,id='bed',color='white'):
  for part,zz in [('foot',z),('head',z-1)]:
   q=self.put(x,1,zz,color+'_bed',id,facing='north',part=part,occupied=False);self.block_entities[q]={'id':'minecraft:bed'}
  self.record(id,'bed',[x,1,z-1,x+1,2,z+1],[(x+1,1,z)],'vanilla_unverified')
 def furnace(self,x,z,id='stove'):
  q=self.put(x,1,z,'furnace',id,facing='south',lit=False);self.block_entities[q]={'id':'minecraft:furnace','Items':[],'BurnTime':0,'CookTime':0,'CookTimeTotal':200,'RecipesUsed':{}}
  self.record(id,'cooking',[x,1,z,x+1,2,z+1],[(x,1,z+1)],'vanilla_unverified')
 def sink(self,x,z,id='sink'):
  self.put(x,1,z,'water_cauldron',id,level=3)
  self.record(id,'water_basin',[x,1,z,x+1,2,z+1],[(x,1,z+1)],'vanilla_unverified')
 def potted(self,x,y,z,id='plant'):
  self.put(x,y,z,'potted_bamboo',id);self.record(id,'small_plant',[x,y,z,x+1,y+1,z+1])
 def cake(self,x,y,z,id='food'):
  self.put(x,y,z,'cake',id,bites=0);self.record(id,'food_display',[x,y,z,x+1,y+1,z+1],interaction='vanilla_unverified')
 def lantern(self,x,y,z,id='light'):
  self.put(x,y,z,'lantern',id,hanging=True,waterlogged=False)
  self.record(id,'supported_lantern',[x,y,z,x+1,y+1,z+1])
 def door(self,x,z,id='door',material='birch',facing='south',hinge='left'):
  for y,half in [(1,'lower'),(2,'upper')]:self.put(x,y,z,material+'_door',id,facing=facing,half=half,hinge=hinge,open=False,powered=False)
  self.record(id,'privacy_door',[x,1,z,x+1,3,z+1],interaction='vanilla_unverified')
