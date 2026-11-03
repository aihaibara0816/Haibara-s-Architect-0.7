"""Explicit engineering design fixtures. These are not recovered 7-Eleven assets."""
from pathlib import Path
import json,copy,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.packet_adapter import adapt

ROOT=Path(__file__).resolve().parents[1]
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def provenance(basis="本轮工程设计参数；用于验证生成闭环，不是现实建筑测绘"):
    return {"status":"design_choice","basis":basis,"fact_ids":["fact-design-brief"],"source_ids":[],"image_ids":[]}

def packet(name,brief):
    p=json.loads((ROOT/"vendor/building_reference/references/packet-template.json").read_text())
    p["packet_id"]="packet-"+name;p["collected_at"]="2026-10-20"
    p["subject"].update(name=brief["name"],kind="single",identity_status="provisional",version="2026-10-20工程研究样板",boundary=brief["scope"])
    p["provenance"].update(user_input=brief["input"],research_status="incomplete")
    p["facts"]=[{"fact_id":"fact-design-brief","field":"construction_translation","value":brief["input"],"unit":None,"kind":"suggestion","status":"proposed","source_ids":[],"image_ids":[],"derived_from_fact_ids":[],"basis":"用户授权首轮小型建筑与变截面塔楼技术验证；本条为本轮工程提案，不声称实际建筑事实。","conflict_group":None,"adoption_reason":None}]
    p["scale"]["selected_s"]=1;p["scale"]["ratio_candidates"]=[{"label":"1 block per study metre","s":1}]
    p["staging"].update(required=False,reason="单一小型工程测试样例；几何按有序构件生成，无需拆分蓝图。")
    for slot in p["selection"]["slots"]:slot["missing_search"]="本次为原创技术研究样板，无对应现实原型或合格实景图；真实复原需另建项目采集对应视角。"
    p["prompts"]["full"]=(brief["input"]+"本项目仅检验确定性参数生成、NBT文件导出以及由文件读回得到的五视角预览。所有场地与构件尺寸均为工程设计参数，真实建筑米制尺寸保持未知。不要把案例标为711、罗森或广州西塔的实测复原。生成器只能执行单独审核的构件数据，不从本段自由文本猜测位置或运行代码。先构造主体、开口、屋顶，再补少量入口铺地和边界绿化；确认方块数据一致后才生成预览。游戏兼容性留待测试世界验证。")
    p["prompts"]["short"]=brief["input"]+"使用独立工程参数执行研究样板；保留未知真实尺寸，输出NBT和同源五视图，游戏验收待定。"
    for sec in p["report_sections"]:
        sec["content"]="工程研究样板。"+brief["scope"]+" 真实资料与尺寸尚未取得，不作实测复原声明。"
        sec["fact_ids"]=["fact-design-brief"]
    p["report_sections"][5]["content"]=p["prompts"]["full"];p["report_sections"][6]["content"]=p["prompts"]["short"]
    p["guidance"]["scope"]=brief["scope"]
    p["guidance"]["site"]="工程提案：小范围入口铺装与边界过渡，不复制周边楼群。"
    p["gaps"]=["没有对应现实建筑的测绘尺度。","当前游戏实例配置未读取，Create导入待实测。","没有已核验实景参考图；本次不是自动看图复原。"]
    return p

def base(name,title,size,scope):
    return {"schema_version":"0.1","spec_id":name,"revision":1,"mode":"study",
     "building":{"name":title,"identity_status":"design_study","real_world_reference":None,"scope":scope},
     "coordinates":{"units":"m","axis_convention":"X_right_Y_up_Z_back","front":"-Z","north":None,"blocks_per_metre":1,"size_blocks":size,"extent_m":size,"rounding":"half_up"},
     "environment":{"minecraft_version":"1.21.1","data_version":3955,"neoforge_version":"21.1.244","create_version":"6.0.10","configuration_status":"historical_target_unverified",
       "world":{"min_y":None,"max_y_exclusive":None,"origin_xyz":None,"confirmed":False,"basis":"历史目标版本；未连接当前Minecraft客户端或服务器，无已确认放置位置。"},"budgets":{"max_cells":1000000,"max_non_air_blocks":250000,"max_cell_visits":5000000}},
     "study_parameters":{"extent_m":size,"basis":"本轮工程试值，包含地景与边缘余量；不覆盖现实尺寸。"},
     "materials":{},"components":[],"levels":[],"lighting":{"component_ids":[],"simulation_status":"blocks_only_no_game_light_simulation"},
     "acceptance":{"clear_air_boxes":[],"walk_paths":[],"minimum_level_clearance_m":3,"profile_relationships":[]},
     "unresolved":[],"deviations":[{"component_id":None,"description":"仅使用整立方体方块；细小窗框、弧面采用整格表达。","authorization":"研究样板技术范围；非声称现实原型的精确复原。"}],
     "review":{"approved_for_strict_reconstruction":False,"basis":"技术研究样板；事实尺度和游戏验收尚未完成。"},
     "output":{"format":"java_structure_nbt","include_air":True,"views":["front","back","left","right","iso45"]}}

