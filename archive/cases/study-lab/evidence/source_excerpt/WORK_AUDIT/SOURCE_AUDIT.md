# 源码级开源比较

审计日期 2026-10-21。全部仓库通过 GitHub 元数据/文件接口核对，不只依据 README。具体文件及 blob SHA 共 60 条见 `evidence/source_index.json`。只对选择的模块作结论，不宣称审完任一完整大型仓库。

## 1. 固定版本

| 项目 | 实际分支 | 本次提交 | 主许可/采用结论 |
|---|---|---|---|
| [PlanCraft](https://github.com/GaborWnuk/PlanCraft) | main | b0746140cf378d7e03b16887ef64ff9d99991f86 | 代码 MIT；小范围代码复用 |
| [Arnis](https://github.com/louis-e/arnis) | main | a889f68637a18b540816fc41007a7972f7d547b4 | Apache-2.0；算法思想移植，GIS 后续独立进程 |
| [ObjToSchematic](https://github.com/LucasDower/ObjToSchematic) | ots-1.0 | b611b52c7a87cad99127908598bab019fe9e7c3f | BSD-3-Clause；分阶段/薄壳思路，暂不整包接入 |
| [threed2vox](https://github.com/skairunner/threed2vox) | master | 46262ae1bc4ce8bf31c4253b0c0e9def605a6d29 | 公开树未见许可证；只读参考 |
| [Minecraft Blueprint Generator](https://github.com/aaaditt/minecraft-schematic-maker) | main | 57827ecaed8f8d730c8b220651590d4045f79f4e | 公开树未见许可证；只读交互参考 |
| [VGGT](https://github.com/facebookresearch/vggt) | main | a288dd0f14786c93483e45524328726ab7b1b4ce | 自定义 Meta 许可，checkpoint 分开；可选 provider 待验证 |
| [VGGT-Ω](https://github.com/facebookresearch/vggt-omega) | main | 48b23c8ce72c9a8fcf987f0d7f43d8e4870759f6 | FAIR Noncommercial Research；暂缓默认接入 |

“有公开源码”不等于能把代码、图片、图标、权重和数据一起按同一许可打包。以下是文件中可观察的许可条件，不代替正式发布前的逐项许可核验。

## 2. PlanCraft：最容易落地的局部借鉴

固定源码：

- [model.py](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/tools/building/building/model.py)：厘米制、Warp/Frame、墙/开口/房间/屋面/楼梯等部件。
- [validate.py](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/tools/building/building/validate.py)：方块状态、门床配对、净空与 flood-fill 通行。
- [buildpaste.py](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/tools/building/building/buildpaste.py)：网格到 BuildPaste JSON、方向和回读比较。
- [review.py](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/tools/building/building/review.py)、[backend guide](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/docs/buildpaste.md)：新测试世界、游戏端回读、相机与渲染距离。
- [.github/skills/real-building/SKILL.md](https://github.com/GaborWnuk/PlanCraft/blob/b0746140cf378d7e03b16887ef64ff9d99991f86/.github/skills/real-building/SKILL.md)：研究/建模工作说明，不是自动视觉训练器。

`source-observed`：模型由已整理的 YAML 参数编译，按 parts 顺序写入 Grid，后写覆盖前写。默认 ceil 将墙面/薄隔墙/标高作为断点，用约束分配格数，再做分段插值。round 保持统一网格。默认 `ceil_tol=0.1`、小间隙折叠等使其不是“任何尺度绝不缩小”的数学保证。Grid 使用 `uint16` 调色板索引，便于状态批量操作，但没有我们的逐单元构件所有权契约。

`verified`：直接运行未改动上游测试，34 通过、2 因缺 `26.1.2/minecraft-server.jar` 和生成的 blocks.json 受阻。未伪造注册表、未跳过后宣称全通过。另编译合成房屋，实测量化取舍，并通过现有 NBT writer/reader 导出读回。结果见 `experiments/run01/quantization_bridge.json`。

采用：保留 MIT 作者和许可；先复用/适配明确的尺寸、开口、净空机制。交付包中的上游 Python 编译器是未改动快照，并非我们的原创引擎。不要直接复用它的整个部署流程：当前后端支持 26.1.2/26.2 的 Fabric/NeoForge，默认游戏审查为 Fabric 26.1.2，Java 25；不等于已适配用户历史 1.21.1/NeoForge/Create 环境。

局限：方块碰撞是启发式，某些门默认视为可通行；材质变体可能依赖真实注册表；`IGNORED_PROPERTIES` 包括部分水/默认状态，不能覆盖我们的流体验收需求。整栋采用轴向变形会影响外形和场地接口。root README 明确图标另属 CC BY-NC-ND，随包不纳入图标和游戏纹理。

最小下一实验：1:1 教学楼/便利店内室与窄走道，同一外边界下比较轮廓保真、净空优先和局部调整；外边界越界、两格净高失败、入口断开或注册表不符即失败。

## 3. Arnis：先学习数据取舍和失败处理

固定源码：

- [overture/mod.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/overture/mod.rs)：`HeightHints` 仅在 OSM 同时缺 height 与 building:levels 时补充，保留来源，不覆盖已有垂直标签。
- [models_3d/pipeline.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/models_3d/pipeline.rs)：3DMR → Wikidata → 自定义构造，累计已认领对象集合，避免同一地物重复生成。
- [mapillary/facade.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/mapillary/facade.rs)：墙面候选、视距/入射角过滤、同一采样点的多视图颜色中位数。
- [mapillary/plane.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/mapillary/plane.rs)：确定性方向网格/投影带搜索、两轮总最小二乘、内点数及角度拒绝门槛。
- [mapillary/confidence.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/mapillary/confidence.rs)：分项质量因子、几何平均及覆盖率上限；它是工程评分，不能直接当建筑真实性概率。
- [mapillary/cache.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/mapillary/cache.rs)：图像 ID、墙 node IDs/piece、参数摘要、算法 EPOCH；失败结果也缓存。
- [floodfill_cache.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/floodfill_cache.rs)：位图坐标集合、共享引用、最后使用后释放。
- [models_3d/voxelize.rs](https://github.com/louis-e/arnis/blob/a889f68637a18b540816fc41007a7972f7d547b4/src/models_3d/voxelize.rs)：glTF 三角形、DDA 采样、覆盖率/材质处理；另有闭合网格竖向交点配对的实体填充入口。

`source-observed`：源码中有上述实现与测试函数；本轮没有执行 Rust 工程/整城生成。Cargo 版本字段为 3.3.0，但以本次 commit 作为审计版本。

关键适用边界：普通竖直墙面和地物轮廓的先验不能直接适用于广州塔斜框架、内外双层及曲面。`voxelize_solid_triangles` 对闭合表面填实体，与需要保留塔体空洞的目标可能冲突；不默认选用。墙面算法中“同一注册场景”的限制值得保留，跨场景的点云不可直接拼角点。EPOCH 是缓存算法版本，不是建筑建成年代；两者在我们的记录中需要独立字段。

新发现：plane.rs 提到的 `tools/facade_lab/plane.py` 和 confidence.py 不存在于本次公开树，实际文件访问为 404。Rust 文件和 golden 目录存在，但不能把注释中的研究脚本当成交付工具。

采用：算法思想移植。我们的 `lab/evidence.py`、`stage_cache.py` 是独立小实现，未复制 Rust 代码。缓存原型已实际写盘、命中、失效和校验损坏，并验证局部结果等于全量；不是 Arnis 性能基准，也不是完整通用依赖调度器。GIS/街景外部服务与用户资料本轮未调用。

最小下一实验：同年代、已知坐标的平直立面，至少 3 个不同拍摄来源，含移动遮挡；另测只有 1 个视角、固定树木遮挡、低内点支持和错误年代。失败应回退并报告原因；不得凭颜色融合推断隐藏空间。校园试验应单独核对 OSM/Overture/Mapillary 数据许可与署名。

## 4. ObjToSchematic 1.0：用于检验体素质量和阶段边界

固定源码：[带厚度 BVH 光线体素器](https://github.com/LucasDower/ObjToSchematic/blob/b611b52c7a87cad99127908598bab019fe9e7c3f/src/voxelisers/bvh-ray-voxeliser-plus-thickness.ts)、[法向修正体素器](https://github.com/LucasDower/ObjToSchematic/blob/b611b52c7a87cad99127908598bab019fe9e7c3f/src/voxelisers/normal-corrected-ray-voxeliser.ts)、[block_mesh.ts](https://github.com/LucasDower/ObjToSchematic/blob/b611b52c7a87cad99127908598bab019fe9e7c3f/src/block_mesh.ts)、[worker_client.ts](https://github.com/LucasDower/ObjToSchematic/blob/b611b52c7a87cad99127908598bab019fe9e7c3f/src/worker_client.ts)。

`source-observed`：选定轴缩放；构建三角形 BVH；沿三个主轴发射光线取得表面交点；带厚度版本沿三角形法向偏移半格补点。之后根据纹理/颜色和方块调色板选材，可做有序/随机抖动、可见面颜色和下落方块处理。导入、体素化、方块指派在 worker 中分阶段。

有用之处是阶段分离和表面覆盖，不能把它理解为“识别建筑构件”。加厚能减少细表面断裂，也可能并拢相邻栏杆、填掉窄缝；法向反向和非封闭网格须单测。原始材质 RGB 也不能替代玻璃、金属、结构柱的语义。

采用：先思想移植，未来可做独立进程基准。BSD-3-Clause 需要保留许可/署名与非背书条款。Node >=16.8、TypeScript、bvh-tree、纹理/调色板等依赖需要固定。本轮未安装运行其完整 Node 构建链，所以 BVH/薄壳在我们的场景仍 `not_tested`；缓存实验只验证阶段分离，不代称其体素器已通过。

最小下一实验：空心盒、开口庭院、两根近距细杆、倾斜薄片、格构塔一段；统一尺度/调色板，比较占用、空洞连通、最小缝宽、表面缺失、耗时和内存。若以降低断裂为代价封闭必要空洞，不通过。

## 5. threed2vox：概念参考，不复制代码

核查 [Cargo.toml](https://github.com/skairunner/threed2vox/blob/46262ae1bc4ce8bf31c4253b0c0e9def605a6d29/Cargo.toml)、[src/lib.rs](https://github.com/skairunner/threed2vox/blob/46262ae1bc4ce8bf31c4253b0c0e9def605a6d29/src/lib.rs)、[nbtifier.rs](https://github.com/skairunner/threed2vox/blob/46262ae1bc4ce8bf31c4253b0c0e9def605a6d29/src/nbtifier.rs) 与 README。

`source-observed`：Rust 0.1.0 工程；OBJ/STL/DAE/glTF/GLB 输入，缩放/旋转，体素与三角网格碰撞检测，顺序或多线程执行，schem/structure 输出。CLI 与固定尺度设计值得参考；它不解决照片语义、材质融合和证据决策。

完整 34 条提交树未见 LICENSE/COPYING/NOTICE，Cargo.toml 也无 license 字段。本轮只读取，交付不包含其源码、不运行、不采用。许可证澄清后，再按薄壳夹具与 NBT 目标版本测试；README 的旧示例与“1.13+”不能证明 1.21.1/Create 兼容。

## 6. Minecraft Blueprint Generator：交互可借鉴，生成路径不宜照搬

核查 [route.ts](https://github.com/aaaditt/minecraft-schematic-maker/blob/57827ecaed8f8d730c8b220651590d4045f79f4e/src/app/api/generate/route.ts)、[VoxelRenderer.tsx](https://github.com/aaaditt/minecraft-schematic-maker/blob/57827ecaed8f8d730c8b220651590d4045f79f4e/src/components/VoxelRenderer.tsx)、package.json 和 NBT 编码文件。

`source-observed`：图像发送给 Anthropic API，返回方块 JSON；现有建筑编辑上下文只取前 50 个方块样本，未知方块回退到颜色匹配；前端有实例化绘制和高度切片。它并未实现我们的 BuildingSpec、几何证据绑定或完整局部修改守卫。README 的 FPS 宣称本轮未测。

完整 634 条公开树未见明确许可证，package.json 无 license。只借鉴图层、切片、反馈入口，不复制/打包源码。本轮未调用付费 API。若将来实现自有界面，必须回放全部构件参数或明确差分，验证区域外零修改，而不是只向模型发送大建筑的前 50 个方块。

## 7. VGGT / VGGT-Ω：辅助资料，不是建造引擎

核查 VGGT 的 [models/vggt.py](https://github.com/facebookresearch/vggt/blob/a288dd0f14786c93483e45524328726ab7b1b4ce/vggt/models/vggt.py)、[pose_enc.py](https://github.com/facebookresearch/vggt/blob/a288dd0f14786c93483e45524328726ab7b1b4ce/vggt/utils/pose_enc.py)、demo_colmap.py、README、LICENSE.txt；以及 Ω 的 [vggt_omega.py](https://github.com/facebookresearch/vggt-omega/blob/48b23c8ce72c9a8fcf987f0d7f43d8e4870759f6/vggt_omega/models/vggt_omega.py)、dense_head.py、pose_enc.py、README、LICENSE。

`source-observed`：VGGT 有相机、点图、深度和跟踪头；Ω 的当前最小推理模型提供相机与深度/置信分数。输出需要从相机约定转换到本地坐标，结合已知尺度/锚点、遮挡及残差核查。没有这些环节不能当测绘真值。深度 confidence 不等于“这个构件百分之几真实”。

许可分开记录：VGGT README 明确代码许可已更新；原 checkpoint 仍为非商业，单独的 Commercial checkpoint 需申请并遵守对应条款。Ω 的仓库 LICENSE 是 FAIR Noncommercial Research，权重需要访问申请。默认实验不下载/打包权重，也不把“源码可见”写成“无限制可商用”。

`not_tested/blocked`：本环境未安装 torch、未准备权重，未发现 nvidia-smi；实际可用 GPU/显存待核实。未运行推理或训练。官网 A100 运行表是作者测试条件，不能当本地可达性能。

采用：VGGT 后续可选外部 provider；Ω 暂缓默认接入。CPU 锚点相似变换原型已通过 5 项测试，但它需要明确 3D 对应点，不是视觉模型替身。下一实验应使用许可清楚、同年代、存在重叠区域的局部照片，分开拟合锚点与留出锚点，对比人工/几何基线。若多视图残差、尺度或反射玻璃区域不稳定，应输出待核实并保留纯图片研究路径。
