from pathlib import Path
import sys,json,math,collections,functools,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import taisho_states,nbtlib as n
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];group=sys.argv[2];src=R/(group+'.nbt');b=load_build(src,Limits(cells=12000000,nodes=50000000,decoded_bytes=256*1024*1024));sp=json.loads((R/(group+'_spec.json')).read_text());f={'entities':b.info['entities_payload']};errors=[];blocks=b.blocks;be={tuple(e['pos']):e['nbt']for e in b.info['block_entities_payload']}
def block(q):return blocks.get(tuple(q),'minecraft:air')
@functools.lru_cache(None)
def boxes(s):return S.boxes(s)
for st in set(blocks.values()):S.validate(st)
for q,st in blocks.items():
 name,pr=parse_state(st)
 if name.endswith('_bed'):
  d=S.DIRS[pr['facing']];other=tuple(q[i]+d[i]*(1 if pr['part']=='foot'else -1)for i in range(3));nn,pp=parse_state(block(other))
  if nn!=name or pp.get('part')==pr['part']or pp.get('facing')!=pr['facing']:errors.append(['bed_pair',q])
  if str(be.get(q,{}).get('id',''))!='minecraft:bed':errors.append(['bed_entity',q])
 if name.startswith('minecraft:potted_')or name=='minecraft:flower_pot'or name.endswith('_carpet'):
  if not any(v[4]>=1 and v[0]<=.5<=v[3]and v[2]<=.5<=v[5]for v in boxes(block((q[0],q[1]-1,q[2])))):errors.append(['small_object_support',q,name])
 if name.endswith('_wall_sign'):
  d=S.DIRS[pr['facing']];back=tuple(q[i]-d[i]for i in range(3))
  if block(back)=='minecraft:air':errors.append(['wall_attachment',q])
 if name.endswith('_leaves')and pr.get('persistent')!='true':errors.append(['leaf_decay',q])
for q,e in be.items():
 name,_=parse_state(block(q));expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else'minecraft:banner'if name.endswith('_wall_banner')else name
 if str(e['id'])!=expected:errors.append(['be_type',q])
for d in sp['doors']:
 q=d['pos'];nn,lo=parse_state(block(q));nu,up=parse_state(block((q[0],q[1]+1,q[2])))
 if nn!=nu or lo.get('half')!='lower'or up.get('half')!='upper'or any(lo.get(k)!=up.get(k)for k in['facing','hinge','open']):errors.append(['door_pair',d['id']])
 if not S.support_cube(block(d['lintel'])):errors.append(['lintel',d['id']])
 delta=(1,0,0)if d['facing']in['north','south']else(0,0,1)
 for sg in[-1,1]:
  if not S.support_cube(block(tuple(q[i]+sg*delta[i]for i in range(3)))):errors.append(['frame',d['id']])
for l in sp['lights']:
 q=l['position']
 if not block(q).startswith('minecraft:lantern'):errors.append(['lamp_missing',q])
 if not any(v[1]<=0 and v[0]<=.5<=v[3]and v[2]<=.5<=v[5]for v in boxes(block(l['support']))):errors.append(['lamp_support',q])
def hit(x,y,z):
 lo=[x-.299,y+.07,z-.299];hi=[x+.299,y+1.8,z+.299];out=[]
 for xx in range(math.floor(lo[0]),math.ceil(hi[0])):
  for zz in range(math.floor(lo[2]),math.ceil(hi[2])):
   for yy in range(math.floor(lo[1]),math.ceil(hi[1])):
    st=block((xx,yy,zz));name=parse_state(st)[0]
    if name.endswith('_door')or name.endswith('_carpet')or name in ['minecraft:short_grass','minecraft:fern','minecraft:oxeye_daisy','minecraft:dandelion','minecraft:bamboo','minecraft:stone_button']:continue
    for bb in boxes(st):
     v=[bb[i]+[xx,yy,zz][i%3]for i in range(6)]
     if all(lo[i]<v[i+3]-1e-5 and hi[i]>v[i]+1e-5 for i in range(3)):out.append([xx,yy,zz,st])
 return out
