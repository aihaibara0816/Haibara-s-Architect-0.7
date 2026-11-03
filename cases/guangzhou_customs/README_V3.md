# 广州新海关 HAF V3

本版交付 run：V3_r02。主引擎 HAF 0.2；case_version 0.3.0 是建筑案例版本。

V2的单侧后伸翼已被用户否定。V3依据用户标注的斜卫星图、既有照片和已保存的OSM粗轮廓，采用居中倒T裙楼。各高度层分别解释，不把高层屋顶的投影位移直接当成地面轮廓。具体尺寸与后门拱券位置仍待实测证据及用户审阅。

## 交付内容

- 160,616个非空气方块，126×148×116包围盒，地面y4，137格研究高度包络。
- 正交俯视、3层水平剖切、四个45°日夜全景和局部，共27个视角；与V2共用相机。
- HTML可在V1/V2基线与V3间对照，包含原图与反馈表单。
- 完整Sponge v3 schem、稀疏NBT、3个分区NBT、偏移表、材料与方块状态表。
- 23项案例检查、23项共享测试通过，独立回读/分区合并相同。技术验证不等于建筑还原度通过。

## 修改范围

1. 前横段 [13,72,114,87]，后段 [25,16,102,72]；主体101格宽收至77格，左右各退12格。
2. 塔身中央后墙z44→52，下段27×32→27×24，与上段一致。钟冠、针尖实际方块不变。
3. 两座屋顶玻璃房移至后部承托屋面；绿灰色是配色代理，不代表已证实草坪/铜材。
4. 三拱入口移至后部轴线末端；形式有照片依据，位置为本轮推定。
5. 旧墙体消失时不再生成悬空窗；中央凹槽用5列一格窄窗维持对称节奏。
6. 保留V1/V2源码、参数、相机、run和HAF共享代码。V3是新增案例适配器；当前案例入口指向V3，旧入口可直接重跑。

## 重跑

Python3.12，依赖见requirements-case.txt；Linux EGL用于预览。先在工程根目录执行：

```bash
python3 tools/agent.py --case guangzhou_customs --run MY_V3_RUN
python3 cases/guangzhou_customs/src/validate_v3.py MY_V3_RUN
python3 tools/render_building_case.py --case guangzhou_customs --run MY_V3_RUN
python3 tools/package_building_case.py --case guangzhou_customs --run MY_V3_RUN --name Customs_V3
```

显式入口为 `cases/guangzhou_customs/src/build_v3.py`，参数为 `params_v3.json`。运行名称不可复用。V1仍可调用build_case.py，V2调用build_v2.py。旧run不会被覆盖。

报告脚本review_v3.py默认读取V3_r02；中文PNG图板使用环境变量HAF_CJK_FONT指定Noto Sans CJK SC等字体。字体不随本源码打包，建筑生成不依赖字体。PNG预览已包含在源码包。

## 导入条件

DataVersion 3955。完整schem含空气，稀疏NBT不清除未记录位置。请在空白区域导入，避免V2的单侧突出残留。模块按module_offsets.csv偏移，相同原点、无额外旋转。

完整包围盒高148，放置时原点Y+148不能超过世界最高Y排他上界，同时检查世界最低Y。若上界320，则原点Y≤172；本地y4是建筑地面。模块切片不会增加世界高度。

未进行Minecraft客户端、导入器兼容、碰撞、植物更新和实际照明测试。夜景为稳定随机的暖冷窗灯游戏设计。没有可靠实景夜照，不宣称灯位复原。

## 反馈与限制

研究记录 `research/v3/feedback_and_decisions.json` 保存用户反馈及每项参数消费者。V2历史记录不改写，V3明确记录其裙楼形态被否定。11张历史参考照片及4张用户输入包含近重复/模型截图，不等于15个独立实景。

倒T拓扑得到用户标注及OSM粗轮廓支持；具体边长、轴向、中央楼体比例及后门布置仍是当前假设。东北拍摄方向没有被当成已测方位。103/114/137米来源口径冲突仍保留。四向标签均为模型坐标。

HTML反馈可本地保存并导出JSON，包含run和NBT哈希。只有新的同部位反馈及证据才能关闭还原度问题。
