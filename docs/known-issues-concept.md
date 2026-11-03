# Concept 模块：已知问题、适用边界与待验收项

核查日期：2026-11-01。本页记录 Haibara’s Architect 0.6 整合时对概念设计、立面变化、家具与室内实验脚本的源码审计和局部试跑结果。列出的缺陷在本轮审计中未修改；没有通过安装额外依赖或临时替代模块使测试通过。

本页 `scripts/`、`references/`、`assets/` 路径以 `gafacraft-concept-design` 技能包为根；`support/`、`cases/` 路径以配套 HAF 工程为根。所有路径均为相对路径。

## 当前验收结论

已经取得并审计真实源码。15 项目标属性检查通过，五个固定家具调用的回调几何与实体元数据检查通过；这些结果只覆盖各自的断言，**不能视为整模块、完整 NBT 构建、渲染或游戏验收通过**。下列已复现问题与依赖缺口仍然存在。

本轮完整室内实验构建在导入 `rural_states` 时失败，未生成 NBT。家具调用可以独立输出格位和元数据，但三个配方在当前 baseline 状态校验器中存在注册缺口。游戏交互和审美均未在本轮验收。

## 已复现的源码问题

| 编号 | 相对源路径 | 已确认行为 | 影响与修复方向 |
|---|---|---|---|
| O-01 | `scripts/plan_openings.py` | `fixed=true`、允许区间 `[0,5]`、原区间 `[1,1.8]`、层高 3、数量 1 时，输出区间为 `[0.85,1.95]`。最小宽度 clamp 把 0.8 米固定组扩到 1.1 米 | 当前不能保证窄固定组原范围不变。应明确固定优先级，并增加窄区间回归检查 |
| O-02 | `scripts/plan_openings.py` | 普通固定组只锁定组范围及数量；改变 seed 仍可改变部分单窗宽度、窗台/窗头与 ledges | `fixed` 不是整组几何和花槽冻结。应拆分锁定粒度，或明确接口仅部分锁定 |
| O-03 | `scripts/plan_openings.py` | 布尔 `count_hint` 可被当作整数；布尔、浮点 seed 可进入计算。与 `plan_variation.py` 只接收非布尔整数或字符串 seed 的规则不一致 | 尚非统一 schema/type 校验；应统一 seed、数量、布尔字段约束和 CLI 错误输出 |
| P-01 | `scripts/preview_material_marks.py` | 仅含 stone 等无识别标记方块时，`out=[]` 形成一维空数组，不能与形状为 `(n,10)` 的顶点数组拼接，抛出 `ValueError` | 空匹配应作为合法无操作，或显式构造正确形状的空顶点数组 |
| P-02 | `scripts/preview_material_marks.py` | 同位置炉子 facing=east 和 west 得到相同识别面；多数面固定朝 `+Z/+X/+Y`，不读取方块朝向 | 朝向变化后标记可能落到错误面。床仅检查 head，水位、蛋糕 bites 等也未完整参与标记几何 |
| P-03 | `scripts/preview_material_marks.py` | 对同一炉子场景连续 `apply`，附加标记三角形由 4 增至 8 | 重复执行会叠加，当前不幂等。应从干净网格重建或识别/替换已生成层 |
| F-01 | `scripts/interior_kit.py` | `barrel(facing='up'/'down')` 先 emit 方块并写入 BlockEntity，再因使用点方向查表抛出 `KeyError` | 失败留下部分输出。应在 emit 前验证，或明确仅支持四个水平方向 |
| F-02 | `scripts/furniture_detail_kit.py` | `__file__.split('/')[-1]` 在 Windows 未取得文件名，`geometry_consumer` 写入完整本机路径 | 元数据不可移植，也不适合直接公开。应采用跨平台 basename 或稳定相对源标识 |

这些问题不因其他目标属性检查通过而关闭。O-01 是固定范围违背；O-02 则是接口锁定范围较窄，两者应分别处理。

## 有条件随机的实际边界

