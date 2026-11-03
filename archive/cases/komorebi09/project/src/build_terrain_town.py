"""Terrain-first bounded adaptation of 18 preserved Japanese interiors.
Generates a reproducible terrain input before earthworks/roads/buildings.
Not Minecraft native worldgen and not an arbitrary terrain-NBT planner.
"""
from pathlib import Path
import sys,json,math,random,hashlib,copy,argparse,heapq,io,gzip,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import terrain_states,modules,nbtlib as n
from detail_lab import states as S
from vendor.voxel_core import Scene,state,parse_state,export_structure
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--seed',type=int,default=1145);ap.add_argument('--layout-seed',type=int,default=309);ap.add_argument('--plan-only',action='store_true');a=ap.parse_args()
R=ROOT/'runs'/a.run;R.mkdir(parents=True,exist_ok=False);W,D,Y=224,184,64
rng=lambda id:random.Random(int(hashlib.sha256(f'komorebi-terrain-1|{a.seed}|{id}'.encode()).hexdigest()[:16],16))
layout=random.Random(a.layout_seed)
xx,zz=np.meshgrid(np.arange(W),np.arange(D),indexing='ij')
# A broad mountain shoulder plus low foothills; edge taper joins the surrounding ground.
h0=6+30*np.exp(-((xx-36)/34)**2-((zz-32)/35)**2)+8*np.exp(-((xx-30)/38)**2-((zz-88)/39)**2)+4*np.exp(-((xx-111)/50)**2-((zz-24)/32)**2)+10*np.exp(-((xx-85)/44)**2-((zz-26)/28)**2)
noise=(np.sin(xx/14+zz/21)+.6*np.sin(xx/7-zz/13)+.35*np.cos(zz/5+xx/23))
taper=np.clip(np.minimum.reduce([xx,zz,W-1-xx,D-1-zz])/12,0,1)
h0=6+(h0-6+noise)*taper;h0=6+(h0-6)*30/(h0.max()-6);H=np.rint(h0).astype(int)
# Continuous downhill channel, with an east-side receiving creek.
stream_nodes=[[62,40,25],[72,50,21],[82,61,17],[98,68,13],[122,74,10],[148,64,8],[178,57,6],[202,73,4],[207,98,4],[200,123,4],[206,150,4],[210,182,4]]
water={};stream=[]
for i,(u,v)in enumerate(zip(stream_nodes,stream_nodes[1:])):
 length=max(abs(v[0]-u[0]),abs(v[1]-u[1]))*3
 for j in range(length+1):
  t=j/length;x=round(u[0]*(1-t)+v[0]*t);z=round(u[1]*(1-t)+v[1]*t);y=round(u[2]*(1-t)+v[2]*t);r=2 if i<5 else 3+(1 if i in[8,9]else 0)
  if not stream or stream[-1][:2]!=[x,z]:stream.append([x,z,y])
  for dx in range(-r,r+1):
   for dz in range(-r,r+1):
    if dx*dx+dz*dz>(r+.25)**2 or not(2<=x+dx<W-2 and 2<=z+dz<D):continue
    q=(x+dx,z+dz);water[q]=max(water.get(q,0),y)
# Taper valley shoulders into the source heightfield, retain solid banks.
for (x,z),y in water.items():
 for dx in range(-5,6):
  for dz in range(-5,6):
   X,Z=x+dx,z+dz
   if 0<=X<W and 0<=Z<D:H[X,Z]=min(H[X,Z],int(y+1+math.hypot(dx,dz)*.7))
for (x,z),y in water.items():H[x,z]=y-2
for (x,z),y in water.items():
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  X,Z=x+dx,z+dz
  if 0<=X<W and 0<=Z<D and(X,Z)not in water:H[X,Z]=max(H[X,Z],y)
