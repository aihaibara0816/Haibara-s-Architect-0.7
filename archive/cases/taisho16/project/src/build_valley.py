"""T16 forest valley case adapter. Design constraints precede building placement."""
from pathlib import Path
import sys,json,copy,hashlib,io,gzip,random,math,heapq,statistics,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n,taisho_states
from prototype_base import Study
from valley_types import all_types
from quarter_types import gable
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state
from valley_terrain import W,H,D,river,riverwidth,riverlevel,natural
RUN=sys.argv[1]if len(sys.argv)>1 else'V01';SEED=int(sys.argv[2])if len(sys.argv)>2 else 151145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=False)
mods=all_types(SEED);byid={m.id:m for m in mods}
city=Study('Taisho16',W,D,1,'木漏日溪谷・森の街');city.blocks={};city.seed=SEED
height={};rawheight={};water=set();protected=set();road=set();hardscape=set();blocked=set();routes=[];records=[];alldoors=[];alluses=[];allstairs=[];alllights=[]
for x in range(W):
 for z in range(D):
  h=natural(x,z);rw=riverwidth(z);dist=abs(x-river(z));wet=20<=z<D-1 and dist<=rw
  if wet:water.add((x,z));h=riverlevel(z)-2
  # All lateral banks are at least as high as the neighboring water surface.
  if not wet and 19<=z<D and dist<rw+3:h=max(h,max(riverlevel(zz)for zz in range(max(20,z-1),min(D,z+2))))
  if z<65 and h>=22:protected.add((x,z))
  rawheight[x,z]=height[x,z]=h
  for y in range(h+1):city.p(x,y,z,'stone'if y<h-2 else'dirt'if y<h else'grass_block','terrain')
  if wet:
   city.p(x,h,z,'gravel','river.bed')
   for y in range(h+1,riverlevel(z)+1):city.p(x,y,z,'water','river',level=0)
  elif z>=19 and dist<rw+6:
   patch=math.sin(x*.22+z*.17);city.p(x,h,z,'sand'if patch>.35 else'gravel'if patch>-.65 else'andesite','river.bank')
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
# Reserve a connected road hierarchy BEFORE placing the 18 buildings.
bridgecells=set();bridgeground={};bridgeends=[]
for bz in [132,229]:
 rc=river(bz);bf=riverlevel(bz)+2;rw=riverwidth(bz)
 for x in range(rc-rw-5,rc+rw+6):
  for z in range(bz-3,bz+4):
   bridgeground[x,z]=height[x,z];height[x,z]=bf;city.p(x,bf,z,'spruce_planks','bridge.deck');bridgecells.add((x,z))
  for z in[bz-4,bz+4]:
   city.p(x,bf,z,'dark_oak_slab','bridge.edge',type='top');city.p(x,bf+1,z,'dark_oak_fence','bridge.rail')
 for x in[rc-rw-4,rc+rw+4]:
  for z in[bz-4,bz+4]:
   for y in range(rawheight[x,z]+1,bf):city.p(x,y,z,'stripped_spruce_log','bridge.pile',axis='y')
 bridgeends.append(((rc-rw-5,bz),(rc+rw+5,bz)))
