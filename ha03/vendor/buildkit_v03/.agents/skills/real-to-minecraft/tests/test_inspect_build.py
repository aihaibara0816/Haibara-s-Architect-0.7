"""Synthetic regression fixtures. These are NOT Minecraft gameplay tests."""
import gzip
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'inspect_build.py'
spec = importlib.util.spec_from_file_location('inspect_build', TOOL)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def string(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def payload(k, v):
    # Tiny synthetic-fixture encoder; not a production schematic exporter.
    if k in (1,2,3,4,5,6):
        return struct.pack('>'+{1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[k], v)
    if k == 7:
        return struct.pack('>i',len(v))+v
    if k == 8:
        return string(v)
    if k == 9:
        subtype, seq = v
        return bytes([subtype])+struct.pack('>i',len(seq))+b''.join(payload(subtype,x) for x in seq)
    if k == 10:
        return b''.join(bytes([t])+string(name)+payload(t,val) for name,(t,val) in v.items())+b'\x00'
    if k in (11,12):
        fmt = 'i' if k == 11 else 'q'
        return struct.pack('>i',len(v))+b''.join(struct.pack('>'+fmt,x) for x in v)
    raise ValueError(k)


def nbt(root, name=''):
    return b'\x0a'+string(name)+payload(10,root)


def structure(blocks=None, names=None, size=(3,3,3)):
    if blocks is None:
        blocks = [(0,0,0,0),(2,1,1,1)]
    if names is None:
        names = ['minecraft:stone','minecraft:glass']
    return {
        'DataVersion':(3,0), # Arbitrary synthetic value; not a game-version claim.
        'size':(9,(3,list(size))),
        'palette':(9,(10,[{'Name':(8,name)} for name in names])),
        'blocks':(9,(10,[{'pos':(9,(3,list(b[:3]))),'state':(3,b[3])} for b in blocks])),
        'entities':(9,(10,[]))}


def schematic(version, data=b'\x00\x01\x00\x01\x00\x01\x00\x01', indices=(0,1), nested=False):
    body={'Version':(3,version),'DataVersion':(3,0),
          'Width':(2,2),'Height':(2,2),'Length':(2,2),'Offset':(11,[3,0,5])}
    block={'Palette':(10,{'minecraft:air':(3,indices[0]),'minecraft:stone':(3,indices[1])}),
           'Data' if version==3 else 'BlockData':(7,data),'BlockEntities':(9,(10,[]))}
    if version==3:
        body['Blocks']=(10,block)
    else:
        body.update(block)
    return {'Schematic':(10,body)} if nested else body

class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def put(self, root=None, raw=None, name='test.nbt', compressed=False):
        data=raw if raw is not None else nbt(root if root is not None else structure())
        path=self.root/name
        path.write_bytes(gzip.compress(data,mtime=0) if compressed else data)
        return path

    def load(self, root=None, **kw):
        return m.load_build(self.put(root,**kw))

    def test_raw_structure_counts(self):
        report=m.inspect(self.load())
        self.assertEqual(report['non_air_non_void_blocks'],2)
        self.assertEqual(report['occupied_bbox_inclusive'],[[0,0,0],[2,1,1]])
        self.assertEqual(report['size_xyz'],[3,3,3])
        self.assertEqual(report['game_validation'],'pending')

    def test_gzip_changes_only_binary_hash(self):
        a=m.inspect(self.load(name='raw.nbt'))
        b=m.inspect(self.load(compressed=True,name='gzip.nbt'))
        self.assertNotEqual(a['file_sha256'],b['file_sha256'])
        self.assertEqual(a['local_listed_blockstates_sha256'],b['local_listed_blockstates_sha256'])

    def test_palette_order_does_not_change_voxel_hash(self):
        a=self.load()
        b=self.load(structure([(0,0,0,1),(2,1,1,0)],['minecraft:glass','minecraft:stone']),name='b.nbt')
        self.assertEqual(m.inspect(a)['local_listed_blockstates_sha256'],m.inspect(b)['local_listed_blockstates_sha256'])

    def test_explicit_air_is_not_absent_for_placement(self):
        a=self.load(structure([],['minecraft:air']))
        b=self.load(structure([(0,0,0,0)],['minecraft:air']),name='b.nbt')
        d=m.compare(a,b)
        self.assertEqual(d['listed_state_changes'],1)
        self.assertEqual(d['visible_state_changes'],0)

    def test_structure_void_is_not_counted_as_building(self):
        report=m.inspect(self.load(structure([(0,0,0,0)],['minecraft:structure_void'])))
        self.assertEqual(report['structure_void_entries'],1)
        self.assertFalse(report['usable_nonempty_sample'])

    def test_duplicate_coordinates_rejected(self):
        with self.assertRaises(m.InvalidBuild):
            self.load(structure([(0,0,0,0),(0,0,0,1)]))

    def test_out_of_bounds_rejected(self):
        for p in [(3,0,0,0),(-1,0,0,0)]:
            with self.assertRaises(m.InvalidBuild):self.load(structure([p]))

    def test_invalid_palette_reference_rejected(self):
        for index in (-1,2):
            with self.assertRaises(m.InvalidBuild):self.load(structure([(0,0,0,index)]))

    def test_invalid_namespaced_id_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(structure([(0,0,0,0)],['bad id']))

    def test_property_order_is_canonicalized(self):
        self.assertEqual(m.state_name('minecraft:oak_stairs[facing=north,half=bottom]'),
                         m.state_name('minecraft:oak_stairs',{'half':'bottom','facing':'north'}))

    def test_trailing_nbt_data_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(raw=nbt(structure())+b'\x00')

    def test_truncated_gzip_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(raw=gzip.compress(nbt(structure()))[:-5])

    def test_decoded_byte_limit(self):
        path=self.put(compressed=True)
        with self.assertRaises(m.InvalidBuild):m.load_build(path,m.Limits(decoded_bytes=16))

    def test_input_file_byte_limit(self):
        path=self.put()
        with self.assertRaises(m.InvalidBuild):m.load_build(path,m.Limits(file_bytes=10))

    def test_cell_budget(self):
        path=self.put()
        with self.assertRaises(m.InvalidBuild):m.load_build(path,m.Limits(cells=10))

    def test_negative_list_length_rejected(self):
        data=b'\x0a\x00\x00'+b'\x09'+string('x')+b'\x03'+struct.pack('>i',-1)+b'\x00'
        with self.assertRaises(m.InvalidBuild):self.load(raw=data)

    def test_duplicate_compound_keys_rejected(self):
        field=b'\x03'+string('x')+struct.pack('>i',1)
        with self.assertRaises(m.InvalidBuild):self.load(raw=b'\x0a\x00\x00'+field+field+b'\x00')

    def test_multi_palette_not_silently_accepted(self):
        root=structure()
        root['palettes']=(9,(9,[]))
        with self.assertRaises(m.InvalidBuild):self.load(root)

    def test_unknown_format_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load({'Width':(2,4)})

    def test_sponge_v2_axis_order(self):
        build=self.load(schematic(2),name='test.schem')
        self.assertEqual(build.blocks[(1,1,1)],'minecraft:stone')
        self.assertEqual(build.blocks[(0,1,1)],'minecraft:air')
        self.assertEqual(build.info['offset_xyz'],[3,0,5])
        self.assertEqual(m.inspect(build)['non_air_non_void_blocks'],4)

    def test_sponge_v3_nested(self):
        build=self.load(schematic(3,nested=True),name='test.schem',compressed=True)
        self.assertEqual(build.info['format'],'sponge_schematic_v3')
        self.assertEqual(build.blocks[(1,0,1)],'minecraft:stone')

    def test_varint_over_127(self):
        data=b'\x00\x81\x01'*4
        build=self.load(schematic(3,data=data,indices=(0,129)))
        self.assertEqual(m.inspect(build)['non_air_non_void_blocks'],4)

    def test_truncated_varint_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(schematic(3,data=b'\x80'))

    def test_overlong_varint_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(schematic(3,data=b'\x80'*6))

    def test_excess_varint_entries_rejected(self):
        with self.assertRaises(m.InvalidBuild):self.load(schematic(3,data=b'\x00'*9))

    def test_roi_reports_changes_outside_target(self):
        a=self.load()
        b=self.load(structure([(0,0,0,1),(2,1,1,0)]),name='b.nbt')
        d=m.compare(a,b,[0,0,0,0,0,0])
        self.assertEqual(d['listed_state_changes'],2)
        self.assertEqual(d['changes_outside_roi'],1)

    def test_cli_never_overwrites_input(self):
        path=self.put()
        original=path.read_bytes()
        result=subprocess.run([sys.executable,str(TOOL),str(path),'--out',str(path)],capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(path.read_bytes(),original)

    def test_cli_report_can_be_created(self):
        path=self.put(compressed=True)
        output=self.root/'report.json'
        result=subprocess.run([sys.executable,str(TOOL),str(path),'--out',str(output)],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('"game_validation": "pending"',output.read_text())

    def test_empty_structure_reports_unusable(self):
        report=m.inspect(self.load(structure([],['minecraft:air'])))
        self.assertFalse(report['usable_nonempty_sample'])

    def test_other_nbt_numeric_tags_do_not_break_parser(self):
        root=structure()
        root['SyntheticMetadata']=(10,{'byte':(1,-1),'short':(2,22),'long':(4,5000000000),
            'float':(5,0.5),'double':(6,0.25),'longs':(12,[1,-2]),'bytes':(7,b'\x00\xff')})
        self.assertTrue(m.inspect(self.load(root))['usable_nonempty_sample'])

    def test_modified_utf8_nul_in_unused_metadata(self):
        field=b'\x08'+string('metadata')+b'\x00\x02\xc0\x80'
        data=nbt(structure())[:-1]+field+b'\x00'
        self.assertEqual(m.inspect(self.load(raw=data))['non_air_non_void_blocks'],2)

if __name__=='__main__':
    unittest.main(verbosity=2)
