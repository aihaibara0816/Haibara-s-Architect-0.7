# 0.7 新归档入口

当前完整图鉴、图片与逐案例下载移至 [案例与研究图鉴](archive07.md)。新增内饰、植物装饰、工业、铁路、街区，保留失败与未关闭项。下文为 0.6 发布时的学习说明；某些“未附成品”已由 0.7 补上，以新图鉴及 [覆盖清单](archive-coverage.md) 为准。


# 案例学习指南

HAF 的案例是显式研究和代码适配的结果。建议沿着“参数 → 构件函数 → 最终 NBT → 检查 → 已知问题”阅读。每个案例保留具体建筑 run，引擎升级不会自动改写它。

所有路径相对仓库根目录，可下载文件只链接本仓库成员。完整字段与 SHA-256 见 [case-index.json](case-index.json)，历代目标见 [版本演进](version-history.md)。没有附齐的外部分支明确留空。

## 建议的阅读顺序

1. **深圳报业／周大福**：立面内外层次、稳定灯光和有限方块状态。
2. **纪念堂／广州南站**：旧失败怎样变成针对性的承托、净空与拼合检查。
3. **大本钟／南山塔／珠江帝景**：古典、地形和居住类型为何需要不同适配器。
4. **市民服务中心**：用途、家具、吊顶、光场与园林怎样联动，冻结输入为何要保留。

## 每个案例目录怎样读

| 文件 | 用途 | 不代表什么 |
|---|---|---|
| 参数 JSON | 已采用的尺寸、种子、范围和部分构造 | 不保证全部细节已经参数化 |
| 生成脚本 | 将本案例的约束写成方块 | 换一个建筑名称就能通用 |
| runs/<run>/building.nbt | 已归档的实际输出 | 已在游戏导入验收 |
| manifest / build_report | 原始版本、尺寸、数量、哈希和范围 | 历史版本随当前发布而变更 |
| 构件、窗与房间记录 | 将结果定位回构件和功能区 | 隐藏空间来自实测 |
| 验证 JSON | 特定检查的结果与失败样点 | 建筑还原度评分 |
| review/previews | 最终 NBT 的离线图或相机记录 | 游戏截图；只有元数据不代表图片仍在 |

完整工程要保留共享 hafusion、support 和相关依赖；单独拿走一个脚本通常不能运行。旧预览器依赖 Linux EGL/Mesa，不能据历史报告声称已适配 Windows。来源与许可见 [ATTRIBUTION.md](../ATTRIBUTION.md)。

## 0.1：广州塔的历史融合路径

建筑 run 为 **V6_r01 → V6_r02**，引擎为 **HAFusion 0.1**。重点是开敞格构、核心、环梁、功能玻璃层、塔冠和多层场地的接口，以及几何和材质阶段的独立缓存。

可读源码：[pipeline.py](../hafusion/pipeline.py)、[cache.py](../hafusion/cache.py)、[evidence.py](../hafusion/evidence.py)。历史复验：[replay_validation.json](../history/canton/reports/replay_validation.json)。

**文件状态：V6_r02 最终 NBT 与完整原输入尚未附齐。** 不提供虚构公开路径，也不推荐直接运行缺少冻结输入的旧 tools/build.py。补齐后仍应核对哈希。

学习问题：移动核心时，哪些灯位应该相对移动？哪些广场和外框坐标要保持？材质替换为何不能改变方块几何？格构粗细、最低截面拟合、整体视觉反馈和游戏通行仍未完全闭合。

## 0.2–0.4：已保留源码和输出的案例

“纳入发布”指主线整合范围；原始生成引擎按各 run 报告独立保留。

| 案例 | 纳入发布 | 建筑 run | 原始输出引擎标记 |
|---|---|---|---|
| 深圳特区报业大厦 | 0.2 / 0.3 / 0.4 | `V2` | HAF mainline + 深圳案例适配器 0.2.0 |
| 广州周大福金融中心 | 0.2 / 0.3 / 0.4 | `V1` | 原报告未给统一HAF版本；保留案例版本 |
| 首尔南山塔与公园 | 0.3 / 0.4 | `V1_r02` | HAF 0.2.0 |
| 伊丽莎白塔（大本钟） | 0.3 / 0.4 | `V1_r02` | HAF 0.2.0 |
| 白金汉宫 | 0.3 / 0.4 | `V1_r02` | HAF 0.2.0 |
| 南山云科技大厦 | 0.3 / 0.4 | `V2_r01` | HAF 0.2.0 |
| 广州新海关大厦 | 0.3 / 0.4 | `V3_r02` | HAF 0.2.0 |
| 广州中山纪念堂 | 0.3 / 0.4 | `V2_r02` | HAF 0.2.0 |
| 广州珠江帝景苑 | 0.3 / 0.4 | `V1_r03` | HAF 0.2.0 |
| 广州南站 | 0.3 / 0.4 | `V1_r02` | HAF 0.2.0 |
| 市民服务中心（原创） | 0.4 | `v03_r16_ceiling_landscape` | HAF 0.3.0 |

