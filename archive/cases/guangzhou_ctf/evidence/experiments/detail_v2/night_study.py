"""Fixed night-pattern experiment on an immutable V1; working axes, not compass."""
from pathlib import Path
import json,sys,importlib.util,shutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
from study import ROOT,CASE,HAF,Scene,load_build,Limits,M,export,render,dump,sha

def adapter():
 sp=importlib.util.spec_from_file_location('ctf_v1_adapter',CASE/'src/build_case.py')
 mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);return mod

def build():
 c=adapter();p=json.loads((CASE/'research/parameters.json').read_text());model=c.shape(p)
 h,masks=c.masks(model);b=load_build(CASE/'runs/V1/building.nbt',Limits(cells=2_000_000))
 s=Scene(b.size,max_cells=2_000_000)
 for q,v in b.blocks.items():s.set(q,v,'V1.preserved')
 changes=[];skipped=[]
 def lamp(q,mat,owner):
  old=s.blocks.get(q)
  if any('glass_pane' in b.blocks.get((q[0]+dx,q[1],q[2]+dz),'') for dx,dz in c.NORMALS.values()):
   skipped.append({'p':q,'reason':'would alter adjoining pane connection','component':owner});return
  if old is not None and old!='minecraft:gray_concrete':
   skipped.append({'p':q,'existing':old,'component':owner});return
  state=M(mat)
  if old!=state:
   s.set(q,state,owner);changes.append({'p':q,'before':old,'after':state,'component':owner})
 # Two visible faces are a local hypothesis. No geographic azimuth is claimed.
 # One row at 198 m is a test anchor within the approx. 185–210 m evidence interval.
 for side in ['south','west']:
  dx,dz=c.NORMALS[side]
  for x,z in sorted(masks[101]):
   if (x+dx,z+dz) not in masks[101] and (x-2*dx,z-2*dz) in masks[101]:
    lamp((x-2*dx,101,z-2*dz),'glowstone','lighting.facade_band.'+side)
  # Upper vertical accents: recessed light cells, preserving original fins and glass.
  for y in range(226,265):
   for x,z in sorted(masks[y]):
    u=x if dz else z
    if u%4 or (x+dx,z+dz) in masks[y]:continue
    if y>h[(x,z)]-2:continue
    q=(x-2*dx,y,z-2*dz)
    if h.get((q[0],q[2]),0)>y:
     lamp(q,'sea_lantern','lighting.upper_vertical.'+side)
 nbt=export(s,'night_pattern_candidate',{
  'status':'partial lighting-layout experiment; not accepted V2',
  'source_ids':['U02','P06','LPA01'],'fixed_pattern_not_random':True,
  'working_faces':['+Z','-X'],'geographic_north':None,
  'band_anchor_y':101,'band_anchor_m':198,'anchor_is_estimate':True,
  'band_observation_interval_m':[185,210],
  'roof_geometry_changed':False,'room_lights_changed':False,
  'other_faces':'preserved V1; reference-to-face mapping pending',
  'crown_vertical_extent':'prototype; not an as-built fixture survey'})
 read=load_build(nbt,Limits(cells=2_000_000))
 actual={q for q in set(b.blocks)|set(read.blocks) if b.blocks.get(q)!=read.blocks.get(q)}
 assert actual=={tuple(v['p']) for v in changes},'Unexpected geometry/state change'
 assert all(b.blocks[q]==read.blocks[q] for q in b.blocks if 'glass' in b.blocks[q] or 'wall[' in b.blocks[q])
 dump(ROOT/'runs/night_pattern_candidate/diff.json',{'changes':changes,'skipped':skipped,'changed_cells':len(actual),'only_declared_lights_changed':True,'glazing_and_fins_unchanged':True,'baseline':sha(CASE/'runs/V1/building.nbt')})
 return nbt

def views():
 whole={'width':900,'height':2250,'ortho':True,'spanX':120,'spanZ':300,'fov':36,'concept':False}
 close={'width':1440,'height':1440,'ortho':True,'spanX':64,'spanZ':64,'fov':36,'concept':False}
 allv=[];roof=[]
 for tag,dx,dz in [('pos_z',0,1),('neg_z',0,-1),('pos_x',1,0),('neg_x',-1,0)]:
  eye=[40+dx*500,134,64+dz*500]
  for night in [False,True]:
   allv.append({**whole,'id':tag+('_night' if night else '_day'),'eye':eye,'target':[40,134,64],'night':night})
  roof.append({**close,'id':tag,'eye':[40+dx*500,242,64+dz*500],'target':[40,242,64]})
 return allv,roof

def share_v1_mesh(label):
 src=ROOT/'review/previews/v1_material_light/scene';dst=ROOT/'review/previews'/label/'scene'
 if not dst.exists():shutil.copytree(src,dst,copy_function=__import__('os').link)

def main():
 nbt=ROOT/'runs/night_pattern_candidate/building.nbt'
 if not nbt.exists():nbt=build()
 if not (nbt.parent/'diff.json').exists():raise ValueError('Candidate has no successful geometry-diff audit')
 allv,roof=views();v1=CASE/'runs/V1/building.nbt'
 share_v1_mesh('four_directions_v1');render(v1,'four_directions_v1',allv+[{**v,'id':'roof_'+v['id']} for v in roof])
 csp=importlib.util.spec_from_file_location('view_source',CASE/'review/render_case.py');cm=importlib.util.module_from_spec(csp);csp.loader.exec_module(cm)
 cams={v['id']:v for v in cm.cameras()}
 render(nbt,'night_pattern_candidate',[v for v in allv if v['night']]+[cams['night'],cams['night_detail'],cams['hero']])
 dump(ROOT/'night_outputs.json',{'candidate_nbt':str(nbt.relative_to(ROOT)),'geographic_north':None,'roof_changed':False,'views':allv+roof,'game_test':'pending'})

if __name__=='__main__':main()
