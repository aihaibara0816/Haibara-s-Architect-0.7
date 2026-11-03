# 大本钟 · 伊丽莎白塔 / HAF 0.2 / V1

192 格钟楼、四面钟盘、钟室、塔内楼梯候选与截断的邻接翼楼。邻翼用于连接关系测试，不是完整威斯敏斯特宫。

交付基线 `V1_r02`。`V1_r01` 保留首轮结果；`V1_replay` 用于重跑核对。全景、近景、夜景、俯视、剖切都从导出的 NBT 回读，属于离线方块预览，不是游戏截图。

## 复现

从工程根目录执行：

```bash
python3 tools/agent.py --case elizabeth_tower --run MY_NEW_RUN
python3 tools/render_building_case.py --case elizabeth_tower --run MY_NEW_RUN
python3 tools/package_building_case.py --case elizabeth_tower --run MY_NEW_RUN
```

Python 3.12、NumPy、Pillow；渲染另需 Linux Mesa / libEGL。状态连接和 NBT 工具保留于 `support/`。`params.json` 是尺度、位置、种子的入口，构件细部在 `src/build_case.py`；不是每一个硬编码常量都已参数化。

## 依据和边界

- 议会官方：塔高 96 米、四面钟盘，每面直径 7 米。 https://www.parliament.uk/about/living-heritage/building/palace/big-ben/facts-figures/
- 修复建筑师图库：整塔、钟盘、钟室、金属屋顶、内部及夜景。 https://purcellarchitecture.com/project/elizabeth-tower/
- 修复后蓝色与金色装饰的证据。 https://www.parliament.uk/about/living-heritage/building/palace/big-ben/elizabeth-tower-and-big-ben-conservation-works-2017-/turning-big-bens-clock-dials-blue/

- 14 格钟盘不能完整写出罗马数字，刻度与浮雕均简化。
- 尖顶、钟室分段高度、邻翼细节仍是照片解释；未使用测绘模型。
- 塔内楼梯未做玩家通行、碰撞或消防式通路验收；钟不会走时或报时。

## 反馈修改

先在 HTML 中选构件记录反馈并导出 JSON，或编辑 `feedback_template.json`。每次修改使用新的 run 名，记录所用照片、参数、保留项和修改项，再用同一相机比较。反馈不会自动执行改造或训练模型。历史 run 不覆盖。

## 本轮修正

- r01 → r02：缩短钟室与灯笼，拉高上尖顶，去掉宽蓝色屋顶条纹。
- r01 → r02：钟盘加入连续背衬，避免透出零散灯块；补齐邻翼端面的窗列。

## 下一轮验收

- 钟面数字与花饰的更细尺度局部样板。
- 对照正视照片校准各段高度与屋顶折点。
- 游戏内检查钟室开口、楼梯和夜景亮度。

## 数据与版权

图片来源、文件哈希和观察保存在 research/；原站照片与 PDF 不随源码包分发。地图及转换后的平面属于 OpenStreetMap 数据衍生，保留 ODbL 1.0 说明。代码规则是案例解释，不是任意西方建筑的自动识别器。