### 深圳特区报业大厦 · `shenzhen_press`

**类型：**现代办公塔／水平幕墙。**案例版本：**V2。

重点观察：横向幕墙、楼板端与窗后层的前后次序；正背面围护、屋顶体块和入口开口；稳定房间ID的暖冷窗灯。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/shenzhen_press/src/build_case.py) |
| 参数入口 | [参数](../cases/shenzhen_press/research/parameters.json) |
| 归档 NBT | [V2/building.nbt](../cases/shenzhen_press/runs/V2/building.nbt) |
| SHA-256 | `e1aefdd2383fed8747c69c5806ab5cd367d7d91eeaf0092cd77c1a1f25176e20` |
| 检查与经验 | [build_case.py](../cases/shenzhen_press/src/build_case.py) · [README.md](../learning/README.md) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**先锁形体与手性，再借鉴细部；为正背面、屋顶、裙楼分别验收；随机只作用于允许的灯位和陈设位。

**还没解决：**背面模式及办公室仍估算；不能把伪内饰宣称真实可进入办公室。

**当前反馈：**用户反馈明显改善；非整栋测绘/游戏验收；游戏状态仍为 pending。

建议练习：只改灯光种子，在新 run 检查非灯光几何差分；新增稳定房间 ID 后，核对旧房间灯光决定不变。旧脚本也会写案例研究日志，练习应使用工作副本。

### 广州周大福金融中心 · `guangzhou_ctf`

**类型：**超高层／竖向幕墙。**案例版本：**V1。

重点观察：竖梃、玻璃、内背景三层关系；弧面量化转角与薄构件状态；固定冠灯、普通窗灯和局部障碍灯样板的区别。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/guangzhou_ctf/src/build_case.py) |
| 参数入口 | [参数](../cases/guangzhou_ctf/research/parameters.json) |
| 归档 NBT | [V1/building.nbt](../cases/guangzhou_ctf/runs/V1/building.nbt) |
| SHA-256 | `58db77a6499aab981ccf8efdd048c3ce80b9383053713059ca61010af7afcc96` |
| 检查与经验 | [README.md](../cases/guangzhou_ctf/README.md) · [vertical_facade_ctf_v1.md](../learning/vertical_facade_ctf_v1.md) · [ctf_night_detail_study.md](../learning/ctf_night_detail_study.md) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**两相反方向检查斜顶；固定夜景灯带与随机窗灯分离；航空灯先算尺寸，3×3格在1:2下宽6米过大。

**还没解决：**细节v2是局部样板，不是完整V2；SU未取得；真实夜景排布及红色光/闪烁未实现。

**复跑依赖：**本地发布基线是V1；V1_r04/V1_r05另存。0.5索引记录整栋V1_r05，不能把V1的NBT哈希当作r05。 Detail V2是局部研究，不是整栋V2。

**当前反馈：**竖向体系获正向反馈；斜顶、夜景及细节仍待改；游戏状态仍为 pending。

建议练习：截取转角，分别看竖梃、玻璃与内背景。对照 V1、V1_r05 和 facade_sample_v2 的范围，不把局部灯体样板称为整栋夜景完成。

### 首尔南山塔与公园 · `namsan_tower`

**类型：**观景塔／山地公园。**案例版本：**V1_r02。

重点观察：粗DEM、人工台地和步道如何衔接；设备环留空与观景舱围护；稀疏场地的实际占用预算。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/namsan_tower/src/build_case.py) |
| 参数入口 | [参数](../cases/namsan_tower/params.json) |
| 归档 NBT | [V1_r02/building.nbt](../cases/namsan_tower/runs/V1_r02/building.nbt) |
| SHA-256 | `828086a50f2193f3020b8cb53497e07ee4ef731b3d0f80c22f61db3f086f9da6` |
| 检查与经验 | [namsan_site_v1.md](../learning/namsan_site_v1.md) · [params.json](../cases/namsan_tower/params.json) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**基座先定承托面并渐变接坡；楼板止于核心内缘；分别限制包围体积与实际占用量。

