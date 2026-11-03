from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder,M
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build

class ClassicalTests(unittest.TestCase):
    def test_four_oriented_windows_open_into_thick_masonry(self):
        for n in [(0,-1),(1,0),(0,1),(-1,0)]:
            b=Builder((64,32,64));f=b.frame(32,32,n)
            f.rect(-5,6,0,20,-10,1,'smooth_quartz','wall')
            f.window(0,5,4,7,'window',floor_y=3)
            def at(u,y,d):return b.s.blocks.get(tuple(map(int,f.xyz(u,y,d))),'minecraft:air')
            self.assertIn('glass_pane',at(-2,6,-1))
            for d in [-3,-4,-7,-8]:self.assertEqual(at(-2,10,d),'minecraft:air')
            self.assertEqual(at(-2,10,-10),'minecraft:smooth_quartz')
            self.assertEqual(at(-3,6,0),'minecraft:smooth_quartz')
            b.finish()
    def test_new_material_states_survive_nbt(self):
        b=Builder((12,4,4))
        for x,mat in enumerate(['sandstone','smooth_sandstone','cut_sandstone','gold_block','lapis_block','oxidized_copper',M('smooth_sandstone_slab',type='top'),M('smooth_sandstone_stairs',facing='west')]):b.put(x,0,0,mat,'sample')
        b.finish()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'states.nbt';export_structure(b.s,p,include_air=False)
            self.assertEqual(load_build(p).blocks,b.s.blocks)
    def test_room_randomness_is_stable_and_has_real_void(self):
        def build():
            b=Builder((64,32,64),20261023);f=b.frame(32,24,(0,-1));f.rect(-16,17,0,20,-12,1,'smooth_quartz','wall')
            for i in [-9,0,9]:f.window(i,5,4,7,'window.'+str(i),floor_y=3)
            b.finish();return b
        a,b=build(),build();self.assertEqual(a.s.blocks,b.s.blocks);self.assertEqual(a.rooms,b.rooms)
        self.assertTrue(any(o.endswith('.room.back') for o in a.s.owners.values()))
    def test_bounds_are_not_silently_clipped(self):
        b=Builder((4,4,4))
        with self.assertRaises(ValueError):b.put(4,0,0,'smooth_sandstone','bad')

if __name__=='__main__':unittest.main()
