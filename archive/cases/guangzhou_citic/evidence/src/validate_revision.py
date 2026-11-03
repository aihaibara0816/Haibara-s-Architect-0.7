"""NBT-level scope, density, lighting and access evidence for the v2 feedback."""
from pathlib import Path
import json,sys,gzip,argparse
from collections import Counter,deque
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
def read(run):
 r=C/'runs'/run;b=load_build(r/'building.nbt',Limits(cells=40000000,nodes=16000000)).blocks
 d=json.loads(gzip.decompress((r/'component_ownership.json.gz').read_bytes()));o={tuple(q[:3]):d['owner_names'][q[3]] for q in d['xyz_owner']}
 return r,b,o
def validate(run):
 r,B,O=read(run);old,A,AO=read('V1_r04');plan=json.loads((r/'resolved_plan.json').read_text());spec=plan['input_snapshot'];checks=[]
 def add(id,ok,detail):checks.append(dict(id=id,status='pass' if ok else 'fail',details=detail))
 def emits(s):return any(t in s for t in ['glowstone','sea_lantern','end_rod'])
 oldlamps=sum(map(emits,A.values()));newlamps=sum(map(emits,B.values()))
 add('emitting_blocks_reduced',newlamps<=oldlamps*.65,{'before':oldlamps,'after':newlamps,'reduction':round(1-newlamps/oldlamps,4),'not_photometric_brightness':True})
 bad=[];delta=Counter()
 for q in set(A)|set(B):
  if A.get(q)==B.get(q):continue
  before=AO.get(q,'air');after=O.get(q,'air');delta[after.split('.')[0]]+=1
  interior=any(32<=q[0]<57 and 52<=q[2]<77 and f['floor_y']-1<=q[1]<f['upper_floor_y'] for f in spec['floor_levels'])
  lamp=emits(A.get(q,'')) or emits(B.get(q,''))
  if not interior and not lamp:bad.append([q,before,after])
 add('changes_within_lighting_and_interior_scope',not bad,{'changed_coordinates':sum(delta.values()),'by_new_owner':dict(delta),'unexpected':bad[:20]})
 protected=('tower.facade.','tower.crown.','tower.spires.','site.','podium.')
 changed=[q for q,o in AO.items() if o.startswith(protected) and A[q]!=B.get(q)]
 add('protected_exterior_and_site_unchanged',not changed,{'changed':changed[:20]})
 # Flood only two full clear cells over a solid floor: conservative, not game pathfinding.
 room_results=[];module_results=[]
 for f in spec['floor_levels']:
  y=f['floor_y'];fid=f['id'];walk=set()
  for x in range(33,56):
   for z in range(53,76):
    if (x,y,z) not in B and (x,y+1,z) not in B and states.boxes(B.get((x,y-1,z),'minecraft:air'))==((0,0,0,1,1,1),):walk.add((x,z))
  start=(44,70);seen={start} if start in walk else set();queue=deque(seen)
  while queue:
   x,z=queue.popleft()
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=(x+dx,z+dz)
    if q in walk and q not in seen:seen.add(q);queue.append(q)
  for room in spec['rooms']:
   if room['floor_id']!=fid:continue
   pts=room['entrances'];room_results.append({'id':room['id'],'reachable':any((q[0],q[2]) in seen for q in pts)})
  for m in plan['modules']:
   if m['bounds_xyz'][1]!=y:continue
   x0,_,z0,x1,_,z1=m['bounds_xyz'];faces=m.get('use_faces',[]);adj=[]
   if 'east' in faces:adj.extend((x1,z) for z in range(z0,z1))
   if 'west' in faces:adj.extend((x0-1,z) for z in range(z0,z1))
   if 'south' in faces:adj.extend((x,z1) for x in range(x0,x1))
   if 'north' in faces:adj.extend((x,z0-1) for x in range(x0,x1))
   reached=[q for q in adj if q in seen];module_results.append({'id':m['component_id'],'reachable_edge_samples':len(reached),'samples':reached[:3]})
 add('room_entries_connected',all(t['reachable'] for t in room_results),room_results)
 add('module_approach_connected',all(t['reachable_edge_samples'] for t in module_results),module_results)
 mods=json.loads((r/'module_consumption.json').read_text());oldmods=json.loads((old/'module_consumption.json').read_text())
 n=sum(o.startswith('module.') for o in O.values());oldn=sum(o.startswith('module.') for o in AO.values())
 add('richer_functional_groups',len(mods)>len(oldmods) and n>oldn,{'groups_before':len(oldmods),'groups_after':len(mods),'furniture_blocks_before':oldn,'furniture_blocks_after':n,'kinds':dict(Counter(m['kind'] for m in mods))})
 result={'run':run,'baseline':'V1_r04','checks':checks,'status':'pass' if all(c['status']=='pass' for c in checks) else 'needs_revision','limits':['Counts are not taste or measured illumination','Conservative cell flood does not establish stair/half-block game collisions','Four demonstration levels only; static lifts and L1 fragments remain']}
 (r/'revision_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();r=validate(a.run);sys.exit(0 if r['status']=='pass' else 1)
