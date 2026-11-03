# Haibara’s Architect · Open Source Lab R0.3

这是研究交付包，不是安装包，不自动改现有 Skill、BuildingSpec、工程或世界。先阅读 FINAL_RESEARCH_REPORT.md，再查看 SOURCE_AUDIT、ALPHA_0_1_PLAN 和真实日志。

## 目录

- 七份中文研究报告：研究结论、源码对比、已有能力、自动/人工边界、接入方案、测试协议、决策记录。
- `lab/`：本轮独立编写的属性证据、缓存和锚点原型、测试及可重跑实验。
- `upstream/PlanCraft/`：固定提交的未改动 Python 工具与测试、所需 BlockTable、许可/说明；不含图标、游戏纹理、安装 Skill 或游戏模组。
- `baselines/architect-v03/`：从用户既有包原样复制的最小 NBT 桥接运行模块，**不是完整 Architect 发布包**。
- `experiments/run01/`：本轮真实 JSON 结果、小房屋网格/NBT。它是互通夹具，不是新广州塔。
- `logs/`：244 项已有回归、RTM 7 项、PlanCraft 34 通过/2 阻塞、Lab 21 项的实际记录。
- `evidence/`：仓库/文件索引、输入校验、V5 记录和来源摘要。
- `manifest.sha256`：本目录所有交付文件（不含此清单自身）的 SHA-256。

## 本地复跑

从本目录运行，建议 Python 3.12。在单独虚拟环境安装 `requirements-lab.txt`。新输出目录必须不存在。

```bash
python -m unittest discover -s lab -p test_lab.py -v
python lab/run_experiments.py --out results/replay01
```

第二条执行属性/缓存/锚点和 PlanCraft → 既有 NBT 的小实验。本包不重复携带 89 MB 的 V5 原归档；未提供 V5 时会明确记录 not_tested。要复核 V5，将其原包解压到另一目录并加：

```bash
python lab/run_experiments.py --out results/replay_with_v5 --v5 /absolute/path/canton-v5
```

上游 PlanCraft 原测试：

```bash
PYTHONPATH=upstream/PlanCraft/tools/building python -m pytest -q -p no:cacheprovider upstream/PlanCraft/tools/building/tests
```

当前机器结果为 34 passed、2 failed；两个失败均在原版注册表路径缺少 `minecraft-server.jar`。完整通过需要其对应游戏数据生成环境，不应伪造 blocks.json。其测试中模拟的 world 文件只在临时目录使用，不能算真实游戏验证。

完整 Architect 回归必须使用原研究包中的完整工程，不能对本包最小 NBT runtime 执行全套测试：

```bash
python tools/run_all_tests.py --out /absolute/new/test/logs
```

实际通过的模型依赖详见 `logs/architect_environment.json`；新的模型测试配置见 `requirements-model-replay.txt`，该文件是本轮观察的配置，不是已替换正式依赖。不要把原 requirements-tested 和 requirements-models 的不同 numpy 固定值无条件一起安装。

## 实验边界

- Evidence：来源家族/年代/状态已由调用者填写；不自动识别图片转载、检查原图许可或推断真值。source_order 是显式策略，不是训练得到的概率。
- Alignment：只拟合已知 3D 对应点。没有 2D 特征检测、相机内参求解或真实照片配准。
- Cache：单进程小型示例；算法版本由调用者显式传入，无通用 DAG 求解、代码自动指纹、多进程锁、磁盘配额、LRU 或生产调度。只证明已测闭包行为。
- PlanCraft 桥接：保留格点和方块状态，不保留上游缺失的逐单元构件身份；示例只有一个 owner；没有扩展 BuildingSpec 几何。
- 没有 Minecraft/NeoForge/Create 实测、没有 VGGT/Ω 推理、没有训练视觉模型。

所有原型通过都不能替代跨建筑 holdout、目标游戏验收或用户审美判断。正式接入遵循 ALPHA_0_1_PLAN 的 C1/C2/C3 范围确认。
