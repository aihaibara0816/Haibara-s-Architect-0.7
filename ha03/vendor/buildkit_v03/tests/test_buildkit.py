import unittest,sys,tempfile,json,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from voxel_core import *
from inspect_build import load_build,inspect,compare
from gafa_colonnade import build
from make_viewer import make_viewer

class CoreTests(unittest.TestCase):
 def test_bad_size(self):
  with self.assertRaises(ValueError):Scene((0,2,3))
 def test_budget(self):
  with self.assertRaises(ValueError):Scene((1001,1001,2))
 def test_outside(self):
  with self.assertRaises(ValueError):Scene((2,2,2)).set((2,1,1),'minecraft:stone','test')
 def test_fill_half_open(self):
  s=Scene((4,4,4));s.fill((1,1,1),(3,3,3),'minecraft:stone','a');self.assertEqual(len(s.blocks),8)
 def test_air_removes(self):
  s=Scene((1,1,1));s.set((0,0,0),'minecraft:stone','a');s.set((0,0,0),AIR,'b');self.assertEqual(s.blocks,{})
 def test_cylinder(self):
  s=Scene((6,6,6));s.cylinder(3,3,1,1,5,'minecraft:stone','a');self.assertEqual(len(s.blocks),16)
 def test_snapshot_independent(self):
  s=Scene((2,2,2));t=s.snapshot();s.set((0,0,0),'minecraft:stone','a');self.assertFalse(t.blocks)
 def test_cumulative_rounding(self):self.assertEqual(repeated_axes(0,6.4,11)[-1],64)
 def test_collapsed_axes(self):
  with self.assertRaises(ValueError):repeated_axes(0,.1,4)
 def test_nonfinite(self):
  with self.assertRaises(ValueError):quantize(float('nan'))
 def test_canonical_state(self):self.assertEqual(state('minecraft:stone_slab',waterlogged='false',type='top'),'minecraft:stone_slab[type=top,waterlogged=false]')
 def test_invalid_state(self):
  with self.assertRaises(ValueError):state('INVALID')
 def test_empty_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):export_structure(Scene((1,1,1)),Path(d)/'a.nbt')
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   s=Scene((3,3,3));s.set((1,1,1),state('minecraft:smooth_stone_slab',type='top',waterlogged='false'),'slab');p=Path(d)/'a.nbt';export_structure(s,p);b=load_build(p);self.assertEqual(b.size,s.size);self.assertEqual({p:t for p,t in b.blocks.items() if t!=AIR},s.blocks);self.assertEqual(len(b.blocks),27)
 def test_deterministic_export(self):
  with tempfile.TemporaryDirectory() as d:
   s=Scene((1,1,1));s.set((0,0,0),'minecraft:stone','a');a=Path(d)/'a.nbt';b=Path(d)/'b.nbt';export_structure(s,a);export_structure(s,b);self.assertEqual(a.read_bytes(),b.read_bytes())
 def test_export_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   s=Scene((1,1,1));s.set((0,0,0),'minecraft:stone','a');p=Path(d)/'a.nbt';export_structure(s,p)
   with self.assertRaises(FileExistsError):export_structure(s,p)
 def test_slab_shapes(self):
  self.assertEqual(block_parts(state('minecraft:smooth_stone_slab',type='top',waterlogged='false'))[0][1],.5)
  self.assertEqual(block_parts(state('minecraft:smooth_stone_slab',type='bottom',waterlogged='false'))[0][4],.5)
 def test_stair_shapes(self):
  for facing in ('east','west','north','south'):
   self.assertEqual(len(block_parts(state('minecraft:quartz_stairs',facing=facing,half='bottom',shape='straight',waterlogged='false'))),2)
 def test_fence_geometry(self):
  self.assertEqual(block_parts(state('minecraft:nether_brick_fence',east='true'))[0][4],1.5)

class SampleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((ROOT/'projects/gafa_admin/parameters.json').read_text());cls.scene,cls.stages,cls.g=build(cls.p)
 def test_bays(self):self.assertEqual(self.g['column_axes_z'],[5,13,21,29])
 def test_four_snapshots(self):self.assertEqual(len(self.stages),4)
 def test_nonempty(self):self.assertGreater(len(self.scene.blocks),3000)
 def test_no_entities(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.nbt';export_structure(self.scene,p);self.assertEqual(inspect(load_build(p))['entities_count'],0)
 def test_opening_clear(self):
  for x in (2,3):
   for y in (6,7,8):
    for z in (16,17):self.assertNotIn((x,y,z),self.scene.blocks)
 def test_stair_top_and_headroom(self):
  tops=[]
  for x in range(15,7,-1):
   boxes=[]
   for (bx,y,z),s in self.scene.blocks.items():
    if bx==x and z==16 and self.scene.owners[(bx,y,z)]=='stair.treads':boxes += [y+b[4] for b in block_parts(s)]
   top=max(boxes);tops.append(top)
   for y in range(math.ceil(top),math.ceil(top)+2):self.assertNotIn((x,y,16),self.scene.blocks)
  self.assertEqual(tops,[2.5,3,3.5,4,4.5,5,5.5,6])
 def test_external_walkway(self):
  for z in range(1,33):
   for y in (2,3,4):self.assertNotIn((19,y,z),self.scene.blocks)
 def test_wrong_scale_rejected(self):
  p=dict(self.p,scale_blocks_per_metre=.5)
  with self.assertRaises(ValueError):build(p)
 def test_output_equality_and_viewer(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);export_structure(self.scene,d/'a.nbt');b=load_build(d/'a.nbt');self.assertEqual({p:s for p,s in b.blocks.items() if s!=AIR},self.scene.blocks)
   make_viewer(b,'Test <title>',d/'view.html',{});text=(d/'view.html').read_text();self.assertNotIn('__BUILD_PAYLOAD__',text);self.assertNotIn('<script src=',text);self.assertIn('mesh_base64',text)

if __name__=='__main__':unittest.main(verbosity=2)
