"""Actual-size 1:2 facade sample, corner, entrance and exposed window-back cut."""
from pathlib import Path
import sys,json
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build
from detail_lab import states
from detail_lab.mesh import write_mesh
from hafusion.facade import add_skin
from vendor import render_egl
M=states.make

def build():
 s=Scene((28,22,18))
 for x in range(2,26):
  for z in range(2,16):s.set((x,0,z),M('smooth_stone'),'sample.ground')
 floors=[1,3,5,8,10,12,14,17,19]
 for y in range(1,20):
  for x in range(4,24):
   if not (10<=x<=13 and y<3):add_skin(s,x,y,4,'north',component='sample.front')
  for z in range(5,14):add_skin(s,24,y,z,'east',component='sample.corner')
  s.set((24,y,4),M('gray_stained_glass'),'sample.sealed_turn')
  s.set((25,y,4),M('diorite_wall'),'sample.corner_fin')
  for x in range(5,24):s.set((x,y,12),M('gray_concrete'),'sample.backwall')
 for y in floors:
  for x in range(4,24):
   for z in range(5,12):s.set((x,y,z),M('smooth_stone_slab',type='top'),'sample.floor')
 for y in [4,9,13,18]:
  for x in [7,16,21]:s.set((x,y,8),M('glowstone' if (x+y)%3 else 'sea_lantern'),'sample.light')
 for x in range(9,15):
  for z in range(1,5):s.set((x,3,z),M('smooth_quartz_slab',type='top'),'sample.canopy')
 states.connect(s);out=CASE/'runs/facade_sample_v2';out.mkdir(parents=True,exist_ok=True)
 export_structure(s,out/'building.nbt',3955,False);b=load_build(out/'building.nbt');assert b.blocks==s.blocks
 dest=CASE/'review/previews/facade_sample_v2';write_mesh(b,out/'building.nbt',dest/'scene')
 c={'width':1800,'height':1500,'ortho':True,'spanX':34,'spanZ':28.3333,'concept':False,'fov':36}
 views=[{**c,'id':'oblique','eye':[50,25,-65],'target':[14,10,8]},
        {**c,'id':'front','eye':[14,10,-90],'target':[14,10,8]},
        {**c,'id':'night','eye':[50,25,-65],'target':[14,10,8],'night':True}]
 p=dest/'cameras.json';p.write_text(json.dumps(views));render_egl.ROOT=CASE/'review';render_egl.main('facade_sample_v2',p)
 print('sample NBT/readback/render complete',flush=True)
if __name__=='__main__':build()