baseH=H.copy();baselinewater=copy.deepcopy(water)
programs=[('machiya','日和小食'),('single','茶と菓子'),('single','八百屋'),('machiya','古本と茶'),('single','花屋'),('compact','住家・青葉'),('single','干物店'),('compact','小さな宿'),('single','木工房'),('compact','仕立屋'),('machiya','米と雑貨'),('compact','住家・白壁'),('machiya','路地の酒場'),('compact','住家・木窓'),('single','文庫'),('single','木葉湯'),('compact','住家・庭先'),('single','陶器店')]
# Candidate neighborhoods follow the slope and stream; bounded seed jitter is accepted only without overlap.
slots=[(99,91,10,0),(124,103,9,0),(147,94,9,1),(164,116,7,0),(132,140,8,2),(31,92,17,3),(106,150,8,2),(65,82,14,0),(71,122,11,3),(125,27,14,2),(156,25,12,1),(18,131,11,0),(166,80,8,0),(51,145,9,1),(82,18,21,1),(176,151,6,2),(104,15,18,0),(149,155,7,2)]
footprints=set();pads={};buildings=[];modlist=[]
def transform(q,m,origin,rot,continuous=False):
 x,y,z=q;w,d=m.w,m.d;sub=0 if continuous else 1
 if rot==1:x,z=d-sub-z,x
 elif rot==2:x,z=w-sub-x,d-sub-z
 elif rot==3:x,z=z,w-sub-x
 return[x+origin[0],y+origin[1],z+origin[2]]
for i,((family,name),(sx,sz,h,rot))in enumerate(zip(programs,slots)):
 id=f'B{i+1:02d}'
 m=modules.machiya(id,name,a.seed,i%4)if family=='machiya'else modules.compact(id,name,a.seed,i%3)if family=='compact'else modules.single(id,name,a.seed,w=18 if name=='木葉湯'else(17 if i%2 else 16),d=19 if name=='木葉湯'else(18 if i%2 else 17),variant=i)
 w,d=(m.d,m.w)if rot%2 else(m.w,m.d);accepted=None
 for attempt in range(30):
  x0,z0=sx+layout.randint(-2,2),sz+layout.randint(-2,2);area={(x,z)for x in range(x0-1,x0+w+1)for z in range(z0-1,z0+d+1)}
  if not(area&footprints or area&set(water)):accepted=x0,z0,area;break
 assert accepted,id
 x0,z0,area=accepted;footprints|=area;origin=[x0,h-2,z0]
 # Feather earthworks beyond the pad. No global flattening.
 for x in range(x0-7,x0+w+7):
  for z in range(z0-7,z0+d+7):
   if(x,z)in water or not(2<=x<W-2 and 2<=z<D-2):continue
   distance=max(x0-x,0,x-(x0+w-1),z0-z,0,z-(z0+d-1));weight=max(0,1-distance/7)
   if distance<=1:pads[x,z]=h
   H[x,z]=round(H[x,z]*(1-weight)+h*weight)
 for x,z in area:H[x,z]=h;pads[x,z]=h
 tr=lambda q,c=False:transform(q,m,origin,rot,c)
 us=[{**u,'pos':tr(u['pos']),'floor_block_y':u['floor_block_y']+h-2}for u in m.uses]
 doors=[]
 for dd in m.doors:
  face=dd['facing']
  for _ in range(rot):face=S.TURN[face]
  doors.append({**dd,'pos':tr(dd['pos']),'lintel':tr(dd['lintel']),'facing':face})
 lights=[{**l,'position':tr(l['position']),'support':tr(l['support'])}for l in m.lights]
 entry=tr(m.entry);direction=[(0,1),(-1,0),(0,-1),(1,0)][rot]
 ex,ey,ez=entry
 # Walk to the outside of this module rather than through a window/roof projection.
 front=[ex,ez]
 while (front[0],front[1])in area:front=[front[0]+direction[0],front[1]+direction[1]]
 front=[front[0]+direction[0],front[1]+direction[1]]
 starts={str(h):[ex,ez]}
 if family=='machiya':starts[str(h+5)]=tr([6,8,14])[::2]
 elif family=='compact':starts[str(h+5)]=tr([3,8,9])[::2]
 bd={'id':id,'name':name,'family':family,'floors':m.levels,'module_size':[m.w,24,m.d],'origin':origin,'rotation':rot*90,'bounds':[x0,h-2,z0,x0+w,h+22,z0+d],'floor_y':h,'entry':entry,'front_outside':[front[0],h+1,front[1]],'floor_starts':starts,'use_points':us,'doors':doors,'lights':lights,'stairs':[[tr(p,True)for p in path]for path in m.stair_paths]}
 buildings.append(bd);modlist.append((m,bd,rot))
