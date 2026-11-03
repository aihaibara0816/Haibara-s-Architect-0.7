"""Additional bounded terrain/forest palette; official models checked separately."""
import town_states
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
s.FULL.update({'cobblestone','mossy_cobblestone','andesite','mossy_stone_bricks'})
s.STAIRS.update({'cobblestone_stairs','mossy_cobblestone_stairs','andesite_stairs'})
s.SLABS.update({'cobblestone_slab','mossy_cobblestone_slab','andesite_slab'})
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
EX={'spruce_log','spruce_leaves','podzol'}
def family(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 return 'leaves'if b=='spruce_leaves'else'cube'if b in EX else of(v)
def validate(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 if b=='spruce_log':assert set(p)=={'axis'}and p['axis']in{'x','y','z'};return True
 if b=='spruce_leaves':assert set(p)=={'distance','persistent','waterlogged'}and p['persistent']in s.BOOL and p['waterlogged']in s.BOOL and p['distance']in map(str,range(1,8));return True
 if b=='podzol':assert set(p)=={'snowy'}and p['snowy']in s.BOOL;return True
 return ov(v)
def make(n,**p):
 b=n.split(':')[-1]
 if b in EX:
  d={'axis':'y'}if b=='spruce_log'else{'snowy':'false'}if b=='podzol'else{'distance':'7','persistent':'true','waterlogged':'false'};d.update({k:str(v).lower()for k,v in p.items()});v=state('minecraft:'+b,**d);validate(v);return v
 return om(n,**p)
def boxes(v):
 if parse_state(v)[0].split(':')[-1]in EX:return ((0,0,0,1,1,1),)
 return ob(v)
def color(v):
 b=parse_state(v)[0].split(':')[-1]
 if b in EX:return {'spruce_log':(89,68,44),'spruce_leaves':(67,102,67),'podzol':(113,85,54)}[b]
 if 'cobblestone'in b:return (116,126,103)if'mossy'in b else(128,129,126)
 if b=='andesite':return (139,140,136)
 return oc(v)
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
