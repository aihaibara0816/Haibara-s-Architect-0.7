"""Higher texture detail for ground-floor views; no extra scene objects."""
from pathlib import Path
import sys,os,json,copy,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT/'pydeps')]
import qilou_states
from vendor.inspect_build import load_build,Limits
from detail_lab.mesh import write_mesh
from vanilla_preview import apply
RUN=sys.argv[1];R=ROOT/'runs'/RUN
for id in ['N03','N08','S03','A1','A2','B3','D5','E4']:
 base=ROOT/'review/previews'/(RUN+'_'+id);src=R/(id+'.nbt');sp=json.loads((R/(id+'_spec.json')).read_text());b=load_build(src,Limits(cells=12_000_000,nodes=20_000_000));top=sp['floors'][1]if len(sp['floors'])>1 else 8
 b.blocks={q:s for q,s in b.blocks.items()if q[1]<=top};b.info=copy.deepcopy(b.info)
 if'entities_payload'in b.info:b.info['entities_payload']=[e for e in b.info['entities_payload']if int(e['nbt']['TileY'])<=top]
 out=ROOT/'review/previews'/(RUN+'_'+id+'_interior_detail');out.mkdir(exist_ok=True,parents=True);os.environ['TOWN_TEXTURE_GRID']='8';write_mesh(b,src,out/'base_scene');(out/'scene').mkdir(exist_ok=True);shutil.copy2(base/'scene/blocklight.bin',out/'scene/blocklight.bin');apply(b,out/'scene',src,out/'base_scene/scene.json')
 views=[v for v in json.loads((base/'cameras_full.json').read_text())if v['id']in['interior','interior_night']]
 for v in views:v['detail_scope']='ground-floor textures; source blocks cropped above ceiling; full-model block light retained'
 f=out/'views.json';f.write_text(json.dumps(views));subprocess.run([sys.executable,str(ROOT/'src/render_district.py'),RUN,'batch',out.name,str(f)],check=True)
 for v in views:shutil.copy2(out/(v['id']+'.png'),base/(v['id']+'.png'))
 print('detail done',id,flush=True)