# Public nodes are distributed among terrain-compatible candidate pockets.
public=[{'id':'P01','name':'山麓休憩亭','pos':[62,23,61],'kind':'pavilion'},{'id':'P02','name':'桥头告示与候坐处','pos':[133,13,83],'kind':'notice'},{'id':'P03','name':'溪边洗手与休息台','pos':[189,7,113],'kind':'water_stop'}]
for p in public:
 x,h,z=p['pos'];rad=4 if p['kind']=='pavilion'else 2
 for X in range(x-rad-3,x+rad+4):
  for Z in range(z-rad-3,z+rad+4):
   if(X,Z)in water or(X,Z)in footprints:continue
   dist=max(abs(X-x),abs(Z-z))-rad;f=max(0,min(1,1-dist/4));H[X,Z]=round(H[X,Z]*(1-f)+h*f)
   if dist<=0:pads[X,Z]=h
# Planned path anchors carry grades; A* respects lots and the protected water corridor.
networks=[[[36,124,12],[58,116,12],[87,112,12],[103,123,10],[126,128,9],[151,123,8],[193,111,7]],[[36,124,12],[36,157,10],[45,169,9],[82,173,8],[101,142,9],[126,128,9]],[[126,128,9],[154,145,7],[190,144,6],[193,111,7]],[[83,48,20],[104,48,17],[123,54,15],[145,54,12],[183,48,10],[194,63,8],[189,77,8],[193,111,7]],[[123,54,15],[123,67,15],[123,82,15],[92,85,13],[87,112,12]],[[36,124,12],[49,116,15],[56,99,17],[58,78,22],[62,61,23],[83,48,20]]]
route={};roadpaths=[];bridges=set();terrace_routes=[]
def astar(start,end,avoid=True):
 start,end=tuple(start),tuple(end);heap=[(0,0,start)];prev={start:None};cost={start:0}
 while heap:
  _,g,q=heapq.heappop(heap)
  if g!=cost[q]:continue
  if q==end:
   result=[]
   while q is not None:result.append(q);q=prev[q]
   return result[::-1]
  for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
   t=(q[0]+dx,q[1]+dz)
   if not(3<=t[0]<W-3 and 3<=t[1]<D-3)or(avoid and t in footprints):continue
   ww=8 if t in water else 0
   # Existing road attracts connectors; slope is a cost, not an absolute ban before grading.
   c=.55 if t in route else 1.0
   ng=g+c+min(3,abs(int(H[t])-int(H[q])))*.16+ww
   if ng<cost.get(t,1e20):cost[t]=ng;prev[t]=q;heapq.heappush(heap,(ng+(abs(t[0]-end[0])+abs(t[1]-end[1]))*.5,ng,t))
 raise RuntimeError(('no path',start,end))
def grade_path(path,ha,hb,id,width=3):
 # Interpolate endpoint grade; protect water with a continuous raised bridge deck.
 ys=[round(ha+(hb-ha)*i/max(1,len(path)-1))for i in range(len(path))]
 for i,q in enumerate(path):
  if q in water:ys[i]=max(ys[i],water[q]+2)
 for _ in range(3):
  for i in range(1,len(ys)):ys[i]=max(ys[i],ys[i-1]-1)
  for i in range(len(ys)-2,-1,-1):ys[i]=max(ys[i],ys[i+1]-1)
 pts=[]
 for i,((x,z),h)in enumerate(zip(path,ys)):
  rad=width//2
  for dx in range(-rad,rad+1):
   for dz in range(-rad,rad+1):
    X,Z=x+dx,z+dz
    if(X,Z)in footprints:continue
    if(X,Z)in water:
     if h<water[X,Z]+2:h=water[X,Z]+2
     bridges.add((X,Z));route[X,Z]=h
    else:
     if(X,Z)in pads:h=max(h,pads[X,Z])
     route[X,Z]=h;H[X,Z]=h
  pts.append([x,h+1,z])
 roadpaths.append({'id':id,'points':pts,'width':width})
