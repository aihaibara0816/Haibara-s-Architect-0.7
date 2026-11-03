import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from architect.legacy import ROOT
from architect.spec_loader import load_spec,validate_spec
from architect.geometry import generate
from architect.revision import guard_revision
from architect.reference_review import validate_review
from architect.pipeline import canonical_hash
sys.path.insert(0,str(ROOT/'tools'))
from migrate_spec import migrate
sys.path.insert(0,str(ROOT/'vendor/building_reference/scripts'))
from reference_set import migrate as migrate_packet
from validate_packet import validate
import selftest as fixtures

def sample():return load_spec(ROOT/'examples/retail_store/building_spec.json')
def packet(count=10):
    p=fixtures.report()
    for i in range(count):fixtures.image(p,'img-'+str(i))
    p=migrate_packet(p);s=p['selection'];s['coverage_requirements']=[]
    s['core']=[{'image_id':im['image_id'],'purpose':'Synthetic view fixture','rationale':'Protocol test, not actual photo'} for im in p['images']]
    p['prompts']['image_ids']=[x['image_id'] for x in s['core']]
    return p

def request():return {'allowed_parameter_paths':{'canopy':['/min_m/2']},'allowed_region':[14,6,2,19,6,5],'protected_regions':[],'allowed_changed_components':['canopy']}

def changed(s):
    s=copy.deepcopy(s);s['revision']+=1
    next(c for c in s['components'] if c['component_id']=='canopy')['parameters']['min_m'][2]=2
    return s
class SpecTests(unittest.TestCase):
    def setUp(self):self.s=migrate(sample())
    def binding(self):
        c=self.s['components'][0];f=self.s['evidence']['facts'][0]['fact_id']
        b={'component_id':c['component_id'],'parameter_path':'/min_m/0','adopted_value':c['parameters']['min_m'][0],'status':'design_choice','basis':'Synthetic protocol fixture; no survey claim','evidence_refs':[{'kind':'fact','id':f,'node_id':None}],'alternatives':[]}
        self.s['research']['parameter_bindings']=[b];return b
    def test_migration_preserves_geometry(self):self.assertEqual(generate(self.s)[0].fingerprint(),generate(sample())[0].fingerprint())
    def test_no_model_route(self):self.s['research']['model_status']='not_found';validate_spec(self.s)
    def test_valid_binding(self):self.binding();validate_spec(self.s)
    def test_binding_wrong_value(self):self.binding()['adopted_value']=100;self.assertRaises(ValueError,validate_spec,self.s)
    def test_conflict_blocks_execution(self):self.binding()['status']='conflicted';self.assertRaises(ValueError,validate_spec,self.s)
    def test_dangling_binding(self):self.binding()['evidence_refs'][0]['id']='fact-missing';self.assertRaises(ValueError,validate_spec,self.s)
    def test_invalid_parameter_path(self):self.binding()['parameter_path']='/absent';self.assertRaises(ValueError,validate_spec,self.s)
    def test_unapproved_overlap(self):self.s['assembly']['allowed_overlaps']=[];self.assertRaises(ValueError,generate,self.s)
    def test_parent_cycle(self):self.s['assembly']['components'][0]['parent_id']=self.s['components'][0]['component_id'];self.assertRaises(ValueError,validate_spec,self.s)
    def model(self):
        m={'model_id':'model-one','sha256':'a'*64,'format':'synthetic','source_id':None,'license_status':'unknown','version':None,'status':'checked','transform':{'metres_per_source_unit':.001,'source_axes':'synthetic Y up','matrix_to_local_m':[[.001,0,0,0],[0,.001,0,0],[0,0,.001,0],[0,0,0,1]],'anchor_ids':['a','b','c'],'residual_m':0,'basis':'Synthetic contract fixture; no SU parsed'}}
        self.s['research'].update(model_status='available',models=[m]);return m
    def test_units_matrix_consistent(self):self.model();validate_spec(self.s)
    def test_units_mismatch(self):self.model()['transform']['metres_per_source_unit']=1;self.assertRaises(ValueError,validate_spec,self.s)
    def test_nonuniform_transform(self):self.model()['transform']['matrix_to_local_m'][0][0]=.002;self.assertRaises(ValueError,validate_spec,self.s)
    def test_new_extra_fields_rejected(self):self.s['research']['magic']=True;self.assertRaises(ValueError,validate_spec,self.s)
class RevisionTests(unittest.TestCase):
    def test_canopy_six_cells(self):s=sample();r=guard_revision(s,changed(s),request());self.assertEqual(r['changed_cells'],6)
    def test_locked_scale(self):s=sample();a=changed(s);a['coordinates']['blocks_per_metre']=2;self.assertRaises(ValueError,guard_revision,s,a,request())
    def test_other_component_change(self):s=sample();a=changed(s);a['components'][0]['parameters']['max_m'][0]-=1;self.assertRaises(ValueError,guard_revision,s,a,request())
    def test_bound_parameter_edit(self):
        s=migrate(sample());c=next(c for c in s['components'] if c['component_id']=='canopy')
        s['research']['parameter_bindings']=[{'component_id':'canopy','parameter_path':'/min_m/2','adopted_value':c['parameters']['min_m'][2],'status':'design_choice','basis':'Initial study choice','evidence_refs':[{'kind':'fact','id':s['evidence']['facts'][0]['fact_id'],'node_id':None}],'alternatives':[]}]
        a=changed(s);a['research']['parameter_bindings'][0]['adopted_value']=2;a['research']['parameter_bindings'][0]['basis']='Explicit canopy extension study'
        self.assertEqual(guard_revision(s,a,request())['changed_cells'],6)
    def test_binding_cannot_change_source_during_edit(self):
        s=migrate(sample());a=changed(s);a['research']['model_status']='not_found'
        self.assertRaises(ValueError,guard_revision,s,a,request())
    def test_protected_region(self):s=sample();r=request();r['protected_regions']=[[14,6,2,19,6,2]];self.assertRaises(ValueError,guard_revision,s,changed(s),r)
    def test_small_roi(self):s=sample();r=request();r['allowed_region']=[0,0,0,1,1,1];self.assertRaises(ValueError,guard_revision,s,changed(s),r)
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'output/legacy_gafa_colonnade';self.s=load_spec(self.root/'building_spec.json');b=json.loads((self.root/'build_report.json').read_text());im=self.s['evidence']['images'][0]['image_id']
        self.r={'schema_version':'0.1','build_id':b['build_id'],'method':'manual','game_status':'pending_game_test','required_image_ids':[im],'pairs':[{'pair_id':'review-one','image_id':im,'component_ids':[self.s['components'][0]['component_id']],'view':'front','camera_match':'unverifiable','status':'unverifiable','severity':None,'finding':'Test fixture; perspective cannot be registered','checkpoints':['silhouette']}]}
    def test_unverifiable_preserved(self):self.assertEqual(validate_review(self.r,self.s,self.root)['visual_status'],'pass_with_gaps')
    def test_unverifiable_cannot_pass(self):self.r['pairs'][0]['status']='pass';self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_component_id_checked(self):self.r['pairs'][0]['component_ids']=['absent'];self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_build_id_checked(self):self.r['build_id']='old';self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_missing_reference_pair(self):self.r['pairs']=[];self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_major_issue_not_pass(self):self.r['pairs'][0].update(camera_match='approximate',severity='major',status='pass');self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_no_fake_game_pass(self):self.r['game_status']='pass';self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
    def test_stale_spec_rejected(self):self.s['revision']+=1;self.assertRaises(ValueError,validate_review,self.r,self.s,self.root)
if __name__=='__main__':unittest.main(verbosity=2)
