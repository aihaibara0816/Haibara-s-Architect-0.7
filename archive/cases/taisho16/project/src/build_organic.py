"""Taisho15: frozen natural terrain, constrained placement, local foundations and path search."""
from pathlib import Path
import sys,json,copy,hashlib,io,gzip,random,math,heapq,statistics
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n,taisho_states
from prototype_base import Study
from organic_types import all_types
from quarter_types import gable
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state
RUN=sys.argv[1]if len(sys.argv)>1 else'O01';SEED=int(sys.argv[2])if len(sys.argv)>2 else 151145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=False)
W,H,D=240,76,208
mods=all_types(SEED);byid={m.id:m for m in mods}
city=Study('Taisho15',W,D,1,'櫻坂山溪町');city.blocks={};city.seed=SEED
height={};rawheight={};water=set();protected=set();road=set();hardscape=set();blocked=set();routes=[];records=[];alldoors=[];alluses=[];allstairs=[];alllights=[]
def river(z):return 193+round(12*math.sin(z*.032)+5*math.sin(z*.081))
def riverwidth(z):return 4+round(1.5*(1+math.sin(z*.051)))
def natural(x,z):
 h=7+2.5*math.sin(x*.038)+1.6*math.cos(z*.035)+1.4*math.sin((x+z)*.053)+.8*math.sin(x*.14)*math.cos(z*.13)
 h+=29*math.exp(-(((x-27)/32)**2+((z-24)/35)**2))+11*math.exp(-(((x-64)/37)**2+((z-20)/27)**2))
 dist=abs(x-river(z));rw=riverwidth(z)
 if dist<rw+16:h=min(h,3+(dist-rw)*.5)
 return max(3,round(h))
for x in range(W):
 for z in range(D):
  h=natural(x,z);rw=riverwidth(z);dist=abs(x-river(z));wet=dist<=rw and z not in[0,D-1]
  if wet:h=2;water.add((x,z))
  elif dist<=rw+2:h=3
  if x<78 and z<67 and h>=20:protected.add((x,z))
  rawheight[x,z]=height[x,z]=h
  for y in range(h+1):city.p(x,y,z,'stone'if y<h-2 else'dirt'if y<h else'grass_block','terrain')
  if wet:city.p(x,2,z,'gravel','river.bed');city.p(x,3,z,'water','river',level=0)
  elif dist<rw+6:
   patch=math.sin(x*.22+z*.17)
   city.p(x,h,z,'sand'if patch>.25 else'gravel'if patch>-.65 else'stone','river.bank')
terrain_base=copy.deepcopy(city)
# Helpers rotate both occupied geometry and every spatial interface.
def dims(m,r):return(m.w,m.d)if r%2==0 else(m.d,m.w)
def pt(q,m,o,r,continuous=False):
 x,y,z=q;w=m.w if continuous else m.w-1;d=m.d if continuous else m.d-1
 if r==1:x,z=d-z,x
 elif r==2:x,z=w-x,d-z
 elif r==3:x,z=z,w-x
 return[x+o[0],y+o[1],z+o[2]]
def rotstate(st,r):
 name,p=parse_state(st);dirs=['north','east','south','west'];mp={v:dirs[(i+r)%4]for i,v in enumerate(dirs)}
 if p.get('facing')in mp:p['facing']=mp[p['facing']]
 if r%2 and p.get('axis')in['x','z']:p['axis']='z'if p['axis']=='x'else'x'
 old={k:p.pop(k)for k in dirs if k in p}
 for k,v in old.items():p[mp[k]]=v
 if r%2 and p.get('shape')in['east_west','north_south']:p['shape']='north_south'if p['shape']=='east_west'else'east_west'
 return name+('['+','.join(k+'='+v for k,v in sorted(p.items()))+']'if p else'')
def footprint(m):return{(x,z)for(x,y,z),st in m.blocks.items()if y==2 and not st.startswith('minecraft:grass_block')and not m.owners.get((x,y,z),'').endswith('.street')}
def groundto(x,z,f,mat,owner):
 old=height[x,z]
 for y in range(min(old,f),max(old,f)+1):city.p(x,y,z,'stone'if y<f else mat if y==f else'air',owner)
 city.p(x,f,z,mat,owner);height[x,z]=f
