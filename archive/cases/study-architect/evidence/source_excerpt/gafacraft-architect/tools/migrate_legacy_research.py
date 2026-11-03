"""Preserve a real historical photo/evidence set as a partial packet v1.0.

This is a documented migration, not a new research or image-inference service.
"""
from pathlib import Path
import json,sys,hashlib,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.packet_adapter import adapt
from architect.pipeline import dump
from architect.legacy import ROOT

def main():
    out=ROOT/"examples/legacy_gafa_research"
    old=ROOT/"vendor/buildkit_v03/projects/gafa_admin"
    original=json.loads((old/"evidence.json").read_text())
    packet=json.loads((ROOT/"vendor/building_reference/references/packet-template.json").read_text())
    packet.update(packet_id="packet-legacy-gafa-colonnade",collected_at="2026-10-20")
    packet["subject"].update(name="广美行政楼廊柱局部历史资料",kind="single",identity_status="provisional",version="用户历史照片，拍摄日期未知",boundary="照片可见廊柱、红墙、浅坡屋顶和外部台阶；不包含整楼或未知背立面。")
    packet["provenance"].update(user_input="接续历史广美廊柱照片与试建资料；保留来源和未知尺寸。",research_status="incomplete")
    image={"image_id":"img-R002","legacy_reference_id":"R002","source_ids":[],"page_url":None,"direct_image_url":None,"creator":None,
           "media_type":"photo","built_state":"constructed","version":"历史用户照片，拍摄日期未知","view":"廊柱局部斜视",
           "orientation":"从台阶一侧朝廊柱内部观察；地理北向未知","covers":["两排深色圆柱","红墙","白色浅坡网格屋顶","外部台阶及平台"],
           "component_ids":[],"verification_state":"full_image_viewed","checked_at":"2026-10-20","building_match_confirmed":None,
           "actual_pixels":[1279,1706],"quality":{"eligible":False,"assessment":"已查看原始照片；可作局部外观观察，身份和公开原页未独立核实，不能进最终四图。","limitations":["透视较强且背立面不可见","无可靠绝对尺度","原始公开页面未知"]},
           "license_status":"unknown","license_url":None,"training_authorized":False,"training_authorization_basis":None,
           "candidate_value":"复用历史资料作局部观察；不能据此生成整栋实测复原。","local_file":"colonnade.jpg"}
    packet["images"]=[image]
    shutil.copy2(old/"references/colonnade.jpg",out/"colonnade.jpg")
    image["local_sha256"]=hashlib.sha256((out/"colonnade.jpg").read_bytes()).hexdigest()
    observations=[("columns","两排后退排列的深色圆柱"),("red_wall","廊柱后方红色墙面"),("roof","白色浅坡网格屋顶"),("stairs","外部台阶、平台及栏杆")]
    packet["facts"]=[{"fact_id":"fact-R002-"+key,"field":"observed_"+key,"value":value,"unit":None,"kind":"observation","status":"verified","source_ids":[],"image_ids":["img-R002"],"derived_from_fact_ids":[],"basis":"本轮直接查看历史用户照片，仅确认画面可见形态，不推导绝对尺寸或建筑身份。","conflict_group":None,"adoption_reason":None} for key,value in observations]
    for slot in packet["selection"]["slots"]:slot["missing_search"]="补充身份可核实、来源明确的整体、背面、侧面或俯视图；历史局部照片保留为补充观察。"
    packet["scale"]["selected_s"]=1
    packet["scale"]["ratio_candidates"]=[{"label":"历史试建比例，非测绘尺度确认","s":1}]
    packet["gaps"]=["实际宽、深、高未知，原试建参数不得回填为现实尺寸。","建筑身份、照片日期、公开来源与授权未独立核实。","缺整栋体量和背侧立面证据。","当前只输出research_context；没有经审核的真实施工坐标。"]
    dump(out/"packet.json",packet)
    dump(out/"research_context.json",adapt(out/"packet.json"))
    dump(out/"original_evidence.json",original)
    dump(out/"migration.json",{"kind":"manual_reviewed_legacy_migration","original_evidence":"vendor/buildkit_v03/projects/gafa_admin/evidence.json","original_evidence_sha256":hashlib.sha256((old/"evidence.json").read_bytes()).hexdigest(),"image_sha256":hashlib.sha256((out/"colonnade.jpg").read_bytes()).hexdigest(),"id_mapping":{"R002":"img-R002"},"geometry_generated":False,"notes":"Original bytes and evidence retained; no exact dimensions or public URLs invented. Full upstream delivery gate not requested; partial packet intake only."})
    print("Migrated R002 -> img-R002; 4 photo observations; all real dimensions remain unknown.")
if __name__=="__main__":main()
