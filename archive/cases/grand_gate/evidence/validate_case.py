from pathlib import Path
import sys,json,gzip,collections,hashlib,tempfile
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import Scene,export_structure
from detail_lab import states
from hafusion.review import review_views,status
from hafusion.case_io import dump,sha
C=Path(__file__).parent;FINAL='v1_r04_final';run=C/'runs'/FINAL;b=load_build(run/'building.nbt',Limits(cells=40000000,nodes=16000000));checks=[]
def check(id,ok,details):checks.append({'id':id,'status':'pass' if ok else 'fail','details':details})
od=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()));own={tuple(r[:3]):od['owner_names'][r[3]] for r in od['xyz_owner']};P=json.loads((run/'params_used.json').read_text())
check('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),list(b.size))
check('states',all(states.validate(v) for v in set(b.blocks.values())),len(set(b.blocks.values())))
check('ownership_complete',set(own)==set(b.blocks),len(own))
check('world_budget_y64',64+b.size[1]<=320,{'exclusive_y_max':64+b.size[1],'origin_y_max':320-b.size[1]})
check('occupied_height_88',max(q[1] for q in b.blocks)+1-P['ground_y']==88,'Y=3 ground, top cell Y=90, occupied height 88')
check('nineteen_floor_levels',len(P['podium']['floor_y'][:-1]+P['tower']['floor_y'][:-1])==19,'1–5 plus 6–19; roof excluded')
check('ground_through_route',all((x,y,z) not in b.blocks for x in range(69,74) for y in range(4,8) for z in range(17,50)),'coordinate clearance only; not game collision')
check('stair_landing_join',all((x,9,z) in b.blocks for x in range(46,51) for z in range(50,56)),'flight top at z55, landing z54..50')
check('stair_headroom',all((x,10,z) not in b.blocks and (x,11,z) not in b.blocks for x in range(46,51) for z in range(50,59)),'upper flight and landing two cells of clearance')
check('deck_join',all((x,9,z) in b.blocks for x in range(80,96) for z in range(50,55)),'second-level platform connects to truncated deck')
check('facade_layers',own.get((37,59,53))=='facade.main_fin' and 'glass' in b.blocks.get((38,59,52),'') and own.get((38,59,49))=='interior.backing','fin z53 / glass z52 / backing z49')
check('rear_core_asymmetry',own.get((40,60,18))=='tower.core' and (40,60,57) not in b.blocks,'rear projected core, no mirrored front projection')
check('three_green_bands',all(any(q[1]==y and o=='podium.green_wall' for q,o in own.items()) for y in [18,22,26]),'three parking levels, not four')
check('covered_eave_sources',all(own.get((q[0],q[1],q[2]+1))=='podium.green_wall' if q[2]==58 else own.get((q[0]-1,q[1],q[2]))=='podium.green_wall' for q,o in own.items() if o=='lighting.eave'),'each eave emitter has a plant block immediately in front')
check('soffit_separate_thin_state',any(o=='podium.soffit_seam' and 'iron_trapdoor' in b.blocks[q] and 'half=top' in b.blocks[q] for q,o in own.items()),'thin top trapdoor state below separate ceiling plate')
for o in ['facade.secondary_mullion','lighting.corner','lighting.fin_base','interior.synthetic_desk','podium.pier']:
 check(o,any(v==o for v in own.values()),sum(v==o for v in own.values()))
# Coordinate adjacency cannot establish collision or structural engineering validity.
left=set(b.blocks);comps=[]
while left:
 q=left.pop();todo=[q];n=0;lo=list(q);hi=list(q)
 while todo:
  q=todo.pop();n+=1;lo=[min(a,c) for a,c in zip(lo,q)];hi=[max(a,c) for a,c in zip(hi,q)]
  for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   r=tuple(q[i]+d[i] for i in range(3))
   if r in left:left.remove(r);todo.append(r)
 comps.append({'cells':n,'lo':lo,'hi':hi})
comps.sort(key=lambda x:-x['cells']);dump(run/'connectivity.json',comps);check('coordinate_connected',len(comps)==1,{'count':len(comps),'largest':comps[:10],'scope':'cell adjacency, not collision'})
rr=json.loads((C/'review/previews'/FINAL/'render_report.json').read_text());v=review_views(rr,sha(run/'building.nbt'));check('four_paired_views_true_top',status(v)=='pass',v);check('preview_hashes',all(sha(C/'review/previews'/FINAL/r['image'])==r['sha256'] for r in rr),len(rr))
samples=[]
for name,lo,hi in [('facade',(30,47,47),(52,74,55)),('podium',(30,13,54),(54,29,62)),('soffit',(36,2,47),(62,16,64))]:
 size=tuple(hi[i]-lo[i] for i in range(3));ss=Scene(size);picked={tuple(q[i]-lo[i] for i in range(3)):v for q,v in b.blocks.items() if all(lo[i]<=q[i]<hi[i] for i in range(3))};ss.blocks=picked;out=C/'samples'/name;out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td)/'building.nbt';m=export_structure(ss,tmp,include_air=False)
  if (out/'building.nbt').exists():assert (out/'building.nbt').read_bytes()==tmp.read_bytes(),'archive samples before changing'
  else:(out/'building.nbt').write_bytes(tmp.read_bytes())
 rb=load_build(out/'building.nbt',Limits(cells=40000000,nodes=16000000));check('sample_'+name,rb.blocks==picked,{'source_sha256':sha(run/'building.nbt'),'lo':lo,'hi_exclusive':hi,'cells':len(picked)});samples.append({'id':name,'source_lo':lo,'source_hi_exclusive':hi,**m})
dump(C/'samples/manifest.json',samples)
report={'case':'Hiroshima JP Building','run':FINAL,'nbt_sha256':sha(run/'building.nbt'),'status':'fail' if any(x['status']=='fail' for x in checks) else 'pass','checks':checks,'visual_status':'V1 review baseline; rear elevation, exact dimensions, louvre density and roof equipment remain approximate','game_status':'pending','scope':'file and explicit geometric contracts; not fidelity score'}
dump(C/'review/validation.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'fail':[x for x in checks if x['status']=='fail']},ensure_ascii=False))
