from build_case import *
def write_report(path, report):
 if path:
  with path.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)

from vendor.inspect_build import load_build,Limits
from detail_lab import states
import gzip
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--output',type=Path,help='Optional new report path; old runs are read-only');a=ap.parse_args();d=C/'runs'/a.run
b=load_build(d/'building.nbt',Limits(cells=40000000,nodes=16000000));blocks=b.blocks;ad=json.loads((d/'adaptation.json').read_text());data=json.loads(gzip.decompress((d/'component_ownership.json.gz').read_bytes()));owners={tuple(q[:3]):data['owner_names'][q[3]] for q in data['xyz_owner']};checks=[]
def ck(name,ok,details=None):checks.append({'name':name,'pass':bool(ok),'details':details})
def area(r,y0,y1):
 x0,z0,x1,z1=xyrect(r);return [(x,y,z) for x in range(x0,x1) for y in range(y0,y1) for z in range(z0,z1)]
def bad_air(r,y0,y1):return [q for q in area(r,y0,y1) if q in blocks]
ck('independent_NBT_bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in blocks),{'size':b.size,'blocks':len(blocks)})
ck('all_states_registered',all(states.validate(v) for v in set(blocks.values())),len(set(blocks.values())))
ck('frozen_75_groups_401_windows',len(ad['openings'])==401 and len(set(o['group'] for o in ad['openings']))==75)
ck('all_401_sources_consumed',all(o['consumed'] for o in ad['openings']),[o['id'] for o in ad['openings'] if not o['consumed']])
missing=[o['id'] for o in ad['openings'] if not any('glass' in blocks.get(tuple(q),'') for q in o['cells'])]
ck('every_window_retains_glass',not missing,missing)
ck('113_ledges_87_planted',len(ad['ledges'])==113 and sum(l['planted'] for l in ad['ledges'])==87)
ledge_bad=[]
for l in ad['ledges']:
 for q in l['cells']:
  q=tuple(q);v=blocks.get(q,'');plant=blocks.get((q[0],q[1]+1,q[2]),'')
  if 'slab' not in v or (l['planted'] and 'leaves' not in plant):ledge_bad.append({'id':l['id'],'xyz':q,'actual':v,'plant':plant})
ck('ledge_trays_and_vegetation_present',not ledge_bad,ledge_bad[:20])
anchors=[]
for q,o in owners.items():
 if o.startswith('ledge.') and o.endswith('.tray'):
  if not any(owners.get((q[0]+dx,q[1],q[2]+dz),'').endswith('.anchor') for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):anchors.append(q)
ck('ledge_horizontal_anchor',not anchors,anchors[:20])
ck('V01_ground_not_excavated',all(q in blocks for q in area([18,26,34,38],3,4)))
va=bad_air([19,27,33,37],14,21 if ad.get('ceiling_landscape_revision') else 22);ck('V01_F2_atrium_air',not va,va[:20])
va=[]
for z0,z1,yt in [(26.5,37.5,22),(38.5,41.5,13),(42.5,47.5,22)]:va+=bad_air([44.5,z0,51.5,z1],4,yt)
ck('V02_air_and_bridge_underpass_4_5m',not va,va[:20])
ck('bridge_continuous_deck',all(q in blocks for q in area([44,38,52,42],13,14)))
for door in ad['doors']:
 q=area(door['rect'],door['y'][0],door['y'][1]);bad=[v for v in q if v in blocks];ck('entry_'+door['id'],not bad,bad[:10])
ck('7_roof_equipment_ids',len(ad['equipment'])==7)
ck('roof_equipment_bearing',all((q[0],q[1]-1,q[2]) in blocks for q,o in owners.items() if o.startswith('equipment.') and o.endswith(('.wall','.body','.mast')) and q[1]==next(e['bounds'][1] for e in ad['equipment'] if o.split('.')[1]==e['id'])))
ck('C1_C2_7_C3_5_stair_links',collections.Counter(v['core'] for v in ad['stairs'])=={'C1':7,'C2':7,'C3':5})
# Detect ceiling interference over every visible stair tread center at 2-block
# game height. This is geometric sampling, not a collision/engine certification.
head=[]
for q,o in owners.items():
 if o.startswith('stair.') and (o.endswith('.up1') or o.endswith('.up2')):
  for dy in [1,2]:
   v=blocks.get((q[0],q[1]+dy,q[2]))
   if v:head.append({'xyz':q,'at':dy,'other':owners.get((q[0],q[1]+dy,q[2]))})
ck('stair_tread_headroom_samples',not head,head[:25])
# Floor-level circulation centers, excluding core interior terminal route points.
corr=[]
for fi,f in enumerate(S['floors']):
 fy=yr(f['elevation'])
 for i,j,kind,id in f['cells']:
  if kind!='circulation':continue
  x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);q=(x0+2,fy,z0+2)
  if q in blocks or (q[0],fy+1,q[2]) in blocks or (q[0],fy-1,q[2]) not in blocks:corr.append({'floor':fi+1,'cell':[i,j],'xyz':q,'owner':owners.get(q)})
