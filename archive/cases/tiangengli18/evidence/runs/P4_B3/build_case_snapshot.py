"""P4 landscape revision of the immutable P3_B4 NBT; no house regeneration."""
from pathlib import Path
import sys,json,gzip,random,heapq,shutil,math,hashlib
import numpy as np
from scipy.ndimage import binary_dilation,label,distance_transform_cdt
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump
M=states.make;run=sys.argv[1] if len(sys.argv)>1 else 'P4_B1';BASE=C/'runs/P3_B4'
old=load_build(BASE/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
p=json.loads((BASE/'params_used.json').read_text());rng=random.Random(20261029)
b=Builder(old.size,20261029);b.s.blocks=dict(old.blocks)
ow=json.loads(gzip.decompress((BASE/'component_ownership.json.gz').read_bytes()))
b.s.owners={tuple(a[:3]):ow['owner_names'][a[3]] for a in ow['xyz_owner']}
original_owners=dict(b.s.owners);B=b.s.blocks
for attr,name in [('rooms','interiors.json'),('windows','windows.json')]:
 if (BASE/name).exists():setattr(b,attr,json.loads((BASE/name).read_text()))
road=np.load(BASE/'roadmask.npy');H,W=road.shape
house=np.zeros_like(road);facility=np.zeros_like(road);field=np.zeros_like(road);banks=np.zeros_like(road)
for h in p['buildings']:
 x,z,w,d=h['x'],h['z'],h['w'],h['d'];house[z-2:z+d+2,x-2:x+w+2]=True
for q,o in original_owners.items():
 if o.startswith('R'):house[q[2],q[0]]=True
for rect in [(245,97,304,137),(240,228,305,251),(243,258,261,269),(282,256,294,269)]:
 x,z,u,v=rect;facility[z:v,x:u]=True
def put(x,y,z,mat,owner='P4.landscape'):b.put(x,y,z,mat,owner)
def erase(x,y,z):B.pop((x,y,z),None);b.s.owners.pop((x,y,z),None)
def clear(x,z,y0=3,y1=5):
 for y in range(y0,y1):erase(x,y,z)
def water(x,z,owner='P4.irrigation',cap=False):
 put(x,1,z,'dirt',owner+'.bed');put(x,2,z,'water',owner)
 if not cap:
  for y in (3,4):
   if not house[z,x] and not facility[z,x]:erase(x,y,z)
paddies={'F01.1','F02.1','F04.1','F06.2','F06.3','F09.2','F14.1','F15.1'}
collectors={};fieldstats=[]
for f in p['fields']:
 a,c,u,v=f['bounds'];field[c+1:v-1,a+1:u-1]=True;banks[c:v,a:u]=True
 coll=set();wet=f['id'] in paddies;f['surface_y']=2;f['bank_y']=3;f['landscape_type']='flooded_paddy_visual' if wet else 'lowered_dry_field'
 # A wet perimeter joins every irrigation strip; irregular crop ages remain seeded.
 spacing=rng.choice([3,4]);offset=rng.randrange(spacing)
 for z in range(c+1,v-1):
  for x in range(a+1,u-1):
   edge=x in (a+1,u-2) or z in (c+1,v-2)
   s3=old.blocks.get((x,3,z),'minecraft:dirt');s4=old.blocks.get((x,4,z))
   clear(x,z);put(x,1,z,'dirt','P4.field.bed')
   if wet:
    strip=((x if f['rows']=='N' else z)+offset)%spacing==0 and not edge
    # Leave a crossing pool halfway along long planting strips.
    if strip and (z if f['rows']=='N' else x)%19 not in (0,1):
     put(x,2,z,M('farmland',moisture=7),'P4.paddy.soil');put(x,3,z,M('wheat',age=rng.choices([1,2,3,4,5],[1,3,4,3,1])[0]),'P4.paddy.seedling')
    else:water(x,z,'P4.paddy.water')
   else:
    put(x,2,z,s3,'P4.field.lowered')
    if s4:put(x,3,z,s4,'P4.field.lowered')
   if edge:
    water(x,z,'P4.field.collector');coll.add((x,z))
 collectors[f['id']]=coll
 fieldstats.append({'id':f['id'],'type':f['landscape_type'],'soil_drop':1,'water_cells':sum('water' in B.get((x,2,z),'') for z in range(c+1,v-1) for x in range(a+1,u-1))})
# Lower existing exterior channels, retaining all building/greenhouse systems.
network=set()
for (x,y,z),s in old.blocks.items():
 if y==3 and 'minecraft:water' in s and not field[z,x] and not facility[z,x] and not house[z,x]:
  water(x,z,cap=bool(road[z,x] or banks[z,x] or b.s.owners.get((x,3,z))=='P4.path'));network.add((x,z))
# Two-block-wide peripheral channel, with road decks left above the water.
for x in range(6,315):
 for z in [6,7,284,285]:water(x,z,cap=bool(road[z,x]));network.add((x,z))
for z in range(6,286):
 for x in [6,7,313,314]:water(x,z,cap=bool(road[z,x]));network.add((x,z))
blocked=house|facility|field
routes=[]
def connect(start,labelname):
 """A* to the current backbone; fields and house foundations are forbidden."""
 goal=np.ones_like(road,dtype=np.uint8)
 for x,z in network:goal[z,x]=0
 dist=distance_transform_cdt(goal,metric='taxicab');q=[(int(dist[start[1],start[0]]),0,start)];best={start:0};prev={}
 end=None
 while q:
  _,g,t=heapq.heappop(q)
  if g!=best[t]:continue
  if t in network:end=t;break
  x,z=t
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   xx,zz=x+dx,z+dz;v=(xx,zz)
   if not(2<=xx<W-2 and 2<=zz<H-2) or blocked[zz,xx]:continue
   cost=1+(5 if road[zz,xx] else 0)+(1 if banks[zz,xx] else 0)
   ng=g+cost
   if ng<best.get(v,10**9):best[v]=ng;prev[v]=t;heapq.heappush(q,(ng+int(dist[zz,xx]),ng,v))
 if end is None:raise ValueError('No canal route '+labelname)
 path=[end]
 while path[-1]!=start:path.append(prev[path[-1]])
 for x,z in path:water(x,z,cap=bool(road[z,x] or banks[z,x] or b.s.owners.get((x,3,z))=='P4.path'));network.add((x,z))
 routes.append({'id':labelname,'path':path,'culvert_cells':sum(bool(road[z,x]) for x,z in path)})
 return path
for f in p['fields']:
 a,c,u,v=f['bounds'];mx=(a+u)//2;mz=(c+v)//2
 opts=[((a,mz),(a+1,mz)),((u-1,mz),(u-2,mz)),((mx,c),(mx,c+1)),((mx,v-1),(mx,v-2))]
 opts=[o for o in opts if not house[o[0][1],o[0][0]] and not facility[o[0][1],o[0][0]]]
 start,inner=min(opts,key=lambda o:min(abs(o[0][0]-x)+abs(o[0][1]-z) for x,z in network))
 connect(start,f['id']);water(*inner,'P4.field.inlet');network.update(collectors[f['id']]);network.add(inner)
# Irregular irrigation pond in the open pocket beside R04.
pond=set()
for z in range(70,94):
 for x in range(198,229):
  theta=math.atan2((z-81)/9,(x-213)/13)
  if ((x-213)/13)**2+((z-81)/9)**2 < 1+.09*math.sin(theta*5)+.05*math.cos(theta*3):
   if not house[z,x] and not road[z,x]:pond.add((x,z));water(x,z,'P4.pond.water')
blocked|=np.array([[ (x,z) in pond for x in range(W)] for z in range(H)])
edge=min(pond,key=lambda t:t[0]);connect((edge[0]-1,edge[1]),'pond');network.update(pond)
for x,z in pond:
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  xx,zz=x+dx,z+dz
  if (xx,zz) not in pond and (xx,zz) not in network and not house[zz,xx] and not road[zz,xx]:put(xx,3,zz,rng.choice(['moss_block','stone','coarse_dirt']),'P4.pond.bank')
# A small shore deck; posts reach the bed and do not delete the channel.
b.box((216,3,88),(224,4,92),'oak_planks','P4.pond.deck')
for x,z in [(216,88),(223,88),(216,91),(223,91)]:b.box((x,1,z),(x+1,3,z+1),'oak_log','P4.pond.deck.post')
features=[];extra_lights=[];added_paths=[]
def pathline(points,width=2):
 for (x,z),(u,v) in zip(points,points[1:]):
  for t in np.linspace(0,1,max(abs(u-x),abs(v-z))*2+1):
   xx=round(x+(u-x)*t);zz=round(z+(v-z)*t)
   for dx in range(width):
    if not house[zz,xx+dx] and not field[zz,xx+dx] and not facility[zz,xx+dx]:
     put(xx+dx,3,zz,'dirt_path','P4.path');added_paths.append((xx+dx,zz))
def light(x,y,z,owner):
 put(x,y,z,'glowstone',owner+'.light');put(x,y+1,z,'dark_oak_slab',owner+'.light.cap');extra_lights.append([x,y,z])
def shed(rect,height=5,owner='P4.shed'):
 a,c,u,v=rect
 b.box((a,3,c),(u,4,v),'gravel',owner+'.floor')
 for x,z in [(a,c),(u-1,c),(a,v-1),(u-1,v-1)]:b.box((x,4,z),(x+1,4+height,z+1),'oak_log',owner+'.post')
 for z in range(c-1,v+1):
  for x in range(a-1,u+1):put(x,4+height+(z-c)//4,z,'dark_oak_slab',owner+'.roof')
 light((a+u)//2,4+height-1,(c+v)//2,owner)
 features.append({'type':'open_farm_shelter','bounds':rect,'id':owner})
def logs(a,c,u,v,levels=2,owner='P4.woodpile'):
 for y in range(4,4+levels):
  for z in range(c+(y-4),v):
   for x in range(a,u):put(x,y,z,M('oak_log',axis='x'),owner)
def garden(rect,name):
 a,c,u,v=rect
 for z in range(c,v):
  for x in range(a,u):
   if x in (a,u-1) or z in (c,v-1):put(x,3,z,'dirt_path',name+'.edge')
   elif (x-a)%5==0:water(x,z,name+'.water',cap=True);erase(x,3,z);erase(x,4,z)
   else:
    put(x,2,z,'dirt',name+'.bed');put(x,3,z,'farmland',name+'.soil');put(x,4,z,M(['carrots','potatoes','beetroots'][(z-c)//3%3],age=rng.randint(1,3)),name+'.crop')
 # Water at the same level as soil, sealed by lower soil and perimeter banks.
 for z in range(c+1,v-1):
  for x in range(a+1,u-1):
   if (x-a)%5==0:put(x,2,z,'dirt',name+'.bed');put(x,3,z,'water',name+'.water')
 features.append({'type':'kitchen_garden','bounds':rect,'id':name})
garden((70,117,82,130),'P4.garden.west1');garden((85,117,98,130),'P4.garden.west2');garden((241,153,256,174),'P4.garden.east')
pathline([(71,131),(99,131),(101,131)]);pathline([(249,174),(258,174)])
shed((95,146,106,153),4,'P4.toolshed.west');logs(95,160,105,164,2);pathline([(89,155),(108,155)])
b.box((96,4,148),(103,5,149),'oak_planks','P4.toolshed.workbench');put(104,4,150,'anvil','P4.toolshed.anvil')
shed((73,256,83,264),5,'P4.southbarn');logs(84,266,92,271,3,'P4.south.wood');b.box((73,4,270),(79,6,274),M('hay_block'),'P4.south.hay')
pathline([(66,259),(71,259),(71,276),(82,276),(82,280)])
# Loose orchard clusters, varying height/radius, with a walkable central clearing.
orchard=[]
for x,z in [(180,215),(191,215),(202,214),(217,214),(224,221),(212,224),(200,225),(187,225),(179,223),(76,268),(91,274),(72,112),(87,113)]:
 h=rng.randint(5,8);r=rng.choice([2,3,3,4]);orchard.append({'x':x,'z':z,'height':h,'radius':r})
 for y in range(4,4+h):put(x,y,z,'oak_log','P4.orchard.trunk')
 for xx in range(x-r,x+r+1):
  for zz in range(z-r,z+r+1):
   for yy in range(4+h-3,4+h+2):
    if ((xx-x)/(r+.3))**2+((zz-z)/(r+.3))**2+((yy-(4+h-1))/2.6)**2<1 and not road[zz,xx] and not house[zz,xx]:
     b.put(xx,yy,zz,rng.choice(['oak_leaves','oak_leaves','azalea_leaves']),'P4.orchard.leaves',empty=True)
pathline([(207,207),(207,221),(217,221),(230,225)]);b.box((202,4,220),(205,5,221),'oak_slab','P4.orchard.bench');light(205,4,220,'P4.orchard')
features.append({'id':'P4.orchard','type':'orchard','tree_count':len(orchard),'trees':orchard})
# Poultry yard structure only: no animal entities or functional animal simulation.
for x in range(215,227):
 for z in [241,252]:put(x,4,z,'iron_bars','P4.pen.fence')
for z in range(241,253):
 for x in [215,226]:put(x,4,z,'iron_bars','P4.pen.fence')
for z in [246,247]:erase(215,4,z)
shed((222,242,226,247),3,'P4.coop');b.box((223,4,242),(226,6,243),'oak_planks','P4.coop.back');put(224,4,244,'hay_block','P4.coop.nest')
pathline([(213,247),(214,247)]);features.append({'id':'P4.pen','type':'poultry_yard_without_entities','bounds':[215,241,227,253]})
# Greenhouse service yard: small static tractor, crates, hay, wash counter.
shed((242,213,251,220),4,'P4.farmservice');b.box((243,4,215),(245,6,217),'hay_block','P4.service.hay')
for x,z in [(252,212),(254,213),(253,215)]:put(x,4,z,'oak_planks','P4.service.crates')
for x,z in [(246,222),(250,222),(246,225),(250,225)]:put(x,4,z,'black_concrete','P4.tractor.wheel')
b.box((247,4,222),(250,6,226),'oxidized_copper','P4.tractor.body');put(248,6,222,'dark_oak_stairs','P4.tractor.seat');put(248,7,225,'iron_bars','P4.tractor.exhaust')
pathline([(241,207),(241,224),(256,224),(258,224)]);features.append({'type':'static_tractor','bounds':[246,222,251,226]})
# Pump hut and reed/bamboo groups at the pond and wet corners.
shed((224,85,229,90),3,'P4.pumphouse');put(226,4,87,'oxidized_copper','P4.pump');pathline([(228,91),(228,98)])
for cx,cz in [(199,75),(204,93),(222,70),(10,55),(61,234),(130,258),(309,197),(235,18)]:
 for k in range(rng.randint(3,6)):
  x=cx+rng.randint(-1,1);z=cz+rng.randint(-1,1)
  if road[z,x] or field[z,x] or house[z,x] or 'water' in B.get((x,3,z),'') or B.get((x,3,z),'').split('[')[0] not in ['minecraft:grass_block','minecraft:dirt','minecraft:moss_block']:continue
  h=rng.randint(2,5)
  for y in range(4,4+h):put(x,y,z,M('bamboo',leaves='large' if y>=3+h else 'none'),'P4.reeds')
# Low marker lights only at working places and bridges, never continuous lit edges.
for x,z in [(68,130),(93,155),(71,264),(229,90),(255,225),(214,250)]:
 if not road[z,x] and not house[z,x]:put(x,4,z,'stone_bricks','P4.marker.base');light(x,5,z,'P4.marker')
# Steps down from the bank into dry plots; solid entry pad kept out of waterways.
steps=[]
for f in p['fields']:
 if f['id'] in paddies:continue
 a,c,u,v=f['bounds'];x=a+3;z=c+1
 for zz in [z,z+1]:
  erase(x,3,zz);put(x,2,zz,'dirt','P4.field.entry.pad')
 put(x,2,z,M('stone_brick_stairs',facing='north'),'P4.field.entry.step');steps.append([x,2,z])
# Clay/stone culvert surfaces identify crossings while preserving public road height.
crossings=[]
for x,z in network:
 if road[z,x] and not house[z,x]:put(x,3,z,'stone_bricks','P4.culvert.deck');crossings.append([x,z])
# Guard low branches along paths and preserve passable roads.
for z,x in zip(*np.where(road)):
 for y in (4,5):
  if b.s.owners.get((int(x),y,int(z)),'').startswith('P4.'):erase(int(x),y,int(z))
# Protect newly built garden beds and workyard structures from repair trenches.
for (x,y,z),owner in b.s.owners.items():
 if y>=3 and owner.startswith(('P4.garden','P4.toolshed','P4.south','P4.orchard','P4.coop','P4.pen','P4.farmservice','P4.service','P4.tractor','P4.pump','P4.marker','P4.woodpile')):blocked[z,x]=True
# Join any inherited disconnected canal sections to the actual peripheral component.
water_connect_repairs=[]
for repair in range(12):
 wm=np.zeros_like(road)
 for (x,y,z),st in B.items():
  if y==2 and st.startswith('minecraft:water'):wm[z,x]=True
 labs,n=label(wm)
 if n==1:break
 root=labs[6,6];network={(int(x),int(z)) for z,x in zip(*np.where(labs==root))}
 dist=distance_transform_cdt(labs!=root,metric='taxicab')
 candidates=[(int(dist[z,x]),int(x),int(z)) for z,x in zip(*np.where(wm & (labs!=root) & ~blocked))]
 if not candidates:raise ValueError('Disconnected water without accessible feeder')
 _,x,z=min(candidates);water_connect_repairs.append(connect((x,z),'network_repair_'+str(repair+1)))
else:raise ValueError('Canal repair did not converge')
for f,stat in zip(p['fields'],fieldstats):
 a,c,u,v=f['bounds'];stat['water_cells']=sum('water' in B.get((x,2,z),'') for z in range(c+1,v-1) for x in range(a+1,u-1))
house_changes=[q for q,o in original_owners.items() if o.startswith('R') and B.get(q)!=old.blocks[q]]
assert not house_changes,house_changes[:10]
p.update(version=run,seed=20261029)
p['landscape_revision']={'base_run':'P3_B4','dry_soil_drop':1,'paddy_count':len(paddies),'paddy_ids':sorted(paddies),'paddy_representation':'Vanilla young wheat on wet planting strips; no rice block or mod.','fields':fieldstats,'routes':routes,'features':features,'extra_lights':extra_lights,'field_steps':steps,'pond_cells':len(pond),'culvert_cells':len(crossings),'house_source_blocks_changed':0,'primary_water_components':int(n),'network_repairs':water_connect_repairs}
p['changes'].append('P4: lowered fields, eight shallow flooded paddies, connected irrigation, pond, orchard and rural workyards.')
out=save_run(C,run,p,b,__file__,{'baseline':'P3_B4','house_source_blocks_changed':0,'landscape_revision':'P4'})
for name in ['entries.json','lighting.json','agricultural_facilities.json','roadmask.npy']:
 shutil.copy2(BASE/name,out/name)
dump(out/'landscape_features.json',p['landscape_revision'])
print('P4 revision saved:',out,flush=True)