@functools.lru_cache(None)
def free(x,z,floor):return any(bb[4]>=1 and bb[0]<=.2 and bb[3]>=.8 and bb[2]<=.2 and bb[5]>=.8 for bb in boxes(block((x,floor,z))))and not hit(x+.5,floor+1,z+.5)
def flood(valid,start):
 seen=set();queue=collections.deque([start])
 while queue:
  q=queue.popleft()
  if q in seen or q not in valid:continue
  seen.add(q);x,z=q;queue.extend([(x+1,z),(x-1,z),(x,z+1),(x,z-1)])
 return seen
from collections import defaultdict
nodes=defaultdict(set);states={}
for (x,y,z),st in blocks.items():
 if S.support_cube(block((x,y+1,z))):continue
 if parse_state(st)[0]in ['minecraft:water','minecraft:bamboo'] or S.family(st)in['groundcover','flower','leaves','banner','button','pot','potted','chain','pane']:continue
 for top in set(bb[4]for bb in boxes(st)):
  yy=round(y+top,3)
  if not hit(x+.5,yy,z+.5):nodes[x,z].add(yy);states[x,yy,z]=st
spawn=sp['spawn_local'];start=(spawn[0],float(spawn[1]),spawn[2]);queue=collections.deque([start]);seen=set()
while queue:
 p=queue.popleft()
 if p in seen:continue
 x,y,z=p
 if y not in nodes.get((x,z),()):continue
 seen.add(p)
 for X,Z in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
  for Y in nodes.get((X,Z),()):
   delta=abs(Y-y)
   if delta<=.51 or delta<=1.01 and ('_stairs' in states.get(p,'')or'_stairs'in states.get((X,Y,Z),'')):queue.append((X,Y,Z))
entrychecks=[];usechecks=[]
for bd in sp['buildings']:
 q=bd['entry_world'];ok=tuple(q)in seen;entrychecks.append({'id':bd['id'],'pos':q,'reachable':ok})
 if not ok:errors.append(['entry',bd['id'],q,hit(q[0]+.5,q[1],q[2]+.5)])
landmarkchecks=[]
for l in sp.get('landmarks',[]):
 ok=tuple(l['pos'])in seen;landmarkchecks.append({**l,'reachable':ok})
 if not ok:errors.append(['landmark',l['id'],l['pos']])
for u in sp['uses']:
 q=u['pos'];ok=tuple(q)in seen;usechecks.append({**u,'reachable':ok})
 if not ok:errors.append(['use',u['id'],q,hit(q[0]+.5,q[1],q[2]+.5)])
# Explicit small-step ascent sampling supplements the coarser cell-centre graph.
stairs=[]
for flight in sp['stairs']:
 prev=flight['start_y'];bad=[]
 for x,_,z in flight['path']:
  tops=[]
  for xx in range(math.floor(x-.299),math.ceil(x+.299)):
   for zz in range(math.floor(z-.299),math.ceil(z+.299)):
    for yy in range(math.floor(prev)-2,math.floor(prev)+2):
     for bb in boxes(block((xx,yy,zz))):
      if xx+bb[0]<x+.299 and xx+bb[3]>x-.299 and zz+bb[2]<z+.299 and zz+bb[5]>z-.299 and prev-.51<=yy+bb[4]<=prev+.51:tops.append(yy+bb[4])
  y=max(tops)if tops else prev;hh=hit(x,y,z)
  if not tops or hh:bad.append({'at':[x,y,z],'hits':hh,'supported':bool(tops)})
  prev=y
 stairs.append({'id':flight['id'],'samples':len(flight['path']),'end_y':prev,'errors':bad})
 if bad or abs(prev-flight['end_y'])>.01:errors.append(['stair',flight['id'],len(bad),prev])
