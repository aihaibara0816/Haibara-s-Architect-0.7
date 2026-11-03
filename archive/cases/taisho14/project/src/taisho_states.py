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

# Taisho13 bounded additions, checked against official 1.21.1 models.
import rural_states
rural_states.LOGS.update({'stripped_dark_oak_log','cherry_log'})
rural_states.BANNERS.add('green_wall_banner')
s.FULL.add('chiseled_stone_bricks')
bf,bv,bm,bb,bc=s.family,s.validate,s.make,s.boxes,s.color

def t13family(v):return 'button'if parse_state(v)[0]=='minecraft:stone_button'else bf(v)
def t13validate(v):
 name,p=parse_state(v)
 if name=='minecraft:stone_button':
  assert set(p)=={'face','facing','powered'}and p['face']=='wall'and p['facing']in s.DIRS and p['powered']in s.BOOL;return True
 return bv(v)
def t13make(name,**p):
 if name.split(':')[-1]=='stone_button':
  q={'face':'wall','facing':'south','powered':'false'};q.update({k:str(v).lower()for k,v in p.items()});return state('minecraft:stone_button',**q)
 return bm(name,**p)
def t13boxes(v):
 name,p=parse_state(v)
 if name=='minecraft:stone_button':
  return ({'south':(.3125,.375,0,.6875,.625,.125),'north':(.3125,.375,.875,.6875,.625,1),'east':(0,.375,.3125,.125,.625,.6875),'west':(.875,.375,.3125,1,.625,.6875)}[p['facing']],)
 return bb(v)
def t13color(v):
 name,p=parse_state(v)
 if name=='minecraft:stone_button':return(130,130,130)
 if name=='minecraft:cherry_log':return(93,62,65)
 if name=='minecraft:stripped_dark_oak_log':return(92,69,42)
 return bc(v)
s.family,s.validate,s.make,s.boxes,s.color=t13family,t13validate,t13make,t13boxes,t13color
base_connect=s.connect

def t13connect(scene):
 count=base_connect(scene)
 for q,v in list(scene.blocks.items()):
  if s.family(v)!='fence':continue
  name,p=parse_state(v)
  for direction,delta in s.DIRS.items():
   other=scene.blocks.get(tuple(q[i]+delta[i]for i in range(3)),'minecraft:air')
   p[direction]='true'if s.family(other)=='fence'or s.support_cube(other)else'false'
  new=state(name,**p);count+=new!=v;scene.blocks[q]=new
 return count
s.connect=t13connect
