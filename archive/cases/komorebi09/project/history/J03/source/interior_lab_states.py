"""Java 1.21.1 block vocabulary for interior_kit; meshes remain approximations."""
from detail_lab import states as s
from vendor.voxel_core import parse_state,state
of,ov,om,ob,oc=s.family,s.validate,s.make,s.boxes,s.color
s.FULL.update({'crafting_table','white_terracotta','light_gray_terracotta','brown_terracotta'})
def family(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 return 'container' if n in ['barrel','furnace'] else 'bed' if n.endswith('_bed') else 'basin' if n=='water_cauldron' else 'potted' if n=='potted_bamboo' else 'cake' if n=='cake' else 'door' if n=='birch_door' else of(st)
def validate(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 schemas={'barrel':dict(facing=set(s.DIRS)|{'up','down'},open=s.BOOL),'furnace':dict(facing=set(s.DIRS),lit=s.BOOL),'white_bed':dict(facing=set(s.DIRS),occupied=s.BOOL,part={'head','foot'}),'water_cauldron':dict(level={'1','2','3'}),'cake':dict(bites=set(map(str,range(7)))),'birch_door':dict(facing=set(s.DIRS),half={'lower','upper'},hinge={'left','right'},open=s.BOOL,powered=s.BOOL),'potted_bamboo':{}}
 if n in schemas:
  q=schemas[n]
  if set(p)!=set(q) or any(p[k] not in q[k] for k in p):raise ValueError(('invalid state',st))
  return True
 return ov(st)
def make(n,**p):
 base=n.split(':')[-1];defaults={'barrel':dict(facing='south',open='false'),'furnace':dict(facing='south',lit='false'),'white_bed':dict(facing='north',occupied='false',part='foot'),'water_cauldron':dict(level='3'),'cake':dict(bites='0'),'birch_door':dict(facing='south',half='lower',hinge='left',open='false',powered='false'),'potted_bamboo':{}}
 if base in defaults:
  q=defaults[base].copy();q.update({k:str(v).lower() for k,v in p.items()});v=state('minecraft:'+base,**q);validate(v);return v
 return om(n,**p)
def boxes(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 if n in ['barrel','furnace']:return ((0,0,0,1,1,1),)
 if n=='white_bed':return ((0,.1875,0,1,.5625,1),(.0625,0,.0625,.1875,.1875,.1875),(.8125,0,.8125,.9375,.1875,.9375))
 if n=='water_cauldron':return ((0,0,0,1,.25,1),(0,.25,0,.125,1,1),(.875,.25,0,1,1,1),(.125,.25,0,.875,1,.125),(.125,.25,.875,.875,1,1),(.125,.25,.125,.875,.875,.875))
 if n=='cake':return ((.0625,0,.0625,.9375,.5,.9375),)
 if n=='potted_bamboo':return ((.3125,0,.3125,.6875,.375,.6875),(.4375,.375,.4375,.5625,1,.5625))
 if n=='birch_door':return ob(st.replace('birch_door','oak_door'))
 return ob(st)
def color(st):
 n,p=parse_state(st);n=n.split(':')[-1]
 return {'barrel':(132,98,61),'furnace':(109,114,113),'white_bed':(230,226,209),'water_cauldron':(99,111,111),'cake':(230,201,158),'potted_bamboo':(107,133,62),'birch_door':(224,215,180),'crafting_table':(157,115,68),'white_terracotta':(207,180,165),'light_gray_terracotta':(133,107,98),'brown_terracotta':(100,72,48)}.get(n,oc(st)) if n not in ['barrel','furnace','white_bed','water_cauldron','cake','potted_bamboo','birch_door'] else {'barrel':(132,98,61),'furnace':(109,114,113),'white_bed':(230,226,209),'water_cauldron':(99,111,111),'cake':(230,201,158),'potted_bamboo':(107,133,62),'birch_door':(224,215,180)}[n]
s.family,s.validate,s.make,s.boxes,s.color=family,validate,make,boxes,color
