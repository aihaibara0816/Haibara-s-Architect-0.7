"""Rebuild the HAF 0.2 control catalog and release documentation; no geometry writes."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'

def main():
    DOC.mkdir(exist_ok=True)
    rows=[]
    def add(id,name,status,grade,controls,implementation,consumers,evidence,limits):
        rows.append(dict(id=id,name=name,status=status,grade=grade,controls=controls,
                         implementation=implementation,consumers=consumers,evidence=evidence,limits=limits))
    add('lighting.rooms','分区窗灯与稳定随机','integrated','B',
        ['CTF: lighting.seed / lighting.activity / lighting.crown_accents',
         '深圳: interior.seed / interior.activity / podium.lighting_seed',
         'room_lighting(seed, floor_id, room_id, zone, activity, namespace)'],
        ['hafusion/lighting.py'],
        ['cases/guangzhou_ctf/src/build_case.py','cases/shenzhen_press/src/build_case.py'],
        ['tests/test_lighting.py','cases/guangzhou_ctf/runs/V1/rooms.json','cases/shenzhen_press/runs/V2/rooms.json'],
        'activity 只是概率基值，加入楼层/分区偏移后截断到 0.08–0.88；0/1 不是全关/全开。荧石选择阈值 0.46 是源码常量，不是可调参数。保留各案例原 namespace；CTF 每房至多放一个灯，不消费所有 fixture_count/offset 提案。crown_accents 为候选开关；CTF V1 实际专用 crown_accent 单元为 0。未在游戏中验证。')
    add('lighting.slots','不破坏幕墙的灯位预留','integrated','B',
        ['first_clear_slot(candidates, occupied, reserved, connection_sensitive)'],
        ['hafusion/lighting.py'],['cases/guangzhou_ctf/src/build_case.py'],
        ['tests/test_light_slots.py'],
        '已用于 CTF；调用方负责边界、支撑与候选生成。暗房也预留灯位，避免换种子改变几何；不能据此推断深圳已接入同一预留策略。')
    add('lighting.fixed','按实景固定灯带与轮廓','sample_only','C',
        ['night_study.py 的已观察立面、试验标高和灯位列表（案例源码）'],
        ['cases/guangzhou_ctf/experiments/detail_v2/night_study.py'],
        ['cases/guangzhou_ctf/experiments/detail_v2/runs/night_pattern_candidate/building.nbt'],
        ['cases/guangzhou_ctf/experiments/detail_v2/runs/night_pattern_candidate/diff.json'],
        '306 个声明灯位改动，玻璃和竖肋未改。仅 +Z/-X 两面候选；约 198m 是试验锚点，北向/背面和最终标高未确认。尚未接入 agent 的建筑参数；不是整栋 CTF V2。')
    add('lighting.obstruction','航空障碍灯比例样板','sample_only','C',
        ['beacon(kind,x,y,z): glass_ring / recessed_cap / torch'],
        ['cases/guangzhou_ctf/experiments/detail_v2/study.py'],
        ['cases/guangzhou_ctf/experiments/detail_v2/runs/beacon_board/building.nbt'],
        ['cases/guangzhou_ctf/experiments/detail_v2/runs/beacon_board/inspection.json',
         'cases/guangzhou_ctf/experiments/detail_v2/runs/beacon_context_recessed_cap/inspection.json'],
        '3×3 红玻璃片包罩、1×1 嵌入罩、红石火把已输出 NBT。CTF 1:2 的 3×3 约 6m，容易夸大；上下文位置仅比例试验。无真实灯位确认、闪烁电路或游戏投射光色验证。')
    add('interiors.case','窗后层、背墙与基础陈设','integrated','B',
        ['CTF: interior.room_bay_blocks / depth_blocks / floor_slab',
         '深圳: interior.floor_ys / room_centers_x（及已有种子）'],
        ['cases/guangzhou_ctf/src/build_case.py','cases/shenzhen_press/src/build_case.py'],
        ['cases/guangzhou_ctf/runs/V1/building.nbt','cases/shenzhen_press/runs/V2/building.nbt'],
        ['cases/guangzhou_ctf/runs/V1/rooms.json','cases/shenzhen_press/runs/V2/rooms.json'],
        '已存在案例化窗后遮挡、楼板和简单家具。playable_floors=false 是范围声明，不是可切换的可游玩楼层生成开关；不宣称真实户型。')
    add('interiors.styles','四类伪内饰与净高控制','sample_only','C',
        ['room_style(seed,room_id,clear_height,zone)',
         'furnishing_cells(style,clear_height): work / library / lounge / green'],
        ['hafusion/interiors.py'],
        ['cases/guangzhou_ctf/experiments/detail_v2/study.py'],
        ['tests/test_detail_feedback.py','cases/guangzhou_ctf/experiments/detail_v2/runs/facade_hybrid/inspection.json'],
        '书架、铁砧、台面、座椅和树叶盆栽已用于 24 个局部样板房间。净高不足不放两格盆栽；office/residential/hotel 暖光比例 0.55/0.75/0.80 是源码常量，和整栋 room_lighting 的 0.46 阈值不是同一控制。尚未替换两个整栋适配器的室内逻辑。')
    add('facade.layers','竖向幕墙与薄构件','integrated','B',
        ['CTF: facade.pitch_blocks / phase / glass / fin / lobby_clear_height',
         'skin_cell 的方向、节距、相位、玻璃与外肋'],
        ['hafusion/facade.py','support/detail_lab/states.py'],
        ['cases/guangzhou_ctf/src/build_case.py'],
        ['tests/test_vertical_facade.py','cases/guangzhou_ctf/runs/V1/building.nbt'],
        '玻璃片、墙、铁栅栏、半砖、楼梯、活板门等已有状态表达；不是任意方块/模组注册器。铁栏杆/混合主肋对照仍属样板，不能默认用深色铁栏替换所有浅色主肋。')
    add('render.emission','材质发光颜色与旧版回放','integrated','B',
        ['emission_shader(source, policy=material/legacy)；实际函数入口及渲染器参数见源码'],
        ['support/detail_lab/shading.py','support/vendor/render_egl.py'],
        ['cases/guangzhou_ctf/experiments/detail_v2/study.py'],
        ['tests/test_detail_feedback.py','cases/guangzhou_ctf/experiments/detail_v2/night_outputs.json'],
        '已纠正把不同发光材料强制染成同色的预览问题；保留旧策略。状态盒与近似光照不是原版材质、RGB 投射光或游戏碰撞；渲染改善不得计为新增建筑几何。')
    add('evidence.parameters','构件取舍、参数守卫与缓存','integrated','B',
        ['稳定 component_id / 候选来源 / adopted_parameters / frame_id',
         'apply_reviewed / apply_building_spec / Stages'],
        ['hafusion/evidence.py','hafusion/cache.py'],
        ['cases/guangzhou_ctf/src/build_case.py','cases/shenzhen_press/src/build_case.py'],
        ['tests/test_hafusion.py'],
        '由研究者明确构件和参数；不做自动相机配准或通用构件识别。阶段失效是保守策略，不保证任何局部改动都只重算该构件。')
    add('model.research','可选模型读取与检查','inherited','B',
        ['ha03/tools/model_research.py import / preview / attach'],
        ['ha03/tools/model_research.py','ha03/architect/model_io.py'],
        ['ha03/architect/model_compare.py'],
        ['ha03/docs/MODEL_RESEARCH_0.3.md'],
        '继承 HA0.3 已有研究入口与历史格式验证；本次不重跑全部 SKP/GLB/glTF/OBJ/STL/PLY/DAE 套件。attach 只登记候选。CTF 尚无下载并导入的 SU/三维网格；纯图片路线继续可用。')
    add('agent.cases','统一主线入口','integrated','B',
        ['python3 tools/agent.py --case <registered_case> --run NEW_RUN [--params FILE]',
         '--version / --catalog（只读）'],
        ['tools/agent.py','agent_config.json'],
        ['cases/shenzhen_press/src/build_case.py','cases/guangzhou_ctf/src/build_case.py'],
        ['tests/test_hafusion.py'],
        '仅注册深圳特区报业大厦和广州周大福；广州塔旧入口保留供历史复跑。新建筑需要新的构件研究和适配器；目录中存在控制目录不代表所有条目已由生成器消费。')
    add('game.acceptance','游戏内导入、碰撞和夜景验收','pending','D',
        [],[],[],[],
        '尚未连接游戏。本版本不宣称完成导入、透明纹理、障碍灯远距可见性、内饰通行或原版/光影亮度验收。')
    catalog=dict(schema_version='1.0',engine_version='0.2.0',updated_at='2026-10-23',
                 purpose='Read-only index of actual controls, consumers and gaps; NOT a build profile or automatically applied defaults.',
                 grading={'A':'已实现且在注明范围内测试可复用','B':'基本实现，仍需补充测试或局部优化','C':'规范或局部原型，关键接入缺失','D':'尚未实现或验证环境尚未接入'},
                 capabilities=rows)
    (DOC/'haf_0_2_capabilities.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    config=json.loads((ROOT/'agent_config.json').read_text())
    config.update(engine_version='0.2.0',release_label='HAF 0.2',control_catalog='docs/haf_0_2_capabilities.json')
    (ROOT/'agent_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'README.md').write_text("""# HAF 0.2

