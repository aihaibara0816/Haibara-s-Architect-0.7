"""P3 plan -> actual 18-house build. Local case adapter, deterministic seed namespaces.
Preserves approved house footprints and road routes; details and farm subdivisions vary.
"""
from pathlib import Path
import sys,json,math,random,hashlib,gzip,collections
import numpy as np
from PIL import Image,ImageDraw
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
from detail_lab import states
M=states.make
RUN=sys.argv[1] if len(sys.argv)>1 else 'P3_B1'
SEED=2026102918;W,D,H=320,288,48;G=3
def rng(key):return random.Random(int.from_bytes(hashlib.sha256(f'{SEED}:{key}'.encode()).digest()[:8],'big'))
spec=json.loads((C/'input/layout_P3.json').read_text());sp=spec['spatial_spec'];houses=sp['houses']
b=Builder((W,H,D),SEED);B=b.s.blocks
print('terrain',flush=True)
b.box((0,0,0),(W,G,D),'dirt','land.base')
b.box((0,G,0),(W,G+1,D),'grass_block','land.surface')
roadmask=np.zeros((D,W),bool);reserved=np.zeros_like(roadmask);fieldmask=np.zeros_like(roadmask)
road_layers=[]
for r in sp['roads']:
 zz,xx=np.mgrid[0:D,0:W];xx=xx+.5;zz=zz+.5;mask=np.zeros((D,W),bool)
 path=r['path'];segments=list(zip(path,path[1:])) or [(path[0],path[0])]
 for (ax,az),(bx,bz) in segments:
  dx,dz=bx-ax,bz-az;length=dx*dx+dz*dz
  t=np.clip(((xx-ax)*dx+(zz-az)*dz)/max(length,1e-10),0,1)
  mask|=(xx-ax-t*dx)**2+(zz-az-t*dz)**2<=(r['width']/2)**2
 roadmask|=mask;road_layers.append((r,mask))
for h in houses:
 x,z,w,d=h['x'],h['z'],h['w'],h['d'];reserved[z-2:z+d+2,x-2:x+w+2]=True
for f in sp['fields']:
 a,c,u,v=f['bounds'];fieldmask[c:v,a:u]=True
for f in sp['greenhouses']+sp['agricultural_auxiliaries']:
 a,c,u,v=f['bounds'];reserved[c-2:v+2,a-2:u+2]=True

