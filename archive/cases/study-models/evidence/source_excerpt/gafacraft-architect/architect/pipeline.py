import json,hashlib,shutil,tempfile
from pathlib import Path
from . import __version__
from .legacy import inspector
from .spec_loader import load_spec,validate_spec
from .geometry import generate
from .export_nbt import export_and_readback
from .voxelizer import scene_from_readback
from .validation import check_geometry
from .render_views import render_views

def dump(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def canonical_hash(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def build(spec_path,out):
    spec=load_spec(spec_path)
    out=Path(out)
    if out.exists():raise ValueError("Output exists: select a new version directory; no overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix=".architect-build-",dir=out.parent))
    try:
        scene,generated=generate(spec)
        spec_hash=canonical_hash(spec)
        build_id=f'{spec["spec_id"]}-r{spec["revision"]}-{spec_hash[:10]}'
        meta,nbt,inspection=export_and_readback(scene,spec,work/"building.nbt")
        # The read-back data, not the generator's buffer, drives checks and images.
        reread=scene_from_readback(nbt)
        reread.owners=dict(scene.owners)
        qa=check_geometry(reread,spec,generated)
        if qa["status"]!="pass":raise ValueError("Geometry acceptance failed: "+json.dumps(qa["checks"]))
        geometry_sha=reread.fingerprint()
        previews=render_views(nbt,spec,work,build_id,geometry_sha)
        owners={}
        for p,c in scene.owners.items():owners.setdefault(c,[]).append(p)
        components={c:{"remaining_blocks":len(pts),"bbox_inclusive":inspector.bbox(pts)} for c,pts in sorted(owners.items())}
        report={"engine_version":__version__,"build_id":build_id,"spec_sha256":spec_hash,"geometry_sha256":geometry_sha,
                "nbt":meta,"size_xyz":list(scene.size),"non_air_blocks":len(scene.blocks),"materials":qa["material_counts"],
                "validation":{"spec":validate_spec(spec),"nbt_readback_exact_match":True,"geometry":qa,"registry":"pending_actual_configuration","game":"pending_game_test","create_import":"pending_game_test"},
                "views":previews,"provenance":{"packet_id":spec["evidence"]["packet_id"],"packet_sha256":spec["evidence"]["packet_sha256"]},
                "limitations":["Study geometry; not surveyed reconstruction.","Full-cube renderer; glass uses opaque schematic color; no Minecraft textures or lighting.","No model inference, credential, network, world edit or website deployment in the engine.","All stages rebuilt; stable component IDs and external diffs do not imply internal incremental generation."]}
        dump(work/"building_spec.json",spec)
        dump(work/"build_report.json",report)
        dump(work/"inspection.json",inspection)
        dump(work/"render_report.json",{"build_id":build_id,"geometry_sha256":geometry_sha,"source_nbt_sha256":meta["sha256"],"views":previews})
        dump(work/"geometry_report.json",generated)
        dump(work/"components.json",components)
        dump(work/"blocks.json",{"size_xyz":list(scene.size),"geometry_sha256":geometry_sha,"blocks":[[*p,state,scene.owners[p]] for p,state in sorted(scene.blocks.items())]})
        dump(work/"placement_manifest.json",{"build_id":build_id,"files":[meta],"origin_world_xyz":spec["environment"]["world"]["origin_xyz"],"front":"-Z","includes_air":spec["output"]["include_air"],"target_environment":spec["environment"],"placement_status":"pending_game_test","notes":"Explicit air replaces cells in the full structure bounding box. Use an empty test world area; never auto-place in production."})
        work.rename(out)
        return report
    except Exception:
        shutil.rmtree(work,ignore_errors=True)
        raise

