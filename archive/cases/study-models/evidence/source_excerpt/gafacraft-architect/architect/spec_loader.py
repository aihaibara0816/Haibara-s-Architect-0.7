"""JSON Schema plus geometry, provenance and environmental invariants."""
import json, math
from pathlib import Path
from jsonschema import Draft202012Validator
from .legacy import ROOT
from .palette import check_materials
from .voxelizer import q, q3, quantized_box

class SpecError(ValueError):
    pass

def read_json(path):
    def unique_pairs(items):
        result={}
        for k,v in items:
            if k in result: raise SpecError(f"Duplicate JSON key: {k}")
            result[k]=v
        return result
    def reject_constant(value): raise SpecError(f"Invalid JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"),object_pairs_hook=unique_pairs,parse_constant=reject_constant)

def _finite(data):
    if isinstance(data,float) and not math.isfinite(data): raise SpecError("Non-finite number")
    if isinstance(data,dict):
        for value in data.values(): _finite(value)
    if isinstance(data,list):
        for value in data: _finite(value)

def _polygon_ok(vertices):
    if len({tuple(v) for v in vertices}) != len(vertices): return False
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(vertices,vertices[1:]+vertices[:1]))
    if abs(area)<1e-9:return False
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on(a,b,c):return min(a[0],b[0])<=c[0]<=max(a[0],b[0]) and min(a[1],b[1])<=c[1]<=max(a[1],b[1])
    edges=list(zip(vertices,vertices[1:]+vertices[:1]))
    for i,(a,b) in enumerate(edges):
        for j,(c,d) in enumerate(edges):
            if j<=i or j==i+1 or (i==0 and j==len(edges)-1):continue
            o1,o2,o3,o4=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
            if o1*o2<0 and o3*o4<0:return False
            if any(abs(o)<1e-9 and on(u,v,w) for o,u,v,w in [(o1,a,b,c),(o2,a,b,d),(o3,c,d,a),(o4,c,d,b)]):return False
    return True

