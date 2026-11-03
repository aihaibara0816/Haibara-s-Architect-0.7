import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hafusion.design_handoff import compile_handoff, HandoffError


class DesignHandoffTests(unittest.TestCase):
    def setUp(self):
        self.s = json.loads((ROOT/'examples/handoff/library.json').read_text())

    def test_primary_function_is_preserved_and_no_geometry_claim(self):
        p = compile_handoff(self.s)
        self.assertEqual(p['primary_use'], 'library')
        self.assertEqual(len(p['lighting_tasks']), 3)
        self.assertTrue(all(x['required'] for x in p['lighting_tasks']))
        self.assertFalse(p['generated_geometry'])
        self.assertEqual(p['game_status'], 'pending')

    def test_low_rise_boundary_and_unknown(self):
        for total, policy in [(9,'all_occupied_spaces'),(10,'evidence_based'),(None,'pending_storey_count')]:
            self.s['storeys_total'] = total
            self.assertEqual(compile_handoff(self.s)['lighting_coverage_policy'], policy)

    def test_unknown_count_is_not_silently_assumed(self):
        self.s['storeys_total'] = None
        p = compile_handoff(self.s)
        self.assertTrue(any('storeys_total unknown' in x for x in p['pending']))
        self.assertFalse(any(t['required'] for t in p['lighting_tasks']))

    def test_styles_have_different_construction(self):
        self.assertEqual(compile_handoff(self.s)['ceiling_plans'][0]['preferred_separator_layers'], 1)
        self.s['style'] = 'modern'
        self.assertEqual(compile_handoff(self.s)['ceiling_plans'][0]['ceiling_y'], 8)

    def test_headroom_cannot_silently_move_floors(self):
        self.s['style'] = 'modern'
        self.s['floor_levels'][0]['min_clear_height'] = 6
        p = compile_handoff(self.s)['ceiling_plans'][0]
        self.assertIsNone(p['ceiling_y'])
        self.assertFalse(p['floor_levels_changed'])
        self.s['route'] = 'constrained_completion'
        self.s['floor_levels'][0]['existing_slab_recess_reason'] = 'preserve landing clearance'
        self.assertEqual(compile_handoff(self.s)['ceiling_plans'][0]['ceiling_y'], 9)

    def test_module_in_route_is_rejected(self):
        self.s['proposed_modules'][0]['bounds_xyz'] = [11,3,3,13,5,5]
        with self.assertRaisesRegex(HandoffError, 'keepout'): compile_handoff(self.s)

    def test_locked_component_cannot_be_replaced(self):
        self.s['proposed_modules'][0]['component_id'] = 'facade.windows.42'
        with self.assertRaisesRegex(HandoffError, 'locked'): compile_handoff(self.s)

    def test_scope_and_module_overlap_rejected(self):
        self.s['authorized_scope']['editable_regions'] = [[0,0,0,10,10,10]]
        with self.assertRaisesRegex(HandoffError, 'authorized'): compile_handoff(self.s)
        self.setUp()
        self.s['proposed_modules'][1]['bounds_xyz'] = self.s['proposed_modules'][0]['bounds_xyz']
        with self.assertRaisesRegex(HandoffError, 'overlap'): compile_handoff(self.s)

    def test_civic_does_not_imply_pond(self):
        self.s['primary_use'] = 'civic'
        self.s['landscape']['archetype'] = 'civic'
        self.assertFalse(compile_handoff(self.s)['landscape_plan']['water_requested'])
        self.s['landscape']['water_requested'] = True
        with self.assertRaisesRegex(HandoffError, 'pond'): compile_handoff(self.s)

    def test_invalid_identity_style_version_and_floor_data_rejected(self):
        for key, value in [('primary_use','unknown'),('identity_features',['desk']),('schema_version','0.2'),('style','unspecified'),('storeys_total',True),('floor_levels',[])]:
            s = copy.deepcopy(self.s); s[key] = value
            with self.subTest(key=key), self.assertRaises(HandoffError): compile_handoff(s)

    def test_override_requires_reason(self):
        self.s['lighting'] = {'coverage_override':'selected_spaces'}
        with self.assertRaisesRegex(HandoffError, 'reason'): compile_handoff(self.s)
        self.s['lighting']['override_reason'] = 'user requested a closed floor'
        self.assertEqual(compile_handoff(self.s)['lighting_coverage_policy'], 'selected_spaces')

    def test_cli_is_plan_only_and_refuses_overwrite(self):
        cmd = [sys.executable,str(ROOT/'tools/agent.py'),'--handoff',str(ROOT/'examples/handoff/library.json')]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/'plan.json'
            good = subprocess.run(cmd+['--out',str(out)],capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr.decode())
            before = out.read_bytes()
            self.assertNotEqual(subprocess.run(cmd+['--out',str(out)],capture_output=True).returncode, 0)
            self.assertEqual(before, out.read_bytes())
            self.assertNotEqual(subprocess.run(cmd+['--run','illegal'],capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