ck('corridor_cell_centers_clear_and_supported',not corr,corr[:25])
# All-floor access: flood walkable full-floor cells from the public corridor
# to a landing beside the stairs. Requires two game blocks of air; no stair
# climbing claim. This catches an outward-facing C3 entrance on upper floors.
route_access=[]
from collections import deque
for core in S['cores']:
 x0,z0,x1,z1=xyrect(core['rect'])
 for fi in range(core['max_floor']):
  fy=yr(S['floors'][fi]['elevation']);target=(x0+9,z0+2)
  # Main F1..F5 corridor at x16,z40; upper floors retain it as well.
  start=(12+Q(16),12+Q(48-40))
  def walk(q):
   x,z=q;v=blocks.get((x,fy-1,z));return v and states.support_cube(v) and (x,fy,z) not in blocks and (x,fy+1,z) not in blocks
  todo=deque([start]);seen={start}
  while todo:
   q=todo.popleft()
   if q==target:break
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
    nq=(q[0]+dx,q[1]+dz)
    if nq not in seen and walk(nq):seen.add(nq);todo.append(nq)
  route_access.append({'core':core['id'],'floor':fi+1,'reachable':target in seen})
ck('public_corridor_reaches_each_stair_landing',all(x['reachable'] for x in route_access),route_access)
# Adjacent frozen rectangles can share one quantized glass strip: record it.
merges=[]
for gid in sorted(set(o['group'] for o in ad['openings'])):
 os=sorted([o for o in ad['openings'] if o['group']==gid],key=lambda o:o['quantized_u'][0])
 for aa,bb in zip(os,os[1:]):
  if aa['quantized_u'][1]>=bb['quantized_u'][0]:merges.append({'a':aa['id'],'b':bb['id'],'source_gap_m':bb['source']['u0_m']-aa['source']['u1_m'],'voxel_gap':bb['quantized_u'][0]-aa['quantized_u'][1]})
ck('uniform_floor_quantization',max(abs(q['error_m']) for q in ad['quantization'])<=.21,ad['quantization'])
ck('whole_world_height',b.size[1]+64<=320,{'recommended_origin_y':64,'max_origin_y':320-b.size[1]})
result={'run':a.run,'status':'pass' if all(c['pass'] for c in checks) else 'needs_revision','NBT_sha256':hashlib.sha256((d/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'pass_count':sum(v['pass'] for v in checks),'total':len(checks),'thin_mullion_merges':merges,'game':'pending','limits':['no structural engineering','approximate state-box preview, no game collision/light/import test','static elevator shaft and doors','0.12m thin pane gaps may merge at 0.5m grid']}
write_report(a.output,result)
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','thin_mullion_merges']},ensure_ascii=False));print('failed',json.dumps([v for v in checks if not v['pass']],ensure_ascii=False));print('quantized_adjacent_merges',len(merges))

raise SystemExit(0 if result['status']=='pass' else 1)