**还没解决：**细部高差/植被估算，真实RGB投光及游戏坡道未验证。

**复跑依赖：**生成读取research/terrain/osm.xml与dem_grid.json；保留OpenStreetMap署名、ODbL记录及SRTM/OpenTopoData来源。

**当前反馈：**用户未作整体验收；不能因转入下一案例记pass；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 伊丽莎白塔（大本钟） · `elizabeth_tower`

**类型：**古典钟塔。**案例版本：**V1_r02。

重点观察：钟盘、钟室、灯笼层和尖顶比例；厚墙窗洞、楼梯与半砖线脚；近似材质和真实资源包纹理的区别。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/elizabeth_tower/src/build_case.py) |
| 参数入口 | [参数](../cases/elizabeth_tower/params.json) |
| 归档 NBT | [V1_r02/building.nbt](../cases/elizabeth_tower/runs/V1_r02/building.nbt) |
| SHA-256 | `88a187dcade9687223e9e80db62c832256db1f4d796ba292c5b46a6c4afd758f` |
| 检查与经验 | [london_western_v1.json](../learning/london_western_v1.json) · [build_case.py](../cases/elizabeth_tower/src/build_case.py) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**固定建筑身份与范围；先看钟盘/钟室/尖顶关系，再加细节；材料ID通过不等于纹理表现通过。

**还没解决：**仅带截断的议会邻翼；钟针静态，钟室/楼梯可玩性待测，未补真实资源包纹理。

**当前反馈：**用户提出材质纹理不足；未关闭；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 白金汉宫 · `buckingham_palace`

**类型：**古典宫殿／内院。**案例版本：**V1_r02。

重点观察：正面开间节奏、侧翼和内院；正背面不同的凸出及窗型；地图平面与估算屋顶高度的边界。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/buckingham_palace/src/build_case.py) |
| 参数入口 | [参数](../cases/buckingham_palace/params.json) |
| 归档 NBT | [V1_r02/building.nbt](../cases/buckingham_palace/runs/V1_r02/building.nbt) |
| SHA-256 | `2d33529237c74937e6212037f40bb97facc645b87af153d97d4941bf85207a33` |
| 检查与经验 | [london_western_v1.json](../learning/london_western_v1.json) · [build_case.py](../cases/buckingham_palace/src/build_case.py) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**地图辅助平面，不供应高度；正背面各自研究；景观不能遮住本轮需要评审的主建筑。

**还没解决：**只做指定建筑群与花园边缘，不是775房间全还原；内饰和园景多为示意。

**复跑依赖：**生成读取research/aligned_plan.json，来自OSM平面；保留OpenStreetMap署名与ODbL记录。

**当前反馈：**纹理感反馈仍开放；无整栋认可记录；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 南山云科技大厦 · `nanshan_cloud`

**类型：**错动办公塔／阶梯露台。**案例版本：**V2_r01。

重点观察：露台宽度／塔宽和挑深的比例；三塔错动与顶层重复节奏；局部修改时保持主体高度和同机位。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/nanshan_cloud/src/build_case.py) |
| 参数入口 | [参数](../cases/nanshan_cloud/params.json) |
| 归档 NBT | [V2_r01/building.nbt](../cases/nanshan_cloud/runs/V2_r01/building.nbt) |
| SHA-256 | `11cdb08cb2d0202fcb802ae0bd91648e523a74d5599349d5fe56b223bd288425` |
| 检查与经验 | [nanshan_cloud_v2.json](../learning/nanshan_cloud_v2.json) · [build_case.py](../cases/nanshan_cloud/src/build_case.py) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**先量露台/塔宽比、挑深和顶层重复节奏；局部修改锁定其他体块，四个45°相机同框同尺度。

**还没解决：**后部塔体和平面未测绘；当地理北未标定时四向只是模型坐标。

**当前反馈：**露台比例经反馈缩小；未收到新版明确验收；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 广州新海关大厦 · `guangzhou_customs`

**类型：**纪念性办公楼／裙楼。**案例版本：**V3_r02。

