"""Authored polygon footprints, terraced land, streets and public details."""
import math,collections
from detail_lab import states
M=states.make

def local(t,x,z):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);r=t['rotation']
 if r==0:a,c=x,z
 elif r==1:a,c=D-1-z,x
 elif r==2:a,c=W-1-x,D-1-z
 else:a,c=z,W-1-x
 return t['x']+a,t['z']+c

def mask(t):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);s=t['shape'];k=t['cut']
 return {(x,z) for x in range(W) for z in range(D) if (s!='front_cut' or x-z<=W-1-k) and (s!='rear_cut' or x+z<=W+D-2-k) and (s!='notch' or x<W-k or z<D-k)}

def setup(b,p):
 w,_,d=p['size_xyz'];foot=set();pads={};hm={}
 for t in p['buildings']:
  foot|={local(t,x,z) for x,z in mask(t)}
  for x in range(t['x']-2,t['x']+t['w']+2):
   for z in range(t['z']-2,t['z']+t['d']+2):pads[x,z]=t['base_y']
 for x in range(w):
  for z in range(d):
   y=3+max(0,min(4,int(min(180-x,170-z)//35)));y=pads.get((x,z),y)
   road=(193<=x<208) or (182<=z<197)
   paved=x>=184 or z>=172
   courtyard=23<=x<184 and 20<=z<172 and (x,z) not in foot
   if road:y=2
   elif paved:y=3
   hm[x,z]=y
   for yy in range(y):b.put(x,yy,z,'dirt' if yy<y-1 else 'gray_concrete' if road else 'smooth_stone' if paved else ('polished_andesite' if (x*13+z*17)%47==0 else 'smooth_stone') if courtyard else 'grass_block','site.terrain' if not paved else 'site.road' if road else 'site.sidewalk')
 # Street edges, no continuous barrier across the crossings.
 for z in range(0,182):b.put(192,2,z,'smooth_stone','site.curb')
 for x in range(0,193):b.put(x,2,181,'smooth_stone','site.curb')
 for z in range(0,182):
  if z%10<5:b.put(200,1,z,'white_concrete','site.road.dash')
 for x in range(0,193):
  if x%10<5:b.put(x,1,189,'white_concrete','site.road.dash')
 paths=set();sets={}
 for st in p['streets']:
  cells=set();r=(st['width']-1)/2
  for (ax,az),(cx,cz) in zip(st['points'],st['points'][1:]):
   den=(cx-ax)**2+(cz-az)**2
   for x in range(max(0,min(ax,cx)-math.ceil(r)),min(w,max(ax,cx)+math.ceil(r)+1)):
    for z in range(max(0,min(az,cz)-math.ceil(r)),min(d,max(az,cz)+math.ceil(r)+1)):
     q=max(0,min(1,((x-ax)*(cx-ax)+(z-az)*(cz-az))/den))
     if (x-ax-q*(cx-ax))**2+(z-az-q*(cz-az))**2<=r*r+.1:cells.add((x,z))
  if cells&foot:raise ValueError(('street-house overlap',st['id'],sorted(cells&foot)[:8]))
  sets[st['id']]=cells;paths|=cells
 # Explicit continuous pedestrian strips. Tree pits are outside these strips.
 sets['east_sidewalk']={(x,z) for x in range(189,193) for z in range(0,182)}
 sets['south_sidewalk']={(x,z) for x in range(0,193) for z in range(177,182)}
 for cells in sets.values():paths|=cells
 for x,z in paths:
  if x<184 and z<172:b.put(x,hm[x,z]-1,z,'light_gray_concrete' if (x*17+z*13)%59 else 'polished_andesite','site.lane.paving')
 return paths,sets,foot,hm

def connect(b,entries,paths,foot,hm,p):
 w,_,d=p['size_xyz']
 for e in entries:
  start=e['outside'][0],e['outside'][2];goal=None;prev={start:None};q=collections.deque([start])
  while q:
   a=q.popleft()
   if a in paths:goal=a;break
   for c in [(a[0]+1,a[1]),(a[0]-1,a[1]),(a[0],a[1]+1),(a[0],a[1]-1)]:
    if c in prev or c in foot or not(0<=c[0]<w and 0<=c[1]<d) or abs(hm[c]-hm[a])>1:continue
    if any((c[0],yy,c[1]) in b.s.blocks for yy in [hm[c],hm[c]+1]):continue
    prev[c]=a;q.append(c)
  if goal is None:raise ValueError(('entry cannot reach public street',e['id'],start))
  route=[]
  while goal is not None:route.append(goal);goal=prev[goal]
  e['outside_route']=route
  for x,z in route:
   paths.add((x,z));b.put(x,hm[x,z]-1,z,'polished_andesite','site.entry_path')
 transitions=[]
 for x,z in sorted(paths):
  y=hm[x,z]
  for dx,dz,face in [(1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')]:
   c=x+dx,z+dz
   if c in paths and hm[c]==y+1:
    b.put(x,y,z,M('stone_brick_stairs',facing=face),'site.grade.stair');transitions.append({'xyz':[x,y,z],'uphill':face});break
 return transitions

def decorate(b,paths,foot,hm,p,lamps):
 trees=[];props=[];w,_,d=p['size_xyz']
 def free(x,z,r=0):return all((a,c) not in paths and (a,c) not in foot and (a,hm[a,c],c) not in b.s.blocks for a in range(x-r,x+r+1) for c in range(z-r,z+r+1) if (a,c) in hm)
 # East/south paired tree pits, plus a sparse open northwest slope.
 for x,z in [(186,z) for z in [16,39,72,116,153]]+[(x,174) for x in [19,40,69,102,139,167]]+[(11,29),(13,77),(12,119),(28,10),(73,10),(113,11),(12,12)]:
  if not free(x,z,1):continue
  y=hm[x,z]
  for a in range(x-1,x+2):
   for c in range(z-1,z+2):b.put(a,y-1,c,'dirt' if a==x and c==z else 'moss_block','site.tree_pit')
  b.tree(x,z,y,h=10 if x>180 or z>170 else 9,r=3)
  trees.append({'root':[x,y-1,z],'height':10,'kind':'street_tree' if x>180 or z>170 else 'open_slope_tree'})
 for x,z in [(185,z) for z in [24,62,100,140]]+[(x,173) for x in [54,86,121,155]]:
  if not free(x,z):
   spots=[(x+dx,z+dz) for dx,dz in [(2,0),(-2,0),(0,3),(0,-3),(3,3)] if (x+dx,z+dz) in hm and free(x+dx,z+dz)]
   if not spots:continue
   x,z=spots[0]
  y=hm[x,z]
  for yy in range(y,y+7):b.put(x,yy,z,'iron_bars','site.streetlight.post')
  for a in range(x,x+3):b.put(a,y+6,z,'iron_bars','site.streetlight.arm')
  b.put(x+2,y+6,z,'sea_lantern','site.streetlight.head');lamps.append({'xyz':[x+2,y+6,z],'material':'sea_lantern','owner':'site.streetlight.head','unit_id':None,'fixture':'pole'})
 # Crossing bands, dropped-curb stairs, road drains and manholes.
 for zz in [71,130,176]:
  for x in range(193,208):
   for z in range(zz-2,zz+3):
    if z%2==0:b.put(x,1,z,'white_concrete','site.crosswalk')
  for z in range(zz-2,zz+3):
   b.put(193,2,z,M('stone_brick_stairs',facing='west'),'site.dropped_curb')
   b.put(207,2,z,M('stone_brick_stairs',facing='east'),'site.dropped_curb')
 for xx in [78,121,148]:
  for z in range(182,197):
   for x in range(xx-2,xx+3):
    if x%2==0:b.put(x,1,z,'white_concrete','site.crosswalk')
  for x in range(xx-2,xx+3):
   b.put(x,2,182,M('stone_brick_stairs',facing='north'),'site.dropped_curb')
   b.put(x,2,196,M('stone_brick_stairs',facing='south'),'site.dropped_curb')
 for z in range(10,180,18):b.put(193,1,z,'polished_deepslate','site.road.drain')
 for x in range(12,190,19):b.put(x,1,182,'polished_deepslate','site.road.drain')
 for x,z in [(197,43),(202,119),(73,187),(140,193)]:
  for a in [x,x+1]:
   for c in [z,z+1]:b.put(a,1,c,'polished_deepslate','site.road.manhole')
 for x,z in [(186,86),(186,131),(76,174),(146,174),(15,52),(66,13)]:
  if free(x,z):b.put(x,hm[x,z],z,M('oak_stairs',facing='south'),'site.bench')
 # Service boxes, litter bins, small parking bays away from clear strips.
 for x,z in [(185,49),(184,93),(113,173),(26,173)]:
  if free(x,z):
   b.put(x,hm[x,z],z,'gray_concrete','site.bin');b.put(x,hm[x,z]+1,z,M('iron_trapdoor',half='bottom'),'site.bin.lid')
 for x,z in [(183,58),(181,101),(47,171),(83,171),(118,171),(153,171),(57,93)]:
  if not all(free(a,z) for a in range(x,x+3)):continue
  y=hm[x,z];o='site.scooter.'+str(len(props))
  for a in [x,x+2]:b.put(a,y,z,M('polished_deepslate_slab'),o)
  b.put(x+1,y,z,M('oak_slab',type='top'),o);b.put(x+2,y+1,z,'iron_bars',o);b.put(x+1,y+1,z,M('dark_oak_trapdoor',half='bottom'),o)
  props.append({'id':o,'kind':'parked_scooter_shape','bounds_xyz':[x,y,z,x+3,y+2,z+1]})
 return trees,props
