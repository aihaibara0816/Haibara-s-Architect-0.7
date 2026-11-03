# Haibara’s Architect 0.7 快速开始

下载完整仓库，在仓库根目录用 Python 3.10+ 运行。每次练习换新 `--run`，旧运行目录不能覆盖。

## 一、了解规则与成果

```sh
python -X utf8 tools/haf.py workflow
python -X utf8 tools/haf.py skill list
python -X utf8 tools/haf.py skill show --name interior
python -X utf8 tools/haf.py recipes
python -X utf8 tools/haf.py archive list
python -X utf8 tools/haf.py archive show --case room06
python -X utf8 tools/haf.py archive verify
python -X utf8 tools/haf.py archive export --case room06 --destination exports
```

`archive export` 复制已归档 ZIP，未重新建造；同名导出不会覆盖。`skill` 展示仓库规则，不执行个人 Skill 安装。

## 二、实际生成阅览室、庭园和工业小样

```sh
python -X utf8 tools/haf.py scene-plan examples/habitat07/reading-garden.json
python -X utf8 tools/haf.py scene-build examples/habitat07/reading-garden.json --runs-root runs/tutorial07 --run garden-001
python -X utf8 tools/haf.py scene-verify --runs-root runs/tutorial07 --run garden-001
python -X utf8 tools/haf.py scene-build examples/habitat07/industrial-yard.json --runs-root runs/tutorial07 --run industry-001
python -X utf8 tools/haf.py scene-verify --runs-root runs/tutorial07 --run industry-001
```

预计分别为 3,261 与 6,633 个非空气方块。`scene-plan` 只编译检查，不写 NBT；`scene-build` 明确建造；`scene-verify` 重放配方、摘要、尺寸、版本、实体、显式空气和最终方块。视觉、游戏与审美状态仍 pending。

坐标 XYZ 中 Y 向上；高程为地面顶层方块 Y，放置承托面一般是地面 + 1。`height_rows[z][x]` 必须由使用者提供。场景单边最多 160、总体积最多 1,000,000 格；1–200 个模块、最多 500 个半开禁放框。方块碰撞、悬空支点、水域上方的树冠也会拒绝。固定尺寸配方不含旋转、缩放或自动道路求解。

输出 `request.json`、`scene_plan.json`、`owners.json`、`scene.nbt`、`manifest.json`。NBT 含显式空气，先导入新的测试区域；程序不会修改存档。

## 三、重跑 Room06 内饰源工程

```sh
python -m pip install -r requirements.txt
python -X utf8 tools/haf.py build-study --case room06 --runs-root runs/tutorial07 --run room-001 --seed 1145
```

新目录中的 `project/runs/result/Room06.nbt` 为建造结果，`build.log` 和 `audit.json` 保存检查。种子只改变原工程允许的植物项，不把 Corner01 整楼标为已返工。需要 `nbtlib`；缺依赖会在创建 run 前明确失败。

## 四、保留的旧案例与规划

```sh
python -X utf8 tools/haf.py build-case --case elizabeth_tower --run tower-001 --execute
python -X utf8 tools/haf.py demo --runs-root runs/tutorial06 --run demo-001
python -X utf8 tools/haf.py verify --runs-root runs/tutorial06 --run demo-001
```

前者使用钟塔专用适配器；后两条是 0.6 兼容规划，不生成 NBT。模型接入见 [说明](model-integration.md)，每代建筑与细节见 [演进](version-history.md)。
