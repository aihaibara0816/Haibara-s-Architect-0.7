"""Contract, construction, readback, locality and acceptance regression tests."""
import copy,hashlib,json,math,tempfile,unittest
from pathlib import Path
from PIL import Image
from architect.legacy import ROOT,core,inspector
from architect.spec_loader import load_spec,validate_spec,read_json
from architect.voxelizer import q,scene_from_readback
from architect.geometry import generate,profile_at
from architect.export_nbt import export_and_readback
from architect.validation import check_geometry
from architect.packet_adapter import adapt
from architect.pipeline import build,canonical_hash
from architect.render_views import VIEWS,render_view

def sample(name="retail_store"):
    return load_spec(ROOT/"examples"/name/"building_spec.json")

class ContractTests(unittest.TestCase):
    def setUp(self):self.s=sample()
    def reject(self):
        with self.assertRaises(ValueError):validate_spec(self.s)
    def test_both_samples_valid(self):
        for name in ("retail_store","tower_segment"):self.assertEqual(validate_spec(sample(name))["schema"],"pass")
    def test_missing_required_field(self):del self.s["coordinates"];self.reject()
    def test_unknown_real_dimensions_valid_in_study(self):
        self.assertTrue(all(m["value_m"] is None and m["status"]=="unknown" for m in self.s["real_dimensions"].values()))
        validate_spec(self.s)
    def test_cannot_promote_study_to_strict(self):self.s["mode"]="strict_reconstruction";self.reject()
    def test_unknown_dimension_cannot_contain_number(self):self.s["real_dimensions"]["height"]["value_m"]=12;self.reject()
    def test_confirmed_dimension_needs_matching_evidence(self):
        self.s["real_dimensions"]["height"].update(status="confirmed",value_m=12);self.reject()
    def test_conflicting_scale(self):self.s["coordinates"]["blocks_per_metre"]=2;self.reject()
    def test_world_height_overflow(self):
        self.s["environment"]["world"].update(min_y=-64,max_y_exclusive=320,origin_xyz=[0,315,0],confirmed=True);self.reject()
    def test_world_exact_boundary_allowed(self):
        self.s["environment"]["world"].update(min_y=-64,max_y_exclusive=320,origin_xyz=[0,308,0],confirmed=True)
        self.assertEqual(validate_spec(self.s)["world_placement"],"checked")
    def test_confirmed_world_needs_origin(self):self.s["environment"]["world"]["confirmed"]=True;self.reject()
    def test_model_cell_budget(self):self.s["environment"]["budgets"]["max_cells"]=10;self.reject()
    def test_unsupported_block_state(self):self.s["materials"]["white"]["block_state"]="minecraft:oak_stairs[facing=north]";self.reject()
    def test_duplicate_component_ids(self):self.s["components"][1]["component_id"]=self.s["components"][0]["component_id"];self.reject()
    def test_forward_dependency_rejected(self):self.s["components"][0]["after"]=["canopy"];self.reject()
    def test_dangling_evidence(self):self.s["components"][0]["provenance"]["fact_ids"]=["fact-missing"];self.reject()
    def test_verified_fact_cannot_be_sourceless(self):self.s["evidence"]["facts"][0]["status"]="verified";self.reject()
    def test_confirmed_geometry_cannot_use_suggestion(self):self.s["components"][0]["provenance"]["status"]="confirmed";self.reject()
    def test_self_intersecting_polygon(self):
        p=next(c for c in self.s["components"] if c["kind"]=="polygon_prism")
        p["parameters"]["vertices_xz_m"]=[[2,2],[5,5],[2,5],[5,2]];self.reject()
    def test_quantization_collapse(self):
        self.s["components"][0]["parameters"]["max_m"][1]=.1;self.reject()
    def test_out_of_bounds_geometry(self):self.s["components"][0]["parameters"]["max_m"][0]=99;self.reject()
    def test_subtraction_requires_explicit_target(self):
        c=next(c for c in self.s["components"] if c["operation"]=="subtract");c["targets"]=[];self.reject()
    def test_profile_anchor_order(self):
        self.s=sample("tower_segment");p=self.s["components"][-1]["parameters"];p["sections"][1]["y_m"]=1;self.reject()
    def test_profile_duplicate_floor(self):
        self.s=sample("tower_segment");self.s["components"][-1]["parameters"]["floor_levels_m"].append(2.1);self.reject()
    def test_path_with_zero_voxel_headroom(self):self.s["acceptance"]["walk_paths"][0]["headroom_m"]=.1;self.reject()
    def test_nonfinite_number_rejected(self):self.s["coordinates"]["blocks_per_metre"]=math.inf;self.reject()
    def test_duplicate_json_key_and_nan(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"
            for value in ['{"a":1,"a":2}','{"a":NaN}']:
                p.write_text(value)
                with self.assertRaises(ValueError):read_json(p)
    def test_half_up_and_cumulative_endpoints(self):
        self.assertEqual(q(2.5,1),3);self.assertEqual(q(5,.5),3)
        self.assertEqual([q(v,.5) for v in [0,3,6,9]],[0,2,3,5])

class AdapterTests(unittest.TestCase):
    def test_adapter_preserves_source_ids_and_unknowns(self):
        folder=ROOT/"examples/retail_store";packet=read_json(folder/"packet.json")
        s=adapt(folder/"packet.json",folder/"construction_overlay.json")
        self.assertEqual(s,sample());self.assertEqual(s["evidence"]["facts"],packet["facts"])
        self.assertEqual(s["evidence"]["packet_sha256"],hashlib.sha256((folder/"packet.json").read_bytes()).hexdigest())
    def test_no_overlay_does_not_invent_geometry(self):
        c=adapt(ROOT/"examples/retail_store/packet.json")
        self.assertNotIn("components",c);self.assertNotIn("size_blocks",c)
    def test_overlay_cannot_overwrite_evidence_or_scale(self):
        base=read_json(ROOT/"examples/retail_store/construction_overlay.json")
        with tempfile.TemporaryDirectory() as d:
            for mode in ("evidence","scale"):
                data=copy.deepcopy(base)
                if mode=="evidence":data["evidence"]={}
                else:data["coordinates"]["blocks_per_metre"]=2
                p=Path(d)/"overlay.json";p.write_text(json.dumps(data))
                with self.assertRaises(ValueError):adapt(ROOT/"examples/retail_store/packet.json",p)
    def test_actual_legacy_photo_context(self):
        c=adapt(ROOT/"examples/legacy_gafa_research/packet.json")
        self.assertEqual(c["evidence"]["images"][0]["image_id"],"img-R002")
        self.assertEqual(len(c["evidence"]["facts"]),4)
        self.assertTrue(all(m["value_m"] is None for m in c["real_dimensions"].values()))
        self.assertEqual(c["upstream_validation"]["status"],"partial_local_evidence_intake")
        self.assertEqual(c["upstream_validation"]["upstream"]["status"],"FAIL")
    def test_legacy_photo_and_old_parameters_generate_new_spec(self):
        folder=ROOT/"examples/legacy_gafa_research"
        spec=adapt(folder/"packet.json",folder/"construction_overlay.json")
        scene,generated=generate(spec)
        self.assertEqual(scene.size,(22,20,34))
        self.assertEqual(check_geometry(scene,spec,generated)["status"],"pass")
        self.assertTrue(all(c["provenance"]["status"]=="design_choice" for c in spec["components"]))
    def test_local_evidence_hash_mismatch_rejected(self):
        folder=ROOT/"examples/legacy_gafa_research"
        p=read_json(folder/"packet.json");p["images"][0]["local_sha256"]="0"*64
        from architect.packet_adapter import validate_packet
        with self.assertRaisesRegex(ValueError,"hash mismatch"):validate_packet(p,folder)
    def test_local_image_cannot_enter_final_four(self):
        folder=ROOT/"examples/legacy_gafa_research";p=read_json(folder/"packet.json")
        p["selection"]["slots"][0].update(image_id="img-R002",purpose="front",rationale="test")
        from architect.packet_adapter import validate_packet
        with self.assertRaises(ValueError):validate_packet(p,folder)

class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=sample();cls.scene,cls.report=generate(cls.spec)
    def test_retail_air_and_walk_acceptance(self):self.assertEqual(check_geometry(self.scene,self.spec,self.report)["status"],"pass")
    def test_blocked_entry_fails_acceptance(self):
        scene=copy.deepcopy(self.scene)
        for x in range(15,19):
            for y in range(2,6):scene.set((x,y,7),"minecraft:white_concrete","test.blocker")
        checks=check_geometry(scene,self.spec,self.report)["checks"]
        self.assertFalse(next(c for c in checks if c["check_id"]=="entry.clear")["passed"])
    def test_missing_support_fails_walk(self):
        scene=copy.deepcopy(self.scene);scene.set((17,1,2),core.AIR,"test")
        checks=check_geometry(scene,self.spec,self.report)["checks"]
        self.assertFalse(next(c for c in checks if c["check_id"]=="public_access")["passed"])
    def test_tower_actual_profile_and_floor_clearance(self):
        s=sample("tower_segment");scene,report=generate(s)
        qa=check_geometry(scene,s,report);self.assertEqual(qa["status"],"pass")
        self.assertEqual(qa["checks"][-1]["widths_lower_middle_upper"],[14,22,10])
        for y in s["components"][-1]["parameters"]["floor_levels_m"][:-1]:
            self.assertIn((16,y,15),scene.blocks)
            self.assertTrue(all((16,h,15) not in scene.blocks for h in range(y+1,y+6)))
    def test_step_and_linear_profiles_differ(self):
        s=sample("tower_segment");p=s["components"][-1]["parameters"]
        self.assertEqual(profile_at(p,26)["width_m"],17)
        p["interpolation"]="step";self.assertEqual(profile_at(p,26)["width_m"],12)
        p["section_shape"]="rectangle";validate_spec(s);scene,rep=generate(s)
        self.assertGreater(len(scene.blocks),0);self.assertEqual(rep["profiles"]["tower.shell"][24]["width_blocks"],12)
    def test_targeted_carve_leaves_other_owner_intact(self):
        s=copy.deepcopy(self.spec);first=copy.deepcopy(s["components"][0]);first.update(component_id="wall",after=[])
        first["parameters"]={"min_m":[1,1,1],"max_m":[4,4,4]}
        other=copy.deepcopy(first);other.update(component_id="protected",after=["wall"],material="wood");other["parameters"]={"min_m":[2,1,1],"max_m":[3,4,4]}
        cut=copy.deepcopy(first);cut.update(component_id="opening",after=["protected"],operation="subtract",material=None,targets=["wall"])
        s["components"]=[first,other,cut];s["levels"]=[];s["lighting"]["component_ids"]=[];s["acceptance"].update(clear_air_boxes=[],walk_paths=[])
        validate_spec(s);scene,_=generate(s)
        self.assertEqual(len(scene.blocks),9);self.assertEqual(set(scene.owners.values()),{"protected"})
    def test_cell_operation_budget_stops_generation(self):
        s=copy.deepcopy(self.spec);s["environment"]["budgets"]["max_cell_visits"]=10
        with self.assertRaisesRegex(ValueError,"budget"):generate(s)
    def test_non_air_budget(self):
        s=copy.deepcopy(self.spec);s["environment"]["budgets"]["max_non_air_blocks"]=10
        with self.assertRaisesRegex(ValueError,"budget"):generate(s)
    def test_nbt_roundtrip_and_deterministic_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            files=[Path(d)/f"{i}.nbt" for i in (1,2)]
            for p in files:
                _,r,_=export_and_readback(self.scene,self.spec,p)
                self.assertEqual(scene_from_readback(r).blocks,self.scene.blocks)
                self.assertEqual(r.info["data_version"],3955)
            self.assertEqual(files[0].read_bytes(),files[1].read_bytes())
    def test_air_omission_roundtrip(self):
        s=copy.deepcopy(self.spec);s["output"]["include_air"]=False
        with tempfile.TemporaryDirectory() as d:
            _,r,_=export_and_readback(self.scene,s,Path(d)/"sparse.nbt")
            self.assertEqual(len(r.blocks),len(self.scene.blocks))
    def test_canopy_revision_changes_only_requested_region(self):
        s=copy.deepcopy(self.spec);next(c for c in s["components"] if c["component_id"]=="canopy")["parameters"]["min_m"][2]=2
        new,_=generate(s);diff={p for p in set(new.blocks)|set(self.scene.blocks) if new.blocks.get(p)!=self.scene.blocks.get(p)}
        self.assertEqual(diff,{(x,6,2) for x in range(14,20)})
    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"marker").write_text("keep")
            with self.assertRaisesRegex(ValueError,"no overwrite"):build(ROOT/"examples/retail_store/building_spec.json",p)
            self.assertEqual((p/"marker").read_text(),"keep")

