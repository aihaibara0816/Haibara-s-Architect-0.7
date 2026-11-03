# GAFAcraft Architect 0.2 — 资料、证据与局部修订

本次升级保留 0.1 几何/NBT/渲染基础，新增可变参考组、参数级证据、人工回查验证、重叠声明与局部修改守卫。没有 SU 搜索/解析、自动看图、模型训练、增量缓存或网站部署。旧档案不变；新输出单独保存。

## 运行

Python 3.12，按 requirements.txt 安装依赖。运行 `python tools/run_all_tests.py`，各组日志与汇总在 reports/v02_tests。

- `python tools/migrate_spec.py INPUT.json NEW.json`：旧 Spec 升级，保留几何指纹与实际已存在的重叠关系；不是结构承载批准。
- `python tools/build.py examples/upgrade/retail_bound.json --out output/my_retail_v02`：真实 NBT 与五视图。输出目录须不存在。
- `python tools/research_tools.py revision examples/upgrade/retail_store/building_spec.json examples/upgrade/retail_edit.json examples/upgrade/revision_request.json reports/my_revision.json`：验证可改参数、全局锁定、允许区域、保护区和实际方块差分。
- `python tools/research_tools.py review output/legacy_gafa_colonnade/building_spec.json examples/upgrade/legacy_review.json output/legacy_gafa_colonnade reports/my_review.json`：验证参考ID、构件ID、build_id、Spec哈希、PNG哈希与人工结论一致性。机位不可比不得pass，缺参考记录失败，未运行游戏不得通过。

## 协议版本

研究 Skill 的 packet 1.0 原模板/59个测试保留。1.1 新模板为 vendor/building_reference/references/packet-v1.1-template.json，selection 使用 core、detail_groups、views、coverage_requirements，详见 reference-box.md。1.1 支持历史Rxx ID和未知来源元数据；缺数据不伪造。参考数量可变；来源、查看、身份、许可和版本仍由研究者审核。字节重复可检验，近重复仍人工标注。下载器保持原字节与状态，没有替换成新的采集系统。

BuildingSpec 0.1 继续使用原Schema；0.2 使用 building_spec_v0.2.schema.json，生成源为 tools/make_schema_v02.py。先严格验证新字段，再投影到0.1完整校验，不能通过扩展绕过原尺度/环境限制。

research.models 是可选模型证据目录：模型hash、格式、来源、许可、版本与状态。checked模型要求单位与变换、锚点记录、误差及依据；程序验证矩阵均匀尺度/正交，不读取SU，不验证锚点真实性/非共线性。status=not_found保留纯图路线。

research.parameter_bindings 用 component_id + JSON pointer 指向具体参数，与 adopted_value逐项相等；证据引用可为image/fact/model，模型引用带node_id。alternatives与basis保留取舍。conflicted阻断执行；不能把未查看图或未核实事实标成observed/resolved。构件级旧provenance依然保留，不由新字段覆盖。

research.reference_set 可保留来自已验证packet 1.1的完整选图/方向/细节组记录，选择集合必须与evidence一致；不强制旧Spec已有此字段。源坐标配准与模型测量提取仍需真实工具和人工研究，协议就绪不等于融合服务已实现。

assembly.components提供角色/父ID，必须一一映射实际组件，无环；allowed_overlaps登记明确的先写/后写覆盖。reject_undeclared会在真正生成时拦截新增的未声明覆盖。report模式仅报告。这里没有自动依赖重算；after仍只表示生成顺序。

## 修改范围

revision守卫采用全量重建 + 独立参数diff + 方块state/owner diff。保持spec_id、组件ID/顺序、环境/比例/证据与结构锁定；只允许指定参数叶节点变化。参数绑定的adopted_value可同步更新，但证据引用不允许趁编辑更换。所有变化须在允许ROI并避开保护ROI，同时检查实际受影响owner在允许名单中。该机制不读取现有游戏存档，不能声称已保护真实玩家装修。

## 案例状态

- 便利店、雨棚修订、变截面测试段、旧廊柱四个Spec迁移后几何指纹不变。
- retail_v02为新引擎实际导出的便利店：3,204格、NBT和五视图。是工程样板，不是现实711复原。
- guarded_revision.json显示雨棚6格变化，区域外0，保护区域0。
- 旧廊柱人工回查只保留资料限制与unverifiable相机；状态pass_with_gaps不代表高还原度。
- 广州塔旧参考记录若没有可靠访问/看图元数据，不能凭历史选图名单自动升级为合格core；迁移保留候选与既有文字记录。

## 本次验收记录

`reports/v02_tests/summary.json`：211项全部通过，包含Architect 77项、旧图片研究59项、参考盒12项、原字节打包4项、BuildKit 28项、Inspector 31项；比原167项增加44项。日志保留实际命令与运行结果，没有Minecraft或SU实测。

`examples/canton_reference_v11/`：以广州塔原13个候选/7条旧选择做离线实际使用检验。report模式为PASS_WITH_GAPS、0错误/48缺口，19项数据保留检查通过；core/detail仍空、照片face全unknown，不能将旧模型回查镜头当成照片方向。另经`reports/canton_original_images.json`核对原包13张图片SHA全部一致，只证明原字节存在，没有替代看图。

`reports/adapter_v11_integration.json`：旧便利店packet迁移到1.1，再经显式overlay进入Spec 0.2，reference_set保留、几何指纹不变。广州塔packet仅提取研究上下文，未生成塔楼；适配器template模式的PASS仅指协议接收，报告完整度仍以report模式的48项缺口为准。

`cases/canton280_v1/`：外置旧V1的主要轮廓/格构/核心/天线参数；`reports/canton_config_regression.json`记录两版内存生成指纹与旧包相同。包内旧名v1/v2分别为V1-r1/V1-r2，都不是SU V2；部分塔冠/场地/材料常量仍未参数化，不能当作任意高度的通用广州塔引擎。

当前个人研究Skill已保存的版本见`reports/skill_release.json`；工程内vendor/building_reference为同一内容快照。real-to-minecraft仅保留工程内Skill及增加集成边界说明，本轮未将它注册为单独全局Skill。

## 文件边界

保持字节不变：原v0.1 Schema、几何量化/调色板/NBT导出/渲染/流水线/原结构验证、原BuildKit/Inspector代码、旧测试与旧输出。精确文件比对见`reports/v02_file_changes.json`。

局部升级：spec_loader按版本分流；packet_adapter接受1.1；geometry记录并检查覆盖；图片研究validate_packet按协议分流。新增research_contract、reference_review、revision及对应Schema/CLI/测试；没有把独立案例包装成已安装Skill。

交付入口为根目录`UPGRADE_REVIEW.html`。原`REVIEW.html`和非UPGRADE命名的历史文档保留为v0.1档案，不代表本次状态；根目录DELIVERY_MANIFEST.json记录本次所有文件的SHA。

## 验收与下一步

旧单测 + 新协议负例 + 原字节打包测试 + 四Spec迁移 + 实际NBT/五视图运行。当前测试覆盖结构与可计算约束；照片理解和模型真实性不能由程序担保。Minecraft/Create均待真实测试。

下一步：补一份身份和机位更明确的小店参考集，人工完成字段级约束与回查。其后才接模型文件读取/配准，以及更精细的方块表达。SU V2对照需固定高度、材质、渲染、相机、评估点与修订预算；历史Canton包内v2只是V1-r2，不能算SU实验。
