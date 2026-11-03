"""Q04 R19: street-facing businesses and purpose-led evening lighting.
Shells, stairs and upper-floor furniture are retained. This is an authored case adapter.
"""
import hashlib,collections
from detail_lab import states as S
import rong_site as VS
M=S.make
def rand(seed,key):return int(hashlib.sha256(f'{seed}/{key}'.encode()).hexdigest()[:12],16)/16**12

NEW_GROUND={'A5':'repair','C5':'tea','C9':'grocery','D3':'laundry','E2':'grocery','E4':'restaurant','E6':'barber'}
# World directions: a commercial label is insufficient if the door faces away from the street.
FACES={'A5':'east','C1':'north','C8':'east','C9':'east','D1':'west','D4':'north','D6':'south','D7':'west','E1':'north','E2':'north','E3':'north','E4':'west','E6':'north'}
MICRO={'D4':('west','repair'),'D7':('south','grocery'),'E1':('west','tea')}
NAMES={'grocery':'街坊便利','restaurant':'街坊食店','repair':'五金修配','laundry':'洗衣缝补','barber':'街坊理发','tea':'茶水小座'}
SIGN={'grocery':'green_terracotta','restaurant':'red_terracotta','repair':'blue_terracotta','laundry':'cyan_terracotta','barber':'brown_terracotta','tea':'dark_oak_planks'}
NORMAL={'north':(0,-1),'east':(1,0),'south':(0,1),'west':(-1,0)}

