# Architect 0.3：实际模型读取

本次已经读取用户上传的广州塔 SKP 几何，并实现 SKP、GLB、glTF、OBJ、DAE、STL、PLY 的统一入口。Architect 版本为 0.3.0；既有 BuildingSpec 仍为 0.2，图片研究 packet 仍为 1.1。模型中间资产为 model-evidence-0.1。这里是工程模块，不是新安装的独立 Skill；本轮没有修改个人图片研究 Skill。

## 已实现

- 读取几何、可用场景层级、实例变换、材质基础色和来源哈希；保留原点，统一到米/Y-up/右手系。不会凭建筑名称把模型强行缩放到 600 米。
- SKP 内部几何按英寸处理，显示单位单独记录；当前上传文件的显示单位为 Millimeter，不会因此再缩小 1000 倍。
- 保留可获得的节点身份、父子关系、原名称与组件定义。SKP 使用祖先实例 GUID 路径；缺 GUID 时明确使用路径回退。通用文件的节点 ID 仅保证同一输入/同一读取器下可复现，不能声称跨格式重新导出后仍保持同一个 ID。
- 校验有限坐标、三角面索引、父子关系、单位冲突与资源引用；记录退化三角面、非等比变换和格式损失。没有悄悄修模。
- GLB/glTF 导出使用米制并保留选定层级与实例资源复用；其他导出烘焙世界变换。副产物明确说明层级/曲线/贴图是否保留。
- 产出真实几何三视图，不是生成式效果图。预览使用中性材质，不能用于验收原模型贴图、透明度或光照。
- 输出与既有 BuildingSpec 0.2 相容的 candidate 模型证据。attach 不改任何可执行构件参数，也不把模型升级成 checked。

## 支持范围与评级

评级 B 表示已经实际实现并通过本轮测试，但仍需要更多独立来源文件；不代表任意该格式文件都能无损读取。

| 格式 | 当前入口与实测 | 保留与限制 | 评级 |
|---|---|---|---|
| SKP | OpenSKP 1.3.0；实际上传的 21.0.0 文件与生成的单位/实例夹具 | 几何、层级、实例、GUID、曲线和来源纹理哈希；未与 SketchUp 官方 SDK 输出做独立一致性对照；隐藏面和保存场景可见性尚未复现 | B |
| GLB / glTF 2.0 | Trimesh 5.1.1；广州塔派生文件与嵌套/镜像实例夹具 | 保留变换和可用图结构；仅静态三角网格；动画、骨骼、形态键、必需扩展会明确拒绝 | B |
| OBJ | 同上；广州塔派生文件与夹具 | 需调用者声明单位、上轴；分组取决于源文件，层级可能已丢失；材质仅预览近似 | B |
| DAE | pycollada 0.9.3；广州塔派生文件与独立毫米/Z-up/嵌套位移夹具 | 自动应用 asset 单位/上轴及节点矩阵；当前要求三角面；非三角多边形明确要求先三角化；不保证材质贴图 | B |
| STL / PLY | Trimesh；广州塔派生文件与夹具 | 需声明单位与上轴；只有网格也可读取，不能从中恢复缺失的建筑构件层级 | B |
| FBX / STEP / IFC / 3DM / USD | 本轮未实现 | 当前明确报 unsupported，不能通过改后缀绕过；后续用真实样本增加独立适配器 | D |

六种通用格式的广州塔实测是“同一 SKP 读取后导出、再读取”的往返测试，不是六套独立软件的导出兼容性测试。逐面比对采用 1 mm 顶点各轴容差，不比较贴图、法线朝向、曲线和建筑真实性。原作者直接提供的 GLB/OBJ/DAE 等文件仍应作为下一轮样本。

## 广州塔样本发现

原文件 SHA-256：`26d4ca7237b4d3e870b421ba3260412d8e215d63e335beb559e48a4927c3fa72`。原件保留为 `cases/canton280_model/source.skp`，没有修改上传文件。

解析得到 13 个组件定义、54 个场景节点、19 项源材质。三角化/实例展开后为 19,844 个三角面（按读取器输出计数，不能等同于独立建筑表面或方块数）。55 个材质子网格资源、140 条独立曲线资源写入模型资产。

整场景含 Google Earth Terrain / Snapshot，网格包围盒约 491.331 × 601.856 × 423.070 m。显式选择剩余塔体组后约为 77.724 × 601.856 × 65.089 m，共 19,588 个三角面。选择依据、包含/排除节点和原哈希均写在 `cases/canton280_model/selection.json`；完整场景仍保留。这是本轮人工检查后的案例选择，不是自动识别地形或塔体的算法。

