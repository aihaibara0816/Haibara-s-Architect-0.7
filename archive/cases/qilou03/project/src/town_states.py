"""Bounded 1.21.1 groundcover extension. Collision is approximate; assets checked locally."""
import room_states
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
FLOWERS={'short_grass','fern','dandelion','cornflower','azure_bluet','allium','blue_orchid'}
def family(v):
 n,p=parse_state(v);return 'groundcover' if n.split(':')[-1]in FLOWERS|{'tall_grass','large_fern'} else of(v)
def validate(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 if b in FLOWERS:assert not p;return True
 if b in {'tall_grass','large_fern'}:assert set(p)=={'half'} and p['half']in{'lower','upper'};return True
 return ov(v)
def make(n,**p):
 b=n.split(':')[-1]
 if b in FLOWERS|{'tall_grass','large_fern'}:
  if b in {'tall_grass','large_fern'}:p={'half':'lower',**p}
  v=state('minecraft:'+b,**p);validate(v);return v
 return om(n,**p)
def boxes(v):
 n,p=parse_state(v)
 if n.split(':')[-1]in FLOWERS|{'tall_grass','large_fern'}:return ()
 return ob(v)
def color(v):
 n,p=parse_state(v);b=n.split(':')[-1]
 return {'short_grass':(112,142,67),'fern':(73,126,71),'dandelion':(223,188,51),'cornflower':(95,112,202),'azure_bluet':(219,226,213),'allium':(180,127,189),'blue_orchid':(93,163,198),'tall_grass':(101,145,68),'large_fern':(67,127,64)}.get(b,oc(v))
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
s.FULL.update({'pumpkin','melon'})
