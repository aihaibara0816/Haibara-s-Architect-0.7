import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(os.environ.get("HAF_ENGINE_ROOT", ROOT)).resolve()
sys.path.insert(0, str(ENGINE))
import hafusion
hafusion.__path__.insert(0, str(ROOT / "hafusion"))
from hafusion.variation06 import VariationError, compile_variation
from hafusion.workflow06 import WorkflowError, case_command, digest, dispatch_call, import_proposal, load_json, validate_request, verify_run, write_run


class Workflow06Tests(unittest.TestCase):
    def setUp(self):
        self.request = load_json(ROOT / "examples/workflow06/library-request.json")
        self.temp = tempfile.TemporaryDirectory()
        self.runs = Path(self.temp.name) / "runs"
        self.addCleanup(self.temp.cleanup)

    def proposal(self, request=None):
        request = request or self.request
        return {"schema_version": "0.6-model-proposal", "source_request_sha256": digest(request),
                "proposed_modules": copy.deepcopy(request["handoff"]["proposed_modules"])}

    def rewrite_artifact_and_manifest(self, run_id, name, value, update_request_hash=False):
        """Simulate a caller editing both data and unsigned hash metadata."""
        folder = self.runs / run_id
        data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        (folder / name).write_bytes(data)
        manifest = load_json(folder / "manifest.json")
        for entry in manifest["artifacts"]:
            if entry["path"] == name:
                entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if update_request_hash:
            manifest["request_sha256"] = digest(value)
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_real_handoff_consumer_and_honest_state(self):
        result = validate_request(self.request)
        self.assertEqual(result["handoff_plan"]["consumer"], "hafusion.design_handoff.compile_handoff")
        self.assertFalse(result["handoff_plan"]["generated_geometry"])
        self.assertFalse(result["variation_plan"]["generated_geometry"])
        self.assertEqual(result["game_status"], "pending")
        self.assertEqual(result["handoff_plan"]["ceiling_plans"][0]["preferred_separator_layers"], 2)

    def test_variation_order_invariance(self):
        first = compile_variation(self.request["variation"])
        other = copy.deepcopy(self.request["variation"])
        other["targets"].reverse()
        other["channels"].reverse()
        for channel in other["channels"]:
            channel["choices"].reverse()
        for target in other["targets"]:
            target["channels"].reverse()
        self.assertEqual(first, compile_variation(other))

    def test_inserting_target_does_not_reshuffle_existing(self):
        spec = self.request["variation"]
        before = compile_variation(spec)["entries"]
        spec["targets"].append({"component_id": "facade.north.new", "bounds_xyz": [2, 3, 0, 7, 8, 1], "channels": ["material", "weathering"]})
        after = compile_variation(spec)["entries"]
        self.assertEqual(before, [e for e in after if e["component_id"] != "facade.north.new"])

    def test_independent_channel_seed(self):
        spec = self.request["variation"]
        before = compile_variation(spec)["entries"]
        next(c for c in spec["channels"] if c["id"] == "weathering")["seed"] += 1
        after = compile_variation(spec)["entries"]
        self.assertEqual([e for e in before if e["channel"] == "material"], [e for e in after if e["channel"] == "material"])
        self.assertNotEqual([e["address_sha256"] for e in before if e["channel"] == "weathering"],
                            [e["address_sha256"] for e in after if e["channel"] == "weathering"])

    def test_frozen_component_preserves_existing_choices(self):
        spec = self.request["variation"]
        first = [e for e in compile_variation(spec)["entries"] if e["component_id"].startswith("facade.windows")]
        spec["seed"] += 100
        self.assertEqual(first, [e for e in compile_variation(spec)["entries"] if e["component_id"].startswith("facade.windows")])
        self.assertTrue(all(e["status"] == "frozen_existing" for e in first))

    def test_frozen_missing_value_is_an_error(self):
        spec = self.request["variation"]
        next(t for t in spec["targets"] if "existing_choices" in t)["existing_choices"] = {}
        with self.assertRaisesRegex(VariationError, "existing choice"):
            compile_variation(spec)

    def test_bounds_keepout_and_duplicate_ids(self):
        for bounds in [[11, 3, 4, 13, 6, 6], [-1, 3, 4, 1, 8, 10]]:
            spec = copy.deepcopy(self.request["variation"])
            spec["targets"][0]["bounds_xyz"] = bounds
            with self.assertRaises(VariationError):
                compile_variation(spec)
        spec = copy.deepcopy(self.request["variation"])
        spec["targets"].append(copy.deepcopy(spec["targets"][0]))
        with self.assertRaisesRegex(VariationError, "duplicate"):
            compile_variation(spec)

    def test_variation_cannot_weaken_handoff_authority(self):
        for field, value in [("editable_regions", [[-100, 0, -100, 100, 100, 100]]), ("keepouts", []), ("locked_component_ids", [])]:
            request = copy.deepcopy(self.request)
            request["variation"][field] = value
            with self.subTest(field=field), self.assertRaises(WorkflowError):
                validate_request(request)

    def test_write_verify_and_immutable_run(self):
        manifest = write_run(self.request, self.runs, "r001")
        before = (self.runs / "r001/manifest.json").read_bytes()
        self.assertEqual(manifest["state"], "planned")
        self.assertEqual(verify_run(self.runs, "r001")["status"], "pass")
        with self.assertRaisesRegex(WorkflowError, "immutable"):
            write_run(self.request, self.runs, "r001")
        self.assertEqual(before, (self.runs / "r001/manifest.json").read_bytes())

    def test_invalid_plan_leaves_no_run(self):
        self.request["handoff"]["proposed_modules"][0]["bounds_xyz"] = [11, 3, 4, 13, 6, 6]
        with self.assertRaises(ValueError):
            write_run(self.request, self.runs, "invalid")
        self.assertFalse((self.runs / "invalid").exists())

    def test_hash_integrity_failure(self):
        write_run(self.request, self.runs, "r001")
        with (self.runs / "r001/handoff_plan.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(WorkflowError, "integrity"):
            verify_run(self.runs, "r001")

    def test_manifest_cannot_point_outside_run(self):
        write_run(self.request, self.runs, "r001")
        path = self.runs / "r001/manifest.json"
        manifest = load_json(path)
        manifest["artifacts"][0]["path"] = "../outside.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "artifact path"):
            verify_run(self.runs, "r001")

    def test_portable_run_names_and_traversal(self):
        for run_id in ["../escape", "a/b", "a\\b", "C:drive", ".", "..", "CON", "LPT1.txt", "r.", "r "]:
            with self.subTest(run_id=run_id), self.assertRaises(WorkflowError):
                write_run(self.request, self.runs, run_id)

    def test_model_revision_creates_new_run_preserves_parent(self):
        write_run(self.request, self.runs, "r001")
        parent_before = (self.runs / "r001/request.json").read_bytes()
        proposal = self.proposal()
        proposal["proposed_modules"][1]["bounds_xyz"] = [18, 3, 16, 22, 5, 20]
        manifest = import_proposal(self.runs, "r001", "r002", proposal)
        self.assertEqual(manifest["parent"]["run_id"], "r001")
        self.assertEqual(verify_run(self.runs, "r002")["status"], "pass")
        self.assertEqual(parent_before, (self.runs / "r001/request.json").read_bytes())

    def test_stale_or_executable_proposal_rejected(self):
        write_run(self.request, self.runs, "r001")
        for field, value in [("source_request_sha256", "wrong"), ("command", "echo not-executed")]:
            proposal = self.proposal()
            proposal[field] = value
            with self.subTest(field=field), self.assertRaises(WorkflowError):
                import_proposal(self.runs, "r001", "r002", proposal)
        self.assertFalse((self.runs / "r002").exists())

    def test_model_cannot_remove_or_change_frozen_module(self):
        write_run(self.request, self.runs, "r001")
        proposal = self.proposal()
        proposal["proposed_modules"] = proposal["proposed_modules"][1:]
        with self.assertRaisesRegex(WorkflowError, "frozen module"):
            import_proposal(self.runs, "r001", "r002", proposal)

    def test_model_module_in_corridor_rejected(self):
        write_run(self.request, self.runs, "r001")
        proposal = self.proposal()
        proposal["proposed_modules"][1]["bounds_xyz"] = [11, 3, 4, 13, 6, 6]
        with self.assertRaisesRegex(ValueError, "keepout"):
            import_proposal(self.runs, "r001", "r002", proposal)

    def test_json_duplicate_and_nonfinite_rejected(self):
        path = Path(self.temp.name) / "bad.json"
        for data in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}', '{"x":-1e999}']:
            path.write_text(data, encoding="utf-8")
            with self.subTest(data=data), self.assertRaises(WorkflowError):
                load_json(path)

    def test_seed_weight_and_bounds_types(self):
        for value in [True, False, 1.0, "12", None, float("nan"), float("inf")]:
            for location in ["global", "channel"]:
                spec = copy.deepcopy(self.request["variation"])
                if location == "global":
                    spec["seed"] = value
                else:
                    spec["channels"][0]["seed"] = value
                with self.subTest(value=value, location=location), self.assertRaisesRegex(VariationError, "seed must be an integer"):
                    compile_variation(spec)
        for value in [True, 0, -1, 1000001, 1.0, float("nan")]:
            spec = copy.deepcopy(self.request["variation"])
            spec["channels"][0]["choices"][0]["weight"] = value
            with self.subTest(weight=value), self.assertRaisesRegex(VariationError, "weight must be an integer"):
                compile_variation(spec)
        spec = copy.deepcopy(self.request["variation"])
        spec["targets"][0]["bounds_xyz"][0] = True
        with self.assertRaisesRegex(VariationError, "six integers"):
            compile_variation(spec)

    def test_python_request_rejects_nonfinite_metadata(self):
        for value in [float("nan"), float("inf"), -float("inf")]:
            request = copy.deepcopy(self.request)
            request["handoff"]["unconsumed_metadata"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                write_run(request, self.runs, "invalid")
            self.assertFalse((self.runs / "invalid").exists())

    def test_stable_id_duplicates_and_invalid_spacing(self):
        for location in ["channel", "choice", "locked", "target_channel"]:
            spec = copy.deepcopy(self.request["variation"])
            if location == "channel":
                spec["channels"].append(copy.deepcopy(spec["channels"][0]))
            elif location == "choice":
                spec["channels"][0]["choices"].append(copy.deepcopy(spec["channels"][0]["choices"][0]))
            elif location == "locked":
                spec["locked_component_ids"].append(spec["locked_component_ids"][0])
            else:
                spec["targets"][0]["channels"].append(spec["targets"][0]["channels"][0])
            with self.subTest(location=location), self.assertRaisesRegex(VariationError, "duplicate"):
                compile_variation(spec)
        for value in ["", " ", " leading", "trailing ", "bad\nidentifier"]:
            spec = copy.deepcopy(self.request["variation"])
            spec["targets"][0]["component_id"] = value
            with self.subTest(value=value), self.assertRaisesRegex(VariationError, "stable ID"):
                compile_variation(spec)

    def test_duplicate_model_module_rejected(self):
        write_run(self.request, self.runs, "r001")
        proposal = self.proposal()
        proposal["proposed_modules"].append(copy.deepcopy(proposal["proposed_modules"][0]))
        with self.assertRaisesRegex(WorkflowError, "duplicate proposal"):
            import_proposal(self.runs, "r001", "r002", proposal)

    def test_proposal_cannot_replace_protected_fields(self):
        write_run(self.request, self.runs, "r001")
        for key, value in [("handoff", {}), ("variation", {}), ("authorized_scope", {}), ("frozen_module_ids", [])]:
            proposal = self.proposal()
            proposal[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(WorkflowError, "exactly"):
                import_proposal(self.runs, "r001", "r002", proposal)
        proposal = self.proposal()
        proposal["proposed_modules"][0]["bounds_xyz"][3] += 1
        with self.assertRaisesRegex(WorkflowError, "frozen module"):
            import_proposal(self.runs, "r001", "r002", proposal)

    def test_verify_rejects_unlisted_files_and_directories(self):
        write_run(self.request, self.runs, "r001")
        extra = self.runs / "r001/unlisted.json"
        extra.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "unlisted"):
            verify_run(self.runs, "r001")
        extra.unlink()
        extra.mkdir()
        with self.assertRaisesRegex(WorkflowError, "unlisted"):
            verify_run(self.runs, "r001")

    def test_verify_replays_constraints_even_if_unsigned_hashes_are_rewritten(self):
        write_run(self.request, self.runs, "r001")
        altered = copy.deepcopy(self.request)
        altered["handoff"]["proposed_modules"][1]["bounds_xyz"] = [11, 3, 4, 13, 6, 6]
        self.rewrite_artifact_and_manifest("r001", "request.json", altered, update_request_hash=True)
        with self.assertRaisesRegex(ValueError, "keepout"):
            verify_run(self.runs, "r001")

    def test_verify_replays_plan_even_if_artifact_hash_is_rewritten(self):
        write_run(self.request, self.runs, "r001")
        plan = load_json(self.runs / "r001/variation_plan.json")
        plan["entries"][0]["choice_id"] = "forged_choice"
        self.rewrite_artifact_and_manifest("r001", "variation_plan.json", plan)
        with self.assertRaisesRegex(WorkflowError, "stored variation"):
            verify_run(self.runs, "r001")

    def test_verify_revision_compares_parent_protected_fields(self):
        write_run(self.request, self.runs, "r001")
        import_proposal(self.runs, "r001", "r002", self.proposal())
        altered = copy.deepcopy(self.request)
        altered["handoff"]["style"] = "medieval"
        plan = validate_request(altered)
        self.rewrite_artifact_and_manifest("r002", "request.json", altered, update_request_hash=True)
        self.rewrite_artifact_and_manifest("r002", "handoff_plan.json", plan["handoff_plan"])
        with self.assertRaisesRegex(WorkflowError, "protected parent fields"):
            verify_run(self.runs, "r002")

    def test_verify_revision_requires_parent_files(self):
        write_run(self.request, self.runs, "r001")
        import_proposal(self.runs, "r001", "r002", self.proposal())
        (self.runs / "r001/manifest.json").unlink()
        with self.assertRaisesRegex(WorkflowError, "regular file"):
            verify_run(self.runs, "r002")

    def test_verify_rejects_parent_cycle(self):
        for run_id in ["r001", "r002"]:
            write_run(self.request, self.runs, run_id)
        for run_id, parent_id in [("r001", "r002"), ("r002", "r001")]:
            folder = self.runs / run_id
            data = json.dumps(self.proposal()).encode("utf-8")
            (folder / "model_proposal.json").write_bytes(data)
            manifest = load_json(folder / "manifest.json")
            manifest["parent"] = {"run_id": parent_id, "request_sha256": digest(self.request)}
            manifest["artifacts"].append({"path": "model_proposal.json", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "cyclic"):
            verify_run(self.runs, "r001")

    def test_unsigned_hashes_do_not_authenticate_fully_rewritten_valid_root(self):
        write_run(self.request, self.runs, "r001")
        altered = copy.deepcopy(self.request)
        altered["handoff"]["style"] = "medieval"
        plans = validate_request(altered)
        self.rewrite_artifact_and_manifest("r001", "request.json", altered, update_request_hash=True)
        self.rewrite_artifact_and_manifest("r001", "handoff_plan.json", plans["handoff_plan"])
        # A new, internally consistent root is indistinguishable without an
        # externally trusted digest/signature. verify must not claim provenance.
        result = verify_run(self.runs, "r001")
        self.assertEqual(result["status"], "pass")
        self.assertNotEqual(result["request_sha256"], digest(self.request))
        self.assertNotIn("trusted", result)
        self.assertEqual(result["source_authenticity"], "not_verified")

    def test_registered_legacy_bridge_is_explicit(self):
        command = case_command(ENGINE, "guangzhou_south", "workflow06-test-new")
        self.assertEqual(command[-4:], ["--case", "guangzhou_south", "--run", "workflow06-test-new"])
        with self.assertRaisesRegex(WorkflowError, "unknown case"):
            case_command(ENGINE, "unregistered_model_name", "r001")

    def test_model_dispatch_binds_parent_and_rejects_commands_paths(self):
        write_run(self.request, self.runs, "r001")
        for call in [{"name": "shell", "arguments": {"command": "anything"}},
                     {"name": "haf_verify_parent", "arguments": {"runs_root": "C:/elsewhere"}},
                     {"name": "haf_import_proposal", "arguments": {"run_id": "r002", "parent": "other", "proposal": self.proposal()}}]:
            with self.subTest(call=call), self.assertRaises(WorkflowError):
                dispatch_call(call, self.runs, "r001")
        result = dispatch_call({"name": "haf_validate_proposal", "arguments": {"proposal": self.proposal()}}, self.runs, "r001")
        self.assertEqual(result["contract_status"], "pass")
        self.assertFalse((self.runs / "r002").exists())
        result = dispatch_call({"name": "haf_import_proposal", "arguments": {"run_id": "r002", "proposal": self.proposal()}}, self.runs, "r001")
        self.assertEqual(result["parent"]["run_id"], "r001")

    def test_invalid_manifest_entry_rejected(self):
        write_run(self.request, self.runs, "r001")
        path = self.runs / "r001/manifest.json"
        manifest = load_json(path)
        manifest["artifacts"] = ["not an artifact entry"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "entry must be an object"):
            verify_run(self.runs, "r001")

    def test_manifest_cannot_claim_unperformed_game_verification(self):
        write_run(self.request, self.runs, "r001")
        path = self.runs / "r001/manifest.json"
        manifest = load_json(path)
        manifest["validation"]["game"] = "pass"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "cannot claim"):
            verify_run(self.runs, "r001")

    def test_cli_demo_verify_and_no_overwrite(self):
        command = [sys.executable, str(ROOT / "tools/haf.py")]
        env = {**os.environ, "HAF_ENGINE_ROOT": str(ENGINE), "PYTHONIOENCODING": "utf-8"}
        demo = subprocess.run(command + ["demo", "--runs-root", str(self.runs), "--run", "cli-demo"], capture_output=True, env=env)
        self.assertEqual(demo.returncode, 0, demo.stderr.decode("utf-8", errors="replace"))
        checked = subprocess.run(command + ["verify", "--runs-root", str(self.runs), "--run", "cli-demo"], capture_output=True, env=env)
        self.assertEqual(checked.returncode, 0, checked.stderr.decode("utf-8", errors="replace"))
        repeated = subprocess.run(command + ["demo", "--runs-root", str(self.runs), "--run", "cli-demo"], capture_output=True, env=env)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertFalse(list(self.runs.rglob("*.nbt")))


if __name__ == "__main__":
    unittest.main()
