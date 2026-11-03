Room06 / 榕角里 · 单间试住
2026-10-30 / HAF 0.4 / 内饰与植被规则 0.4.3

最终几何：runs/R03/Room06.nbt，种子1145。
这是从零布置的独立单间试验，沿用城中村材料方向；不是对 Corner01 整楼的修改。
室内8×8格含独卫、3格净高。尺度按Minecraft原版家具与通行量化，不把64格直接宣传成现实紧凑出租屋的面积。
区域：双床拼接睡眠、木框双人沙发、窗边书桌、独卫、洗涤/烹饪/备餐/储物、入口柜。
植物：沙发端部原生竹、桌边原版盆栽、入口柜面盆栽。换种子时门、主家具、光源保持固定。

使用：另行提供的Room06_World_1.21.1.zip解压后，把Room06_1.21.1文件夹放入saves。出生点0 65 5，朝北进入。创造模式，无必需模组。
离线检查：15个声明接近点、2组门扇/门框、床头床尾、10个方块实体、盆栽承托、NBT到世界MCA逐格回读、固定种子复跑通过。
未运行Minecraft客户端。真实碰撞、开关门、光照重算、床/容器交互、用户审美仍pending。
沙发、椅子、坐便、淋浴、镜面、空调是造型；没有原版坐下动作。花盆也用于符号化杯具，空容器并无预设内容。

复跑（Python 3.12；始终使用新run目录）：
python -m pip install numpy pillow nbtlib
python src/build_room.py NewRun --seed 1145
python src/audit_room.py NewRun
python src/fetch_vanilla_assets.py
python src/render_room.py NewRun
python src/world_room.py NewRun ../Room06_NewWorld
渲染另外需要Linux EGL/Mesa。脚本从Mojang官方来源获取固定1.21.1的客户端模型/材质并检查SHA1；本包不含客户端JAR、原始模型或贴图。

预览边界：原版JSON方块模型和静态纹理采样 + 离线EGL照明。床与旗帜仍用近似盒体，床顶有识别色标。生物群系染色、UV锁定、元素缩放、加权变体和动画并非完整客户端实现。预览不能作为实机截图。
R03_NoPlants / R03_SeedB是同壳、同家具的植物对照，R03_Replay用于确定性检查。历史R01/R02的通行问题已经修正；不随项目包交付这些过期样本。
src/build.py、src/render.py、src/audit.py为恢复的上轮四展间来源；本案例入口明确为带_room的脚本。

材质和模型归Mojang/Microsoft所有。预览仅用于本项目的方块布置审阅。
