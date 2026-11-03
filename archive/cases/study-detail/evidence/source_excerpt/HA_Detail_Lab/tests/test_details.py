import unittest,json,tempfile,hashlib
from pathlib import Path
from collections import Counter
from detail_lab.states import make,boxes,connect,rotate_scene,rotate_state,validate,family,DIRS
from detail_lab.builders import build,control,Builder
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build
ROOT=Path(__file__).resolve().parents[1]
CONFIGS=json.loads((ROOT/'configs/samples.json').read_text())

def volume(s):return sum((b[3]-b[0])*(b[4]-b[1])*(b[5]-b[2]) for b in boxes(s))
class DetailTests(unittest.TestCase):
    def test_geometry_volume_and_ranges(self):
        for kind,v in [('straight',.75),('inner_left',.875),('inner_right',.875),('outer_left',.625),('outer_right',.625)]:
            for facing in DIRS:
                for half in ['bottom','top']:
                    s=make('quartz_stairs',facing=facing,shape=kind,half=half);self.assertEqual(volume(s),v)
                    for b in boxes(s):self.assertTrue(all(0<=b[i]<b[i+3]<=1 for i in range(3)))
        for t,v in [('top',.5),('bottom',.5),('double',1)]:self.assertEqual(volume(make('quartz_slab',type=t)),v)
        self.assertEqual(volume(make('iron_trapdoor',open=True)),.1875)
        self.assertEqual(volume(make('glass_pane',east=True,west=True)),.125)
    def test_four_rotations_preserve_cells_states_and_owners(self):
        for c in CONFIGS:
            original=build(c);out=original
            for _ in range(4):out=rotate_scene(out)
            self.assertEqual(original.size,out.size);self.assertEqual(original.blocks,out.blocks);self.assertEqual(original.owners,out.owners)
    def test_rotated_visual_geometry_matches_rotated_states(self):
        def rotated(b):return (1-b[5],b[1],b[0],1-b[2],b[4],b[3])
        samples=[make('iron_trapdoor',facing=d,open=True) for d in DIRS]+[make('chain',axis=a) for a in 'xyz']
        samples += [make('quartz_stairs',facing=d,half=h,shape=s) for d in DIRS for h in ['top','bottom'] for s in ['straight','outer_left','outer_right','inner_left','inner_right']]
        samples += [make('glass_pane',north=True,east=True)]
        for s in samples:self.assertEqual(sorted(map(rotated,boxes(s))),sorted(boxes(rotate_state(s))),s)
    def test_connection_after_assembly_and_rotation(self):
        s=Scene((7,5,7));s.set((2,2,2),make('glass_pane'),'left');s.set((3,2,2),make('glass_pane'),'right');s.set((3,2,3),make('iron_bars'),'fin');s.set((4,2,2),make('smooth_quartz'),'column')
        connect(s);self.assertIn('east=true',s.blocks[(2,2,2)]);self.assertIn('west=true',s.blocks[(3,2,2)]);self.assertIn('south=true',s.blocks[(3,2,2)])
        self.assertEqual(connect(s),0)
        r=rotate_scene(s);before=dict(r.blocks);connect(r);self.assertEqual(before,r.blocks)
        s.set((3,2,2),'minecraft:air','remove');connect(s);self.assertIn('east=false',s.blocks[(2,2,2)])
    def test_unknown_states_fail(self):
        for s in ['minecraft:stone[axis=x]','minecraft:quartz_slab','minecraft:quartz_slab[type=side,waterlogged=false]','mod:glass','minecraft:glass_pane[east=true]']:
            with self.assertRaises((ValueError,IndexError)):validate(s)
    def test_unapproved_component_overlap_fails(self):
        b=Builder('example',(4,4,4));b.put((1,1,1),'glass','glass')
        with self.assertRaises(ValueError):b.put((1,1,1),'iron_block','column')
        b.put((1,1,1),'iron_block','column',replace=True);self.assertEqual(sum(b.replacements.values()),1)
    def test_eight_pairs_independent_roundtrip_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            for c in CONFIGS:
                detail=build(c);coarse=control(detail);self.assertEqual(detail.blocks.keys(),coarse.blocks.keys());self.assertNotEqual(detail.blocks,coarse.blocks)
                for tag,scene in [('A',coarse),('B',detail)]:
                    path=Path(tmp)/(c['id']+tag+'.nbt');info=export_structure(scene,path);decoded=load_build(path)
                    self.assertEqual({p:s for p,s in decoded.blocks.items() if s!='minecraft:air'},scene.blocks)
                    self.assertEqual(decoded.size,scene.size)
                    again=Path(tmp)/(c['id']+tag+'replay.nbt');export_structure(scene,again)
                    self.assertEqual(path.read_bytes(),again.read_bytes())
    def test_framework_glass_confined_to_functional_floors(self):
        s=build(next(c for c in CONFIGS if c['id']=='framework'))
        for (x,y,z),state in s.blocks.items():
            if 'glass' in state:self.assertTrue(14<=y<19)
        for p in [(10,8,8),(10,22,8)]:self.assertNotIn(p,s.blocks)
        self.assertIn((13,8,11),s.blocks)
    def test_ceiling_glass_and_background_are_separate(self):
        s=build(CONFIGS[0])
        self.assertIn('iron_bars',s.blocks[(5,3,4)]);self.assertIn('glass_pane',s.blocks[(5,3,5)])
        self.assertNotIn((5,3,6),s.blocks);self.assertIn('concrete',s.blocks[(5,3,15)])
        self.assertIn('slab',s.blocks[(5,6,8)])
        self.assertEqual(boxes(s.blocks[(5,6,8)])[0][1],0)
        self.assertEqual(boxes(s.blocks[(5,6,8)])[0][4],.5)
        self.assertIn('sea_lantern',s.blocks[(4,5,13)])
    def test_flower_support_and_persistent_leaves(self):
        s=build(next(c for c in CONFIGS if c['id']=='planter'))
        for (x,y,z),state in s.blocks.items():
            if family(state)=='flower':self.assertIn('grass_block',s.blocks.get((x,y-1,z),''))
            if family(state)=='leaves':self.assertIn('persistent=true',state)
    def test_bay_parameter_changes_width_without_duplicating_ids(self):
        c=json.loads(json.dumps(CONFIGS[0]));a=build(c);c['parameters']['bays']=3;b=build(c)
        self.assertEqual(a.size[0]-b.size[0],6);self.assertFalse(any('.bay3.' in owner for owner in b.owners.values()))
    def test_source_integrity(self):
        data=json.loads((ROOT/'evidence/original_integrity.json').read_text())
        # External original files are available only in the authoring workspace.
        entries=data if isinstance(data,list) else data.get('files',[])
        found=0
        for entry in entries:
            p=Path(entry.get('source',entry.get('path','')))
            if p.is_file():self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),entry['sha256']);found+=1
        if not found:self.skipTest('Original external assets not present; see hash inventory')
    def test_preview_ceiling_does_not_leak_directly_upward(self):
        from detail_lab.mesh import write_mesh
        import numpy as np
        s=Scene((5,5,5));s.fill((0,0,0),(5,5,5),make('white_concrete'),'enclosure')
        s.fill((1,1,1),(4,4,4),'minecraft:air','space')
        s.fill((1,2,1),(4,3,4),make('quartz_slab'),'ceiling')
        s.set((2,1,2),make('sea_lantern'),'lamp')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.nbt';export_structure(s,p);write_mesh(load_build(p),p,Path(tmp)/'mesh')
            light=np.fromfile(Path(tmp)/'mesh/blocklight.bin',dtype=np.uint8).reshape(5,5,5)
            self.assertEqual(int(light[2,1,2]),15);self.assertEqual(int(light[2,3,2]),0)
if __name__=='__main__':unittest.main()