def urban(b,d,p):
 seed=p['seed'];shops=[];fixtures=[];units={u['id']:u for u in d['units']};rooms={u['id']:u for u in d['rooms']}
 def put(q,st,owner):b.put(*q,st if st.startswith('minecraft:') else M(st),owner)
 def remove_module(m):
  prefix=m['component_id']
  for q,o in list(b.s.owners.items()):
   if o==prefix or o.startswith(prefix+'.'):put(q,'air',prefix+'.removed')
  d['modules'].remove(m)
 for t in p['buildings']:
  tid=t['id'];shape={VS.local(t,x,z)for x,z in VS.mask(t)};W,D=(t['w'],t['d'])if t['rotation']%2==0 else(t['d'],t['w'])
  jobs=[]
  if t['ground']!='home':jobs.append((tid+'.F01.R',FACES.get(tid,['north','east','south','west'][t['rotation']]),t['ground']))
  if tid in MICRO:
   face,kind=MICRO[tid];uid=tid+'.F01.L';u=units[uid];u.update(kind=kind,layout='small_street_service',lit=True)
   main=rooms[u['rooms'][0]];main['function']=kind
   for m in list(d['modules']):
    if m['unit_id']==uid and m['room_id']==main['id']:remove_module(m)
   # A narrow service shop has a counter, working equipment, stock and a waiting stool.
   a,y,c,A,Y,C=main['bounds_xyz'];longx=A-a>C-c
   candidates=[(x,3,z)for x in range(a,A)for z in range(c,C)if (x,z)in shape and all((x,yy,z)not in b.s.blocks for yy in[3,4]) and not any(r['unit_id']==uid and r['function']=='bathroom'and r['bounds_xyz'][0]<=x<r['bounds_xyz'][3]and r['bounds_xyz'][2]<=z<r['bounds_xyz'][5]for r in d['rooms'])]
   nx,nz=NORMAL[face];tx,tz=-nz,nx;mx,mz=(a+A-1)/2,(c+C-1)/2
   candidates.sort(key=lambda q:(abs((q[0]-mx)*tx+(q[2]-mz)*tz),q[0]*nx+q[2]*nz))
   used=[]
   # Reject isolated one-cell pockets behind the bathroom partition before placing stock.
   entry=tuple(u['entry'][::2]);queue=collections.deque([entry]);reachable=set()
   while queue:
    xx,zz=queue.popleft()
    if (xx,zz)in reachable or not(t['x']<=xx<t['x']+t['w']and t['z']<=zz<t['z']+t['d']):continue
    if any((xx,yy,zz)in b.s.blocks for yy in[3,4]):continue
    reachable.add((xx,zz));queue.extend([(xx+1,zz),(xx-1,zz),(xx,zz+1),(xx,zz-1)])
   candidates=[q for q in candidates if(q[0],q[2])in reachable]
   for k,st in enumerate(['barrel','crafting_table'if kind=='repair'else'water_cauldron','barrel','dark_oak_stairs']):
    choices=[q for q in candidates if sum(abs(q[i]-u['entry'][i])for i in[0,2])>3 and all(abs(q[0]-v[0])+abs(q[2]-v[2])>=3 for v in used)]
    choices=[q for q in choices if sum(a<=q[0]+dx<A and c<=q[2]+dz<C and all((q[0]+dx,yy,q[2]+dz)not in b.s.blocks for yy in[3,4])for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)])>=2]
    if not choices:break
    q=choices[0];used.append(q);owner=uid+'.shopfit.'+str(k)
    put(q,M(st,level=3)if st=='water_cauldron'else M(st),owner)
    d['modules'].append({'component_id':owner,'unit_id':uid,'room_id':main['id'],'kind':['counter','workstation','stock','chair'][k],'bounds_xyz':[q[0],3,q[2],q[0]+1,4,q[2]+1],'use_faces':['adjacent_floor'],'game_functional':st in['barrel','crafting_table']})
   jobs.append((uid,face,kind))
  for uid,face,kind in jobs:
   u=units[uid];a,y,c,A,Y,C=u['bounds_xyz'];nx,nz=NORMAL[face];tx,tz=-nz,nx
   # Exterior wall cells immediately adjoining this commercial unit; reject bath/service rooms.
   pool=[]
   for x,z in shape:
    ix,iz=x-nx,z-nz
    if(x+nx,z+nz)in shape or not(a<=ix<A and c<=iz<C):continue
    if any(r['unit_id']==uid and r['function']=='bathroom'and r['bounds_xyz'][0]<=ix<r['bounds_xyz'][3]and r['bounds_xyz'][2]<=iz<r['bounds_xyz'][5]for r in d['rooms']):continue
    pool.append((x,z))
   groups=collections.defaultdict(list)
   for x,z in pool:groups[x*nx+z*nz].append((x,z))
   runs=[]
   for group in groups.values():
    group.sort(key=lambda q:q[0]*tx+q[1]*tz);run=[]
    for q in group:
     if run and abs(q[0]-run[-1][0])+abs(q[1]-run[-1][1])!=1:runs.append(run);run=[]
     run.append(q)
    if run:runs.append(run)
   assert runs,('no street facade',uid,face)
   run=max(runs,key=len);assert len(run)>=4,('narrow frontage',uid,run)
   length=min(len(run),13 if uid.endswith('.R')else 9);start=max(0,(len(run)-length)//2);run=run[start:start+length]
   # Locate a two-wide opening with an actual interior floor and a clear internal approach.
   candidate=[]
   for k in range(1,len(run)-2):
    q=run[k];inn=(q[0]-nx*3,q[1]-nz*3)
    if not(a<=inn[0]<A and c<=inn[1]<C):continue
    blockers=sum((x-nx*j,yy,z-nz*j)in b.s.blocks for x,z in run[k:k+2]for j in[1,2,3]for yy in[3,4])
    candidate.append((blockers+abs(k-len(run)//2)*.12,k))
   assert candidate,('no door',uid,face)
   k=min(candidate)[1];doorcells=run[k:k+2];owner=uid+'.streetfront'
   clear={(x-nx*j,yy,z-nz*j)for x,z in doorcells for j in range(-1,4)for yy in[3,4,5]}
   for m in list(d['modules']):
    if m['unit_id']!=uid:continue
    bounds=m['bounds_xyz']
    if any(bounds[0]<=q[0]<bounds[3]and bounds[1]<=q[1]<bounds[4]and bounds[2]<=q[2]<bounds[5]for q in clear):remove_module(m)
   for q in clear:put(q,'air',owner+'.door_clear')
   for j,(x,z)in enumerate(run):
    if (x,z)not in doorcells:
     for yy in[3,4,5]:put((x,yy,z),'smooth_stone'if j in[0,len(run)-1]or j%6==0 else'glass_pane',owner+'.display')
    for dep in[1,2]:
     q=(x+nx*dep,6,z+nz*dep)
     if q not in b.s.blocks:put(q,M('smooth_stone_slab',type='top'),owner+'.awning')
    # Sign band lies below the next storey's existing windows.
    put((x+nx,7,z+nz),SIGN[kind],owner+'.sign_band')
    if j in[2,len(run)-3]:
     q=(x+nx,6,z+nz);put(q,'sea_lantern'if kind in['grocery','laundry']else'glowstone',owner+'.awning_light');fixtures.append({'xyz':q,'class':'shop_canopy','building':tid,'unit_id':uid})
   for x,z in doorcells:
    for dep in[-1,0,1,2]:put((x+nx*dep,2,z+nz*dep),'polished_andesite',owner+'.apron')
   x,z=doorcells[0];e={'id':tid+'.street.'+uid[-1],'unit_id':uid,'entry':[x,3,z],'inside':[x-nx,3,z-nz],'outside':[x+nx,3,z+nz],'width':2,'kind':kind,'role':'customer','face':face}
   d['entries'].append(e)
   shops.append({'building':tid,'unit_id':uid,'kind':kind,'name':NAMES[kind],'face':face,'frontage_width':len(run),'entry':e['entry'],'inside':e['inside'],'outside':e['outside'],'front_cells':run,'canopy_depth':2,'residential_entry_separate':True})
 # Goods distinguish convenience/repair shops from library shelving.
 for mod in d['modules']:
  uid=mod['unit_id'];kind=units[uid]['kind']
  if mod['kind']!='shelf' or kind not in['grocery','repair']:continue
  prefix=mod['component_id'];base=units[uid]['floor_y']
  for q,o in list(b.s.owners.items()):
   if o==prefix and b.s.blocks.get(q)=='minecraft:bookshelf':
    material='barrel'if q[1]==base or kind=='repair'else('melon'if(q[0]+q[2])%3==0 else'red_wool'if(q[0]+q[2])%3==1 else'barrel')
    put(q,material,prefix)
 # Replace old household lighting with independent activity states. Common stairs remain on.
 for lamp in d['lamps']:
  if lamp.get('unit_id') and tuple(lamp['xyz'])in b.s.blocks:
   q=tuple(lamp['xyz']);st=b.s.blocks[q]
   if any(k in st for k in['sea_lantern','glowstone','end_rod']):put(q,'white_concrete',lamp['owner']+'.off_panel')
 d['lamps']=[l for l in d['lamps']if not l.get('unit_id')]
 activities=[]
 for uid,u in units.items():
  home=u['kind']=='home';v=rand(seed,uid+'/evening_activity');rate=.48+.35*rand(seed,u['building']+'/occupancy')
  state=('asleep'if v>=rate else'bedside'if v<rate*.22 else'cooking'if v<rate*.43 else'living')if home else('closing'if rand(seed,uid+'/business')<.14 else'open')
  u['activity']=state;u['lit']=state!='asleep';lamps=[]
  if state!='asleep':
   a,fy,c,A,Y,C=u['bounds_xyz'];cy=fy+3
   candidates=[]
   for x in range(a,A):
    for z in range(c,C):
     q=(x,cy,z)
     if b.s.blocks.get(q)=='minecraft:white_concrete'and all((x,yy,z)not in b.s.blocks for yy in[fy+1,fy+2]):
      candidates.append((x,z))
   # Room-scale pools reach windows; the count varies with activity and floor area.
   if state in['bedside','cooking']:
    targetmods=[m for m in d['modules']if m['unit_id']==uid and m['kind']==('bed'if state=='bedside'else'kitchen')]
    targets=[(m['bounds_xyz'][0],m['bounds_xyz'][2])for m in targetmods][:2]or[(A-2,c+3)]
   else:
    targets=[(a+2,c+2),(A-3,c+3),(A-3,(c+C)//2),(a+2,C-3)]
    if C-c>22:targets.extend([(A-3,C-4),((a+A)//2,(c+C)//2)])
    if A-a>18:targets.extend([((a+A)//2,c+3),((a+A)//2,C-4)])
    if state=='closing':targets=targets[:2]
   for j,tar in enumerate(targets):
    valid=[q for q in candidates if all(abs(q[0]-v[0])+abs(q[1]-v[2])>=5 for v in lamps)]
    if not valid:continue
    x,z=min(valid,key=lambda q:abs(q[0]-tar[0])+abs(q[1]-tar[1]));q=(x,cy,z)
    material='sea_lantern'if(not home and u['kind']in['grocery','barber','laundry'])or state=='cooking'else'glowstone'
    put(q,material,uid+'.activity_light.'+str(j));lamps.append(q);d['lamps'].append({'xyz':q,'material':material,'owner':uid+'.activity_light','unit_id':uid,'fixture':'recessed','activity':state})
  activities.append({'unit_id':uid,'building':u['building'],'floor':u['floor'],'use':u['kind'],'activity':state,'fixtures':lamps})
 # Keep existing window shapes. Colour intent uses materials; vanilla lighting is not coloured.
 d['shopfronts']=shops;d['evening_activity']=activities;d['frontage_lamps']=fixtures
 return {'shopfronts':shops,'activity_counts':dict(collections.Counter(v['activity']for v in activities)),'homes':sum(v['use']=='home'for v in activities),'active_homes':sum(v['use']=='home'and v['activity']!='asleep'for v in activities),'commercial_units':sum(v['use']!='home'for v in activities),'independent_seed_channels':['occupancy','evening_activity','business','street_fixture'],'vanilla_coloured_light':False}

def street(city,roads,alleys,street_cells,plaza,seed):
 """Staggered arms on main roads, shorter alley poles and shaded plaza lighting."""
 # Replace the old bare luminous cubes only; upper storeys and tree crowns are not edited.
 for q,o in list(city.owners.items()):
  if '.lamp.'in o:city.p(*q,'air','old_street_lamp_removed')
 results=[];occupied=set()
 def add(x,z,typ,dx,dz):
  if (x,z)in roads or(x,z)in alleys:return False
  h={'road':9,'lane':6,'garden':5}[typ]
  cells={(x,y,z):('polished_andesite'if y==3 else'iron_bars')for y in range(3,h+1)}
  cells[x,h,z]='smooth_stone'
  length=3 if typ=='road'else 1
  for k in range(1,length+1):cells[x+dx*k,h,z+dz*k]=M('smooth_stone_slab',type='bottom')
  cells[x+dx*length,h-1,z+dz*length]='sea_lantern'if typ=='road'else M('lantern',hanging='true')
  cells[x+dx*length,h,z+dz*length]=M('smooth_stone_slab',type='bottom')
  if any(q in city.blocks or q in occupied for q in cells):return False
  if any(abs(x-r['base'][0])+abs(z-r['base'][2])<(13 if typ=='road'else 9)for r in results):return False
  for q,st in cells.items():city.p(*q,st,'streetlight.'+typ);occupied.add(q)
  results.append({'type':typ,'base':[x,3,z],'light':[x+dx*length,h-1,z+dz*length],'height':h,'head_arm_length':length});return True
 # Shared family, staggered sides and bounded spacing; main carriageway stays completely clear.
 for side,z,dz in[('north',124,1),('south',140,-1)]:
  x=8 if side=='north'else 22
  while x<350:
   for off in[0,1,-1,2,-2,4,-4]:
    if add(x+off,z,'road',0,dz):break
   x+=24+int(rand(seed,f'road/{side}/{x}')*11)
 for side,x,dx in[('west',209,1),('east',225,-1)]:
  z=10 if side=='west'else 26
  while z<245:
   if not 115<z<150:
    for off in[0,2,-2,4,-4]:
     if add(x,z+off,'road',dx,0):break
   z+=25+int(rand(seed,f'cross/{side}/{z}')*10)
 # Alley-edge candidates face the actual route; omit any that touch foliage/buildings.
 candidates=[]
 for x,z in alleys:
  for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)]:
   q=(x+dx,z+dz)
   if q not in alleys and q not in roads and 3<q[0]<353 and 3<q[1]<247:candidates.append((q[0],q[1],-dx,-dz))
 for x,z,dx,dz in sorted(set(candidates),key=lambda q:rand(seed,str(q)+'/lane')):
  if sum(r['type']=='lane'for r in results)>=24:break
  add(x,z,'lane',dx,dz)
 for x,z,dx,dz in[(180,113,1,0),(194,114,-1,0),(200,100,0,1),(187,96,0,1)]:add(x,z,'garden',dx,dz)
 return {'fixtures':results,'counts':dict(collections.Counter(v['type']for v in results)),'method':'staggered main-road arms; alley-edge lanterns; shop canopy fixtures; steady public cores; unit activity profiles','seed':seed}