obstacles=water-bridgecells
# Search favors broad gentle corridors, without a random checkerboard centreline.
def route(start,goal,avoid=None):
 avoid=obstacles if avoid is None else avoid;pq=[(0,start)];cost={start:0};came={}
 while pq:
  _,p=heapq.heappop(pq)
  if p==goal:
   a=[p]
   while p in came:p=came[p];a.append(p)
   return a[::-1]
  x,z=p
  for q in[(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
   X,Z=q
   if not(5<X<W-6 and 5<Z<D-6)or q in avoid:continue
   delta=abs(height[q]-height[p])
   if delta>1:continue
   c=cost[p]+1+delta*4+(.1 if q in road else .4)
   if c<cost.get(q,1e12):cost[q]=c;came[q]=p;heapq.heappush(pq,(c+abs(X-goal[0])+abs(Z-goal[1]),q))
 return None
trunks=[('main.west',7,[(100,275),(92,240),(98,204),(100,172),(107,144),(112,122),(95,102),(76,81),(55,62)]),('main.east',7,[(238,274),(241,242),(219,217),(211,185),(217,160),(207,133),(193,109),(171,88),(162,63)]),('main.west_loop',5,[(92,240),(51,227),(43,183),(61,146),(95,102)]),('main.bridge_upper',7,[(107,144),bridgeends[0][0],bridgeends[0][1],(207,133)]),('main.bridge_lower',7,[(92,240),bridgeends[1][0],bridgeends[1][1],(241,242)])]
mainreserve=set();maincenter=set()
for id,width,points in trunks:
 path=[]
 for a,b in zip(points,points[1:]):
  p=route(a,b)
  if p is None:raise RuntimeError(('main road route',id,a,b))
  path+=p if not path else p[1:]
 for x,z in path:
  maincenter.add((x,z))
  for dx in range(-width//2-1,width//2+3):
   for dz in range(-width//2-1,width//2+3):mainreserve.add((x+dx,z+dz))
 routes.append({'id':id,'hierarchy':'main','clear_width':width,'cells':path});road.update(path)
# Nearest-main distance for entrance orientation and candidate scoring.
main_distance={q:0 for q in maincenter};queue=collections.deque(maincenter)
while queue:
 x,z=queue.popleft()
 for q in[(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
  if 0<=q[0]<W and 0<=q[1]<D and q not in main_distance:main_distance[q]=main_distance[x,z]+1;queue.append(q)
# Fixed functional neighborhood hints; candidates and orientation choices are scored against frozen terrain.
anchors={'School':(237,75,1),'Library':(242,146,1),'Bookshop':(9,155,3),'Textile':(182,153,3),'Clinic':(190,62,1),'Sake':(115,153,1),'Tea':(72,69,0),'Photo':(26,132,3),'Pharmacy':(114,195,1),'Inn':(54,187,3),'Florist':(265,159,1),'Residence':(12,249,2),'Bakery':(102,252,2),'Post':(222,244,2),'Workshop':(18,88,0),'Bath':(244,202,1),'Hall':(117,233,2),'Station':(167,244,0)}
chosen=json.loads((ROOT/'input/selected_layout.json').read_text()) if SEED==151145 else {}
placements=[];rng=random.Random(str(SEED)+'/layout')
for id in ['School','Inn','Station','Hall','Clinic','Library','Workshop','Bath','Pharmacy','Bookshop','Residence','Sake','Florist','Textile','Photo','Tea','Post','Bakery']:
 m=byid[id];ax,az,ar=anchors[id];fp=footprint(m);candidates=[];rotfps={rr:[(pt([xx,0,zz],m,[0,0,0],rr)[0],pt([xx,0,zz],m,[0,0,0],rr)[2])for xx,zz in fp]for rr in range(4)}
 for r in ([chosen[id]['r']] if id in chosen else [ar,(ar+1)%4,(ar+2)%4,(ar+3)%4]):
  ww,dd=dims(m,r)
  for dx in ([chosen[id]['origin'][0]-ax]if id in chosen else range(-30,31,3)):
   for dz in ([chosen[id]['origin'][2]-az]if id in chosen else range(-30,31,3)):
    x,z=ax+dx,az+dz
    if x<3 or z<3 or x+ww>W-8 or z+dd>D-3:continue
    cells={(xx+x,zz+z)for xx,zz in rotfps[r]}
    if cells&(water|protected|mainreserve):continue
    reserve={(xx,zz)for xx in range(x-2,x+ww+2)for zz in range(z-2,z+dd+2)}
    if reserve&blocked:continue
    hs=[rawheight[q]for q in cells];f=round(statistics.median(hs));delta=[f-h for h in hs]
    if max(map(abs,delta))>5:continue
    ep=pt(m.entry,m,[x,0,z],r);direction=[(0,1),(-1,0),(0,-1),(1,0)][r];front=(ep[0]+direction[0]*10,ep[2]+direction[1]*10)
    if front not in main_distance:continue
    score=sum(abs(v)for v in delta)/len(delta)+.055*(abs(dx)+abs(dz))+.17*(r!=ar)+.065*main_distance[front]+rng.random()*.65
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
 m.local_spec={'case_id':m.id,'run':RUN,'seed':SEED,'buildings':[{**m.stats(),'origin':[0,0,0],'entry_world':m.entry}],'uses':m.uses,'doors':m.doors,'lights':m.lights,'stairs':m.stair_paths,'spawn_local':[m.entry[0],3,m.entry[2]+1],'upper_start':m.upper_start}
 for x in range(m.entry[0]-1,m.entry[0]+2):m.p(x,2,m.entry[2]+1,'stone_bricks','threshold')
import pickle
for sub in [n.Compound,n.Int,n.String,n.Double,n.Float,n.Short,n.Byte]:
 cls=n.List[sub];setattr(n.tag,cls.__name__,cls)
(OUT/'placement_checkpoint.pkl').write_bytes(pickle.dumps({k:globals()[k]for k in ['city','terrain_base','height','rawheight','water','protected','road','hardscape','blocked','routes','records','alldoors','alluses','allstairs','alllights','placements','mods','bridgecells','bridgeground','maincenter','anchors']}))
# Reserve true geometry, with shop thresholds and larger public paved areas instead of lawn to every wall.
solidplan={(x,z)for(x,y,z),st in city.blocks.items()if height.get((x,z),99)<y<=height.get((x,z),99)+2 and not st.startswith('minecraft:water')}
terminals=[];entrypaths=[]
for m,o,r,cells in placements:
 ex,ey,ez=pt(m.entry,m,o,r);dx,dz=[(0,1),(-1,0),(0,-1),(1,0)][r];f=ey-1
 path=[]
 for step in range(1,17):
  x,z=ex+dx*step,ez+dz*step
  if not(2<x<W-3 and 2<z<D-3):break
  if step>3 and (x,z)in solidplan:break
  if step>3:f=max(f-1,min(f+1,height[x,z]))
  for s in[-1,0,1]:
   xx,zz=x+(s if dx==0 else 0),z+(s if dz==0 else 0)
   if (xx,zz)in water or (xx,zz)in maincenter:continue
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
obstacles=solidplan|(water-bridgecells)
for path in entrypaths:
 for q in path:obstacles.discard(q)
network=set(maincenter);road=set()
for terminal,id in terminals:
 path=None
 for goal in sorted(network,key=lambda p:abs(p[0]-terminal[0])+abs(p[1]-terminal[1]))[:80]:
  path=route(terminal,goal)
  if path:break
 if path is None:raise RuntimeError('No branch '+id+' '+str(terminal))
 routes.append({'id':id,'hierarchy':'branch','clear_width':3,'cells':path});network.update(path)
for i,p in enumerate(entrypaths):routes.append({'id':'entry.'+str(i),'hierarchy':'entry','clear_width':3,'cells':p})
# Wide cross-sections are levelled locally. Entire building parcels are never terraced.
roadheight={tuple(q):height[tuple(q)]for rr in routes for q in rr['cells']if tuple(q)not in obstacles};roadclass={q:3 for q in roadheight}
for rec in routes:
 radius=rec['clear_width']//2
 for x,z in rec['cells']:
  f=height[x,z]
  for xx in range(x-radius,x+radius+1):
   for zz in range(z-radius,z+radius+1):
    q=(xx,zz)
    if q in obstacles or q in roadheight:continue
    if q in bridgecells or q in protected:fq=height[q]
    else:fq=f
    if abs(height[q]-fq)>3:continue
    roadheight[q]=fq;roadclass[q]=rec['clear_width']
for (x,z),f in roadheight.items():
 rr=random.Random(f'{SEED}/paving/{x//5}/{z//6}');mat=rr.choices(['cobblestone','mossy_cobblestone','andesite','gravel'],[74,9,14,3])[0]
 if(x,z)in bridgecells:city.p(x,f,z,'spruce_planks','bridge.deck')
 else:groundto(x,z,f,mat,'path.surface')
 for y in range(f+1,f+4):
  if city.owners.get((x,y,z),'').startswith(('Taisho16.terrain','Taisho16.path','Taisho16.entry')):city.p(x,y,z,'air')
 road.add((x,z))
# Stair strips span every road width; central paths carry explicit stair direction.
for x,z in sorted(road):
 f=height[x,z]
 for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
  q=(x+dx,z+dz)
  if q in road and height[q]==f+1:
   face={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[dx,dz]
   city.p(x,f+1,z,'cobblestone_stairs','path.step',facing=face);break
# Small river square belongs to the hall, with material edges and seating.
hallrec=next(q for q in records if q['id']=='Hall');cx,cy,cz=hallrec['origin'];plazaf=cy+2
for x in range(cx-4,cx+31):
 for z in range(cz-8,cz+4):
  q=x,z
  if q in solidplan|water|road or q in protected or not(2<x<W-2 and 2<z<D-2):continue
  if abs(height[q]-plazaf)>2:continue
  groundto(x,z,plazaf,'stone_bricks'if(x//6+z//5)%4 else'andesite','hall.square');hardscape.add(q)
# Private side/back gardens, two different materials; gates and walks lead to the same entrance apron.
yards=[]
for id in['Residence','Photo']:
 m,o,r,cells=next(p for p in placements if p[0].id==id);ww,dd=dims(m,r);x0,z0=o[0]-3,o[2]-5;X,Z=o[0]+ww+3,o[2]+dd+3;fences=[]
 for x,z in[(x,z0)for x in range(x0,X)]+[(x0,z)for z in range(z0,Z)]+[(X-1,z)for z in range(z0,Z)]:
  if not(1<x<W-1 and 1<z<D-1)or(x,z)in road or(x,z)in hardscape or(x,z)in solidplan or(x,z)in water:continue
  f=height[x,z];city.p(x,f+1,z,'cobblestone_wall'if id=='Residence'else'dark_oak_fence','private.boundary');fences.append([x,f+1,z])
 yards.append({'id':id,'boundary':fences,'open_side':['south','west','north','east'][r]+'; entrance apron kept open','privacy':'side and rear enclosure, varying ground level'})
# Mountain lookout: supported deck on the existing crown, with an open pavilion and a torii on approach.
peak=min(protected,key=lambda q:(q[0]-36)**2+(q[1]-37)**2);px,pz=peak;pf=rawheight[peak]+1
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
 routes.append({'id':'lookout_trail','hierarchy':'trail','clear_width':3,'cells':path})
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
  x,z=path[j];x+=5
  if not(1<x<W-1 and 1<z<D-1)or(x,z)in solidplan|water|road or any((x-a)**2+(z-b)**2<50 for a,b in lamp_sites):continue
  f=height[x,z]
  if any((x,y,z)in city.blocks for y in range(f+1,f+6)):continue
  for y in range(f+1,f+5):city.p(x,y,z,'dark_oak_fence','lamp.post')
  city.p(x,f+5,z,'dark_oak_slab','lamp.arm',type='bottom');city.p(x+1,f+5,z,'dark_oak_slab','lamp.arm',type='bottom');city.p(x+1,f+4,z,'lantern','lamp',hanging=True);alllights.append({'position':[x+1,f+4,z],'support':[x+1,f+5,z]});lamp_sites.append((x,z))
# Plaza benches and planters take their support from finished paving; leave all mapped routes open.
for x,z in sorted(hardscape):
 if x<cx-8 or x>cx+30 or z<cz-7 or z>cz+24 or(x,z)in road:continue
 if(x-cx)%11==0 and(z-cz)%13==0 and all((xx,z)in hardscape and(xx,z)not in road|solidplan for xx in range(x,x+4)):
  for xx in range(x,x+4):city.p(xx,height[xx,z]+1,z,'dark_oak_slab','plaza.bench',type='bottom')
# Forest is a connected canopy, not a few isolated ornaments. Overlapping leaves
# are allowed; geometry, trunks and the road walking envelope remain protected.
tree_reserved=road|hardscape|solidplan|water
plant_reserved=road|hardscape
trees=[];rr=random.Random(str(SEED)+'/groves')
def tree(x,z,h,kind):
 f=height[x,z];rad=rr.randint(4,6)if kind=='spruce'else rr.randint(4,6)
 if any((xx,zz)in tree_reserved for xx in range(x-2,x+3)for zz in range(z-2,z+3)):return False
 if (x-px)**2+(z-pz)**2<9**2:return False
 cells=[]
 for dy in range(5,h+3):
  if kind=='spruce':r=max(1,round(rad*(1-(dy-5)/(h-1)))+(1 if dy%3==1 else 0))
  else:r=rad
  for dx in range(-r,r+1):
   for dz in range(-r,r+1):
    valid=abs(dx)+abs(dz)<=r+max(1,r//2) if kind=='spruce'else(dx/r)**2+(dz/r)**2+((dy-h)/3.1)**2<1.25
    if valid:cells.append((x+dx,f+dy,z+dz))
 for xx,yy,zz in cells:
  if not(1<xx<W-1 and 1<zz<D-1)or yy>=H:return False
  st=city.blocks.get((xx,yy,zz),'minecraft:air');owner=city.owners.get((xx,yy,zz),'')
  if st!='minecraft:air'and not any(t in owner for t in['tree.','terrain','groundcover']):return False
  if(xx,zz)in road and yy<=height[xx,zz]+4:return False
 for y in range(f+1,f+h+1):
  st=city.blocks.get((x,y,z),'minecraft:air')
  if st!='minecraft:air'and 'tree.'not in city.owners.get((x,y,z),''):return False
 for y in range(f+1,f+h+1):city.p(x,y,z,kind+'_log','tree.trunk',axis='y')
 for xx,yy,zz in cells:
  if (xx,yy,zz)not in city.blocks:city.p(xx,yy,zz,kind+'_leaves','tree.canopy',persistent=True,distance=1)
 trees.append((x,z,kind,h));return True
# Dense north forest, side groves, then scattered village canopy; separate seeds.
for attempt in range(8500):
 x=rr.randrange(8,W-8);z=rr.randrange(7,D-7)
 dense=z<82 or x<33 or x>277 or (x<78 and z<145)
 grove=math.sin(x*.061+z*.019)+math.cos(z*.077-x*.021)>.5
 if not dense and rr.random()>(.38 if grove else .12):continue
 spacing=5 if dense else 8
 if any((x-a)**2+(z-b)**2<spacing**2 for a,b,_,_ in trees):continue
 tree(x,z,rr.randint(13,23)if dense else rr.randint(11,18),'spruce')
for cx0,cz0 in [(136,230),(227,185),(80,170),(204,145),(245,104),(130,183)]:
 for _ in range(10):
  x=round(rr.gauss(cx0,10));z=round(rr.gauss(cz0,9))
  if not(9<x<W-9 and 9<z<D-9)or any((x-a)**2+(z-b)**2<8**2 for a,b,_,_ in trees):continue
  tree(x,z,rr.randint(7,10),'cherry')
for x in range(2,W-2):
 for z in range(2,D-2):
  f=height[x,z]
  if not city.blocks.get((x,f,z),'').startswith('minecraft:grass_block')or(x,f+1,z)in city.blocks or(x,z)in plant_reserved:continue
  p=.46 if math.sin(x*.2)+math.cos(z*.17)>.4 else.23
  if rr.random()<p:city.p(x,f+1,z,rr.choices(['short_grass','fern','oxeye_daisy','dandelion'],[42,47,8,3])[0],'groundcover')
  if abs(x-river(z))<20 and x<river(z)-9 and 82<z<116 and rr.random()<.17:
   for y in range(f+1,f+rr.randint(4,9)):city.p(x,y,z,'bamboo','bamboo',age=1,leaves='large'if y>f+3 else'none',stage=1)
# Re-seat transferred facade planters where local terrain grading removed their support.
for (x,y,z),st in list(city.blocks.items()):
 if st.startswith('minecraft:potted_') and not any(bb[4]>=1 and bb[0]<=.5<=bb[3] and bb[2]<=.5<=bb[5] for bb in S.boxes(city.blocks.get((x,y-1,z),'minecraft:air'))):
  city.p(x,y-1,z,'spruce_planks','planter.support')
from finish_fixes import apply as finish_fixes
finish_fixes(city,height,rawheight)
# Independent terrain audit: protection is measured in surface heights, not plant replacement.
groundheight={**height,**bridgeground}
deltas=[{'x':x,'z':z,'before':rawheight[x,z],'after':groundheight[x,z]}for x in range(W)for z in range(D)if rawheight[x,z]!=groundheight[x,z]]
terrain={'seed':SEED,'dimensions':[W,H,D],'protected_columns':len(protected),'protected_changed':sum(height[q]!=rawheight[q]for q in protected),'changed_columns':len(deltas),'unchanged_columns':W*D-len(deltas),'cut_blocks':sum(max(0,q['before']-q['after'])for q in deltas),'fill_blocks':sum(max(0,q['after']-q['before'])for q in deltas),'delta':deltas,'trees':trees,'yards':yards,'lookout':{'point':[px,pf+1,pz],'peak_ground':rawheight[peak],'route_found':bool(path)},'source':'authored elongated ridge and descending central creek; T07-inspired spatial relationships; not copied terrain or vanilla worldgen'}
assert terrain['protected_changed']==0
(OUT/'finished_checkpoint.pkl').write_bytes(pickle.dumps({k:globals()[k]for k in ['city','terrain_base','terrain','height','rawheight','water','protected','road','hardscape','routes','records','alldoors','alluses','allstairs','alllights','mods','anchors','px','pf','pz']}))
# Exact-state sparse NBT exporter.
def clean(m):
 for q,be in list(m.bes.items()):
  name=m.blocks.get(q,'minecraft:air').split('[')[0];expect='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else'minecraft:banner'if name.endswith('_wall_banner')else name
  if str(be['id'])!=expect:del m.bes[q]
def save(m,name,sp,size):
 clean(m);sc=Scene(size,max_cells=12000000)
 for q,st in m.blocks.items():sc.set(q,st,m.owners.get(q,'detail'))
 S.connect(sc)
 for st in set(sc.blocks.values()):S.validate(st)
 p=OUT/(name+'.nbt')
 if len(sc.blocks)>200000:
  from stream_structure import write
  write(p,sc,m.bes,m.entities)
 else:
  raw=OUT/(name+'.geometry.tmp');export_structure(sc,raw,include_air=False);f=n.load(raw)
  for b in f['blocks']:
   q=tuple(map(int,b['pos']))
   if q in m.bes:b['nbt']=m.bes[q]
  f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(e['Pos']),'blockPos':n.List[n.Int]([e[k]for k in['TileX','TileY','TileZ']]),'nbt':e})for e in m.entities]);buf=io.BytesIO();f.write(buf);p=OUT/(name+'.nbt');p.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
 sp.update(source_nbt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),non_air=len(sc.blocks),size_xyz=list(size),block_entities=len(m.bes),entities=len(m.entities));(OUT/(name+'_spec.json')).write_text(json.dumps(sp,ensure_ascii=False,indent=2));return sp
save(terrain_base,'Terrain_Input',{'case_id':'Terrain_Input','run':RUN,'seed':SEED,'scope':'Frozen terrain before roads and buildings'},(W,H,D))
del terrain_base
for m in mods:save(m,m.id,m.local_spec,(m.w,m.h,m.d))
sp={'case_id':'Taisho16','run':RUN,'mainline':'HAF 0.4','seed':SEED,'buildings':sorted(records,key=lambda r:list(anchors).index(r['id'])),'uses':alluses,'doors':alldoors,'lights':alllights,'stairs':allstairs,'routes':routes,'river_water_columns':[[x,z,riverlevel(z)]for x,z in sorted(water)],'road_hierarchy':{'main':[q['id']for q in routes if q.get('hierarchy')=='main'],'widths':[7,5,3]},'landmarks':[{'id':'mountain_lookout','pos':[px,pf+1,pz]}],'spawn_local':[100,height[100,275]+1,275],'terrain':{k:v for k,v in terrain.items()if k not in['delta','trees','yards']},'scope':'T16 case-specific main-road-first valley adapter; 17 preserved T15 modules and one occupied public hall. Not an arbitrary NBT solver.','status':{'game':'pending','aesthetic':'pending user review'}}
save(city,'Taisho16',sp,(W,H,D));(OUT/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(OUT/'terrain_audit.json').write_text(json.dumps(terrain,ensure_ascii=False,indent=2));(OUT/'heightmap_before.json').write_text(json.dumps([[rawheight[x,z]for x in range(W)]for z in range(D)]));(OUT/'heightmap.json').write_text(json.dumps([[height[x,z]for x in range(W)]for z in range(D)]));print('BUILT',RUN,'buildings',len(mods),'blocks',len(city.blocks),flush=True)
