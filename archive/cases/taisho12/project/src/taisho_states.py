"""Small additional palette for the three Taisho studies; not a universal block registry."""
import terrain_states
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
s.FULL.update({'green_terracotta','birch_planks','light_blue_concrete','yellow_concrete','brown_wool','light_gray_wool','stripped_birch_log','white_wool','black_wool','gray_wool'})
s.FULL.update({'dark_prismarine','green_wool'})
s.SLABS.update({'dark_prismarine_slab'})
s.STAIRS.update({'dark_prismarine_stairs'})
s.WALLS.update({'brick_wall'})
s.SLABS.update({'birch_slab','brick_slab'})
s.STAIRS.update({'birch_stairs','brick_stairs'})
s.TRAPS.update({'birch_trapdoor','spruce_trapdoor'})
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
EX={'rail','polished_diorite'}
def family(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 return 'rail'if b=='rail'else'cube'if b=='polished_diorite'else of(v)
def validate(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 if b=='rail':assert set(p)=={'shape','waterlogged'}and p['shape']in{'east_west','north_south'}and p['waterlogged']=='false';return True
 if b=='stripped_birch_log':assert p.get('axis')in{'x','y','z'}and len(p)==1;return True
 if b=='polished_diorite':assert not p;return True
 return ov(v)
def make(n,**p):
 b=n.split(':')[-1]
 if b in EX or b=='stripped_birch_log':
  d={'shape':'east_west','waterlogged':'false'}if b=='rail'else{'axis':'y'}if b=='stripped_birch_log'else{};d.update({k:str(v).lower()for k,v in p.items()});v=state('minecraft:'+b,**d);validate(v);return v
 return om(n,**p)
def boxes(v):
 if parse_state(v)[0]=='minecraft:rail':return ()
 return ob(v)
def color(v):
 b=parse_state(v)[0].split(':')[-1]
 if b=='rail':return(143,137,119)
 if b=='black_wool':return(30,32,37)
 if b=='green_terracotta':return(116,126,62)
 if b=='polished_diorite':return(204,204,196)
 if b=='light_blue_concrete':return(121,163,182)
 if b in['birch_planks','stripped_birch_log']:return(202,187,134)
 if b=='polished_diorite':return(204,204,196)
 return oc(v)
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
