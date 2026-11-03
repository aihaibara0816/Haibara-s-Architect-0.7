Taisho14 · 櫻坂風貌街 · HAF 0.4 · Q03
2026-10-31

本轮交付
  18栋用途与体量不同的和洋混合街区，双坡街、连接巷道、溪桥及公共节点。
  独立钟楼、学校、公共文库、诊所、地方车站；保留并深化日常小店、旅馆和住宅。
  查看器采用：整体/片区/单栋 → 视图 → 四方向 → 日夜。
  默认片区近景；单栋按名称直选，方向和日夜分别控制，可缩放、复位和放大。
  新的查看器源码与规范可复用，但未修改已安装的个人Skill。

主要文件
  delivery/Taisho14.html：完全离线HTML，附图片及NBT/地图下载。
  delivery/Taisho14_World_1.21.1.zip：Java 1.21.1地图。
  runs/Q03/Taisho14.nbt：整街；同目录另有18份单栋NBT。
  runs/Q03/spec.json：地块、入口、楼梯、灯与使用接近点。
  research/design_brief_14.json：本轮设计范围与假设。
  research/presentation_standard_v1.json：展示规范。
  assets/viewer_v1.js、assets/quarter_report.html：可复用的查看器和报告模板。

进入地图
  ZIP内 Taisho14_World 文件夹放入 .minecraft/saves。
  出生点 94 68 19，东侧下街溪桥；/time set night 查看夜景。
  原版方块，无必需模组；NeoForge 1.21.1环境应保持对应原版方块。
  整街结构196×60×158；世界偏移[-98,62,-79]。
  普通结构方块默认尺寸不适合整街，建议用地图或支持大结构的导入器。
  稀疏NBT不负责清除目标场地所有旧方块。

使用与边界
  钟楼底层可进入，上部钟面固定装饰，不是运行时钟。
  车站有候车厅、售票、站务、站台和短轨道，不是完整铁路系统。
  原版床、桶、炉、告示牌有数据；椅子、相机、杯具、邮筒主要为造型。
  所有预览从最终结构文件生成；单栋地块基准Y=2，城内另有旋转与高差。
  原版模型/纹理首帧颜色离线近似，实体画、床、文字、透明和灯光有简化。
  没有启动客户端。近似人体通行、灯与小物支撑、状态/载荷检查不替代实机。
  18栋扩展与测试通过不等于审美验收通过。

复现
  Python3.10+，安装 requirements.txt。Node.js用于查看器逻辑检查。
  Linux Mesa/EGL libEGL.so.1、libGLESv2.so.2用于离线渲染。
  官方Minecraft资源不随项目分发，运行 python src/fetch_vanilla_assets.py 获取已固定版本。
  新建run，构建器拒绝覆盖已有目录：
    python src/build_quarter.py NEW_RUN 141145
    python src/audit_quarter.py NEW_RUN Taisho14
    python src/audit_more.py NEW_RUN Bookshop
  对其余17栋按NBT文件名运行 audit_more.py。
    python src/render_quarter.py NEW_RUN full
    python src/export_quarter_world.py NEW_RUN delivery/World_NEW_RUN
  只渲染特定建筑可加第四参数，例如：
    python src/render_quarter.py NEW_RUN full Clock,School,Station
  官方资源与渲染网格缓存体积大，不包含在归档中，可重建。

随机复现
    python src/build_quarter.py REPLAY14 141145
    python src/build_quarter.py ALT14 141146
    python src/verify_quarter_repro.py Q03 REPLAY14 ALT14
  18栋体量、用途、位置、门与楼梯均为设计结果；种子只控制允许的道路修补和植物。
  没有任意地形NBT自动布局求解器，也没有训练神经网络权重。

展示页和打包
  先把 delivery/Taisho14_World_1.21.1.zip 解压，内部目录在delivery改名为Taisho14_World_Final。
    python src/report_quarter.py Q03
    node src/check_quarter.cjs Q03
    python src/package_quarter.py Q03
  生成报告读取该run的最终图像、审计、地图检查、复现记录；不要把旧run标签当新证据。

来源
  Taisho13 S05当前项目恢复后的延续。原成果保持不变。
  沿用BV1Dx41187iG此前部分片段观察，本轮为新增原创用途和街区，不声称完整视频复刻。
  视频与Minecraft官方资源归各权利方，不分发视频截图、客户端JAR或官方资源包。
