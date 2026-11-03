# 日和旧街 · 18栋加密重制

当前交付 J14。固定160×128场地，18栋：8住宅、6店铺、旅馆、钱汤、町会所、小祠。工程路径与文件名前缀沿用 JapanTown12，便于保留历代；内容已扩充为18栋。主线 HAF 0.4，研究总档 HAF05，不是模型权重训练。

请先看 STATE.md 与交付HTML。JapanDetail01原始研究HTML在 docs/JapanDetail01/。J05现代版、J09老街初版和J10–J13草稿均保留，旧运行不覆盖。

## 关键文件

- cases/japan_town12/src/build_detailtown.py：当前原创案例适配器；固定地块及用途，受约束的细节随机。
- cases/japan_town12/runs/J14：最终NBT、空间参数、材料、来源、几何与世界检查记录。
- cases/japan_town12/review/previews/J14：实际NBT离线渲染；scene缓存不打包，可重建。
- cases/japan_town12/review/diagrams/J14：18栋楼层图，H01剖面、四立面与爆炸图。
- cases/japan_town12/src/build_oldtown.py：J09旧分支；build.py为更早的现代版。
- support/japanese_detail_states.py：本轮新增原版方块子集；预览盒体不等于游戏碰撞。

## 复跑

需要 Python 3、numpy、Pillow、nbtlib、Linux libEGL/libGL。渲染使用ctypes EGL，无需PyOpenGL。使用新运行名与不存在的世界输出目录；不要覆盖已有run。当前world导出器明确适用于本案例48格高度。

```bash
python3 cases/japan_town12/src/build_detailtown.py NEW_RUN 20261029104
python3 cases/japan_town12/src/verify_detailtown.py NEW_RUN
python3 cases/japan_town12/src/setup_detail_views.py NEW_RUN
python3 tools/render_building_case.py --case japan_town12 --run NEW_RUN
python3 cases/japan_town12/src/diagrams_detailtown.py NEW_RUN
python3 cases/japan_town12/src/world_detailtown.py NEW_RUN /absolute/new/world/HiyoriTown18
python3 cases/japan_town12/src/build_detailtown.py NEW_RUN_replay 20261029104
python3 cases/japan_town12/src/finish_detailtown.py NEW_RUN NEW_RUN_replay /absolute/new/world/HiyoriTown18 /absolute/delivery
```

最后一步验证banner实体、相同种子字节一致，再生成离线HTML与预览图。世界文件夹可直接装进Java 1.21.1的saves；世界ZIP应把HiyoriTown18作为顶层文件夹。生成器先写input/design_detailtown.json，最终可信记录为每个run的params_used.json与独立回读NBT。

## 实现边界

灰瓦、木框、暖帘、灯具均为原版方块。30个楼层按用途布置并设灯。白玻璃片近似障子/屏风；地毯为不可睡眠的装饰铺床，彩色未燃蜡烛为商品代理；招牌无字。预览没有木纹、旗帜动画或实机光照。

固定18个规划地块，北排锁横向位置和宽度，前后退距/部分宽度/木色/窗组/植被采用稳定随机通道。age和maintenance仅记录，未驱动旧化。尚非任意seed自由排镇引擎；换seed需要重新通过几何和视觉验收。

没有运行Minecraft客户端。门扇、楼梯碰撞、流体更新、旗帜外观和光照仍须实机检查。18份HAF 0.4计划采用既有home/market/restaurant/civic大类，特殊建筑的真实用途布置在案例空间数据中，不能把通用交接计划当作已实现的自动特殊建筑引擎。
