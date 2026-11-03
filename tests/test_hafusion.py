import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from hafusion.evidence import apply_reviewed,apply_building_spec,arbitrate
from research_lab.stage_cache import DiskCache,digest,stage_key
from hafusion.qa import circulation
from hafusion.canton import scene
from member_shapes import block_parts

class EvidenceTests(unittest.TestCase):
    def change(self):return dict(path='/height',old=4,new=5,review='accepted',status='estimated',reason='Explicit study choice',evidence=['study'])
    def test_stale_base_rejected(self):
        with self.assertRaises(ValueError):apply_reviewed({'height':4},[self.change()],'stale',lambda _:None,{'/height'})
    def test_input_remains_unchanged(self):
        a={'height':4};b=apply_reviewed(a,[self.change()],digest(a),lambda _:None,{'/height'});self.assertEqual(a,{'height':4});self.assertEqual(b['height'],5)
    def test_unreviewed_rejected(self):
        p=self.change();p['review']='pending'
        with self.assertRaises(ValueError):apply_reviewed({'height':4},[p],digest({'height':4}),lambda _:None,{'/height'})
    def test_undeclared_path_rejected(self):
        with self.assertRaises(ValueError):apply_reviewed({'height':4},[self.change()],digest({'height':4}),lambda _:None,set())
    def test_existing_spec_adapter_runs_schema(self):
        from architect.spec_loader import validate_spec
        path=ROOT/'ha03/examples/upgrade/packet11_roundtrip/building_spec.json';s=json.loads(path.read_text());before=copy.deepcopy(s)
        p=dict(component_id='site.foundation',parameter_path='/max_m/1',old=1,new=.8,review='accepted',status='estimated',
               reason='Integration fixture: reduced foundation height, not a measured building',evidence=['fact-design-brief'],
               evidence_refs=[{'kind':'fact','id':'fact-design-brief','node_id':None}])
        out=apply_building_spec(s,[p],digest(s));validate_spec(out);self.assertEqual(s,before)
        self.assertEqual(out['research']['parameter_bindings'][0]['adopted_value'],.8)
    def test_same_rank_conflict_does_not_average(self):
        rows=[dict(component_id='x',attribute='width',value=v,unit='m',source_id=f's{i}',source_family=f'f{i}',epoch='now',phase='as_built',status='observed',source_type='photo') for i,v in enumerate([4,8])]
        r=arbitrate(rows,kind='length',tolerance=.1,target_epoch='now',source_order=['photo'],baseline_hash='x')
        self.assertEqual(r['status'],'needs_review');self.assertIsNone(r['selected'])

class CacheTests(unittest.TestCase):
    def test_corrupt_cache_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            c=DiskCache(d);key=digest('x');c.get_or_build(key,'test',lambda:[1]);p=Path(d)/(key+'.json');obj=json.loads(p.read_text());obj['payload']=[2];p.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):c.get_or_build(key,'test',lambda:[3])
    def test_roles_and_frame_change_key(self):
        ctx=dict(frame_id='a',units='block',target_epoch='now',source_hash='s')
        a=stage_key('geometry','x','1',{},dict(left='x',right='y'),ctx)
        self.assertNotEqual(a,stage_key('geometry','x','1',{},dict(left='y',right='x'),ctx))
        self.assertNotEqual(a,stage_key('geometry','x','1',{},dict(left='x',right='y'),{**ctx,'frame_id':'b'}))

class PlanCraftBridgeTests(unittest.TestCase):
    def test_blocked_court_detected(self):
        blocks={(x,1,z):'minecraft:stone' for x in range(10) for z in range(10)}
        for x in range(2,8):
          for z in range(2,8):
            if x in [2,7] or z in [2,7]:
              for y in range(2,5):blocks[x,y,z]='minecraft:stone'
        a=circulation(blocks,(10,24,10),[('room',4,2,4)]);self.assertFalse(a['targets'][0]['reachable'])
        for y in [2,3]:del blocks[2,y,4]
        b=circulation(blocks,(10,24,10),[('room',4,2,4)]);self.assertTrue(b['targets'][0]['reachable'])
    def test_static_check_does_not_mutate_blocks(self):
        b={(4,1,4):'minecraft:stone'};old=copy.deepcopy(b);circulation(b,(8,24,8),[('p',4,2,4)]);self.assertEqual(b,old)

if __name__=='__main__':unittest.main()
