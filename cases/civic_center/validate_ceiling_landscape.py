"""Read final NBT, independently check intended deltas and physical interfaces."""
from build_case import *
def write_report(path, report):
 if path:
  with path.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)

from vendor.inspect_build import load_build,Limits
from detail_lab import states
from collections import deque,Counter
import gzip,numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--output',type=Path,help='Optional new report path; old runs are read-only');a=ap.parse_args();d=C/'runs'/a.run

def read(path):
 b=load_build(path/'building.nbt',Limits(cells=40000000,nodes=16000000));o=json.loads(gzip.decompress((path/'component_ownership.json.gz').read_bytes()));return b,{tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']}
b,own=read(d);old,oo=read(C/'runs/v03_r13_lighting');B=b.blocks;ad=json.loads((d/'adaptation.json').read_text());rv=ad['ceiling_landscape_revision'];checks=[]
def ck(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'details':detail})
protected=[q for q,o in oo.items() if o.startswith(('window.','ledge.','screen.','stair.','interior2.'))]
recessto={tuple(v['to']) for v in rv['recessed_slab_fixtures']}
connections=[q for q in protected if 'glass_pane[' in old.blocks[q] and old.blocks[q].split('[')[0]==B.get(q,'').split('[')[0] and old.blocks[q]!=B.get(q)]
bad=[q for q in protected if B.get(q)!=old.blocks[q] and q not in recessto and q not in connections];ck('frozen_windows_ledges_stairs_and_interior_exact',not bad,{'count':len(protected),'bad':bad[:20],'connection_only_updates':len(connections)})
recessfrom={tuple(v['from']) for v in rv['recessed_slab_fixtures']};recessto={tuple(v['to']) for v in rv['recessed_slab_fixtures']};bad=[]
for q in old.blocks.keys()|B.keys():
 if old.blocks.get(q)==B.get(q):continue
 o=oo.get(q,'air');n=own.get(q,'air');x,y,z=q
 if q in recessfrom or q in recessto or q in connections:continue
 if o=='air' and n=='ceiling4.panel':continue
 if o.startswith(('garden.','lighting3.garden.')) or o=='lighting3.entry_path':continue
 if 60<=x<140 and 58<=z<116 and (o=='air' or o.startswith('site.')) and (n=='air' or n.startswith(('landscape4.','lighting4.'))):continue
 bad.append({'xyz':q,'before':o,'after':n})
ck('only_declared_ceiling_and_forecourt_changes',not bad,bad[:25])
cb=[]
for x,y,z in rv['ceiling_cells']:
 if B.get((x,y,z))!='minecraft:smooth_quartz' or not states.support_cube(B.get((x,y+1,z),'minecraft:air')):cb.append([x,y,z])
