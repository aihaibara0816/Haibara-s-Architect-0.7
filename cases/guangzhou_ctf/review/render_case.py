"""NBT-derived fixed cameras. No generative-image substitution."""
from pathlib import Path
import sys,json,argparse,shutil
ROOT=Path(__file__).resolve().parent;CASE=ROOT.parent;HAF=CASE.parents[1]
sys.path.insert(0,str(HAF/'support'))
from vendor.inspect_build import load_build,Build,Limits
from detail_lab.mesh import write_mesh
from vendor import render_egl

def cameras():
 t={'width':1600,'height':2600,'ortho':True,'spanX':184.6154,'spanZ':300,'fov':36,'concept':False}
 w={'width':1800,'height':1400,'ortho':True,'spanX':70,'spanZ':54.4444,'fov':36,'concept':False}
 return [
  {**t,'id':'hero','eye':[-240,185,480],'target':[40,131,53]},
  {**t,'id':'front','eye':[40,133,600],'target':[40,133,53]},
  {**t,'id':'opposite','eye':[290,177,-430],'target':[40,131,53]},
  {**t,'id':'side','eye':[-500,133,64],'target':[40,133,64]},
  {**t,'id':'night','eye':[-240,185,480],'target':[40,131,53],'night':True},
  {**w,'id':'crown','eye':[-100,267,220],'target':[40,238,64],'spanX':76,'spanZ':59.1111},
  {**w,'id':'setback','eye':[-150,190,210],'target':[27,169,67],'spanX':47,'spanZ':36.5556},
  {**w,'id':'facade','eye':[-70,110,230],'target':[37,103,78],'spanX':27,'spanZ':21},
  {**w,'id':'podium','eye':[-110,60,-150],'target':[40,16,31],'spanX':88,'spanZ':68.4444},
  {**w,'id':'base','eye':[-100,32,190],'target':[40,15,62],'spanX':82,'spanZ':63.7778},
  {**w,'id':'bridge','eye':[-95,10,44],'target':[36,14,44],'spanX':45,'spanZ':35},
  {**w,'id':'night_detail','eye':[-70,110,230],'target':[37,103,78],'spanX':37,'spanZ':28.7778,'night':True},
  {**w,'id':'podium_night','eye':[-110,60,-150],'target':[40,16,31],'spanX':88,'spanZ':68.4444,'night':True},
  {**w,'id':'plan','eye':[42,320,49.99],'target':[42,0,50],'spanX':116,'spanZ':90.2222,'cutY':31},
  {**w,'id':'window_cut','eye':[120,115,130],'target':[37,102,72],'spanX':29,'spanZ':22.5556,'minY':95,'cutY':110,'cutX':43,'minZ':68}
 ]

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--only');a=ap.parse_args();views=cameras()
 chosen=[v for v in views if not a.only or v['id'] in a.only.split(',')];nbt=CASE/'runs'/a.run/'building.nbt';b=load_build(nbt,Limits(cells=2_000_000));dest=ROOT/'previews'/a.run
 if not (dest/'scene/scene.json').exists():write_mesh(b,nbt,dest/'scene')
 render_egl.ROOT=ROOT;(ROOT/'cameras.json').write_text(json.dumps(views,indent=2));cropkeys=['minY','cutY','cutX','minZ'];plain=[v for v in chosen if not any(k in v for k in cropkeys)]
 previous=json.loads((dest/'render_report.json').read_text()) if (dest/'render_report.json').exists() else [];records=[]
 if plain:
  cp=dest/'cameras.json';cp.write_text(json.dumps(plain));render_egl.main(a.run,cp);records+=json.loads((dest/'render_report.json').read_text())
 for v in chosen:
  crop={k:v[k] for k in cropkeys if k in v}
  if not crop:continue
  cells={p:s for p,s in b.blocks.items() if p[0]<crop.get('cutX',b.size[0]) and crop.get('minY',0)<=p[1]<crop.get('cutY',b.size[1]) and p[2]>=crop.get('minZ',0)}
  cut=Build(b.size,cells,b.info,b.palette);tmp=ROOT/'previews'/(a.run+'__'+v['id']);write_mesh(cut,nbt,tmp/'scene');cp=tmp/'camera.json';cp.write_text(json.dumps([{k:x for k,x in v.items() if k not in crop}]))
  render_egl.main(tmp.name,cp);shutil.copyfile(tmp/(v['id']+'.png'),dest/(v['id']+'.png'));rec=json.loads((tmp/'render_report.json').read_text())[0];rec['crop']=crop;records.append(rec)
 merged={r['image']:r for r in previous};merged.update({r['image']:r for r in records});(dest/'render_report.json').write_text(json.dumps(list(merged.values()),indent=2));print('render complete',a.run,len(chosen),flush=True)
