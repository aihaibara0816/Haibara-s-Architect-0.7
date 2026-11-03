from pathlib import Path
import sys,json,math,collections,functools,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import taisho_states,nbtlib as n
from detail_lab import states as S
from vendor.voxel_core import parse_state
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];group=sys.argv[2];src=R/(group+'.nbt');b=load_build(src,Limits(cells=1000000,nodes=8000000));sp=json.loads((R/(group+'_spec.json')).read_text());f=n.load(src);errors=[];blocks=b.blocks;be={tuple(map(int,e['pos'])):e['nbt']for e in f['blocks']if'nbt'in e}
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
 name,_=parse_state(block(q));expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else name
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
    if name.endswith('_door')or name.endswith('_carpet'):continue
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
valid={(x,z)for x in range(b.size[0])for z in range(b.size[2])if free(x,z,2)};ground=flood(valid,(sp['spawn_local'][0],sp['spawn_local'][2]));upper=flood({(x,z)for x in range(b.size[0])for z in range(b.size[2])if free(x,z,8)},tuple(sp['upper_start']));usechecks=[];entrychecks=[]
for u in sp['uses']:
 x,y,z=u['pos'];ok=(x,z)in(ground if u['floor_block_y']==2 else upper);usechecks.append({**u,'reachable':ok})
 if not ok:errors.append(['use',u['id'],u['pos'],hit(x+.5,y,z+.5)])
for bd in sp['buildings']:
 q=[bd['entry'][i]+bd['origin'][i]for i in range(3)];ok=(q[0],q[2])in ground;entrychecks.append({'id':bd['id'],'pos':q,'reachable':ok})
 if not ok:errors.append(['entry',bd['id'],q])
stairs=[]
for path in sp['stairs']:
 prev=3.;bad=[]
 for x,_,z in path:
  tops=[]
  for xx in range(math.floor(x-.299),math.ceil(x+.299)):
   for zz in range(math.floor(z-.299),math.ceil(z+.299)):
    for yy in range(1,10):
     for bb in boxes(block((xx,yy,zz))):
      if xx+bb[0]<x+.299 and xx+bb[3]>x-.299 and zz+bb[2]<z+.299 and zz+bb[5]>z-.299 and prev-.51<=yy+bb[4]<=prev+.51:tops.append(yy+bb[4])
  y=max(tops)if tops else prev;hh=hit(x,y,z)
  if not tops or hh:bad.append({'at':[x,y,z],'hits':hh,'supported':bool(tops)})
  prev=y
 stairs.append({'samples':len(path),'end_y':prev,'errors':bad})
 if bad or abs(prev-9)>.01:errors.append(['stair',len(bad),prev])
for en in f['entities']:
 e=en['nbt'];q=tuple(int(e[k])for k in['TileX','TileY','TileZ']);d=S.DIRS[['south','west','north','east'][int(e['facing'])]];back=tuple(q[i]-d[i]for i in range(3))
 if not S.support_cube(block(back))or block(q)!='minecraft:air':errors.append(['painting',q,block(q)])
from vanilla_preview import applications
failed=[]
for st in set(blocks.values()):
 try:assert applications(st)
 except Exception as e:failed.append([st,str(e)])
errors+=failed
report={'source_nbt_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'non_air':len(blocks),'entries':entrychecks,'use_points':len(usechecks),'use_checks':usechecks,'stair_checks':stairs,'errors':errors,'block_entities':len(be),'paintings':len(f['entities']),'official_model_states':len(set(blocks.values())),'scope':'Final NBT readback, door-frame/bed/painting/light support; approximate 0.6 x 1.8 body, doors treated open. Not game collision verification.','game':'pending','aesthetic':'pending'}
(R/(group+'_audit.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items()if k not in['use_checks','stair_checks']},ensure_ascii=False));sys.exit(bool(errors))
