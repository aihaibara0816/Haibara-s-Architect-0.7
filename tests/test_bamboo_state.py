from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from detail_lab import states
from hafusion.classical import Builder,M
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build
class BambooTests(unittest.TestCase):
 def test_native_stem_states_roundtrip_and_do_not_connect_panes(self):
  b=Builder((8,8,8));b.put(2,0,2,'moss_block','soil')
  for y,leaves in enumerate(['none','small','large'],1):b.put(2,y,2,M('bamboo',age=1,leaves=leaves,stage=1),'bamboo')
  b.put(1,1,2,'glass_pane','glass');b.finish()
  self.assertIn('east=false',b.s.blocks[(1,1,2)])
  self.assertFalse(states.support_cube(b.s.blocks[(2,1,2)]))
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bamboo.nbt';export_structure(b.s,p,include_air=False);self.assertEqual(load_build(p).blocks,b.s.blocks)
 def test_official_stem_widths_and_invalid_state_rejection(self):
  for age,width in [(0,2/16),(1,3/16)]:
   box=states.boxes(M('bamboo',age=age))[0];self.assertAlmostEqual(box[3]-box[0],width)
  with self.assertRaises(ValueError):M('bamboo',leaves='oak')
  with self.assertRaises(ValueError):M('bamboo',stage=2)
