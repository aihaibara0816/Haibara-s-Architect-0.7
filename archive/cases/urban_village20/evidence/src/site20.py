"""Six-sided district, anchored terraces and graded public streets."""
import math,collections,heapq
from detail_lab import states
M=states.make
DIRS=[(1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')]
def local(t,x,z):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);r=t['rotation']
 if r==0:a,c=x,z
 elif r==1:a,c=D-1-z,x
 elif r==2:a,c=W-1-x,D-1-z
 else:a,c=z,W-1-x
 return t['x']+a,t['z']+c

def mask(t):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);s=t['shape'];k=t['cut']
 cells={(x,z) for x in range(W) for z in range(D) if (s!='front_cut' or x-z<=W-1-k) and (s!='rear_cut' or x+z<=W+D-2-k) and (s!='notch' or x<W-k or z<D-k)}
 for q in t.get('edge_recesses',[]):
  dep=q['depth']
  if q['face']=='right':cells={v for v in cells if not(v[0]>=W-dep and q['start']<=v[1]<q['end'])}
  if q['face']=='rear_right':cells={v for v in cells if not(v[0]>=W-dep and v[1]>=D-dep)}
 return cells

def inside(x,z,poly):
 yes=False
 for (a,c),(A,C) in zip(poly,poly[1:]+poly[:1]):
  if (c>z)!=(C>z) and x<(A-a)*(z-c)/(C-c)+a:yes=not yes
 return yes

def east_edge(z,p):
 x0,z0,x1,z1=p['site']['east_edge'];return math.floor(x0+(x1-x0)*(z-z0)/(z1-z0))
def south_edge(x,p):
 x0,z0,x1,z1=p['site']['south_edge'];return math.floor(z0+(z1-z0)*(x-x0)/(x1-x0))
def road_kind(x,z,p):
 e=east_edge(z,p)-x;s=south_edge(x,p)-z
 return (3<=e<=17 or 3<=s<=17),(e<=26 or s<=26)
def surface(x,z,p):
 lo,hi=p['site']['height_range'];hx,hz=p['site']['high_anchor'];lx,lz=p['site']['low_anchor']
 return lo+max(0,min(hi-lo,round((hi-lo)*(.55*(lx-x)+.45*(lz-z))/(.55*(lx-hx)+.45*(lz-hz)))))
def terrain_field(p):
 w,_,d=p['size_xyz'];poly=p['site']['boundary_xz'];domain={(x,z) for x in range(w) for z in range(d) if inside(x+.5,z+.5,poly)};foot=set();pads={}
 for t in p['buildings']:
  shape={local(t,x,z) for x,z in mask(t)}
  if shape-domain:raise ValueError(('building outside site',t['id']))
  if foot&shape:raise ValueError(('building overlap',t['id']))
  foot|=shape
  apron=t.get('terrain_apron_pad',1)
  for x in range(t['x']-apron,t['x']+t['w']+apron):
   for z in range(t['z']-apron,t['z']+t['d']+apron):
    q=x,z
    if q not in domain:continue
    if q in pads and pads[q]!=t['base_y']:raise ValueError(('incompatible adjacent terraces',t['id'],q,pads[q],t['base_y']))
    pads[q]=t['base_y']
 def envelope(sign):
  out={q:y*sign for q,y in pads.items()};heap=[(v,q) for q,v in out.items()];heapq.heapify(heap)
  while heap:
   v,q=heapq.heappop(heap)
   if out[q]!=v:continue
   for dx,dz,_ in DIRS:
    a=q[0]+dx,q[1]+dz
    if a in domain and v+1<out.get(a,9999):out[a]=v+1;heapq.heappush(heap,(v+1,a))
  return out
 upper=envelope(1);lower={q:-v for q,v in envelope(-1).items()};hm={};raw={}
 for q in domain:
  if lower[q]>upper[q]:raise ValueError(('terrace grade impossible',q))
  y=max(lower[q],min(upper[q],surface(*q,p)));raw[q]=y;road,paved=road_kind(*q,p)
  if q in foot and paved:raise ValueError(('building on main street',q))
  hm[q]=y-int(road)
 return foot,hm,raw

