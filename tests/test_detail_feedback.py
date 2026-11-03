import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'support'))
from detail_lab import states
from detail_lab.shading import emission_shader,LEGACY_EMISSION,MATERIAL_EMISSION
from hafusion.interiors import room_style,furnishing_cells

class DetailFeedbackTests(unittest.TestCase):
 def test_anvil_visual_bounds_match_official_asset(self):
  p=ROOT/'cases/guangzhou_ctf/research/detail_study_v2/vanilla/template_anvil.json'
  expected=tuple(tuple(v/16 for v in e['from']+e['to']) for e in json.loads(p.read_text())['elements'])
  self.assertEqual(states.boxes(states.make('anvil',facing='south')),expected)
  s=states.make('anvil');rot=s
  for i in range(4):rot=states.rotate_state(rot)
  self.assertEqual(rot,s)
 def test_room_styles_do_not_require_excess_clearance(self):
  for height in [1,2]:
   a={f'r{i}':room_style(23,f'r{i}',height) for i in range(60)}
   b={k:room_style(23,k,height) for k in reversed(a)};self.assertEqual(a,b)
   for row in a.values():
    for x,y,z,mat in furnishing_cells(row['style'],height):
     self.assertLess(y,height);self.assertTrue(0<=x<4 and 2<=z<4);states.validate(states.make(mat))
   self.assertEqual({r['light'] for r in a.values()},{'glowstone','sea_lantern'})
  with self.assertRaises(ValueError):furnishing_cells('green',1)
 def test_emissive_colour_preserved_with_legacy_replay(self):
  self.assertEqual(emission_shader(LEGACY_EMISSION),MATERIAL_EMISSION)
  self.assertEqual(emission_shader(LEGACY_EMISSION,'legacy'),LEGACY_EMISSION)
  self.assertGreater(states.color(states.make('glowstone'))[0]-states.color(states.make('glowstone'))[2],80)
  with self.assertRaises(ValueError):emission_shader('unreviewed shader')
if __name__=='__main__':unittest.main()
