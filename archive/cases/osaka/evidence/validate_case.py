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
od=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()));own={tuple(r[:3]):od['owner_names'][r[3]] for r in od['xyz_owner']}
check('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),list(b.size))
check('states',all(states.validate(v) for v in set(b.blocks.values())),len(set(b.blocks.values())))
check('ownership_complete',set(own)==set(b.blocks),len(own))
check('world_budget_y64',64+b.size[1]<=320,{'exclusive_y_max':64+b.size[1],'origin_y_max':320-b.size[1]})
tower=[q for q,v in own.items() if v.split('.')[0] in ['tower','roof']];check('occupied_height',max(q[1] for q in tower)+1-4==98,{'ground_local_y':4,'top_exclusive_y':max(q[1] for q in tower)+1})
check('clear_entry',all((x,y,z) not in b.blocks for x in range(56,61) for y in range(4,8) for z in range(24,28)),{'lo':[56,4,24],'hi_exclusive':[61,8,28]})
q=(44,63,26);check('recess_glass_backing',q not in b.blocks and 'glass' in b.blocks.get((44,63,27),'') and b.blocks.get((44,63,30))=='minecraft:gray_concrete',{'opening':q,'glass':[44,63,27],'backing':[44,63,30]})
check('non_mirrored_river_mass',own.get((67,60,57))=='tower.service_blade' and (67,60,17) not in b.blocks,'river service blade extends beyond main wall')
check('separate_tv_soffit',own.get((84,9,53))=='tv.soffit' and (84,7,53) not in b.blocks,'solid underside at y9, recessed passage below')
check('roof_rail_not_filled',own.get((45,101,33))=='roof.railing' and (45,101,36) not in b.blocks,'perimeter rail with central roof air')
for owner in ['facade.solid','facade.glass','interior.room_back','lighting.room','public.window_soffit','site.railing','tv.fine_mullion']:
 check(owner+'_present',owner in own.values(),sum(v==owner for v in own.values()))
# Coordinate connectivity is reported independently of collision.
left=set(b.blocks);comps=[]
while left:
 q=left.pop();todo=[q];n=0;lo=list(q);hi=list(q)
 while todo:
  q=todo.pop();n+=1;lo=[min(a,c) for a,c in zip(lo,q)];hi=[max(a,c) for a,c in zip(hi,q)]
  for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   r=tuple(q[i]+d[i] for i in range(3))
   if r in left:left.remove(r);todo.append(r)
 comps.append({'cells':n,'lo':lo,'hi':hi})
comps.sort(key=lambda x:-x['cells']);dump(run/'connectivity.json',comps);check('single_cell_component',len(comps)==1,{'count':len(comps),'largest':comps[:12],'scope':'voxel adjacency, not collision'})
rr=json.loads((C/'review/previews'/FINAL/'render_report.json').read_text());v=review_views(rr,sha(run/'building.nbt'));check('four_paired_views_true_top',status(v)=='pass',v);check('preview_hashes',all(sha(C/'review/previews'/FINAL/r['image'])==r['sha256'] for r in rr),len(rr))
samples=[]
for name,lo,hi in [('facade',(32,46,24),(54,76,33)),('tv',(77,4,43),(89,33,66)),('deck',(25,2,59),(46,11,72))]:
 size=tuple(hi[i]-lo[i] for i in range(3));ss=Scene(size);picked={tuple(q[i]-lo[i] for i in range(3)):v for q,v in b.blocks.items() if all(lo[i]<=q[i]<hi[i] for i in range(3))};ss.blocks=picked
 out=C/'samples'/name;out.mkdir(parents=True,exist_ok=True);
 with tempfile.TemporaryDirectory() as td:
  tmp=Path(td)/'building.nbt';m=export_structure(ss,tmp,include_air=False)
  if (out/'building.nbt').exists():assert (out/'building.nbt').read_bytes()==tmp.read_bytes(), 'Sample content changed; archive old samples first'
  else:(out/'building.nbt').write_bytes(tmp.read_bytes())
 rb=load_build(out/'building.nbt',Limits(cells=40000000,nodes=16000000));check('sample_'+name,rb.blocks==picked,{'source_nbt_sha256':sha(run/'building.nbt'),'source_lo':lo,'source_hi_exclusive':hi,'cells':len(picked)});samples.append({'id':name,'source_lo':lo,'source_hi_exclusive':hi,**m})
dump(C/'samples/manifest.json',samples)
report={'case':'Osaka V1','run':FINAL,'nbt_sha256':sha(run/'building.nbt'),'status':'fail' if any(x['status']=='fail' for x in checks) else 'pass','checks':checks,'visual_status':'needs_revision: facade modules, side details, roof and plan estimates','game_status':'pending','scope':'file, explicit geometric contracts and preview integrity; not fidelity score'}
dump(C/'review/validation.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'fail':[x for x in checks if x['status']=='fail']},ensure_ascii=False))
