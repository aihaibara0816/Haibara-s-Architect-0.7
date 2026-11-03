import unittest,sys,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'support'))
from detail_lab import states
from hafusion.facade import skin_cell
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build

class VerticalFacadeTests(unittest.TestCase):
    def test_scene_budget_is_explicit_bounded_and_survives_snapshot(self):
        with self.assertRaises(ValueError):Scene((80,269,92))
        s=Scene((80,269,92),max_cells=2_000_000)
        self.assertEqual(s.snapshot().max_cells,2_000_000)
        self.assertEqual(states.rotate_scene(s).max_cells,2_000_000)
        with self.assertRaises(ValueError):Scene((1,1,1),max_cells=2_000_001)
    def test_wall_matches_official_post_and_side_asset(self):
        refs=ROOT/'cases/guangzhou_ctf/research/vanilla'
        post=json.loads((refs/'template_wall_post.json').read_text())['elements'][0]
        expected=tuple(v/16 for v in post['from']+post['to'])
        self.assertEqual(states.boxes(states.make('diorite_wall')),(expected,))
        side=json.loads((refs/'template_wall_side.json').read_text())['elements'][0]
        self.assertEqual(states.boxes(states.make('diorite_wall',up=False,north='low')),
                         (tuple(v/16 for v in side['from']+side['to']),))
        with self.assertRaises(ValueError):states.make('diorite_wall',east='true')
    def test_rotation_and_roundtrip_preserve_non_cube_states(self):
        s=Scene((8,9,8))
        for y in range(1,8):
            for row in skin_cell(2,y,3,'north'):
                x,yy,z,state,owner=row;s.set((x,yy,z),state,owner)
        states.connect(s);r=s
        for _ in range(4):r=states.rotate_scene(r)
        self.assertEqual(r.blocks,s.blocks)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'test.nbt';export_structure(s,p,3955,False)
            self.assertEqual(load_build(p).blocks,s.blocks)
    def test_cardinal_layer_order_and_phase(self):
        for side,d in [('north',(0,-1)),('south',(0,1)),('west',(-1,0)),('east',(1,0))]:
            glass,fin=skin_cell(4,5,6,side,pitch=2)
            self.assertEqual(fin[:3],(4+d[0],5,6+d[1]))
            self.assertIn('glass_pane',glass[3]);self.assertIn('diorite_wall',fin[3])
        self.assertEqual(len(skin_cell(3,5,6,'north',pitch=2)),1)
        with self.assertRaises(ValueError):skin_cell(2,5,6,'north',pitch=0)

if __name__=='__main__':unittest.main()