# Orthogonal agricultural parcels with uneven subdivision, short setbacks and grouped ages.
farm_records=[];water=set();crop_records=collections.Counter()
def plant_plot(fid,rect,crop,vertical,rr,stage=None):
 a,c,u,v=rect
 if u-a<5 or v-c<5:return
 # A short service notch changes the outer outline without meandering row geometry.
 notch=rr.choice([0,0,2,3]);notch_len=rr.randint(3,max(3,min(9,(v-c)//3)))
 stage=stage if stage is not None else rr.choice([2,4,5,7,7])
 maxage=3 if crop=='beetroots' else 7
 baseage=min(maxage,round(stage*maxage/7))
 start,end=(a+1,u-1) if vertical else (c+1,v-1)
 irrig=list(range(start+4,end,9))
 if not irrig:irrig=[(start+end)//2]
 if end-1-irrig[-1]>4:irrig.append(end-4)
 harvest=rr.random()<.23 and crop!='fallow';cut=rr.uniform(.10,.26)
 for z in range(c,v):
  for x in range(a,u):
   edge=x in (a,u-1) or z in (c,v-1)
   omitted=notch and x<a+notch and z<c+notch_len
   if omitted:
    b.put(x,G,z,'coarse_dirt',fid+'.loading_notch');continue
   if edge:b.put(x,G,z,'dirt_path',fid+'.bank');continue
   row=x if vertical else z;along=z-c if vertical else x-a;length=v-c if vertical else u-a
   if crop!='fallow' and row in irrig:
    b.put(x,G,z,'water',fid+'.water');water.add((x,G,z));continue
   if crop=='fallow':
    mat='coarse_dirt' if ((x-a)//4+(z-c)//6)%4 else 'dirt'
    b.put(x,G,z,mat,fid+'.resting');continue
   b.put(x,G,z,'farmland',fid+'.soil')
   if harvest and along<length*cut:continue
   # Cluster-level growth differences plus sparse natural gaps, not per-block confetti.
   patch=rng(f'{fid}:{(x-a)//8}:{(z-c)//9}').choice([-1,0,0,0,1])
   age=max(0,min(maxage,baseage+patch))
   if rr.random()<.028:continue
   b.put(x,G+1,z,M(crop,age=age),fid+'.crop');crop_records[crop]+=1
 farm_records.append(dict(id=fid,bounds=rect,crop=crop,rows='N' if vertical else 'E',base_age=baseage,harvest_strip=harvest,notch=notch))
for f in sp['fields']:
 if f['crop'] in ['facility','nursery']:continue
 rr=rng(f['id']);a,c,u,v=f['bounds'];rects=[[a,c,u,v]]
 target=rr.randint(2,4) if (u-a)*(v-c)>1800 else rr.choice([1,2])
 while len(rects)<target:
  ri=max(range(len(rects)),key=lambda i:(rects[i][2]-rects[i][0])*(rects[i][3]-rects[i][1]))
  aa,cc,uu,vv=rects.pop(ri)
  if uu-aa>vv-cc:
   cut=aa+round((uu-aa)*rr.uniform(.35,.65));rects.extend([[aa,cc,cut,vv],[cut,cc,uu,vv]])
  else:
   cut=cc+round((vv-cc)*rr.uniform(.35,.65));rects.extend([[aa,cc,uu,cut],[aa,cut,uu,vv]])
 for j,rect in enumerate(rects):
  if f['crop']=='wheat':crop=rr.choice(['wheat','wheat','wheat','potatoes'])
  elif f['crop']=='fallow':crop='fallow' if j==0 else rr.choice(['wheat','carrots'])
  else:crop=rr.choice(['carrots','potatoes','beetroots','carrots'])
  plant_plot(f'{f["id"]}.{j+1}',rect,crop,rr.random()<(.8 if f['rows']=='N' else .2),rr)

# Irrigation channels are recessed at constant elevation and bounded by soil.
for ci,path in enumerate(sp['channels']):
 im=Image.new('1',(W,D));ImageDraw.Draw(im).line(path,fill=1,width=1)
 for z,x in zip(*np.where(np.array(im))):
  x,z=int(x),int(z)
  if not roadmask[z,x]:b.put(x,G,z,'water',f'channel.{ci}');water.add((x,G,z))

print('18 houses from source NBT',flush=True)
sources={};metas={};source_hashes={}
for label in ['V4','archive']:
 p=C/'input'/label
 sources[label]=load_build(p/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000)).blocks
 metas[label]={h['id']:h for h in json.loads((p/'params.json').read_text())['buildings']}
 source_hashes[label]=hashlib.sha256((p/'building.nbt').read_bytes()).hexdigest()
ownjson=json.loads(gzip.decompress((C/'input/V4/owners.json.gz').read_bytes()))
owners={tuple(q[:3]):ownjson['owner_names'][q[3]] for q in ownjson['xyz_owner']}
def rotate(x,z,w,d,k):
 for _ in range(k):x,z,w,d=d-1-z,x,d,w
 return x,z
def local(h,a,y,c):
 lw,ld=(h['d'],h['w']) if h['rotation']%2 else (h['w'],h['d'])
 xx,zz=rotate(a,c,lw,ld,h['rotation']);return h['x']+xx,y,h['z']+zz
def hp(h,a,y,c,mat,owner):
 st=M(mat) if not mat.startswith('minecraft:') else mat
 for _ in range(h['rotation']):st=states.rotate_state(st)
 b.put(*local(h,a,y,c),st,h['id']+'.'+owner)
copy_records=[];entries=[];room_lights=[]
for h in houses:
 tid=h['id'];src=sources[h['source_set']];old=metas[h['source_set']][h['source_id']];k=h['rotation_delta'];rr=rng(tid)
 sx,sz=old['x'],old['z'];w,d=old['w'],old['d'];g=h['base'];count=0
 # Small plinth only: no inherited wide fenced court.
 for z in range(h['z'],h['z']+h['d']):
  for x in range(h['x'],h['x']+h['w']):
   for y in range(G,g+1):b.put(x,y,z,'smooth_stone',tid+'.plinth')
 for xx in range(-1,w+1):
  for zz in range(-1,d+1):
   for yy in range(old['base'],H):
    q=(sx+xx,yy,sz+zz);st=src.get(q)
    if st is None:continue
    if yy==old['base'] and not(0<=xx<w and 0<=zz<d):continue
    own=owners.get(q,'') if h['source_set']=='V4' else tid+'.archived'
    if h['source_set']=='V4' and (not own.startswith(old['id']+'.') or any(t in own for t in ['yard','court.','shed.','brick.stack','timber.stack'])):continue
    rx,rz=rotate(xx,zz,w,d,k);nx,nz=h['x']+rx,h['z']+rz;ny=yy-old['base']+g
    for _ in range(k):st=states.rotate_state(st)
    # R18 becomes a warm rendered farmhouse with muted teal frames and varied roof use.
    if tid=='R18':
     name,props=parse_state(st)
     if name=='minecraft:white_concrete':st=M('smooth_sandstone')
     elif name=='minecraft:red_terracotta':st=M('oxidized_copper')
     elif 'glass_pane' in name:st=M('light_blue_stained_glass_pane',**props)
     if '.roof.drying' in own:continue
    b.put(nx,ny,nz,st,tid+'.'+(own.split('.',1)[-1] if '.' in own else 'source'));count+=1
 lw,ld=(h['d'],h['w']) if h['rotation']%2 else (h['w'],h['d'])
 # Reproducible house-level glazing variation; whole window bay shares one tint.
 for q,st in list(B.items()):
  if not b.s.owners[q].startswith(tid+'.') or 'glass_pane' not in st:continue
  name,p=parse_state(st);bay=(q[0]//6,q[1]//6,q[2]//6)
  if rng(f'{tid}:glazing:{bay}').random()<.16: b.put(*q,M('gray_stained_glass_pane' if tid!='R18' else 'light_blue_stained_glass_pane',**p),b.s.owners[q])
 # Living rooms, stairs, bedrooms and washrooms all retain working lights.
 for f in range(h['floors']):
  if h['kind'] in ['frame','brick'] or h['kind']=='hybrid' and f==h['floors']-1:continue
  fy=g+1+6*f;lamps=[]
  for role,aa,cc in [('stairs',4,8),('living',9,7),('bedroom',10,ld-4),('wash',lw-3,ld//2+3)]:
   if h['shape']=='L' and aa>=lw-6 and cc>=ld-6:continue
   q=local(h,aa,fy+4,cc)
   if local(h,aa,fy+3,cc) in B and states.family(B[local(h,aa,fy+3,cc)])=='cube':continue
   # All full lamps are flush with the lower ceiling layer, upper floor remains above.
   mat='sea_lantern' if role in ['wash','stairs'] or f==0 and rr.random()<.38 else 'glowstone'
   hp(h,aa,fy+4,cc,mat,'lighting.'+role);lamps.append(dict(role=role,xyz=q,material=mat))
  room_lights.append(dict(house=tid,floor=f+1,lamps=lamps))
 # Short threshold and canopy light; stairs bridge the single-block raised plinth.
 ex,ez=[math.floor(v) for v in h['entry']];entries.append(dict(id=tid,x=ex,z=ez,floor=g+1,front=h['front']))
 for aa in [7,8]:
  for cc in [-2,-1,0]:
   for yy in range(g+1,g+4):hp(h,aa,yy,cc,'air','entrance.clear')
  hp(h,aa,G,-1,'smooth_stone','threshold')
  if g>G:hp(h,aa,G+1,-1,M('stone_brick_stairs',facing='south'),'threshold.step')
 hp(h,7,g+4,-1,'sea_lantern' if h['kind']=='finished' else 'glowstone','entrance.lamp')
 # Tiny supported attachments in distinct positions, leaving the access path free.
 if h['kind'] in ['finished','old']:
  for f in range(1,h['floors']):
   if rr.random()<.65:
    fy=g+1+6*f;start=rr.randint(12,max(12,lw-6));length=rr.randint(2,4)
    for aa in range(start,min(lw-2,start+length)):
     hp(h,aa,fy-1,1,'smooth_stone','planter.bearing');hp(h,aa,fy,1,'terracotta','planter');hp(h,aa,fy+1,1,'oak_leaves','planter.leaves')
  # Unequal short timber or teal shade panels, only on selected rear roof terraces.
  if h['kind']=='finished' and (tid in ['R03','R08','R14','R18']):
   top=g+1+h['floors']*6;aa=max(9,lw-10);cc=max(9,ld-8)
   for a0 in [aa,aa+5]:
    for c0 in [cc,cc+4]:
     for y in range(top,top+3):hp(h,a0,y,c0,'iron_bars','roof.shade.post')
   for a0 in range(aa,aa+6):
    for c0 in range(cc,cc+5):hp(h,a0,top+3,c0,M('dark_oak_slab',type='top'),'roof.shade')
 else:
  # Retain load-bearing frame; stacks and scaffold tell distinct construction stages.
  top=g+1+h['floors']*6
  for aa in [lw-1]:
   for cc in range(3,min(ld-2,8)):
    hp(h,aa,g+1,cc,'bricks','building.materials')
  for cc in [ld-2,ld-6]:
   for yy in range(g+1,top):hp(h,-1,yy,cc,'iron_bars','scaffold')
  for yy in range(g+5,top,6):
   for cc in range(ld-6,ld-1):hp(h,-1,yy,cc,M('oak_slab',type='top'),'scaffold.deck')
 copy_records.append(dict(id=tid,source=h['source_set'],source_id=h['source_id'],rotation=k,copied_blocks=count))
del sources,owners,ownjson

print('roads and agriculture',flush=True)
# Road surfaces always override field margins, never approved house bodies.
for r,mask in road_layers:
 rr=rng(r['id']);base={'main':'smooth_stone','lane':'gravel','farm':'dirt_path','service':'smooth_stone','access':'smooth_stone'}[r['kind']]
 for z,x in zip(*np.where(mask)):
  x,z=int(x),int(z)
  b.put(x,G,z,base,'road.'+r['id'])
  # Preserve the raised threshold steps and overhead entry canopies.
  for y in [G+1,G+2]:
   own=b.s.owners.get((x,y,z),'')
   if not own.startswith('R'):b.put(x,y,z,'air','road.clear')
# Loosely worn working ground around homes, not entire rectangular yards.
for h in houses:
 rr=rng(h['id']+':ground');x,z,w,d=h['x'],h['z'],h['w'],h['d']
 for zz in range(z-4,z+d+4):
  for xx in range(x-4,x+w+4):
   if fieldmask[zz,xx] or roadmask[zz,xx] or (x<=xx<x+w and z<=zz<z+d):continue
   dist=max(x-xx,0,xx-x-w+1)+max(z-zz,0,zz-z-d+1)
   if dist<=rr.choice([1,2,2,3]) and B.get((xx,G,zz))==M('grass_block'):
    b.put(xx,G,zz,'coarse_dirt' if rr.random()<.8 else 'gravel',h['id']+'.workground')

facilities=[]
for gh in sp['greenhouses']:
 tid=gh['id'];a,c,u,v=gh['bounds'];rr=rng(tid);mid=(a+u-1)//2
 if gh['kind']=='film':
  # Curved section in block steps; sides roll up leaving one-block ventilation strips.
  for x in range(a,u):
   t=(x-(a+u-1)/2)/((u-a)/2);roof=G+2+round(3*math.sqrt(max(0,1-t*t)))
   for z in range(c,v):
    rib=(z-c)%5==0 or z==v-1
    b.put(x,roof,z,'iron_block' if rib else 'white_stained_glass',tid+'.roof')
    if x in [a,u-1] and rib:
     for y in range(G+1,roof):b.put(x,y,z,'iron_bars',tid+'.post')
  for z in range(c+1,v-1):
   for x in range(a+1,u-1):
    if x==mid:b.put(x,G,z,'dirt_path',tid+'.aisle');continue
    if x in [a+1,u-2]:b.put(x,G,z,'water',tid+'.irrigation');water.add((x,G,z));continue
    b.put(x,G,z,'farmland',tid+'.soil');b.put(x,G+1,z,M('carrots' if tid in ['G01','G03'] else 'potatoes',age=rr.choice([2,3,4,5])),tid+'.crop')
  for y in [G+1,G+2,G+3]:b.put(mid,y,v-1,'air',tid+'.door')
 else:
  for x in range(a,u):
   for z in range(c,v):
    b.put(x,G,z,'coarse_dirt',tid+'.base')
    b.put(x,G+5,z,M('dark_oak_trapdoor',half='top'),tid+'.shade_mesh')
    if x in [a,u-1] and (z-c)%6==0 or z in [c,v-1] and (x-a)%7==0:
     for y in range(G+1,G+5):b.put(x,y,z,'iron_bars',tid+'.frame')
    if a+2<=x<u-2 and c+2<=z<v-2 and (x-a)%7 not in [0,1]:
     if (z-c-4)%8==0:b.put(x,G+1,z,'water',tid+'.irrigation');water.add((x,G+1,z));b.put(x,G,z,'dirt',tid+'.tray.base')
     else:b.put(x,G+1,z,'farmland',tid+'.tray');b.put(x,G+2,z,M('beetroots',age=rr.choice([0,1,2])),tid+'.seedlings')
  # Enclose raised trays; walking lanes stay at ground height.
  for z in range(c+1,v):
   for x in range(a+1,u):
    if (x,G+1,z) in water:
     for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
      if (x+dx,G+1,z+dz) not in B:b.put(x+dx,G+1,z+dz,'terracotta',tid+'.tray.edge')
 facilities.append(dict(id=tid,kind=gh['kind'],bounds=gh['bounds']))
# Shared sorting area, practical shelter, working tables and water reservoir.
for aux in sp['agricultural_auxiliaries']:
 a,c,u,v=aux['bounds'];tid=aux['id'];b.box((a,G,c),(u,G+1,v),'smooth_stone',tid+'.pad')
 if tid=='A01':
  for x in [a,u-1]:
   for z in [c,v-1]:b.box((x,G+1,z),(x+1,G+5,z+1),'oak_log',tid+'.post')
  b.box((a,G+5,c),(u,G+6,v),'oxidized_copper',tid+'.roof')
  b.box((a+2,G+1,c+1),(u-2,G+2,c+3),'oak_planks',tid+'.sorting.table')
  for x in [a+3,a+7]:b.put(x,G+4,c+3,'sea_lantern',tid+'.work.light')
 else:
  for x in range(a+1,u-1):
   for z in range(c+1,v-1):
    if (x-(a+u-1)/2)**2+(z-(c+v-1)/2)**2<5:
     b.box((x,G+1,z),(x+1,G+5,z+1),'iron_block',tid+'.tank')
  b.put(a,G+1,c+3,'iron_bars',tid+'.tap')

# Shared sunning patch; two unaligned produce stacks and a bench under a tree.
b.box((112,G,163),(130,G+1,172),'gravel','common.yard')
b.box((114,G+1,164),(119,G+2,167),'hay_block','common.harvest')
b.box((125,G+1,168),(129,G+2,171),'oak_planks','common.worktable')
for x in range(119,123):b.put(x,G+1,170,M('oak_stairs',facing='north'),'common.bench')

# Trees in irregular clusters along edges and residual pockets; crowns avoid roads and farm plots.
tree_records=[];tr=rng('landscape');sites=[]
for x in range(12,309,11):
 if tr.random()<.66:sites.append((x+tr.randint(-3,3),tr.choice([3,4])))
 if tr.random()<.55:sites.append((x+tr.randint(-3,3),tr.choice([284,285])))
for z in range(20,278,13):
 if tr.random()<.55:sites.append((tr.choice([3,4]),z+tr.randint(-3,3)))
sites += [(98,88),(100,155),(120,166),(216,95),(211,212),(94,252),(179,257),(229,167),(129,78),(224,215),(201,222)]
for x,z in sites:
 r=tr.choice([2,2,3]);height=tr.randint(7,10)
 if not(r<=x<W-r and r<=z<D-r) or roadmask[z-r:z+r+1,x-r:x+r+1].any() or reserved[z-r:z+r+1,x-r:x+r+1].any():continue
 if fieldmask[z-r:z+r+1,x-r:x+r+1].any():continue
 if B.get((x,G,z))!=M('grass_block'):continue
 b.tree(x,z,G+1,height,r);tree_records.append([x,z,height,r])
# Low native vegetation in small clusters; never on roads, water or cropped fields.
for i in range(220):
 rr=rng(f'vegetation:{i}');cx=rr.randrange(4,W-4);cz=rr.randrange(4,D-4)
 for j in range(rr.randrange(3,9)):
  x=cx+rr.randrange(-2,3);z=cz+rr.randrange(-2,3)
  if roadmask[z,x] or reserved[z,x] or fieldmask[z,x] or (x,G+1,z) in B:continue
  if B.get((x,G,z))!=M('grass_block'):continue
  b.put(x,G,z,'moss_block' if j%3 else 'coarse_dirt','landscape.patch')
  if j%4==0:b.put(x,G+1,z,'oxeye_daisy' if i%5 else 'poppy','landscape.flower')

# Village junctions: low, single arm lamps rather than a repeated avenue of tall double poles.
street_lamps=[]
for x,z in [(48,132),(99,131),(139,132),(204,132),(228,147),(88,178),(137,208),(229,228),(102,99),(237,91),(306,139),(234,255)]:
 if reserved[z,x] or roadmask[z,x] or fieldmask[z,x]:continue
 b.put(x,G,z,'stone_bricks','lighting.pole.base')
 b.box((x,G+1,z),(x+1,G+6,z+1),'iron_bars','lighting.pole')
 b.put(x+1,G+5,z,'iron_bars','lighting.arm');b.put(x+1,G+4,z,'glowstone','lighting.street')
 b.put(x+1,G+6,z,M('polished_deepslate_slab'),'lighting.cap');street_lamps.append([x+1,G+4,z])

# Every water cell has a containing bottom and no horizontal air escape at its elevation.
for x,y,z in list(water):
 if 'water' not in B.get((x,y,z),''):continue
 if (x,y-1,z) not in B:b.put(x,y-1,z,'dirt','water.bottom')
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=(x+dx,y,z+dz)
  if 0<=q[0]<W and 0<=q[2]<D and states.family(B.get(q,'minecraft:air')) in ['air','crop','flower']:
   b.put(*q,'dirt','water.bank')

# Remove only external appendages that intrude into the approved road clearance.
# R07's rain pipe and condenser bracket previously crossed the narrow east lane.
pruned=[];columns=set()
for q,st in list(B.items()):
 x,y,z=q;own=b.s.owners[q]
 if roadmask[z,x] and y in [G+1,G+2] and own.startswith('R') and not states.family(st)=='stairs':
  inside=any(h['x']<=x<h['x']+h['w'] and h['z']<=z<h['z']+h['d'] for h in houses)
  if inside:raise ValueError(('road crossed approved house body',q,own))
  if any(k in own for k in ['pipe','aircon']):columns.add((x,z))
  pruned.append([*q,st,own]);b.put(*q,'air','road.appendage.clearance')
for q,st in list(B.items()):
 own=b.s.owners[q]
 if (q[0],q[2]) in columns and any(k in own for k in ['pipe','aircon']):b.put(*q,'air','road.appendage.clearance')

params=dict(case='田埂里',version=RUN,route='approved_P3_layout_to_NBT',seed=SEED,size_xyz=[W,H,D],coordinates=sp['coordinates'],buildings=houses,fields=farm_records,greenhouses=facilities,roads=sp['roads'],source_hashes=source_hashes,source_plan_sha256=hashlib.sha256((C/'input/layout_P3.json').read_bytes()).hexdigest(),house_adoption=copy_records,trees=tree_records,lighting='All occupied low-rise rooms lit; raw floors unlit; cool/warm material intent only',changes=['P3 footprints and road centerlines preserved','Unequal rectangular subplots, growth cohorts, harvested strips, loading notches','Narrow thresholds instead of wide courts','R18 sandstone and teal details, rooftop shade, blue glazing','Six agricultural sheds built'],limitations=['Furniture is decorative','Approximate preview materials and light; no in-game screenshots','Player collision and live game lighting pending'])
dump(C/'input/entries_B1.json',entries);dump(C/'input/lighting_B1.json',room_lights)
out=save_run(C,RUN,params,b,__file__,{'building_count':18,'game_status':'pending','preview_type':'Final NBT state boxes, not game screenshots'})
dump(out/'entries.json',entries);dump(out/'lighting.json',room_lights);dump(out/'agricultural_facilities.json',facilities)
dump(out/'road_appendage_pruning.json',pruned)
np.save(out/'roadmask.npy',roadmask)
print(json.dumps({'run':RUN,'blocks':len(B),'subplots':len(farm_records),'crop_counts':dict(crop_records),'trees':len(tree_records),'street_lamps':len(street_lamps)},ensure_ascii=False),flush=True)
