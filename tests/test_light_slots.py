import unittest
from hafusion.lighting import first_clear_slot

class FixtureSlotTests(unittest.TestCase):
    def test_no_structural_replacement_or_new_pane_connection(self):
        candidates=[(0,2,0),(1,2,0),(2,2,0),(4,2,0)]
        occupied={(0,2,0):'wall'};reserved={(1,2,0)};panes={(2,2,1)}
        self.assertEqual(first_clear_slot(candidates,occupied,reserved,panes),(4,2,0))
        self.assertEqual(occupied,{(0,2,0):'wall'})
    def test_no_clear_slot_is_explicit(self):
        self.assertIsNone(first_clear_slot([(1,1,1)],{(1,1,1):'wall'},set()))

if __name__=='__main__':unittest.main()
