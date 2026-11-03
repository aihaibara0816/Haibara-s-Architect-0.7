"""Branch-first subtropical trees, planted soil patches and restrained paving variation.
Original MC recipes informed by reference silhouettes; not botanical simulation.
"""
import math,hashlib,random,collections
from detail_lab import states as S
def noise(*a):return int(hashlib.sha256('/'.join(map(str,a)).encode()).hexdigest()[:12],16)/16**12

def build(city,records,roads,lanes,street,plaza,inside,seed):
 W,H,D=city.w,84,city.d
 # Preserve the full two-block pedestrian strip, all entry routes and every building.
 keep=roads|lanes|{(x,z)for x,z in street if z in[122,123,141,142]or x in[207,208,226,227]}
 for r in records:
  ex,ey,ez=r['entry']
  keep|={(ex+dx,ez+dz)for dx in range(-2,3)for dz in range(-2,3)}
 protected2=set(inside)
 for x,z in inside:
  protected2.update((x+dx,z+dz)for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)])
 def surface_ok(x,z):return 1<x<W-2 and 1<z<D-2 and (x,z)not in keep and (x,z)not in protected2 and (x,3,z)not in city.blocks
 planting=set();patches=[]
 def patch(id,cx,cz,rx,rz):
  cells=[]
  phase=noise(seed,id)*6.28
  for x in range(max(2,math.floor(cx-rx-2)),min(W-2,math.ceil(cx+rx+2))):
   for z in range(max(2,math.floor(cz-rz-2)),min(D-2,math.ceil(cz+rz+2))):
    th=math.atan2((z-cz)/rz,(x-cx)/rx);bound=1+.13*math.sin(th*3+phase)+.07*math.sin(th*5-phase)
    if ((x-cx)/rx)**2+((z-cz)/rz)**2<bound and surface_ok(x,z):cells.append((x,z))
  if len(cells)<7:return
  planting.update(cells);patches.append({'id':id,'center':[cx,cz],'radii':[rx,rz],'cells':len(cells)})
 # Plaza has distinct islands, clear cross paths and a generous visible root bed.
 for a in [('banyan_bed',191,104,8,6),('plaza_north',195,91,8,3),('plaza_east',203,109,3,7),('plaza_west',176,114,4,6),('plaza_south',195,119,6,2.3)]:patch(*a)
 # Linear street gardens leave two clear blocks beside the arcades.
 for i,(x,z,l) in enumerate([(8,124,6),(29,124,9),(63,124,7),(104,124,8),(145,124,7),(35,140,7),(73,140,8),(123,140,7),(170,140,9),(250,123,8),(289,123,9),(328,122,7),(248,144,8),(302,143,7)]):patch('street_'+str(i),x,z,l,1.5)
 # Several real pocket lawns, not a green outline around each building.
 for i,a in enumerate([(7,35,5,23),(7,87,5,21),(112,26,5,13),(160,28,5,17),(80,76,9,7),(165,47,9,6),(203,47,4,28),(231,38,5,24),(306,43,5,23),(341,72,10,6),(249,118,15,4),(329,118,14,4),(9,213,6,24),(27,229,6,12),(83,211,4,26),(109,229,3,14),(163,226,3,14),(215,244,17,3),(256,236,22,5),(302,198,5,14),(348,211,4,25),(348,45,4,27)]):patch('pocket_'+str(i),*a)
 # Public paving: sparse coherent repair areas, with tiny local grain. Never random holes.
 paving=collections.Counter()
 for (x,y,z),o in list(city.owners.items()):
  if y!=2 or any(v in o for v in ['road','crosswalk']):continue
  if (x,z)in inside or (x,z)in planting:continue
  if not any(o.endswith('.'+v)for v in ['paving','lane','plaza']):continue
  field=noise(seed,x//4,z//3,'paving');grain=noise(seed,x,z,'grain')
  if (x,z)in plaza:mat='stone_bricks'if field<.60 else'polished_andesite'if field<.83 else'smooth_stone'
  elif (x,z)in lanes:mat='stone_bricks'if field<.57 else'andesite'if field<.80 else'polished_andesite'
  else:mat='smooth_stone'if field<.63 else'polished_andesite'if field<.87 else'stone_bricks'
  if mat=='stone_bricks'and grain<.09:mat='cracked_stone_bricks'
  city.p(x,2,z,mat,'paving.varied');paving[mat]+=1
 for x,z in planting:
  mat='moss_block'if noise(seed,x//3,z//3,'soil')<.16 else'grass_block'
  city.p(x,2,z,mat,'landscape.soil')
 # Only boundary pieces receive a curb; a low flush apron keeps the patch from looking boxed.
 edges={q for q in planting if any((q[0]+dx,q[1]+dz)not in planting for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)])}
 for x,z in edges:
  if (x,z)in plaza and noise(seed,x//3,z//3,'curb')<.65:city.p(x,2,z,'moss_block','landscape.edge')
 building_solids={q for q in city.blocks if q[1]>2 and not any(v in city.owners.get(q,'') for v in ['tree','landscape'])}
 def blocked(x,y,z):
  return any((x+dx,y+dy,z+dz)in building_solids for dx,dy,dz in [(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
 trees=[]
 def tree(id,x,z,r,h,kind='broadleaf'):
  # Roots stay within planting. A branch can reach over a street only above headroom.
  if (x,z)not in planting or (x,3,z)in city.blocks:return False
  rr=random.Random(f'{seed}/{id}/branch-first-v2');wood={};leaf={};segments=[];clusters=[]
  def line(a,b,rad0=0,rad1=0):
   steps=max(1,math.ceil(max(abs(a[i]-b[i])for i in range(3))*2.4));prev=None
   axis='xyz'[max(range(3),key=lambda i:abs(a[i]-b[i]))]
   for j in range(steps+1):
    t=j/steps;pt=tuple(round(a[i]+(b[i]-a[i])*t)for i in range(3));rad=rad0+(rad1-rad0)*t
    if prev is not None and sum(abs(pt[k]-prev[k])for k in range(3))>1:
     bridge=list(prev)
     for k in sorted(range(3),key=lambda k:abs(b[k]-a[k]),reverse=True):
      bridge[k]=pt[k];q=tuple(bridge)
      if not blocked(*q)and q not in city.blocks and(q[1]>=6 or(q[0],q[2])in planting):wood[q]=S.make('oak_wood'if kind!='palm'else'jungle_wood',axis=axis)
    for dx in range(-math.ceil(rad),math.ceil(rad)+1):
     for dy in range(-math.ceil(rad),math.ceil(rad)+1):
      for dz in range(-math.ceil(rad),math.ceil(rad)+1):
       if dx*dx+dy*dy+dz*dz>(rad+.35)**2:continue
       q=(pt[0]+dx,pt[1]+dy,pt[2]+dz);X,Y,Z=q
       if not(1<X<W-2 and 3<=Y<H-1 and 1<Z<D-2)or blocked(*q):continue
       if Y<6 and (X,Z)not in planting:continue
       if q in city.blocks and not any(v in city.owners.get(q,'')for v in['tree','landscape']):continue
       wood[q]=S.make('oak_wood'if kind!='palm'else'jungle_wood',axis=axis)
    prev=pt
   segments.append({'start':a,'end':b,'radius':[rad0,rad1]})
  def clump(cx,cy,cz,rx,ry,rz):
   cand=[]
   phase=rr.random()*6.28
   for X in range(math.floor(cx-rx-1),math.ceil(cx+rx+1)):
    for Z in range(math.floor(cz-rz-1),math.ceil(cz+rz+1)):
     for Y in range(math.floor(cy-ry-1),math.ceil(cy+ry+1)):
      v=((X-cx)/rx)**2+((Y-cy)/ry)**2+((Z-cz)/rz)**2
      wobble=.14*math.sin(X*1.6+Z*.9+phase)+.09*math.cos(Y*1.7-Z+phase)
      if v>1+wobble or v>.58 and noise(id,X,Y,Z,'holes')<.13:continue
      if not(1<X<W-2 and 6<Y<H-1 and 1<Z<D-2):continue
      cand.append((X,Y,Z))
   # Reject obstructed clumps whole; never shave a tree into a flat wall against a house.
   if not cand or sum(blocked(*q)or q in city.blocks for q in cand)>.08*len(cand):return False
   use='azalea_leaves'if rr.random()<.22 else'oak_leaves'
   for q in cand:
    if not blocked(*q)and q not in city.blocks:leaf[q]=S.make(use,persistent=True)
   clusters.append({'center':[cx,cy,cz],'radii':[rx,ry,rz]});return True
  leanx=rr.choice([-1,1])*rr.uniform(.7,1.6);leanz=rr.uniform(-1.1,1.1)
  if kind=='palm':
   base=[x,3,z];elbow=[x+leanx,3+h*.52,z+leanz*.4];tip=[x+leanx*2,3+h,z+leanz]
   line(base,elbow);line(elbow,tip)
   angle=rr.random()*6.28
   for i in range(7):
    th=angle+i*6.28/7;length=rr.uniform(4.1,6.0)
    for j in range(6):
     t=j/5;cx=tip[0]+math.cos(th)*length*t;cz=tip[2]+math.sin(th)*length*t;cy=tip[1]+math.sin(t*math.pi)*1.6-t*2.2
     for dx,dz in [(0,0),(1,0)]if 1<j<4 else[(0,0)]:
      q=(round(cx)+dx,round(cy),round(cz)+dz)
      if not blocked(*q)and q not in city.blocks:leaf[q]=S.make('jungle_leaves',persistent=True)
   clusters.append({'palm_fronds':7,'center':tip})
  else:
   big=kind=='banyan';base=[x,3,z];fork=[x+leanx,3+h*.40,z+leanz];head=[x+leanx*1.6,3+h*.74,z+leanz*2]
   line(base,fork,1.3 if big else .45,.8 if big else 0);line(fork,head,.6 if big else 0,0)
   # Unequal flaring roots tie the trunk to soil, not to a broad circular platter.
   for i in range(5 if big else 3):
    th=rr.random()*6.28;d=rr.uniform(2.2,4.5)if big else rr.uniform(1.1,2.1)
    line([x,5,z],[x+math.cos(th)*d,3,z+math.sin(th)*d],.55 if big else 0,0)
   angle=rr.random()*6.28;branches=8 if big else 5
   for i in range(branches):
    th=angle+i*6.28/branches+rr.uniform(-.21,.21);reach=r*rr.uniform(.50,.88)
    a=[fork[0],fork[1]+rr.uniform(-1.2,2),fork[2]];b=[x+math.cos(th)*reach*.55,3+h*rr.uniform(.56,.70),z+math.sin(th)*reach*.55]
    c=[x+math.cos(th)*reach,3+h*rr.uniform(.70,.98),z+math.sin(th)*reach]
    if blocked(*map(round,b))or blocked(*map(round,c)):continue
    line(a,b,.55 if big else 0,0);line(b,c)
    radi=rr.uniform(2.6,3.8)if big else rr.uniform(1.9,2.8)
    clump(*c,radi,rr.uniform(2.2,3.4),radi*rr.uniform(.8,1.1))
    # Secondary forks create visible branch structure below individual leaf masses.
    for j in [-1,1]:
     ang=th+j*rr.uniform(.4,.8);d=rr.uniform(2.5,4.3)if big else rr.uniform(1.5,2.5)
     e=[b[0]+math.cos(ang)*d,b[1]+rr.uniform(2.2,5.3),b[2]+math.sin(ang)*d]
     if blocked(*map(round,e)):continue
     line(b,e);clump(*e,radi*.80,radi*.76,radi*.90)
   clump(head[0],head[1]+2,head[2],r*.29,3.0,r*.31)
   if big:
    # Two aerial roots begin on real branches and reach soil; unequal placement and thickness.
    for dx,dz in [(-5,-1),(4,3)]:
     qx,qz=x+dx,z+dz
     if (qx,qz)not in planting:continue
     parent=[qx,11+rr.randint(0,3),qz];line(fork,parent,.4,0);line(parent,[qx,3,qz],0,0)
  if len(wood)<8 or len(leaf)<(15 if kind=='palm'else 80):return False
  for q,st in wood.items():city.p(*q,st,'tree.'+id+'.wood')
  for q,st in leaf.items():
   if q not in wood:city.p(*q,st,'tree.'+id+'.leaves')
  trees.append(dict(id=id,x=x,z=z,r=r,h=h,kind=kind,branch_segments=len(segments),leaf_clusters=len(clusters),wood_blocks=len(wood),leaf_blocks=len(leaf),branches=segments,clusters=clusters));return True
 # Ficus, camphor-like shade crowns and a few palm accents are distinct silhouettes.
 tree('plaza_banyan',191,104,12,22,'banyan')
 requested=[(8,112,6,15),(29,124,6,18),(63,124,5,18),(104,124,6,20),(145,124,5,19),(73,140,5,20),(123,140,6,19),(170,140,5,20),(250,123,5,14),(289,123,5,18),(328,122,5,16),(7,36,6,15),(112,26,5,14),(160,28,5,15),(80,76,5,12),(165,47,5,12),(9,213,7,17),(27,229,5,14),(83,211,5,14),(256,236,6,15),(348,211,5,16),(348,45,5,15)]
 for i,(x,z,r,h)in enumerate(requested):
  candidates=sorted([(a,c)for a,c in planting if abs(a-x)+abs(c-z)<5],key=lambda q:abs(q[0]-x)+abs(q[1]-z))
  for a,c in candidates:
   if tree('shade_'+str(i),a,c,r,h):break
 for i,(x,z)in enumerate([(204,108),(196,91),(329,118),(248,144)]):
  choices=sorted([(a,c)for a,c in planting if abs(a-x)+abs(c-z)<4],key=lambda q:abs(q[0]-x)+abs(q[1]-z))
  for a,c in choices:
   if tree('palm_'+str(i),a,c,5,12+i%2,'palm'):break
 plants=collections.Counter()
 for x,z in sorted(planting):
  if (x,3,z)in city.blocks:continue
  # Cover is grouped by 4×4 patches, with space to read the planted soil and the root flare.
  near=any((x-t['x'])**2+(z-t['z'])**2<9 for t in trees)
  field=noise(seed,x//4,z//4,'understorey');u=noise(seed,x,z,'plant')
  if near:
   if u<.38:city.p(x,2,z,'rooted_dirt','landscape.rootsoil')
   if u>.12:continue
  if field<.22 and u<.54:
   st='azalea_leaves'if field<.17 else'flowering_azalea_leaves';city.p(x,3,z,st,'landscape.shrub',persistent=True);plants[st]+=1
   if u<.08 and (x,4,z)not in city.blocks:city.p(x,4,z,'azalea_leaves','landscape.shrub',persistent=True)
  elif u<.18:city.p(x,3,z,'fern','landscape.fern');plants['fern']+=1
  elif u<.31:city.p(x,3,z,'short_grass','landscape.grass');plants['short_grass']+=1
  elif u<.34:
   flower=['blue_orchid','azure_bluet','allium'][int(noise(seed,x//6,z//6,'flower')*3)];city.p(x,3,z,flower,'landscape.flower');plants[flower]+=1
 # Local light near the seating, distinct from tall roadway lamps.
 for x,z in [(182,113),(201,111),(191,92)]:
  if (x,z)in planting and all((x,y,z)not in city.blocks for y in [3,4]):
   city.p(x,3,z,'diorite_wall','landscape.light_base');city.p(x,4,z,'lantern','landscape.light')
 return trees,dict(algorithm='branch-first-v2 / coherent-planted-patches-v1',seed=seed,planting_cells=sorted(planting),planted_ground_cells=len(planting),patches=patches,understorey_counts=dict(plants),paving_counts=dict(paving),tree_species_intent={'banyan':'榕树意象：粗干、分枝、气根','broadleaf':'榕科与樟树式阔叶树冠意象','palm':'少量棕榈意象'},primary_routes_preserved=True)
