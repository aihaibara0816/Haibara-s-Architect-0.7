Guanggang01 / 广钢式工业区 · 一号钢厂
原创样板，非广钢实测复原。用地 240 × 192 方块，结构容器高 88 方块。
Java 1.21.1 / DataVersion 3955，原版方块，无必需模组。
最终运行 G03。所有图片和旋转模型由最终 NBT 独立回读派生。
世界存档：Guanggang01_G03_1.21.1，放入 saves。出生点 12 65 83。
schem：Sponge v2，厂门内站立点为粘贴原点，包含完整空气范围。WorldEdit 未实测。
NBT：完整场景源数据，超出原版结构方块常用尺寸，优先使用存档或 schem。
未运行 Minecraft 客户端。机器、车辆、生产线都是静态造型。灯光离线近似。

复现（Python 3.10+，numpy、Pillow；nbtlib 已附在 deps）：
python src/build_industrial.py NEW_RUN
python src/preview.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
固定视图：src/preview.py NEW_RUN runs/G03/camera_batch_0.json，依次批次 0..5。
源构建脚本是本案例参数化适配器；不是任意工厂的全自动生成器。

内容：
src / support：本案例脚本与复用的方块核心、独立读取器、EGL 预览工具。
assets：预览着色器与交互模型脚本。
input：原创设计交接、规划核对、来源记录和世界模板。
hafusion / docs：HAF 0.4 交接检查器及本案例扩充的工业用途类别。
runs/G03：NBT、schem、构件归属、规格与检查结果。
review：最终 18 个 PNG 视图及渲染记录；PNG 内含源 NBT 哈希。
Guanggang01_Model.html：离线可旋转模型。

来源参考：广州市林业和园林局 https://lyylj.gz.gov.cn/ztzl/lvst/stsfd/content/post_9910092.html
原型范围：高炉、热风炉、煤气柜、料仓、上料斜廊、厂房、铁路和循环水设施。
尚未覆盖：焦化、烧结、炼钢、能源站等完整联合钢厂系统；未模拟工艺能力。
