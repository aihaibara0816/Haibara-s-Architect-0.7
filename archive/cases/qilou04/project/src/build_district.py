"""Qilou04 / Grey arcades and Rongyinli-derived irregular parcels. Java 1.21.1."""
from pathlib import Path
import sys,json,copy,math,hashlib,uuid,collections,heapq
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n
import qilou_core as C,qilou_recipes as R,rong_build as V,rong_site as VS
import q04_facades as F,q04_landscape as L,q04_activity as ACT
from prototype_base import Study
from detail_lab import states as S
from district_plan import W,D,H,BASE_SEED,plan,rng
from qilou_detail import chamfer
RUN=sys.argv[1];SEED=int(sys.argv[2]) if len(sys.argv)>2 else BASE_SEED
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=True);C.OUT=R.OUT=OUT;C.SEED=R.SEED=SEED
city=Study('Qilou04',W,D,1,'榕灰里 · 骑楼与里巷');city.seed=SEED
city.box((0,0,0),(W,2,D),'dirt','base');city.box((0,2,0),(W,3,D),'smooth_stone','paving')
records=[];entries=[];allmods={};foot=set();roads=set();alleys=set();trees=[]
def shift(m,e):
 if not e:return
 def xyz(q):return [q[0],q[1],q[2]+e]
 m.blocks={(x,y,z+e):s for (x,y,z),s in m.blocks.items()};m.owners={(x,y,z+e):s for (x,y,z),s in m.owners.items()};m.bes={(x,y,z+e):s for (x,y,z),s in m.bes.items()}
 m.entry=xyz(m.entry);m.rear_entry=xyz(m.rear_entry)if m.rear_entry else None
 for r in m.rooms:r['bounds'][2]+=e;r['bounds'][5]+=e
 for r in m.uses:r['pos']=xyz(r['pos'])
 for r in m.lights:
  for k in ['position','support']:r[k]=xyz(r[k])
 for r in m.doors:
  for k in ['pos','lintel']:r[k]=xyz(r[k])
 for r in m.groups:
  if 'bounds_xyz'in r:r['bounds_xyz'][2]+=e;r['bounds_xyz'][5]+=e
  if 'use_points'in r:r['use_points']=[xyz(q)for q in r['use_points']]
 m.stair_paths=[[xyz(q) for q in line]for line in m.stair_paths]
 for r in m.stair_runs:r['path']=[xyz(q)for q in r['path']]
 m.upper_starts={k:[q[0],q[1]+e]for k,q in m.upper_starts.items()}
 if hasattr(m,'extra_entries'):m.extra_entries=[xyz(q)for q in m.extra_entries]
 for r in m.variation:r['position']=xyz(r['position'])
 for r in m.entities:r['TileZ']=n.Int(int(r['TileZ'])+e);r['Pos'][2]=n.Double(float(r['Pos'][2])+e)
 m.d+=e
def transform(q,r,floats=False):
 x,y,z=q;w,d=r['w'],r['d'];lim=0 if floats else 1
 for _ in range(r['turn']):x,z=d-lim-z,x;w,d=d,w
 return [x+r['origin'][0],y+r['origin'][1],z+r['origin'][2]]
def ensure_bes(m):
 for q,s in m.blocks.items():
  name=s.split('[')[0]
  if name.endswith('_bed'):m.bes[q]=n.Compound({'id':n.String('minecraft:bed')})
  elif name=='minecraft:barrel':m.bes.setdefault(q,n.Compound({'id':n.String(name),'Items':n.List[n.Compound]([])}))
  elif name=='minecraft:furnace':m.bes.setdefault(q,n.Compound({'id':n.String(name),'Items':n.List[n.Compound]([]),'BurnTime':n.Short(0),'CookTime':n.Short(0),'CookTimeTotal':n.Short(200),'RecipesUsed':n.Compound({})}))
 # Persistent leaves stay present without random-tick workarounds in imported structures.
 for q,s in list(m.blocks.items()):
  if '_leaves'in s:m.blocks[q]=s.replace('persistent=false','persistent=true')
