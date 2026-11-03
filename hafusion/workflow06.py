"""Immutable model-neutral planning runs over the existing HAF handoff consumer."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import stat
import sys

from .design_handoff import compile_handoff
from .variation06 import canonical, compile_variation

VERSION = "0.6.0"
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
REQUEST_KEYS = {"schema_version", "handoff", "variation", "frozen_module_ids"}
PROPOSAL_KEYS = {"schema_version", "source_request_sha256", "proposed_modules"}
MAX_JSON_BYTES = 8 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MANIFEST_KEYS = {"schema_version", "workflow_version", "run_id", "created_utc", "state", "request_sha256", "parent", "validation", "generated_geometry", "artifacts"}


class WorkflowError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise WorkflowError(message)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path):
    path = Path(path)
    require(path.is_file(), "JSON input must be a regular file")
    require(path.stat().st_size <= MAX_JSON_BYTES, "JSON input exceeds 8 MiB")
    def duplicate_check(pairs):
        value = {}
        for key, child in pairs:
            require(key not in value, "duplicate JSON key: " + key)
            value[key] = child
        return value
    def reject_constant(value):
        raise WorkflowError("non-finite JSON value: " + value)
    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), "non-finite JSON number: " + value)
        return number
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=duplicate_check,
                      parse_constant=reject_constant, parse_float=finite_float)


def validate_request(request):
    require(isinstance(request, dict) and set(request) <= REQUEST_KEYS, "request has unknown fields")
    require(request.get("schema_version") == "0.6", "request schema_version must be 0.6")
    # Python callers must obey JSON's finite-number rule too, before consumers run.
    request_hash = digest(request)
    handoff = request.get("handoff")
    require(isinstance(handoff, dict), "handoff object required")
    # Preserve the real 0.4 contract. Do not relabel it 0.6 without a migration.
    plan = compile_handoff(handoff)
    frozen = request.get("frozen_module_ids", [])
    require(isinstance(frozen, list) and all(isinstance(x, str) and x for x in frozen)
            and len(frozen) == len(set(frozen)), "frozen_module_ids must contain unique IDs")
    modules = {m["component_id"]: m for m in handoff.get("proposed_modules", [])}
    require(set(frozen) <= set(modules), "frozen module missing from handoff")
    variation = None
    if "variation" in request:
        spec = request["variation"]
        require(isinstance(spec, dict), "variation must be an object")
        # Variation cannot weaken spatial authority inherited from the handoff.
        require(spec.get("editable_regions") == handoff["authorized_scope"]["editable_regions"],
                "variation editable_regions must match handoff authority")
        require(spec.get("keepouts", []) == handoff.get("circulation_keepouts", []),
                "variation keepouts must match handoff circulation")
        variation = compile_variation(spec)
        require(set(spec.get("locked_component_ids", [])) >= set(handoff["authorized_scope"].get("locked_component_ids", [])),
                "variation cannot remove handoff component locks")
    return {"handoff_plan": plan, "variation_plan": variation,
            "request_sha256": request_hash, "contract_status": "pass",
            "geometry_status": "pending_adapter", "visual_status": "pending", "game_status": "pending"}


def validate_run_id(run_id):
    require(isinstance(run_id, str) and RUN_ID.fullmatch(run_id) is not None
            and run_id not in (".", "..") and not run_id.endswith((".", " ")),
            "run ID must be one portable filename component, 1..80 ASCII characters")
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM" + str(n) for n in range(1, 10)), *("LPT" + str(n) for n in range(1, 10))}
    require(run_id.split(".")[0].upper() not in reserved, "reserved device filename is not a run ID")
    return run_id


def reject_links(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        # lstat reparse attributes also cover Windows junctions on Python 3.10/3.11,
        # where pathlib.Path.is_junction is not yet available.
        try:
            attributes = getattr(part.lstat(), "st_file_attributes", 0)
        except FileNotFoundError:
            attributes = 0
        reparse = attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        require(not part.is_symlink() and not reparse,
                "symlink/junction paths are not accepted for workflow runs")


def run_path(runs_root, run_id):
    validate_run_id(run_id)
    root = Path(runs_root).absolute()
    reject_links(root)
    path = root / run_id
    reject_links(path)
    return path


def write_run(request, runs_root, run_id, parent=None, proposal=None):
    validated = validate_request(request)
    require((parent is None) == (proposal is None), "revision requires both parent and proposal")
    if parent is not None:
        require(isinstance(parent, dict) and set(parent) == {"run_id", "request_sha256"}, "invalid parent reference")
        proposed_request, verified_parent = prepare_proposal(runs_root, parent["run_id"], proposal)
        require(parent["request_sha256"] == verified_parent["request_sha256"] and canonical(proposed_request) == canonical(request),
                "revision request must be the authorized parent plus proposed modules")
    destination = run_path(runs_root, run_id)
    require(not destination.exists(), "existing run is immutable; choose a new run ID")
    artifacts = {"request.json": request, "handoff_plan.json": validated["handoff_plan"]}
    if validated["variation_plan"] is not None:
        artifacts["variation_plan.json"] = validated["variation_plan"]
    if proposal is not None:
        artifacts["model_proposal.json"] = proposal
    encoded = {name: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
               for name, value in artifacts.items()}
    require(all(len(data) <= MAX_JSON_BYTES for data in encoded.values()), "generated planning artifact exceeds 8 MiB")
    manifest = {"schema_version": "0.6", "workflow_version": VERSION, "run_id": run_id,
                "created_utc": datetime.now(timezone.utc).isoformat(), "state": "planned",
                "request_sha256": validated["request_sha256"], "parent": parent,
                "validation": {"contract": "pass", "geometry": "pending_adapter", "visual": "pending", "game": "pending"},
                "generated_geometry": False,
                "artifacts": [{"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                              for name, data in sorted(encoded.items())]}
    # mkdir and exclusive files prevent replacing an existing run. Manifest is last:
    # an interrupted write is incomplete and verify_run rejects it, not a valid run.
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    for name, data in encoded.items():
        with (destination / name).open("xb") as stream:
            stream.write(data)
    with (destination / "manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    return manifest


def verify_run(runs_root, run_id):
    """Replay content and lineage; hashes provide consistency, not authenticity."""
    return _verify_run(runs_root, run_id, ())


def _verify_run(runs_root, run_id, ancestors):
    require(run_id not in ancestors, "cyclic parent lineage")
    require(len(ancestors) < 64, "parent lineage exceeds 64 runs")
    path = run_path(runs_root, run_id)
    reject_links(path / "manifest.json")
    manifest = load_json(path / "manifest.json")
    require(isinstance(manifest, dict) and set(manifest) == MANIFEST_KEYS, "manifest must contain only the required fields")
    require(manifest.get("schema_version") == "0.6" and manifest.get("run_id") == run_id, "invalid run manifest identity")
    require(manifest.get("workflow_version") == VERSION, "unsupported workflow manifest version")
    require(manifest.get("state") == "planned" and manifest.get("generated_geometry") is False,
            "workflow06 verifies planning runs only")
    require(manifest.get("validation") == {"contract": "pass", "geometry": "pending_adapter", "visual": "pending", "game": "pending"},
            "manifest cannot claim geometry, visual or game verification")
    require(isinstance(manifest.get("request_sha256"), str) and SHA256.fullmatch(manifest["request_sha256"]) is not None, "invalid request digest")
    entries = manifest.get("artifacts")
    require(isinstance(entries, list), "manifest artifacts missing")
    seen = set()
    allowed = {"request.json", "handoff_plan.json", "variation_plan.json", "model_proposal.json"}
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"}, "artifact entry must be an object with path, bytes and sha256")
        name = entry.get("path")
        require(isinstance(name, str) and name in allowed and name not in seen, "invalid or duplicate artifact path")
        require(isinstance(entry["bytes"], int) and not isinstance(entry["bytes"], bool) and 0 <= entry["bytes"] <= MAX_JSON_BYTES,
                "artifact bytes must be an integer in 0..8 MiB")
        require(isinstance(entry["sha256"], str) and SHA256.fullmatch(entry["sha256"]) is not None, "invalid artifact digest")
        seen.add(name)
        artifact = path / name
        reject_links(artifact)
        require(artifact.is_file(), "missing artifact: " + name)
        require(artifact.stat().st_size <= MAX_JSON_BYTES, "artifact exceeds 8 MiB")
        raw = artifact.read_bytes()
        require(len(raw) == entry.get("bytes") and hashlib.sha256(raw).hexdigest() == entry.get("sha256"),
                "artifact integrity mismatch: " + name)
    require({"request.json", "handoff_plan.json"} <= seen, "required artifacts missing")
    require({p.name for p in path.iterdir()} == seen | {"manifest.json"}, "run contains unlisted files or directories")
    request = load_json(path / "request.json")
    validated = validate_request(request)
    require(validated["request_sha256"] == manifest.get("request_sha256"), "request identity mismatch")
    require(digest(load_json(path / "handoff_plan.json")) == digest(validated["handoff_plan"]), "stored handoff does not match its request")
    if validated["variation_plan"] is not None:
        require("variation_plan.json" in seen, "variation artifact missing")
        require(digest(load_json(path / "variation_plan.json")) == digest(validated["variation_plan"]), "stored variation does not match its request")
    else:
        require("variation_plan.json" not in seen, "unexpected variation artifact")
    parent = manifest.get("parent")
    if parent is not None:
        require(isinstance(parent, dict) and set(parent) == {"run_id", "request_sha256"}, "invalid parent reference")
        validate_run_id(parent["run_id"])
        require(parent["run_id"] != run_id and "model_proposal.json" in seen, "revision requires a distinct parent and model proposal")
        verified_parent = _verify_run(runs_root, parent["run_id"], ancestors + (run_id,))
        require(parent["request_sha256"] == verified_parent["request_sha256"], "parent request identity mismatch")
        proposal = load_json(path / "model_proposal.json")
        require(isinstance(proposal, dict) and set(proposal) == PROPOSAL_KEYS, "invalid stored proposal")
        require(proposal["schema_version"] == "0.6-model-proposal" and proposal["source_request_sha256"] == parent["request_sha256"], "proposal parent identity mismatch")
        require(canonical(proposal["proposed_modules"]) == canonical(request["handoff"]["proposed_modules"]), "proposal does not match revision modules")
        source = load_json(run_path(runs_root, parent["run_id"]) / "request.json")
        expected = apply_proposal(source, proposal, verified_parent["request_sha256"])
        require(canonical(expected) == canonical(request), "revision changes protected parent fields")
    else:
        require("model_proposal.json" not in seen, "proposal artifact requires a parent reference")
    return {"status": "pass", "run_id": run_id, "artifacts_verified": len(seen),
            "request_sha256": validated["request_sha256"], "generated_geometry": False,
            "verification_scope": "content_rules_and_parent_lineage", "source_authenticity": "not_verified",
            "geometry_status": "pending_adapter", "visual_status": "pending", "game_status": "pending"}


def apply_proposal(source, proposal, expected_hash):
    require(isinstance(proposal, dict) and set(proposal) == PROPOSAL_KEYS, "proposal must contain exactly schema_version, source_request_sha256, proposed_modules")
    require(proposal["schema_version"] == "0.6-model-proposal", "unknown model proposal contract")
    require(proposal["source_request_sha256"] == expected_hash, "proposal is stale or refers to another request")
    require(isinstance(proposal["proposed_modules"], list), "proposed_modules must be a list")
    previous = {m["component_id"]: m for m in source["handoff"].get("proposed_modules", [])}
    updated = {}
    for module in proposal["proposed_modules"]:
        require(isinstance(module, dict) and isinstance(module.get("component_id"), str), "proposal module requires component_id")
        require(module["component_id"] not in updated, "duplicate proposal component_id")
        updated[module["component_id"]] = module
    for frozen in source.get("frozen_module_ids", []):
        require(frozen in updated and canonical(updated[frozen]) == canonical(previous[frozen]), "proposal changes/removes frozen module: " + frozen)
    request = copy.deepcopy(source)
    request["handoff"]["proposed_modules"] = proposal["proposed_modules"]
    return request


def prepare_proposal(runs_root, parent_id, proposal):
    verified = verify_run(runs_root, parent_id)
    source = load_json(run_path(runs_root, parent_id) / "request.json")
    request = apply_proposal(source, proposal, verified["request_sha256"])
    return request, verified


def import_proposal(runs_root, parent_id, run_id, proposal):
    request, verified = prepare_proposal(runs_root, parent_id, proposal)
    return write_run(request, runs_root, run_id,
                     parent={"run_id": parent_id, "request_sha256": verified["request_sha256"]}, proposal=proposal)


def dispatch_call(call, runs_root, parent_id):
    """Model-host boundary: host binds paths and parent; model supplies data only."""
    require(isinstance(call, dict) and set(call) == {"name", "arguments"}, "tool call requires exactly name and arguments")
    args = call["arguments"]
    require(isinstance(args, dict), "tool arguments must be an object")
    if call["name"] == "haf_verify_parent":
        require(not args, "verify_parent takes no model arguments")
        return verify_run(runs_root, parent_id)
    if call["name"] == "haf_validate_proposal":
        require(set(args) == {"proposal"}, "validate_proposal takes only proposal")
        request, _ = prepare_proposal(runs_root, parent_id, args["proposal"])
        return validate_request(request)
    if call["name"] == "haf_import_proposal":
        require(set(args) == {"run_id", "proposal"}, "import_proposal takes only run_id and proposal")
        return import_proposal(runs_root, parent_id, args["run_id"], args["proposal"])
    raise WorkflowError("unknown model tool; shell and case builds are not exposed")


def case_command(engine_root, case_id, run_id):
    """Prepare a registered legacy adapter call; never infer it from model text."""
    validate_run_id(run_id)
    validate_run_id(case_id)
    root = Path(engine_root).resolve()
    config = load_json(root / "agent_config.json")
    require(case_id in config.get("cases", {}), "unknown case adapter; no generic generator is registered")
    script = (root / config["cases"][case_id]).resolve()
    require(script.is_relative_to(root) and script.is_file() and script.suffix == ".py", "adapter script must be a Python file inside the engine")
    case_destination = root / "cases" / case_id / "runs" / run_id
    reject_links(case_destination)
    require(not case_destination.exists(), "legacy case run already exists")
    entry = root / "tools" / "agent.py"
    require(entry.is_file(), "legacy agent entry missing")
    return [sys.executable, str(entry), "--case", case_id, "--run", run_id]
