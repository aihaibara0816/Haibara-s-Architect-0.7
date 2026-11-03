"""Bounded vanilla palette; plant preview envelopes are approximations, not textures."""
import rural_states,japanese_detail_states,corner_states
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
POTS={'potted_fern','potted_azalea_bush','potted_flowering_azalea_bush'}
def family(v):
 n,p=parse_state(v)
 if n=='minecraft:sea_pickle':return 'pickle'
 return 'potted' if n.split(':')[-1] in POTS else of(v)
def validate(v):
 n,p=parse_state(v)
 if n=='minecraft:sea_pickle':
  assert set(p)=={'pickles','waterlogged'} and p['pickles'] in {'1','2','3','4'} and p['waterlogged'] in {'false','true'};return True
 if n.split(':')[-1] in POTS:
  if p:raise ValueError(v)
  return True
 return ov(v)
def make(n,**p):
 if n.split(':')[-1]=='sea_pickle':
  q={'pickles':'1','waterlogged':'false'};q.update(p);v=state('minecraft:sea_pickle',**q);validate(v);return v
 if n.split(':')[-1] in POTS:
  v=state('minecraft:'+n.split(':')[-1],**p);validate(v);return v
 return om(n,**p)
def boxes(v):
 n,p=parse_state(v)
 if n=='minecraft:sea_pickle':return ((.1,0,.1,.9,.4,.9),)
 if n.split(':')[-1] in POTS:
  # Pot plus a bounded leafy silhouette, no claim of exact vanilla alpha geometry.
  return ((.3125,0,.3125,.6875,.375,.6875),(.44,.35,.44,.56,.75,.56),(.18,.48,.38,.82,.58,.62),(.38,.55,.18,.62,.65,.82),(.29,.66,.29,.71,.77,.71))
 return ob(v)
def color(v):
 n,p=parse_state(v)
 if n=='minecraft:sea_pickle':return (124,130,66)
 if n.split(':')[-1] in POTS:return (93,129,66)
 return oc(v)
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
