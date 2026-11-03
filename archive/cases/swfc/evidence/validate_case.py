from pathlib import Path
import sys,json,gzip,collections,math,hashlib
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import Scene,export_structure
from detail_lab import states
from hafusion.review import review_views,status
from hafusion.case_io import dump,sha
C=Path(__file__).parent;FINAL='v1_r02_final';run=C/'runs'/FINAL;b=load_build(run/'building.nbt',Limits(cells=40000000,nodes=16000000));p=json.loads((run/'params_used.json').read_text());s=p['scale'];o=p['origin'];checks=[]
def check(id,ok,details):checks.append({'id':id,'status':'pass' if ok else 'fail','details':details})
check('bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),list(b.size))
check('states',all(states.validate(v) for v in set(b.blocks.values())),len(set(b.blocks.values())))
check('world_budget_at_y64',64+b.size[1]<=320,{'exclusive_upper_y':64+b.size[1],'origin_y_max':320-b.size[1]})
od=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()));own={tuple(r[:3]):od['owner_names'][r[3]] for r in od['xyz_owner']};check('ownership_complete',set(own)==set(b.blocks),len(own))
a=p['aperture'];rays=[];occupied=0
for y in range(math.ceil(o[1]+a['lower_m']*s),math.floor(o[1]+a['upper_m']*s)):
 h=(y+.5-o[1])/s;t=(h-a['lower_m'])/(a['upper_m']-a['lower_m']);w=(a['width_lower_m']*(1-t)+a['width_upper_m']*t)*s
 xs=[x for x in range(b.size[0]) if abs(x+.5-o[0])<w/2-.6]
 cells=[(x,y,z) for x in xs for z in range(b.size[2])];n=sum(q in b.blocks for q in cells);occupied+=n;rays.append({'y':y,'clear_width_blocks':len(xs),'occupied':n})
check('portal_through_air_all_stages',occupied==0,{'rays':rays,'note':'all z along interior aperture rays; boundary margin 0.6 blocks'})
check('portal_widens_upward',rays[-1]['clear_width_blocks']>rays[0]['clear_width_blocks'],[rays[0]['clear_width_blocks'],rays[-1]['clear_width_blocks']])
tower=[q for q,v in own.items() if v.split('.')[0] not in ('site','entry','podium')]
check('tower_height',abs(max(q[1] for q in tower)+1-o[1]-492*s)<1,{'occupied_top_exclusive':max(q[1] for q in tower)+1,'analytic_top':o[1]+492*s})
sections=[]
for h in [50,200,350,430,486]:
 y=math.floor(o[1]+h*s);qs=[q for q in tower if q[1]==y and abs(q[0]+.5-o[0])<1];zs=[q[2] for q in qs];sections.append({'h':h,'depth':max(zs)-min(zs)+1})
check('blade_depth_decreases',all(sections[i]['depth']>sections[i+1]['depth'] for i in range(len(sections)-1)),sections)
for owner in ['bridge.floor','bridge.soffit','bridge.ceiling','interior.backing','facade.mullion','lighting.windows','lighting.crown_slots']:
 check(owner+'_present',sum(v==owner for v in own.values())>0,sum(v==owner for v in own.values()))
left=set(b.blocks);comps=[]
while left:
 q=left.pop();todo=[q];n=0;lo=list(q);hi=list(q)
 while todo:
  q=todo.pop();n+=1;lo=[min(a,b) for a,b in zip(lo,q)];hi=[max(a,b) for a,b in zip(hi,q)]
  for dx,dy,dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
   r=(q[0]+dx,q[1]+dy,q[2]+dz)
   if r in left:left.remove(r);todo.append(r)
 comps.append({'cells':n,'lo':lo,'hi':hi})
comps.sort(key=lambda x:-x['cells']);dump(run/'connectivity.json',comps);check('single_cell_connected_component',len(comps)==1,{'count':len(comps),'largest':comps[:10],'scope':'cell adjacency, not game collision'})
rr=json.loads((C/'review/previews'/FINAL/'render_report.json').read_text());vc=review_views(rr,sha(run/'building.nbt'));check('paired_four_views_and_top',status(vc)=='pass',vc);check('preview_hashes',all(sha(C/'review/previews'/FINAL/r['image'])==r['sha256'] for r in rr),len(rr))
# Export exact same-scale crops from final NBT for practical in-game local testing.
samples=[]
for name,lo,hi in [('facade',(29,83,44),(46,111,55)),('corner',(43,75,34),(56,102,49)),('portal',(16,208,26),(57,233,47))]:
 size=tuple(hi[i]-lo[i] for i in range(3));ss=Scene(size);picked={tuple(q[i]-lo[i] for i in range(3)):v for q,v in b.blocks.items() if all(lo[i]<=q[i]<hi[i] for i in range(3))};ss.blocks=picked
 out=C/'samples'/name;out.mkdir(parents=True,exist_ok=True);m=export_structure(ss,out/'building.nbt',include_air=False);rb=load_build(out/'building.nbt',Limits(cells=40000000,nodes=16000000));check('sample_'+name,rb.blocks==picked,{'source_nbt_sha256':sha(run/'building.nbt'),'source_lo':lo,'source_hi_exclusive':hi,'cells':len(picked)});samples.append({'id':name,'source_lo':lo,'source_hi_exclusive':hi,**m})
dump(C/'samples/manifest.json',samples)
env=[q for q,v in own.items() if v.startswith('envelope.')];glass=sum('glass' in b.blocks[q] for q in env)
report={'case':'SWFC V1','run':FINAL,'nbt_sha256':sha(run/'building.nbt'),'status':'fail' if any(x['status']=='fail' for x in checks) else 'pass','checks':checks,'statistics':{'envelope_glass_cells':glass,'envelope_cells':len(env),'share':glass/len(env),'note':'not real opening ratio or fidelity score'},'visual_status':'needs_revision: coarse stair-stepped arcs, facade joints and site estimated','game_status':'pending','scope':'file, stated geometry and preview integrity only'}
dump(C/'review/validation.json',report);print(json.dumps({'status':report['status'],'checks':len(checks),'fail':[x for x in checks if x['status']=='fail'],'statistics':report['statistics']},ensure_ascii=False))
