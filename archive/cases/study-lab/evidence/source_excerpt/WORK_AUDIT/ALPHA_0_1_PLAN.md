# Alpha 0.1 最小接入计划（提案，待确认）

本轮 Lab R0.3 不是 Alpha 0.1 成品，也不是已安装的新 Skill。以下安排均在现有核心之上推进；正式 workflow 修改按用户要求等待确认。

## 1. 推荐边界

继续使用 Architect 0.3 / BuildingSpec 0.2。图片研究和可选模型研究产生候选；外置证据记录保存属性/来源/单位/年代；人工/Agent 审阅后的取舍经适配器写入现有 `research.parameter_bindings` 与构件参数；原生成、NBT 独立回读和差分守卫保持。

第一批不把任意网格强行塞进只支持特定原语的 BuildingSpec。复杂广州塔网格继续使用案例适配器和明确的输入/输出接口。提案中也不把父子层级当成已存在的增量执行器。

## 2. 可审阅接口

| 接口 | 最小字段 | 保证/失败方式 | 状态 |
|---|---|---|---|
| EvidenceCandidate | component_id、attribute、value/unit、source_id、source_family、source_type、epoch、phase、status | 未知单位不能执行；跨年代分开；转载不重复计支持 | Lab 实现基本裁决；尚未接真实 packet |
| EvidenceDecision | 原值/归一值、候选/排除、冲突、取舍原因、baseline_hash、automatic_write=false | 对相同等级冲突给 needs_review；不输出平均形态；估算保持估算 | Lab 已测，字段到 schema 的适配待开发 |
| AlignmentCandidate | 源/目标 frame、单位、锚点 IDs、4×4 变换、拟合与留出残差 | 至少 3 个非共线锚点；只允许正尺度刚性旋转/平移；异常保持待审 | Lab 仅有 3D 数学拟合；图像锚点与完整元数据尚缺 |
| ProposedSpecChange | base_spec_sha、component_id、parameter_path、old/new、evidence_refs、reason | 先校验旧哈希与参数路径；经现有 guard；不变更引用证明的含义 | 方案，待 C1 |
| GeometryArtifact | frame_id、bounds、稀疏占用或解析几何、component ownership、source/algorithm hashes | 每构件输入明确，负空间和重叠规则可追溯 | 通用执行接口待 C2；不能直接用最终网格恢复构件 |
| CacheEntry | stage/component、版本/代码标识、角色化依赖哈希、参数、frame/units、目标年代、结果哈希 | 改角色、原点/单位、来源、算法均失效；损坏拒绝；冷/热结果相同 | Lab 单进程实验；无多进程锁、LRU、磁盘配额或完整 DAG |
| ComparisonRun | 输入/代码/参数/调色板哈希、尺寸/相机/环境、文件/几何/游戏结果、人工评分、费用工时 | 缺项明确 pending；不同 track 不混算 | 方案与本轮局部结果；待 benchmark runner |

日期字段至少区分建筑年代、资料拍摄/发布日、检索日、算法缓存版本。不能用一个 epoch 覆盖这些含义。

## 3. 最小修改对照表

表中路径相对既有 Architect 工程或安装 Skill；“拟升级”表示尚未修改。