重点观察：真俯视和分层轮廓；反T形裙楼、主楼和钟楼比例；形体返工后独立复核保留灯位。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/guangzhou_customs/src/build_v3.py) |
| 参数入口 | [参数](../cases/guangzhou_customs/params_v3.json) |
| 归档 NBT | [V3_r02/building.nbt](../cases/guangzhou_customs/runs/V3_r02/building.nbt) |
| SHA-256 | `56a665db8c46fa364c6c0ce7c8c769ffb051f91335ed81aa7863a2e42f312224` |
| 检查与经验 | [README_V3.md](../cases/guangzhou_customs/README_V3.md) · [customs_v3_user_acceptance.json](../learning/customs_v3_user_acceptance.json) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**强制真俯视+分层轮廓；对称只能作为待证假设，不能由建筑类型直接决定；返工单独保护灯光。

**还没解决：**钟楼/大堂照明未补；137格是研究包络而非解决了所有高度来源冲突。

**当前反馈：**形体获用户认可；大堂裙楼和钟楼灯光needs_revision；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 广州中山纪念堂 · `guangzhou_memorial`

**类型：**中式纪念建筑／复杂屋顶。**案例版本：**V2_r02。

重点观察：完整柱脚承托和入口地坪；复杂坡屋顶的离散接缝；用旧失败版本验证修复检查。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/guangzhou_memorial/src/build_case_v2.py) |
| 参数入口 | [参数](../cases/guangzhou_memorial/research/parameters_v2.json) |
| 归档 NBT | [V2_r02/building.nbt](../cases/guangzhou_memorial/runs/V2_r02/building.nbt) |
| SHA-256 | `81b06dce9e1ba323f1f34a522be08d2716e56fe942c2c7ab2aa40c55fdd66995` |
| 检查与经验 | [guangzhou_memorial_v2.json](../learning/guangzhou_memorial_v2.json) · [validate_repairs.py](../cases/guangzhou_memorial/src/validate_repairs.py) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**承托要查完整脚印；入口查地坪+净空；共享屋面边界按离散方块验收；旧失败版本必须能触发新检查。

**还没解决：**8项修复检查不等于8栋测试；复杂屋面仍案例几何；礼堂示意布局和游戏碰撞待验。

**当前反馈：**V2离线几何修复已验证；用户视觉验收待补；游戏状态仍为 pending。

建议练习：先看 V1_r03 的失败，再看 V2_r02/repair_validation.json；找到检查坐标与修复构件的对应关系。检查必须能检出旧问题。

### 广州珠江帝景苑 · `zhujiang_dijing`

**类型：**城市住宅楼组。**案例版本：**V1_r03。

重点观察：窗后开口与阳台进深；水体、玻璃片及栏杆邻接；楼组范围、屋顶柱脚和夜景。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/zhujiang_dijing/src/build_case.py) |
| 参数入口 | [参数](../cases/zhujiang_dijing/research/parameters.json) |
| 归档 NBT | [V1_r03/building.nbt](../cases/zhujiang_dijing/runs/V1_r03/building.nbt) |
| SHA-256 | `47d8dac25bda3241ebe47c2504259cc9cc862241d0a94e0e71d6844a8d871855` |
| 检查与经验 | [zhujiang_dijing_v1.json](../learning/zhujiang_dijing_v1.json) · [validation.json](../cases/zhujiang_dijing/runs/V1_r03/validation.json) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**窗透明性与栏杆连接分开检查；水不是玻璃片/栏杆的实体邻块；HTML内嵌且短文件名，单独试开下载。

**还没解决：**不代表整个小区；真实楼栋身份、绿化分布与户型细节待核；夜景远景偏弱。

**当前反馈：**技术问题修过；用户主要反馈下载失败，未有视觉验收；游戏状态仍为 pending。

建议练习：从参数选一个明确尺寸，找到消费它的构件函数，再从最终 NBT 的尺寸或归属记录验证；把估算、程序检查和人工视觉判断分开。

### 广州南站 · `guangzhou_south`

**类型：**大型交通建筑／大跨屋盖。**案例版本：**V1_r02。

重点观察：大跨主次体量与上下层空间；门洞开空后竖梃再次阻挡的拼合问题；大网格原子写入与固定相机。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/guangzhou_south/src/build_case.py) |
| 参数入口 | [参数](../cases/guangzhou_south/research/parameters.json) |
| 归档 NBT | [V1_r02/building.nbt](../cases/guangzhou_south/runs/V1_r02/building.nbt) |
| SHA-256 | `d1be52d98763c1337d9a9ecee53d82bac9a8d6ed9842ee00ac89d32d4f1be245` |
| 检查与经验 | [guangzhou_south_v1.json](../learning/guangzhou_south_v1.json) · [validate_case.py](../cases/guangzhou_south/src/validate_case.py) · [test_mesh_write.py](../tests/test_mesh_write.py) |

