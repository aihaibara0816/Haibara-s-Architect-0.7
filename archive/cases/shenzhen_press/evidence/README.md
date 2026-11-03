# 深圳特区报业大厦 · HAF V2

当前发布 `runs/V2`。原 HAF r03 固定为 `baselines/V1`；HA0.3 和原始双路线工作目录均保留。后续细节、学习和生成全部进入 HAF，案例参数仍需按真实建筑证据填写。

## 交付

- `deliverables/Shenzhen_Press_HAF_V1_V2.html`：14 组同机位对照，可点击大图、切换叠图、导出构件反馈；包含材料表与 NBT/数据包下载。
- `deliverables/Shenzhen_Press_HAF_V2.nbt`：实际主建筑，87,248 个非空气格位。
- `deliverables/Shenzhen_Press_HAF_V1_V2_Java_1.21.1.zip`：两版各24个 ≤32格模板，独立回读后精确拼合。
- `*_Materials.csv` / `*_Blockstates.csv`：材料ID与完整状态分账；半砖/楼梯/玻璃片不折算为完整方块。
- `research/v2_feedback.json`：问题、改法、证据、构件ID、视图和剩余限制。

## 生成及回改

从 HAF 根目录运行：

```bash
python3 tools/agent.py --case shenzhen_press --run MY_NEW_RUN
python3 cases/shenzhen_press/review/render_compare.py --version V2 --run MY_NEW_RUN
PYTHONPATH=support/deps python3 -m unittest discover -s tests -v
```

`tools/agent.py` 调用本案例，实际使用根目录 `hafusion/cache.py`、`hafusion/lighting.py` 与 `support/`。没有另建一个 HA0.3 新版本。`parameters.json` 控制主弧面、楼层与灯光；当前屋顶/侧翼/裙房的细部几何仍在 `src/build_case.py`，不是任意建筑的通用自动生成器。

灯光：`interior.seed` 控制办公室的亮暗/材质/灯位，家具布局使用独立固定种子。`podium.lighting_seed` 控制裙楼后房间。门厅和入口引导灯保留固定位置。同一种子复跑 NBT 完全相同；换室内种子只改变灯光，已用161个差异格位验证。改变源码仍使全部14阶段失效；纯室内种子改变只重建2阶段。

后续比较在新 run 下生成，不能覆盖 V1/V2。发布校验目前固定读 `runs/V2`，新版本必须显式更新校验目标，不能照搬本轮通过记录。

## 本轮修订

- 保留原主弧面、斜边网格、新闻眼及天线格架，已按所有原归属格位核验。
- 增加左侧横窗翼和圆玻璃连接，侧后翼与承托；核心小窗嵌入墙面。
- 加厚屋顶实体与退后连接覆顶；屋顶轮廓尺寸仍估算。
- 裙房顶檐加厚、右端斜收、左实体露台和圆角体，补后侧围护；前部敞廊仍开放。
- 146个窗后房间是表现楼板/吊顶/隔墙/家具层次的游戏补全，79个在当前种子下亮灯；不代表真实房间数。
- 实际海晶灯65、荧石36、末地烛8。灯色和亮度由 Minecraft/资源包决定，预览不是原版游戏光照证明。

## 保留与证据

`baselines/V1/source` 是原 HAF 源码/参数快照，原始可运行双路线工程保存在源包的 `preserved_legacy/Shenzhen_Press_Two_Routes_Source.zip`。原文件未重新打包；外部完整目录仍在 `shenzhen_press_pair_20261023`。`validation/protected_before.json` 与发布校验确认1,123份历史源码、依赖、输出和交付文件未改。

输入图13份（原11份加N13/N14），额外搜索记录保留在研究目录；不存在六图输入限制。N14只覆盖背部边缘，未得到完整背面或可信夜景。背面窗格、屋顶精确尺寸、室内布置均为估算。照片互证和外部schem表达研究推动了本轮规则修改，不表示机器学习训练完成。

原输入照片信用与来源在 `input/manifest.json`；新图许可未知，私有研究使用，不据此推断训练/公开分发授权。报告引用照片优先保留 Commons 的原归属信息。

## 验证层次

16项发布检查、HAF 12项单元回归通过；48个模板精确拼合。同机位预览由最终NBT回读；原细部表达模块仍是有限原版状态白名单。视觉为操作者检查，用户尚未验收，不能把方块数量增长称为还原度提高。

没有 Minecraft 游戏内测试，未验证原版碰撞、邻接更新、通行与灯光。整楼连续交通未完成。场景68×214×68，地面Y+2，尖顶Y+211。数据包目标Java1.21.1，稀疏模板不清除旧方块，请使用净空测试区域。完整NBT与分块二选一；不要重叠导入。
