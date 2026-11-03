"""Demonstrate old photo + historical assumptions -> generic BuildingSpec.

This intentionally simplifies BuildKit's slabs/fences to supported full cubes.
It is not byte-equivalent to the original, nor a newly surveyed reconstruction.
"""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.create_examples import base,material,box
from architect.legacy import ROOT
from architect.pipeline import dump
from architect.packet_adapter import adapt

def main():
    folder=ROOT/"examples/legacy_gafa_research"
    p=json.loads((ROOT/"vendor/buildkit_v03/projects/gafa_admin/parameters.json").read_text())
    s=base("legacy_gafa_colonnade","广美行政楼廊柱局部历史资料",p["size_xyz"],"复用R002照片可见形态与历史研究参数，验证真实资料到新协议的接入；仅廊柱局部。")
    s["building"]["identity_status"]="provisional"
    for entry in [("base","stone_bricks","#8F9690","基础"),("paving","smooth_stone","#C9CBBE","铺装"),("red","red_terracotta","#9B5143","红墙"),("column","gray_concrete","#454C4B","柱"),("roof","smooth_quartz","#E9E8DE","屋顶")]:material(s,*entry)
    box(s,"ground.foundation",[0,0,0],[22,1,34],"base")
    box(s,"ground.paving",[0,1,0],[22,2,34],"paving")
    box(s,"wall.red_core",[2,2,2],[4,18,32],"red")
    def roof_y(x):return math.floor(p["roof_high_y_assumed"]-(x-2)*p["roof_slope_assumed"])
    for row,cx in enumerate(p["column_centres_x"]):
        for i in range(p["bay_count"]+1):
            z=int(p["first_column_z"]+i*p["bay_pitch_metres_assumed"])
            box(s,f"columns.r{row}.c{i}",[cx-1,2,z-1],[cx+1,roof_y(cx),z+1],"column")
    for x in range(2,21):box(s,f"roof.strip_{x}",[x,roof_y(x),1],[x+1,roof_y(x)+1,33],"roof")
    for i,z in enumerate([5,13,21,29]):
        for x in range(4,20):box(s,f"roof.beam_{i}_{x}",[x,roof_y(x)-1,z],[x+1,roof_y(x),z+1],"roof")
    box(s,"landing",[4,2,14],[8,6,20],"red")
    for i in range(4):box(s,f"stairs.step_{i}",[14-i*2,2,15],[16-i*2,3+i,19],"paving")
    box(s,"opening.ground",[2,2,10],[4,5,12],None,"subtract",["wall.red_core"])
    box(s,"opening.landing",[2,6,16],[4,9,18],None,"subtract",["wall.red_core"])
    for c in s["components"]:
        cid=c["component_id"]
        fact="fact-R002-columns" if cid.startswith("columns") else "fact-R002-roof" if cid.startswith("roof") else "fact-R002-red_wall" if cid.startswith("wall") else "fact-R002-stairs"
        c["provenance"]={"status":"design_choice","basis":"照片只支持构件形态；坐标、柱距、屋顶高度和坡度复用旧parameters.json的明确研究假设，整方块适配由本轮显式编写。","fact_ids":[fact],"source_ids":[],"image_ids":["img-R002"]}
    s["acceptance"]["clear_air_boxes"]=[{"check_id":"ground_opening","min_m":[2,2,10],"max_m":[4,5,12]}]
    s["unresolved"]=["没有重新测量建筑；所有原尺寸仍为null。","新引擎仅整方块，屋顶、柱头、楼梯和栏杆较旧BuildKit样板进一步简化；不与旧NBT声称等价。","楼梯通行性和游戏放置未实测。"]
    s["deviations"].append({"component_id":None,"description":"旧版本的半砖屋面、半级踏步与围栏暂未移植，使用整格阶梯屋顶与简化台阶。","authorization":"新协议全立方体原型范围；保留旧实现可回看。"})
    dump(folder/"construction_overlay.json",s)
    dump(folder/"building_spec.json",adapt(folder/"packet.json",folder/"construction_overlay.json"))
    print("Historical photo and assumed parameters adapted through generic components:",len(s["components"]))
if __name__=="__main__":main()
