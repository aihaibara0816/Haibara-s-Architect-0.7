import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from reference_set import migrate as migrate_packet
from validate_packet import validate
import selftest as fixtures
def packet(count=10):
    p=fixtures.report()
    for i in range(count):fixtures.image(p,'img-'+str(i))
    p=migrate_packet(p);s=p['selection'];s['coverage_requirements']=[]
    s['core']=[{'image_id':im['image_id'],'purpose':'Synthetic view fixture','rationale':'Protocol test, not actual photo'} for im in p['images']]
    p['prompts']['image_ids']=[x['image_id'] for x in s['core']]
    return p

class ReferenceTests(unittest.TestCase):
    def test_legacy_ids_and_unknown_source_date(self):
        p=packet(1);p['images'][0]['image_id']='R01'
        p['selection']['core'][0]['image_id']='R01';p['selection']['views'][0]['image_id']='R01';p['prompts']['image_ids']=['R01'];p['sources'][0]['accessed_at']=None;p['sources'][0]['title']=None
        r=validate(p,'template');self.assertNotEqual(r['status'],'FAIL');self.assertTrue(r['gaps'])
    def test_verified_fact_needs_source_visit(self):
        p=packet(1);fixtures.dimension(p);p['sources'][0]['accessed_at']=None
        self.assertEqual(validate(p,'template')['status'],'FAIL')
    def test_ten_core_and_extra_detail(self):
        p=packet();p['components']=[{'component_id':'component-crown','name':'crown','parent_component_id':None,'fact_ids':[]}]
        fixtures.image(p,'img-detail');p['selection']['views'].append({'image_id':'img-detail','face':'unknown','orientation_basis':None,'layer':'outer','occlusion':'unknown','component_ids':['component-crown'],'duplicate_of':None,'sha256':None})
        p['selection']['detail_groups']=[{'component_id':'component-crown','image_ids':['img-detail'],'purpose':'crown detail'}];p['prompts']['image_ids'].append('img-detail')
        self.assertNotEqual(validate(p,'template')['status'],'FAIL')
    def test_one_image_not_padded(self):
        p=packet(1);self.assertNotEqual(validate(p,'template')['status'],'FAIL');self.assertEqual(len(p['selection']['core']),1)
    def test_missing_back_is_gap(self):
        p=packet();p['selection']['coverage_requirements']=[{'face':'back','component_id':None,'missing_search':'Find verified rear photo'}]
        r=validate(p,'template');self.assertTrue(r['gaps']);self.assertEqual(r['coverage'][0]['status'],'missing')
    def test_known_direction_requires_basis(self):
        p=packet();p['selection']['views'][0]['face']='front';self.assertEqual(validate(p,'template')['status'],'FAIL')
    def test_duplicate_hash_cannot_inflate_core(self):
        p=packet(2)
        for x in p['selection']['views']:x['sha256']='a'*64
        self.assertEqual(validate(p,'template')['status'],'FAIL')
    def test_duplicate_relationship_cannot_be_core(self):
        p=packet(2);p['selection']['views'][1]['duplicate_of']='img-0';self.assertEqual(validate(p,'template')['status'],'FAIL')
    def test_dangling_detail_component(self):
        p=packet();p['selection']['detail_groups']=[{'component_id':'component-absent','image_ids':['img-0'],'purpose':'x'}];self.assertEqual(validate(p,'template')['status'],'FAIL')
    def test_migration_preserves_original(self):
        p=fixtures.report();old=copy.deepcopy(p);new=migrate_packet(p)
        self.assertEqual(p,old);self.assertEqual(new['images'],old['images']);self.assertEqual(new['selection']['legacy_slots'],old['selection']['slots'])
    def test_local_hash_and_path_checked(self):
        p=packet(1);im=p['images'][0];im.update(page_url=None,source_ids=[],local_file='photo.bin')
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'photo.bin';f.write_bytes(b'fixture');im['local_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
            self.assertNotEqual(validate(p,'template',d)['status'],'FAIL')
            im['local_sha256']='0'*64;self.assertEqual(validate(p,'template',d)['status'],'FAIL')
    def test_unknown_view_cannot_count_as_coverage(self):
        p=packet();p['selection']['coverage_requirements']=[{'face':'unknown','component_id':None,'missing_search':'Need direction evidence'}]
        self.assertEqual(validate(p,'template')['coverage'][0]['status'],'missing')

if __name__=="__main__":unittest.main(verbosity=2)