**预览状态：**主线恢复包未附本例最终 PNG。已有相机或 render_report 只是历史记录，不作为可查看图片。

**得到的规则：**入口契约必须在最终NBT检查；原子写入+网格字节长度+图像读回保护大场景预览；主次体量优先于重复细节密度。

**还没解决：**轨道和列车装饰性；ETFE/柱网/广场估算；采光脊文字尺寸与含端部包络未完全闭合；游戏未测。

**当前反馈：**用户认可当前体量下已足够；细节限制继续保留；游戏状态仍为 pending。

建议练习：比较 V1_r01 与 V1_r02 入口样点。分别检查“玻璃开洞正确”和“最终拼合后门洞仍空”；再检查固定灯位是否因修形丢失。

### 市民服务中心（原创） · `civic_center`

**类型：**原创公共服务建筑／功能内饰与园林。**案例版本：**V0.3.3 / v03_r16_ceiling_landscape。

重点观察：用途分区、成组家具和公共休息空间；上层地板／下层吊顶的两格关系及净高例外；整片园林、全宽路径、嵌灯与窗组保护。

| 文件 | 仓库位置 |
|---|---|
| 生成入口 | [源码](../cases/civic_center/revise_ceiling_landscape.py) |
| 参数入口 | [参数](../cases/civic_center/parameters.json) |
| 归档 NBT | [v03_r16_ceiling_landscape/building.nbt](../cases/civic_center/runs/v03_r16_ceiling_landscape/building.nbt) |
| SHA-256 | `5facdc6ad0ba108d9ff34c7e83d284836e449f10ab4786e277e3633bc8a84b9c` |
| 检查与经验 | [STATE.md](../cases/civic_center/STATE.md) · [validation.json](../cases/civic_center/runs/v03_r16_ceiling_landscape/validation.json) · [interior_validation.json](../cases/civic_center/runs/v03_r16_ceiling_landscape/interior_validation.json) · [ceiling_landscape_validation.json](../cases/civic_center/runs/v03_r16_ceiling_landscape/ceiling_landscape_validation.json) |

**已附的同源预览：**[se_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/se_day.png) · [sw_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/sw_day.png) · [ne_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/ne_day.png) · [nw_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/nw_day.png) · [top_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/top_day.png) · [entrance_garden_day](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/entrance_garden_day.png) · [ceiling_eye](../cases/civic_center/review/previews/v03_r16_ceiling_landscape/ceiling_eye.png)。它们采用近似材质和离线光照。

**得到的规则：**保留批准窗口与标高；先动线和净空，再功能家具、灯具及植物；检查整条路径宽度。

**还没解决：**真实游戏碰撞/通行/照明未测；内饰模块迁移至第二建筑未完成。

**复跑依赖：**生成R16修订读取R13冻结NBT、构件归属、窗与房间记录；不支持通用--params。 内饰验收还读取R06；吊顶/照明对比读取R13和R16的离线光场。 原run manifest保留HAF 0.3.0，不改写成0.4。

**当前反馈：**可以的；授权归纳升级 HAF0.4。不是游戏验收。；游戏状态仍为 pending。

建议练习：比较 R13/R16 普通楼板截面，再看楼梯和桥下例外；随后看 R14/R15 路径失败，理解植物为何不能只避开中心线。

## 进行一次新练习

先复制工作目录，安装当前工程声明的依赖，再使用新的 run 名：

```bash
python tools/agent.py --version
python tools/agent.py --catalog
python tools/agent.py --case guangzhou_memorial --run STUDY_NEW_01
python tools/agent.py --case guangzhou_memorial --run STUDY_NEW_01 --review
```

共享 --review 检查文件、已声明几何样点和视图元数据。缺契约或缺视图应保留待检查；它不能代替专用检查，也不能凭历史记录判断当前 PNG 是否存在。

具有 Linux EGL/Mesa 环境时，可以从新 NBT 生成公共入口支持的视图：

```bash
python tools/render_building_case.py --case guangzhou_memorial --run STUDY_NEW_01
```

输出到 cases/guangzhou_memorial/review/previews/STUDY_NEW_01/。周大福与南山塔有专用预览入口，见索引的 render_command。深圳旧包没有可直接套用的统一相机配置；不能照抄另一例相机就声称历史同机位对照。

