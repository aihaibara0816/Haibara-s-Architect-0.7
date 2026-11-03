# ChatGPT Work 执行任务书｜GAFAcraft Architect 首轮技术落地

**请直接进入实际工作，不要仅仅复述开发方案。** 我已经确定方向，请同时阅读另外两份交接文件《01_项目目标与完整工作流》《02_已有成果与待核实资产》，以本任务书为执行指令。

## 1. 你现在的职责

担任 GAFAcraft Architect 的技术负责人和执行开发者，接管既有建筑复原 Skill 与案例资料，优先打通 **“研究数据 / BuildingSpec → 参数化方块生成 → Java NBT 导出 → 同源固定五视图 → 文件校验”** 的最小闭环；然后研究把“用户一句话或上传参考图”通过现有 Skill 接到这个闭环。项目未来部署在 `gafacraft.cn`，但本轮先完成可运行的本地原型。

用户是设计背景，不需要反复询问常见开发细节；可自主选择稳妥的 Python 技术实现。遇到影响建筑真实性、比例、正式环境安全或现有文件不可获取的关键阻碍，再集中询问。**若工具支持文件修改和测试，应实际编写、运行、交付代码；不要只提交一份长策划或空目录。**

## 2. 明确不可更改的产品决策

- 允许用户只输建筑名称、一句话或多张建筑照片，Skill 应主动研究、查证并补全，不把大量专业参数表丢给用户。
- 不让建筑生成引擎自己猜测：AI 研究和建筑决策层产生结构化、校验过的 `BuildingSpec v0.1`，Engine 只按规格执行。
- 已有研究 `packet.json` 不可粗暴覆盖或改名为 `BuildingSpec`；二者间必须有映射与来源链。
- MVP 用四个正交立面（前、后、左、右）+ 斜上 45° 的固定五视图；暂不强制实现实时可旋转的三维查看器。
- 预览必须从**同一份方块数据**生成，不能用文生图代替真实生成结果。
- 目标主要是 Minecraft Java `1.21.1` / NeoForge `21.1.244` / Create `6.0.10`，这些是历史目标版本，必须核实现时配置。
- 优先支持 Java 结构 `.nbt` 并实测 Create 的实际导入兼容性；`.schem` 可后续实现。
- 遵守用户设定比例；超出世界高度需报告，不能私自缩放。区分证实尺寸、估算、假设与游戏内适配。
- 不使用“已训练小模型”作为先决条件；优先已有模型 + Skills + 程序化引擎。
- **未经用户明确授权，不改官网线上环境、Minecraft 正式存档、正式服务器配置，不公开发布或推送到远端仓库。**

## 3. 执行顺序（请尽量在本次 Work 内实际推进）

### P0｜第一件事：资产与环境审计（短而实）

1. 找到并读取 `$gafacraft-building-reference`（记录版号 `9bac699e678baa649c4a36feb09a84444f98a979`）、`real-to-minecraft` v0.2、`GAFAcraft-building-workflow.html`、相关源文件和历史资料包。
2. 尝试运行现有比例换算、`validate_packet.py`、`selftest.py`、`tools/inspect_build.py`；若当前 Skill 不可访问，优先搜索当前项目与文件库，明确记载缺口，不假装存在。
3. 检索本地/项目/可访问仓库是否已有 NBT exporter、建筑几何生成器、预览器；避免重复开发。
4. 交付 `docs/ASSET_INVENTORY.md` 和 `docs/STATE.md`，明确已验证与未核实状态。不要让审计无限期占用开发时间。

### P1｜BuildingSpec v0.1 协议落地

创建并验证：

- `schema/building_spec.schema.json`：JSON Schema；有 schema 版本、建筑身份、来源/置信状态、坐标系、原尺寸/方块尺寸、比例、建筑组件、材质、建造参数、输出环境、待确认信息与偏差记录。
- `docs/BUILDING_SPEC.md`：字段解释、研究包 `packet.json` 到施工规范 `building_spec.json` 的映射关系，严格明确哪些字段属于事实、推断或工程设计。
- 两份最小样例：`examples/retail_store/building_spec.json`（便利店等小型建筑）与 `examples/tower_segment/building_spec.json`（简化塔楼的变截面主体，非宣称 1:1 的广州 IFC）。
- `tests/`：正向、缺少必需字段、未知尺寸、冲突比例、世界高度超界等自动化测试。

