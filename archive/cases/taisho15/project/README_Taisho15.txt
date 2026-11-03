Taisho15 · 櫻坂山溪町 · HAF 0.4

18 栋主建筑 + 山顶眺望亭、鸟居。先冻结地形，再选择低填挖地块。
河畔钟楼广场、两户侧后院、砂砾岸线、樱花群与云杉林。
钟面改为 5×5 固定装饰，用户已放宽先前 3×3 要求。

文件
  delivery/Taisho15.html：离线分类查看器与下载。
  delivery/Taisho15_World_1.21.1.zip：Java 1.21.1 存档。
  runs/O09：整街、18 栋单体、建设前地形 NBT、审计与空间数据。
  research/recipe_catalog_15.json：用途、体量、内饰配方和实际应用状态。
  research/skill_update_15.json：个人 Skill 0.4.4 已更新记录。

把 ZIP 内 Taisho15_World 放入 .minecraft/saves。
整街 240×76×208 格，世界偏移 [-120,62,-104]；具体出生点见 world_check.json。
建议直接使用存档；普通结构方块不适合整街尺寸，稀疏 NBT 不清除所有目标旧方块。

保留条件与边界
  当前输入是原创解析地形，并非 Minecraft 原生生成地形。
  地形冻结后，使用组团提示、填挖评分和有限候选放置18栋。
  保护山脊高程不变；建筑占地内和入口允许局部处理，桥面单列。
  全镇共享建筑配方，但用途及 L/T 翼不同。体量配方由设计选择，不是任意风格自动生成。
  同 seed 应得到完全相同 NBT，另一 seed 改变可选位置和植物/铺地。
  尚不是任意用户地形 NBT 自动求解器，也没有训练神经网络权重。
  山顶构筑物为日式屋檐眺望亭，与鸟居构成原创景观，不是实存寺庙复原。
  钟楼底厅可进入，上部装饰钟体没有楼梯；钟面不走时。
  车站短轨道仅为场景，桌椅及部分器物为方块造型。

验证
  整街和单体按实际最终 NBT 检查门、床、画、小物支撑、状态及通行。
  近似 0.6×1.8 人体、门视为开启；另有楼梯采样，不等同客户端碰撞。
  预览为实际 NBT 离线渲染，方块纹理、透明、实体和光传播有简化。
  尚未启动游戏，真实光照/碰撞/水更新及审美仍待实机和用户确认。
  部分单体几何未改，图片与单体审计仅在 NBT SHA-256 完全一致时复用。

复现
  Python 3.10+；安装 requirements.txt，绘图另需 matplotlib。Node.js 用于查看器逻辑验证。
  Linux Mesa/EGL libEGL.so.1、libGLESv2.so.2 用于离线渲染。
  不分发官方 Minecraft 资源。python src/fetch_vanilla_assets.py 获取固定 1.21.1 资源。
  python src/build_organic.py NEW 151145
  python src/audit_quarter.py NEW Taisho15
  python src/validate_locals.py NEW
  python src/render_quarter.py NEW full
  python src/export_quarter_world.py NEW delivery/Taisho15_World_O09
  python src/build_organic.py REPLAY 151145
  python src/build_organic.py ALT 151146
  python src/verify_quarter_repro.py NEW REPLAY ALT
  python src/terrain_plot.py NEW
  python src/report_quarter.py NEW
  node src/check_quarter.cjs NEW
  python src/package_quarter.py NEW
  构建器拒绝覆盖已有目录；若已有导出世界目录，请选新目录并同步报告路径。

来源
  Taisho14 原版本保留。Komorebi09 / T07 山溪版用于山体和组团关系对照。
  用户的两条新钟楼视频标题、作者与简介已读取，但播放器缓冲未取得可用教程画面。
  本轮钟楼为原创比例方案，不声称逐帧学习或教程复刻。