历史 build_case_snapshot.py 记录某次输出的源码。当前案例代码可能继续演进，因此“生成新 run”和“逐字节重放旧 run”是两项任务。本文没有承诺所有历史结果可由当前代码直接重现。

## 0.5：外部分支作为研究案例阅读

以下条目进入研究总库，没有因此全部接入主线 CLI。本清单未附齐各分支源码/NBT，不提供仅作者可访问的下载链接。

| 案例 / 建筑版本 | 类型与细节 | 仍需检查 |
|---|---|---|
| 广州琶洲微信总部 · V3b / v3b_04_final | 材质分色与几何分层分开对照；连接型方块必须检查实际邻居。 | 旧主表“尚未重做幕墙”已过时；V3b 尚无用户整栋认可，裙楼、大堂、峡谷与背面推断仍待核验。 |
| 广州国际金融中心（西塔） · V1_r02 | 固定结构后再改变窗后活动；局部变更以差分证明。 | 731 个窗后家具样本不是完整房间；不是 103 层可行走内饰；原分支依赖 HAF 0.3。 |
| 上海东方明珠 · v1_r04_final | 先读远景剪影，再检查支撑与球舱，不让玻璃掩盖骨架。 | 细三角幕墙、裙楼、真实内饰与彩色泛光仍不完整。 |
| 上海环球金融中心 · v1_r02_final | 开洞形状、侧墙厚度与顶部透空要联合检查。 | 当前视觉仍待修订；21 项检查不能替代建筑还原评价。 |
| 大阪城希尔顿逸林酒店 · v1_r04_final | 按朝向建立不同立面；底面装饰必须带支撑关系。 | 未生成 373 间真实客房；河岸仅为场景示意，部分参数仍为常量。 |
| 广岛 JP 大厦 · v1_r04_final | 建筑身份先校正，再分层研究商业基座、标准层与悬挑。 | 商业内饰未完整建成；手工研究与案例适配仍是主要方式。 |
| 广州中信广场 · V2_r02 | 普通窗按开间/楼层组分布；入口、商业、冠部和标识灯独立控制。 | -44.4% 是灯方块数量变化，非照度变化；示范楼层不能称为 80 层真实办公室。 |
| 千禧年代住区 · V3_r01 | 墙面近色穿插与修补斑块是两种独立风格；本案采用非成片散点。 | 28 项回读检查与 4,750 格限定差分已留档；家具可用性、玩家碰撞仍待游戏验证。 |
| 榕荫里 · 20 栋城中村 · V4_r02 | 边界、进深、街巷和地形先确定；加建与栏窗随住户/楼栋形成差异。 | 30 项离线检查与 101 张楼层图；V3 方向获认可，V4 最终版尚未见用户验收。 |
| 田埂里 · 13 栋初版 · V4 | 居住、旧化、建造阶段分开记录；房屋与田地是相互关联的生产场景。 | 作为田埂里同一案例家族的前代保留，不计作独立泛化建筑。 |
| 田埂里 · 18 栋田园深化 · P4_B4 | 先保证水路/田埂/入口/净空，再按功能补农具、果树、竹与休耕地；田内下沉一格保留田埂层次。 | 俯视仍偏矩形分区，边界树列均匀；共用随机数流可能串扰。16,649 格水连通仅是几何拓扑，未实测水更新。 |

琶洲还保留早期 HA03/HAF 两个基线 NBT，用来理解“共用参数产生相同输出”的执行一致性比较；它们不是 V3b。田埂里 13 栋与 18 栋属于同一家族的前后代，不算两份独立泛化验证。

## 来源与发布范围

保留来源、日期、误差和未验事项。代码许可不能自动覆盖照片、模型或地图数据。本学习包不包含原始研究照片、SKP 模型及 Linux support/deps 环境包；NBT 和同源预览也不改变原资料权利归属。

南山塔 OSM XML 自带 OpenStreetMap contributors 署名与 ODbL 1.0 声明；白金汉宫平面对齐数据来源相同。相关记录随输入保留。SRTM/OpenTopoData 样本约30米原始分辨率，不能作为精细台地测绘。PlanCraft 和字体各自的许可记录应与对应文件一同保留。

导入游戏前核对目标版本、尺寸、原点与世界高度。稀疏 NBT 不清除未写入位置的旧地形。离线图、文件回读与几何通过，不能替代游戏中的注册、碰撞、通行、光照和水行为检查。
