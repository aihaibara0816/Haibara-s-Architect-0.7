# N Seoul Tower / 南山首尔塔 V1

HAF 0.2 主线的新案例。交付基线 `runs/V1_r02`，重复生成 `runs/V1_replay` 的 NBT SHA-256 相同。V1_r01 留作内部首轮检查记录，不是交付版。

## 范围与坐标

- 320 × 308 × 320 格包围盒，X 向东、-Z 向北，约 1 格/米；主塔从 Y=67 到 Y=303，共237格。
- 包括塔体、观景舱、开放设备环、红白天线、多层商业露台、八角亭广场、烽燧台、附属通信塔、缆车上站附近与林地。
- 只覆盖山顶320米场地，不是完整南山公园或完整缆车线路。
- SRTM 约30米原始精度，保存121个采样点。地形采用插值；平台、台阶和挡墙高度由照片解释。官方旧资料、2026手册与DEM的高程差异记录在 `research/component_decisions.json`，不取平均。
- 地形采用封底与边缘封口的表层壳体，内部留空；树木分布与房间布置为程序化近似。

## 复现

Python 3.12；核心生成依赖 numpy、Pillow。地形图另需 matplotlib。预览另需 Linux Mesa EGL (`libEGL.so.1`)。

```sh
python3 tools/agent.py --case namsan_tower --run MY_NEW_RUN
python3 cases/namsan_tower/src/render_case.py --run MY_NEW_RUN
python3 cases/namsan_tower/src/package_import.py --run MY_NEW_RUN
```

每次指定新目录，已有 run 拒绝覆盖。运行不访问网络、不操作游戏世界；研究时取得的 OSM/SRTM 已随工程保存。

`params.json` 记录尺度、种子、半径及场地契约。其中若干楼层高程是案例代码中的明确常量，修改层序请同时查看 `src/build_case.py` 的 `podium_build`、`tower`。这个文件不是通用 BuildingSpec，也不承诺任意建筑自动融合。

## 本轮验证

- HAF 核心26项测试通过，见 `validation/core_tests.txt`。
- 案例22项检查通过，见 `validation/acceptance.json`：237格高度、白色塔身不被内部楼板改色、设备环留空、重复生成、图像对应NBT哈希、历史源码/输出保护等。
- 709,460 个非空气方块，41种方块ID、100种状态，645棵程序化树木。
- Sponge v3 `.schem` 经独立NBT/varint读取后，与源NBT的非空气坐标和状态完全一致。
- 14个 NBT 分块，最大252,235字节；全量拼合与源NBT完全一致。
- 未完成 Minecraft 导入实测、全园步行碰撞验证、真实室内复原及塔身RGB投光还原。离线预览没有资源包纹理或游戏截图保证。

## 反馈入口

交付HTML可按构件填写反馈并导出JSON。填写观察视角、具体问题、希望保留的特征，比只写“更精细”更有助于下一轮修改。新版本保留相同相机与种子，先比较形态，再比较灯光与细节。

## 来源与许可

地图数据 © OpenStreetMap contributors，ODbL 1.0： https://www.openstreetmap.org/copyright ；原始 `osm.xml` 与转换后的地图数据库在 `research/terrain`，其地图数据部分按 ODbL 提供： https://opendatacommons.org/licenses/odbl/1-0/ 。

地形：SRTM，经 OpenTopoData 获取，https://www.opentopodata.org/datasets/srtm/ 。图片/官方手册的URL、查看记录、采用理由及SHA位于 `research/image_sources.json`。交付工程不再分发官方图库图片；代码复现使用已保存的几何参数、地图与高程，不需要下载这些照片。图片研究是人工辅助的构件判断，不是模型权重训练。

保留 HAF 0.2 的 BuildKit 状态库、NBT读写、预览与稳定灯光模块；仅增加有单独预算的 `hafusion/site_scene.py` 和南山案例适配器。既有广州塔、深圳、周大福输出未改写。