def material(spec,key,state,color,role):spec["materials"][key]={"block_state":"minecraft:"+state,"preview_color":color,"role":role}
def component(spec,cid,name,kind,parameters,mat,operation="add",targets=None):
    c={"component_id":cid,"name":name,"kind":kind,"operation":operation,"material":mat,"targets":targets or [],"after":[spec["components"][-1]["component_id"]] if spec["components"] else [],"provenance":provenance(),"parameters":parameters}
    spec["components"].append(c);return c
def box(spec,cid,lo,hi,mat,operation="add",targets=None):return component(spec,cid,cid,"box",{"min_m":lo,"max_m":hi},mat,operation,targets)

def retail():
    s=base("retail_store","GAFA便利店技术样板",[34,12,26],"独立单层便利店、入口小广场、轻量绿化与服务侧门；非711复原。")
    for x in [("foundation","stone_bricks","#858F8A","基础"),("paving","smooth_stone","#C6CBC5","铺地"),("white","white_concrete","#EBE8DA","墙体"),("dark","gray_concrete","#454E50","屋面与窗框"),("glass","cyan_stained_glass","#518794","玻璃整块示意"),("green","green_concrete","#326750","招牌"),("amber","orange_concrete","#D88445","招牌细带"),("wood","oak_planks","#B29A72","室内与雨棚格栅"),("light","sea_lantern","#F6E9BB","灯块"),("plants","moss_block","#65824E","绿化"),("planter","polished_andesite","#999E92","花池边界")]:material(s,*x)
    box(s,"site.foundation",[0,0,0],[34,1,26],"foundation")
    box(s,"site.paving",[1,1,1],[33,2,25],"paving")
    box(s,"store.floor",[5,1,7],[29,2,23],"white")
    box(s,"wall.front",[5,2,7],[29,8,8],"white")
    box(s,"wall.back",[5,2,22],[29,8,23],"white")
    box(s,"wall.left",[5,2,8],[6,8,22],"white")
    box(s,"wall.right",[28,2,8],[29,8,22],"white")
    # Subtract from explicitly owned walls; later glazing is a separate component.
    for cid,lo,hi,target in [("entry",[15,2,7],[19,6,8],"wall.front"),("front_left",[7,3,7],[13,6,8],"wall.front"),("front_right",[21,3,7],[27,6,8],"wall.front"),("left_window",[5,3,12],[6,6,19],"wall.left"),("right_window",[28,3,10],[29,6,16],"wall.right"),("service_door",[28,2,19],[29,5,21],"wall.right"),("rear_window",[9,4,22],[15,6,23],"wall.back")]:
        box(s,"opening."+cid,lo,hi,None,"subtract",[target])
        if cid not in ("entry","service_door"):box(s,"glazing."+cid,lo,hi,"glass")
    box(s,"entry.frame_left",[14,2,6],[15,6,8],"dark")
    box(s,"entry.frame_right",[19,2,6],[20,6,8],"dark")
    box(s,"entry.header",[14,6,6],[20,7,8],"dark")
    box(s,"roof.main",[4,8,6],[30,9,24],"dark")
    box(s,"roof.upper",[6,9,9],[28,10,22],"white")
    box(s,"roof.vent",[24,10,18],[27,11,21],"dark")
    box(s,"sign.band",[6,7,5],[28,9,6],"green")
    box(s,"sign.amber_line",[6,6,5],[28,7,6],"amber")
    for i,(lo,hi) in enumerate([([8,7,4],[9,9,5]),([9,8,4],[11,9,5]),([11,7,4],[12,9,5])]):box(s,"sign.emblem_"+str(i),lo,hi,"white")
    box(s,"canopy",[14,6,3],[20,7,6],"wood")
    for i,x in enumerate([7,12,21,26]):
        box(s,"ceiling.light_"+str(i),[x,7,10],[x+1,8,20],"light");s["lighting"]["component_ids"].append("ceiling.light_"+str(i))
    # Interior is an explicit design proposal, with a 4-block central aisle.
    for i,x in enumerate([9,22]):
        box(s,"shelf.base_"+str(i),[x,2,12],[x+2,3,19],"wood")
        box(s,"shelf.top_"+str(i),[x,4,12],[x+2,5,19],"wood")
        for z in [12,18]:box(s,f"shelf.side_{i}_{z}",[x,3,z],[x+2,4,z+1],"white")
    box(s,"counter",[22,2,9],[27,4,11],"wood")
    box(s,"counter.worktop",[22,4,9],[27,5,11],"dark")
    box(s,"rear.storage",[18,2,20],[25,5,22],"white")
    # L-shaped planter tests polygon extrusion without introducing a second building.
    component(s,"site.planter_left","入口L形花池","polygon_prism",{"vertices_xz_m":[[2,2],[11,2],[11,4],[4,4],[4,10],[2,10]],"y_min_m":2,"y_max_m":3},"planter")
    box(s,"site.plants_left",[3,3,2],[10,4,3],"plants")
    box(s,"site.plants_side",[2,3,4],[3,4,9],"plants")
    box(s,"site.planter_right",[24,2,2],[31,3,4],"planter")
    box(s,"site.plants_right",[25,3,2],[30,4,3],"plants")
    box(s,"site.bench",[7,2,5],[12,3,6],"wood")
    box(s,"site.service_pad",[30,2,18],[33,3,23],"planter")
    s["levels"]=[{"level_id":"ground","floor_top_m":2,"ceiling_bottom_m":7,"use":"单层商店，室内为工程补全","provenance":provenance()}]
    s["acceptance"]["clear_air_boxes"]=[{"check_id":"entry.clear","min_m":[15,2,6],"max_m":[19,6,9]},{"check_id":"central_aisle","min_m":[15,2,9],"max_m":[19,5,20]}]
    s["acceptance"]["walk_paths"]=[{"check_id":"public_access","start_xyz_m":[17,2,2],"end_xyz_m":[17,2,19],"headroom_m":3},{"check_id":"service_access","start_xyz_m":[27,2,20],"end_xyz_m":[29,2,20],"headroom_m":3}]
    return s