后续建筑 Agent 的主线。0.2 把已有的构件研究、灯光、薄构件、窗后层与伪内饰样板统一编目，并增加只读版本/能力入口；不重新生成历史建筑。

- 项目总览与交付缺口：`docs/HAF_0.2.md`。
- 实际控制、消费者和证据：`docs/haf_0_2_capabilities.json`。该文件是目录，不是自动应用的参数配置。
- 已注册案例：`cases/shenzhen_press/README.md`（V2）、`cases/guangzhou_ctf/README.md`（V1）。
- 周大福后续灯光/内饰/障碍灯：`learning/ctf_night_detail_study.md` 与 `cases/guangzhou_ctf/experiments/detail_v2/`。仍为局部研究，不等于已验收整栋 V2。

```bash
python3 tools/agent.py --version
python3 tools/agent.py --catalog
python3 tools/agent.py --case guangzhou_ctf --run NEW_RUN
PYTHONPATH=support/deps python3 -m unittest discover -s tests -v
```

使用新 run 名；旧输出拒绝覆盖。案例参数仍在各自 `research/parameters.json`，新参数副本通过 `--params` 传入。研究图数量不限，原六图 Skill 服务外部建筑 AI。

房间随机灯光已用于两个整栋案例；固定实景灯带、航空障碍灯与四类新伪内饰仍有样板范围限制。没有通用自动构件识别、盲融合或 Minecraft 施工。最终光照/透明纹理/碰撞仍需游戏验证。