# Falling bank materials need a real support block.
for q,st in blocks.items():
 if st.split('[')[0] in ['minecraft:sand','minecraft:gravel'] and not S.support_cube(block((q[0],q[1]-1,q[2]))):errors.append(['sediment_support',q])
# All source water has a bottom and a solid or source-water lateral enclosure.
water_bad=[];cascade_faces=[]
water_columns={(x,z):y for x,z,y in sp.get('river_water_columns',[])}
for q,st in blocks.items():
 if st.startswith('minecraft:water['):
  x,y,z=q
  for dx,dy,dz in [(0,-1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]:
   v=block((x+dx,y+dy,z+dz))
   if not(S.support_cube(v)or v.startswith('minecraft:water[')):
    downstream=water_columns.get((x+dx,z+dz))
    if dy==0 and downstream is not None and downstream<y and y-downstream<=1:cascade_faces.append([q,[dx,dy,dz]])
    else:water_bad.append([q,[dx,dy,dz],v])
if water_bad:errors.append(['water_enclosure',len(water_bad),water_bad[:10]])
for en in f['entities']:
 e=en['nbt'];q=tuple(int(e[k])for k in ['TileX','TileY','TileZ']);d=S.DIRS[['south','west','north','east'][int(e['facing'])]];back=tuple(q[i]-d[i]for i in range(3))
 if not S.support_cube(block(back))or block(q)!='minecraft:air':errors.append(['painting',q,block(q)])
from vanilla_preview import applications
for st in set(blocks.values()):
 try:assert applications(st)
 except Exception as e:errors.append(['model',st,str(e)])
spatial_checks={}
if sp.get('case_id')=='Taisho16':
 hm=json.loads((R/'heightmap.json').read_text());canopy={(x,z)for(x,y,z),st in blocks.items()if '_leaves['in st};main_checks=[]
 for rr in sp['routes']:
  if rr.get('hierarchy')!='main':continue
  failures=[];cells=rr['cells'];width=rr['clear_width'];radius=width//2
  for i,(x,z)in enumerate(cells):
   a=cells[max(0,i-1)];b0=cells[min(len(cells)-1,i+1)];dx,dz=b0[0]-a[0],b0[1]-a[1]
   cross=[(x,z+j)if abs(dx)>abs(dz)else(x+j,z)for j in range(-radius,radius+1)]
   good=sum(any(word in block((X,hm[Z][X],Z))for word in ['cobblestone','andesite','gravel','planks','stone_bricks'])for X,Z in cross)
   if good<width:failures.append({'at':[x,z],'paved_cells':good,'required':width})
  main_checks.append({'id':rr['id'],'nominal_width':width,'sections':len(cells),'incomplete':failures})
 spatial_checks={'main_cross_sections':main_checks,'canopy_columns':len(canopy),'north_canopy_fraction':round(sum(z<82 for x,z in canopy)/(320*82),4),'scope':'Paved cross-section coverage is separate from approximate body connectivity. Not a client walking test.'}
 (R/'spatial_checks.json').write_text(json.dumps(spatial_checks,indent=2))
report={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'non_air':len(blocks),'entries':entrychecks,'landmarks':landmarkchecks,'use_points':len(usechecks),'use_checks':usechecks,'navigation_nodes':len(seen),'stair_checks':stairs,'intentional_cascade_faces':len(cascade_faces),'water_boundary_errors':len(water_bad),'errors':errors,'block_entities':len(be),'paintings':len(f['entities']),'official_model_states':len(set(blocks.values())),'scope':'Final NBT readback; approximate 0.6 x 1.8 body with doors treated open; terrain connectivity allows stair-mediated one-block centre transitions; stair flights sampled separately. Not game collision or lighting verification.','game':'pending','aesthetic':'pending'}
(R/(group+'_audit.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'group':group,'entries':entrychecks,'uses':len(usechecks),'errors':errors},ensure_ascii=False));sys.exit(bool(errors))
