# 已有工程与 Skill 能力核查

本轮优先实际代码和最新资产。研究包的 Skill 清单停留在工作流 0.1、V5 缺失状态；当前已安装 Architect Skill 为工作流 0.2，V5_r02 完整归档已恢复核验。以下修正只写入本研究报告，不覆盖原始文档。

## 1. 资产清单与真实位置

本轮根目录：`/workspace/scratch/cfe8adbb046e/ha-research-r03`。

| 名称/版本 | 实际位置 | 类型与安装状态 | 作用 |
|---|---|---|---|
| gafacraft-architect，工作流 0.2 | `/root/.codex/skills/remote-skills/skill-6ad7c490ca488191aefa1152167fbe16/SKILL.md` | 已安装个人 Skill | 研究、可选模型、构件取舍、调用案例/引擎、验证与交付 |
| gafacraft-building-reference，协议 1.1 | `/root/.codex/skills/remote-skills/skill-6ad26bc8a18081918d5339dd69880ed2/SKILL.md` | 已安装个人 Skill | 多向参考盒、来源核验、尺度、十节报告、图片离线打包 |
| real-to-minecraft，BuildKit 0.3 | `architect-v0.3/vendor/buildkit_v03/.agents/skills/real-to-minecraft/SKILL.md`，相对原工作区根目录 | 工程内 Skill，非独立安装个人 Skill | 参数化构建、NBT、阶段检查和区域差分 |
| Architect 0.3 / BuildingSpec 0.2 | 原工作区 `architect-v0.3/`；本轮隔离副本 `baselines/architect-v03/` | Python 工程，不是新 Skill | 参数契约、几何、模型读取、NBT、预览、修订守卫 |
| RTM Research R0.1 | `inputs/Haibaras_Architect_RTM_Research_Pack_v0.2/rtm_r01_source/RTM_Research_R0_1/` | 独立研究原型，未集成引擎 | 属性优先级、冲突、缓存键、简化度量 |
| 广州塔 V4_r02 | 研究包 `inputs/reference_archives/GAFAcraft_Canton280_V4_Code_And_Build.zip` 内 `canton-v4/` | 案例适配器与历史运行 | 内移环梁、主体/广场、灯光与分块 |
| 广州塔 V5_r02 | `baselines/广州塔_V5_代码建筑与反馈记录.zip`；本轮只读工作副本 `baselines/canton-v5/` | 案例工程与冻结产物 | 1F 以上塔脚、上层平台、场地融合 |
| 构件/裙楼研究页 | 研究包 `inputs/current_research/` | 资料、图片标注和设计研究，非独立 Skill | 16 张构件资料/30 区域；裙楼 12 张资料/层级关系 |
| 本轮 Lab R0.3 | `lab/`、`WORK_AUDIT/experiments/run01/` | 新隔离研究代码，未安装 | 单位/年代裁决、磁盘缓存、3D 锚点、上游网格到已有 NBT |

原始 Architect ZIP SHA256：`4d41eebcc2cb2b4bc00965bcfdc532347475db4b0a7160059e88a0a66c854d8c`。
原始 V5 ZIP SHA256：`d47a3d815dd2534fb7cd0b0599b765654846d4e78e80b5fa888b6dbddddd889d`。
上传研究包 SHA256：`d9480844e9351b8c189b73005d8b599d581f82c876ca041b8c97caf8c5257c73`。

## 2. 统一评级

A：已实现且相应测试通过，可复用。B：基本实现，需真实案例/局部优化或补测。C：规范或原型，关键能力未完成。D：尚未实现。评级限定到表中能力，不给整个系统贴一个笼统 A。