保留 HA0.3、广州塔 V5 及旧 run。广州塔 `tools/build.py` 是原 0.1 路线；其版本标记不改写为新算法。原 README 归档于 `history/pre_haf_0_2/README.md`，另有更早快照。旧工作目录名 HAFusion-0.1 不代表当前包版本；发行 ZIP 根目录为 HAF-0.2。

本次源代码包以已交付 CTF 研究包为基础，保留其成员，再加入 0.2 文档与入口。包含 HA0.3 依赖、CTF V1/局部实验、深圳 V2 所需基线；不替代全部广州塔/V5/SKP 原始归档。详细范围见包内 ARCHIVE_SCOPE.txt。Skill 安装通过独立 Skills 保存，不把工程 ZIP 当 Skill 安装包。
""")
    header="""# 0.2.0 / 2026-10-23

- 汇总当前 HAF 主线、两例建筑、已实现窗灯/薄构件及局部夜景/伪内饰/障碍灯实验的真实边界。
- 新增只读 `--version` 和 `--catalog`；保留原生成命令和案例参数位置。
- 新增控制目录、工作流、交付缺口与验收分级；版本号从 0.1.0 变为 0.2.0。
- 本次发布整理不改生成算法、案例参数、方块状态、随机 namespace 或历史 NBT。先前研究已完成的着色修正/灯位预留/伪内饰模块纳入 0.2 清单，不冒充此次新增算法。
- HAF 为工程版本；Architect 编排规则 0.2.2、HA 研究规则 0.2.1、BuildingSpec 0.2 与 BuildKit 0.3 各自版本独立。

"""
    old=(ROOT/'history/pre_haf_0_2/CHANGELOG.md').read_text()
    (ROOT/'CHANGELOG.md').write_text(header+old)
    learning=(ROOT/'history/pre_haf_0_2/learning/README.md').read_text()
    (ROOT/'learning/README.md').write_text(learning+"""

## HAF 0.2 归纳

- `ctf_night_detail_study.md`：固定灯带、冷暖预览修正、四向/塔顶、薄肋、四类伪内饰、三种障碍灯比例。失败样本继续保留。
- `../docs/haf_0_2_capabilities.json`：区分整栋消费者、局部样板、源码常量和未实现项。
- 下一步先把认可的样板按构件接入新 run，再做目标游戏验收及不同建筑迁移；不能通过改版本号把样板升级为通用能力。
""")
    print(json.dumps({'controls':len(rows),'engine_version':config['engine_version']},ensure_ascii=False))

if __name__=='__main__':main()
