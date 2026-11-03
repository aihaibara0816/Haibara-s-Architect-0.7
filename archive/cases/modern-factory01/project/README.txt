ModernFactory01 V3 / 新港制造园 · 综合生产基地
硬质场地修订版：植被仅作边界、树池和休息区点缀。
原创园区 448 × 336，高度容器 72；最终运行 E07。相对上一版用地约 2.47 倍。
后场：原料堆场、筒仓、加工塔架、储罐及管廊。
中段：连续生产、包装检测、成品库及装卸区。
前场：八层办公主楼＋五层侧翼、两层食堂、两栋六层宿舍、员工连廊和配套。
宿舍 120 间双人房 / 240 个床位；食堂一层 144 席，二层 48 席及休息活动。
Java 1.21.1 / DataVersion 3955，原版方块，无必需模组。
世界目录 ModernFactory01_E07_1.21.1 放入 saves，出生点 2 65 161。
Sponge v2 schematic 的粘贴原点为主入口，包含空气，先在空白测试区导入。
没有运行客户端或 WorldEdit；设备和车辆为静态造型，原版床/门/容器互动待实机验证。
预览使用真实 NBT 几何；材质、玻璃、照明为近似，水平切片按四格分段。

复现（Python 3.10+，numpy、Pillow；nbtlib 已在 deps）：
python src/build_expansion.py NEW_RUN
python src/access_audit.py NEW_RUN
python src/cameras.py NEW_RUN
python src/preview.py NEW_RUN
python src/render_all.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新的世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
python src/deliver.py NEW_RUN
EGL 渲染需要 libEGL / OpenGL 3.3；交互页面需要 WebGL2 与 DecompressionStream。
在 deliver.py 打包前，世界目录应为 deliverables/ModernFactory01_NEW_RUN_1.21.1。

input/：设计交接、空间与来源记录。
runs/E07/：最终结构、schem、房间与通行数据、规格、独立检查。
review/：30 张同源 PNG 及预览网格。
src/：本案例生成器、预览与导出程序。
support/：复用并针对原版床/木桶/熔炉补齐实体导出的 HAF 核心。
assets/：交互脚本、报告样式、上一版对照图。
ModernFactory01_Model.html：独立离线旋转模型。
本案例为原创建筑场景，不是实际工厂工程方案，也不是通用生成器。
