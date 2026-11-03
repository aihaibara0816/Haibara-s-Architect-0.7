from pathlib import Path
import json,gzip,sys,argparse,hashlib
from collections import Counter,deque
C=Path(__file__).resolve().parents[1];R=C.parents[1];sys.path[:0]=[str(R),str(R/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
def validate(run):
 out=C/'runs'/run;b=load_build(out/'building.nbt',Limits(cells=40000000,nodes=16000000));p=json.loads((out/'params_used.json').read_text());checks=[]
 data=json.loads(gzip.decompress((out/'component_ownership.json.gz').read_bytes()));own={tuple(r[:3]):data['owner_names'][r[3]] for r in data['xyz_owner']};B=b.blocks
 def add(name,ok,details):checks.append({'id':name,'status':'pass' if ok else 'fail','details':details})
 def cells(box):
  a,c,d,e,f,g=box
  for x in range(a,e):
   for y in range(c,f):
    for z in range(d,g):yield(x,y,z)
 def solid(q):return q in B and states.boxes(B[q])==((0,0,0,1,1,1),) and not states.transparent(B[q])
 manifest=json.loads((out/'manifest.json').read_text());add('file_hash',hashlib.sha256((out/'building.nbt').read_bytes()).hexdigest()==manifest['sha256'],manifest['sha256'])
 add('sparse_no_air',all(v!='minecraft:air' for v in B.values()),len(B));add('owner_coverage',set(own)==set(B),len(own))
 add('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in B),b.size)
 for st in set(B.values()):states.validate(st)
 add('known_blockstates',True,len(set(B.values())))
 spire=[q for q in B if own[q].startswith('tower.spires')];tips={x:max(q[1] for q in spire if q[0]==x)+1 for x in [36,52]}
 add('two_spires_height',len({q[0] for q in spire})==2 and all(y-p['grade_y']==182 for y in tips.values()),tips)
 supported={x:solid((x,147,64)) for x in [36,52]};add('spire_base_support',all(supported.values()),supported)
 # Each path tests full width, solid floor and two whole cells of clear headroom.
 failures=[];sampled=0
 for r in json.loads((out/'paths.json').read_text()):
  x0,z0,x1,z1=r['bounds'];fy=r['floor_y']
  for x in range(x0,x1):
   for z in range(z0,z1):
    sampled+=1
    if not solid((x,fy-1,z)) or any((x,y,z) in B for y in range(fy,fy+2)):failures.append([r['id'],x,z,own.get((x,fy,z))])
 add('whole_width_site_paths',not failures,{'sampled':sampled,'failures':failures[:50]})
 # Entrance is stepped: test landing at Y4, then half-step cell at Z76.
 bad=[q for q in cells([42,4,73,48,7,77]) if q in B]
 add('main_portal_clear',not bad,{'width':6,'height':3,'occupied':bad[:10]})
 mods=json.loads((out/'module_consumption.json').read_text());bad=[];actual={}
 for m in mods:
  prefix='module.'+m['component_id'];qs=[q for q,o in own.items() if o.startswith(prefix+'.')];actual[m['component_id']]=len(qs);bb=m['bounds_xyz']
  if not qs:bad.append([m['component_id'],'missing'])
  for q in qs:
   if not all(bb[i]<=q[i]<bb[i+3] for i in range(3)):bad.append([m['component_id'],'outside_bounds',q])
 add('resolved_modules_consumed',not bad,{'counts':actual,'failures':bad[:20]})
 plan=json.loads((out/'resolved_plan.json').read_text());bad=[]
 for keep in plan['input_snapshot']['circulation_keepouts']:
  for q in cells(keep):
   if q in B:bad.append([q,own[q]])
 add('demo_circulation_clear',not bad,bad[:30])
 bad=[];columns=0
 for f in p['synthetic_levels']:
  fy=f['floor_y'];cy=f['upper_floor_y']-2;fid=f['id'];lamps=[q for q,o in own.items() if o=='interior.'+fid+'.flush_light']
  if not lamps:bad.append([fid,'no_lights'])
  for q in lamps:
   if q[1]!=cy or not solid((q[0],cy+1,q[2])):bad.append([q,'not_flush_supported'])
  for x,z in [(36,56),(36,72),(53,56),(53,72)]:
   qs=[q for q,o in own.items() if o=='interior.'+fid+'.visual_column' and q[0]==x and q[2]==z]
   if qs:
    columns+=1
    if not all(own.get((x,y,z))=='interior.'+fid+'.visual_column' for y in range(fy,cy)) or not solid((x,fy-1,z)) or not solid((x,cy,z)):bad.append([fid,x,z,'column_gap'])
 add('flush_lights_and_two_layers',not bad,{'columns':columns,'failures':bad})
 lamps=json.loads((out/'lamps.json').read_text());gone=[r for r in lamps if B.get(tuple(r['xyz']))!=states.make(r['material'])]
 add('lamp_survival',not gone,{'declared':len(lamps),'overwritten':len(gone),'first':gone[:10]})
 plants=json.loads((out/'plants.json').read_text());bad=[]
 for r in plants:
  x,y,z=r['root']
  if B.get((x,y,z))!=states.make('moss_block') or 'oak_log' not in B.get((x,y+1,z),''):bad.append(r)
 add('plant_root_support',not bad,{'plants':len(plants),'failures':bad})
 # Water is confined horizontally and has an opaque solid bottom.
 water=[q for q,s in B.items() if s.startswith('minecraft:water')];bad=[]
 for x,y,z in water:
  if not solid((x,y-1,z)):bad.append([x,y,z,'bottom'])
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   nq=(x+dx,y,z+dz)
   if nq not in B:bad.append([*nq,'edge'])
 add('water_containment',not bad,{'water_cells':len(water),'failures':bad[:20]})
 metrics={'blocks':len(B),'blockstates':len(set(B.values())),'lamps':sum(any(a in s for a in ['glowstone','sea_lantern','end_rod']) for s in B.values()),'modules':len(mods),'designed_rooms':len(plan['input_snapshot']['rooms']),'window_back_rooms':len(json.loads((out/'interiors.json').read_text())),'site_trees':len(plants),'visual_columns':columns}
 result={'run':run,'source_nbt_sha256':manifest['sha256'],'checks':checks,'metrics':metrics,'status':'pass' if all(x['status']=='pass' for x in checks) else 'needs_revision','game_status':'pending','limits':['No real tenant layout, lift mechanics or full 80-floor circulation','Path checks use conservative occupied cells; actual Minecraft collisions are pending','No structural calculation or actual illumination certification']}
 (out/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();r=validate(a.run);sys.exit(0 if r['status']=='pass' else 1)