ck('new_lower_ceiling_beneath_existing_upper_floor',not cb and len(rv['ceiling_cells'])>1000,{'new_cells':len(rv['ceiling_cells']),'bad':cb[:10]})
lamps=[q for q,v in B.items() if v in ['minecraft:sea_lantern','minecraft:glowstone'] and own.get(q,'').startswith(('lighting.','lighting3.','lighting4.'))]
drops=[]
for x,y,z in lamps:
 if y not in [12,21,30,38,46,54,62]:continue
 if not states.support_cube(B.get((x,y+1,z),'minecraft:air')):continue
 n=sum(states.support_cube(B.get((x+dx,y,z+dz),'minecraft:air')) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
 if n<2:drops.append([x,y,z])
ck('no_cubic_ceiling_lamps_hanging_below_finish',not drops,{'recessed_into_existing_slab':len(recessto),'protrusions':drops})
roomlights=[]
for r in I['rooms']:
 fy=yr(r['floor_elevation_m']);top=yr(r['floor_elevation_m']+r['floor_to_floor_height_m']);mask=set()
 for i,j in r['occupied_cells']:
  x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
 ls=[q for q in lamps if (q[0],q[2]) in mask and fy-1<=q[1]<=top-1]
 if r['id']=='104':ls=[q for q in lamps if (q[0],q[2]) in mask and 3<=q[1]<=22]
 roomlights.append({'id':r['id'],'floor':r['floor'],'emissive_blocks':len(ls)})
ck('all_39_functional_spaces_have_active_lights',len(roomlights)==39 and all(r['emissive_blocks']>0 for r in roomlights),roomlights)
mask=set()
for i,j,*_ in S['floors'][0]['cells']:
 x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
bad=[q for q,o in own.items() if o.startswith('landscape4.') and q[1]>=4 and (q[0],q[2]) in mask]
ck('landscape_outside_ground_floor_footprint',not bad,bad[:20])
water={tuple(q) for q in rv['water']};bad=[]
for x,y,z in water:
 if 'water[' not in B.get((x,y,z),'') or not states.support_cube(B.get((x,y-1,z),'minecraft:air')):bad.append([x,y,z])
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=x+dx,y,z+dz
  if q not in water and not states.support_cube(B.get(q,'minecraft:air')):bad.append(q)
ck('pond_sources_contained_by_floor_and_bank',bool(water) and not bad,{'water_cells':len(water),'bad':bad[:20]})
bad=[]
for s in rv['bamboo_stems']:
 x,y,z=s['base'];h=s['height']
 if B.get((x,y-1,z))!='minecraft:moss_block' or any(not B.get((x,Y,z),'').startswith('minecraft:bamboo[') for Y in range(y,y+h)):bad.append(s)
ck('bamboo_native_and_grounded',len(rv['bamboo_stems'])>=15 and not bad,{'stems':len(rv['bamboo_stems']),'bad':bad})
pathbad=[]
for x,z in rv['path_cells']:
 if not states.support_cube(B.get((x,3,z),'minecraft:air')) or any((x,y,z) in B for y in [4,5,6]):pathbad.append([x,z])
ck('full_declared_path_widths_clear',not pathbad,pathbad[:25])
def walk(q):
 x,z=q;return states.support_cube(B.get((x,3,z),'minecraft:air')) and all((x,y,z) not in B for y in [4,5,6])
start=(81,113);todo=deque([start]);seen={start}
while todo:
 x,z=todo.popleft()
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=x+dx,z+dz
  if 60<=q[0]<140 and 12<=q[1]<116 and q not in seen and walk(q):seen.add(q);todo.append(q)
targets={'main_entry':(64,54),'east_entry':(124,54),'park_passage':(108,14),'pond_seating':(96,107),'pergola':(94,70)};ck('entrances_park_and_stay_areas_connected',all(q in seen for q in targets.values()),{k:q in seen for k,q in targets.items()})
ck('landscape_light_fixtures_inset_or_thin',all(q[1]<=3 or 'end_rod' in B[q] for q,o in own.items() if o.startswith(('lighting4.path','lighting4.pond','lighting4.pergola'))))
# The same preview grid is diagnostic, not a Minecraft lighting certification.
def lightstats(run,rb):
 p=C/'review/previews'/run/'scene';meta=json.loads((p/'scene.json').read_text());assert meta['source_nbt_sha256']==hashlib.sha256((C/'runs'/run/'building.nbt').read_bytes()).hexdigest();field=np.fromfile(p/'blocklight.bin',np.uint8).reshape((rb.size[2],rb.size[1],rb.size[0]));rows=[]
 for fi,f in enumerate(S['floors'],1):
  fy=yr(f['elevation']);vs=[]
  for i,j,*_ in f['cells']:
   x,z,_,_=xyrect([i*2,j*2,i*2+2,j*2+2]);x+=2;z+=2
   if (x,fy+1,z) not in rb.blocks and states.support_cube(rb.blocks.get((x,fy-1,z),'minecraft:air')):vs.append(int(field[z,fy+1,x]))
  rows.append({'floor':fi,'samples':len(vs),'positive_percent':round(100*sum(v>0 for v in vs)/len(vs),1),'mean_preview_level':round(sum(vs)/len(vs),2)})
 return {'emissive_blocks':len(meta['lamps']),'floors':rows}
before=lightstats('v03_r13_lighting',old);after=lightstats(a.run,b);ck('all_floor_preview_samples_above_90_percent',all(r['positive_percent']>=90 for r in after['floors']),after['floors'])
r={'run':a.run,'baseline':'v03_r13_lighting','NBT_sha256':hashlib.sha256((d/'building.nbt').read_bytes()).hexdigest(),'status':'pass' if all(v['pass'] for v in checks) else 'needs_revision','pass_count':sum(v['pass'] for v in checks),'total':len(checks),'checks':checks,'before':before,'after':after,'game':'pending'};write_report(a.output,r);print(json.dumps({k:v for k,v in r.items() if k!='checks'},ensure_ascii=False));print('FAILED',json.dumps([v for v in checks if not v['pass']],ensure_ascii=False))

raise SystemExit(0 if r['status']=='pass' else 1)
