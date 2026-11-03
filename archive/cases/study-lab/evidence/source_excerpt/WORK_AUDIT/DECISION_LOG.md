# 采纳与研究决策记录

日期：2026-10-21。所有正式接入仍待用户确认。代码作者和上游许可保留；“本地化”指在自身边界内理解、适配和验证，不是去除来源后改称原创。

| ID | 对象 | 决定 | 理由与证据 | 状态 |
|---|---|---|---|---|
| D01 | 现有 Architect/BuildKit | 保留 | 244 项回归通过；NBT/绑定/差分已有实现，重复开发收益低 | verified |
| D02 | 旧 6 个错误 | 不立即改源码 | 已验证依赖下未重现；保留旧失败日志，补环境锁定/异源模型测试 | verified + 根因待核实 |
| D03 | V5 | 冻结为当前案例基线 | ZIP/NBT 哈希、118,566 单元、9 分块核对 | verified；游戏 not_tested |
| D04 | PlanCraft 编译/量化 | 局部代码复用/适配 | 34/36 上游测试通过，2 环境阻塞；房屋/NBT 小实验通过 | verified（限定范围） |
| D05 | PlanCraft 全局 ceil | 不设为全局默认 | 改变映射外宽；净空、外观、接口需要分别约束 | verified 夹具 + source-observed |
| D06 | PlanCraft 游戏后端 | 借鉴回读流程，暂不替换导入器 | 26.x/Java 25 与历史 1.21.1 环境不同；无游戏实测 | source-observed |
| D07 | Arnis | 移植缓存/取舍/失败回退思想 | 参数和算法版本、无结果缓存、来源优先、确定性墙面拟合 | source-observed；自有缓存夹具 verified |
| D08 | Arnis GIS/整城核心 | 后续独立适配 | 单体建筑不需要立即承受整个 GIS 工程依赖 | proposed |
| D09 | ObjToSchematic | 先思想参考，再独立基准 | BVH 表面、厚度与材质分阶段有价值；开放结构需负空间评测 | source-observed；未运行其引擎 |
| D10 | threed2vox | 只读参考 | 提交树与 Cargo 未见许可证；多格式/NBT 已与现有功能重叠 | source-observed；不复制 |
| D11 | Blueprint Generator | 只借鉴交互设计 | 无明确许可；API 直接方块 JSON，编辑仅带前 50 方块样本，不满足大建筑可审计修改 | source-observed；未调用 API |
| D12 | VGGT | 可选 provider，暂不默认接入 | 相机/深度可辅助；需权重许可、锚点、算力和真实残差 | source-observed；inference not_tested |
| D13 | VGGT-Ω | 暂缓 | 非商业研究许可与权重申请；目前没有推理条件验证 | blocked/not_tested |
| D14 | 新 Lab | 保留为独立研究代码 | 21 项测试通过；证据单位/年代、真实磁盘缓存、3D 锚点 | verified 夹具，整体成熟度 C |
| D15 | 旧 geometry hash | 保留定义，加新旁路指标 | 当前包含状态，不能暗改历史语义 | source-observed；接入 proposed |
| D16 | 新 Skill/整体 workflow | 不在本轮安装或变更 | 用户明确要求内部架构改动先确认 | awaiting_user_scope |

## 本轮过程中的失败与调整

- PlanCraft 首次测试缺 pytest；在独立 test-deps 安装 pytest 8.4.2 后重跑，34 通过、2 注册表受阻。两个结果都保留。没有通过修改上游测试或假注册表消除失败。
- Arnis 注释引用的两个 facade_lab Python 文件未在公开树中找到，访问 404；据实际 Rust 源码研究，停止把它们当可运行 Python 入口。
- 当前环境与研究包 3.13 环境不同，244 通过的含义是此依赖组合通过；没有改掉 Duplicate node ID 校验来追求绿灯。
- 本轮新实验输出明确标为合成夹具；没有给广州塔补造尺寸、训练结果、效果评分或推理时间。
- 工程桥接以一个合成构件输出，不能证明跨引擎组件所有权自动保留。

## 尚未决的问题

1. 用户批准 C1/C2/C3 哪一批正式变更。
2. 目标 Minecraft/NeoForge/Create/导入器和资源包是否仍为历史配置。
3. 真实配准可用的尺度/方向锚点与照片控制点，及其误差。
4. 缺许可项目的代码是否会获得明确授权；当前不采用其源码。
5. 未来视觉模型的 checkpoint、许可场景和可用硬件。
6. 复杂构件的外形与通行之间的偏差预算、持出建筑和用户审美评价。

不需要这些问题全部解决才能做 C1，但不应绕过它们宣称图模融合、游戏表现或通用泛化已经完成。
