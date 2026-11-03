import copy, json, tempfile, unittest
from pathlib import Path
import numpy as np
from evidence import arbitrate
from stage_cache import DiskCache, demonstration, stage_key, digest
from alignment import fit_similarity, transform

POLICY=dict(kind='length', tolerance=.02, target_epoch='2025', source_order=['survey','photograph','3d_model'], baseline_hash='fixture-baseline')
def row(sid='p1', value=5, **kwargs):
    d=dict(component_id='podium.deck',attribute='height',value=value,unit='m',source_id=sid,source_family=sid,source_type='photograph',epoch='2025',phase='as_built',status='estimated')
    d.update(kwargs);return d

class EvidenceTests(unittest.TestCase):
    def test_same_length_different_units_not_conflict(self):
        d=arbitrate([row(),row('p2',500,unit='cm')],**POLICY)
        self.assertEqual(d['status'],'proposal');self.assertFalse(d['conflicts'])
    def test_peer_conflict_does_not_average(self):
        d=arbitrate([row(),row('p2',7)],**POLICY)
        self.assertEqual(d['status'],'needs_review');self.assertIsNone(d['selected'])
    def test_old_photo_and_design_cannot_vote_for_built_epoch(self):
        d=arbitrate([row('old',9,epoch='2019'),row('design',8,phase='design'),row()],**POLICY)
        self.assertEqual(len(d['excluded']),2);self.assertEqual(d['selected']['source_id'],'p1')
    def test_reposts_do_not_create_independent_support(self):
        rows=[row('copy-'+str(i),source_family='original-photo') for i in range(20)]
        d=arbitrate(rows,**POLICY);self.assertEqual(d['independent_families'],1)
    def test_duplicate_source_with_conflicting_annotations_requires_review(self):
        d=arbitrate([row(),row(value=8)],**POLICY)
        self.assertEqual(d['reason'],'same_family_inconsistent')
    def test_unknown_unit_never_silently_falls_back(self):
        d=arbitrate([row('survey',5000,unit='unknown',source_type='survey'),row()],**POLICY)
        self.assertEqual(d['status'],'blocked')
    def test_weaker_conflict_preserved_and_status_not_promoted(self):
        d=arbitrate([row(),row('mesh',8,source_type='3d_model')],**POLICY)
        self.assertEqual(d['selected']['status'],'estimated');self.assertEqual(len(d['conflicts']),1)
        self.assertFalse(d['automatic_write'])
    def test_nonfinite_numeric_rejected(self):
        self.assertEqual(arbitrate([row(value=float('nan'))],**POLICY)['status'],'blocked')
    def test_cross_component_merge_rejected(self):
        with self.assertRaises(ValueError): arbitrate([row(),row('other',component_id='tower')],**POLICY)

class CacheTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory();self.cache=DiskCache(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def test_warm_disk_cache_survives_new_instance(self):
        a=demonstration(self.cache);b=demonstration(DiskCache(self.temp.name))
        self.assertEqual(a['output'],b['output']);self.assertEqual(b['rebuilt'],[]);self.assertEqual(b['hits'],7)
    def test_material_change_preserves_geometry_and_unrelated_component(self):
        a=demonstration(self.cache);b=demonstration(self.cache,left_material='minecraft:glass')
        self.assertEqual(a['geometry_hash'],b['geometry_hash'])
        self.assertEqual(set(b['rebuilt']),{'material:pier.left','assembly:scene'})
        self.assertEqual([r for r in a['output'] if r[4]!='pier.left'],[r for r in b['output'] if r[4]!='pier.left'])
    def test_dependency_edit_matches_full_rebuild_and_preserves_void(self):
        demonstration(self.cache);inc=demonstration(self.cache,width=3)
        with tempfile.TemporaryDirectory() as td: full=demonstration(DiskCache(td),width=3)
        self.assertEqual(inc['output_hash'],full['output_hash'])
        self.assertNotIn('geometry:pier.right',inc['rebuilt'])
        self.assertIn('geometry:connector',inc['rebuilt'])
        self.assertNotIn([5,1,0], [r[:3] for r in inc['output']])
    def test_input_roles_matter(self):
        context=dict(frame_id='Y-up',units='m',target_epoch='2025',source_hash='fixture')
        a=stage_key('x','a','v1',{}, {'left':'1','right':'2'},context)
        b=stage_key('x','a','v1',{}, {'left':'2','right':'1'},context)
        self.assertNotEqual(a,b)
    def test_context_and_algorithm_versions_invalidate(self):
        c=dict(frame_id='Y-up',units='m',target_epoch='2025',source_hash='fixture')
        a=stage_key('x','a','v1',{}, {},c)
        for name,value in [('frame_id','Z-up'),('units','cm'),('target_epoch','2019'),('source_hash','changed')]:
            other={**c,name:value};self.assertNotEqual(a,stage_key('x','a','v1',{}, {},other))
        self.assertNotEqual(a,stage_key('x','a','v2',{}, {},c))
    def test_corruption_does_not_reuse_stale_result(self):
        demonstration(self.cache)
        path=next(Path(self.temp.name).glob('*.json'));d=json.loads(path.read_text());d['payload']={'corrupted':True};path.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'mismatch'): demonstration(self.cache)
    def test_nan_parameter_rejected(self):
        with self.assertRaises(ValueError):digest({'height':float('nan')})

class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.a=np.array([[0,0,0],[1,0,0],[0,2,0],[0,0,3]],float)
        self.rotation=np.array([[0,0,-1],[0,1,0],[1,0,0]])
        self.b=self.a@self.rotation*2.5+[10,20,30]
    def test_known_transform_and_unseen_anchor(self):
        d=fit_similarity(self.a,self.b,target_unit='m',tolerance=.001)
        self.assertAlmostEqual(d['scale'],2.5);self.assertEqual(d['status'],'candidate')
        test=np.array([[.2,.3,.7],[2,3,4]])
        np.testing.assert_allclose(transform(test,d['matrix']),test@self.rotation*2.5+[10,20,30],atol=1e-9)
    def test_collinear_anchors_rejected(self):
        p=[[0,0,0],[0,1,0],[0,2,0]]
        with self.assertRaises(ValueError):fit_similarity(p,p,target_unit='m',tolerance=.1)
    def test_nonuniform_model_not_silently_stretched(self):
        d=fit_similarity(self.a,self.a*[2,3,4],target_unit='m',tolerance=.01)
        self.assertEqual(d['status'],'needs_review')
    def test_mirror_not_silently_accepted(self):
        d=fit_similarity(self.a,self.a*[-1,1,1],target_unit='m',tolerance=.01)
        self.assertGreater(d['det_rotation'],0);self.assertEqual(d['status'],'needs_review')
    def test_mismatched_anchor_requires_review(self):
        b=self.b.copy();b[0]+=3
        d=fit_similarity(self.a,b,target_unit='m',tolerance=.1)
        self.assertEqual(d['status'],'needs_review')

if __name__=='__main__':unittest.main(verbosity=2)