for ni,network in enumerate(networks):
 for j,(u,v)in enumerate(zip(network,network[1:])):
  path=astar(u[:2],v[:2]);grade_path(path,u[2],v[2],f'R{ni+1}.{j+1}',width=3 if ni!=0 else 5)
# Entrances and public nodes attach to the actual connected network.
for bd in buildings:
 x,y,z=bd['front_outside'];start=(x,z);target=min(route,key=lambda q:(q[0]-x)**2+(q[1]-z)**2)
 path=astar(start,target);grade_path(path,bd['floor_y'],route[target],bd['id']+'.approach',3)
 ex,ey,ez=bd['entry'];p0=astar((ex,ez),start,avoid=False)
 # Threshold-to-front is level and belongs to this building's clearance, not a new street.
 for X,Z in p0:
  for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
   if (X+dx,Z+dz)not in water:route[X+dx,Z+dz]=bd['floor_y'];H[X+dx,Z+dz]=bd['floor_y']
 terrace_routes.append({'id':bd['id'],'points':p0,'floor_y':bd['floor_y']})
for p in public:
 x,h,z=p['pos'];start=(x,z+3);target=min(route,key=lambda q:(q[0]-x)**2+(q[1]-z-3)**2);grade_path(astar(start,target),h,route[target],p['id']+'.approach',3)
# Neighboring route cells must differ at most one block; locked pads set the constraints.
for _ in range(80):
 changed=False
 for q,h in list(route.items()):
  for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
   t=(q[0]+dx,q[1]+dz)
   if t not in route or abs(route[t]-route[q])<=1:continue
   low,high=(q,t)if route[q]<route[t]else(t,q)
   if low in pads:
    if high in pads:continue
    route[high]=route[low]+1
   else:route[low]=route[high]-1
   changed=True
 if not changed:break
for q,h in route.items():
 if q not in water:H[q]=h
# Blend only the thin road shoulder, preserving established pads and creek.
for (x,z),h in route.items():
 for dx in range(-3,4):
  for dz in range(-3,4):
   q=(x+dx,z+dz)
   if not(1<=q[0]<W-1 and 1<=q[1]<D-1)or q in route or q in pads or q in water:continue
   d=abs(dx)+abs(dz)
   if d<=3:H[q]=max(h-d,min(h+d,int(H[q])))
for q,h in pads.items():H[q]=h
# Keep every outside bank at least as high as the adjacent source-water block.
for (x,z),y in water.items():
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=(x+dx,z+dz)
  if 0<=q[0]<W and 0<=q[1]<D and q not in water:H[q]=max(H[q],y)
# Final route grades reflect protected thresholds.
for q in route:
 if q not in water:route[q]=int(H[q])