def validate_spec(spec):
    _finite(spec)
    if spec.get("schema_version")=="0.2":
        from .research_contract import legacy_projection,validate_research
        schema=read_json(ROOT/"schema/building_spec_v0.2.schema.json")
        errors=list(Draft202012Validator(schema).iter_errors(spec))
        if errors:raise SpecError("v0.2 schema: "+str(errors[0].message))
        base=validate_spec(legacy_projection(spec))
        base["research"]=validate_research(spec)
        return base
    schema=read_json(ROOT/"schema/building_spec.schema.json")
    Draft202012Validator.check_schema(schema)
    errors=sorted(Draft202012Validator(schema).iter_errors(spec),key=lambda e:str(list(e.path)))
    if errors:
        raise SpecError("; ".join(f"{'/'.join(map(str,e.path)) or 'root'}: {e.message}" for e in errors[:8]))
    s=spec["coordinates"]["blocks_per_metre"]
    size=spec["coordinates"]["size_blocks"]
    extent=spec["coordinates"]["extent_m"]
    if tuple(size)!=q3(extent,s):raise SpecError("Conflicting scale / extent_m / size_blocks")
    if math.prod(size)>spec["environment"]["budgets"]["max_cells"]:raise SpecError("Bounding-box cell budget exceeded")
    if spec["study_parameters"] is not None and spec["study_parameters"]["extent_m"]!=extent:raise SpecError("Study extent conflicts with coordinates")
    if spec["mode"]=="study" and spec["study_parameters"] is None:raise SpecError("Study mode requires explicit study_parameters")
    world=spec["environment"]["world"]
    bounds_known=all(world[k] is not None for k in ("min_y","max_y_exclusive","origin_xyz"))
    if world["confirmed"] and not bounds_known:raise SpecError("Confirmed world needs actual origin and bounds")
    if bounds_known:
        if world["min_y"]>=world["max_y_exclusive"]:raise SpecError("Invalid world bounds")
        if world["origin_xyz"][1]<world["min_y"] or world["origin_xyz"][1]+size[1]>world["max_y_exclusive"]:
            raise SpecError("World height exceeded; no implicit rescaling")
    maps={}
    for group,key in [("sources","source_id"),("facts","fact_id"),("images","image_id")]:
        items=spec["evidence"][group]
        if any(not isinstance(x.get(key),str) or not x[key] for x in items):raise SpecError(f"Missing {key}")
        maps[group]={x[key]:x for x in items}
        if len(maps[group])!=len(items):raise SpecError(f"Duplicate evidence IDs in {group}")
    for fact in maps["facts"].values():
        for field,group in [("source_ids","sources"),("image_ids","images"),("derived_from_fact_ids","facts")]:
            if not isinstance(fact.get(field,[]),list) or any(v not in maps[group] for v in fact.get(field,[])):
                raise SpecError("Dangling fact evidence reference")
        if fact.get("status")=="verified":
            sources=[maps["sources"][v] for v in fact.get("source_ids",[])]
            photos=[maps["images"][v] for v in fact.get("image_ids",[])]
            documented=any(str(v.get("url","")).startswith(("https://","http://")) and v.get("accessed_at") for v in sources)
            if not documented and not any(v.get("verification_state")=="full_image_viewed" for v in photos):
                raise SpecError("Verified fact requires a documented source or viewed image")
    for im in maps["images"].values():
        if any(v not in maps["sources"] for v in im.get("source_ids",[])):raise SpecError("Dangling image source")
    for image_id in spec["evidence"]["selected_image_ids"]:
        im=maps["images"].get(image_id,{})
        if im.get("verification_state")!="full_image_viewed" or im.get("quality",{}).get("eligible") is not True:
            raise SpecError("Selected image lacks upstream visual eligibility")
    def evidence_refs(provenance):
        for field,group in [("source_ids","sources"),("fact_ids","facts"),("image_ids","images")]:
            for ident in provenance[field]:
                if ident not in maps[group]:raise SpecError(f"Dangling {field}: {ident}")
        if provenance["status"] in ("unknown","conflicted"):raise SpecError("Unresolved component cannot be executed")
        if provenance["status"]=="confirmed":
            if not provenance["fact_ids"] or any(maps["facts"][f].get("status")!="verified" for f in provenance["fact_ids"]):raise SpecError("Confirmed geometry needs verified facts")
    fields={"width":("width","building_dimensions.width"),"depth":("length","building_dimensions.length"),"height":("overall_height","building_dimensions.overall_height")}
    for dim,m in spec["real_dimensions"].items():
        if m["value_m"] is not None and m["range_m"] is not None:raise SpecError("Cannot combine exact and ranged dimensions")
        if m["status"]=="unknown" and (m["value_m"] is not None or m["range_m"] is not None):raise SpecError("Unknown real dimension must remain null")
        if m["range_m"] is not None and m["range_m"][0]>m["range_m"][1]:raise SpecError("Reversed measurement range")
        for field,group in [("fact_ids","facts"),("source_ids","sources")]:
            if any(v not in maps[group] for v in m[field]):raise SpecError("Dangling measurement evidence")
        if m["status"]=="confirmed":
            matches=[maps["facts"][f] for f in m["fact_ids"]]
            if m["value_m"] is None or not any(f.get("status")=="verified" and f.get("kind")=="fact" and f.get("source_ids") and f.get("unit")=="m" and f.get("field") in fields[dim] and f.get("value")==m["value_m"] for f in matches):
                raise SpecError("Confirmed measurement lacks matching verified field/value")
    check_materials(spec["materials"])
    seen=set()
    for c in spec["components"]:
        cid=c["component_id"];p=c["parameters"]
        if cid in seen:raise SpecError(f"Duplicate component ID {cid}")
        if not set(c["after"]).issubset(seen):raise SpecError("Dependencies must refer to previous components")
        if c["operation"]=="subtract":
            if c["kind"]!="box" or not c["targets"] or not set(c["targets"]).issubset(seen) or c["material"] is not None:
                raise SpecError("Subtraction requires a box, previous targets and null material")
        elif c["material"] not in spec["materials"] or c["targets"]:raise SpecError("Add requires a known material and no targets")
        evidence_refs(c["provenance"])
        if c["kind"]=="box":
            lo,hi=quantized_box(p["min_m"],p["max_m"],s)
        elif c["kind"]=="polygon_prism":
            vertices=p["vertices_xz_m"]
            if not _polygon_ok(vertices):raise SpecError("Polygon must be simple and nondegenerate")
            quantized=[[q(x,s),q(z,s)] for x,z in vertices]
            if not _polygon_ok(quantized):raise SpecError("Polygon becomes invalid on block grid")
            lo=(min(v[0] for v in vertices),p["y_min_m"],min(v[1] for v in vertices))
            hi=(max(v[0] for v in vertices),p["y_max_m"],max(v[1] for v in vertices))
            lo,hi=quantized_box(lo,hi,s)
        else:
            sec=p["sections"]
            if any(a["y_m"]>=b["y_m"] for a,b in zip(sec,sec[1:])):raise SpecError("Section heights must strictly increase")
            if len({q(v["y_m"],s) for v in sec})!=len(sec):raise SpecError("Section anchors collapse on voxel grid")
            if q(p["wall_thickness_m"],s)<1 or q(p["floor_thickness_m"],s)<1:raise SpecError("Wall/floor thickness collapsed")
            if p["floor_material"] not in spec["materials"] or p["mullion_material"] not in spec["materials"]:raise SpecError("Unknown profile material")
            if p["mullion_pitch_m"]>0 and q(p["mullion_pitch_m"],s)<1:raise SpecError("Mullion pitch collapsed")
            if any(y<sec[0]["y_m"] or y+p["floor_thickness_m"]>sec[-1]["y_m"] for y in p["floor_levels_m"]):raise SpecError("Floor outside profile")
            floor_starts=sorted(q(y,s) for y in p["floor_levels_m"])
            if any(b-a<q(p["floor_thickness_m"],s) for a,b in zip(floor_starts,floor_starts[1:])):raise SpecError("Floors overlap on voxel grid")
            lo=q3([min(v["cx_m"]-v["width_m"]/2 for v in sec),sec[0]["y_m"],min(v["cz_m"]-v["depth_m"]/2 for v in sec)],s)
            hi=q3([max(v["cx_m"]+v["width_m"]/2 for v in sec),sec[-1]["y_m"],max(v["cz_m"]+v["depth_m"]/2 for v in sec)],s)
        if any(lo[i]<0 or hi[i]>size[i] for i in range(3)):raise SpecError(f"{cid}: geometry outside declared size")
        seen.add(cid)
    if not set(spec["lighting"]["component_ids"]).issubset(seen):raise SpecError("Dangling lighting components")
    for l in spec["levels"]:
        evidence_refs(l["provenance"])
        if l["floor_top_m"]<0 or l["ceiling_bottom_m"]>extent[1]:raise SpecError("Declared level outside model")
        if l["ceiling_bottom_m"]-l["floor_top_m"]<spec["acceptance"]["minimum_level_clearance_m"]:raise SpecError("Insufficient declared floor clearance")
    for item in spec["acceptance"]["clear_air_boxes"]:
        lo,hi=quantized_box(item["min_m"],item["max_m"],s)
        if any(lo[i]<0 or hi[i]>size[i] for i in range(3)):raise SpecError("Air check outside model")
    for path in spec["acceptance"]["walk_paths"]:
        headroom=q(path["headroom_m"],s)
        if headroom<1:raise SpecError("Walk headroom collapsed")
        points=[q3(path[key],s) for key in ("start_xyz_m","end_xyz_m")]
        if points[0][1]!=points[1][1]:raise SpecError("Walk checks support flat paths only")
        if any(any(p[i]<0 or p[i]>=size[i] for i in range(3)) or p[1]<1 or p[1]+headroom>size[1] for p in points):raise SpecError("Walk check outside model")
    for check in spec["acceptance"]["profile_relationships"]:
        if check["component_id"] not in seen:raise SpecError("Unknown profile check component")
    if spec["mode"]=="strict_reconstruction":
        if spec["building"]["identity_status"]!="confirmed":raise SpecError("Strict reconstruction requires confirmed identity")
        if spec["study_parameters"] is not None or any(m["status"]!="confirmed" for m in spec["real_dimensions"].values()):raise SpecError("Strict reconstruction requires confirmed real dimensions, no study overrides")
        if any(c["provenance"]["status"]!="confirmed" for c in spec["components"]):raise SpecError("Strict reconstruction requires approved confirmed components")
        if not spec["review"]["approved_for_strict_reconstruction"] or not world["confirmed"] or spec["environment"]["configuration_status"]!="verified_test_environment":raise SpecError("Strict reconstruction requires reviewed geometry and verified test environment")
    return {"schema":"pass","semantic":"pass","world_placement":"checked" if world["confirmed"] else "pending_actual_configuration","mode":spec["mode"]}

def load_spec(path):
    data=read_json(path)
    validate_spec(data)
    return data