def add_module(m,r,sp):
 ensure_bes(m);sp.update(id=r['id'],name=r['name'],family=r['family'],placement=r)
 C.save(m,r['id'],sp,(m.w,m.h,m.d));allmods[r['id']]=sp
 occupied=[]
 for q,s in m.blocks.items():
  p=tuple(transform(q,r));st=R.rotate(s,r['turn'])
  if p[1]>2 and p in city.blocks:raise ValueError(('house collision',r['id'],p,city.owners[p]))
  if not(0<=p[0]<W and 0<=p[2]<D and 0<=p[1]<H):raise ValueError(('outside',r['id'],p))
  city.p(*p,st,m.owners.get(q,r['id']));occupied.append(p)
  if p[1]==2:foot.add((p[0],p[2]))
 for q,be in m.bes.items():city.bes[tuple(transform(q,r))]=copy.deepcopy(be)
 for ee in m.entities:
  e=copy.deepcopy(ee);e['Pos']=n.List[n.Double]([n.Double(v)for v in transform(list(map(float,e['Pos'])),r,True)])
  q=transform([int(e[k])for k in ['TileX','TileY','TileZ']],r)
  for k,v in zip(['TileX','TileY','TileZ'],q):e[k]=n.Int(v)
  face=['south','west','north','east'][int(e['facing'])]
  for _ in range(r['turn']):face=S.TURN[face]
  e['facing']=n.Byte(['south','west','north','east'].index(face));u=uuid.uuid5(uuid.NAMESPACE_URL,f'Q04/{r["id"]}/{q}')
  e['UUID']=n.IntArray([int.from_bytes(u.bytes[i:i+4],'big',signed=True) for i in range(0,16,4)]);city.entities.append(e)
 bbox=[[min(q[i]for q in occupied),max(q[i]for q in occupied)+1]for i in range(3)]
 r.update(floors=m.floors,levels=len(m.floors),entry=transform(m.entry,r),geometry_bounds=bbox,source_nbt_sha256=sp['source_nbt_sha256'])
 records.append(r);print('module',r['id'],len(m.blocks),flush=True)
 return r

# Checkpoint only the authored buildings; site/landscape edits remain independent.
import pickle,shutil
cache_sources=['rong_build','rong_site','district_plan','qilou_core','qilou_recipes','qilou_detail','qilou_states','prototype_base','interior_kit','q04_facades','q04_activity']
cachekey=hashlib.sha256((str(SEED)+Path(__file__).read_text().rsplit('# A legible main street',1)[0]+''.join((ROOT/'src'/(name+'.py')).read_text() for name in cache_sources)).encode()).hexdigest()
cp=ROOT/'cache'/('houses_'+cachekey+'.pkl');cp.parent.mkdir(exist_ok=True)
if cp.exists():
 with cp.open('rb') as fp:city,records,entries,allmods,foot,p,vd,cache_origin=pickle.load(fp)
 city.bes={q:n.parse_nbt(v)for q,v in city.bes.items()};city.entities=[n.parse_nbt(v)for v in city.entities]
 for r in records:
  for suffix in ['.nbt','_spec.json']:shutil.copyfile(Path(cache_origin)/(r['id']+suffix),OUT/(r['id']+suffix))
 for name in ['urban_records.json','plan_used.json']:shutil.copyfile(Path(cache_origin)/name,OUT/name)
 print('reuse immutable building checkpoint',len(records),flush=True)