| 范围 | 已实现 | 不应推导出的承诺 |
|---|---|---|
| 开窗变化 | `scripts/plan_openings.py` 在人工编写的 `allowed_u_m` 内改变组长、偏移、数量和窗形，输出 proposed 几何 | 不会自动识别可开窗墙段，也不校验门洞、逃生、核心筒、采光或三维碰撞；原固定窄区间还有 O-01 |
| 稳定 seed | 两个计划器按 seed 和稳定键做 SHA256 确定性取值，无顺序消耗的共享 RNG | 两者 JSON 序列化方法不同，相同 seed/键不保证同值；也不能只保存 seed 而丢失算法版本、输入、稳定 ID 和采纳结果 |
| 局部隔离 | 输入重排和新增独立组/region 不因循环顺序扰动原组；旧化、玻璃、花槽使用不同键 | 同一 region 增删 panel 会改变玻璃排名截断与配额，可能改变其他入选者，不能声称任意编辑都完全隔离 |
| 花槽分组 | `scripts/plan_variation.py` 使用 `hash(seed, group_id) < planter_density` 按组选择 | density 是组级选择概率，不是精确候选占比。同组九个合格候选可能全选或全不选；不是强制空间密度约束 |
| 组标识 | planter group 的 hash 不包含 region | group_id 应全局稳定且唯一到预期组；跨区复用同名 group 会关联选择结果 |
| 声明支撑 | openings 要求 truthy `support_ref`；variation 要求 support_ref、严格布尔 true 的 support_confirmed/clear_of_routes，并排除 protected | 只检查作者声明，不检查真实承托、荷载、固定件、排水、通路或碰撞。无实际支撑的场景也可能被声明为合格 |
| 玻璃配额 | 按每个 region 的合格玻璃 panel 数量向下取整配额，再稳定排序挑选 | 60 个合格 panel × 0.06 得 3 个，实际比例 0.05；不能以总墙面面积或全部方块数作为同一分母 |
| protected | 禁止玻璃点缀与旧化；`allow_weather=false` 仅禁止旧化 | protected 的 glazed panel 仍赋主玻璃材质，不能理解为整条记录或原材质绝对不变 |
| 旧化 | 依据年代、翻新、维护、暴露与 override 计算强度，输出 `surface-mask-required` | 这是设计控制公式，不是现实劣化预测；未生成窗台流挂、接缝、雨水管、表面剥蚀等空间遮罩或最终方块 |

`references/facade-variation.md` 中的比例和维护参数属于可调整设计预设，不是法规或现实统计。开窗结果需替换旧的逐 bay 窗矩形，不能叠加；front/back 局部 u 轴还需消费者显式映射到世界坐标和朝向。

## 家具、植物与室内实验的边界

`scripts/interior_kit.py` 与 `scripts/furniture_detail_kit.py` 是固定原语及配方消费者。它们没有全屋布置求解、自动旋转/缩放、覆盖保护、统一支撑检查或随机组景算法。调用方须先保留 footprint 和使用通路。`door` 只放门扇，不生成或验收门框、门楣与完整门洞。

`InteriorKit.potted()` 已能输出固定单格 `potted_bamboo`；`references/interior-planting.md` 的分组、叶冠边界、合法候选、独立 plant_seed、局部重放和 metadata 规则仍不能据此视为已实现。2026-10-30 的分组植物实验标记为 `schematic_only`，未把植物组写入四个展厅 NBT。

| 最小调用 | 输出格数 | 输出实体元数据 | 当前 baseline + 状态适配结果 |
|---|---:|---|---|
| `framed_daybed(width=2)` | 10 | 4 个 bed half | 全部 state 通过 |
| `framed_daybed(width=3)` | 13 | 6 个 bed half | 全部 state 通过 |
| `bed_wall()` | 24 | 4 个 bed half | spruce_planks、lantern、flower_pot、light_gray_carpet 缺注册 |
| `kitchen_band()` | 23 | 2 barrel + 1 furnace | spruce_planks、flower_pot 缺注册 |
| `mixed_cabinet()` | 15 | 2 barrel | flower_pot 缺注册 |

五次调用验证了单配方内无覆盖、父组件半开 bounds、床配对、应有实体类型/位置、声明使用点未被同配方占用、重复确定性及 origin 平移。未验证整房路径、外部支撑、NBT 序列化、游戏使用或审美。状态拒绝是当前词表/注册缺口，**不是上述 Minecraft 原生方块无效**。

`scripts/interior_lab_states.py` 依赖 HAF 的 `detail_lab.states` 和 `vendor.voxel_core`，并全局替换部分状态函数；存在导入顺序依赖。识别某一 family 不表示所有材质、颜色、属性均已完整支持。简化预览盒和颜色也不是游戏网格/材质证据。

## 实验脚本依赖与消费状态