发现 5 个节点含非等比局部变换，49 个资源三角面退化。模型网格高度范围不是恰好 600 m，且原点/地面/尖顶端点尚未与照片配准；本轮保留它们，不推测误差来源或自动修正。许多节点名称是 Component/Group，尚未确认每个子节点分别代表外框架、内核、塔冠等。

原始 loose curves 已保留在 geometry.npz / model_document.json；六种网格导出不包含这些曲线。图中不显示曲线不等于把它们误当成已体素化的钢构件。

## 文件入口

- `architect/model_io.py`：读取、统一坐标、检查、存取资产、导出和候选证据接入。
- `architect/model_compare.py`：不依赖面排列顺序的逐三角面顶点匹配。
- `architect/model_preview.py`：从实际网格生成三视图。
- `tools/model_research.py`：import / export / preview / attach。
- `output/model_canton_skp/model_document.json`、`geometry.npz`：真实模型资产。
- `output/model_canton_skp/canton_full.glb`、`canton_tower.glb`：米制完整场景/塔体网格。
- `output/model_format_trials/`：GLB、glTF、OBJ、DAE、STL、PLY 文件和每项读取记录。
- `reports/model_format_roundtrip.json`：真实广州塔往返逐面比较结果。
- `reports/v03_tests/`：本次全套测试；`reports/v02_tests/` 保持上轮记录。

## 运行

Python 3.12。在独立虚拟环境安装 `python -m pip install -r requirements-models.txt`。模型库为可选依赖；已有几何引擎仍保留原入口。安装后模型处理不需要云转换服务或付费生成接口。

```bash
python tools/model_research.py import cases/canton280_model/source.skp --model-id model-canton --out output/my_canton --preview
python tools/model_research.py import path/to/building.obj --metres-per-unit 0.001 --up Z --out output/my_obj
python tools/model_research.py import path/to/building.glb --out output/my_glb
python tools/model_research.py export output/my_canton output/my_canton.glb
python tools/model_research.py preview output/model_canton_skp output/my_tower.png --root node-18c3dccd26dbb06cada8
python tools/run_all_tests.py
```

OBJ/STL/PLY 的 0.001/Z 只是“文件由毫米/Z-up 软件导出”的例子，必须依据实际导出设置填写。GLB/glTF 采用协议的米/Y-up；DAE 使用文件元数据；冲突不自动猜测。preview 中 LOCAL -Z / +X 是模型轴向，不是广州塔地理前后。

已有同一建筑的 Spec 0.2 后可使用 `python tools/model_research.py attach ASSET_DIR SPEC.json NEW_SPEC.json`。它只追加 candidate，不会执行模型参数。当前广州塔 V1 仍是专用案例程序，尚无经过审核的同建筑通用 Spec；本轮只交付 `model_candidate.json`，不把它冒充可建造 Spec。attach 的保留行为通过合成夹具测试。

## 下一步

先在 SketchUp 或另一可靠软件中导出同一模型的 GLB/DAE，比较米制尺寸、世界变换、隐藏对象和主要构件，以独立验证原生读取器；再标注塔体的地面、腰部、冠部与天线端点，建立真实照片/模型锚点。没有配准依据时 candidate 保持原状。

之后才把原作者的组件映射到 Architect 稳定组件 ID，逐参数比较图片与模型，保留冲突和采用理由，再开展 280 格的 V2。此次没有广州塔 Minecraft V2、模型体素化或游戏内测试。

## 依赖与资料

- OpenSKP 1.3.0，MIT：https://github.com/iamahsanmehmood/openskp 。本轮使用其解析与场景 API；未使用其默认毫米 GLB 导出器，使用本工程的米制导出。
- Trimesh 5.1.1，MIT：https://trimesh.org/trimesh.exchange.load.html 。本轮导出/读取结果已实际核对。
- pycollada 0.9.3，BSD：https://pycollada.github.io/ 。当前 NumPy 2.5 下存在上游弃用提示，测试通过；版本已锁定，不屏蔽测试日志。
- SketchUp C API（内部单位说明）：https://extensions.sketchup.com/developers/sketchup_c_api/sketchup/index.html 。官方 SDK 未在本次环境运行。

本轮未从零重写文件解析库；复用开源读取器，新增本项目需要的统一单位、来源、层级、局部选取、校验和证据边界。OpenSKP 的解析成功不能替代现实建筑的证据审核。
