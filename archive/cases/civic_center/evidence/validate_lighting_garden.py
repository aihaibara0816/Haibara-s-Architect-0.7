"""Independent revision diff, native bamboo, entry access and preview-light checks."""
from build_case import *
from vendor.inspect_build import load_build,Limits
from detail_lab import states
import numpy as np,gzip
from collections import deque,Counter
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--output');a=ap.parse_args();d=C/'runs'/a.run;base=C/'runs/v03_r10_public'
def read(p):
 b=load_build(p/'building.nbt',Limits(cells=40000000,nodes=16000000));o=json.loads(gzip.decompress((p/'component_ownership.json.gz').read_bytes()));return b,{tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']}
b,own=read(d);old,oo=read(base);B=b.blocks;checks=[];ad=json.loads((d/'adaptation.json').read_text());rv=ad.get('lighting_garden_revision',{})
def ck(name,ok,details=None):checks.append({'name':name,'pass':bool(ok),'details':details})
bad=[];modified=Counter()
for q in old.blocks.keys()|B.keys():
 if old.blocks.get(q)==B.get(q):continue
 o=oo.get(q,'air');n=own.get(q,'air');modified[n.split('.')[0]]+=1
 if q not in old.blocks and n.startswith(('lighting3.','garden.')):continue
 if n.startswith('lighting3.') and states.support_cube(B.get(q,'minecraft:air')) and states.support_cube(old.blocks.get(q,'minecraft:air')) and (o.startswith(('floor.','terrace.')) or '.floor.' in o or o.startswith('core.') and o.endswith('.wall')):continue
 bad.append({'xyz':q,'before':o,'after':n})
ck('only_declared_light_and_garden_changes',not bad,{'unexpected':bad,'changed_counts':modified})
ck('all_prior_lamps_retained',all(B.get(q)==s for q,s in old.blocks.items() if oo[q].startswith('lighting.')))
protected=[q for q,o in oo.items() if o.startswith(('window.','ledge.','screen.','stair.')) or o.startswith('interior2.') and '.floor.' not in o]
ck('windows_ledges_screens_stairs_furniture_columns_exact',all(B.get(q)==old.blocks[q] for q in protected),len(protected))
mask=set()
for i,j,*_ in S['floors'][0]['cells']:
 x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
garden=[q for q,o in own.items() if o.startswith('garden.')];ck('garden_outside_ground_floor_footprint',bool(garden) and all((q[0],q[2]) not in mask for q in garden))
ck('two_actual_bamboo_gardens',len(rv.get('gardens',[]))==2 and len(rv.get('bamboo_stems',[]))>=20,len(rv.get('bamboo_stems',[])))
stem_bad=[]
for s in rv.get('bamboo_stems',[]):
 x,y,z=s['base'];h=s['height']
 if B.get((x,y-1,z))!='minecraft:moss_block' or any(not B.get((x,Y,z),'').startswith('minecraft:bamboo[') for Y in range(y,y+h)) or 'stage=1' not in B.get((x,y+h-1,z),''):stem_bad.append(s)
ck('bamboo_native_states_grounded_and_capped',bool(rv.get('bamboo_stems')) and not stem_bad,stem_bad)
supportbad=[]
for q,o in own.items():
 if o.startswith('garden.') and q[1]==4 and not states.support_cube(B.get((q[0],3,q[2]),'minecraft:air')):supportbad.append(q)
ck('garden_rims_benches_and_posts_supported',not supportbad,supportbad)
lampbad=[]
for f in rv.get('fixtures',[]):
 for q in f['cells']:
  x,y,z=q
  if f['type']=='ceiling' and not states.support_cube(B.get((x,y+1,z),'minecraft:air')):lampbad.append(q)
  if f['type'] in ['inset_floor','inset_slab','wall_inset'] and not states.support_cube(old.blocks.get(tuple(q),'minecraft:air')):lampbad.append(q)
ck('fixtures_supported_or_flush_replacements',bool(rv.get('fixtures')) and not lampbad,lampbad)
start=(82,100);target=(64,54);seen={start};todo=deque([start])
def walk(x,z):return states.support_cube(B.get((x,3,z),'minecraft:air')) and all((x,y,z) not in B for y in [4,5,6])
while todo:
 x,z=todo.popleft()
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=x+dx,z+dz
  if 60<=q[0]<=102 and 54<=q[1]<=108 and q not in seen and walk(*q):seen.add(q);todo.append(q)
ck('forecourt_reaches_main_door',target in seen)
def lightstats(run,rb):
 p=C/'review/previews'/run/'scene';meta=json.loads((p/'scene.json').read_text());assert meta['source_nbt_sha256']==hashlib.sha256((C/'runs'/run/'building.nbt').read_bytes()).hexdigest();field=np.fromfile(p/'blocklight.bin',np.uint8).reshape((rb.size[2],rb.size[1],rb.size[0]));rows=[]
 for fi,f in enumerate(S['floors'],1):
  fy=yr(f['elevation']);vs=[]
  for i,j,*_ in f['cells']:
   x,z,_,_=xyrect([i*2,j*2,i*2+2,j*2+2]);x+=2;z+=2
   if (x,fy+1,z) not in rb.blocks and states.support_cube(rb.blocks.get((x,fy-1,z),'minecraft:air')):vs.append(int(field[z,fy+1,x]))
  rows.append({'floor':fi,'samples':len(vs),'positive_percent':round(100*sum(v>0 for v in vs)/len(vs),1),'mean_preview_level':round(sum(vs)/len(vs),2)})
 return {'emissive_blocks':len(meta['lamps']),'floors':rows}
before=lightstats('v03_r10_public',old);after=lightstats(a.run,b)
ck('all_floor_sample_coverage_above_90_percent',all(r['positive_percent']>=90 for r in after['floors']),after['floors'])
ck('every_floor_improves_vs_R10',all(y['positive_percent']>x['positive_percent'] for x,y in zip(before['floors'],after['floors'])))
res={'run':a.run,'baseline':'v03_r10_public','NBT_sha256':hashlib.sha256((d/'building.nbt').read_bytes()).hexdigest(),'status':'pass' if all(c['pass'] for c in checks) else 'needs_revision','pass_count':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks,'before':before,'after':after,'game':'pending','limits':['Preview lightfield is a conservative 6-neighbor grid, not actual Minecraft light or lux.','Positive sample percentage does not certify gameplay safety or lighting compliance.','Bamboo leaves simplified in preview; native vanilla block state used in NBT.']}
dump(Path(a.output) if a.output else d/'lighting_garden_validation.json',res);print(json.dumps({k:v for k,v in res.items() if k in ['run','status','pass_count','total','before','after']},ensure_ascii=False));print('failed',json.dumps([c for c in checks if not c['pass']],ensure_ascii=False))
