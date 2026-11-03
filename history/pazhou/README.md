# 琶洲微信总部 · HA0.3 / HAFusion 新案例实验

2026-10-23。先打开 `delivery/琶洲微信总部_快速对比.html`；完整版保留八张原始照片与图片 ZIP 下载。两版 NBT、材料、源代码、参数、检查和局部返工实验均在本包。

本轮不是广州塔 V5→V6。两路从同一新建筑的原始资料池出发，各自记录决策并在独立进程生成。为控制变量，两路使用同一宿主、几何编译规则、尺度、材料和相机；因此不是独立设计师盲测，也没有测试两种自动图片理解模型。

结果：两路各39,306个非空气方块，56×100×82格；最终状态逐块一致。当前 HAF 的真实新增价值在证据仲裁、缓存和复核保护。本例没有证明美观程度更高或全流程更快。32项文件/几何/流程检查通过；7组同相机独立渲染逐像素一致。真实游戏导入、光照、碰撞未进行。

## 边界

- 主楼总高206.75m有施工方竣工来源；按当前图片 Skill 的高楼城市比例280/600格每米，主体96格。原 BuildKit 的默认1:1没有被偷偷混入。
- 平面宽60m、深44m等为试值；真实宽深仍为unknown。裙楼45/54.05m来源冲突保留，本次暂取54.05m研究。
- 包含主楼、北裙楼、跨路连接、简单地景；不含地下和邻栋。室内只作示意核心与楼板，不代表38层全部可走。
- 使用已读图片与文献，没有可用本项目三维模型。本轮没有模型训练、自动摄影测量、自动SU融合。
- `research/packet.json` 是本案例的 `case-research-1.0` 档案，服务此实验；不是宣称已通过通用 packet v1.1 全字段验证的插件交换文件。
- HAF原完整pipeline是广州塔案例入口，本轮没有调用它。`tools/run_route.py` 是新增的薄案例入口；调用原有通用仲裁、缓存、HA几何和PlanCraft检查。`engines/`是未修改快照，原工程也未改动。
- HAF的分组几何日志目前只覆盖组内重叠；没有实现严格跨组冲突拒绝。最后拼合与HA全量结果逐块核对通过。

## 目录

`engines/HA03/` 与 `engines/HAF/`：原引擎必要代码的逐字快照及许可文件。

`routes/<route>/research/`：各自收到的资料快照、采用决定；HAF另外保存仲裁结果和人工复核。

`routes/<route>/runs/baseline/`：各自基线NBT、执行BuildingSpec、读回检查、原生预览和方块数据。

`routes/HAF/runs/warm_repeat/`：13个阶段全命中的重复运行。

`routes/<route>/runs/local_revision/`：测试性花池平移1格。两路都仅6个方块状态变化，声明范围外变化0；HAF只重建geometry.terrace2与assembly.materials。该实验没有混入交付基线。

`routes/<route>/checkpoints/`：从各自最终参数实际重建的体量/主塔诊断NBT，以及最终结果指针。属于回顾用阶段导出，不是隐藏思维或原始实时进度录像。

`previews/`：独立NBT回读后的七视角图；相机冻结于 `cameras.json`。预览用整方块、示意颜色和近似光照，不是游戏截图。

`reports/`：32项测试、逐像素比较、HTML资产验证与引擎原件哈希。

## 可复跑命令

Python 3.12；核心需要numpy、Pillow、jsonschema，准确版本见requirements。现有run不覆盖，使用新名字：

```bash
python tools/run_route.py HA03 --run experiment_02
python tools/run_route.py HAF --run experiment_02
python tools/run_route.py HAF --run experiment_02_revision --revision
python tools/evaluate.py
python tools/export_scene.py HA03
python tools/export_scene.py HAF
python tools/render_egl.py HA03 cameras.json
python tools/render_egl.py HAF cameras.json
```

EGL图片渲染另外需要Linux Mesa libEGL/OpenGL；不具备该环境时原生CPU预览仍可生成。`evaluate.py`核对本包既有baseline/warm_repeat/local_revision；新命名实验需更新检查输入或单独检查它的report。快照原件完整性检查在原环境还会比较原文件；移到别的电脑时找不到原路径应记pending，不能伪造原件核对。

`case_spec.py`是本建筑几何解释入口，修改它将改变案例，不是升级通用引擎。不能把本例的60m宽或平台高度推广成其他建筑默认值。缓存键同时包含代码、证据、坐标、依赖及参数；更新源代码后不得沿用旧命中结果作新版本性能证据。

## 游戏测试与反馈

将两个基线NBT分别在空白测试区域导入。包含显式空气，不能直接覆盖正式建筑。历史目标为Java1.21.1/DataVersion3955，当前实际客户端/Create版本尚未核验。先看外形、玻璃、道路和公共入口，再检查灯光。HTML中的反馈区支持按构件记录意见并导出JSON。

重点待改：幕墙过粗、裙楼太规则、峡谷斜面与平台亭体简化、水平尺度未测绘、参数证据绑定仍偏宽泛。先补对应构件资料，再确定修改范围，不用继续追加相似全景图。

## 来源与许可

第三方代码保留原许可，PlanCraft为MIT，本次使用的commit为b0746140cf378d7e03b16887ef64ff9d99991f86。HAF关于Arnis/ObjToSchematic的借鉴是已有独立实现的设计思路，不表示本案例调用了那些程序。

照片来源为AJN项目页，标署©有方Archiposition；其他许可未知。只作本次有来源的研究参考，不代表取得训练、商用或再许可授权。完整网页正文没有打包再发布；来源URL与阅读记录在research档案。
