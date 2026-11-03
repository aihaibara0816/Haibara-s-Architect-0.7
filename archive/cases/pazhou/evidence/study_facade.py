"""Three comparable, real NBT samples cropped from the delivered V2 wing.
Not a game screenshot. Colour-only control and layered treatment share a camera.
"""
from pathlib import Path
import sys,json,gzip,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import dump
from vendor.inspect_build import load_build
from vendor.voxel_core import export_structure
from detail_lab.mesh import write_mesh
from facade_layers import apply
C=Path(__file__).resolve().parent
p=json.loads((C/'params.json').read_text())
old=C/'runs/v2b_03_final';rb=load_build(old/'building.nbt')
data=json.loads(gzip.decompress((old/'component_ownership.json.gz').read_bytes()))
owners={tuple(v[:3]):data['owner_names'][v[3]] for v in data['xyz_owner']}
roi_lo=(31,38,44);roi_hi=(44,59,68);size=tuple(z-a for a,z in zip(roi_lo,roi_hi))
common={'width':1100,'height':1100,'spanX':30,'spanZ':30,'ortho':True,'fov':36,'concept':True,'sun_day':[.6,.9,-.8]}
cameras=[dict(common,id='corner_flat',eye=[43,24,-32],target=[6,10,11]),
 dict(common,id='front_flat',eye=[6,10,-70],target=[6,10,11],spanX=25,spanZ=25),
 dict(common,id='top_slice',eye=[6,80,12],target=[6,10,12],cutY=7,spanX=29,spanZ=29)]
dump(C/'review/facade_sample_cameras.json',cameras)
records=[]
for mode,label in [('original','sample_r01_A_original'),('colour','sample_r01_B_colour'),('layered','sample_r01_C_layered')]:
 b=Builder(rb.size);b.s.blocks=dict(rb.blocks);b.s.owners=dict(owners)
 if mode!='original':apply(b,p['tower'],p['layered_facade'],mode);b.finish()
 sample=Builder(size)
 for q,s in b.s.blocks.items():
  if all(a<=v<z for v,a,z in zip(q,roi_lo,roi_hi)):
   sample.s.set(tuple(v-a for v,a in zip(q,roi_lo)),s,b.s.owners[q])
 run=C/'runs'/label
 if run.exists():raise ValueError('Immutable sample '+label)
 run.mkdir();meta=export_structure(sample.s,run/'building.nbt',include_air=False)
 read=load_build(run/'building.nbt');assert read.blocks==sample.s.blocks
 # Preserve the complete-building connection state at the cropped edge.
 dump(run/'sample.json',dict(mode=mode,roi_lo=roi_lo,roi_hi_exclusive=roi_hi,nbt=meta,edge_connections='preserved from full building; may change after neighbour updates in game'))
 mesh=write_mesh(read,run/'building.nbt',C/'review/previews'/label/'scene')
 records.append({'label':label,'mode':mode,'nbt_sha256':mesh['source_nbt_sha256'],'blocks':len(read.blocks)})
dump(C/'review/facade_samples.json',records)
print(json.dumps(records))
