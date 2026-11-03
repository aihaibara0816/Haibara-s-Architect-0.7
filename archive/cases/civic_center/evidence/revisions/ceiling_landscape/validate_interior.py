"""Independent NBT comparisons and public-space access checks for this revision."""
from build_case import *
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from collections import deque,Counter
import gzip

ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
d=C/'runs'/args.run;base=C/'runs/v03_r06_final';checks=[]
def read(p):
 b=load_build(p/'building.nbt',Limits(cells=40000000,nodes=16000000));o=json.loads(gzip.decompress((p/'component_ownership.json.gz').read_bytes()))
 return b,{tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']}
b,owners=read(d);old,oldowners=read(base);ad=json.loads((d/'adaptation.json').read_text());rev=ad['interior_revision'];B=b.blocks
def ck(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'details':detail})
changed=[q for q in old.blocks.keys()|B.keys() if old.blocks.get(q)!=B.get(q)]
door={(x,y,31) for x in [117,118] for y in range(14,18)} if rev.get('internal_access_repair') else set()
connections=[];bad=[]
for q in changed:
 o=oldowners.get(q,'air');a=old.blocks.get(q,'');v=B.get(q,'')
 if o.startswith(('interior.','lighting.','floor.')) or o=='air':continue
 if o.startswith('terrace.') and o.endswith('.deck') and owners.get(q,'').startswith('lighting3.terrace.') and v=='minecraft:glowstone':continue
 if o.startswith('core.') and o.endswith('.wall') and owners.get(q,'').startswith('lighting3.core_inset.') and v=='minecraft:glowstone':continue
 if q in door and o=='core.C3.wall' and not v:continue
 if o.startswith('window.') and 'glass_pane[' in a and a.split('[')[0]==v.split('[')[0]:connections.append({'xyz':q,'before':a,'after':v});continue
 bad.append({'xyz':q,'owner':o,'before':a,'after':v})
ck('protected_building_geometry_preserved',not bad,{'unexpected_changes':bad,'window_connection_updates':len(connections),'changed_cells':len(changed)})
ck('frozen_window_and_ledge_records_exact',ad['openings']==json.loads((base/'adaptation.json').read_text())['openings'] and ad['ledges']==json.loads((base/'adaptation.json').read_text())['ledges'])
ck('no_old_scattered_furniture_remains',not any(o.startswith('interior.') for o in owners.values()))
rooms={r['id']:r for r in I['rooms']};masks={}
for rid,r in rooms.items():
 mask=set()
 for i,j in r['occupied_cells']:
  x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
 masks[rid]=mask
outside=[];floorbad=[]
for q,o in owners.items():
 if not o.startswith('interior2.'):continue
 rid=o.split('.')[1]
 if rid=='frame':continue
 if (q[0],q[2]) not in masks[rid]:outside.append((q,o))
 if '.floor.' in o and not oldowners.get(q,'').startswith('floor.'):floorbad.append((q,o))
ck('new_modules_inside_owned_room_cells',not outside,outside[:20]);ck('floor_finishes_replace_only_existing_slabs',not floorbad,floorbad[:20])
colbad=[]
for f in rev['frames']:
 x,y,z=f['xy_base'];w,h,dep=f['size']
 for X in range(x,x+w):
  for Z in range(z,z+dep):
   if not all((X,Y,Z) in B for Y in range(y-1,y+h+1)):colbad.append((X,y,Z))
ck('visual_columns_meet_floor_and_ceiling',len(rev['frames'])>0 and not colbad,{'count':len(rev['frames']),'bad':colbad})
ck('all_public_floors_have_visual_columns',set([1,2,3]).issubset({f['floor'] for f in rev['frames']}))
circbad=[];reachable={};ports=[];approaches=[]
for fi,f in enumerate(S['floors'],1):
 fy=yr(f['elevation'])
 def walk(q):
  x,z=q;v=B.get((x,fy-1,z));return v and states.support_cube(v) and all((x,Y,z) not in B for Y in [fy,fy+1])
 todo=deque([(44,28)]);seen={(44,28)}
 while todo:
  q=todo.popleft()
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   p=q[0]+dx,q[1]+dz
   if p not in seen and walk(p):seen.add(p);todo.append(p)
 reachable[fi]=seen
 for i,j,kind,id in f['cells']:
  if kind!='circulation':continue
  x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2])
  for x in range(x0,x1):
   for z in range(z0,z1):
    for y in [fy,fy+1,fy+2]:
     if owners.get((x,y,z),'').startswith('interior2.'):circbad.append((x,y,z))
 for rid,p in rev['room_access_ports'].items():
  if rooms[rid]['floor']==fi:ports.append({'room':rid,'reachable':(p[0],p[2]) in seen})
 for m in rev['modules']:
  if m['floor']!=fi or m['kind'] in ['pseudo_column','indoor_planter','shelf_partition','glazed_partition']:continue
  x0,y0,z0,x1,y1,z1=m['bounds'];near=[(x,z) for x in range(x0-1,x1+1) for z in range(z0-1,z1+1) if (x in [x0-1,x1] or z in [z0-1,z1])]
  approaches.append({'room':m['room'],'module':m['id'],'reachable':any(p in seen for p in near)})
ck('full_circulation_cells_clear_of_new_furniture',not circbad,circbad[:20])
ck('all_room_access_ports_reachable',len(ports)==39 and all(p['reachable'] for p in ports),ports)
ck('furniture_groups_have_reachable_approach',all(p['reachable'] for p in approaches),approaches)
ck('all_floor_zones_have_written_cells',all(z['painted_blocks']>0 for z in rev['zones']),{'zones':len(rev['zones'])})
ck('three_distinct_floor_finishes',len({B[q].split('[')[0] for q,o in owners.items() if o.startswith('interior2.') and '.floor.' in o})>=3)
kinds=Counter(m['kind'] for m in rev['modules']);byfloor={str(fi):Counter(m['kind'] for m in rev['modules'] if m['floor']==fi) for fi in range(1,8)}
ck('F1_continuous_service_and_public_seating',byfloor['1']['service_counter']>=2 and byfloor['1']['sofa']>=3)
ck('F3_community_uses_without_work_pods',byfloor['3']['work_pod']==0 and byfloor['3']['sofa']>=3 and byfloor['3']['activity_table']>=2 and byfloor['3']['workshop_table']>=2)
ck('F4_to_F7_work_and_break_groups',all(byfloor[str(f)]['work_pod']>0 and byfloor[str(f)]['sofa']>0 for f in range(4,8)))
res={'run':args.run,'baseline':'v03_r06_final','NBT_sha256':hashlib.sha256((d/'building.nbt').read_bytes()).hexdigest(),'status':'pass' if all(c['pass'] for c in checks) else 'needs_revision','pass_count':sum(c['pass'] for c in checks),'total':len(checks),'checks':checks,'module_counts':kinds,'floor_module_counts':byfloor,'connection_updates':connections,'omitted_candidates':rev['skipped_modules'],'limits':['Visual pseudo-columns only; no load-bearing or engineering claim.','Reachability tests 2-air-block cells on each floor; not game collision or seating usability.','Perimeter approach does not validate every chair.','Window positions and materials unchanged; neighboring pane connection arms recomputed.','No full fit-out, operational elevators or game import tested.']}
dump(d/'interior_validation.json',res)
print(json.dumps({k:v for k,v in res.items() if k in ['run','status','pass_count','total','module_counts']},ensure_ascii=False));print('FAILED',json.dumps([c for c in checks if not c['pass']],ensure_ascii=False))
