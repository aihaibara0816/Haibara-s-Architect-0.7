from pathlib import Path
import sys, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.site_scene import SiteScene
from vendor.voxel_core import Scene, export_structure, AIR
from vendor.inspect_build import load_build, Limits

class SiteSceneTests(unittest.TestCase):
    def test_sparse_budget_and_legacy_limit(self):
        with self.assertRaises(ValueError): Scene((320,310,320),max_cells=2_000_000)
        s=SiteScene((320,310,320),max_blocks=2)
        s.set((0,0,0),'minecraft:stone_bricks','terrain')
        s.set((319,309,319),'minecraft:glass','top')
        with self.assertRaises(ValueError):s.set((1,0,0),'minecraft:stone_bricks','terrain')
        s.set((0,0,0),'minecraft:dirt','terrain')
        s.set((0,0,0),AIR,'terrain')
        s.set((1,0,0),'minecraft:dirt','terrain')
        with self.assertRaises(ValueError):s.set((320,0,0),AIR,'terrain')

    def test_snapshot_and_nbt_roundtrip(self):
        s=SiteScene((320,310,320),max_blocks=3)
        s.set((160,303,176),'minecraft:red_concrete','mast')
        q=s.snapshot();q.set((160,304,176),'minecraft:glass','beacon')
        self.assertNotEqual(s.fingerprint(),q.fingerprint())
        self.assertEqual(q.max_blocks,3)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.nbt';export_structure(q,p,include_air=False)
            b=load_build(p,Limits(cells=40_000_000))
            self.assertEqual(q.blocks,b.blocks)
            self.assertEqual(q.size,b.size)

    def test_invalid_budgets(self):
        for size,kwargs in [((400,400,400),{'max_volume_cells':40_000_000}),((0,10,10),{}),((3,3,3),{'max_blocks':0}),((3,3,3),{'max_volume_cells':65_000_000})]:
            with self.assertRaises(ValueError):SiteScene(size,**kwargs)
