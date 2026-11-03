"""NBT-derived renderer with an explicitly approximate open iron-bar preview.
Vanilla NBT unchanged. Thin rods stand in for alpha-textured iron-bar planes.
"""
from pathlib import Path
import sys,argparse,json,subprocess,hashlib
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
from detail_lab import states,mesh
original_boxes=states.boxes
def grille_boxes(s):
 name,p=parse_state(s)
 if name!='minecraft:iron_bars':return original_boxes(s)
 out=[(.47,0,.47,.53,1,.53)]
 for d in ['north','south','east','west']:
  if p.get(d)!='true':continue
  if d in ['east','west']:
   lo,hi=(.5,1) if d=='east' else (0,.5)
   for yy in [.26,.73]:out.append((lo,yy,.475,hi,yy+.055,.525))
   for xx in [lo+.13,lo+.36]:out.append((xx,0,.475,xx+.045,1,.525))
  else:
   lo,hi=(.5,1) if d=='south' else (0,.5)
   for yy in [.26,.73]:out.append((.475,yy,lo,.525,yy+.055,hi))
   for zz in [lo+.13,lo+.36]:out.append((.475,0,zz,.525,1,zz+.045))
 return tuple(out)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--only',nargs='*');ap.add_argument('--reuse-mesh',action='store_true');a=ap.parse_args()
 nbt=C/'runs'/a.run/'building.nbt';out=C/'review/previews'/a.run;out.mkdir(parents=True,exist_ok=True)
 if not a.reuse_mesh:
  print('read final NBT; case grille mesh',flush=True);b=load_build(nbt,Limits(cells=40_000_000,nodes=16_000_000));mesh.boxes=grille_boxes;meta=mesh.write_mesh(b,nbt,out/'scene');del b
  meta['case_preview_overrides']={'iron_bars':'Thin grid rods approximate alpha cutouts, not vanilla model/textures or collision.','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(out/'scene/scene.json').write_text(json.dumps(meta,indent=2));print(meta['triangles'],flush=True)
 cmd=[sys.executable,str(ROOT/'tools/render_building_case.py'),'--case',C.name,'--run',a.run,'--reuse-mesh']
 if a.only:cmd+=['--only']+a.only
 subprocess.run(cmd,check=True)
if __name__=='__main__':main()
