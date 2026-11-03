import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
import trimesh
from architect.model_io import ModelAsset,mesh,node,analyze,read_model,save_asset,load_asset,export_mesh,coordinates,attach_candidate,candidate_record,local_resource,world_meshes
from architect.model_compare import compare
from architect.spec_loader import load_spec
from architect.legacy import ROOT

def fixture():
    a=ModelAsset({'schema_version':'model-evidence-0.1','model_id':'model-fixture','source':{'sha256':'a'*64,'format':'synthetic','license_status':'unknown'},'reader':{},'nodes':[],'warnings':[]})
    g=trimesh.creation.box(extents=[2,4,6]);mesh(a,'mesh-a',g.vertices,g.faces)
    node(a,'node-root','root',None,np.eye(4));t=np.eye(4);t[:3,3]=[10,20,30]
    node(a,'node-parent','building', 'node-root',t)
    r=np.eye(4);r[:3,:3]=[[0,0,1],[0,1,0],[-1,0,0]]
    node(a,'node-one','frame', 'node-parent',r,['mesh-a'])
    r=np.eye(4);r[0,0]=-1;r[:3,3]=[-5,3,8]
    node(a,'node-two','mirrored', 'node-parent',r,['mesh-a'])
    return analyze(a)

class ModelIOTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.a=fixture()
    def tearDown(self):self.temp.cleanup()
    def roundtrip(self,ext):
        p=self.root/('sample.'+ext);export_mesh(self.a,p)
        b=read_model(p,**({'metres_per_unit':1,'up':'Y'} if ext in ('obj','stl','ply') else {}))
        result=compare(self.a,b,tolerance_m=.0001);self.assertEqual(result['status'],'pass',result)
        return b
    def test_glb_nested_mirrored_instances(self):self.roundtrip('glb')
    def test_gltf_embedded_buffers(self):self.roundtrip('gltf')
    def test_obj_geometry(self):self.roundtrip('obj')
    def test_stl_geometry(self):self.roundtrip('stl')
    def test_ply_geometry(self):self.roundtrip('ply')
    def test_dae_geometry(self):self.roundtrip('dae')
    def test_obj_requires_unit(self):
        p=self.root/'x.obj';p.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n');self.assertRaises(ValueError,read_model,p)
    def test_axis_conversion_is_right_handed(self):
        t=coordinates(.001,'Z');np.testing.assert_allclose(t[:3,:3]@[0,0,1000],[0,1,0]);self.assertGreater(np.linalg.det(t[:3,:3]),0)
    def test_invalid_scale(self):self.assertRaises(ValueError,coordinates,float('nan'),'Y')
    def test_unsupported_format(self):
        p=self.root/'x.fbx';p.write_text('not a decoder');self.assertRaises(ValueError,read_model,p)
    def test_empty_mesh_rejected(self):self.assertRaises(ValueError,mesh,self.a,'new',[[0,0,0]],[])
    def test_nonfinite_rejected(self):self.assertRaises(ValueError,mesh,self.a,'new',[[0,0,0],[1,0,0],[0,float('nan'),0]],[[0,1,2]])
    def test_out_of_range_index(self):self.assertRaises(ValueError,mesh,self.a,'new',[[0,0,0],[1,0,0],[0,1,0]],[[0,1,9]])
    def test_noninteger_indices(self):self.assertRaises(ValueError,mesh,self.a,'new',[[0,0,0],[1,0,0],[0,1,0]],[[0.,1.,2.]])
    def test_disconnected_parent(self):self.a.document['nodes'][1]['parent_id']='missing';self.assertRaises(ValueError,analyze,self.a)
    def test_repeated_node_id(self):self.a.document['nodes'][1]['node_id']='node-root';self.assertRaises(ValueError,analyze,self.a)
    def test_asset_byte_hash(self):
        out=self.root/'asset';save_asset(self.a,out);b=load_asset(out);self.assertEqual(compare(self.a,b)['status'],'pass')
        with (out/'geometry.npz').open('ab') as f:f.write(b'changed')
        self.assertRaises(ValueError,load_asset,out)
    def test_no_overwrite(self):
        out=self.root/'asset';save_asset(self.a,out);self.assertRaises(FileExistsError,save_asset,self.a,out)
    def test_node_selection(self):
        parts=list(world_meshes(self.a,['node-one']));self.assertEqual(len(parts),1)
        self.assertRaises(ValueError,list,world_meshes(self.a,['absent']))
    def test_geometry_change_detected(self):
        b=copy.deepcopy(self.a);b.meshes['mesh-a']['vertices'][0,0]+=.1
        self.assertEqual(compare(self.a,b)['status'],'fail')
    def test_no_path_escape(self):self.assertRaises(ValueError,local_resource,self.root/'x.gltf','../secret.bin')
    def test_no_remote_resource(self):self.assertRaises(ValueError,local_resource,self.root/'x.gltf','https://example.com/a.bin')
    def test_gltf_missing_buffer_rejected(self):
        p=self.root/'x.gltf';p.write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':'missing.bin','byteLength':4}]}));self.assertRaises(ValueError,read_model,p)
    def test_gltf_animation_rejected(self):
        p=self.root/'x.gltf';p.write_text(json.dumps({'asset':{'version':'2.0'},'animations':[{}]}));self.assertRaises(ValueError,read_model,p)
    def test_gltf_required_extension_rejected(self):
        p=self.root/'x.gltf';p.write_text(json.dumps({'asset':{'version':'2.0'},'extensionsRequired':['KHR_draco_mesh_compression']}));self.assertRaises(ValueError,read_model,p)
    def test_gltf_conflicting_scale(self):
        p=self.root/'x.glb';export_mesh(self.a,p);self.assertRaises(ValueError,read_model,p,metres_per_unit=.001)
    def test_read_identity_deterministic(self):
        p=self.root/'x.glb';export_mesh(self.a,p)
        a=read_model(p);b=read_model(p)
        self.assertEqual([n['node_id'] for n in a.document['nodes']],[n['node_id'] for n in b.document['nodes']])
    def test_candidate_does_not_claim_alignment(self):
        rec=candidate_record(self.a);self.assertEqual(rec['status'],'candidate');self.assertIsNone(rec['transform'])
    def test_attach_candidate_preserves_executable_components(self):
        s=load_spec(ROOT/'examples/upgrade/retail_store/building_spec.json');b=attach_candidate(s,self.a)
        self.assertEqual(b['components'],s['components']);self.assertEqual(b['research']['models'][0]['status'],'candidate')
        self.assertRaises(ValueError,attach_candidate,b,self.a)
    def test_dae_millimetres_and_z_up(self):
        p=self.root/'tiny.dae';p.write_text('''<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1"><asset><unit name="millimeter" meter="0.001"/><up_axis>Z_UP</up_axis></asset><library_geometries><geometry id="g"><mesh><source id="p"><float_array id="a" count="9">0 0 0 1000 0 0 0 0 2000</float_array><technique_common><accessor source="#a" count="3" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source><vertices id="v"><input semantic="POSITION" source="#p"/></vertices><triangles count="1"><input semantic="VERTEX" source="#v" offset="0"/><p>0 1 2</p></triangles></mesh></geometry></library_geometries><library_visual_scenes><visual_scene id="s"><node id="parent"><translate>1000 0 0</translate><node id="child"><instance_geometry url="#g"/></node></node></visual_scene></library_visual_scenes><scene><instance_visual_scene url="#s"/></scene></COLLADA>''')
        a=read_model(p);np.testing.assert_allclose(a.document['statistics']['bounds_m'],[[1,0,0],[2,2,0]])

class NativeSkpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from openskp import create
        cls.temp=tempfile.TemporaryDirectory();cls.path=Path(cls.temp.name)/'inches.skp'
        b=create()
        with b.add_component_definition('survey_fixture') as d:d.add_face([(0,0,0),(100,0,0),(0,0,200)])
        b.add_instance(d,name='translated',translation=(10,0,20));b.save(str(cls.path))
        cls.a=read_model(cls.path)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_inches_not_display_units(self):np.testing.assert_allclose(self.a.document['statistics']['size_m'],[2.54,5.08,0],atol=1e-6)
    def test_nested_translation_applied(self):np.testing.assert_allclose(self.a.document['statistics']['bounds_m'][0],[.254,.508,0],atol=1e-6)
    def test_skp_scene_has_real_mesh(self):self.assertGreater(self.a.document['statistics']['placed_triangles'],0)

if __name__=='__main__':unittest.main(verbosity=2)