为快速验证可采用 Python JSON Schema 库或兼容实现；正式确定字段前先读取旧资料协议，尽可能保留证据 ID。真实尺寸和研究样板暂定尺寸必须分开，禁止为了通过测试编造尺寸来源。

### P2｜最小可运行建筑生成引擎

目标：从 `building_spec.json` 运行程序后，**真的**导出结构文件，而不是只输出 Prompt。

建议先建立以下清晰模块（可根据现有代码实际调整）：

```text
gafacraft-architect/
  README.md
  docs/
    ASSET_INVENTORY.md
    ARCHITECTURE.md
    BUILDING_SPEC.md
    STATE.md
  schema/building_spec.schema.json
  examples/retail_store/building_spec.json
  examples/tower_segment/building_spec.json
  architect/
    spec_loader.py
    geometry.py
    voxelizer.py
    palette.py
    export_nbt.py
    render_views.py
    validation.py
  tools/build.py
  tests/
  output/
```

最低几何能力：平面矩形/多边形建筑体块、墙体和屋面、门窗开洞、多个分层体量、玻璃/混凝土等材质映射、带高度变化的塔楼简化截面。全部组件带稳定 ID；给定相同 Spec 时可稳定重建。

真实文件交付应包含：`output/<case>/building.nbt`、`preview_front.png`、`preview_back.png`、`preview_left.png`、`preview_right.png`、`preview_iso45.png`、`building_spec.json`、`build_report.json`（含长宽高、方块数量/材质、文件哈希、检查状态），需要拆分时再加 `placement_manifest.json`。

导出格式必须通过当前可用 NBT 检查器读取回验。若已存在的 `tools/inspect_build.py` 有文件兼容性约束，则修复或使用独立新测试，不能仅将文件后缀命名为 `.nbt`。

### P3｜第一个真实可演示的端到端原型

1. 先用 **一栋简单便利店/公共小楼** 打通 BuildingSpec → NBT → 五视图 → 校验，确认外轮廓、门窗、屋顶、材料至少在图中有真实表现。
2. 再用 **塔楼变截面测试段** 验证“下收/中鼓/上收”或台阶退台，不必在第一版直接完成整栋广州 IFC；这一步检验我们的核心优势是否能表达复杂建筑。
3. 能访问多模态 AI 或已有 Skill 时，选其中一个例子尝试 **一句话 + 已有资料/照片 → `packet.json` → `BuildingSpec`**；如果当前工具不能直接调用模型，先将 Skill 输出的真实资料包/人工审核数据接入并明确 AI 环节尚待对接，不得伪称自动图片理解已实现。
4. 给出真实运行命令、测试结果、两个样例产物及其错误清单。视图与 `.nbt` 应源于相同方块结构和构建 ID / 数据哈希。
5. 如果无法运行 Minecraft，不得宣称“Create 游戏内导入已成功”；将此项列入 `pending_game_test` 和下一阶段计划。

### P4｜网站接入预研（前面完成后再做）

只审查 `gafacraft.cn` 已有站点的技术栈与是否便于新增 `/architect` 或独立子站，不改线上环境。规划：图片上传、扩写前的任务保存、异步任务队列、五视图预览、蓝图下载、文件大小限制、任务超时、资源配额、隐私与来源授权。输出简短接入说明，不抢占 P1–P3 的开发时间。

## 4. 交付清单与验收方式

本轮最低交付（若有技术限制，给出真实缺口，其他项目仍应推进）：

1. 已盘点的资产与工具状态表：有对应文件、版本和测试结果；
2. 有效的 `BuildingSpec v0.1` JSON Schema 与两份样例；
3. 可运行的建筑生成脚本、必要依赖、清晰 README；
4. 至少一个真实生成的 NBT 和五张真实方块预览；
5. 自动文件/几何检查结果；
6. 对下一轮“自然语言/图片 → Skill → Spec”和网站部署的明确接口与障碍；
7. `STATE.md`：完成、未完成、运行命令、失败测试和下一步，禁止凭描述冒充已执行。

**从 P0 立即开工，并尽快写出可运行的第一版，而不是先讨论网站 UI。** 当资料存在冲突、无法核实真实尺寸或缺少当前环境时，使用明确标记的研究样板参数继续做可行的技术验证，同时保留正式复原不可绕过的审核门槛。
