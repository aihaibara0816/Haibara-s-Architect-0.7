"""J10 vanilla vocabulary. Visual boxes approximate models, not collision tests."""
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
s.FULL.update({'deepslate_tiles','deepslate_bricks','mossy_stone_bricks','white_wool','brown_wool','green_wool','yellow_wool','red_wool','light_gray_wool'})
s.SLABS.update({'deepslate_tile_slab','deepslate_brick_slab','spruce_slab'})
s.STAIRS.update({'deepslate_tile_stairs','deepslate_brick_stairs','spruce_stairs'})
oldfamily,oldmake,oldvalidate,oldboxes,oldcolor=s.family,s.make,s.validate,s.boxes,s.color
CARPETS={'white_carpet','brown_carpet','green_carpet','yellow_carpet','red_carpet','light_gray_carpet'}
CANDLES={'white_candle','yellow_candle','purple_candle','green_candle','red_candle'}
COLORS={'white':(229,222,204),'brown':(112,79,55),'green':(131,142,80),'yellow':(192,170,101),'red':(159,69,50),'light_gray':(178,181,166),'purple':(135,93,144)}
def family(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 return 'carpet' if n in CARPETS else 'candle' if n in CANDLES else 'pot' if n=='flower_pot' else oldfamily(st)
def validate(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 if n in CARPETS or n=='flower_pot':assert not p;return True
 if n in CANDLES:
  assert set(p)=={'candles','lit','waterlogged'} and p['candles'] in {'1','2','3','4'} and p['lit'] in s.BOOL and p['waterlogged'] in s.BOOL;return True
 return oldvalidate(st)
def make(n,**p):
 base=n.split(':')[-1]
 if base in CARPETS or base=='flower_pot':return 'minecraft:'+base
 if base in CANDLES:
  q=dict(candles='1',lit='false',waterlogged='false');q.update(p);return state('minecraft:'+base,**q)
 return oldmake(n,**p)
def boxes(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 if n in CARPETS:return ((0,0,0,1,.0625,1),)
 if n=='flower_pot':return ((.3125,0,.3125,.6875,.375,.6875),)
 if n in CANDLES:
  pts=[(.375,.375,.5),(.625,.5,.375),(.375,.6875,.625),(.625,.75,.625)]
  return tuple((x,.0,z,x+.125,h,z+.125) for x,z,h in pts[:int(p['candles'])])
 return oldboxes(st)
def color(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 for tail in ['_carpet','_wool','_candle']:
  if n.endswith(tail):return COLORS[n[:-len(tail)]]
 if 'deepslate_tile' in n:return (67,75,75)
 if 'deepslate_brick' in n:return (78,84,81)
 if n=='mossy_stone_bricks':return (115,125,102)
 if n.startswith('spruce_') and n.endswith(('_stairs','_slab')):return (130,101,68)
 if n=='flower_pot':return (147,92,67)
 return oldcolor(st)
s.family,s.make,s.validate,s.boxes,s.color=family,make,validate,boxes,color
