"""Same-source technical diagrams from independently re-read final NBT."""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import export_structure
from hafusion.site_scene import SiteScene
from hafusion.design_handoff import compile_handoff
from detail_lab import states
from detail_lab.mesh import write_mesh
import render_egl_site as egl
R=C/'runs'/sys.argv[1];O=C/'review/diagrams'/sys.argv[1];O.mkdir(parents=True,exist_ok=True)
rb=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));B=rb.blocks;sp=json.loads((R/'site_records.json').read_text());source_hash=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
def col(s):return states.color(s) if s else (245,242,233)
def save_grid(a,title,name,scale=20):
 im=Image.fromarray(np.asarray(a,np.uint8)).resize((len(a[0])*scale,len(a)*scale),Image.Resampling.NEAREST)
 out=Image.new('RGB',(max(620,im.width+60),im.height+100),(248,246,240));out.paste(im,(30,60));d=ImageDraw.Draw(out);d.text((30,18),title,font=font,fill=(45,58,56));out.save(O/name)
# Whole-town floor atlases: every building uses its own actual ground elevation.
for level in [0,1]:
 a=np.full((rb.size[2],rb.size[0],3),240,np.uint8)
 for h in sp['buildings']:
  if level>=h['floors']:continue
  fy=h['g']+level*h.get('floor_step',7)
  for z in range(h['z'],h['z']+h['d']):
   for x in range(h['x'],h['x']+h['w']):
    s=next((B[(x,y,z)] for y in range(fy+3,fy,-1) if (x,y,z) in B),None)
    a[z,x]=col(s) if s else (218,198,156)
 im=Image.fromarray(a).resize((rb.size[0]*8,rb.size[2]*8),Image.Resampling.NEAREST);d=ImageDraw.Draw(im)
 for h in sp['buildings']:
  if level<h['floors']:d.text((h['x']*8,h['z']*8-20),h['id'],font=font,fill=(20,40,40))
 for r in sp['connections']:
  if level==0:d.line([(p[0]*8,p[2]*8) for p in r['path']],fill=(210,86,52),width=3)
 im.save(O/f'floor_{level+1}.png')
h=sp['buildings'][0];x0,z0=h['x']-2,h['z']-2;x1,z1=h['x']+h['w']+2,h['z']+h['d']+2;y0,y1=h['g'],29; section_x=h['x']+2
# Section along x=18 through H01's real stair lane.
a=np.full((y1-y0,z1-z0,3),245,np.uint8)
for y in range(y0,y1):
 for z in range(z0,z1):a[y1-1-y,z-z0]=col(B.get((section_x,y,z)))
save_grid(a,f'H01 / SECTION X={section_x} / stair + floor opening','section.png',24)
# Four elevations, exact same block scale; nearest non-air state wins per pixel.
for face in ['south','north','east','west']:
 axis='x' if face in ['south','north'] else 'z';umin,umax=(x0,x1) if axis=='x' else (z0,z1)
 ds=list(range(z0,z1)) if axis=='x' else list(range(x0,x1))
 if face in ['south','east']:ds=ds[::-1]
 a=np.full((y1-y0,umax-umin,3),245,np.uint8)
 for y in range(y0,y1):
  for u in range(umin,umax):
   for dep in ds:
    q=(u,y,dep) if axis=='x' else (dep,y,u)
    if q in B:a[y1-1-y,u-umin]=col(B[q]);break
 if face in ['north','east']:a=a[:,::-1]
 save_grid(a,'H01 / '+face.upper()+' ELEVATION / equal scale',f'elevation_{face}.png',24)
# Structured HAF 0.4 handoff plans, separately from the already-built case consumer.
handoffs=[]
for h in sp['buildings']:
 roomrows=[r for r in sp['rooms'] if r['building']==h['id']];rooms=[]
 for i,r in enumerate(roomrows):
  bounds=r['bounds_xyz'];ep=next((v['inside'] for v in sp['entrances'] if v['building']==h['id']),None) if i==0 else [bounds[0]+2,r['standing_y'],bounds[2]+2]
  rooms.append(dict(id=r['id'],floor_id=r['id'],function=h['use'],bounds_xyz=bounds,entrances=[ep],color_intent='neutral' if h['use']=='clinic' else 'warm'))
 use=dict(home='home',cafe='restaurant',grocer='market',clinic='clinic',community='civic',koban='office')[h['use']]
 spec=dict(schema_version='0.4',project_id=h['id'],route='original',primary_use=use,secondary_uses=[],identity_features=dict(home=['living','kitchen','sleeping'],cafe=['counter','tables','reading'],grocer=['shelves','checkout','stock'],clinic=['reception','waiting','exam_beds'],community=['welcome','activities','library'],koban=['desk','visitor_seat','records'])[h['use']],style='japanese_traditional' if h.get('floor_step')==6 else 'modern',coordinates=dict(unit='block',up='Y',north='-Z'),storeys_total=h['floors'],storeys_assumption=True,interior_level='L2',authorized_scope=dict(editable_regions=[[h['x']-4,0,h['z']-4,h['x']+h['w']+4,48,h['z']+h['d']+4]],locked_component_ids=[]),floor_levels=[dict(id=r['id'],floor_y=r['standing_y'],upper_floor_y=r['standing_y']+h.get('floor_step',7)-1,min_clear_height=4) for r in roomrows],rooms=rooms,circulation_keepouts=[],proposed_modules=[],lighting={})
 handoffs.append(compile_handoff(spec))
(R/'handoff_plans.json').write_text(json.dumps(handoffs,ensure_ascii=False,indent=2))
# Exploded display: keep each block's X/Z, add a documented vertical display offset.
h=sp['buildings'][0];ex=SiteScene((30,60,32));offsets=[]
for (x,y,z),s in B.items():
 if x0<=x<x1 and z0<=z<z1 and y0<=y<29:
  off=0 if y<h['g']+h.get('floor_step',7) else 9 if y<h['g']+h.get('floor_step',7)*2 else 18
  ex.set((x-x0+2,y-y0+2+off,z-z0+2),s,'H01.exploded')
out=O/'exploded_diagram.nbt';export_structure(ex,out,include_air=False)
er=load_build(out,Limits(cells=40_000_000,nodes=16_000_000));label=sys.argv[1]+'_exploded';dest=C/'review/previews'/label;dest.mkdir(parents=True,exist_ok=True);write_mesh(er,out,dest/'scene')
cams=[dict(id='exploded',eye=[77,60,90],target=[14,25,13],width=1200,height=1600,spanX=50,spanZ=66.667,ortho=True)]
cp=O/'exploded_cameras.json';cp.write_text(json.dumps(cams));egl.ROOT=C/'review';egl.main(label,cp)
(O/'provenance.json').write_text(json.dumps(dict(source_nbt_sha256=source_hash,section_x=section_x,facades='H01 only; original block states, no textures',floor_plans='All buildings; original floor heights; topmost state in floor +1..+3',exploded='H01 only; y display offsets 0,9,18; X/Z unchanged; NOT construction NBT',handoff='12 HAF 0.4 planning consumer results; actual geometry separately verified'),indent=2))
print('technical views and 12 handoffs complete')
