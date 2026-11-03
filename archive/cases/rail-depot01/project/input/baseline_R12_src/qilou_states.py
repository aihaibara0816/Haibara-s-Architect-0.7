"""Bounded Java 1.21.1 palette additions for Qilou01."""
import taisho_states, rural_states
from detail_lab import states as S
S.FULL.update({'melon','blue_terracotta','cyan_terracotta','calcite','chiseled_quartz_block','red_wool','blue_wool','cyan_wool','rooted_dirt','gray_wool','yellow_terracotta','terracotta','sandstone','cut_sandstone','weathered_cut_copper','waxed_weathered_cut_copper','oxidized_cut_copper','cracked_stone_bricks','moss_block','flowering_azalea_leaves'})
rural_states.LOGS.update({'oak_wood','dark_oak_wood','jungle_wood','jungle_log'})
rural_states.LOGS.add('quartz_pillar')
_family,_validate,_make,_boxes,_color=S.family,S.validate,S.make,S.boxes,S.color
def proxy(v):
 for leaf in ['flowering_azalea_leaves','jungle_leaves','dark_oak_leaves']:v=v.replace('minecraft:'+leaf,'minecraft:oak_leaves')
 return v.replace('minecraft:dark_oak_door','minecraft:oak_door').replace('minecraft:gray_bed','minecraft:white_bed').replace('minecraft:brown_bed','minecraft:white_bed')
def family(v):return _family(proxy(v))
def validate(v):return _validate(proxy(v))
def make(name,**p):
 if name.split(':')[-1]in ['flowering_azalea_leaves','jungle_leaves','dark_oak_leaves']:return _make('oak_leaves',**p).replace('minecraft:oak_leaves','minecraft:'+name.split(':')[-1])
 if name.split(':')[-1] in ['gray_bed','brown_bed']:return _make('white_bed',**p).replace('minecraft:white_bed','minecraft:'+name.split(':')[-1])
 if name.split(':')[-1]=='dark_oak_door':return _make('oak_door',**p).replace('minecraft:oak_door','minecraft:dark_oak_door')
 return _make(name,**p)
def boxes(v):return _boxes(proxy(v))
def color(v):
 if 'dark_oak_door' in v:return (73,50,30)
 if v.startswith('minecraft:gray_stained_glass'):return (92,104,108)
 if v=='minecraft:gray_wool':return (64,66,69)
 if v=='minecraft:gray_concrete':return (58,61,65)
 if v=='minecraft:cyan_wool':return (21,137,145)
 if v=='minecraft:blue_wool':return (53,57,157)
 return _color(v)
S.family,S.validate,S.make,S.boxes,S.color=family,validate,make,boxes,color