| 相对源路径 | 已确认条件或缺口 | 尚不能宣称完成的内容 |
|---|---|---|
| `scripts/build_interior_lab.py` | 四种硬编码房间，seed 只作记录/Builder 接口，geometry_randomness 明示 none；需 HAF support 中的 rural_states、detail_lab、vendor、hafusion.classical 及 nbtlib 等 | 不会按 seed 自动改变房型、用途或布局。本轮因缺 rural_states 在导入阶段失败，未生成 NBT |
| `scripts/audit_interior_lab.py` | 针对固定房间、活动点、门/床/实体、简化 BFS 与状态规则；依赖配套状态注册和 nbtlib | 不能升级为任意房间的完整碰撞、开门动作、睡眠、容器、光照/刷怪或审美验收 |
| `scripts/render_interior_lab.py` | 依赖可导入 render_egl_site、detail_lab.mesh、vendor、NumPy，并硬编码读取 `cases/japan_town12/review/assets/render_shader_reference.html` | 当前恢复的 baseline 缺所需入口和资源。其他案例发现的同名渲染器还使用 Linux EGL，未验证可直接在 Windows 运行 |
| `scripts/preview_material_marks.py` | 需 NumPy 和真实 vendor.voxel_core；只提供 apply(build, scene)，修改 opaque.bin/scene.json 的程序化识别面 | 不修改 NBT、不新增家具，也不是资源包纹理、独立渲染器或游戏截图；另有 P-01 至 P-03 |
| `scripts/plan_openings.py`、`scripts/plan_variation.py` | 输出计划与候选分配，不是 HAF 适配器；variation 记录规范化输入 digest，openings 没有对应 digest | 世界坐标、blockstate、支撑/碰撞、旧化空间遮罩、构建与回读尚需明确消费者 |

本轮环境中 NumPy/Pillow 可用，但 nbtlib 不可用；恢复的 baseline 未找到 rural_states。不能把历史“实验已生成”的记录转换为当前包组合开箱可用的结论。

## 典型否定案例与尚未关闭的问题

| 案例 / 参考文件 | 已知否定或纠正 | 不能以什么替代验收 |
|---|---|---|
| Civic v01；`references/civic-and-jiejao.md` | 即使多视图一致，重复彩色窗、缺花槽仍被否定 | 不能用视图一致证明建筑语言成立，也不能把案例尺度变成全项目默认 |
| jiejao；`references/civic-and-jiejao.md` | NBT 可作为局部构件/材料样本，整体参数不宜照搬 | 方块 ID 不证明原作者设计意图，平涂投影不是游戏截图 |
| Library+Cafe rev03/rev04；`references/interior-identity.md` | rev03 图书馆空；rev04 借助书架与阅读内容补强 | 22→201 普通书架是案例记录，不是通用数量门槛；仍需空间、视觉和实机验收 |
| 门框、图书馆、餐馆；`references/interior-rebuild.md` | 门扇/门框错位；散放书架缺阅读服务；桌椅缺迎宾/备餐/回收/服务边界 | 只验前后净空、家具数量或把未设计空地称通道均不足 |
| Corner01；`references/furniture-craft.md` | 粗糙、薄、勉强占位、楼梯椅替代、沙发及软硬层次不足；状态保持 needs_revision | 四个新展厅或几何/数量通过不能自动关闭原房间反馈 |
| 室内植物；`references/interior-planting.md` | 房间过硬、单调；植物需与家具、软装和留白同步设计 | 随机散点或每角同一盆栽不能替代构图；平面试验不代表 NBT 实装 |
| Taisho14 / Taisho15 / T07；`references/terrain-first-settlements.md` | Taisho14 规则梯度、近似平行街、矩形整平、重复盒体、等距樱花和过大钟面；Taisho15 主次道路不清、林冠不足、裸露土包和钟楼比例失败，仍 needs_revision；T07 的山溪与林地关系获认可 | 高程保留率或几何通过不能覆盖审美否定；T07 认可不要求照搬尺寸或建筑，也不能扩大成全部布局验收 |

案例编号和版本不得补成不存在的连续升级链。I01 与 InteriorDetail05 属于不同实验路线；没有证据支持“Interior01–05 全部连续完成”或为缺失的规则 0.4.4 编造能力。综合发布版本 Haibara’s Architect 0.6 也不自动改写各局部 schema、算法及 recipe 的 0.1/0.2/0.4 版本号。

## 下一轮关闭条件

1. 修复并回归 O-01、统一类型边界；明确 fixed 的锁定粒度和 group_id 命名约束。
2. 修复 preview 的空匹配、朝向和重复执行；修复 barrel 的半输出失败与 Windows 元数据路径。
3. 恢复真实依赖和状态注册，记录精确来源/版本，完成固定实验的 build → NBT 回读 → audit → render。
4. 为计划输出提供明确几何消费者，验证世界坐标、blockstate、支撑、通路、碰撞与旧化遮罩；植物组景补充稳定重放及局部 seed 隔离的真实实现。
5. 在同房间、同机位、同材质和光照下复查家具、植物、软装与墙地顶，并分别记录 data_checked、geometry_checked、visually_reviewed、engine_consumed、game_checked。用户否定反馈应由对应案例复查关闭。

在这些步骤完成前，可描述为“可执行的局部计划器、固定家具配方及有限状态/预览适配”；不能描述为通用全屋自动设计、完整随机植物 NBT、全部游戏交互或端到端验收通过。
