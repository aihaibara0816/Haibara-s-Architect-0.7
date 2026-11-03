# 木漏日町 · 山溪版 T07

当前交付：Komorebi09 T07，HAF 0.4 有界原创案例。J03 是已交付的上一版平地街区，保留在 runs/J03 与 review/previews/J03，旧说明见 README.md。

## 本次变化

- 场地 224 × 64 × 184（X,Y,Z），西北山顶相对 y=6 基准地面高 30 格，峰顶 y=36。
- 18 栋原有可进入建筑采用不同朝向、位置与首层标高（y=6…21），保留厨卫、床组、家具、照明、12 幅画和使用点。
- 山涧沿谷地下降并接入东侧溪流；跨溪连接、绕行圆石小路、局部石阶、路缘草径与台地挡土收边。
- 230 组云杉、3 组樱花、两片共 73 根竹子，以及 6,558 株地面草花。树冠和植物避让道路与入口；原版叶块设置 persistent，世界 randomTickSpeed=0。
- 3 处开放公共构筑物：山麓休憩亭、桥头告示候坐处、溪边洗手休息台。不计入 18 栋封闭建筑。
- 参考用户上传的松山湖截图，以台地、水系、路径和分组关系为借鉴，不复制全部建筑，不声称测绘复原。

采用自建高度场，并设置存档中的 taiga 群系标签。不是调用 Minecraft 原生种子生成；混合云杉、竹林、樱花是本次景观设计。

## 原始地形与建设分开

`runs/T07/Terrain_Input.nbt` 是建设前的地形与水系。`terrain_original.npy` / `terrain_final.npy` 保存地面高程。`plan.json` 与 `spatial_contract.json` 保存采用的落位、入口、道路标高、水体保护、公共节点和填挖明细。

目前的适配器会生成本案例地形、在候选组团内对建筑位置进行受约束扰动、形成台地和道路，然后放置已知的三类建筑模块。它尚未接受任意用户地形 NBT，尚未自动识别树冠/地表/洞穴/已有建筑，不能宣称通用自主城镇规划已经完成。

后续研究方向：导入并保存用户原始 NBT → 分离地表与保护物 → 坡度/水系/可建区域 → 候选地块与用途 → 少填挖的道路和台地 → 生成差异与预览 → 用户确认。应保留原始文件，不先清平场地。

## 复现与检查

Python 3.11+，`numpy`、`Pillow`、`nbtlib==2.0.4`。以下命令从工程根目录运行，run 名称必须是未使用的新目录：

```bash
python src/build_terrain_town.py MyTerrain --seed 1145 --layout-seed 309
python src/audit_terrain_town.py MyTerrain
python src/world_terrain_town.py MyTerrain world_MyTerrain
python src/diagram_terrain_town.py MyTerrain
```

默认 seed 管理植物和道路材料；layout-seed 管理已有候选组团内的位置扰动。地块族、用途和道路关键节点是有意设计的约束，不是所有东西都随机。不要把本案例验证解释为所有种子和所有地形都可用。源 Scene 的显式预算上限扩到 4,000,000 格；默认预算仍保持原值，以容纳此地形包围盒。

当前最终 NBT SHA-256：`03a9da770cb2462ae1d2b8e55f658eb4f54a3177679ce15173ac824795cb8149`。

检查范围：18/18 入口、285 个用途接近点、10 条室内楼梯、门框/门扇、床、画、灯具承托、地被和水岸。室外连接图允许一格变化，包含需要跳跃的可能，尚不能视为全程无跳跃通行。房屋内楼梯按近似人物体积与半格上升采样。动态流水未运行客户端验证。用户的实机否定优先于这些离线记录。

## 预览与交付

官方 Java 1.21.1 模型/材质不随包提供，来源见 assets/vanilla_source.json 与 src/fetch_vanilla_assets.py。设置 ROOM06_MC_ASSETS 为实际 assets/minecraft 目录。Linux EGL/OpenGL 3.3 环境用于离线绘制；Node.js 只用于 HTML 行为测试。

```bash
python src/render_terrain_town.py T07 overview
python src/render_terrain_town.py T07 walk
python src/render_terrain_town.py T07 B01
```

B02…B18 同样调用。分组顺序执行，共用临时 mesh。完整街景每次只绘制一张，避免在同一 EGL 进程累积大场景缓冲。最后运行 `python src/render_terrain_town.py T07 planting`，替换竹林与樱花的最终机位，自动合并到 walk_report.json 和 walk_cameras.json。overview 纹理采样上限为 2，walk 为 4，建筑近景为 10。建筑近景裁取该栋附近几何，保留该建筑天花和屋顶。四向等尺度日景、夜景、正交俯视、四向立面与人物视角均从最终 NBT 回读。樱叶保持原版固有粉色，云杉叶采用专门色值，其余生物群系色有近似。

```bash
python src/report_terrain_town.py T07 /path/Komorebi09.html /path/Komorebi09_World_1.21.1.zip
```

交付 HTML 包含 68 张本轮 NBT 预览，72 个独立内嵌图像资源（含对照图和 SVG），4 个字节一致的下载文件。离线检查覆盖 36 次逐栋视图切换、18 个地图键盘入口、4 类筛选、5 个主图切换和放大弹窗；没有执行完整浏览器或 Minecraft 客户端测试。

世界包解压后，将 Komorebi09_1.21.1 放进 Java 1.21.1 的 saves。无必需模组。世界偏移 [-112,58,-92]，出生点由实际道路标高确定，见 world_check.json。首次进入需要重算光照；地图外继续生成与接缝待实机。完整 NBT 为稀疏结构，粘贴前须清空完整范围，推荐直接用世界包。

`src/vanilla_preview.py` 补充了樱叶/云杉叶色修正。历史 J03 的生成脚本放在 history/J03/source，J03 旧图保持原有结果，不冒称本轮图。重型临时网格、缓存、游戏客户端与官方材质不打包。
