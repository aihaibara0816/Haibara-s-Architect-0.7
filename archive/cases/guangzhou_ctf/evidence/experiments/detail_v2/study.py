"""CTF V1 feedback experiments. Preserve release; export real NBT samples."""
from pathlib import Path
import sys,json,hashlib,shutil,argparse,importlib.util
from collections import Counter
ROOT=Path(__file__).resolve().parent;CASE=ROOT.parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from vendor.voxel_core import Scene,export_structure,parse_state
from vendor.inspect_build import load_build,Limits,Build
from detail_lab import states
from detail_lab.mesh import write_mesh
from vendor import render_egl
from hafusion.facade import add_skin
from hafusion.interiors import room_style,furnishing_cells
from hafusion.lighting import unit
M=states.make

def dump(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def place(s,p,mat,owner):
 if p in s.blocks:raise ValueError(('collision',p,s.owners[p],owner))
 s.set(p,M(mat),owner)
def export(s,name,notes=None):
 dest=ROOT/'runs'/name
 if dest.exists():raise ValueError('Use a new experiment directory; do not overwrite')
 dest.mkdir(parents=True);states.connect(s);meta=export_structure(s,dest/'building.nbt',3955,False)
 b=load_build(dest/'building.nbt',Limits(cells=2_000_000));assert b.blocks==s.blocks
 dump(dest/'inspection.json',{'nbt':meta,'materials':dict(Counter(parse_state(v)[0] for v in b.blocks.values())),'notes':notes or {},'game_test':'pending'})
 return dest/'building.nbt'

def facade(kind):
 s=Scene((28,18,16));floors=[1,4,6,9,11,14,16];roomlog=[]
 for x in range(1,27):
  for z in range(1,15):s.set((x,0,z),M('smooth_stone'),'sample.ground')
 for y in range(1,17):
  for x in range(3,24):
   fin='diorite_wall' if kind=='wall' or kind=='hybrid' and x in [4,22] else 'iron_bars'
   add_skin(s,x,y,4,'north',fin=fin,component='sample.front')
  for z in range(5,13):
   fin='diorite_wall' if kind=='wall' or kind=='hybrid' and z in [6,12] else 'iron_bars'
   add_skin(s,24,y,z,'east',fin=fin,component='sample.return')
  s.set((24,y,4),M('gray_stained_glass'),'sample.turn')
  s.set((25,y,4),M('diorite_wall' if kind!='bars' else 'iron_bars'),'sample.turn_fin')
  for x in range(3,25):s.set((x,y,11),M('gray_concrete'),'sample.backing')
 for y in floors:
  for x in range(3,25):
   for z in range(5,11):s.set((x,y,z),M('smooth_stone_slab',type='top'),'sample.floor')
 for row,y in enumerate(floors[:-1]):
  clear=floors[row+1]-y-1
  for bay,x in enumerate([4,9,14,19]):
   rid=f'floor{y}.bay{bay}';choice=room_style(20261023,rid,clear)
   # Same furnished rooms in every facade variant, independent of fin selection.
   for dx,dy,dz,mat in furnishing_cells(choice['style'],clear):
    q=(x+dx,y+1+dy,5+dz);assert q[1]<floors[row+1]
    place(s,q,mat,'room.'+rid+'.'+choice['style'])
   anchor=(x+2,floors[row+1]-1,6)
   lit=unit(20261023,rid,'sample-lit',namespace='ctf-detail-0.1')<.65
   if lit:place(s,anchor,choice['light'],'room.'+rid+'.lamp')
   roomlog.append({'id':rid,**choice,'lit':lit,'lamp':anchor if lit else None})
 return export(s,'facade_'+kind,{'rooms':roomlog,'fin':kind,'clearance':'1 or 2 full clear cells; not all rooms playable','scale':'same block scale as CTF V1'})

def beacon(s,kind,x,y,z):
 if kind=='glass_ring':
  for dx in [-1,0,1]:
   for dz in [-1,0,1]:
    s.set((x+dx,y-1,z+dz),M('smooth_quartz'),'beacon.support')
    if dx or dz:s.set((x+dx,y,z+dz),M('red_stained_glass_pane'),'beacon.red_casing')
  s.set((x,y,z),M('glowstone'),'beacon.light');s.set((x,y+1,z),M('red_stained_glass'),'beacon.red_cap')
 elif kind=='recessed_cap':
  s.set((x,y-1,z),M('glowstone'),'beacon.recessed_light');s.set((x,y,z),M('red_stained_glass'),'beacon.cap')
 elif kind=='torch':
  s.set((x,y-1,z),M('smooth_quartz'),'beacon.support');s.set((x,y,z),M('redstone_torch'),'beacon.light')
 else:raise ValueError(kind)

def beacon_samples():
 s=Scene((36,7,14))
 for x in range(1,35):
  for z in range(1,13):s.set((x,0,z),M('smooth_stone'),'sample.ground')
 for x,kind in [(6,'glass_ring'),(18,'recessed_cap'),(30,'torch')]:beacon(s,kind,x,2,7)
 return export(s,'beacon_board',{'positions_along_positive_x':['glass_ring','recessed_cap','torch'],'display_left_to_right':['torch','recessed_cap','glass_ring'],'occupied_footprints':[[3,3],[1,1],[1,1]],'interpretation':'Red lamp bodies; no blinking circuit or coloured radiance claim'})

def beacon_context(kind):
 b=load_build(CASE/'runs/V1/building.nbt',Limits(cells=2_000_000));s=Scene(b.size,max_cells=2_000_000)
 for q,v in b.blocks.items():s.set(q,v,'V1.preserved')
 x,z=39,75
 roof=max(y for xx,y,zz in b.blocks if xx==x and zz==z);y=roof+1
 beacon(s,kind,x,y,z)
 return export(s,'beacon_context_'+kind,{'base_nbt_sha256':sha(CASE/'runs/V1/building.nbt'),'beacon_anchor':[x,y,z],'placement':'scale experiment only; not confirmed real fixture location'})

def render(nbt,label,views,policy='material',crop=None):
 dest=ROOT/'review/previews'/label;b=load_build(nbt,Limits(cells=2_000_000))
 if crop:
  cells={p:s for p,s in b.blocks.items() if all(lo<=p[i]<hi for i,(lo,hi) in enumerate(crop))}
  b=Build(b.size,cells,b.info,b.palette)
 if not (dest/'scene/scene.json').exists():write_mesh(b,nbt,dest/'scene')
 dump(dest/'cameras.json',views);render_egl.ROOT=ROOT/'review';render_egl.main(label,dest/'cameras.json',policy)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build-only',action='store_true');a=ap.parse_args()
 assets=ROOT/'review/assets';assets.mkdir(parents=True,exist_ok=True)
 shutil.copy2(CASE/'review/assets/render_shader_reference.html',assets/'render_shader_reference.html')
 records={}
 for k in ['wall','bars','hybrid']:records['facade_'+k]=facade(k)
 records['beacon_board']=beacon_samples()
 for k in ['glass_ring','recessed_cap','torch']:records['beacon_context_'+k]=beacon_context(k)
 if a.build_only:return
 w={'width':1440,'height':1200,'ortho':True,'spanX':34,'spanZ':28.3333,'fov':36,'concept':False}
 facade_views=[{**w,'id':'oblique','eye':[58,25,-70],'target':[14,8,8]},
               {**w,'id':'front','eye':[14,8,-100],'target':[14,8,8]},
               {**w,'id':'night','eye':[58,25,-70],'target':[14,8,8],'night':True}]
 for k in ['wall','bars','hybrid']:render(records['facade_'+k],'facade_'+k,facade_views)
 render(records['facade_hybrid'],'rooms_cut',[{**w,'id':'cut','spanX':28,'spanZ':23.3333,'eye':[12,16,-45],'target':[13,7,8]}],crop=[(0,23),(0,14),(5,16)])
 b={'width':1800,'height':900,'ortho':True,'spanX':40,'spanZ':20,'fov':36,'concept':False}
 render(records['beacon_board'],'beacon_board',[{**b,'id':'day','eye':[38,18,-48],'target':[18,2,7]},{**b,'id':'night','eye':[38,18,-48],'target':[18,2,7],'night':True}])
 camera_spec=importlib.util.spec_from_file_location('ctf_cameras',CASE/'review/render_case.py');mod=importlib.util.module_from_spec(camera_spec);camera_spec.loader.exec_module(mod)
 cams={c['id']:c for c in mod.cameras()}
 roof={**w,'width':1440,'height':1200,'spanX':48,'spanZ':40,'id':'roof','eye':[-90,283,185],'target':[40,254,64],'night':True}
 for k in ['glass_ring','recessed_cap','torch']:
  render(records['beacon_context_'+k],'beacon_context_'+k,[roof,{**cams['night'],'width':1000,'height':1625}])
 v1=CASE/'runs/V1/building.nbt'
 render(v1,'v1_material_light',[cams['night_detail'],cams['night']])
 # No new roof geometry: isolate viewpoint as a cause before guessing a slope.
 roofviews=[{**roof,'night':False,'id':'z_face','eye':[40,250,320],'target':[40,245,64]},
            {**roof,'night':False,'id':'x_face','eye':[-250,250,64],'target':[40,245,64]},
            {**roof,'night':False,'id':'opposite','eye':[180,275,-160],'target':[40,245,64]}]
 render(v1,'roof_view_study',roofviews)
 dump(ROOT/'study_outputs.json',{'nbt':{k:str(v.relative_to(ROOT)) for k,v in records.items()},'preserved_v1':sha(v1),'model_mesh_imported':False,'roof_geometry_changed':False,'game_test':'pending'})
 print('detail study complete',flush=True)
if __name__=='__main__':main()