| 对象/能力 | 评级 | 文件或执行依据 | 缺口/边界 |
|---|---|---|---|
| 图片协议、包校验、图片离线打包 | A | vendor/building_reference；59+12+4 项本轮通过 | 校验不等于图片语义正确；当前个人 Skill 后加规则需另做案例验证 |
| 多向参考盒组织、视角与部件标签 | B | 参考协议 1.1；Component Study；16 张资料/30 区域 | 人工/AI 看图标注；不是自动相机配准或逐像素分割；近重复图识别仍需补充 |
| 文字研究、结构/设计意图与照片互证 | B | 图片 Skill 原有资料校验和报告；现有案例来源记录 | 尚非独立文字 Skill；维基/百科应作为线索，关键结构仍需原始资料核对 |
| 总控 Skill 的已有流程编排 | B | 已安装 workflow 0.2；V2–V5 案例记录 | 通用新建筑尚需适配器，未完成全自动选择/融合 |
| 参数化基础几何与有界构建 | A | geometry.py / spec_loader.py / validation.py；本轮主 suite 110 项通过 | 几何原语范围有限，不能代表任意网格 BuildingSpec 执行 |
| 多格式模型读取与规范坐标 | B | model_io.py；本轮 GLB/glTF/OBJ/STL/PLY/DAE/SKP 测试通过 | 历史真实建筑六格式来自同一 SKP 导出；层级、单位、纹理保真仍需异源模型验证 |
| 模型证据及参数绑定 | A | research_contract.py + schema 0.2；模型/来源/变换/绑定/冲突测试 | attach 只是候选，不会自动改变执行几何；非共线锚点旧契约仍靠审查 |
| NBT 导出与独立回读 | A | export_nbt.py → BuildKit writer + inspector；本轮回归及桥接 | 不证明目标模组注册、碰撞、透明或流体 |
| 稳定组件 ID、所有权、重叠限制、差分守卫 | A | geometry.py / research_contract.py / revision.py | 单次工程稳定，不保证跨格式导出仍是同一 ID |
| 真正按依赖增量重建 | C | revision.py 明写 full_regeneration / not_implemented；本轮仅新 Lab 实验 | 需要完整依赖、负空间/重叠和接口影响范围；未接主引擎 |
| RTM R0.1 属性裁决 | C | evidence.py；7 项测试本轮通过 | 固定排名、同一数值容差，单位未归一，缺年代/转载家族；不是视觉融合 |
| RTM R0.1 缓存 | C | cache.py 的 stage_key | 只有键，无读写、命中、依赖执行与损坏处理 |
| 本轮 Lab 属性/缓存/锚点实验 | C | lab/test_lab.py，21 项通过 | 合成夹具，尚未成为可替换正式模块；无建筑泛化结论 |
| 广州塔 V5 文件/分块 | A | 本轮独立读回、blocks.json 一致、9 分块精确拼回 | 仅文件层与坐标拼合 |
| 广州塔 V5 造型/空间真实性 | B | 历史 15 项案例检查；来源与构件取舍有记录 | 场地尺寸估算；46 等距环梁、核心接触、闭环未解决；审美待用户评价 |
| 自动像素分割、深度/遮挡恢复、图模配准 | D | 现有脚本未实现，本轮未推理视觉模型 | Lab 3D 锚点拟合不等于这些能力 |
| 通用自动审美融合/自动构件识别 | D | 案例采用人工/AI 审阅节点和参数 | 需要语义标注、证据对应、holdout 与失败回退 |
| Minecraft/NeoForge/Create 游戏验收 | D | 现有报告 pending；本轮未启动游戏 | 目标版本、导入器、注册表、流体/光照/可通行仍需真实测试 |

## 3. 可以复用的调用入口

| 模块 | 入口 | 输入 → 输出 |
|---|---|---|
| 模型读取 | `python tools/model_research.py import INPUT --out NEW_ASSET` | SKP/GLB/glTF/OBJ/DAE/STL/PLY → 模型文档、归一化网格、统计；无单位格式另传单位与 up |
| 模型候选绑定 | `tools/model_research.py attach` / model_io.attach_candidate | 资产 + BuildingSpec → 新候选记录；执行 components 保持 |
| 研究契约 | research_contract.validate_research | BuildingSpec 0.2 → 引用/尺度/参数值一致性检查 |
| 正式参数化构建 | `python tools/build.py`，参数以脚本实际帮助为准 | BuildingSpec → NBT、回读检查、固定视图、参数与报告 |
| 局部修订 | revision.guard_revision | before/after/request → 允许路径、范围、保护区、构件变化验证；内部全量生成 |
| NBT 适配边界 | export_nbt.export_and_readback | 已生成 Scene + 输出环境 → 原 NBT writer + 独立 reader |
| 广州塔 V5 | `python src/build_v5.py --run NEW_ID` | 案例参数/资料 → 新 run；本轮未执行生成 |

