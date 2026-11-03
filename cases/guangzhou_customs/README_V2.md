# 广州新海关 · HAF V2

交付：`V2_r06`，2026-10-24。沿用 HAF 0.2，花城大道83号新海关，纯图片路线。

## 怎么看

先打开 `Guangzhou_Customs_HAF_V2_Review.html`。推荐按西北日景 → 钟冠后斜视 → 正俯视 → 三层平面剖切 → 裙楼斜视 → 正面入口的顺序看。页面同时保留27个同机位V1/V2对照和11张参考照片。照片不是同机位摄影测量；模型的四向标签不是已测地理北。

交付建筑为170,919个非空气方块，包围体126×148×116格。地面y=4，总高度137格保留为对比包络。19项案例技术检查、23项原有共享测试通过；还原度待用户复核，Minecraft游戏内导入未测试。

## 本轮修改

- `src/build_case.py`、`params.json`、V1_r04输出与全部HAF共享核心保留原样。
- `src/build_v2.py` 是独立V2案例适配器，复用V1的窗洞、柱、钟冠及HAF状态方块/导出机制。
- `params_v2.json`：中央下段27×32、上段27×24；原中央体27×48。钟室13×13不变，移至新上段中心并增加阶梯底座。
- 两翼前后进退与环绕上部横带分别生成。裙楼分为前部、内退后墙、突出翼及侧入口，模型-X为大拱门侧、+X为普通窗墙侧。这是两张侧照互证后的相对映射，绝对方位待核。
- 补连续柱廊、内缩玻璃、半砖吊顶、上层小拱窗、低栏杆、门纹代理、侧入口台阶及连续平台。
- 内部楼梯随体块收窄迁移；房间与灯位在楼梯完成后分配，避免穿墙及覆盖灯具。
- `agent_config.json` 在此交付副本中指向V2适配器；旧入口仍可直接运行。未修改正式仓库或网站。
- `cameras.json` 只新增正俯视剖切与局部视图，原14个相机不改；通用渲染器仍自动补八个昼夜四向。

## 重跑

Python3.12、numpy、Pillow；EGL预览另需Linux libEGL与OpenGL环境。

```bash
python3 tools/agent.py --case guangzhou_customs --run MY_V2_RUN
python3 cases/guangzhou_customs/src/validate_v2.py MY_V2_RUN
python3 tools/render_building_case.py --case guangzhou_customs --run MY_V2_RUN
python3 tools/package_building_case.py --case guangzhou_customs --run MY_V2_RUN --name Customs_Custom
```

V1重跑使用：

```bash
python3 cases/guangzhou_customs/src/build_case.py --run MY_V1_REPLAY --params cases/guangzhou_customs/params.json
```

报告脚本 `src/review_v2.py` 默认读取交付run。需要更改报告版本时同时更新脚本顶部RUN。PNG图板中文字体通过`HAF_CJK_FONT`指定；不影响建筑生成和渲染。

## 证据与限制

`research/v2/image_manifest.json`逐张记录图片来源、真实文件、用途、SHA和是否查看。`component_decisions.json`记录图片→构件→参数→代码消费者。旧资料包中未采用的大图被重新取回查看，另有CTBUH侧照。02/12近重复，03/05遮挡明显，低清图只做佐证；11张不等于11个方向。源图版权归原作者；随案例保存供私人研究，不授予商业转授权或模型训练许可。

OSM粗轮廓与一次卫星区域观察保存在`research/v2/context`。卫星影像存在高楼倾倒、遮挡及轮廓口径问题，没有取得可靠实测屋顶平面。影像拼接只是按地图切片坐标排布，并非从多张建筑照片重建相机或三维参考盒。地图来源：© OpenStreetMap contributors（ODbL）；Esri, Vantor, Earthstar Geographics, GIS User Community。未把9张邻接地图瓦片计为9个建筑视角。

高度103/114/137米口径冲突未解；中央体、裙楼进深及侧入口尺度都是可调试作假设。部分背面与隐藏位置按连续围护推定。细小钟面和古典纹样仍受一格尺度限制。伪内饰、海晶灯/荧石混合与航空红点是游戏设计，无可靠夜照支持。没有SU或其他三维模型，没有训练神经网络权重。

## 导入

建筑包包含完整Sponge v3 `.schem`、稀疏Java结构`.nbt`、3个分区NBT、偏移表、材料CSV和状态CSV。DataVersion3955。建议新空白场地试导入；稀疏NBT不能清空V1旧方块，必须事先清场或使用含空气的schem。分区必须使用相同原点、按`module_offsets.csv`的XYZ偏移放置。这里只做离线格式与精确方块状态回读，不能代替游戏兼容性、光照、植物更新或导入工具实测。

## 下一轮反馈

在HTML选择构件与视角，记录问题并导出JSON。导出包含最终NBT哈希，避免讨论时误用旧图。优先核中央上段深度、普通窗翼/拱门侧的相对位置、裙楼进退，再核钟面、柱径和石材层次。不要用增加细节或灯数替代形体判断。

