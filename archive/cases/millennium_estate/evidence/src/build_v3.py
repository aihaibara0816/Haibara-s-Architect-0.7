"""Local revision of final V2: 70% homes lit, isolated facade tones, nine pipes."""
from pathlib import Path
import sys,json,gzip,hashlib,collections,argparse,copy
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump,sha
from hafusion.design_handoff import compile_handoff
from vendor.inspect_build import load_build,Limits
from detail_lab import states
M=states.make
def rnd(key):return int(hashlib.sha256(key.encode()).hexdigest()[:12],16)/16**12
def build(run):
 source=C/'runs/V2_r05';read=lambda n:json.loads((source/(n+'.json')).read_text())
 p=read('params_used');p.update(version='V3',baseline='V2_r05',lighting_policy='Exactly 70% of homes lit; common and garden lighting retained; mixed flush glowstone/sea lantern and supported end rods.',facade_variation_policy='Isolated similar-tone blocks, NOT clustered aging patches; fixed coordinate seed.',lighting_coverage=.7)
 base=load_build(source/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
 data=json.loads(gzip.decompress((source/'component_ownership.json.gz').read_bytes()))
 owners={tuple(q[:3]):data['owner_names'][q[3]] for q in data['xyz_owner']}
 b=Builder(p['size_xyz'],p['seed'])
 for q,s in base.blocks.items():b.put(*q,s,owners[q])
 b.rooms=read('interiors');b.windows=read('windows');towers={t['id']:t for t in p['towers']}
 units=read('units');old_lit={u['id'] for u in units if u['lit']};selected=set()
 for t in p['towers']:
  us=[u for u in units if u['tower']==t['id']];quota=round(len(us)*.7)
  ranked=sorted(us,key=lambda u:(u['id'] not in old_lit,rnd(u['id']+'.v3.occupancy')))
  selected.update(u['id'] for u in ranked[:quota])
 for u in units:u['lit']=u['id'] in selected
 lamps=[];allowed={};restored=[]
 for l in read('lamps'):
  q=tuple(l['xyz'])
  if '.U' in l['owner']:
   b.put(*q,'white_concrete',l['owner'].split('.')[0]+'.ceiling');allowed[q]='private_lighting';restored.append(list(q))
  else:
   l['installation']='flush' if l['owner'].split('.')[0] in towers else 'retained_site'
   lamps.append(l)
 room_lights=[]
 for r in b.rooms:
  rid=r['id'];uid=rid.rsplit('.',1)[0]
  if uid not in selected:continue
  x,y,z,X,Y,Z=r['bounds_xyz'];cx,cz=(x+X)//2,(z+Z)//2
  candidates=sorted([(xx,zz) for xx in range(x,X) for zz in range(z,Z)],key=lambda q:(abs(q[0]-cx)+abs(q[1]-cz),q))
  candidates=[(xx,zz) for xx,zz in candidates if b.s.blocks.get((xx,y+3,zz))==M('white_concrete')]
  if not candidates:raise ValueError('No ceiling support: '+rid)
  rod=r['function'] in ['bedroom','study'] and rnd(rid+'.v3.rod')<.20
  rod_candidates=[q for q in candidates if all((q[0],yy,q[1]) not in b.s.blocks for yy in [y,y+1,y+2])]
  if rod and rod_candidates:
   xx,zz=rod_candidates[0];q=(xx,y+2,zz);mat='end_rod';s=M(mat,facing='down');install='ceiling_rod'
  else:
   xx,zz=candidates[0];q=(xx,y+3,zz);neutral=r['function'] in ['kitchen','bathroom','utility','study']
   if r['function'] in ['bedroom','living','living_dining','dining'] and rnd(uid+'.v3.cool_household')<.15:neutral=True
   mat='sea_lantern' if neutral else 'glowstone';s=M(mat);install='flush'
  owner=rid+'.light.v3';b.put(*q,s,owner);allowed[q]='private_lighting'
  l={'xyz':list(q),'material':mat,'owner':owner,'room_id':rid,'unit_id':uid,'installation':install,'floor_y':y,'color_intent':'neutral' if mat!='glowstone' else 'warm'}
  lamps.append(l);room_lights.append(l)
 # User explicitly overrode patch-based weathering: all selected accents are
 # isolated from other accents in the 6-neighbor lattice, stable at block scale.
 normalized={};palettes={};counts=collections.Counter()
 for q,o in owners.items():
  if o not in {t+'.facade' for t in towers}:continue
  t=towers[o.split('.')[0]];x,y,z=q;lx=x-t['x'];belt=(y-3)%5==4
  pale=(t['type']=='A' and 11<=lx<=20) or (t['type']=='B' and 13<=lx<=23)
  mat='smooth_sandstone' if belt or pale else 'yellow_terracotta'
  normalized[q]=mat;palettes[q]='cream' if belt or pale else 'warm';b.put(*q,mat,o)
  if base.blocks[q]!=M(mat):allowed[q]='facade_tone'
 offsets=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
 accents=set();variations=[]
 for q in sorted(normalized,key=lambda q:rnd(str(p['seed'])+str(q)+'.v3.tone_order')):
  key=str(p['seed'])+str(q);v=rnd(key+'.v3.tone');group=palettes[q]
  if v>=(.15 if group=='warm' else .09):continue
  if any(tuple(a+d for a,d in zip(q,off)) in accents for off in offsets):continue
  mat=('packed_mud' if rnd(key+'.v3.material')<.8 else 'terracotta') if group=='warm' else 'cut_sandstone'
  accents.add(q);b.put(*q,mat,owners[q]);allowed[q]='facade_tone';counts[mat]+=1
  variations.append({'xyz':list(q),'base':normalized[q],'material':mat,'owner':owners[q]})
 pipes=[];paths=set(map(tuple,read('paths')['cells_xz']))
 for t in p['towers']:
  candidates=[(-1,24,'east')] if t['type']=='A' else [(-1,17,'east'),(37,13,'west')]
  for n,(x,z,side) in enumerate(candidates,1):
   x+=t['x'];z+=t['z'];y0,y1=3,2+5*t['storeys'];oid=t['id']+f'.pipe.v3.{n}';dx,_,dz=states.DIRS[side]
   if (x,z) in paths:raise ValueError('Pipe blocks declared path')
   if not states.support_cube(b.s.blocks[x,y0-1,z]):raise ValueError('Pipe lacks ground support')
   brackets=[]
   for y in range(y0,y1):
    q=(x,y,z)
    if q in b.s.blocks:raise ValueError('Pipe collision '+str(q))
    arm=(y-7)%5==0
    if arm:
     if not states.support_cube(b.s.blocks[x+dx,y,z+dz]):raise ValueError('Pipe bracket lacks wall')
     brackets.append([x,y,z])
    b.put(*q,M('diorite_wall',**({side:'low'} if arm else {})),oid);allowed[q]='pipe'
   pipes.append({'id':oid,'tower':t['id'],'xz':[x,z],'y_range_exclusive':[y0,y1],'towards_wall':side,'brackets':brackets,'material':'diorite_wall','purpose':'Decorative stacked wet-zone pipe; no working plumbing'})
 # Final connections must not alter protected windows or exterior geometry.
 b.finish();diff=[]
 for q in sorted(base.blocks.keys()|b.s.blocks.keys()):
  before,after=base.blocks.get(q),b.s.blocks.get(q)
  if before==after:continue
  if q not in allowed:raise ValueError('Unauthorized changed block: '+str(q))
  diff.append({'xyz':list(q),'before':before,'after':after,'reason':allowed[q]})
 extra={'route':'original','approved_plan':'P01','units':len(units),'furniture_modules':len(read('module_consumption')),'lit_households':len(selected),'lighting_policy':p['lighting_policy'],'baseline_run':'V2_r05','baseline_sha256':sha(source/'building.nbt'),'pipe_stacks':len(pipes),'facade_accent_blocks':len(variations)}
 out=save_run(C,run,p,b,Path(__file__),extra)
 for n in ['stairs','entries','floor_levels','module_consumption','roof_parts','paths','doorway_cells','trees']:
  (out/(n+'.json')).write_bytes((source/(n+'.json')).read_bytes())
 specs=read('design_handoffs')
 for s in specs:
  s['lighting']={'coverage_override':'selected_spaces','override_reason':'用户指定住宅约70%覆盖；精确分配84/120户，公共交通灯保留。'}
 for n,obj in [('units',units),('lamps',lamps),('design_handoffs',specs),('resolved_plans',[compile_handoff(s) for s in specs]),('pipes',pipes),('revision_diff',diff)]:dump(out/(n+'.json'),obj)
 dump(out/'lighting_assignment.json',{'target_coverage':.7,'actual_lit':len(selected),'total_households':len(units),'preserved_previously_lit':len(selected&old_lit),'per_tower':dict(collections.Counter(u['tower'] for u in units if u['lit'])),'lamp_materials':dict(collections.Counter(l['material'] for l in lamps)),'private_lamp_installations':dict(collections.Counter(l['installation'] for l in room_lights)),'scope':'Coverage counts households, not blocks or window area. Every declared room in selected homes has one main fixture.','game_light_propagation':'pending'})
 dump(out/'facade_variation.json',{'policy':'Scattered similar-color single blocks; no connected accent patches; coordinate seeded','base_facade_blocks':len(normalized),'accent_blocks':len(variations),'palette_counts':dict(counts),'palette_groups':dict(collections.Counter(palettes.values())),'normalized_old_sandstone_patch_cells':sum(base.blocks[q]!=M(m) for q,m in normalized.items()),'visual_colors':'Untextured preview approximations, not sampled vanilla textures','cells':variations})
 dump(out/'provenance.json',{'source_baseline_sha256':sha(source/'building.nbt'),'approved_plan_sha256':sha(C/'input/approved_P01.json'),'status':'authored_case_revision','user_request':'70% homes lit; mixed fixtures; similar-colored blocks interspersed, explicitly no patches; selected diorite-wall pipes.','web_research_this_revision':False,'source_code':sha(Path(__file__)),'changed_counts':dict(collections.Counter(d['reason'] for d in diff))})
 print('RUN',out,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);build(ap.parse_args().run)
