广州中山纪念堂 HAF V2 / V2_r02
主线 HAF 0.2；图像研究案例；非任意建筑自动生成。
2 格/米；建筑地坪至顶端 97 格；整包 X/Y/Z = 236/108/280。
本包包括 .schem、稀疏 .nbt、10 个分片、材料与偏移表。
Sponge .schem 含显式空气；稀疏 NBT 不会清除原场地已有方块。
DataVersion 3955；建议在空白测试世界使用兼容导入器。
原点 Y 范围（现代主世界 -64..319 假设）：-64 至 212。
已做离线逐格回读/分片重组。游戏导入、照明、碰撞、通行均待验证。
场地为前广场和部分园林；未制作整个园区。屋檐、博古、雕像与室内座席含近似。
最终 NBT SHA-256: 81b06dce9e1ba323f1f34a522be08d2716e56fe942c2c7ab2aa40c55fdd66995

复跑（从 HAF_Guangzhou_Memorial 根目录）：
python3 tools/agent.py --case guangzhou_memorial --run NEW_RUN
python3 cases/guangzhou_memorial/src/validate_case.py NEW_RUN
python3 tools/render_building_case.py --case guangzhou_memorial --run NEW_RUN
python3 tools/package_building_case.py --case guangzhou_memorial --run NEW_RUN --name Guangzhou_Memorial_HAF_V2
PYTHONPATH=support/deps python3 -m unittest discover -s tests -v
V2 入口参数：cases/guangzhou_memorial/research/parameters_v2.json
V1 入口保留：python3 tools/agent.py --case guangzhou_memorial_v1 --run NEW_V1_RUN
源图、来源及构件证据：cases/guangzhou_memorial/research/
生成快照与不覆盖历史：cases/guangzhou_memorial/runs/
EGL 预览需要系统 EGL/OpenGL 和 NumPy/Pillow；所有已经生成的大图随包保留。