# Fixed functional neighborhood hints; candidates and orientation choices are scored against frozen terrain.
anchors={'School':(100,8,0),'Library':(114,57,1),'Bookshop':(10,89,0),'Textile':(209,108,0),'Clinic':(161,8,1),'Sake':(157,50,2),'Tea':(12,143,3),'Photo':(25,60,3),'Pharmacy':(65,98,0),'Inn':(105,113,2),'Florist':(154,85,1),'Residence':(42,153,2),'Bakery':(102,166,1),'Post':(158,151,2),'Workshop':(65,57,0),'Bath':(5,171,2),'Clock':(172,120,0),'Station':(155,164,2)}
placements=[];rng=random.Random(str(SEED)+'/layout')
for id in ['School','Inn','Station','Clock','Clinic','Library','Workshop','Bath','Pharmacy','Bookshop','Residence','Sake','Florist','Textile','Photo','Tea','Post','Bakery']:
 m=byid[id];ax,az,ar=anchors[id];fp=footprint(m);candidates=[]
 for r in [ar,(ar+2)%4]:
  ww,dd=dims(m,r)
  for dx in range(-42,43,3):
   for dz in range(-42,43,3):
    x,z=ax+dx,az+dz
    if x<3 or z<3 or x+ww>W-8 or z+dd>D-3:continue
    cells={(pt([xx,0,zz],m,[x,0,z],r)[0],pt([xx,0,zz],m,[x,0,z],r)[2])for xx,zz in fp}
    if cells&(water|protected):continue
    reserve={(xx,zz)for xx in range(x-2,x+ww+2)for zz in range(z-2,z+dd+2)}
    if reserve&blocked:continue
    hs=[rawheight[q]for q in cells];f=round(statistics.median(hs));delta=[f-h for h in hs]
    if max(map(abs,delta))>5:continue
    score=sum(abs(v)for v in delta)/len(delta)+.035*(abs(dx)+abs(dz))+.12*(r!=ar)+rng.random()*.32
    candidates.append((score,x,z,r,f,cells,reserve,min(hs),max(hs)))
 if not candidates:raise RuntimeError('No low-impact site for '+id)
 score,x,z,r,f,cells,reserve,hmin,hmax=min(candidates,key=lambda a:a[0]);o=[x,f-2,z];blocked|=reserve;placements.append((m,o,r,cells));rec=m.stats();rec.update(origin=o,rotation=r*90,rotated_180=r==2,entry_world=pt(m.entry,m,o,r),upper_start=m.upper_start,form=m.form,raw_ground_range=[hmin,hmax],fit_score=round(score,3),size=[m.w,m.h,m.d]);records.append(rec)
 print('SITE',id,o,r,'terrain',hmin,hmax,flush=True)
 # Only the actual occupied ground footprint is levelled, not its rectangular parcel.
 for xx,zz in cells:groundto(xx,zz,f,'stone_bricks','foundation')
 # Building clearance above its true floor excludes trees (planted only later).
 for q,st in m.blocks.items():
  if q[1]<2:continue
  owner=m.owners.get(q,'')
  if q[1]==2 and(st.startswith('minecraft:grass_block')or owner.endswith('.street')):continue
  if any(owner.endswith('.'+s)for s in['groundcover','pot','shrub']):continue
  g=pt(q,m,o,r);city.p(*g,rotstate(st,r),owner)
 # Remove natural earth from every room/ground footprint above the floor, before overlaying geometry again.
 for xx,zz in cells:
  for yy in range(f+1,rawheight[xx,zz]+1):city.p(xx,yy,zz,'air')
 for q,st in m.blocks.items():
  if q[1]<=2:continue
  owner=m.owners.get(q,'')
  if any(owner.endswith('.'+s)for s in['groundcover','pot','shrub']):continue
  city.p(*pt(q,m,o,r),rotstate(st,r),owner)
 for q,be in m.bes.items():
  g=tuple(pt(q,m,o,r))
  if g in city.blocks:city.bes[g]=copy.deepcopy(be)
 for e in m.entities:
  ee=copy.deepcopy(e);q=pt([int(ee[k])for k in['TileX','TileY','TileZ']],m,o,r)
  for k,a in zip(['TileX','TileY','TileZ'],q):ee[k]=n.Int(a)
  ee['Pos']=n.List[n.Double]([n.Double(a)for a in pt(list(map(float,ee['Pos'])),m,o,r,True)]);ee['facing']=n.Byte((int(ee['facing'])+r)%4);city.entities.append(ee)
 for u in m.uses:alluses.append({**u,'pos':pt(u['pos'],m,o,r),'floor_block_y':u['floor_block_y']+o[1]})
 for d in m.doors:alldoors.append({**d,'pos':pt(d['pos'],m,o,r),'lintel':pt(d['lintel'],m,o,r),'facing':['north','east','south','west'][(['north','east','south','west'].index(d['facing'])+r)%4]})
 for l in m.lights:alllights.append({'position':pt(l['position'],m,o,r),'support':pt(l['support'],m,o,r)})
 for p in m.stair_paths:allstairs.append({'id':m.id,'path':[pt(q,m,o,r,True)for q in p],'start_y':o[1]+3,'end_y':o[1]+9})
 m.local_spec={'case_id':m.id,'run':RUN,'seed':SEED,'buildings':[{**m.stats(),'origin':[0,0,0]}],'uses':m.uses,'doors':m.doors,'lights':m.lights,'stairs':m.stair_paths,'spawn_local':[m.entry[0],3,m.entry[2]+1],'upper_start':m.upper_start}
 for x in range(m.entry[0]-1,m.entry[0]+2):m.p(x,2,m.entry[2]+1,'stone_bricks','threshold')
