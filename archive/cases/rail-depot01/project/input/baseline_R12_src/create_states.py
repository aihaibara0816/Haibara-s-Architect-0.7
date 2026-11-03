"""Pinned Create 6.0.10 vocabulary. Offline rail mesh has measured sleeper/rail envelopes, not game textures."""
import industrial_states
from detail_lab import states as S
from vendor.voxel_core import state,parse_state
S.SLABS.add('cobblestone_slab')
S.FULL.update({'cobblestone','andesite'})
_old={k:getattr(S,k) for k in ['make','family','validate','boxes','color','support_cube']}
MOD={'create:track','create:track_station','create:track_signal'}
def make(n,**p):
 if n in MOD:
  q={'shape':'xo','turn':'false','waterlogged':'false'} if n=='create:track' else {'powered':'false','type':'entry_signal'} if n.endswith('signal') else {'assembling':'false','waterlogged':'false'}
  q.update(p);v=state(n,**q);validate(v);return v
 return _old['make'](n,**p)
def validate(v):
 n,p=parse_state(v)
 if n not in MOD:return _old['validate'](v)
 a={'shape':{'xo','zo'},'turn':{'true','false'},'waterlogged':{'false'}} if n=='create:track' else {'powered':{'false','true'},'type':{'entry_signal','cross_signal'}} if n.endswith('signal') else {'assembling':{'false','true'},'waterlogged':{'false'}}
 assert set(a)==set(p) and all(p[k] in a[k] for k in p),(n,p)
 return True
def family(v):return 'create' if parse_state(v)[0] in MOD else _old['family'](v)
def boxes(v):
 n,p=parse_state(v)
 if n=='create:track':
  # Six-faced solid approximation to the measured official alpha-plane model.
  b=[(-.871875,-.12,.125,1.871875,.10,.375),(-.871875,-.12,.625,1.871875,.10,.875),(-.590625,.08,0,-.340625,.346484,1),(1.340625,.08,0,1.590625,.346484,1)]
  return tuple((z,y,x,Z,Y,X) for x,y,z,X,Y,Z in b) if p['shape']=='xo' else tuple(b)
 if n=='create:track_station':return ((0,0,0,1,.25,1),(.1,.25,.1,.9,1,.9))
 if n=='create:track_signal':return ((.125,0,.125,.875,.25,.875),(.375,.25,.375,.625,1.8,.625),(.2,1.2,.2,.8,1.9,.8))
 return _old['boxes'](v)
def color(v):
 n=parse_state(v)[0]
 return {'create:track':(126,122,112),'create:track_station':(143,123,80),'create:track_signal':(193,145,63),'minecraft:cobblestone_slab':(126,130,123),'minecraft:cobblestone':(121,128,125),'minecraft:andesite':(137,143,139)}.get(n,_old['color'](v) if n not in MOD else (120,120,120))
def support_cube(v):return False if parse_state(v)[0] in MOD else _old['support_cube'](v)
for k in _old:setattr(S,k,globals()[k])
