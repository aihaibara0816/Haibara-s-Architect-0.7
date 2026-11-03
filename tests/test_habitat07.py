import copy
import json
from pathlib import Path
import tempfile
import unittest
import gzip
import hashlib
import struct
from hafusion.habitat07 import compile_scene,build_scene,verify_scene,dispatch_scene,RECIPES
from hafusion.archive07 import catalog,find_case,verify_case,export_case

ROOT=Path(__file__).resolve().parents[1]
def example(name='reading-garden'):
    return json.loads((ROOT/'examples/habitat07'/f'{name}.json').read_text('utf8'))

class HabitatTests(unittest.TestCase):
    def test_all_recipes_compile_within_declared_envelope(self):
        for recipe in RECIPES:
            r=example();r['modules']=[{'id':'sample','recipe':recipe,'origin':[2,1,2]}]
            s,p=compile_scene(r);self.assertGreater(p['non_air_blocks'],45*36)
            self.assertEqual(p['terrain_changes'],0)

    def test_same_seed_and_input_reorder_preserve_all_geometry(self):
        a=example();b=copy.deepcopy(a);b['modules'].reverse()
        self.assertEqual(compile_scene(a)[0].fingerprint(),compile_scene(b)[0].fingerprint())

    def test_added_component_does_not_change_existing_component(self):
        a=example();b=copy.deepcopy(a);b['modules'].append({'id':'new-pot','recipe':'planter','origin':[2,1,23]})
        sa,_=compile_scene(a);sb,_=compile_scene(b)
        for q,owner in sa.owners.items():
            if owner!='terrain':self.assertEqual(sa.blocks[q],sb.blocks[q])

    def test_changed_seed_preserves_room_envelope_furniture_and_lights(self):
        a=example();b=copy.deepcopy(a);b['seed']=2718
        sa,_=compile_scene(a);sb,_=compile_scene(b)
        for q,owner in sa.owners.items():
            if owner=='library' and not sa.blocks[q].startswith('minecraft:potted_'):
                self.assertEqual(sa.blocks[q],sb.blocks[q])

    def test_unrelated_terrain_slope_is_not_flattened(self):
        r=example();r['terrain']['height_rows'][35][0]=4
        s,_=compile_scene(r);self.assertIn((0,4,35),s.blocks);self.assertNotIn((0,5,35),s.blocks)

    def test_unsupported_floor_is_rejected(self):
        r=example();r['terrain']['height_rows'][4][3]=1
        with self.assertRaises(ValueError):compile_scene(r)

    def test_canopy_keepout_and_water_are_protected(self):
        r=example();r['keepouts'].append([25,1,2,34,20,11])
        with self.assertRaises(ValueError):compile_scene(r)
        r=example();r['terrain']['water_cells']=[[29,6]]
        with self.assertRaises(ValueError):compile_scene(r)

    def test_final_late_decoration_cannot_block_a_use_probe(self):
        r=example();r['modules'].append({'id':'zz-blocking-pot','recipe':'planter','origin':[8,2,12]})
        with self.assertRaises(ValueError):compile_scene(r)

    def test_bad_seed_ids_recipe_and_volume_are_rejected(self):
        for v in [True,1.2,-1,'1145']:
            r=example();r['seed']=v
            with self.assertRaises(ValueError):compile_scene(r)
        r=example();r['modules'][1]['id']=r['modules'][0]['id']
        with self.assertRaises(ValueError):compile_scene(r)
        r=example();r['modules'][0]['recipe']='../../script.py'
        with self.assertRaises(ValueError):compile_scene(r)
        r=example();r['terrain']['size_xyz']=[160,160,160]
        with self.assertRaises(ValueError):compile_scene(r)

    def test_readback_and_replay_are_exact_and_run_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            r=build_scene(example(),td,'sample');self.assertEqual(r['status']['nbt'],'exact_readback')
            self.assertEqual(verify_scene(td,'sample')['status'],'pass')
            with self.assertRaises(FileExistsError):build_scene(example(),td,'sample')
            p=Path(td)/'sample/scene.nbt';p.write_bytes(p.read_bytes()+b'x')
            with self.assertRaises(ValueError):verify_scene(td,'sample')

    def test_unsafe_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):build_scene(example(),td,'../outside')

    def test_model_additions_preserve_host_base_and_need_explicit_execution(self):
        base=example();before=copy.deepcopy(base)
        call={'name':'ha_scene_add_modules','arguments':{'modules':[{'id':'new-pot','recipe':'planter','origin':[2,1,23]}]}}
        with tempfile.TemporaryDirectory() as td:
            r=dispatch_scene(call,base,td,'added');self.assertFalse(r['generated_geometry']);self.assertFalse((Path(td)/'added').exists());self.assertEqual(base,before)
            dispatch_scene(call,base,td,'added',True);self.assertEqual(verify_scene(td,'added')['status'],'pass')
            for bad in [dict(call,name='shell'),dict(call,path='escape'),{'name':call['name'],'arguments':{'modules':call['arguments']['modules'],'seed':2}},{'name':call['name'],'arguments':{'modules':[base['modules'][0]]}}]:
                with self.assertRaises(ValueError):dispatch_scene(bad,base,td,'bad')

    def test_manifest_type_and_nbt_summary_are_checked(self):
        with tempfile.TemporaryDirectory() as td:
            build_scene(example(),td,'sample');p=Path(td)/'sample/manifest.json';m=json.loads(p.read_text('utf8'))
            for bad in [[],dict(m,nbt={}),dict(m,release='0.6.0')]:
                p.write_text(json.dumps(bad),'utf8')
                with self.assertRaises(ValueError):verify_scene(td,'sample')

    def test_nbt_size_version_entities_and_air_coverage_are_checked(self):
        with tempfile.TemporaryDirectory() as td:
            build_scene(example(),td,'sample');p=Path(td)/'sample';original=(p/'scene.nbt').read_bytes();m=json.loads((p/'manifest.json').read_text('utf8'))
            for kind in ['size','version','entity','air']:
                raw=gzip.decompress(original)
                if kind=='size':raw=raw.replace(b'\x03\x00\x00\x00\x03'+struct.pack('>iii',45,20,36),b'\x03\x00\x00\x00\x03'+struct.pack('>iii',46,20,36),1)
                elif kind=='version':raw=raw.replace(b'DataVersion'+struct.pack('>i',3955),b'DataVersion'+struct.pack('>i',3954),1)
                elif kind=='entity':raw=raw.replace(b'entities\x0a\x00\x00\x00\x00',b'entities\x0a\x00\x00\x00\x01\x00',1)
                else:
                    # Export the correct scene without explicit air; physical blocks remain identical.
                    from vendor.voxel_core import export_structure
                    temp=Path(td)/'no-air.nbt';export_structure(compile_scene(example())[0],temp,include_air=False);raw=gzip.decompress(temp.read_bytes())
                changed=gzip.compress(raw,mtime=0);self.assertNotEqual(changed,original)
                (p/'scene.nbt').write_bytes(changed);m['artifacts']['scene.nbt']={'bytes':len(changed),'sha256':hashlib.sha256(changed).hexdigest()};(p/'manifest.json').write_text(json.dumps(m),'utf8')
                with self.assertRaises(ValueError):verify_scene(td,'sample')
                (p/'scene.nbt').write_bytes(original)

class ArchiveTests(unittest.TestCase):
    def test_public_packs_and_images_exist_and_hashes_match(self):
        entries=catalog()['entries'];self.assertGreaterEqual(len(entries),36)
        self.assertEqual(len({c['id'] for c in entries}),len(entries))
        for c in entries:self.assertEqual(verify_case(c['id'])['status'],'pass')

    def test_export_preserves_exact_archive_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            r=export_case('room06',td);self.assertTrue(Path(r['output']).exists());self.assertFalse(r['generated'])
            with self.assertRaises(FileExistsError):export_case('room06',td)

    def test_unknown_case_and_personal_installation_not_invented(self):
        with self.assertRaises(ValueError):find_case('invented-case')
        d=json.loads((ROOT/'knowledge/workflow07.json').read_text('utf8'))
        self.assertEqual(d['skill_installation']['personal_skills'],'not_installed_by_this_release')

if __name__=='__main__':unittest.main()