| 对象/文件 | 保留不动 | 拟最小修改/新增 | 确认点 |
|---|---|---|---|
| `architect/export_nbt.py`、`legacy.py`、vendor writer/inspect_build | 原导出、独立回读、有界解析与禁止覆盖 | 外部网格桥接调用现有 API，不复制一套 writer | C1 只接外围 |
| `architect/model_io.py`、`model_compare.py` | 原读取、单位轴、唯一 ID、路径限制与候选语义 | 先锁环境/异源回归；若复现问题再提针对补丁 | 本轮没有足够证据改 reader |
| `requirements-tested.txt`、`requirements-models.txt` | 历史文件保留为旧运行证据 | 新建有明确 Python/平台的 core/model 配置；解决 numpy 版本组合含混 | C1 |
| `schema/building_spec_v0.2.schema.json`、`research_contract.py` | 现有来源、变换、绑定、冲突与组合验证 | 第一批外置 sidecar，适配到已有字段；额外信息不绕过 strict schema | C1 不升级 schema；确需新字段另批 |
| `architect/voxelizer.py` | 原 half-up 默认、尺寸塌缩拒绝 | 后续显式 quantization policy，按构件/接口约束选择；不暗换默认 | C2/专门量化试验 |
| `architect/palette.py`、render_views | 现有受支持范围及准确限制说明 | 拟新增目标版本 registry adapter 和薄构件碰撞/预览能力 | 新能力，不能只放宽列表 |
| `architect/geometry.py`、`pipeline.py`、`revision.py` | 现有生成顺序、owner、重叠/保护区与全量回退 | 先旁路指标；第二批增加阶段产物/依赖闭包/缓存，保留全量验证模式 | C2 |
| `Scene.fingerprint()` 与旧 geometry_sha256 | 旧定义与历史比较全部保留 | 新增 occupancy_sha256（尺寸/坐标/坐标系），ownership_sha256；不更改旧哈希语义 | C1 可在外置评测报告先做 |
| 新 `research/evidence_adapter.py` 等提议文件 | 不写到现有项目，先审阅设计 | 接 packet/模型候选 → 属性决策 → ProposedSpecChange；源许可/年代外置记录 | C1 |
| 新 `evaluation/` 提议目录 | 沿用 NBT readback | 固定 case manifest、照片/相机、差分和指标；区分原始/候选状态 | C1 |
| 图片 Skill 的 SKILL.md/reference-box/podium-level-evidence | 原多向参考盒、下载、十节、校验 | 增补来源家族、年代/建成状态、属性证据入口及新案例反例 | C1 用户批准后再改并保存版本 |
| Architect Skill 的 workflow/evaluation/canton-case/podium-fusion | 两路、局部返工、四层验证边界 | 增补新的适配调用、失败回退、量化权衡与本轮练习证据 | C1 用户批准后再改 |
| V1–V5 全部输入/run | 历史代码、图片、模型、NBT、失败记录 | 只新增后续 run 与对照记录 | 本轮不启动新塔 |

## 4. P0 / P1 / P2

| 顺序 | 最小交付 | 验收 | 失败/回滚 |
|---|---|---|---|
| P0-1 环境与基线 | core/model 配置、环境 JSON、V5 manifest | 新独立环境重现 244 项；旧包哈希不变 | 用当前已验证环境；保留所有失败日志 |
| P0-2 属性证据适配 | 真实 packet → 决策 sidecar；不自动改 spec | 单位/年代/转载/同级冲突正确；来源无丢失；估计未变实测 | 保持旧研究流程，sidecar 不影响构建 |
| P0-3 固定评测 | occupancy/owner/diff/相机/输入清单 | 材质编辑占用不变；构件 ID 变化可见；NBT 精确回读 | 不改旧 hash，只撤旁路结果 |
| P1-1 候选写入现有绑定 | ProposedSpecChange + 原 guard | 旧哈希过期拒绝；参数值/证据一致；区域外零修改 | 不应用候选，原版本继续可用 |
| P1-2 净空/薄壳试验 | 房间、窄走道、格构段、开口庭院 | 轮廓预算与净空同时报告；不能用填孔换完整率 | 退回原量化或明确局部重设计 |
| P1-3 阶段与缓存 | 组件几何/材质产物 + 依赖闭包 | 缓存和冷启动输出完全一致；来源/代码/参数/框架更改正确失效 | 禁用缓存，保留全量重建；不靠缓存修正结果 |
| P1-4 目标游戏回读 | 隔离测试实例的注册表与导入证据 | 结构/分块/状态、通行、灯光、流体过关 | 不标游戏通过，不碰正式世界 |
| P2-1 可选视觉 provider | 一块立面的候选相机/深度/残差 | 许可/环境清楚；留出视角可评；失败能回退 | 不依赖 provider，继续人工/图片研究 |
| P2-2 场地/GIS 与 Studio | 独立场地适配/交互原型 | 标高/占地/道路一致；交互编辑有全状态差分 | 保留单体主线，不引入城市级依赖 |

成本判断是相对范围而非已承诺工期：P0 主要接已有字段，风险最低；P1 量化/几何/碰撞跨多个模块，风险明显更高；P2 还涉及外部数据、权重和实际运行环境，不应提前合成一个大 workflow。

## 5. 等待确认的三项选择

推荐先确认 **C1：正式接入第一批外围能力**，范围限定为依赖配置、外置证据决策、现有绑定适配、旁路评测和两份已有 Skill 的说明。保留核心 schema、NBT writer 与原几何默认行为。

**C2：组件阶段和缓存**会改变内部执行边界，应另行确认；本轮三构件实验不能作为整个引擎升级已完成的凭证。

**C3：VGGT/GIS/真实游戏 workflow**分开讨论，按资料、版本、许可和运行条件逐项启动。本轮不默认申请账号、调用付费 API 或安装新模型权重。
