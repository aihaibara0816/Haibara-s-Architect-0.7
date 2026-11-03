"""Bounded Java 1.21.1 palette additions for Qilou01."""
import taisho_states, rural_states
from detail_lab import states as S
S.FULL.update({'calcite','chiseled_quartz_block','red_wool','blue_wool','cyan_wool'})
rural_states.LOGS.add('quartz_pillar')
_family,_validate,_make,_boxes,_color=S.family,S.validate,S.make,S.boxes,S.color
def proxy(v):return v.replace('minecraft:dark_oak_door','minecraft:oak_door')
def family(v):return _family(proxy(v))
def validate(v):return _validate(proxy(v))
def make(name,**p):
 if name.split(':')[-1]=='dark_oak_door':return _make('oak_door',**p).replace('minecraft:oak_door','minecraft:dark_oak_door')
 return _make(name,**p)
def boxes(v):return _boxes(proxy(v))
def color(v):
 if 'dark_oak_door' in v:return (73,50,30)
 if v=='minecraft:cyan_wool':return (21,137,145)
 if v=='minecraft:blue_wool':return (53,57,157)
 return _color(v)
S.family,S.validate,S.make,S.boxes,S.color=family,validate,make,boxes,color
