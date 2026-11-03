from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support')]
import industrial_states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];label=R.name+'_Substation01';out=ROOT/'review/previews'/label
if len(sys.argv)==2:
 from detail_lab.mesh import write_mesh
 b=load_build(R/'Substation01.nbt',Limits(cells=12_000_000,nodes=30_000_000,decoded_bytes=128*1024*1024))
 print(write_mesh(b,R/'Substation01.nbt',out/'scene')['triangles'],flush=True)
else:
 import render_egl_site as egl
 egl.ROOT=ROOT/'review';egl.main(label,sys.argv[2])