# Reserve true geometry, with shop thresholds and larger public paved areas instead of lawn to every wall.
solidplan={(x,z)for(x,y,z),st in city.blocks.items()if height.get((x,z),99)<y<=height.get((x,z),99)+2 and not st.startswith('minecraft:water')}
terminals=[];entrypaths=[]
for m,o,r,cells in placements:
 ex,ey,ez=pt(m.entry,m,o,r);dx,dz=[(0,1),(-1,0),(0,-1),(1,0)][r];f=ey-1
 path=[]
 for step in range(1,13):
  x,z=ex+dx*step,ez+dz*step
  if not(2<x<W-3 and 2<z<D-3):break
  if step>4:f=max(f-1,min(f+1,rawheight[x,z]))
  for s in[-1,0,1]:
   xx,zz=x+(s if dx==0 else 0),z+(s if dz==0 else 0)
   if (xx,zz)in water:continue
   groundto(xx,zz,f,'polished_andesite','entry.apron');hardscape.add((xx,zz))
   for yy in[f+1,f+2]:city.p(xx,yy,zz,'air')
  path.append((x,z))
 terminals.append((path[-1],m.id));entrypaths.append(path)
 f=ey-1
 # A broad irregular paved shop apron is confined to the front, not a universal square platform.
 for step in range(1,4):
  for side in range(-5,6):
   xx=ex+dx*step+(side if dx==0 else 0);zz=ez+dz*step+(side if dz==0 else 0)
   if(xx,zz)in solidplan or(xx,zz)in water or(xx,zz)in protected:continue
   if abs(height[xx,zz]-f)<=2:groundto(xx,zz,f,'andesite'if side%4 else'polished_andesite','shop.apron');hardscape.add((xx,zz))