class PreviewTests(unittest.TestCase):
    def test_cameras_are_orthonormal_and_iso_elevation_45(self):
        for axes in VIEWS.values():
            for a in axes:self.assertAlmostEqual(sum(x*x for x in a),1)
            for a,b in [(axes[0],axes[1]),(axes[1],axes[2]),(axes[0],axes[2])]:self.assertAlmostEqual(sum(x*y for x,y in zip(a,b)),0)
        self.assertAlmostEqual(math.degrees(math.asin(VIEWS["iso45"][2][1])),45)
    def test_delivered_previews_and_nbt_share_hash_and_build_id(self):
        for case in ("retail_store","tower_segment","legacy_gafa_colonnade","retail_store_revision"):
            out=ROOT/"output"/case;report=read_json(out/"build_report.json")
            nbt=inspector.load_build(out/"building.nbt");actual=scene_from_readback(nbt).fingerprint()
            spec=load_spec(out/"building_spec.json");regenerated,_=generate(spec)
            self.assertEqual(regenerated.fingerprint(),actual)
            self.assertEqual(canonical_hash(spec),report["spec_sha256"])
            self.assertEqual(report["geometry_sha256"],actual)
            self.assertEqual(report["nbt"]["sha256"],hashlib.sha256((out/"building.nbt").read_bytes()).hexdigest())
            self.assertEqual(len(report["views"]),5)
            for view in report["views"]:
                path=out/view["file"]
                with Image.open(path) as im:
                    self.assertEqual(im.size,(1280,1000));self.assertEqual(im.info["geometry_sha256"],actual)
                    self.assertEqual(im.info["build_id"],report["build_id"]);self.assertEqual(im.info["source"],"NBT_readback")
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),view["sha256"])
                self.assertGreater(view["non_background_pixels"],1000)
    def test_render_repeats_from_exported_nbt(self):
        out=ROOT/"output/retail_store";report=read_json(out/"build_report.json");nbt=inspector.load_build(out/"building.nbt")
        with tempfile.TemporaryDirectory() as d:
            hashes=[]
            for name in ("front1.png","front2.png"):
                result=render_view(nbt,sample(),"front",Path(d)/name,report["build_id"],report["geometry_sha256"])
                hashes.append(result["sha256"])
            # Repeatability on this runtime; fonts may change PNG bytes across OSes.
            self.assertEqual(hashes[0],hashes[1])

if __name__=="__main__":unittest.main()
