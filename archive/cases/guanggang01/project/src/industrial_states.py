"""Explicit vanilla 1.21.1 additions, with approximate offline geometry."""
import qilou_states
from detail_lab import states as S
from vendor.voxel_core import state,parse_state
S.FULL.update({'coal_block','raw_iron_block','yellow_concrete','brown_concrete','waxed_cut_copper','waxed_exposed_cut_copper','waxed_weathered_cut_copper','waxed_oxidized_cut_copper'})
_make,_family,_validate,_boxes,_color=S.make,S.family,S.validate,S.boxes,S.color
def make(name,**p):
 b=name.split(':')[-1]
 if b in {'rail','ladder'}:
  q={'shape':'north_south','waterlogged':'false'} if b=='rail' else {'facing':'south','waterlogged':'false'}
  q.update(p);v=state('minecraft:'+b,**q);validate(v);return v
 return _make(name,**p)
def family(v):
 b=parse_state(v)[0].split(':')[-1]
 return b if b in {'rail','ladder'} else _family(v)
def validate(v):
 b,p=parse_state(v);b=b.split(':')[-1]
 if b=='rail':
  assert set(p)=={'shape','waterlogged'} and p['shape'] in {'north_south','east_west'} and p['waterlogged']=='false';return True
 if b=='ladder':
  assert set(p)=={'facing','waterlogged'} and p['facing'] in S.DIRS and p['waterlogged']=='false';return True
 return _validate(v)
def boxes(v):
 b,p=parse_state(v);b=b.split(':')[-1]
 if b=='rail':
  return ((.15,0,0,.25,.12,1),(.75,0,0,.85,.12,1)) if p['shape']=='north_south' else ((0,0,.15,1,.12,.25),(0,0,.75,1,.12,.85))
 if b=='ladder':
  f=p['facing'];return {'south':((0,0,0,1,1,.125),),'north':((0,0,.875,1,1,1),),'east':((0,0,0,.125,1,1),),'west':((.875,0,0,1,1,1),)}[f]
 return _boxes(v)
def color(v):
 b=parse_state(v)[0].split(':')[-1]
 return {'coal_block':(32,33,31),'raw_iron_block':(138,103,77),'yellow_concrete':(205,161,49),'brown_concrete':(100,74,55),'waxed_cut_copper':(173,103,68),'waxed_exposed_cut_copper':(150,119,87),'waxed_weathered_cut_copper':(99,139,120),'waxed_oxidized_cut_copper':(72,143,125),'rail':(143,137,123),'ladder':(132,103,65)}.get(b,_color(v))
S.make,S.family,S.validate,S.boxes,S.color=make,family,validate,boxes,color
