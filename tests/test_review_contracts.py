import copy, unittest
from hafusion.review import review_samples, review_views, construction_checks, status
from hafusion.views import ensure_review_views

class ReviewContracts(unittest.TestCase):
    def test_empty_contract_is_pending(self):
        self.assertEqual(status([]), 'pending')
        self.assertEqual(status(review_samples({}, (3,3,3), [{'id':'entry','kind':'air','samples':[]}])), 'pending')

    def test_water_and_pane_cannot_bear_column(self):
        for st in ('minecraft:water[level=0]', 'minecraft:glass_pane[east=false,north=false,south=false,waterlogged=false,west=false]'):
            checks=review_samples({(1,0,1):st}, (3,3,3), [{'id':'base','kind':'full_bearing','samples':[[1,0,1]]}])
            self.assertEqual(status(checks),'fail')

    def test_outside_bounds_cannot_fake_clearance(self):
        self.assertEqual(status(review_samples({},(3,3,3),[{'id':'door','kind':'air','samples':[[9,1,1]]}])),'fail')

    def test_assembled_mullion_and_lost_lamp_detected(self):
        records={'entries':[{'x':4,'z':3,'floor_y':0}], 'lamps':[{'xyz':[1,2,1],'material':'glowstone'}]}
        checks=construction_checks(records)
        b={(x,0,3):'minecraft:stone_bricks' for x in range(1,8)}
        b[4,1,3]='minecraft:iron_block';b[1,2,1]='minecraft:sea_lantern'
        before=copy.deepcopy(b);r={c['id']:c for c in review_samples(b,(10,5,10),checks)}
        self.assertEqual(r['entry_headroom']['status'],'fail')
        self.assertEqual(r['lamp_survival']['status'],'fail')
        self.assertEqual(b,before)

    def test_unknown_material_and_invalid_contract_fail_honestly(self):
        self.assertEqual(status(review_samples({(0,0,0):'mod:stone'},(1,1,1),[{'id':'base','kind':'full_bearing','samples':[[0,0,0]]}])),'pending')
        with self.assertRaises(ValueError):review_samples({},(3,3,3),[{'id':'x','kind':'guess','samples':[]}])
        with self.assertRaises(ValueError):review_samples({},(3,3,3),[{'id':'x','kind':'air','samples':[]},{'id':'x','kind':'air','samples':[]}])

    def test_review_views_include_true_top_and_preserve_details(self):
        detail={'id':'door','target':[1,1,1],'eye':[4,3,4],'cutY':2}
        v=ensure_review_views([detail],(640,64,660))
        self.assertEqual(v,ensure_review_views(v,(640,64,660)))
        self.assertEqual(v[0],detail)
        top=next(x for x in v if x['id']=='top_day')
        self.assertEqual(top['eye'][0::2],top['target'][0::2])
        self.assertGreaterEqual(top['spanX'],640)
        self.assertGreaterEqual(top['spanZ'],660)
        records=[{'camera':x,'source_nbt_sha256':'a'} for x in v]
        self.assertEqual(status(review_views(records,'a')),'pass')

    def test_tilted_satellite_is_not_top_even_with_top_label(self):
        records=[{'camera':x,'source_nbt_sha256':'a'} for x in ensure_review_views([],(100,200,80))]
        records[-1]['camera']['eye'][0]+=10
        self.assertEqual(status(review_views(records,'a')),'fail')

    def test_missing_camera_or_stale_nbt_cannot_pass(self):
        r=[{'camera':x,'source_nbt_sha256':'a'} for x in ensure_review_views([],(100,200,80))]
        self.assertEqual(status(review_views(r[:-1],'a')),'pending')
        self.assertEqual(status(review_views(r,'b')),'fail')
        r[1]['camera']['spanX']+=5
        self.assertEqual(status(review_views(r,'a')),'fail')

    def test_legacy_true_top_is_accepted_without_renaming_history(self):
        r=[{'camera':x,'source_nbt_sha256':'a'} for x in ensure_review_views([],(100,200,80))]
        r[-1]['camera']['id']='top'
        old=copy.deepcopy(r)
        self.assertEqual(status(review_views(r,'a')),'pass')
        self.assertEqual(r,old)

if __name__=='__main__':unittest.main()