上述命令不能在只有 SKILL.md 或只有报告的目录直接运行。完整依赖与案例输入必须在位。

## 4. 六个旧错误的处理结论

研究包记录 Python 3.13.5、未精确锁依赖，241 项运行中有 6 errors：2 个 collada 缺失，1 个 openskp setup 缺失，3 个 GLB/glTF Duplicate node ID。

本轮使用 Python 3.12.14 和现有 model_deps，保留源代码，复跑得到 244 项通过。缺失 setup 恢复后 NativeSkp 的 3 项实际执行，计数不同是 suite setup 的差异。主 suite 为 110；其余 59/12/4/28/31。实际依赖见 `logs/architect_environment.json`。

不能因此声称 Python 3.13 已修复。重复 ID 发生在通用 reader 根据 scene graph 名称构造节点之后；本轮未复现原依赖图，根因暂列环境/reader 兼容性待定位。**不删除唯一性检查，也不先改正式 reader。**

另发现 `requirements-tested.txt` 的 numpy 是 2.3.5，而 `requirements-models.txt` 固定 2.5.4。这两个文件并非可以无条件同时安装的单一锁文件。本轮全回归实际用 2.5.4；本地新 Lab 使用系统 2.3.5。应整理成明确的 core/model 两组可复现配置，并记录平台，不能把一次通过写成所有组合都通过。

## 5. V4/V5 与反馈资料

V4_r02：报告给出 128×288×232、89,642 非空气单元、9 分块，NBT SHA256 `d6ba225adeb6801fb23637d4475d423773b4c9535edecc2480b555b97a47d9a4`。本轮打开归档并读参数/代码/报告，V4 几何检查按 `reported` 保留。

V5_r02：128×282×232，塔体 280 格，118,566 非空气单元。NBT SHA256 `9cacf7cc2ebe615e63b799c5fde792736af624a94b58414776e03e574855d18b`。本轮验证最终文件、逐坐标状态与 9 分块拼合；没有重生成 V5。354 发光块、15 项案例检查与上部冻结来自保存的报告，应与本轮只读验证分开理解。

V5_r01 的南侧台阶交接失败和 r02 修复记录保留。1F 行走面 Y=2，上层平台 Y=7；庭院截在 1F 是用户范围适配，不是完整建成广场复原。现有 46 道等距环梁、122 处核心接触/20 处竖井跳过是历史待解决记录；不能从导出通过推出环梁独立闭合。

已有研究页面不是新增生成器。Component Study 的区域框是语义研究标注；Podium Study 的旧图/建成图/用户图按用途区分，不能把所有绿色区域放在同一高度。当前图片 Skill 还明确低矮建筑默认 1:1、相连综合体共用比例，不把广州塔 280/600 套给所有建筑。

## 6. 下一轮每类 Skill 的练习与验收

| 对象 | 练习案例 | 最低验收 |
|---|---|---|
| 图片/文字研究 Skill | 同一建筑的设计稿、旧建成照、新改造照、转载裁剪图；一组室内与外框架混合图 | 年代/状态/来源家族可追溯；未知方位为空；不把核心筒当内饰，不把无玻璃区域补满；没有证据不输出精确尺寸 |
| 模型研究模块 | 来自不同作者的 SKP、GLB、OBJ/DAE；含毫米/英寸、镜像、嵌套实例、背景地形 | 显式单位/轴/原点报告；缺单位阻止执行；节点可追溯；重复实例不误计；独立导出不当同源 roundtrip |
| 总控/融合 Skill | 广州塔一个框架段与塔冠 + 低层建筑入口/房间 | 按属性选来源，冲突留痕；纯图片路径仍能执行；候选不静默改几何；区域外变化为零 |
| BuildKit/建造验证 | 有门洞的房间、开敞格构、平台楼梯、透明与灯光局部样板 | NBT 精确回读/分块；必要净空不丢；外宽偏差在预定界限；真实游戏中注册、通行与水/光检查后才标通过 |
| 裙楼/场地职责（尚未独立 Skill） | 广州塔 1F/上层平台和一个未调参的庭院建筑 | 承托面、标高、出入口、排除地下的截断面明确；不复制同心椭圆或等宽绿带充当真实拓扑 |

只有广州塔一个复杂案例时，合格结论是案例练习成功，不是通用 Skill 已训练完成。
