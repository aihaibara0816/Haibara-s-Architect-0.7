from pathlib import Path
import sys,json,random,math,heapq,collections,hashlib
import numpy as np
from PIL import Image,ImageDraw
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump
from detail_lab import states
M=states.make
W,D,H=320,288,48
b=Builder((W,H,D),20261029);rng=random.Random(20261029)
# Position, dimensions, floors, type, entrance rotation; this is an authored settlement, not grid jitter.
rows=[(70,104,24,19,3,'finished',2),(104,100,18,22,2,'old',2),(132,83,28,21,3,'finished',2),(171,74,20,18,2,'frame',2),(201,76,24,18,3,'finished',2),(69,146,19,16,1,'old',0),(98,134,22,18,2,'brick',1),(137,119,24,18,4,'finished',2),(178,112,18,21,2,'old',0),(224,117,24,19,3,'finished',3),(63,196,22,17,2,'finished',0),(94,202,19,15,1,'old',0),(126,178,26,20,3,'finished',0),(165,168,23,21,3,'hybrid',0),(201,157,22,17,2,'brick',1),(222,199,27,21,2,'finished',3),(171,211,20,15,1,'old',0),(132,223,22,18,1,'foundation',0)]
rows=[rows[i] for i in [0,1,2,3,5,6,7,9,10,11,12,13,16]]
houses=[];blocked=np.zeros((D,W),bool);entries=[];lamps=[];rooms=[];stairs=[];field_records=[]
for i,(x,z,w,d,n,kind,rot) in enumerate(rows):
 t=dict(id=f'R{i+1:02}',x=x,z=z,w=w,d=d,floors=n,kind=kind,rotation=rot,shape='L' if i in [0,2,9,12,15] else 'rect')
 houses.append(t);blocked[z-3:z+d+3,x-3:x+w+3]=True
# Terrain is low-gradient farmland, each home on a level yard. Ground top 3..5.
ground=np.full((D,W),3,np.int16)
for z in range(D):
 for x in range(W):ground[z,x]=3+int(x<122 and z<172)+int(x<73 and z<121)