plan={'case_id':'Komorebi09','run':a.run,'version':'terrain-1','seed':a.seed,'layout_seed':a.layout_seed,'size_xyz':[W,Y,D],'coordinates':'+X east, +Z south','buildings':buildings,'public_nodes':public,'roads':roadpaths,'route_heights':[[x,z,h]for(x,z),h in sorted(route.items())],'water_levels':[[x,z,h]for(x,z),h in sorted(water.items())],'stream_centerline':stream,'mountain':{'peak_local_y':int(baseH.max()),'settlement_datum_y':6,'relative_height':int(baseH.max())-6,'position':list(map(int,np.unravel_index(baseH.argmax(),baseH.shape)))},'reference':'input/Songshanhu_reference.png; spatial composition only, not a measured reconstruction','terrain_method':'authored seeded heightfield, not native Minecraft world generation','randomness':{'layout':'bounded candidate-site jitter; stable 18 programs and neighborhoods, not an arbitrary NBT planner','planting':'seeded contextual spruce clusters and groundcover','paths':'graded routes; coherent material patches, cobblestone dominant'},'limitations':['game execution pending','source interiors reused; 3 bounded families','not a generic terrain NBT importer or autonomous settlement solver']}
np.save(R/'terrain_original.npy',baseH);np.save(R/'terrain_final.npy',H);(R/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
if a.plan_only:print('plan only',flush=True);raise SystemExit()
scene=Scene((W,Y,D),max_cells=4000000);bes={};entities=[];lights=[]
def put(x,y,z,name,owner,**props):
 if not(0<=x<W and 0<=y<Y and 0<=z<D):raise ValueError((x,y,z,name))
 st=S.make(name,**{k:str(v).lower()for k,v in props.items()})if not name.startswith('minecraft:')else name;scene.set((int(x),int(y),int(z)),st,owner);bes.pop((int(x),int(y),int(z)),None)
def terrain(hf):
 ss=Scene((W,Y,D),max_cells=4000000)
 for x in range(W):
  for z in range(D):
   h=int(hf[x,z]);slope=max(abs(h-int(hf[min(W-1,x+1),z])),abs(h-int(hf[x,min(D-1,z+1)])))
   top='stone'if h>24 and slope>=2 else'grass_block'
   if(x,z)in water:top='gravel'
   for y in range(h+1):ss.set((x,y,z),S.make(top if y==h else'dirt'if y>=h-2 else'stone'),'terrain')
 return ss
print('terrain input',flush=True);baseline=terrain(baseH)
for(x,z),h in water.items():
 for y in [h-1,h]:baseline.set((x,y,z),S.make('water',level=0),'water')
export_structure(baseline,R/'Terrain_Input.nbt',include_air=False);del baseline
print('terrain earthworks',flush=True);scene=terrain(H)
for(x,z),h in water.items():
 for y in range(int(H[x,z])+1,h+1):put(x,y,z,'water','water.channel',level=0)
# Cobble-dominant paths use contiguous patch contexts, not independent salt-and-pepper noise.
path_materials=collections.Counter();stair_cells=[]
for(x,z),h in route.items():
 if(x,z)in footprints:continue
 rr=rng(f'roadpatch/{x//4}/{z//4}');v=rr.random()
 material='cobblestone'if v<.76 else'mossy_cobblestone'if v<.85 else'andesite'if v<.93 else'gravel'
 if(x,z)in bridges:material='spruce_planks'
 put(x,h,z,material,'road.surface');path_materials[material]+=1
 if(x,z)not in bridges:
  # Standard stairs on one-block changes. Wider landings at junctions remain level.
  higher=[(dx,dz)for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]if route.get((x+dx,z+dz))==h+1]
  if higher:
   dx,dz=higher[0];face={(1,0):'east',(-1,0):'west',(0,1):'south',(0,-1):'north'}[dx,dz]
   put(x,h+1,z,'cobblestone_stairs','road.riser',facing=face);stair_cells.append([x,h+1,z,face])
# Route shoulders expose patches of worn soil rather than a uniform green ribbon.
for(x,z),h in list(route.items()):
 for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
  q=(x+dx,z+dz)
  if q in route or q in footprints or q in water or not(2<=q[0]<W-2 and 2<=q[1]<D-2):continue
  if not any((q[0]+ddx,q[1]+ddz)in water for ddx,ddz in[(1,0),(-1,0),(0,1),(0,-1)])and rng(f'edge/{q[0]//3}/{q[1]//3}').random()<.38:put(q[0],int(H[q]),q[1],'dirt_path','road.worn_edge')
print('place buildings',flush=True)
for m,bd,rot in modlist:
 origin=bd['origin'];tr=lambda q,c=False:transform(q,m,origin,rot,c)
 for q,st in m.blocks.items():
  for _ in range(rot):st=S.rotate_state(st)
  scene.set(tuple(tr(q)),st,bd['id']+'.building')
 for q,be in m.bes.items():bes[tuple(tr(q))]=copy.deepcopy(be)
 for en in m.entities:
  en=copy.deepcopy(en);en['Pos']=n.List[n.Double](map(n.Double,tr(list(map(float,en['Pos'])),True)))
  anchor=tr([int(en[k])for k in['TileX','TileY','TileZ']])
  for k,v in zip(['TileX','TileY','TileZ'],anchor):en[k]=n.Int(v)
  en['facing']=n.Byte((int(en['facing'])+rot)%4);en['Rotation'][0]=n.Float((float(en['Rotation'][0])+rot*90)%360);entities.append(en)
 lights+=bd['lights']
 # Low retaining stone only where a pad has a real exposed cut/fill face.
 x0,_,z0,x1,_,z1=bd['bounds'];h=bd['floor_y']
 for x in range(x0-1,x1+1):
  for z in range(z0-1,z1+1):
   if x not in[x0-1,x1]and z not in[z0-1,z1]:continue
   low=min(int(H[x+dx,z+dz])for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)])
   for yy in range(max(0,low),h):put(x,yy,z,'mossy_cobblestone'if(yy+x+z)%5==0 else'cobblestone',bd['id']+'.retaining')