else:
 # Eight commercial parcels on each side. Continuous arcade ground, varied upper programmes.
 catalog={r['id']:r for r in R.CONFIG}
 frontages=[('N',15,93,0,['Apothecary','Grain','Bookshop','Hardware','Grocery','Textile','Barber','Teahouse'],[0,0,6,0,2,0,5,0]),('S',44,139,2,['Post','Clinic','Inn','Bakery','Hardware','Grain','Textile','Teahouse'],[0,5,0,2,0,4,0,0])]
 for side,x,z,turn,ids,gaps in frontages:
  for i,src in enumerate(ids):
   if side=='N'and i==3 or side=='S'and i in[1,4,5]:continue
   new_id=side+str(i+1).zfill(2)
   r=copy.deepcopy(catalog[src]);extra=[0,4,6,2,5,0,3,4][i] if side=='N' else [0,3,0,5,2,4,0,2][i]
   wall=F.PALETTES[F.CHOICES[new_id][0]]['wall'];r['wall']=wall
   if new_id in['N03','S01','S04']:
    m,largeinfo=F.large(new_id,wall);r.update(largeinfo)
   else:
    m=R.decorate(R.shop(r),r)
    if m.kind=='corner':chamfer(m,r)
   m.id=new_id;m.program=r['name'];m.h=36
   # Exterior colour is edited by ownership, keeping interior upholstery and shop goods purposeful.
   r['facade_revision']=F.finish(m,new_id)
   wall=r['facade_revision']['wall']
   shift(m,extra)
   if extra:
    # A lower rear workroom changes depth and roof silhouette without stretching any furniture.
    for xx in range(3,m.w-2):
     for zz in range(0,extra+4):
      m.p(xx,2,zz,'polished_andesite','annex.floor');m.p(xx,8,zz,'smooth_stone','annex.roof')
      if xx in [3,m.w-3]or zz==0:
       for yy in range(3,8):m.p(xx,yy,zz,wall,'annex.wall')
    for yy in [3,4]:m.p(5,yy,0,'air','annex.door')
    m.rear_entry=[5,3,0];m.use('annex.entry',5,1)
    for xx in range(8,m.w-4,3):m.barrel(xx,3,2);m.barrel(xx,4,2);m.pot(xx,5,2)
    m.p(6,7,2,'sea_lantern','annex.light');m.lights.append({'position':[6,7,2],'support':[6,8,2],'type':'sea_lantern'})
    # Passage to the pre-existing rear entry; keep two clear blocks throughout.
    for zz in range(1,extra+5):
     for xx in [4,5]:
      for yy in [3,4]:m.p(xx,yy,zz,'air','annex.passage')
    m.doors=[dd for dd in m.doors if not(dd['pos'][0]in[4,5]and dd['pos'][1]==3 and 1<=dd['pos'][2]<=extra+4)]
    m.door(5,3,0,'north','dark_oak')
    m.room('annex','后屋备货与家务',4,1,m.w-3,extra+3,2,2)
   r.update(id=new_id,source_recipe=src,origin=[x,0,z-extra if turn==0 else z],turn=turn,w=m.w,d=m.d,family='qilou',name=r['name']+(' · 南街'if side=='S'else''),depth_extension=extra)
   sp=m.stats();sp.update(kind=m.kind,program=r['program'],upper_starts=m.upper_starts,stair_runs=m.stair_runs,rear_entry=m.rear_entry,variation=m.variation)
   add_module(m,r,sp)
   entries.append({'id':new_id+'.shop','entry':r['entry'],'outside':transform([m.entry[0],3,m.entry[2]+1],r)})
   if m.rear_entry:entries.append({'id':new_id+'.rear','entry':transform(m.rear_entry,r),'outside':transform([m.rear_entry[0],3,m.rear_entry[2]-1],r)})
   for k,q in enumerate(getattr(m,'extra_entries',[])):
    entries.append({'id':new_id+'.wing'+str(k),'entry':transform(q,r),'outside':transform([q[0],3,q[2]+(1 if q[2]>=extra+20 else-1)],r)})
   end=3 if new_id=='N03'else 1 if new_id=='S01'else 5 if new_id=='S04'else i
   x+=m.w+gaps[end]
 
 # The original Rongyinli engine supplies 32 different parcels, unit divisions and roof access cores.
 p=plan(SEED);vb,vd=V.build(p);vd['activity_summary']=ACT.urban(vb,vd,p);(OUT/'urban_records.json').write_text(json.dumps(vd,ensure_ascii=False));(OUT/'plan_used.json').write_text(json.dumps(p,ensure_ascii=False,indent=2))
 for t in p['buildings']:
  id=t['id'];localblocks={q:s for q,s in vb.s.blocks.items()if vb.s.owners.get(q,'').startswith(id+'.')}
  # Tile plates cut away by the floor mask are ground context, not a second owner’s house.
  assert localblocks,id
  xmin=min(q[0]for q in localblocks);zmin=min(q[2]for q in localblocks);xmax=max(q[0]for q in localblocks);zmax=max(q[2]for q in localblocks)
  m=Study(id,xmax-xmin+1,zmax-zmin+1,t['floors'],t['name']);m.h=H;m.floors=[2+5*f for f in range(t['floors'])];m.kind=t['shape']
  for (xx,y,zz),s in localblocks.items():m.p(xx-xmin,y,zz-zmin,s,vb.s.owners.get((xx,y,zz),id))
  ownentries=[e for e in vd['entries']if e['id']==id or e['id'].startswith(id+'.')];entry=ownentries[0]['entry'];m.entry=[entry[0]-xmin,entry[1],entry[2]-zmin]
  for u in vd['rooms']:
   if u['unit_id'].startswith(id+'.'):
    a=copy.deepcopy(u);q=a['bounds_xyz'];a['bounds']=[q[0]-xmin,q[1],q[2]-zmin,q[3]-xmin,q[4],q[5]-zmin];m.rooms.append(a)
  for shop in vd['shopfronts']:
   if shop['building']!=id:continue
   cells=shop['front_cells'];xx,zz=cells[len(cells)//2];nx,nz=ACT.NORMAL[shop['face']];q=(xx+nx*2-xmin,7,zz+nz*2-zmin)
   m.p(*q,S.make('oak_wall_sign',facing=shop['face']),id+'.shop_text')
   textside=n.Compound({'messages':n.List[n.String]([n.String(json.dumps({'text':v,'color':'white'},ensure_ascii=False))for v in ['',shop['name'],id,'']]),'color':n.String('white'),'has_glowing_text':n.Byte(1)})
   m.bes[q]=n.Compound({'id':n.String('minecraft:sign'),'front_text':copy.deepcopy(textside),'back_text':copy.deepcopy(textside),'is_waxed':n.Byte(1)})
  sp=m.stats();sp.update(kind=t['shape'],program=t['ground'],urban=t,unit_count=sum(u['building']==id for u in vd['units']),main_entries=ownentries,upper_starts={},stair_runs=[])
  r=dict(id=id,name=t['name'],origin=[xmin,0,zmin],turn=0,w=m.w,d=m.d,family='village',kind=t['shape'],program=t['ground'],lot=t,facade_revision={'palette':t['palette'],'wall':V.PAL[t['palette']][0],'roof':'flat_service','roof_label':'平屋顶与生活设备'})
  add_module(m,r,sp);entries+=ownentries
 del vb
 
 oldbes,oldentities=city.bes,city.entities
 city.bes={q:v.snbt()for q,v in city.bes.items()};city.entities=[v.snbt()for v in city.entities]
 with cp.with_suffix('.tmp').open('wb')as fp:pickle.dump((city,records,entries,allmods,foot,p,vd,str(OUT)),fp,protocol=5)
 cp.with_suffix('.tmp').replace(cp)
 city.bes,city.entities=oldbes,oldentities

# A legible main street and crossroad remain continuous. Rear lanes are routed through actual gaps.
for x in range(W):
 for z in range(126,139):roads.add((x,z))
for x in range(211,224):
 for z in range(D):roads.add((x,z))
for x,z in roads:
 assert not any((x,y,z)in city.blocks for y in [3,4]),('road obstruction',x,z)
 city.p(x,2,z,'gray_concrete','road')
for x in range(3,W-4):
 if x%11<5 and not 203<=x<=232:city.p(x,2,132,'yellow_terracotta','road.marking')
for z in range(4,D-3):
 if z%11<5 and not 117<=z<=147:city.p(217,2,z,'white_concrete','road.marking')
for x in [204,228]:
 for xx in range(x,x+3):
  for z in range(126,139,2):city.p(xx,2,z,'white_concrete','crosswalk')
for z in [119,143]:
 for zz in range(z,z+3):
  for x in range(211,224,2):city.p(x,2,zz,'white_concrete','crosswalk')
inside_foot=set()
for t in p['buildings']:inside_foot.update(VS.local(t,x,z)for x,z in VS.mask(t))
for r in records:
 if r['family']!='qilou':continue
 e=r['depth_extension'];right=r['w']-5 if r['kind']=='corner'else r['w']
 for xx in range(right):
  for zz in range(e+3,e+24):
   q=transform([xx,3,zz],r);inside_foot.add((q[0],q[2]))
 if e:
  for xx in range(3,r['w']-2):
   for zz in range(e+4):
    q=transform([xx,3,zz],r);inside_foot.add((q[0],q[2]))
def walk(q):
 x,z=q
 return 1<=x<W-1 and 1<=z<D-1 and q not in inside_foot and all((x,y,z)not in city.blocks or any(v in city.blocks[x,y,z]for v in ['carpet','door['])for y in [3,4])
street={(x,z)for x in range(W)for z in [122,123,124,125,139,140,141,142]if walk((x,z))}|{(x,z)for x in [207,208,209,210,224,225,226,227]for z in range(D)if walk((x,z))}
paths=[]
# A secondary rear door inside a shared rear annex is an internal connection, not an external entrance.
entries=[e for e in entries if '.wing'not in e['id']or tuple(e['outside'][::2])not in inside_foot]
for e in entries:
 start=tuple(e['outside'][::2]);dest=street|alleys
 # A* prefers existing lanes, with bends induced by buildings rather than arbitrary zigzags.
 dist={start:0};prev={start:None};h=[];heapq.heappush(h,(0,start));goal=None
 while h:
  cost,q=heapq.heappop(h)
  if cost!=dist[q]:continue
  if q in dest:goal=q;break
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   a=(q[0]+dx,q[1]+dz)
   if not walk(a):continue
   edge=1 if a in alleys else 2+sum(not walk((a[0]+dx0,a[1]+dz0))for dx0,dz0 in[(1,0),(-1,0),(0,1),(0,-1)])*2
   v=cost+edge
   if v<dist.get(a,10**12):dist[a]=v;prev[a]=q;heapq.heappush(h,(v,a))
 if goal is None:raise ValueError(('no public approach',e['id'],start))
 line=[]
 while goal is not None:line.append(goal);goal=prev[goal]
 paths.append({'id':e['id'],'line':line})
 for x,z in line:
  for dx in [-1,0,1]:
   for dz in [-1,0,1]:
    a=x+dx,z+dz
    if walk(a)and a not in roads:alleys.add(a)
for x,z in alleys:city.p(x,2,z,'stone_bricks'if (x//7+z//6)%4==0 else'polished_andesite','lane')
# Irregular public pocket: a shaded forecourt at the NW crossroad, open to both streets.
plaza=set()
for x in range(173,208):
 for z in range(88,126):
  if x+z<268 or not walk((x,z)):continue
  plaza.add((x,z));city.p(x,2,z,'polished_andesite'if (x//5+z//7)%3 else'smooth_stone','plaza')
public_keep=roads|alleys|{q for q in street if q[1]in[122,123,141,142]or q[0]in[207,208,226,227]}
for x,z,w in[(181,116,5),(195,88,5)]:
 if all(walk((xx,z))and(xx,z)not in public_keep for xx in range(x-1,x+w+1)):C.bench(city,x,z,2,w,'brown')
# Attached pots, goods and meters collect at edges; not across every lane centre.
for t in p['buildings']:
 rr=rng(SEED,t['id'],'street_props');candidates=[]
 for x in range(t['x']-2,t['x']+t['w']+2):
  for z in [t['z']-2,t['z']+t['d']+1]:
   if walk((x,z))and(x,z)not in public_keep and(x,z)not in plaza:candidates.append((x,z))
 rr.shuffle(candidates)
 for x,z in candidates[:rr.randint(1,3)]:
  city.barrel(x,3,z);city.pot(x,4,z)
for i,(x,z)in enumerate([(10,123),(70,124),(155,124),(202,123),(232,124),(291,124),(347,124),(43,141),(111,141),(184,141),(229,141),(304,141),(209,47),(225,83),(209,190),(225,232)]):
 if not walk((x,z))or (x,z)in alleys:continue
 for y in range(3,10):city.p(x,y,z,'iron_bars','lamp.post')
 city.p(x,10,z,'sea_lantern','lamp.head');city.p(x,11,z,'smooth_stone_slab','lamp.cap',type='bottom')
trees,landscape=L.build(city,records,roads,alleys,street,plaza,inside_foot,SEED)
street_activity=ACT.street(city,roads,alleys,street,plaza,SEED)
# Count and snapshot, binding every model / render to the same final blocks.
ensure_bes(city)
spec=dict(case_id='Qilou04',run=RUN,seed=SEED,size_xyz=[W,H,D],name='榕灰里 · 骑楼与里巷',buildings=records,spawn_local=[200,3,121],entries=entries,roads=[{'id':'main','width':13,'bounds':[0,126,W,139]},{'id':'cross','width':13,'bounds':[211,0,224,D]}],road_cells=sorted(roads),lane_cells=sorted(alleys),paths=paths,plaza_cells=sorted(plaza),trees=trees,landscape=landscape,activity=vd['activity_summary'],street_lighting=street_activity,revision='R19 · 沿街商铺与生活夜景',regions={'arcades':'西侧主街两侧','back_lanes':'骑楼背后的生活区','east_village':'过十字路口后以住宅为主','plaza':'十字路口西北角榕树广场'},variation_scope='Authored irregular parcel topology; independent seeded dimensions, setbacks, height, household lighting and details. Main street connectivity is constrained.',status={'game':'pending','aesthetic':'pending user review'})
C.save(city,'Qilou04',spec,(W,H,D));(OUT/'spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
print(json.dumps({'buildings':len(records),'blocks':len(city.blocks),'trees':len(trees),'sha256':spec['source_nbt_sha256']},ensure_ascii=False),flush=True)
