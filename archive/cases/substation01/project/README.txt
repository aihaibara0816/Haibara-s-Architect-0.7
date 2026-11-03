Substation01 / 新港枢纽变电站 / S04
Minecraft Java 1.21.1 原版方块，原创工业建筑。
范围 256 × 64 × 240；X 东，Z 南，Y 上。地面脚面本地 Y7。
220 / 110 / 10 kV 仅为设计主题；设备为装饰性建筑，不进行电力仿真。
源文件 NBT SHA-256: be2a371a680a03c5ba89e65f6bd6245c0db72a0c3e601ef42f6fe9b76f0e28cc

交付：Substation01.html（含旋转模型、29 张视图和内嵌下载）、Substation01.nbt、Substation01.schem、Substation01_World.zip。
世界出生点 (-26, 65, 118)，位于南门；解压后放入 saves。
SCHEM 定位原点：本地 (102,7,238)。包含空气，粘贴前检查目标区域。
模型没有修改既有工业园或列车所；跨项目供电为规划关系。
文件、几何与离线图像已核对，Minecraft 实机碰撞/光照与 WorldEdit 导入待验。

复建（项目根目录，Python3 + numpy + Pillow；nbtlib 已包含）：
python3 src/build_station.py NEW_RUN
python3 src/verify_station.py NEW_RUN
python3 src/export_schematic.py NEW_RUN
python3 src/export_world.py NEW_RUN runs/NEW_RUN/Substation01_World
python3 src/preview.py NEW_RUN
python3 src/cameras.py NEW_RUN
python3 src/render_all.py NEW_RUN
python3 src/pack_interactive.py NEW_RUN
python3 src/deliver.py NEW_RUN
离线渲染需要 EGL/OpenGL；交付脚本的 JavaScript 语法检查需要 Node。
