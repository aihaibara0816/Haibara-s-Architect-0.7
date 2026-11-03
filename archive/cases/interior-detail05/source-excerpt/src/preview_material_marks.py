"""Procedural face marks for recognition, derived ONLY from existing NBT block IDs.
No game textures, added furniture or geometry edits. Marks stay on the source block.
"""
import numpy as np,json
from pathlib import Path
from vendor.voxel_core import parse_state

def apply(build,scene):
 out=[]
 def face(pos,u0,v0,u1,v1,c,axis='z',plane=1.002):
  if axis=='z':pts=[(u0,v0,plane),(u1,v0,plane),(u1,v1,plane),(u0,v1,plane)];n=[0,0,1]
  elif axis=='x':pts=[(plane,v0,u1),(plane,v0,u0),(plane,v1,u0),(plane,v1,u1)];n=[1,0,0]
  else:pts=[(u0,plane,v1),(u1,plane,v1),(u1,plane,v0),(u0,plane,v0)];n=[0,1,0]
  for i in [0,1,2,0,2,3]:out.append([*[pos[j]+pts[i][j] for j in range(3)],*n,*[x/255 for x in c],0])
 for p,s in build.blocks.items():
  name,prop=parse_state(s)
  if name=='minecraft:bookshelf':
   for axis in ['z','x']:
    for v in [.12,.57]:
     face(p,.08,v,.92,v+.30,(57,43,31),axis)
     for i,c in enumerate([(145,65,48),(60,104,103),(183,156,77),(87,97,54),(112,79,114),(174,123,65)]):face(p,.105+i*.13,v+.02,.20+i*.13,v+.23+(i%3)*.02,c,axis)
  elif name=='minecraft:barrel':
   for v in [.12,.78]:face(p,0,v,1,v+.08,(76,65,49))
   face(p,.43,.42,.57,.57,(55,48,37))
  elif name=='minecraft:furnace':
   face(p,.12,.14,.88,.43,(31,33,34));face(p,.15,.65,.85,.84,(48,51,52))
  elif name=='minecraft:water_cauldron':face(p,.14,.14,.86,.86,(65,137,156),'y',.877)
  elif name=='minecraft:white_bed' and prop.get('part')=='head':face(p,.07,.08,.93,.47,(253,250,235),'y',.564)
  elif name=='minecraft:cake':
   face(p,.063,.063,.936,.936,(244,235,215),'y',.502)
   for u,v in [(.2,.2),(.6,.3),(.4,.7)]:face(p,u,v,u+.12,v+.12,(167,55,46),'y',.504)
 scene=Path(scene);raw=np.fromfile(scene/'opaque.bin',dtype='<f4').reshape(-1,10)
 np.concatenate([raw,np.asarray(out,dtype='<f4')]).astype('<f4').tofile(scene/'opaque.bin')
 m=json.loads((scene/'scene.json').read_text());m['material_mode']='procedural block-face recognition marks; no resource-pack textures';m['triangles']['opaque']+=len(out)//3;(scene/'scene.json').write_text(json.dumps(m,indent=2))
