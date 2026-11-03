import unittest
from unittest.mock import patch
from hafusion.lighting import room_lighting, unit

class LightingTests(unittest.TestCase):
    def test_stable_room_ids_and_seed(self):
        ids=[f'f{y}.r{x}' for y in range(18) for x in range(6)]
        def make(order,seed):
            return {rid:room_lighting(seed,rid.split('.')[0],rid,int(rid[-1])//2) for rid in order}
        a=make(ids,230023)
        self.assertEqual(a,make(list(reversed(ids)),230023))
        extended=make(ids+['f99.r1'],230023)
        self.assertEqual(a,{k:extended[k] for k in ids})
        self.assertEqual(a['f4.r2'],room_lighting(230023,'f4','f4.r2',1))
        b=make(ids,230024)
        self.assertNotEqual(a,b)
        self.assertEqual({v['material'] for v in a.values()},{None,'sea_lantern','glowstone'})
        self.assertTrue(20 < sum(v['lit'] for v in a.values()) < 90)
        self.assertGreater(len({tuple(a[f'f{y}.r{x}']['lit'] for x in range(6)) for y in range(18)}),5)

    def test_invalid_activity(self):
        with self.assertRaises(ValueError):room_lighting(1,'floor','room','zone',1.5)

    def test_published_shenzhen_room_decision(self):
        # Golden value from the preserved Shenzhen V2 rooms.json.
        self.assertEqual(room_lighting(230023,'floor29','office.front.y29.x20','left',.53),
                         {'lit':True,'material':'sea_lantern','fixture_count':1,
                          'offset_x':1,'depth':2,'probability':.3313})

    def test_module_release_does_not_reseed_a_saved_stream(self):
        for namespace in ['room-lighting-0.1','room-lighting-0.2']:
            before=(unit(16,'room','furniture',namespace=namespace),
                    room_lighting(23,'floor','room','zone',namespace=namespace))
            with patch('hafusion.lighting.VERSION','unrelated-helper-release'):
                after=(unit(16,'room','furniture',namespace=namespace),
                       room_lighting(23,'floor','room','zone',namespace=namespace))
            self.assertEqual(before,after)

if __name__=='__main__':unittest.main()