for t in houses:
 x,z,w,d=t['x'],t['z'],t['w'],t['d'];g=int(ground[z+d//2,x+w//2]);t['base']=g
 ground[z-4:z+d+4,x-4:x+w+4]=g
for z in range(D):
 for x in range(W):
  g=int(ground[z,x]);b.box((x,0,z),(x+1,g,z+1),'dirt','land.base');b.put(x,g,z,'grass_block','land.surface')
# A loose inhabited envelope; fields occupy the outskirts and enter its indentations.
poly=[(65,93),(125,65),(223,59),(261,110),(256,178),(270,225),(215,250),(170,244),(122,257),(84,232),(46,218),(53,159)]
im=Image.new('1',(W,D));ImageDraw.Draw(im).polygon(poly,fill=1);village=np.array(im,bool)
# Oblique Voronoi-like field parcels, with individual crop rows and 1-2 block banks.
seeds=[(26,32),(81,28),(144,23),(208,27),(277,26),(27,94),(295,98),(18,157),(291,173),(30,259),(91,272),(190,274),(267,264),(308,231)]
ids=np.zeros((D,W),int)
for z in range(D):
 for x in range(W):ids[z,x]=min(range(len(seeds)),key=lambda i:(x-seeds[i][0])**2+(z-seeds[i][1])**2)
for i in range(len(seeds)):
 cells=[];crop=['wheat','carrots','potatoes','beetroots','wheat','fallow'][i%6];orient=i%2
 for z in range(3,D-3):
  for x in range(3,W-3):
   if village[z,x] or ids[z,x]!=i:continue
   g=int(ground[z,x]);edge=any(ids[z+dz,x+dx]!=i for dx,dz in [(2,0),(-2,0),(0,2),(0,-2)])
   if edge:b.put(x,g,z,'dirt_path','field.bank');continue
   row=x if orient==0 else z
   if row%9==0:
    b.put(x,g,z,'water',f'field.{i}.irrigation');b.put(x,g-1,z,'dirt',f'field.{i}.channel_base')
   elif crop=='fallow':b.put(x,g,z,'coarse_dirt',f'field.{i}.fallow')
   else:
    b.put(x,g,z,'farmland',f'field.{i}.soil')
    if row%3!=0 or crop=='wheat':b.put(x,g+1,z,M(crop,age=7 if crop!='beetroots' else 3),f'field.{i}.crop')
   cells.append((x,z))
 field_records.append({'id':f'F{i+1:02}','crop':crop,'cells':len(cells),'rows':'X' if orient==0 else 'Z'})
# Road network is routed round pre-existing plots. Branches and yards join later.
def astar(start,end):
 start,end=tuple(start),tuple(end);pq=[(0,start)];prev={start:None};cost={start:0}
 while pq:
  _,p=heapq.heappop(pq)
  if p==end:break
  x,z=p
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   q=(x+dx,z+dz);xx,zz=q
   if not(2<=xx<W-2 and 2<=zz<D-2) or blocked[zz,xx] and q not in [start,end]:continue
   nc=cost[p]+1+.03*math.sin(xx*.12+zz*.08)
   if nc<cost.get(q,1e9):cost[q]=nc;prev[q]=p;heapq.heappush(pq,(nc+abs(xx-end[0])+abs(zz-end[1]),q))
 assert end in prev,(start,end)
 route=[];q=end
 while q is not None:route.append(q);q=prev[q]
 return route[::-1]
roads=set();road_paths=[]
def road(route,r,material):
 road_paths.append(route)
 for x,z in route:
  for dz in range(-r,r+1):
   for dx in range(-r,r+1):
    xx,zz=x+dx,z+dz
    if not(0<=xx<W and 0<=zz<D) or dx*dx+dz*dz>r*r+1:continue
    g=int(ground[zz,xx]);b.put(xx,g+1,zz,'air','road.clear');b.put(xx,g,zz,material if rng.random()>.03 else 'gravel','road.surface');roads.add((xx,zz))
anchors=[(3,185),(49,182),(92,180),(125,159),(165,155),(205,143),(215,109),(259,101),(316,77)]
for a,c in zip(anchors,anchors[1:]):road(astar(a,c),2,'smooth_stone')
road(astar((125,159),(122,244)),1,'dirt_path');road(astar((165,155),(193,211)),1,'gravel');road(astar((165,155),(165,64)),1,'dirt_path')
for t in houses:
 tid=t['id'];x,z,w,d,rot=t['x'],t['z'],t['w'],t['d'],t['rotation'];N=t['floors'];kind=t['kind'];g=t['base'];LW,LD=(w,d) if rot%2==0 else (d,w)
 def xyz(a,y,c):
  if rot==0:xx,zz=a,c
  elif rot==1:xx,zz=LD-1-c,a
  elif rot==2:xx,zz=LW-1-a,LD-1-c
  else:xx,zz=c,LW-1-a
  return x+xx,y,z+zz
 def put(a,y,c,s,o='body'):
  if o in ['bed','headboard','wardrobe','kitchen','hob','fridge','sofa','table','chair','partition','bath.wall','bath.door','light'] and t['shape']=='L' and a>=LW-6 and c>=LD-6:return
  v=s if s.startswith('minecraft:') else M(s)
  for _ in range(rot):v=states.rotate_state(v)
  b.put(*xyz(a,y,c),v,tid+'.'+o)
 def box(a,c,A,C,y,Y,s,o='body'):
  for aa in range(a,A):
   for cc in range(c,C):
    for yy in range(y,Y):put(aa,yy,cc,s,o)
 def inside(a,c):return not(t['shape']=='L' and a>=LW-6 and c>=LD-6)
 mask={(a,c) for a in range(LW) for c in range(LD) if inside(a,c)}
 edge={(a,c) for a,c in mask if any((a+da,c+dc) not in mask for da,dc in [(1,0),(-1,0),(0,1),(0,-1)])}
 floor=g+1;top=floor+N*6
 colors=[('white_concrete','gray_concrete'),('smooth_sandstone','dark_oak_planks'),('light_gray_concrete','red_terracotta'),('white_concrete','blue_concrete')]
 mat,trim=colors[int(tid[1:])%4]
 if kind=='old':mat='packed_mud' if int(tid[1:])%2 else 'bricks';trim='dark_oak_planks'
 if kind in ['brick','hybrid']:mat='bricks';trim='polished_andesite'
 # Yard with room for tools and a broad, unblocked gate.
 for aa in range(-3,LW+3):
  for cc in range(-5,LD+3):
   px,_,pz=xyz(aa,g,cc)
   for yy in range(g+1,g+3):b.put(px,yy,pz,'air','yard.clear')
   b.put(px,g,pz,'coarse_dirt' if kind in ['old','foundation'] else 'smooth_stone',tid+'.yard')
 if kind=='foundation':
  for aa,cc in mask:
   put(aa,g+1,cc,'gravel','foundation')
   if aa%7==0 or cc%7==0:put(aa,g+1,cc,'polished_andesite','footing')
  for aa in [0,LW//2,LW-1]:
   for cc in [0,LD-1]:box(aa,cc,aa+1,cc+1,g+1,g+3,'polished_andesite','starter');put(aa,g+3,cc,'iron_bars','rebar')
 else:
  for f in range(N+1):
   fy=floor+f*6
   for aa,cc in mask:
    put(aa,fy-1,cc,'oak_planks' if kind=='old' else 'smooth_stone','floor')
    if f and kind not in ['frame','brick']:put(aa,fy-2,cc,'white_concrete','ceiling')
  for f in range(N):
   fy=floor+6*f
   israw=kind in ['frame','brick'] or kind=='hybrid' and f==N-1
   # frame columns/beams intact; infill unfinished by bay, no arbitrary structural holes.
   for aa,cc in edge:
    for yy in range(fy,fy+4):
     if kind=='frame':continue
     if israw and ((aa//6+cc//5+f)%3==0 and yy>fy+1):continue
     wall=mat
     if kind=='hybrid' and f<N-1:wall='white_concrete'
     if kind=='old' and ((aa*13+cc*7+yy*3)%43<3):wall='terracotta'
     put(aa,yy,cc,wall,'facade')
   if israw:
    for aa in range(0,LW,7):
     for cc in [0,LD-1]:box(aa,cc,aa+1,cc+1,fy,fy+5,'polished_andesite','column')
    for aa in [0,LW-1]:
     for cc in range(0,LD,7):box(aa,cc,aa+1,cc+1,fy,fy+5,'polished_andesite','column')
    for aa,cc in edge:put(aa,fy+4,cc,'polished_andesite','beam')
   else:
    # grouped windows, room-based positions; front corner loggia on finished houses.
    for aa in range(3,LW-2,6):
     for cc in [0,LD-1]:
      for ux in range(aa,min(aa+3,LW-1)):
       if not inside(ux,cc):continue
       for yy in range(fy+1,fy+3):put(ux,yy,cc,'gray_stained_glass_pane','window')
       if f>0:put(ux,fy,cc-1 if cc==0 else cc+1,M('smooth_stone_slab',type='top'),'sill')
    for cc in range(3,LD-2,6):
     for aa in [0,LW-1]:
      if not inside(aa,cc):continue
      for zz in range(cc,min(cc+3,LD-1)):
       if inside(aa,zz):
        for yy in range(fy+1,fy+3):put(aa,yy,zz,'glass_pane','window')
    if f>0 and kind=='finished':
     # recessed front loggia, 3 blocks deep with glass doors at the back.
     for aa in range(8,LW-2):
      for cc in range(0,3):
       for yy in range(fy,fy+4):put(aa,yy,cc,'air','balcony.void')
      put(aa,fy,0,'iron_bars','balcony.rail')
      for yy in range(fy,fy+3):put(aa,yy,3,'gray_stained_glass_pane','balcony.glass')
     box(10,3,12,4,fy,fy+3,'air','balcony.door')
    # Interior: entrance corridor, private stair on left, rear bedroom and kitchen/bath.
    for aa in range(7,LW-1):
     if inside(aa,LD//2):
      for yy in range(fy,fy+4):put(aa,yy,LD//2,'white_concrete','partition')
    box(9,LD//2,11,LD//2+1,fy,fy+3,'air','room.door')
    if LW>18:
     for cc in range(LD//2+1,LD-1):
      if inside(LW-6,cc):box(LW-6,cc,LW-5,cc+1,fy,fy+4,'white_concrete','bath.wall')
     box(LW-6,LD//2+2,LW-5,LD//2+4,fy,fy+3,'air','bath.door')
    # beds, wardrobe, living/dining/kitchen change between floors.
    box(8,LD-5,11,LD-2,fy,fy+1,'white_concrete','bed');box(8,LD-5,11,LD-4,fy,fy+1,'oak_planks','headboard')
    box(7,LD-3,8,LD-1,fy,fy+2,'oak_planks','wardrobe')
    if f==0:
     box(LW-4,2,LW-2,5,fy,fy+1,'smooth_quartz','kitchen');put(LW-3,fy+1,2,'iron_trapdoor','hob')
     box(LW-2,LD//2+2,LW-1,LD//2+3,fy,fy+2,'iron_block','fridge')
    for aa in range(8,11):put(aa,fy,5,M('oak_stairs',facing='north'),'sofa')
    box(LW-7,5,LW-5,7,fy,fy+1,M('oak_slab',type='top'),'table')
    put(LW-8,fy,6,M('oak_stairs',facing='east'),'chair')
    for aa,cc in [(4,8),(9,7),(10,LD-4),(LW-3,LD//2+3)]:
     if inside(aa,cc):put(aa,fy+4,cc,'glowstone' if f else 'sea_lantern','light');lamps.append(xyz(aa,fy+4,cc))
    rooms.append({'id':tid+f'.F{f+1}','kind':'home','floor_y':fy,'finished':True})
   # U-stair 2-wide: 3 rises, landing, 3 return rises, 6 block storey.
   box(1,2,6,8,fy-1,fy+6,'air','stair.void')
   for aa in range(1,6):
    for cc in range(2,9):put(aa,fy-1,cc,'smooth_stone','stair.base')
   for step in range(3):
    for aa in [1,2]:put(aa,fy+step,3+step,M('stone_brick_stairs',facing='south'),'stair')
    for aa in [4,5]:put(aa,fy+3+step,5-step,M('stone_brick_stairs',facing='north'),'stair')
   box(1,6,6,8,fy+2,fy+3,'smooth_stone','stair.landing')
   box(4,1,6,3,fy+5,fy+6,'smooth_stone','stair.upper')
   stairs.append({'house':tid,'floor':f+1,'width':2,'rise':6})
  # Rebuild the entire vertical core after all floor plates, preserving actual openings.
  box(1,2,6,8,floor,top+1,'air','stair.final_void')
  for f in range(N):
   fy=floor+6*f
   for step in range(3):
    for aa in [1,2]:put(aa,fy+step,3+step,M('stone_brick_stairs',facing='south'),'stair.final')
    for aa in [4,5]:put(aa,fy+3+step,5-step,M('stone_brick_stairs',facing='north'),'stair.final')
   box(1,6,6,8,fy+2,fy+3,'smooth_stone','stair.mid')
   box(4,1,6,3,fy+5,fy+6,'smooth_stone','stair.exit')
  # Weather roof / terrace; unfinished gets exposed starters, never tiled roof.
  if kind=='old':
   for aa in range(-1,LW+1):
    for cc in range(-1,LD+1):
     yy=top+min(cc+1,LD-cc)//2
     put(aa,yy,cc,'polished_deepslate' if int(tid[1:])%2 else 'red_terracotta','roof.tile')
  elif kind=='finished':
   for aa,cc in edge:put(aa,top,cc,'white_concrete','parapet')
   box(LW-5,LD-5,LW-2,LD-2,top,top+2,'iron_block','tank')
   for aa in range(9,LW-3):put(aa,top+1,LD-2,M('iron_trapdoor',half='top'),'solar')
   box(0,1,7,9,top,top+3,'air','roof.access.clear')
   # Small roof stair shelter leaves front open.
   box(0,1,1,9,top,top+3,mat,'stair.shelter');box(6,1,7,9,top,top+3,mat,'stair.shelter');box(0,8,7,9,top,top+3,mat,'stair.shelter');box(0,1,7,9,top+3,top+4,'smooth_stone','stair.shelter.roof')
  else:
   for aa in [0,LW//2,LW-1]:
    for cc in [0,LD-1]:box(aa,cc,aa+1,cc+1,top,top+3,'iron_bars','rebar')
  # Primary entry always remains clear after furnishing.
  box(7,0,9,1,floor,floor+3,'air','entry');entry=xyz(7,floor,-1)
  entries.append({'house':tid,'xyz':entry,'floor_y':floor})
  for aa in range(6,11):put(aa,floor+3,-1,M('smooth_stone_slab',type='top'),'canopy')
  # Pipes, external condenser and small attachments on maintained houses.
  if kind=='finished':
   for yy in range(floor,top):put(LW,yy,LD-3,'iron_bars','pipe')
   for f in range(N):put(LW,floor+f*6+2,4,'iron_block','aircon');put(LW,floor+f*6+1,4,M('smooth_stone_slab',type='top'),'aircon.bracket')
 # Borrowed video motifs applied to selected finished facades, not every house.
 if kind=='finished':
  for f in range(N):
   fy=floor+6*f
   for aa in range(LW):
    put(aa,fy+4,-1,M('smooth_stone_slab',type='top'),'cornice')
    if int(tid[1:])%3!=0:put(aa,fy+5,0,'red_terracotta','front.trim')
   if f==0 or int(tid[1:])%2==0:
    for aa in range(3,LW-2,6):
     for ux in range(aa,min(aa+3,LW-1)):
      for yy in range(fy+1,fy+3):put(ux,yy,-1,'iron_bars','window.cage')
  if int(tid[1:])%2==0:
   for aa in range(2,LW-2):
    for yy in range(floor,top-2):
     px,py,pz=xyz(aa,yy,LD-1)
     if b.s.blocks.get((px,py,pz)) in [M(mat),M('white_concrete')]:put(aa,yy,LD-1,'polished_andesite','unfinished.rear.render')
  if int(tid[1:])%3==0:box(9,4,14,8,top,top+1,'hay_block','roof.drying')
 # Household yard detail kept away from entry and stair routes.
 # Unequal side courts: a low wall, open gate, lean-to roof and work bench.
 if kind in ['old','finished']:
  for aa in range(-3,LW+3):
   if aa not in range(5,11):put(aa,g+1,-5,'bricks' if kind=='old' else 'smooth_sandstone','court.wall')
  if int(tid[1:])%2==0:
   for aa in range(-3,2):
    for cc in range(LD-4,LD+2):put(aa,g+4,cc,M('dark_oak_slab',type='bottom'),'shed.roof')
   for aa in [-3,1]:
    for cc in [LD-4,LD+1]:box(aa,cc,aa+1,cc+1,g+1,g+4,'oak_log','shed.post')
   box(-2,LD-3,1,LD,g+1,g+2,'oak_planks','shed.workbench')

 if kind in ['frame','brick','foundation','hybrid']:
  box(LW-4,-4,LW-1,-2,g+1,g+3,'bricks','brick.stack');box(LW+1,LD-6,LW+3,LD-1,g+1,g+2,'oak_planks','timber.stack')
  if kind!='foundation':
   for yy in range(g+1,top+1):put(-2,yy,LD-2,'iron_bars','scaffold');put(-2,yy,LD-5,'iron_bars','scaffold')
   for yy in range(g+6,top+1,6):box(-3,LD-6,0,LD-1,yy,yy+1,M('oak_slab',type='bottom'),'scaffold.deck')
 else:
  box(LW-3,-4,LW-1,-2,g+1,g+2,'hay_block','yard.harvest')
 # gates tie a short front path into the nearest public road.
 start=xyz(7,g,-5);sx,_,sz=start
 # clear the buffer only for this approach, other plots remain protected.
 original=blocked.copy();blocked[max(0,z-4):z+d+4,max(0,x-4):x+w+4]=False;blocked[z:z+d,x:x+w]=True
 target=min(roads,key=lambda q:(q[0]-sx)**2+(q[1]-sz)**2)
 route=astar((sx,sz),target);road(route,1,'gravel');blocked[:]=original
# Replace ornamental lawn gaps with working ground and irregular kitchen gardens.
for zz in range(58,250):
 for xx in range(44,266):
  if not village[zz,xx] or blocked[zz,xx] or (xx,zz) in roads:continue
  gg=int(ground[zz,xx]);near=min((max(t['x']-xx,0,xx-t['x']-t['w'])**2+max(t['z']-zz,0,zz-t['z']-t['d'])**2)**.5 for t in houses)
  if near<10:
   b.put(xx,gg,zz,'coarse_dirt' if (xx+2*zz)%13 else 'gravel','court.workground')
  elif ((xx-217)/23)**2+((zz-196)/29)**2<1 or ((xx-218)/24)**2+((zz-81)/16)**2<1:
   if (xx+zz//10)%8==0:b.put(xx,gg,zz,'water','garden.irrigation')
   elif xx%3!=0:b.put(xx,gg,zz,'farmland','garden.soil');b.put(xx,gg+1,zz,M('carrots',age=7),'garden.crop')
# Shade trees at irregular corners, protected against buildings and paths.
for x,z,h,r in [(56,116,8,4),(118,72,10,5),(237,68,9,4),(266,150,12,6),(56,228,11,5),(108,240,8,4),(207,238,10,5),(240,179,9,4),(45,175,10,5),(159,204,8,4),(188,146,8,4)]:
 if not blocked[z,x] and (x,z) not in roads:
  before=set(b.s.blocks);b.tree(x,z,int(ground[z,x])+1,h,r)
  for q in set(b.s.blocks)-before:
   if q[1]>int(ground[q[2],q[0]]) and (q[0],q[2]) in roads:b.s.set(q,'minecraft:air','tree.trim')
# Village shade/sunning yard, one pump shelter, pole lights only at junctions.
for x,z in [(47,181),(123,158),(167,154),(212,142),(261,102)]:
 if (x,z) in roads:continue
 b.lamp(x,z,int(ground[z,x])+1)
# Close irrigation banks wherever a terrain step exposes a side to air/crops.
for (xx,yy,zz),ss in list(b.s.blocks.items()):
 if ss.startswith('minecraft:water'):
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   q=(xx+dx,yy,zz+dz)
   if not(0<=q[0]<W and 0<=q[2]<D):continue
   other=b.s.blocks.get(q,'minecraft:air')
   if states.family(other) in ['air','crop']:b.put(*q,'dirt','irrigation.bank_step')
# Save explicit design / references / same-source layer metadata.
p={'case':'田埂里','route':'original','seed':20261029,'size_xyz':[W,H,D],'coordinates':{'north':'-Z','east':'+X','unit':'block'},'buildings':houses,'fields':field_records,'roads':road_paths,'lighting':'All occupied rooms lit; unfinished storeys unlit','video':{'url':'https://www.bilibili.com/video/BV1TpGw6JEHQ/','access':'Browser playback inspected: preview around 00:23, wall openings around 06:27 and roof details around 12:29; not watched in full','source':'Bad_Door, user-provided Bilibili video; original interpretation' },'construction':'6 finished, 4 old, 3 construction-stage buildings','interior_limitations':'Decorative beds and furniture; no functional bed/block-entity inventory claims'}
dump(C/'input/design.json',p);dump(C/'input/entries.json',entries);dump(C/'input/lamps.json',lamps);dump(C/'input/stairs.json',stairs);dump(C/'input/rooms.json',rooms)
out=save_run(C,'V4',p,b,__file__,{'game_status':'pending','building_count':len(houses),'fields':len(field_records),'crop_preview':'approximate boxes, actual vanilla crops in NBT'})
np.save(out/'ground.npy',ground)
print('DONE',len(b.s.blocks),len(rooms),flush=True)
