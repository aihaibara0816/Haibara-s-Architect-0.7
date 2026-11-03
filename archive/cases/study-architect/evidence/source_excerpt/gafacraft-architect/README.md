# GAFAcraft Architect v0.2

本次升级与命令见 [docs/UPGRADE_0.2.md](docs/UPGRADE_0.2.md)。当前全套测试入口为 `python tools/run_all_tests.py`；旧版说明保留下文作基线记录。新版审阅入口为 `UPGRADE_REVIEW.html`。

---

# GAFAcraft Architect v0.1

本地可运行的建筑技术原型：**研究包 + 显式施工参数 → BuildingSpec → 方块 → Java 结构 NBT → 从 NBT 读回的五视图 → 静态验收**。

本轮交付真实源码和已生成文件。没有模型权重、没有后台训练，也没有自动图片识别服务。官网、正式服务器和正式存档未修改。

## 先看结果

打开 `REVIEW.html`：离线查看全部案例、五个视角、报告和下载 NBT。不需要安装 Minecraft 或运行服务器。

| 案例 | 输出目录 | 包围盒 X×Y×Z | 非空气方块 | 性质 |
|---|---|---|---|---|
| 单层便利店 | `output/retail_store/` | 34×12×26 | 3,204 | 原创工程样板，不是找回的711 |
| 变截面塔楼 | `output/tower_segment/` | 32×76×30 | 6,556 | 结构测试段，无完整垂直交通 |
| 便利店雨棚修改 | `output/retail_store_revision/` | 34×12×26 | 3,210 | 雨棚延长1格，区域外变化0 |
| 历史廊柱资料接入 | `output/legacy_gafa_colonnade/` | 22×20×34 | 见构建报告 | 旧照片 + 旧假设参数，重新表达为通用构件 |

每个目录包含 `building.nbt`、前后左右和斜上45° PNG、完整 Spec、哈希与静态检查报告、方块清单及放置记录。PNG 来自导出的 NBT，不是文生图。透明玻璃用不透明示意色显示；没有游戏材质、发光模拟或物理模拟。

## 运行

已在 Python 3.12.14 / Linux 上执行。建议 Python 3.11 或 3.12；不需要 GPU、API Key 或联网模型。

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell 改用：.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tools/run_tests.py
python tools/build.py examples/retail_store/building_spec.json --out output/my_store_v1
python tools/build.py examples/tower_segment/building_spec.json --out output/my_tower_v1
```

`requirements-tested.txt` 记录本次测试环境的精确版本。字体在不同系统上的回退会改变 PNG 字节；NBT 与方块哈希不受字体影响。交付文件自身的哈希可以跨系统验证；同一运行环境下再次渲染应保持一致。

输出目录必须是新路径；已有目录会被拒绝，不覆盖历史版本。引擎不会把模型放进世界。

## 接入研究资料

```bash
python tools/adapt_packet.py examples/retail_store/packet.json --overlay examples/retail_store/construction_overlay.json --out output/adapted_spec.json
python tools/build.py output/adapted_spec.json --out output/from_packet_v1
```

没有 `--overlay` 时只得到 `research_context`，不会猜出构件尺寸或位置。原 `packet.json` 不改名、不覆盖；证据原 ID、来源、状态与文件 SHA-256 均保留。已有广美照片资料在 `examples/legacy_gafa_research/`，具体映射见 `docs/BUILDING_SPEC.md`。

复现局部编辑：`python tools/revise_canopy.py --out output/my_canopy_v2`。脚本保持其他构件参数，读取前后两个 NBT 做区域差分。它仍然完整重建，不是内部增量计算。

## 验收与限制

`reports/tests_final.json` 是新引擎测试结果；`reports/audit_*.txt` 是118项继承测试及旧工具运行记录。`docs/TEST_REPORT.md` 列出实际失败、修复和未测试项。

本轮仅支持明确允许的原版整立方体材质；楼梯、半砖、栅栏、模组方块、实体及方块实体尚未接入新引擎。原 BuildKit 的实现仍完整保存在 `vendor/buildkit_v03/`。新引擎用有限原语取代案例专用生成逻辑，但不意味着已覆盖旧样板全部细节。

`Minecraft 1.21.1 / NeoForge 21.1.244 / Create 6.0.10` 是历史目标配置。当前没有可运行的 Minecraft 环境，全部输出标记 `pending_game_test`。NBT 使用显式空气，会影响包围盒内空气位置；后续只在空白测试区做导入与放置验证。

下一轮优先级：测试世界实际导入 → 从图片/文字提取可追溯几何约束 → 构件组合模板与局部编辑 → 网站异步任务接口。详见 `docs/STATE.md`、`docs/NEXT_STEPS.md` 和 `docs/WEB_INTEGRATION.md`。
