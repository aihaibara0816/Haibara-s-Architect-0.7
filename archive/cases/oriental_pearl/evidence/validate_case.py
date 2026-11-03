from pathlib import Path
import sys,json,gzip,collections,math,hashlib
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from hafusion.review import review_views,status
from hafusion.case_io import dump,sha
C=Path(__file__).parent;run=C/'runs/v1_r04_final';b=load_build(run/'building.nbt',Limits(cells=40000000,nodes=16000000));p=json.loads((run/'params_used.json').read_text());s=p['scale'];o=p['origin'];checks=[]
def check(id,ok,details):checks.append({'id':id,'status':'pass' if ok else 'fail','details':details})
check('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),list(b.size))
check('state_vocabulary',all(states.validate(v) for v in set(b.blocks.values())),len(set(b.blocks.values())))
check('mast_vertical_coverage',all(any((x,y,z) in b.blocks for x in range(43,45) for z in range(43,45)) for y in range(166,222)),{'y_inclusive':[166,221]})
cs=json.loads((run/'components.json').read_text());balls=[x for x in cs if x['kind']=='sphere'];check('eleven_authored_spheres',len(balls)==11,len(balls))
check('world_budget_at_y64',64+b.size[1]<=320,{'min_y':64,'exclusive_upper_y':64+b.size[1],'world_exclusive_upper':320})
od=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()));own={tuple(r[:3]):od['owner_names'][r[3]] for r in od['xyz_owner']}
check('ownership_complete',set(own)==set(b.blocks),len(own))
# All six support feet have authored material on the ground and survive later assembly.
feet=[]
for i in range(3):
 for typ in ['main','slant']:
  cells=[q for q,v in own.items() if v==f'structure.{typ}_{i}'];feet.append({'id':f'{typ}_{i}','min_y':min(q[1] for q in cells),'count':len(cells)})
check('six_support_feet_reach_ground',all(r['min_y']<=4 for r in feet),feet)
# Main tube gap contract at a level between small pearls and Y beams.
y=round(o[1]+155*s);coords=[q for q in b.blocks if q[1]==y and math.hypot(q[0]+.5-o[0],q[2]+.5-o[2])<8];empty=sum((x,y,z) not in b.blocks for x in range(36,52) for z in range(36,52));check('shaft_interstitial_air',empty>=170,{'sample_y':y,'empty_of_256':empty})
for ball in balls:
 pref=ball['id']+'.';qs=[q for q,v in own.items() if v.startswith(pref) and '.interior.' not in v and '.lighting.' not in v and '.seam' not in v]
 expected=2*ball['radius_voxel'];width=max(q[0] for q in qs)-min(q[0] for q in qs)+1
 check(ball['id']+'_width',abs(width-expected)<=2,{'expected_unrounded':expected,'output_width':width,'tolerance_blocks':2})
# Compare same adapter revision and same input geometry; changes confined to big sphere envelopes.
a=load_build(C/'runs/v1_r04_glass_control/building.nbt',Limits(cells=40000000,nodes=16000000));diff=[q for q in set(a.blocks)|set(b.blocks) if a.blocks.get(q)!=b.blocks.get(q)]
def near_big(q):
 return any(abs(math.dist([v+.5 for v in q],x['center_voxel'])-x['radius_voxel'])<2.0 for x in balls[:3])
check('control_diff_confined_to_big_shells',all(near_big(q) for q in diff),len(diff))
for label,bb in [('glass_control',a),('layered',b)]:
 big=[q for q,v in own.items() if any(v.startswith(x['id']+'.') for x in balls[:3]) and '.interior.' not in v]
 n=sum('glass' in bb.blocks.get(q,'') for q in big);checks.append({'id':label+'_shell_glass_share','status':'observed','details':{'glass_cells':n,'envelope_sample_cells':len(big),'share':n/len(big)}})
# Coordinate connectivity is recorded, never described as game collision validation.
left=set(b.blocks);components=[]
while left:
 q=left.pop();todo=[q];n=0;lo=list(q);hi=list(q)
 while todo:
  q=todo.pop();n+=1;lo=[min(a,b) for a,b in zip(lo,q)];hi=[max(a,b) for a,b in zip(hi,q)]
  for dx,dy,dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   r=(q[0]+dx,q[1]+dy,q[2]+dz)
   if r in left:left.remove(r);todo.append(r)
 components.append({'cells':n,'lo':lo,'hi':hi})
components.sort(key=lambda x:-x['cells']);dump(run/'connectivity.json',components)
check('single_connected_build',len(components)==1,{'six_neighbor_components':len(components),'largest_share':components[0]['cells']/len(b.blocks),'note':'cell adjacency only; isolated shrubs/rods are separately listed'})
rr=json.loads((C/'review/previews/v1_r04_final/render_report.json').read_text());vc=review_views(rr,sha(run/'building.nbt'))
check('four_paired_45_degree_and_true_top',status(vc)=='pass',vc)
check('preview_hashes',all(sha(C/'review/previews/v1_r04_final'/r['image'])==r['sha256'] for r in rr),len(rr))
report={'case':'Oriental Pearl V1','run':'v1_r04_final','nbt_sha256':sha(run/'building.nbt'),'status':'fail' if any(x['status']=='fail' for x in checks) else 'pass','checks':checks,'visual_status':'needs_revision: triangle grid, curved-glass detail, current podium, night colour missing','game_status':'pending','scope':'File/geometry/preview integrity; not a visual fidelity score'}
dump(C/'review/validation.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
