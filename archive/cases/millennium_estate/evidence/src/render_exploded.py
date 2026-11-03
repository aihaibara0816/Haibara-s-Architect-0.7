"""Separate explanatory NBT: translate A1/F2 component layers, retain a reversible mapping."""
from pathlib import Path
import sys,json,argparse,hashlib,gzip
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(C/'src'),str(ROOT),str(ROOT/'support'),str(ROOT/'cases/namsan_tower/src')]
from vendor.inspect_build import load_build,Limits
from hafusion.classical import Builder
from vendor.voxel_core import export_structure
from detail_lab import mesh
from render_case import grille_boxes
import render_egl_site as egl
def main(run):
 r=C/'runs'/run;d=C/'review/previews'/(run+'_exploded');d.mkdir(parents=True,exist_ok=True)
 par=json.loads((r/'params_used.json').read_text());tz=par['towers'][0]['z']-4;tx=par['towers'][0]['x']-3;tw=par['towers'][0]['w']+6;td=par['towers'][0]['d']+8
 own=json.loads(gzip.decompress((r/'component_ownership.json.gz').read_bytes()));names=own['owner_names'];owned={tuple(q[:3]) for q in own['xyz_owner'] if names[q[3]].startswith('A1.')}
 src=load_build(r/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));b=Builder([tw,21,td]);mapping={7:1,8:6,9:7,10:8,11:13,12:18}
 for (x,y,z),s in src.blocks.items():
  if (x,y,z) in owned and tx<=x<tx+tw and tz<=z<tz+td and y in mapping:b.put(x-tx,mapping[y],z-tz,s,'derived.A1.F2')
 export_structure(b.s,d/'layers.nbt',include_air=False);rb=load_build(d/'layers.nbt',Limits(cells=40_000_000,nodes=16_000_000));mesh.boxes=grille_boxes;mesh.write_mesh(rb,d/'layers.nbt',d/'scene')
 cams=[dict(id='exploded',eye=[65,60,80],target=[tw/2,9,td/2],spanX=58,spanZ=52,width=1440,height=1290,ortho=True,concept=False)]
 (d/'cameras.json').write_text(json.dumps(cams));egl.ROOT=C/'review';egl.main(run+'_exploded',d/'cameras.json',emission_policy='material')
 (d/'derivation.json').write_text(json.dumps({'source_final_nbt_sha256':hashlib.sha256((r/'building.nbt').read_bytes()).hexdigest(),'tower':'A1','floor':2,'source_y_to_display_y':mapping,'xz_crop':[tx,tz,tx+tw,tz+td],'offset_xz':[-tx,-tz],'scope':'Floor / room layer / recessed-light ceiling / upper finished-floor layer. Display translations only; not the final build.'},indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);main(ap.parse_args().run)
