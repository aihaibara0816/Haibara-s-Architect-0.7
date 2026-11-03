"""Maintain the published JSON Schema in a compact, reviewable form."""
import json
from pathlib import Path

def obj(properties, required=None):
    return {"type":"object","properties":properties,"required":list(properties) if required is None else required,"additionalProperties":False}
def arr(items, **kw): return {"type":"array","items":items,**kw}
def ref(name): return {"$ref":"#/$defs/"+name}
def enum(*values): return {"enum":list(values)}
text={"type":"string","minLength":1}
num={"type":"number","minimum":0}
pos={"type":"number","exclusiveMinimum":0}
nullable_num={"type":["number","null"],"minimum":0}
string_or_null={"type":["string","null"]}
vec=arr(num,minItems=3,maxItems=3)
ints=arr({"type":"integer","minimum":1},minItems=3,maxItems=3)
id_type={"type":"string","pattern":"^[A-Za-z][A-Za-z0-9_.-]*$","maxLength":100}
ids=arr(id_type,uniqueItems=True)
evidence=obj({"status":enum("confirmed","observed","estimated","design_choice","unknown","conflicted"),"basis":text,"fact_ids":ids,"source_ids":ids,"image_ids":ids})
measurement=obj({"value_m":nullable_num,"range_m":{"oneOf":[{"type":"null"},arr(num,minItems=2,maxItems=2)]},"status":enum("confirmed","observed","estimated","unknown","conflicted"),"basis":string_or_null,"fact_ids":ids,"source_ids":ids})
box=obj({"min_m":vec,"max_m":vec})
polygon=obj({"vertices_xz_m":arr(arr(num,minItems=2,maxItems=2),minItems=3,maxItems=64),"y_min_m":num,"y_max_m":pos})
section=obj({"y_m":num,"cx_m":num,"cz_m":num,"width_m":pos,"depth_m":pos})
profile=obj({"sections":arr(section,minItems=2,maxItems=64),"section_shape":enum("rectangle","ellipse"),"interpolation":enum("linear","step"),"wall_thickness_m":pos,"floor_levels_m":arr(num,uniqueItems=True),"floor_thickness_m":pos,"floor_material":id_type,"mullion_pitch_m":num,"mullion_material":id_type,"cap_top":{"type":"boolean"}})
common={"component_id":id_type,"name":text,"kind":enum("box","polygon_prism","profile_shell"),"operation":enum("add","subtract"),"material":{"oneOf":[id_type,{"type":"null"}]},"targets":ids,"after":ids,"provenance":ref("provenance"),"parameters":{}}
variants=[]
for kind,params in [("box",box),("polygon_prism",polygon),("profile_shell",profile)]:
    props=dict(common);props["kind"]={"const":kind};props["parameters"]=params
    variants.append(obj(props))
schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:gafacraft:architect:building-spec:0.1","title":"GAFAcraft Architect BuildingSpec v0.1","$defs":{"provenance":evidence,"measurement":measurement,"component":{"oneOf":variants}}}
schema.update(obj({
    "schema_version":{"const":"0.1"},"spec_id":id_type,"revision":{"type":"integer","minimum":1},"mode":enum("study","strict_reconstruction"),
    "building":obj({"name":text,"identity_status":enum("design_study","provisional","confirmed"),"real_world_reference":string_or_null,"scope":text}),
    "coordinates":obj({"units":{"const":"m"},"axis_convention":{"const":"X_right_Y_up_Z_back"},"front":{"const":"-Z"},"north":string_or_null,"blocks_per_metre":pos,"size_blocks":ints,"extent_m":vec,"rounding":{"const":"half_up"}}),
    "environment":obj({"minecraft_version":text,"data_version":{"type":"integer","minimum":1},"neoforge_version":string_or_null,"create_version":string_or_null,"configuration_status":enum("historical_target_unverified","verified_test_environment"),
       "world":obj({"min_y":{"type":["integer","null"]},"max_y_exclusive":{"type":["integer","null"]},"origin_xyz":{"oneOf":[{"type":"null"},arr({"type":"integer"},minItems=3,maxItems=3)]},"confirmed":{"type":"boolean"},"basis":text}),
       "budgets":obj({"max_cells":{"type":"integer","minimum":1,"maximum":1000000},"max_non_air_blocks":{"type":"integer","minimum":1,"maximum":1000000},"max_cell_visits":{"type":"integer","minimum":1,"maximum":20000000}})}),
    "real_dimensions":obj({"width":ref("measurement"),"depth":ref("measurement"),"height":ref("measurement")}),
    "study_parameters":{"oneOf":[{"type":"null"},obj({"extent_m":vec,"basis":text})]},
    "evidence":obj({"packet_id":string_or_null,"packet_schema_version":string_or_null,"packet_sha256":{"type":["string","null"],"pattern":"^[a-f0-9]{64}$"},"sources":arr({"type":"object"}),"facts":arr({"type":"object"}),"images":arr({"type":"object"}),"selected_image_ids":ids,"upstream_component_ids":ids,"notes":arr(text)}),
    "materials":{"type":"object","minProperties":1,"propertyNames":id_type,"additionalProperties":obj({"block_state":text,"preview_color":{"type":"string","pattern":"^#[0-9A-Fa-f]{6}$"},"role":text})},
    "components":arr(ref("component"),minItems=1,maxItems=500),
    "levels":arr(obj({"level_id":id_type,"floor_top_m":num,"ceiling_bottom_m":pos,"use":text,"provenance":ref("provenance")})),
    "lighting":obj({"component_ids":ids,"simulation_status":{"const":"blocks_only_no_game_light_simulation"}}),
    "acceptance":obj({"clear_air_boxes":arr(obj({"check_id":id_type,"min_m":vec,"max_m":vec})),"walk_paths":arr(obj({"check_id":id_type,"start_xyz_m":vec,"end_xyz_m":vec,"headroom_m":pos})),"minimum_level_clearance_m":num,"profile_relationships":arr(obj({"component_id":id_type,"lower_y_m":num,"middle_y_m":num,"upper_y_m":num,"expectation":enum("middle_wider_than_ends")}))}),
    "unresolved":arr(text),"deviations":arr(obj({"component_id":{"oneOf":[id_type,{"type":"null"}]},"description":text,"authorization":text})),
    "review":obj({"approved_for_strict_reconstruction":{"type":"boolean"},"basis":text}),
    "output":obj({"format":{"const":"java_structure_nbt"},"include_air":{"type":"boolean"},"views":{"const":["front","back","left","right","iso45"]}})
}))
if __name__=="__main__":
    path=Path(__file__).resolve().parents[1]/"schema/building_spec.schema.json"
    path.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(path)