def street_cells(st,p,hm):
 w,_,d=p['size_xyz'];cells=set();r=(st['width']-1)/2
 for (ax,az),(cx,cz) in zip(st['points'],st['points'][1:]):
  den=(cx-ax)**2+(cz-az)**2
  for x in range(max(0,min(ax,cx)-math.ceil(r)),min(w,max(ax,cx)+math.ceil(r)+1)):
   for z in range(max(0,min(az,cz)-math.ceil(r)),min(d,max(az,cz)+math.ceil(r)+1)):
    q=max(0,min(1,((x-ax)*(cx-ax)+(z-az)*(cz-az))/den))
    if (x-ax-q*(cx-ax))**2+(z-az-q*(cz-az))**2<=r*r+.1 and (x,z) in hm:cells.add((x,z))
 return cells

def setup(b,p):
 foot,hm,raw=terrain_field(p);poly=p['site']['boundary_xz'];b.site_surface=raw
 for (x,z),y in sorted(hm.items()):
  road,paved=road_kind(x,z,p);near_open=x<23 or not inside(x+.5,z-8,poly)
  mat='gray_concrete' if road else 'smooth_stone' if paved else 'grass_block' if near_open and (x,z) not in foot else ('polished_andesite' if (x*13+z*17)%83==0 else 'smooth_stone')
  for yy in range(y):b.put(x,yy,z,mat if yy==y-1 else 'stone_bricks' if yy>=y-3 and not road else 'dirt','site.road' if road else 'site.sidewalk' if paved else 'site.terrain')
  e=east_edge(z,p)-x;s=south_edge(x,p)-z
  if (e==10 and z%10<5) or (s==10 and x%10<5):b.put(x,y-1,z,'white_concrete','site.road.dash')
  if not road and (e==18 or s==18):b.put(x,y-1,z,'smooth_stone','site.curb')
 paths=set();sets={}
 for st in p['streets']:
  cells=street_cells(st,p,hm)
  if cells&foot:raise ValueError(('street-house overlap',st['id'],sorted(cells&foot)[:8]))
  sets[st['id']]=cells;paths|=cells
 sets['east_sidewalk']={q for q in hm if 18<=east_edge(q[1],p)-q[0]<=21 and not road_kind(*q,p)[0]}
 sets['south_sidewalk']={q for q in hm if 18<=south_edge(q[0],p)-q[1]<=21 and not road_kind(*q,p)[0]}
 for cells in sets.values():paths|=cells
 for x,z in paths:
  if not road_kind(x,z,p)[1]:b.put(x,hm[x,z]-1,z,'light_gray_concrete' if (x*17+z*13)%59 else 'polished_andesite','site.lane.paving')
 return paths,sets,foot,hm

def connect(b,entries,paths,foot,hm,p):
 for e in entries:
  start=e['outside'][0],e['outside'][2];goal=None;prev={start:None};q=collections.deque([start])
  while q:
   a=q.popleft()
   if a in paths:goal=a;break
   for dx,dz,_ in DIRS:
    c=a[0]+dx,a[1]+dz
    if c in prev or c in foot or c not in hm or a not in hm or abs(hm[c]-hm[a])>1:continue
    if any((c[0],yy,c[1]) in b.s.blocks for yy in [hm[c],hm[c]+1]):continue
    prev[c]=a;q.append(c)
  if goal is None:raise ValueError(('entry cannot reach public street',e['id'],start))
  route=[]
  while goal is not None:route.append(goal);goal=prev[goal]
  e['outside_route']=route
  for x,z in route:paths.add((x,z));b.put(x,hm[x,z]-1,z,'polished_andesite','site.entry_path')
 transitions=[]
 for x,z in sorted(paths):
  y=hm[x,z]
  for dx,dz,face in DIRS:
   a=x+dx,z+dz
   if a in paths and hm[a]==y+1:
    b.put(x,y,z,M('stone_brick_stairs',facing=face),'site.grade.stair');transitions.append({'xyz':[x,y,z],'uphill':face});break
 return transitions

