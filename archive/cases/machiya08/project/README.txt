日和小食 Machiya08 / HAF 0.4 / 最终 M08

原创老式日式町屋单栋：两层木构，首层居酒屋（三席吧台+两组四人桌席）、后厨、卫浴；
二楼双床卧室、衣柜、茶席、沙发和书桌。后侧小庭院含竹株、低盆、水钵和木平台。
主体约17×16格；按Minecraft家具尺度折中，不是现实町屋测绘，非Freedom逐格复刻。

快速体验：Machiya08_World_1.21.1.zip 解压，将 Machiya08_1.21.1 放进 saves。
Java 1.21.1，创造模式，无必需模组。出生点 -1 65 9，朝北进入店铺。
床、熔炉、储物、告示牌采用原版实体；座位、纸门风格、暖帘、席面、坐便和杯具是造型。
主入口改为三格宽开放店口，没有打烊闭合机制。其余七樘原版门保留，未添加推拉门机制。旗帜和玻璃只近似障子/暖帘，杯具以花盆代指。

文件：
runs/M08/Machiya08.nbt：最终结构，含空气和实体。
runs/M08/spec.json、design_contract.json：空间/外立面、门、楼梯、灯、植物和使用面。
runs/M08/{audit,stair_check,world_check,random_check,revision_check,report_check}.json：检查报告。
review/previews/M08：42张原始PNG、机位、同源哈希；exploded.svg为结构楼板示意。
input/JapanDetail01_record.json：此前日式研究记录。
input/Freedom_frontage_research.json：本次查看 #80 公开展示静帧（视频未播放成功），并复看 #104 的00:12、00:25展示片段。没有完整观看教程或推断未见的内饰。
不打包第三方截图、视频或其参考图片。
history：保留 M01–M07 过程和此前源码；M06 获得“能用”反馈，但外立面/屋顶需要返工。
M08 为营业门面与屋顶返工，未经实机和新版审美验收。历史记录不是当前交付世界。

渲染与检查边界：
原版1.21.1静态模型和纹理离线渲染，不是Minecraft截图；床/旗帜/告示牌外形近似，
告示牌字样写入NBT但未完整画在离线图上。生物群系染色、动态纹理、UV与光照不完整。
门视作打开，0.6×1.8身体使用近似几何检测；楼梯按0.125格采样。
NBT和MCA方块/实体回读一致，尚未运行客户端；游戏碰撞、交互和审美仍待确认。
旧日式整镇内饰的用户否定反馈不因这个新案例通过脚本而关闭。

复现（Python3.12 + requirements.txt）：
  python src/build_machiya.py NewRun --seed 1145
  python src/audit_machiya.py NewRun
  python src/stair_check.py NewRun
  python src/frontage_check.py NewRun
  python src/world_machiya.py NewRun /ABS/NEW_WORLD_DIRECTORY
  python src/diagram_machiya.py NewRun

每个run和世界目录必须是新的，脚本不覆盖旧NBT。
如要渲染：系统需EGL/OpenGL。原版客户端JAR与模型纹理不随包分发。
  python src/fetch_vanilla_assets.py
该脚本从Mojang官方来源取1.21.1并校验 assets/vanilla_source.json 中SHA1。
默认资产路径 assets/minecraft-source/assets/minecraft；可设环境变量 ROOM06_MC_ASSETS
指向已有且经过校验的 assets/minecraft（变量名沿用渲染器历史兼容接口）。
  python src/render_machiya.py NewRun

随机对照：
  python src/build_machiya.py Replay --seed 1145
  python src/build_machiya.py SeedB --seed 2718
  python src/random_check.py NewRun Replay SeedB
random_check也需要原版模型资产，用于已采用状态的模型解析验证。
生成world_check、random_check和render_report以后再做HTML：
  python src/report_machiya.py NewRun /ABS/Machiya08.html

专用适配器从布局到摆放均为原创显式代码，不是通用建筑AI，也没有训练模型权重。

M04首层返工：楼道3桶+楼梯下2桶、三幅真实原版画、西侧四人卡座、东侧四人桌、吧台3席。补备餐柜、厨房两侧地柜与壁架、布巾、杯瓶造型。容器内容为空。
画实体采用Java 1.21.1的variant/facing/TileXYZ/Pos保存字段；写入结构entities和世界entities区域，确定性UUID；离线回读3个实体载荷完全一致。画的生存判定与实际交互尚待客户端确认。
42张当前预览另附8张历史对照（M03三张、M04一张、M06四张）。保留M03首层needs_revision记录，新版审美pending。

M06楼梯下：进店左侧楼梯门内，右侧为半开放备货角。新增后侧低柜、侧柜、薄活板门壁架、短隔板和有支撑的灯笼；实际新增3个取物点。保留原楼梯与平台。M05是厚壁架试验，M06压薄壁架并调整近景。

M08门面与屋顶：左侧开放窗台、中段三格宽退入入口、右侧客席开窗、东侧短柜台；上层窄窗与长窗分组、薄格扇、装饰窗沿和两端盆栽。主切妻叠一个原创小前山墙，区分窗檐、入口檐与侧面短檐，补屋脊收边和木构端头。候位凳、菜单与花盆分组，局部上层檐下灯。
保持室内家具、楼梯、楼梯下备货角和三幅画；入口内侧框架是唯一室内交界改动。revision_check 记录 M06 到 M08 的逐格变化及保护范围。最终回读修正侧招牌与椽端重叠，验证方块实体类型与实际方块一致。
上层窗沿不能作为阳台行走，小前山墙没有可进入阁楼。随机性仅在植物组种类与竹高，布局为本案例原创设计。

HTML离线检查（可选 Node.js 18+）：
  python src/check_report.py NewRun /ABS/Machiya08.html /ABS/QA_TEMP
  node src/check_report_dom.cjs /ABS/QA_TEMP runs/NewRun/report_check.json
图像解码、下载载荷和DOM交互检查不等同完整浏览器验收。
