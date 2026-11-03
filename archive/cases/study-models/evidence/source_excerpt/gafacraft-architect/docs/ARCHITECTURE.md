# 架构与边界

`packet.json` 是证据与研究结论，`construction_overlay.json` 是显式施工决策；`packet_adapter.py` 合并为 `BuildingSpec v0.1`。没有施工决策时只能输出研究上下文。

1. `spec_loader.py`：JSON Schema 和语义检查，拒绝重复键、非有限数值、无证据确认、比例冲突、世界高度超界、构件引用错误及体素化后消失的关键参数。
2. `geometry.py` / `voxelizer.py`：执行有序 box、polygon_prism、profile_shell。米制坐标统一 half-up 量化，box 使用左闭右开边界。每个可见格保留最后写入的构件 ID。
3. `palette.py`：材质名映射到允许的 vanilla 整立方体状态与示意色。未知方块和属性组合停止执行，不能把楼梯等误画成普通整块。
4. `export_nbt.py`：复用 BuildKit v0.3 的 NBT exporter。采用确定性 gzip，包含 DataVersion、size、palette、blocks、entities。
5. 独立 `inspect_build.py` 读回 NBT，比较尺寸、全部非空气坐标与状态及几何 SHA-256。比较通过才继续。
6. `validation.py`：在读回结果上验证明确声明的空气区、平面通路和变截面关系。归属信息在几何完全相等后关联，不能用归属掩盖方块差异。
7. `render_views.py`：从读回 NBT 用 CPU 深度缓冲绘制五视角。PNG 记录 build_id 和 geometry_sha256；文件还逐一校验 PNG 完整性。没有文生图参与。
8. `pipeline.py`：临时目录构建，成功后生成不可覆盖的版本目录及完整报告。CLI 不访问网络、不执行自然语言、不修改存档。

## 几何能力

| 原语 | 参数 | 用途 |
|---|---|---|
| `box` add | min_m / max_m / material | 基础、墙、屋面、楼板、体量叠加 |
| `box` subtract | 同上，targets 指定历史构件，material=null | 开门窗、局部挖空；不误删其他构件 |
| `polygon_prism` | XZ多边形、上下Y | 凹多边形平面、花池、非矩形体块；不支持孔洞环 |
| `profile_shell` | 分层截面、插值、壁厚、楼板与竖梃 | 矩形/椭圆变截面壳体；linear或step |

变截面在每个方块层的中心高度求截面，再体素化；因此实际宽度与连续设计值可能有一格级差异，检查以最终格点为准。楼板内部填充，其余保留空腔。圆柱暂可由多边形拉伸表达，案例一格半径时圆形效果受分辨率限制。

## 坐标与相机

X向右，Y向上，Z向后；前=-Z，后=+Z，左=-X，右=+X。这里是模型局部坐标，不等于真实地理北向。ISO视角水平从-Z向+X转45°、仰角45°；使用正交投影。四立面无透视变形，玻璃用示意色，灯块只表示材质位置。

## 稳定性和资源

相同 Spec 的构件顺序、取整、方块排序和 gzip 时间戳固定，NBT可重复生成。PNG在相同依赖与字体环境下重复。build_id由spec_id、revision和canonical Spec哈希组成；几何哈希只含边界和排序后的坐标/状态，视觉变化不会改动它。

预检包围盒最多1,000,000格；限制非空气数和写入/开洞操作次数。当前 `max_cell_visits` 统计执行到方块写入/挖空的次数，不是完整的CPU耗时上限；部署时必须加进程超时、内存限制和并发配额。引擎拒绝超限，不自动缩放，也未做大结构切片。

没有游戏内物理、跨楼层寻路、真实光照或配置读取。平面路径检查是一格宽、固定Y、有支撑和足够净空的BFS，不是Minecraft玩家可达性证明。保存了组件级数据和外部局部差分，但每次仍完整构建。
