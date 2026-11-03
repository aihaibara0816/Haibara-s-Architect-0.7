# HAFusion 0.1 — 广州塔 V6_r02

在保留 HA0.3 与广州塔 V5 的基础上，将已研究的开源机制接入独立本地工程。
当前交付是工程测试版与一个真实建筑案例，不是已安装的新 Skill、通用自动重建器或已训练视觉模型。

## 从这里开始

- `deliverables/HAFusion_V5_V6_对照与反馈.html`：9 组同相机对照、精确剖面、验证、来源与反馈导出。
- `runs/V6_r02/GAFAcraft_Canton280_V6.nbt`：最终建筑；SHA256 `a186747e423754ca2edccfbac2536ac3b02086c376d6b55c901b5309d2419afe`。
- `runs/V6_r02/modules/`：9 个互不重叠的分块，与完整 NBT 二选一。
- `runs/V6_r02/placement_manifest.json`、`materials.json`：放置偏移和材料。
- `reports/comparison_metrics.json`、`replay_validation.json`：公平对照与实际冷/热缓存结果。
- `preserved_originals/`：交付 ZIP 内保存 V5 与 HA0.3 的原始 ZIP 字节，未重打包其内容。

## 复跑

在独立 Python 3.12 环境安装 `requirements-core.lock.txt`；V6 使用原 SKP 的已校验归一化资产，不要求再次解析 SKP。

```bash
python -m pip install -r requirements-core.lock.txt
python tools/build.py --run V6_my_replay
python -m unittest discover -s tests -v
```

输出写入新 `runs/`，同名 run 会拒绝覆盖。首次构建约 25 秒是本次机器上的一次记录；后续耗时因环境而异。NBT 字节应等于上面哈希。
`requirements-model-optional.txt` 仅列出原 HA0.3 可选读模依赖，本轮未复跑原始格式导入，不能将其与 core 配置盲目混装。

## 渲染与评审

```bash
python tools/export_preview.py V6 runs/V6_r02 GAFAcraft_Canton280_V6.nbt
python tools/render_egl.py V6 configs/comparison_views.json
python tools/package_review.py
```

渲染需 Linux Mesa EGL/OpenGL 与 `libEGL.so.1`，不需外部模型 API。图片从最终 NBT 回读，显示半砖、墙和铁栏杆的示意方块形状；玻璃与灯光是近似，不能替代 Minecraft。
Windows 可先使用随包图像与报告；原 case/views 的浏览器渲染器也保留，但其历史 V5 入口不能直接当 V6 入口。
`package_review.py` 依赖已保存的 V5 / V6 预览和本轮验证记录；它只重建报告，不重新生成建筑。

## 实际融合边界

1. **PlanCraft 原代码（MIT）**：Grid、reachable、block-pair 检查直接执行于最终 NBT 的地面/平台测试区域。6 个目标两版都可达。为适配独立岛状场地，测试添加首层标高的外部地坪，它不写入输出。原 house compiler 另作 318 单元桥接验证，未用作整塔生成器。
2. **Arnis 机制借鉴**：来源/版本参与缓存键，失败保持可诊断，证据候选与取舍独立记录。代码为本项目独立实现；没有复制整个 Rust 引擎、GIS 或街景处理器。
3. **ObjToSchematic 机制借鉴**：几何产物、材质替换分阶段，材质不得悄悄改变方块形状。21 个实际缓存阶段可复用；几何依赖保守，修改布局会使多个几何阶段失效，不是任意构件都只重算自身。
4. **HA0.3 与 BuildKit 原内核**：已有参数契约、导出和独立读回继续使用。`hafusion/evidence.py` 的 BuildingSpec 适配器通过原 schema 测试；广州塔走独立案例适配器，未宣称已有 BuildingSpec 可以执行任意网格。

VGGT/Ω、自动照片相机、自动构件分割、实景尺寸测量、游戏施工均未接入。
源码来源、许可证、固定 commit 和复用方式见 `ATTRIBUTION.md`；之前的研究报告在 `research_archive/`，其中历史状态和测试数不代表本轮新增执行。

## V6 的几何决定

塔高 280、整体 128×282×232、1F 以上范围、外柱/斜撑占用坐标、塔冠、天线与广场保留。
旧核心筒中心 `[28.5,28.5]` 移至塔局部 `[29.5,26.5]`，保留半径和 3×3 竖井。
这是 ±3 格候选中避免规划环梁/外框架同格冲突的最小整数位移，状态始终为 **estimated**，不是测绘位置。
核心灯位、竖井和首层入口跟随核心；梁柱邻接方块状态重新计算。

按相同规划路径与最终 NBT 检查：V5 有 20 个缺失单元、120 个与核心同格的单元；V6 均为 0。
这是最终读回口径，与历史 V4 生成中间态的 122 个 contacts 计数不同；原记录未更改。
环梁路径可与柱/斜撑共用节点；零同格冲突不保证全周一格净空，也不等于独立环网格或结构工程验算。
46 道等距水平环仍是旧近似，未解决真实变间距与倾角；核心轴线和广场尺度仍待校准。

V6 共 118,930 非空气单元、370 个实际发光块。V5 为 118,566 / 354。
增加灯数来自核心轴线调整后原逻辑灯位随动，不能据此宣称照度更好。

## 验证与反馈

- 最终 16 项文件/几何检查通过，9 分块精确拼回。
- HAFusion 10 项测试；原 HA0.3 核心 49 项与升级 28 项通过；本轮未重跑全部原始模型格式套件。
- 热缓存 21/21 命中、零几何阶段重建；全新缓存重建 NBT 字节相同。
- 玻璃材料测试复用所有几何，纯占用和归属哈希不变。广泛替换灰色混凝土触及冻结广场的失败 run 保留，守卫确实阻止通过。
- `V6_r01` 留下灯位仍使用旧绝对坐标的诊断；`V6_r02` 修正为核心相对灯位。最终交付只取 r02。
- `reports/original_integrity.json` 复核 639 个既有文件未改；`working_dependency_integrity.json` 复核工作副本中的原依赖文件也未改。
- 工程包重新解开后，从空缓存独立生成 V6，最终 NBT 字节哈希相同；见 `reports/portable_replay.json`。首次打包的缓存过滤误排除 `cache.py`，已修正并通过解包复跑。

报告反馈入口导出带 NBT 哈希的 JSON；下一轮按 component_id、view_id、observed、expected 审阅。不会自动修改建筑或正式世界。
游戏注册、碰撞、通行、水和光仍 pending。整体高度 282；若世界最高 Y 排他上界 320，原点 Y≤38，另需检查下界。
稀疏 NBT 不会清除 V5 旧块，应在净空区导入。完整文件约 352 KiB，若导入器限制 256 KiB，使用分块。