def decorate(b,paths,foot,hm,p,lamps):
 trees=[];props=[]
 def free(x,z,r=0):
  cells={(a,c) for a in range(x-r,x+r+1) for c in range(z-r,z+r+1)}
  return all(q in hm and q not in paths and q not in foot and (q[0],hm[q],q[1]) not in b.s.blocks for q in cells)
 treepoints=[(east_edge(z,p)-24,z) for z in [25,53,114,164,182]]+[(x,south_edge(x,p)-24) for x in [21,49,96,139,179,232]]+[(14,79),(14,115),(14,157),(40,60),(83,57),(137,38),(180,24),(210,17),(190,136)]
 for x,z in treepoints:
  if not free(x,z,2):continue
  y=hm[x,z]
  for a in range(x-1,x+2):
   for c in range(z-1,z+2):b.put(a,y-1,c,'dirt' if a==x and c==z else 'moss_block','site.tree_pit')
  b.tree(x,z,y,h=9,r=2);trees.append({'root':[x,y-1,z],'height':9,'kind':'street_tree' if road_kind(x,z,p)[1] else 'open_slope_tree'})
 for x,z in [(east_edge(z,p)-25,z) for z in [39,88,141,175]]+[(x,south_edge(x,p)-25) for x in [79,123,161,212]]:
  if not free(x,z):
   candidates=[(x+dx,z+dz) for dx,dz in [(1,0),(-1,0),(0,3),(0,-3)] if free(x+dx,z+dz)]
   if not candidates:continue
   x,z=candidates[0]
  y=hm[x,z]
  for yy in range(y,y+7):b.put(x,yy,z,'iron_bars','site.streetlight.post')
  for a in range(x,x+3):b.put(a,y+6,z,'iron_bars','site.streetlight.arm')
  b.put(x+2,y+6,z,'sea_lantern','site.streetlight.head');lamps.append({'xyz':[x+2,y+6,z],'material':'sea_lantern','owner':'site.streetlight.head','unit_id':None,'fixture':'pole'})
 for z0 in p['site']['east_crossings']:
  for z in range(z0-2,z0+3):
   edge=east_edge(z,p)
   for x in range(edge-17,edge-2):
    if (x,z) in hm and z%2==0:b.put(x,hm[x,z]-1,z,'white_concrete','site.crosswalk')
   for x,face in [(edge-17,'west'),(edge-3,'east')]:
    if (x,z) in hm:b.put(x,hm[x,z],z,M('stone_brick_stairs',facing=face),'site.dropped_curb')
 for x0 in p['site']['south_crossings']:
  for x in range(x0-2,x0+3):
   edge=south_edge(x,p)
   for z in range(edge-17,edge-2):
    if (x,z) in hm and x%2==0:b.put(x,hm[x,z]-1,z,'white_concrete','site.crosswalk')
   for z,face in [(edge-17,'north'),(edge-3,'south')]:
    if (x,z) in hm:b.put(x,hm[x,z],z,M('stone_brick_stairs',facing=face),'site.dropped_curb')
 for z in range(24,189,18):
  x=east_edge(z,p)-17
  if (x,z) in hm:b.put(x,hm[x,z]-1,z,'polished_deepslate','site.road.drain')
 for x in range(20,262,19):
  z=south_edge(x,p)-17
  if (x,z) in hm:b.put(x,hm[x,z]-1,z,'polished_deepslate','site.road.drain')
 for x,z in [(274,62),(275,119),(75,195),(140,199),(228,202)]:
  for a in [x,x+1]:
   for c in [z,z+1]:
    if (a,c) in hm and road_kind(a,c,p)[0]:b.put(a,hm[a,c]-1,c,'polished_deepslate','site.road.manhole')
 for x,z in [(16,98),(90,130),(192,135),(210,130),(261,153),(185,181)]:
  if free(x,z):b.put(x,hm[x,z],z,M('oak_stairs',facing='south'),'site.bench')
 for x,z in [(258,91),(256,145),(76,180),(150,182),(189,131)]:
  if free(x,z):b.put(x,hm[x,z],z,'gray_concrete','site.bin');b.put(x,hm[x,z]+1,z,M('iron_trapdoor',half='bottom'),'site.bin.lid')
 for x,z in [(216,98),(213,133),(70,142),(117,176),(151,176),(199,179)]:
  if not all(free(a,z) for a in range(x,x+3)):continue
  y=hm[x,z];o='site.scooter.'+str(len(props))
  for a in [x,x+2]:b.put(a,y,z,M('polished_deepslate_slab'),o)
  b.put(x+1,y,z,M('oak_slab',type='top'),o);b.put(x+2,y+1,z,'iron_bars',o);b.put(x+1,y+1,z,M('dark_oak_trapdoor',half='bottom'),o)
  props.append({'id':o,'kind':'parked_scooter_shape','bounds_xyz':[x,y,z,x+3,y+2,z+1]})
 return trees,props
