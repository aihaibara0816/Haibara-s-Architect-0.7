RailDepot01 / 新港列车所 / R15
Minecraft 1.21.1 + Create 6.0.10；目标 NeoForge 21.1.244。
新建原创场地 480×240，高度容器104；15层综合楼、低层库房与员工配套。
主场十股道：北侧6条、南侧4条，各自逐级汇入双线接口Z87/Z93，轨心距6格。
10段曲线51.573–52.668格；原有效检修120格；两条新增露天线各100格侧平台。
独立检修道移入主场南侧Z135，长141格；压缩空气机组移至水罐一侧。
撤去北侧外围道路；股道之间使用嵌地灯组，每级道床边缘使用深色收边。
道床高于普通维护场地2格；新增变配电场、水罐泵房、压缩空气机组；研发塔楼接入三层实验培训裙楼；北侧三处设施统一正面边线。
原附件：两端驾驶+中间车厢，车体包络约68格，宽5格。原始参考与校核尺度分开。
新世界不含活动列车；只有Create的轨道、车站、信号与示范时刻表。
调度楼一层木桶 -18 65 62：RD-TEST-W / RD-TEST-E 独立试验线循环时刻表，20秒停站。
主库自动作业需在外部接入和待避线路落实后另行配置。
不要将离线检查理解为自动运行已通过。需要实机验证区块加载、轨道图、站名、双向驾驶、信号方向与时刻表。
独立世界目录 RailDepot01_R15_Create6.0.10 放入 saves；出生点 -50 65 111。
原生 .nbt 用于Create蓝图导入测试；.schem 为Sponge v3，保留完整空气和嵌套数据。WorldEdit导入未实测。
使用v3是为了让Sponge的实体类型Id与Create内部UUID Id各自保留，不能压成同一个字段。

复现：Python3 + numpy、Pillow；项目deps提供nbtlib。EGL/OpenGL用于固定图渲染。
python src/build_depot.py NEW_RUN
python src/audit_rail.py NEW_RUN
python src/verify_redesign.py NEW_RUN
python src/verify_campus.py NEW_RUN
python src/cameras.py NEW_RUN
python src/preview.py NEW_RUN
python src/render_all.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
python src/research_views.py
python src/deliver.py NEW_RUN
打包前将世界放在deliverables/RailDepot01_NEW_RUN_Create6.0.10。

input/source/：原始三个NBT；research/：测量、数据示意及证据分层；runs/R15/：最终模型和检查。
src/：本案例生成器及Create适配器；support/：复用HAF核心；reference/create/：MIT许可源码与来源记录。
Create官方美术资产未打包；预览为独立的无纹理近似网格。
Mod运行环境不随包分发。需自行使用服务器对应版本及依赖；未改写用户服务器配置。
完整报告 RailDepot01.html；独立旋转模型 RailDepot01_Model.html。
