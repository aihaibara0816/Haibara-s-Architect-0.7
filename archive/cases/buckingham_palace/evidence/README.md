# 白金汉宫 / HAF 0.2 / V1

216 格宽主正面、地图轮廓内院与侧翼、前庭、简化维多利亚纪念碑和花园边缘。不是全园、全部街区或真实 775 间室内。

交付基线 `V1_r02`。`V1_r01` 保留首轮结果；`V1_replay` 用于重跑核对。全景、近景、夜景、俯视、剖切都从导出的 NBT 回读，属于离线方块预览，不是游戏截图。

## 复现

从工程根目录执行：

```bash
python3 tools/agent.py --case buckingham_palace --run MY_NEW_RUN
python3 tools/render_building_case.py --case buckingham_palace --run MY_NEW_RUN
python3 tools/package_building_case.py --case buckingham_palace --run MY_NEW_RUN
```

Python 3.12、NumPy、Pillow；渲染另需 Linux Mesa / libEGL。状态连接和 NBT 工具保留于 `support/`。`params.json` 是尺度、位置、种子的入口，构件细部在 `src/build_case.py`；不是每一个硬编码常量都已参数化。

## 依据和边界

- 王室官方：主立面宽 108 米，主体进深约 120 米（含内院）、高 24 米。 https://www.royal.uk/royal-residences-buckingham-palace
- Historic England：正面 3—7—3—7—3 窗列、中央与两端构图；花园面有弧形凸部。 https://historicengland.org.uk/listing/the-list/list-entry/1239087
- Royal Collection Trust：东翼与内院的历史关系。 https://www.rct.uk/visit/buckingham-palace/history-of-the-east-wing-of-buckingham-palace
- 官方参观图解：只查看第 10、18 页，采用入口雨篷关系。 https://media.rct.uk/sites/default/files/2025-08/Buckingham%20Palace%20-%20Access%20Guide_Photo%20Journey_2025.pdf
- 平面数据 © OpenStreetMap contributors，ODbL 1.0；非测绘、非内部实测。 https://www.openstreetmap.org/copyright

- 地图高度不等于测绘高度；主正面按 108 米宽校准，屋顶、各翼和局部雕饰为估计。
- 窗后家具是可重复的伪内饰；不宣称还原真实房间布局或全部房间。
- 维多利亚纪念碑雕塑、喷泉和种植被简化；不是完整景观还原。
- 静态英国旗只是模型标识，不表示当日王室是否在宫内。

## 反馈修改

先在 HTML 中选构件记录反馈并导出 JSON，或编辑 `feedback_template.json`。每次修改使用新的 run 名，记录所用照片、参数、保留项和修改项，再用同一相机比较。反馈不会自动执行改造或训练模型。历史 run 不覆盖。

## 本轮修正

- r01 → r02：修复厚墙后没有连通开间的问题；可检查玻璃、墙厚、房间空隙的前后关系。
- r01 → r02：花园立面改用独立大窗、小窗、柱列和半穹顶构图；补上高低屋面之间的外露窗墙。
- r01 → r02：主正面相机移入前庭，防止纪念碑挡住中央阳台。

## 下一轮验收

- 先检验庭院与侧翼屋面高度，避免地图库标签导致体块偏厚。
- 继续细化后立面窗位、柱式和雕饰；不要用增加随机细节代替照片比对。
- 游戏内检查入口、门窗、栏杆连接、伪内饰通行及窗灯亮度。

## 数据与版权

图片来源、文件哈希和观察保存在 research/；原站照片与 PDF 不随源码包分发。地图及转换后的平面属于 OpenStreetMap 数据衍生，保留 ODbL 1.0 说明。代码规则是案例解释，不是任意西方建筑的自动识别器。