# Program-specific exterior additions: bath chimney and workshop stock yard.
bath=buildings[15];x0,_,z0,x1,_,z1=bath['bounds'];h=bath['floor_y']
for yy in range(h+1,h+15):
 for x in range(x1,x1+2):
  for z in range(z1-5,z1-3):put(x,yy,z,'bricks','B16.chimney')
# Public pavilion / information shelter / wash-stop: three open structures, outside the 18 enclosed buildings.
for p in public:
 x,h,z=p['pos'];kind=p['kind'];r=4 if kind=='pavilion'else 2
 for X in range(x-r,x+r+1):
  for Z in range(z-r,z+r+1):put(X,h,Z,'spruce_planks'if kind=='pavilion'else'cobblestone',p['id']+'.floor')
 if kind=='pavilion':
  for dx,dz in[(-3,-3),(3,-3),(-3,3),(3,3)]:
   opts=sorted([(xx,zz)for xx in range(3,6)for zz in range(3,6)],key=lambda q:sum(q))
   px,pz=next((x+(1 if dx>0 else -1)*xx,z+(1 if dz>0 else -1)*zz)for xx,zz in opts if(x+(1 if dx>0 else -1)*xx,z+(1 if dz>0 else -1)*zz)not in route)
   for yy in range(min(int(H[px,pz]),h)+1,h+5):put(px,yy,pz,'spruce_log',p['id']+'.post',axis='y')
  for dx in range(-5,6):
   for dz in range(-5,6):put(x+dx,h+5+max(0,2-abs(dz)//2),z+dz,'spruce_slab',p['id']+'.roof',type='bottom')
  put(x,h+4,z,'lantern',p['id']+'.lamp',hanging=True);put(x,h+5,z,'spruce_planks',p['id']+'.support');lights.append({'position':[x,h+4,z],'support':[x,h+5,z]})
  for dx in[-2,-1,0,1,2]:put(x+dx,h+1,z-2,'spruce_stairs',p['id']+'.bench',facing='south')
 elif kind=='notice':
  for dx in[-2,2]:
   for yy in range(h+1,h+4):put(x+dx,yy,z-1,'spruce_log',p['id']+'.post',axis='y')
  for dx in range(-2,3):put(x+dx,h+3,z-1,'spruce_planks',p['id']+'.board');put(x+dx,h+4,z-1,'spruce_slab',p['id']+'.cap')
  for dx in[-1,0,1]:put(x+dx,h+1,z+1,'spruce_stairs',p['id']+'.bench',facing='north')
 else:
  put(x-1,h+1,z-1,'water_cauldron',p['id']+'.basin',level=3)
  for dx in[0,1,2]:put(x+dx,h+1,z-1,'spruce_stairs',p['id']+'.bench',facing='south')
# Lamps at selected bends / endpoints, all with real support and no path obstruction.
for j in range(0,len(roadpaths),2):
 path=roadpaths[j]['points'];x,_,z=path[len(path)//2]
 for dx,dz in[(3,0),(-3,0),(0,3),(0,-3)]:
  X,Z=x+dx,z+dz
  if(X,Z)not in route and(X,Z)not in footprints and(X,Z)not in water and scene.blocks.get((X,int(H[X,Z])+1,Z),'minecraft:air')=='minecraft:air':break
 else:continue
 h=int(H[X,Z]);put(X,h+1,Z,'cobblestone','light.base')
 for yy in range(h+2,h+5):put(X,yy,Z,'spruce_fence','light.post')
 put(X,h+5,Z,'spruce_slab','light.cap',type='bottom');put(X+1,h+4,Z,'spruce_log','light.arm',axis='x');put(X+1,h+3,Z,'lantern','light.lamp',hanging=True);lights.append({'position':[X+1,h+3,Z],'support':[X+1,h+4,Z]})
# Contextual forest: denser on the mountain, broken at yards, views and stream crossings.
def available(x,z,margin=0):
 if not(5<=x<W-5 and 5<=z<D-5):return False
 for dx in range(-margin,margin+1):
  for dz in range(-margin,margin+1):
   q=(x+dx,z+dz)
   if q in route or q in footprints or q in water:return False
 h=int(H[x,z]);return scene.blocks.get((x,h+1,z),'minecraft:air')=='minecraft:air'and 'grass_block'in scene.blocks.get((x,h,z),'')
trees=[];candidates=[(x,z)for x in range(7,W-6,4)for z in range(7,D-6,4)];rng('trees').shuffle(candidates)
for x,z in candidates:
 rr=rng(f'tree/{x}/{z}');density=.94 if x<80 and z<95 else .36
 if any((x-bx)**2+(z-bz)**2<90 for bx,bz in [(75,72),(89,46),(132,88),(188,121),(151,75),(99,140),(159,141)])or rr.random()>density or not available(x,z,3)or any((x-t['x'])**2+(z-t['z'])**2<32 for t in trees):continue
 h=int(H[x,z]);height=rr.randint(8,13);radius=rr.choice([2,3]);kind='spruce'
 # Keep full crown clear of constructed structures, not merely the trunk.
 if any(scene.owners.get((X,y,Z),'').startswith(('B','P','road','light'))for X in range(x-radius,x+radius+1)for Z in range(z-radius,z+radius+1)for y in range(h+3,h+height+2)):continue
 for y in range(h+1,h+height+1):put(x,y,z,'spruce_log','plant.tree.trunk',axis='y')
 for y in range(h+3,h+height+2):
  remain=h+height+1-y;r=min(radius,max(0,math.ceil(remain/3)))
  if remain%3==0 and r>1:r-=1
  for dx in range(-r,r+1):
   for dz in range(-r,r+1):
    if abs(dx)+abs(dz)>r*1.6+.5:continue
    q=(x+dx,y,z+dz)
    if q not in scene.blocks:put(*q,'spruce_leaves','plant.tree.canopy')
 for dx in range(-2,3):
  for dz in range(-2,3):
   X,Z=x+dx,z+dz
   if available(X,Z)and rr.random()<.65:put(X,int(H[X,Z]),Z,'podzol','plant.forest_soil')
 trees.append({'id':f'T{len(trees)+1:03d}','x':x,'z':z,'ground':h,'height':height,'radius':radius,'kind':kind})
# Broad cherry crowns at social/bridge nodes; bamboo occupies two coherent groves.
cherry_points=[(132,88),(188,121),(151,75),(99,140),(159,141)]
for ci,(cx,cz)in enumerate(cherry_points):
 opts=sorted([(x,z)for x in range(cx-5,cx+6)for z in range(cz-5,cz+6)if available(x,z,3)],key=lambda q:(q[0]-cx)**2+(q[1]-cz)**2)
 if not opts:continue
 x,z=opts[0];h=int(H[x,z]);height=6+ci%2;radius=3
 for y in range(h+1,h+height+1):put(x,y,z,'oak_log','plant.cherry.trunk',axis='y')
 for y in range(h+height-2,h+height+3):
  for dx in range(-radius,radius+1):
   for dz in range(-radius,radius+1):
    if dx*dx+dz*dz+(y-h-height)**2*2>13:continue
    q=(x+dx,y,z+dz)
    if q not in scene.blocks:put(*q,'cherry_leaves','plant.cherry.canopy')
 trees.append({'id':f'C{ci+1:02d}','x':x,'z':z,'ground':h,'height':height,'radius':radius,'kind':'cherry'})
bamboo=[]
for gi,(cx,cz,rad)in enumerate([(75,72,8),(89,46,7)]):
 for x in range(cx-rad,cx+rad+1):
  for z in range(cz-rad,cz+rad+1):
   if ((x-cx)/rad)**2+((z-cz)/(rad*.7))**2>1 or not available(x,z,1):continue
   rr=rng(f'bamboo/{gi}/{x}/{z}')
   if rr.random()>.38:continue
   h=int(H[x,z]);height=rr.randint(4,8)
   if any(scene.blocks.get((x,y,z),'minecraft:air')!='minecraft:air'for y in range(h+1,h+height+1)):continue
   for j in range(1,height+1):put(x,h+j,z,'bamboo','plant.bamboo',age=1,leaves='large'if j>=height-1 else'small'if j==height-2 else'none',stage=1 if j==height else 0)
   bamboo.append({'grove':gi+1,'anchor':[x,h+1,z],'height':height})
plants=[]
for x in range(3,W-3):
 for z in range(3,D-3):
  if not available(x,z):continue
  rr=rng(f'ground/{x}/{z}');cluster=.5+.5*math.sin(x/7+math.sin(z/11))*math.cos(z/9)
  if rr.random()>.10+.48*cluster:continue
  h=int(H[x,z]);shade=any((x-t['x'])**2+(z-t['z'])**2<(t['radius']+1)**2 for t in trees)
  patch=rng(f'flowerpatch/{x//9}/{z//9}').choice(['oxeye_daisy','dandelion','cornflower','azure_bluet'])
  name=rr.choices(['fern'if shade else'short_grass',patch,'large_fern'if shade else'tall_grass'],[78,16,6])[0]
  if name in['large_fern','tall_grass']:
   if scene.blocks.get((x,h+2,z),'minecraft:air')!='minecraft:air':name='short_grass'
   else:put(x,h+2,z,name,'plant.ground',half='upper')
  put(x,h+1,z,name,'plant.ground',**({'half':'lower'}if name in['large_fern','tall_grass']else{}));plants.append({'anchor':[x,h+1,z],'kind':name})
print('connect / export',len(scene.blocks),flush=True);S.connect(scene)
for st in set(scene.blocks.values()):S.validate(st)
base=R/'base.nbt';export_structure(scene,base,include_air=False);f=n.load(base)
f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(en['Pos']),'blockPos':n.List[n.Int]([en[k]for k in['TileX','TileY','TileZ']]),'nbt':en})for en in entities])
for e in f['blocks']:
 q=tuple(map(int,e['pos']))
 if q in bes:e['nbt']=bes[q]
