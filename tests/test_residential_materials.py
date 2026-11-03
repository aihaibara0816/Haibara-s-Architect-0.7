"""Only the added green-pane / still-water vocabulary; no game test claims."""
import unittest
from hafusion.site_scene import SiteScene
from detail_lab import states

class ResidentialMaterials(unittest.TestCase):
    def test_water_has_no_solid_pane_support(self):
        water=states.make('water');self.assertTrue(states.transparent(water));self.assertFalse(states.support_cube(water))
        s=SiteScene((3,3,3));s.set((1,1,1),states.make('green_stained_glass_pane'),'pane');s.set((2,1,1),water,'water');states.connect(s)
        self.assertEqual(states.parse_state(s.blocks[(1,1,1)])[1]['east'],'false')
    def test_green_panes_join_symmetrically(self):
        s=SiteScene((3,3,3))
        for x in [0,1]:s.set((x,1,1),states.make('green_stained_glass_pane'),'pane')
        states.connect(s)
        self.assertEqual(states.parse_state(s.blocks[(0,1,1)])[1]['east'],'true')
        self.assertEqual(states.parse_state(s.blocks[(1,1,1)])[1]['west'],'true')
        self.assertEqual(len(states.boxes(s.blocks[(0,1,1)])),2)
    def test_invalid_fluid_level_rejected(self):
        with self.assertRaises(ValueError):states.make('water',level=16)
    def test_green_glass_remains_transparent(self):
        for kind in ['green_stained_glass','green_stained_glass_pane']:
            s=states.make(kind);self.assertTrue(states.transparent(s));self.assertTrue(states.boxes(s))

if __name__=='__main__':unittest.main()