# A river-side plaza surrounds the clock on all sides and meets the entry/river promenade.
clockrec=next(q for q in records if q['id']=='Clock');cx,cy,cz=clockrec['origin'];plazaf=cy+2
for x in range(cx-9,cx+23):
 for z in range(cz-8,cz+25):
  if not(1<x<W-1 and 1<z<D-1)or(x,z)in water or(x,z)in protected or(x,z)in solidplan:continue
  if((x-cx-6)/20)**2+((z-cz-7)/20)**2>1.1:continue
  if abs(height[x,z]-plazaf)>3:continue
  groundto(x,z,plazaf,'stone_bricks'if(x//5+z//4)%5 else'polished_andesite','clock.plaza');hardscape.add((x,z))
# Roads use original slopes and avoid footprints, reserved river cells and hard protection.
bridgecells=set();bridgeground={}
for bz in[98,159]:
 rc=river(bz);bf=5
 for x in range(rc-13,rc+14):
  for z in range(bz-1,bz+2):
   bridgeground[x,z]=height[x,z];height[x,z]=bf;city.p(x,bf,z,'spruce_planks','bridge.deck');bridgecells.add((x,z))
  for z in[bz-2,bz+2]:city.p(x,bf,z,'dark_oak_slab','bridge.edge',type='top');city.p(x,bf+1,z,'dark_oak_fence','bridge.rail')
 for x in[rc-12,rc+12]:
  for z in[bz-2,bz+2]:
   for y in range(rawheight[x,z]+1,bf):city.p(x,y,z,'stripped_spruce_log','bridge.pile',axis='y')
obstacles=solidplan|(water-bridgecells)
for path in entrypaths:
 for q in path:obstacles.discard(q)
# Keep exact road heights and steps, not landscape-wide planar gradients.
def route(start,goal):
 pq=[(0,start)];cost={start:0};came={};visited=0
 while pq:
  _,p=heapq.heappop(pq)
  if p==goal:
   a=[p]
   while p in came:p=came[p];a.append(p)
   return a[::-1]
  visited+=1;x,z=p
  for q in[(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
   X,Z=q
   if not(2<X<W-3 and 2<Z<D-3)or q in obstacles or q in protected:continue
   delta=abs(height[q]-height[p])
   if delta>1:continue
   # Road reuse and smooth slopes preferred; no random zigzag in the centreline.
   c=cost[p]+(.45 if q in road else 1)+delta*3
   if c<cost.get(q,1e9):cost[q]=c;came[q]=p;heapq.heappush(pq,(c+abs(X-goal[0])+abs(Z-goal[1]),q))
 return None
root=next(q for q,id in terminals if id=='Clock');network={root};pending=terminals.copy()
while pending:
 t,id=min(pending,key=lambda t:min(abs(t[0][0]-p[0])+abs(t[0][1]-p[1])for p in network));pending.remove((t,id));goals=sorted(network,key=lambda p:abs(t[0]-p[0])+abs(t[1]-p[1]))[:12];path=None
 for goal in goals:
  path=route(t,goal)
  if path:break
 if path is None:raise RuntimeError('No walking route '+id+' '+str(t))
 road.update(path);network.update(path);routes.append({'id':id,'cells':path})
for i,p in enumerate(entrypaths):routes.append({'id':'entry.'+str(i),'cells':p})
# Path width follows each local contour; step blocks mediate every height change.
for rec in routes:
 path=rec['cells']
 for x,z in path:
  f=height[x,z]
  for xx,zz in[(x,z),(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
   if(xx,zz)in obstacles or(xx,zz)in protected or abs(height[xx,zz]-f)>1:continue
   rr=random.Random(f'{SEED}/paving/{xx//4}/{zz//5}');mat=rr.choices(['cobblestone','mossy_cobblestone','andesite','gravel'],[70,10,15,5])[0]
   if (xx,zz)in bridgecells and mat=='gravel':mat='andesite'
   city.p(xx,height[xx,zz],zz,mat,'path.surface');road.add((xx,zz))
 for a,b in zip(path,path[1:]):
  if height[a]==height[b]:continue
  low,high=(a,b)if height[a]<height[b]else(b,a);dx,dz=high[0]-low[0],high[1]-low[1];face={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[dx,dz]
  city.p(low[0],height[low]+1,low[1],'cobblestone_stairs','path.step',facing=face)
# Private side/back gardens, two different materials; gates and walks lead to the same entrance apron.
yards=[]
for id in['Residence','Photo']:
 m,o,r,cells=next(p for p in placements if p[0].id==id);ww,dd=dims(m,r);x0,z0=o[0]-3,o[2]-5;X,Z=o[0]+ww+3,o[2]+dd+3;fences=[]
 for x,z in[(x,z0)for x in range(x0,X)]+[(x0,z)for z in range(z0,Z)]+[(X-1,z)for z in range(z0,Z)]:
  if not(1<x<W-1 and 1<z<D-1)or(x,z)in road or(x,z)in hardscape or(x,z)in solidplan or(x,z)in water:continue
  f=height[x,z];city.p(x,f+1,z,'cobblestone_wall'if id=='Residence'else'dark_oak_fence','private.boundary');fences.append([x,f+1,z])
 yards.append({'id':id,'boundary':fences,'open_side':'south; apron approach retained','privacy':'side and rear enclosure, varying ground level'})
# Mountain lookout: supported deck on the existing crown, with an open pavilion and a torii on approach.
peak=max(protected,key=lambda q:rawheight[q]);px,pz=peak;pf=rawheight[peak]+1
for x in range(px-5,px+6):
 for z in range(pz-4,pz+5):
  city.p(x,pf,z,'spruce_planks','lookout.deck')
  if x in[px-5,px+5]and z in[pz-4,pz+4]:
   for y in range(height[x,z]+1,pf):city.p(x,y,z,'stripped_spruce_log','lookout.pile',axis='y')
  if z==pz-4 or x in[px-5,px+5]:city.p(x,pf+1,z,'dark_oak_fence','lookout.rail')
for x in[px-4,px+4]:
 for z in[pz-3,pz+3]:city.box((x,pf+1,z),(x+1,pf+6,z+1),'stripped_dark_oak_log','pavilion.post',axis='y')
gable(city,px-6,pz-5,px+7,pz+6,pf+6,'x');city.lamp(px,pf+4,pz);alllights.append(city.lights[-1])
# A mountain stair trail can occupy protected ground without changing its original surface.
mountstart=(px,pz+5);mountend=min(network,key=lambda q:abs(q[0]-px)+abs(q[1]-pz));savedprotected=protected;protected=set();oldobs=obstacles;obstacles=solidplan|water
path=route(mountstart,mountend);protected=savedprotected;obstacles=oldobs
if path:
 for x,z in path:
  city.p(x,height[x,z],z,'cobblestone','mountain.trail');road.add((x,z))
 for a,b in zip(path,path[1:]):
  if height[a]!=height[b]:
   lo,hi=(a,b)if height[a]<height[b]else(b,a);face={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[hi[0]-lo[0],hi[1]-lo[1]];city.p(lo[0],height[lo]+1,lo[1],'cobblestone_stairs','mountain.stair',facing=face)
 routes.append({'id':'lookout_trail','cells':path})
# Deck edge step matches the crown without excavating it.
city.p(px,pf-1,pz+5,'spruce_stairs','lookout.entry',facing='north');city.p(px,pf,pz+4,'spruce_stairs','lookout.entry',facing='north');road.add((px,pz+5))
if path and len(path)>18:
 tx,tz=path[15];tf=height[tx,tz]
 for x in[tx-3,tx+3]:
  for y in range(height[x,tz]+1,tf+7):city.p(x,y,tz,'red_terracotta','torii.post')
 for x in range(tx-4,tx+5):city.p(x,tf+6,tz,'red_terracotta','torii.beam');city.p(x,tf+7,tz,'dark_oak_slab','torii.cap',type='top')
 for x in range(tx-3,tx+4):city.p(x,tf+4,tz,'red_terracotta','torii.tie')
# Sparse individually chosen lights: thresholds, bends and public nodes, not equal-spacing rows.
lamp_sites=[]
for rec in routes:
 path=rec['cells']
 for j in range(5,len(path),17+(len(rec['id'])%7)):
  x,z=path[j];x+=2
  if not(1<x<W-1 and 1<z<D-1)or(x,z)in solidplan|water|road or any((x-a)**2+(z-b)**2<50 for a,b in lamp_sites):continue
  f=height[x,z]
  if any((x,y,z)in city.blocks for y in range(f+1,f+6)):continue
  for y in range(f+1,f+5):city.p(x,y,z,'dark_oak_fence','lamp.post')
  city.p(x,f+5,z,'dark_oak_slab','lamp.arm',type='bottom');city.p(x+1,f+5,z,'dark_oak_slab','lamp.arm',type='bottom');city.p(x+1,f+4,z,'lantern','lamp',hanging=True);alllights.append({'position':[x+1,f+4,z],'support':[x+1,f+5,z]});lamp_sites.append((x,z))
# Plaza benches and planters take their support from finished paving; leave all mapped routes open.
for x,z in sorted(hardscape):
 if x<cx-8 or x>cx+21 or z<cz-7 or z>cz+24 or(x,z)in road:continue
 if(x-cx)%11==0 and(z-cz)%13==0 and all((xx,z)in hardscape and(xx,z)not in road|solidplan for xx in range(x,x+4)):
  for xx in range(x,x+4):city.p(xx,height[xx,z]+1,z,'dark_oak_slab','plaza.bench',type='bottom')
# Multi-scale plant clusters; canopy occupancy tested against actual buildings and walking envelope.
def tree(x,z,h,kind,rr):
 if (x-px)**2+(z-pz)**2<13**2 or px-5<x<px+19 and pz<z<pz+26:return False
 f=height[x,z];rad=rr.randint(3,5)if kind=='cherry'else rr.randint(2,4)
 if any((xx,zz)in road|hardscape|solidplan|water for xx in range(x-2,x+3)for zz in range(z-2,z+3)):return False
 cells=[]
 for dy in range(3,h+3):
  r=max(1,rad-(dy-3)//3)if kind=='spruce'else rad
  for dx in range(-r,r+1):
   for dz in range(-r,r+1):
    if kind=='spruce':valid=abs(dx)+abs(dz)<r+2
    else:valid=(dx/r)**2+(dz/r)**2+((dy-h)/2.7)**2<1.35
    if valid:cells.append((x+dx,f+dy,z+dz))
 if any(not(1<xx<W-1 and 1<zz<D-1)or yy>=H or (xx,zz)in solidplan or (xx,yy,zz)in city.blocks for xx,yy,zz in cells):return False
 for y in range(f+1,f+h+1):city.p(x,y,z,kind+'_log','tree.trunk',axis='y')
 for xx,yy,zz in cells:
  if(xx,yy,zz)not in city.blocks:city.p(xx,yy,zz,kind+'_leaves','tree.canopy',persistent=True,distance=1)
 return True
rr=random.Random(str(SEED)+'/groves');trees=[]
clusters=[('spruce',25,28,40,100),('spruce',60,16,25,25),('spruce',20,116,15,20),('spruce',226,40,14,20),('spruce',226,170,13,18),('cherry',70,145,20,16),('cherry',172,128,17,14),('cherry',155,80,18,15),('cherry',47,75,12,10),('cherry',125,185,13,12)]
for kind,cx0,cz0,radius,count in clusters:
 for _ in range(count):
  x=round(rr.gauss(cx0,radius*.55));z=round(rr.gauss(cz0,radius*.55))
  if not(7<x<W-7 and 7<z<D-7)or any((x-a[0])**2+(z-a[1])**2<(6 if kind=='cherry'else 4)**2 for a in trees):continue
  h=rr.randint(6,9)if kind=='cherry'else rr.randint(8,14)
  if tree(x,z,h,kind,rr):trees.append((x,z,kind,h))
for x in range(2,W-2):
 for z in range(2,D-2):
  f=height[x,z]
  if not city.blocks.get((x,f,z),'').startswith('minecraft:grass_block')or(x,f+1,z)in city.blocks or(x,z)in road|hardscape:continue
  p=.37 if math.sin(x*.2)+math.cos(z*.17)>.4 else.13
  if rr.random()<p:city.p(x,f+1,z,rr.choices(['short_grass','fern','oxeye_daisy','dandelion'],[55,30,10,5])[0],'groundcover')
  if abs(x-river(z))<15 and x<river(z)-8 and 45<z<95 and rr.random()<.13:
   for y in range(f+1,f+rr.randint(4,8)):city.p(x,y,z,'bamboo','bamboo',age=1,leaves='large'if y>f+3 else'none',stage=1)
# Re-seat transferred facade planters where local terrain grading removed their support.
for (x,y,z),st in list(city.blocks.items()):
 if st.startswith('minecraft:potted_') and not any(bb[4]>=1 and bb[0]<=.5<=bb[3] and bb[2]<=.5<=bb[5] for bb in S.boxes(city.blocks.get((x,y-1,z),'minecraft:air'))):
  city.p(x,y-1,z,'spruce_planks','planter.support')
# Independent terrain audit: protection is measured in surface heights, not plant replacement.
groundheight={**height,**bridgeground}
deltas=[{'x':x,'z':z,'before':rawheight[x,z],'after':groundheight[x,z]}for x in range(W)for z in range(D)if rawheight[x,z]!=groundheight[x,z]]
terrain={'seed':SEED,'dimensions':[W,H,D],'protected_columns':len(protected),'protected_changed':sum(height[q]!=rawheight[q]for q in protected),'changed_columns':len(deltas),'unchanged_columns':W*D-len(deltas),'cut_blocks':sum(max(0,q['before']-q['after'])for q in deltas),'fill_blocks':sum(max(0,q['after']-q['before'])for q in deltas),'delta':deltas,'trees':trees,'yards':yards,'lookout':{'point':[px,pf+1,pz],'peak_ground':rawheight[peak],'route_found':bool(path)},'source':'authored analytic terrain frozen before site selection; not vanilla worldgen'}
assert terrain['protected_changed']==0
# Exact-state sparse NBT exporter.
def clean(m):
 for q,be in list(m.bes.items()):
  name=m.blocks.get(q,'minecraft:air').split('[')[0];expect='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else'minecraft:banner'if name.endswith('_wall_banner')else name
  if str(be['id'])!=expect:del m.bes[q]
def save(m,name,sp,size):
 clean(m);sc=Scene(size,max_cells=4000000)
 for q,st in m.blocks.items():sc.set(q,st,m.owners.get(q,'detail'))
 S.connect(sc)
 for st in set(sc.blocks.values()):S.validate(st)
 raw=OUT/(name+'.geometry.tmp');export_structure(sc,raw,include_air=False);f=n.load(raw)
 for b in f['blocks']:
  q=tuple(map(int,b['pos']))
  if q in m.bes:b['nbt']=m.bes[q]
 f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(e['Pos']),'blockPos':n.List[n.Int]([e[k]for k in['TileX','TileY','TileZ']]),'nbt':e})for e in m.entities]);buf=io.BytesIO();f.write(buf);p=OUT/(name+'.nbt');p.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
 sp.update(source_nbt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),non_air=len(sc.blocks),size_xyz=list(size),block_entities=len(m.bes),entities=len(m.entities));(OUT/(name+'_spec.json')).write_text(json.dumps(sp,ensure_ascii=False,indent=2));return sp
save(terrain_base,'Terrain_Input',{'case_id':'Terrain_Input','run':RUN,'seed':SEED,'scope':'Frozen terrain before buildings'},(W,H,D))
for m in mods:save(m,m.id,m.local_spec,(m.w,m.h,m.d))
sp={'case_id':'Taisho15','run':RUN,'mainline':'HAF 0.4','seed':SEED,'buildings':sorted(records,key=lambda r:list(anchors).index(r['id'])),'uses':alluses,'doors':alldoors,'lights':alllights,'stairs':allstairs,'routes':routes,'landmarks':[{'id':'mountain_lookout','pos':[px,pf+1,pz]}],'spawn_local':[root[0],height[root]+1,root[1]],'terrain':{k:v for k,v in terrain.items()if k not in['delta','trees','yards']},'scope':'Terrain-led case-specific candidate packing and height-aware A* routes; program-linked wing recipes. Not arbitrary NBT solver.','status':{'game':'pending','aesthetic':'pending user review'}}
save(city,'Taisho15',sp,(W,H,D));(OUT/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(OUT/'terrain_audit.json').write_text(json.dumps(terrain,ensure_ascii=False,indent=2));(OUT/'heightmap_before.json').write_text(json.dumps([[rawheight[x,z]for x in range(W)]for z in range(D)]));(OUT/'heightmap.json').write_text(json.dumps([[height[x,z]for x in range(W)]for z in range(D)]));print('BUILT',RUN,'buildings',len(mods),'blocks',len(city.blocks),flush=True)
