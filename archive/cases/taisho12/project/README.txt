Taisho12 / A06 — 三栋大正浪漫参考小样
HAF 0.4 / Minecraft Java 1.21.1 / seed 1145

交付：青葉書肆（铜板看板门脸书店）、白鷺薬局（洋式街角药局）、松風館（和洋小旅馆）。
这是原创参考设计与三栋比较街，不是历史原物的精确复原，也不是完整18栋地形街区。
本轮追加的 Bilibili《大正的街道～最终景》观察在 research/video_observations.json。
该视频收到时 A06 已生成，新增观察尚未落实进 A06 模型。没有宣称看完全部视频、验证其室内或完成模型训练。

直接使用：
1. delivery/Taisho12.html 是离线研究页，含92张预览、四个NBT、空间JSON与地图ZIP下载按钮。
2. delivery/Taisho12_World_1.21.1.zip 解压后，将 Taisho12_World 放入 .minecraft/saves。
   出生点 0 65 22；书店入口 -40 65 11；药局 3 65 6；旅馆 32 65 9。
3. structures 中为小写结构名。单栋地块均不超过48格；整街宽110格，请用存档或兼容导入器。
   稀疏NBT不会自动清空所有旧建筑，请在备份或空白测试地图中导入。
4. 门、床、桶、炉等数据已保留；画为实际 painting 实体；椅子/杯具为装饰造型。
   塔屋为封闭装饰屋顶，不是额外可进入的客房。

复现（从本目录运行，Python 3.12；不要覆盖已存在的 runs/A06）：
python3 -m pip install -r requirements.txt --target pydeps
PYTHONPATH=pydeps python3 src/build_more.py REBUILD 1145
python3 src/fetch_vanilla_assets.py
PYTHONPATH=pydeps python3 src/audit_more.py REBUILD Bookshop
PYTHONPATH=pydeps python3 src/audit_more.py REBUILD Pharmacy
PYTHONPATH=pydeps python3 src/audit_more.py REBUILD Inn
PYTHONPATH=pydeps python3 src/render_more.py REBUILD Bookshop
PYTHONPATH=pydeps python3 src/render_more.py REBUILD Pharmacy
PYTHONPATH=pydeps python3 src/render_more.py REBUILD Inn
PYTHONPATH=pydeps python3 src/render_more.py REBUILD Taisho12
PYTHONPATH=pydeps python3 src/export_world.py REBUILD delivery/Taisho12_World_Rebuilt

渲染需系统 EGL/OpenGL；官方客户端与材质不随包分发，fetch_vanilla_assets.py 从 Mojang 官方源下载并校验。
渲染、审计、报告脚本及其依赖均随包附带。报告生成器默认读取已附带的 runs/A06 和预览；重新导出到不存在的
目录 delivery/Taisho12_World_Final 后，可运行 PYTHONPATH=pydeps python3 src/report_more.py；node src/check_more.cjs 检查报告。

最终验证：
- 四份NBT相同种子字节复现；换种子仅改变合法路面及植物位。
- 三栋门框、床配对、承托、31个功能接近点与楼梯近似碰撞检查无报错。
- 世界回读229376格，差异0；157个方块实体和9幅画载荷对应。
- 整街NBT SHA256 b25303bd94c35c198448ccb4133f5c4acd0a966e1098f880b0d0a10fc1d3072e
- 未运行Minecraft客户端。完整碰撞、实体表现、实际光照和审美仍需进图确认。
- PNG为最终NBT的离线近似渲染，不是游戏截图；玻璃、字面、床实体与光传播有简化。

文件说明：
research：来源、现场观察、设计说明、照片出处。
runs/A06：最终NBT、参数和检查记录。
research/diagnostics：本轮早期失败的审计快照；不包含其过时NBT。
review/previews/A06_*：最终四面、室内、平面、剖面、分层与日夜图。
manifest.json：文件校验清单及研究状态。

参考照片版权归各原作者/机构，仅作署名研究对照，不代表训练或商业再发布许可。
