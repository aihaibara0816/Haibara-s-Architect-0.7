"""Read packet v1.0/v1.1; add an explicit reviewed construction overlay.

No free-text parsing, image inference, or fabricated geometry lives here.
"""
import copy,hashlib,importlib.util,sys
from pathlib import Path
from .legacy import ROOT
from .spec_loader import read_json,validate_spec,SpecError

def validate_packet(packet,base_dir=None):
    scripts=ROOT/"vendor/building_reference/scripts"
    # Upstream script has an absolute import of its sibling 'scale'.
    old_path=list(sys.path)
    try:
        sys.path.insert(0,str(scripts))
        spec=importlib.util.spec_from_file_location("architect_upstream_packet",scripts/"validate_packet.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.Validator(packet,"template",base_dir).run()
    finally:
        sys.path[:]=old_path
    if result["status"]=="FAIL":
        # packet v1.0 assumes original HTTP pages for viewed images. A legacy
        # local attachment has no such page. Keep the original FAIL report;
        # allow only this explicitly documented, hash-checked intake extension.
        allowed=[]
        if base_dir is not None:
            root=Path(base_dir).resolve()
            selected=set(module.reference_set.selected_ids(packet))
            for im in packet["images"]:
                rel=im.get("local_file");sha=im.get("local_sha256")
                if not rel or not sha or im["image_id"] in selected or im.get("quality",{}).get("eligible") is not False:continue
                local=(root/rel).resolve()
                if not local.is_relative_to(root) or not local.is_file():continue
                if hashlib.sha256(local.read_bytes()).hexdigest()!=sha:raise SpecError("Local evidence hash mismatch")
                allowed.append(im["image_id"]+": viewed images require original-page source_ids")
        if not result["errors"] or any(e not in allowed for e in result["errors"]):
            raise SpecError("Invalid upstream packet: "+"; ".join(result["errors"]))
        return {"status":"partial_local_evidence_intake","upstream":result,"extension":"Hash-checked local attachments may support observations only. No public-page or final-four-image eligibility is granted."}
    return result

def research_context(packet,raw_bytes,base_dir=None):
    report=validate_packet(packet,base_dir)
    mapped={}
    for dest,source in [("width","width"),("depth","length"),("height","overall_height")]:
        m=packet["scale"]["building_dimensions"][source]
        facts={f["fact_id"]:f for f in packet["facts"]}
        fact=facts.get(m["fact_id"],{})
        status="unknown"
        if m["value_m"] is not None:status="confirmed" # Upstream validates exact field/value, verified status and source.
        elif m["range_m"] is not None:status="estimated"
        mapped[dest]={"value_m":m["value_m"],"range_m":copy.deepcopy(m["range_m"]),"status":status,
                      "basis":m["basis"],"fact_ids":[m["fact_id"]] if m["fact_id"] else [],"source_ids":copy.deepcopy(fact.get("source_ids",[]))}
    return {"building_name":packet["subject"]["name"],"real_dimensions":mapped,"selected_s":packet["scale"]["selected_s"],
            "evidence":{"packet_id":packet["packet_id"],"packet_schema_version":packet["schema_version"],"packet_sha256":hashlib.sha256(raw_bytes).hexdigest(),
                        "sources":copy.deepcopy(packet["sources"]),"facts":copy.deepcopy(packet["facts"]),"images":copy.deepcopy(packet["images"]),
                        "selected_image_ids":([x["image_id"] for x in packet["selection"]["slots"] if x["image_id"]] if packet["schema_version"]=="1.0" else list(dict.fromkeys([x["image_id"] for x in packet["selection"]["core"]]+[i for g in packet["selection"]["detail_groups"] for i in g["image_ids"]]))),
                        "upstream_component_ids":[c["component_id"] for c in packet["components"]],
                        "notes":["Original packet source/fact/image IDs and epistemic states are retained. Geometry requires a separately reviewed construction overlay."]},
            "upstream_validation":report,"unresolved":copy.deepcopy(packet.get("gaps",[])),
            "mapping":[{"from":f"scale.building_dimensions.{a}","to":f"real_dimensions.{b}"} for a,b in [("width","width"),("length","depth"),("overall_height","height")]]}

def adapt(packet_path,overlay_path=None):
    p=Path(packet_path);packet=read_json(p)
    context=research_context(packet,p.read_bytes(),p.parent)
    if overlay_path is None:return context
    spec=read_json(overlay_path)
    if "evidence" in spec or "real_dimensions" in spec:raise SpecError("Construction overlay must not override packet evidence or real measurements")
    if spec["building"]["name"]!=context["building_name"]:raise SpecError("Packet/overlay building identity mismatch")
    if context["selected_s"] is not None and context["selected_s"]!=spec["coordinates"]["blocks_per_metre"]:raise SpecError("Packet selected_s conflicts with construction scale")
    spec["evidence"]=context["evidence"]
    spec["real_dimensions"]=context["real_dimensions"]
    spec["unresolved"]=list(dict.fromkeys(spec["unresolved"]+context["unresolved"]))
    if spec.get("schema_version")=="0.2":
        spec["research"]["reference_set"]=copy.deepcopy(packet["selection"]) if packet["schema_version"]=="1.1" else None
    validate_spec(spec)
    return spec

