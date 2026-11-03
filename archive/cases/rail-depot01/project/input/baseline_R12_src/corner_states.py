"""Bounded Java 1.21.1 vocabulary. Previews remain box approximations."""
import rural_states,interior_lab_states
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
s.FULL.update({'polished_diorite','diorite','cut_copper','green_terracotta'})
def family(v):
 n,p=parse_state(v)
 return 'sign' if n=='minecraft:oak_wall_sign' else of(v)
def validate(v):
 n,p=parse_state(v)
 if n=='minecraft:oak_wall_sign':
  assert set(p)=={'facing','waterlogged'} and p['facing'] in s.DIRS and p['waterlogged'] in s.BOOL;return True
 return ov(v)
def make(n,**p):
 if n.split(':')[-1]=='oak_wall_sign':
  q={'facing':'south','waterlogged':'false'};q.update({k:str(v).lower() for k,v in p.items()});return state('minecraft:oak_wall_sign',**q)
 return om(n,**p)
def boxes(v):
 n,p=parse_state(v)
 if n=='minecraft:oak_wall_sign':return ({'south':(0,.25,0,1,.75,.125),'north':(0,.25,.875,1,.75,1),'east':(0,.25,0,.125,.75,1),'west':(.875,.25,0,1,.75,1)}[p['facing']],)
 return ob(v)
def color(v):
 n,p=parse_state(v);cs={'minecraft:polished_diorite':(201,201,188),'minecraft:diorite':(195,195,183),'minecraft:cut_copper':(176,103,69),'minecraft:green_terracotta':(99,109,60),'minecraft:oak_wall_sign':(166,128,80)}
 return cs[n] if n in cs else oc(v)
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
