from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support')]
import create_states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];label=R.name+'_RailDepot01';out=ROOT/'review/previews'/label
if len(sys.argv)==2:
 from detail_lab.mesh import write_mesh
 b=load_build(R/'RailDepot01.nbt',Limits(cells=12_000_000,nodes=30_000_000,decoded_bytes=128*1024*1024))
 from types import SimpleNamespace
 from rail_mesh import append_tracks
 v=SimpleNamespace(size=b.size,blocks={p:s for p,s in b.blocks.items() if not s.startswith('create:track[')})
 write_mesh(v,R/'RailDepot01.nbt',out/'scene')
 print(append_tracks(b,R/'RailDepot01.nbt',out/'scene')['triangles'],flush=True)
else:
 import render_egl_site as egl
 egl.ROOT=ROOT/'review';egl.main(label,sys.argv[2])