def tower():
    s=base("tower_segment","变截面塔楼结构测试段",[32,76,30],"检验下部收分、中段鼓起、顶部再收窄及多层楼板；非广州IFC复原，无完整室内交通。")
    for x in [("base","stone_bricks","#8C9690","基础"),("paving","smooth_stone","#C9CEC5","铺装"),("glass","light_blue_stained_glass","#5B8C9D","幕墙示意"),("frame","white_concrete","#E1E1D4","竖向框架和楼板"),("green","moss_block","#668457","边界绿化")]:material(s,*x)
    box(s,"site.foundation",[0,0,0],[32,1,30],"base")
    box(s,"site.paving",[1,1,1],[31,2,29],"paving")
    box(s,"site.left_green",[2,2,5],[4,3,25],"green")
    box(s,"site.right_green",[28,2,5],[30,3,25],"green")
    sections=[{"y_m":y,"cx_m":16,"cz_m":15,"width_m":w,"depth_m":d} for y,w,d in [(2,14,12),(14,12,10),(38,22,18),(56,16,14),(72,10,8)]]
    floors=list(range(2,69,6))
    component(s,"tower.shell","连续变截面主体","profile_shell",{"sections":sections,"section_shape":"ellipse","interpolation":"linear","wall_thickness_m":1,"floor_levels_m":floors,"floor_thickness_m":1,"floor_material":"frame","mullion_pitch_m":4,"mullion_material":"frame","cap_top":True},"glass")
    for i,y in enumerate(floors[:-1]):s["levels"].append({"level_id":f"level_{i}","floor_top_m":y+1,"ceiling_bottom_m":y+6,"use":"结构检验楼板；无垂直交通设计","provenance":provenance()})
    s["acceptance"]["clear_air_boxes"]=[{"check_id":"interior_headroom","min_m":[15,3,14],"max_m":[17,8,16]}]
    s["acceptance"]["profile_relationships"]=[{"component_id":"tower.shell","lower_y_m":4,"middle_y_m":38,"upper_y_m":69,"expectation":"middle_wider_than_ends"}]
    s["unresolved"].append("此塔楼仅为结构段，未设计入口、楼梯、电梯、消防或完整室内流线，不能作为可使用整楼。")
    return s

def main():
    for case,make,input_text in [("retail_store",retail,"制作一栋独立单层便利店技术样板，绿色招牌、玻璃店面、中央入口和少量入口绿化；保留通行空间。"),("tower_segment",tower,"制作一段下部较窄、中部鼓起、顶部收窄的塔楼结构样板，加入楼板及简化幕墙，检验连续变截面。")]:
        spec=make();folder=ROOT/"examples"/case
        p=packet(case,{"name":spec["building"]["name"],"scope":spec["building"]["scope"],"input":input_text})
        save(folder/"packet.json",p);save(folder/"construction_overlay.json",spec)
        save(folder/"building_spec.json",adapt(folder/"packet.json",folder/"construction_overlay.json"))
        (folder/"input.txt").write_text(input_text+"\n本例由当前助手把简短要求整理为显式构件数据；尚未接入自动模型服务。\n",encoding="utf-8")
        print(case,len(spec["components"]))
if __name__=="__main__":main()