buf=io.BytesIO();f.write(buf);out=R/'Komorebi09.nbt';out.write_bytes(gzip.compress(buf.getvalue(),mtime=0));base.unlink()
changed=H-baseH
sp={**plan,'source_nbt_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'terrain_input_sha256':hashlib.sha256((R/'Terrain_Input.nbt').read_bytes()).hexdigest(),'mainline':'HAF 0.4','route_cells':[[x,z]for x,z in sorted(route)],'bridges':[[x,z,h]for(x,z),h in sorted(route.items())if(x,z)in bridges],'water_cells':[[x,z]for x,z in water],'lights':lights,'trees':trees,'groundcover':plants,'bamboo':bamboo,'stairs_outdoor':stair_cells,'path_materials':dict(path_materials),'earthworks':{'changed_columns':int(np.sum(changed!=0)),'cut_blocks':int(-changed[changed<0].sum()),'fill_blocks':int(changed[changed>0].sum()),'unchanged_columns':int(np.sum(changed==0))},'non_air':len(scene.blocks),'block_entities':len(bes),'paintings':len(entities),'spawn_local':[126,route[126,128]+1,128],'status':{'geometry':'pending','game':'pending','aesthetic':'pending'}}
(R/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(R/'owners.json').write_text(json.dumps({','.join(map(str,q)):v for q,v in scene.owners.items()}))
print(json.dumps({k:sp[k]for k in ['run','non_air','source_nbt_sha256','mountain','earthworks','path_materials']}),flush=True)
