"""Write traceable case notes without changing any generated run."""
from pathlib import Path
import json
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    run=CASE/'runs/V1_r04';m=json.loads((run/'manifest.json').read_text())
    e=json.loads((CASE/'research/component_evidence.json').read_text())
    for c in e['components']:
        c['execution_status']='generated_V1_r04; manual geometric preview reviewed; user fidelity approval pending'
        if c['component_id']=='tower.facade':c['uncertainty']='铁栅栏替换过宽木活板门；颜色、连接外观仍需原版纹理和游戏邻接更新检查'
        if c['component_id']=='lighting.fixed':c['parameter_paths']='Cloud.lightlines 内固定坐标；lighting.warm_outline_faces_note 仅记录，不是可执行控制项'
    dump(CASE/'research/component_evidence.json',e)
    changes=[
      {'run':'V1_r01','status':'preserved prototype','issue':'高塔相对高度未采用最新正面建成照片；楼板与平台层高重叠','response':'转入 r02 修正'},
      {'run':'V1_r02','status':'preserved previewed prototype','issue':'竖肋过宽偏木色；窗间板覆盖玻璃；核心槽偏浅','response':'r03 改铁栅栏，横向细部移至玻璃外，核心玻璃加深'},
      {'run':'V1_r03','status':'preserved previewed prototype','issue':'屋顶开敞区混入窗后家具；楼梯末端与二层通道未接齐','response':'r04 增加屋顶内饰排除，补上平台并移除入口栏杆'},
      {'run':'V1_r04','status':'delivery baseline','issue':'背部平台、第三塔高度及场地仍属照片解释','response':'保留可审阅 V1；补平面或模型后再校准，不以技术通过替代还原度验收'}]
    dump(CASE/'history/revision_log.json',changes)
    dump(CASE/'review/feedback_template.json',{'schema_version':1,'case':'nanshan_cloud','baseline_run':'V1_r04','baseline_nbt_sha256':m['sha256'],'status':'awaiting actual user feedback; no feedback fabricated','items':[],'item_fields':['component_id','view_id','problem','requested_change','evidence_url','priority']})
    learning={'case':'nanshan_cloud','baseline_run':'V1_r04','engine':'HAF 0.2.0','case_adapter':'nanshan-cloud-0.1.1','category':'多塔错位 / 阶梯平台 / 双幕墙语汇 / 架空底部','learning_kind':'reviewed construction rules and case records, not neural model training','retained':['HAF state-aware partial blocks and connection solver','stable room IDs, warm/cool lamps and deterministic seed','independent NBT readback, module union, source-bound previews'],'new_case_rules':[{'rule':'塔体与退台使用独立楼板节奏，先检查整体并集再判断外露立面','consumer':'Cloud.floors_and_skin','failure':'r01 层高错位导致玻璃面被额外楼板切割'},{'rule':'窗间板、压边放到玻璃外层，保留连续围护','consumer':'Cloud.floors_and_skin','failure':'r02 用不透明细部替换玻璃'},{'rule':'屋顶设备区禁止合成办公室家具/窗灯','consumer':'Cloud.interiors','failure':'r03 屋顶混入办公室陈设'},{'rule':'前期设计图和建成照片分开，冲突时按构件取舍','consumer':'params.height_anchor / towers','failure':'早期高度和塔体差异容易被当作竣工几何'}],'generalization_status':'case validated offline; repeat on a second independent stepped building before promoting case assumptions to generic engine rules','limits':e['unknowns']+['当前渲染未加载资源包纹理','Minecraft 导入、邻接更新和可通行性待测','地面景观为范围内近似，不是园区全量还原'],'next_acceptance':['用至少一个独立视角复核平台深度和第三塔高度','加载纹理后检查铁栅栏和玻璃片连接，不出现外立面网格意外变化','以相同相机复核总体轮廓、退台、塔间槽、屋顶和柱廊','游戏导入后检查灯光、楼梯连接和无意洞口'],'source_manifest':'cases/nanshan_cloud/research/images.json'}
    dump(ROOT/'learning/nanshan_cloud_v1.json',learning)
    (CASE/'README.md').write_text(f'''# 南山云科技大厦 · HAF V1

交付基线：V1_r04；引擎 HAF 0.2.0；案例适配器 nanshan-cloud-0.1.1。
约 1 格/米，最高塔体 235 格；局部包围盒 140 × 244 × 140。
最终非空气方块：{m['non_air_blocks']:,}；NBT SHA256：{m['sha256']}。

这是深圳留仙洞万科云城六期 1 栋的图片研究案例，不是韩国南山塔。
本轮覆盖三组错位塔体、四组阶梯状平台、两种幕墙、屋顶设备区、架空柱廊、部分二层通道、入口与局部景观。没有采用 SU / 其他三维模型。
相对塔高、平面深度、后部平台和场地取照片近似；不含地下、周边楼群和拟建连廊。

## 复现

在工程根目录运行（Python 3.12、numpy、Pillow）：

```sh
python3 tools/agent.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/render_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/package_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 cases/nanshan_cloud/src/validate_case.py
```

生成无需联网。Linux 离线预览另需 EGL/Mesa。验证脚本固定比较已存的 V1_r04 / V1_replay，并核对已存最终预览。更改代码后要用新 run，不能覆盖历史。

## 研究与可修改位置

- `params.json`：坐标、塔高、相对尺寸、层高、种子、玻璃和肋条。
- `src/build_case.py`：特定建筑的阶梯外形、底部、屋顶、灯位规则；部分坐标仍是案例常量，没有虚构完全参数化。
- `research/images.json`：22 条候选索引，下载/查看/采用状态不同；不是 22 张全部经过验证的有效参考。
- `research/component_evidence.json`：构件证据、消费代码、冲突与待核实项。
- `history/revision_log.json`：r01 至 r04 自检与修改原因。
- `review/feedback_template.json`：用户反馈入口，尚未填写。
- `validation/acceptance.json`：独立读回与几何检查，不是写实度评分。

玻璃采用连续立面算法；`windows.json` 的空列表表示未使用独立窗洞登记器，并不表示没有窗。`interiors.json` 是程序化窗后空间记录，不能当作真实房间数。
后侧围护已生成，但不等于后侧形态已准确验证。预览来自实际 NBT，未加载 Minecraft 资源包纹理，未进入游戏。
''')
    guide='''南山云科技大厦 HAF V1 / 导入说明

目标数据版本：Minecraft Java 1.21.1（DataVersion 3955）。
本次只完成离线文件验证，未在 Minecraft / Create / WorldEdit 内试放。

包内提供完整 NBT、Sponge v3 .schem、分区 NBT、材料和方块状态 CSV。
Sponge v3 格式需使用兼容工具；NBT 分区文件每个不超过 256 KiB。
256 KiB 是本项目/Create 兼容检查的字节阈值，不代表原版结构方块能够直接放置该尺寸。
完整 NBT 大于 1 MB；若导入器限制文件大小，请用 modules，并按 module_offsets.csv 拼合。
模块最小角 = 统一项目原点 + offset_xyz。所有模块采用同一方向，不可分别旋转。

坐标：本地 X/Y/Z；Y 向上，+Z 为工作正面；真实地理北未核实。
包围盒：140 × 244 × 140；地面在局部 Y=4，铺装表面在 Y=4。
若整个包围盒放入默认 [-64,320) 世界高度区间，原点 Y 应在 -64 至 76 之间。
例如原点 Y=64，则建筑地面在世界 Y=68。请按自己的世界高度设置调整。

完整 .schem 包含空气；正常粘贴可能清除选区内旧物。
稀疏 NBT 和跳过空气的粘贴不会主动清空洞口内旧方块。建议在空白测试场地先预览。
这份文件不含实体、容器内容或真实完整室内交通。楼梯局部连接已检查，全楼可通行性未验。
窗后办公家具仅用于层次；背部平台和周边绿地的形状仍是照片解释。

夜景使用固定暖色灯带与部分亮起的室内灯，材料含荧石和海晶灯。
预览的有色光晕为离线近似，原版游戏不会按此传播彩色光。未放置未经确认灯位的航空障碍灯。
导入后重点检查铁栅栏/玻璃片邻接更新、活板门方向、屋顶设备区、空中平台和灯光。

完整材料表按方块 ID 合并；blockstates.csv 保留精确方向、半砖、玻璃片与铁栅栏连接状态。
导入工具参考：https://worldedit.enginehub.org/en/latest/usage/clipboard/
'''
    (run/'import_pack/IMPORT_GUIDE.txt').write_text(guide)
    print('case notes and feedback saved')
if __name__=='__main__':main()
