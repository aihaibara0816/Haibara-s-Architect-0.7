"""Case extension: vanilla crops/soil; simplified preview geometry only."""
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
s.FULL.update({'stone','bedrock','coarse_dirt','gravel','hay_block'})
oldfamily,oldvalidate,oldboxes,oldcolor,oldmake=s.family,s.validate,s.boxes,s.color,s.make
CROPS={'wheat':7,'carrots':7,'potatoes':7,'beetroots':3}
def family(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 return 'crop' if n in CROPS else 'soil' if n in {'farmland','dirt_path'} else oldfamily(v)
def validate(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n in CROPS:
  assert set(p)=={'age'} and 0<=int(p['age'])<=CROPS[n];return True
 if n=='farmland':assert set(p)=={'moisture'} and 0<=int(p['moisture'])<=7;return True
 if n=='dirt_path':assert not p;return True
 if n=='hay_block':assert p.get('axis') in ['x','y','z'];return True
 return oldvalidate(v)
def make(n,**p):
 base=n.split(':')[-1]
 if base in CROPS:return state('minecraft:'+base,age=str(p.get('age',CROPS[base])))
 if base=='farmland':return state('minecraft:farmland',moisture=str(p.get('moisture',7)))
 if base=='dirt_path':return 'minecraft:dirt_path'
 if base=='hay_block':return state('minecraft:hay_block',axis=str(p.get('axis','y')))
 return oldmake(n,**p)
def boxes(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n in CROPS:
  h=.3+.5*int(p['age'])/CROPS[n];return ((.15,0,.15,.3,h,.3),(.65,0,.2,.8,h,.4),(.4,0,.65,.6,h,.85))
 if n in {'farmland','dirt_path'}:return ((0,0,0,1,.9375,1),)
 return oldboxes(v)
def color(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n in CROPS:
  return (180,166,67) if n=='wheat' and int(p['age'])>=6 else (95,142,50) if n!='beetroots' else (75,118,48)
 return {'farmland':(111,78,47),'dirt_path':(159,135,83),'coarse_dirt':(132,112,77),'gravel':(148,142,134),'stone':(123,128,126),'bedrock':(78,81,79),'hay_block':(184,163,66)}.get(n,oldcolor(v))
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color

# JapanTown12 local extension, vanilla Java 1.21.1 shapes approximated for preview.
s.FULL.update({'green_concrete'})
jfamily,jvalidate,jmake,jboxes,jcolor=s.family,s.validate,s.make,s.boxes,s.color
def townfamily(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 return 'door' if n=='oak_door' else 'lantern' if n=='lantern' else 'leaves' if n=='cherry_leaves' else jfamily(v)
def townvalidate(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n=='oak_door':
  ok={'facing':set(s.DIRS),'half':{'lower','upper'},'hinge':{'left','right'},'open':s.BOOL,'powered':s.BOOL}
  assert set(p)==set(ok) and all(v in ok[k] for k,v in p.items());return True
 if n=='lantern':assert set(p)=={'hanging','waterlogged'} and all(v in s.BOOL for v in p.values());return True
 if n=='cherry_leaves':
  assert set(p)=={'distance','persistent','waterlogged'} and p['distance'] in set(map(str,range(1,8))) and p['persistent'] in s.BOOL and p['waterlogged'] in s.BOOL;return True
 return jvalidate(v)
def townmake(n,**p):
 base=n.split(':')[-1]
 if base=='oak_door':
  q=dict(facing='south',half='lower',hinge='left',open='false',powered='false');q.update({k:str(v).lower() for k,v in p.items()});return state('minecraft:oak_door',**q)
 if base=='lantern':
  q=dict(hanging='false',waterlogged='false');q.update(p);return state('minecraft:lantern',**q)
 if base=='cherry_leaves':return state('minecraft:cherry_leaves',distance='7',persistent='true',waterlogged='false')
 return jmake(n,**p)
def townboxes(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n=='oak_door':
  return ({'south':(0,0,0,1,1,.1875),'north':(0,0,.8125,1,1,1),'east':(0,0,0,.1875,1,1),'west':(.8125,0,0,1,1,1)}[p['facing']],)
 if n=='lantern':return ((.3125,.125,.3125,.6875,.6875,.6875),(.4375,.6875,.4375,.5625,1,.5625))
 if n=='cherry_leaves':return ((0,0,0,1,1,1),)
 return jboxes(v)
def towncolor(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 return {'cherry_leaves':(231,168,184),'green_concrete':(75,107,69),'lantern':(248,195,114),'oak_door':(155,116,73)}.get(n,jcolor(v))
s.family,s.validate,s.make,s.boxes,s.color=townfamily,townvalidate,townmake,townboxes,towncolor

# Old street case vocabulary. Vanilla states; preview meshes omit texture and cloth motion.
ofamily,ovalidate,omake,oboxes,ocolor=s.family,s.validate,s.make,s.boxes,s.color
LOGS={'stripped_oak_log','stripped_spruce_log','spruce_log'}
FENCES={'oak_fence','spruce_fence','dark_oak_fence'}
BANNERS={'purple_wall_banner','blue_wall_banner','red_wall_banner','white_wall_banner'}
s.FULL.update({'spruce_planks'})
def streetfamily(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 return 'cube' if n in LOGS else 'fence' if n in FENCES else 'banner' if n in BANNERS else ofamily(v)
def streetvalidate(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n in LOGS:assert set(p)=={'axis'} and p['axis'] in {'x','y','z'};return True
 if n in FENCES:assert set(p)==set(s.DIRS)|{'waterlogged'} and all(q in s.BOOL for q in p.values());return True
 if n in BANNERS:assert set(p)=={'facing'} and p['facing'] in s.DIRS;return True
 return ovalidate(v)
def streetmake(n,**p):
 base=n.split(':')[-1]
 if base in LOGS:return state('minecraft:'+base,axis=p.get('axis','y'))
 if base in FENCES:
  q={d:'false' for d in s.DIRS};q['waterlogged']='false';q.update(p);return state('minecraft:'+base,**q)
 if base in BANNERS:return state('minecraft:'+base,facing=p.get('facing','south'))
 return omake(n,**p)
def streetboxes(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 if n in FENCES:
  a=[(.375,0,.375,.625,1,.625)]
  for d in s.DIRS:
   if p[d]=='true':
    x,z,X,Z={'north':(.4375,0,.5625,.5),'south':(.4375,.5,.5625,1),'west':(0,.4375,.5,.5625),'east':(.5,.4375,1,.5625)}[d]
    for y,Y in [(.375,.5625),(.75,.9375)]:a.append((x,y,z,X,Y,Z))
  return tuple(a)
 if n in BANNERS:
  # Cloth extends below its attachment; slab-like box is an approximate static silhouette.
  return ({'south':(.125,-.75,.03,.875,.95,.10),'north':(.125,-.75,.9,.875,.95,.97),'east':(.03,-.75,.125,.10,.95,.875),'west':(.9,-.75,.125,.97,.95,.875)}[p['facing']],)
 return oboxes(v)
def streetcolor(v):
 n,p=parse_state(v);n=n.split(':')[-1]
 colors={'stripped_oak_log':(182,145,92),'stripped_spruce_log':(133,99,62),'spruce_log':(82,64,45),'spruce_planks':(137,103,66),'oak_fence':(167,127,77),'spruce_fence':(122,90,57),'dark_oak_fence':(94,66,42),'purple_wall_banner':(108,58,111),'blue_wall_banner':(55,64,109),'red_wall_banner':(153,47,43),'white_wall_banner':(225,216,192)}
 return colors[n] if n in colors else ocolor(v)
s.family,s.validate,s.make,s.boxes,s.color=streetfamily,streetvalidate,streetmake,streetboxes,streetcolor

# J10 adds only new vanilla IDs; historical state rendering stays unchanged.
import japanese_detail_states
