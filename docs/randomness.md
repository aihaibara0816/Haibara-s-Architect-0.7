# Haibara’s Architect 0.6：有边界、可复现的随机

本层随机的对象是“某个稳定构件在某个通道选择哪一个语义值”。例如西侧面板的材质选 `light_stone`，维护状态选 `maintained`。程序不随机搬动楼层、改变轮廓或生成地形，也不自动把 choice ID 转成 Minecraft 方块。

建筑判断仍需先完成：材料候选是否合适、哪些区域受雨、哪部分必须保持整齐、哪些细节已经确认，都应先变成明确输入，再让随机在范围内发生。

## 为什么不用一条连续的随机序列

连续抽取一个全局随机数序列时，在前面增加一个构件常常会让后面的结果全部改变。当前实现按以下地址独立计算 SHA-256：

```text
[算法版本, 全局 seed, 通道 ID, 通道 seed, component ID]
```

随后把摘要转成整数，按候选值的整数权重选择。候选项按 choice ID 排序；输出按 component ID 和通道 ID 排序。算法 ID 固定为 `haf-addressed-choice-sha256-v1`，实现在 `hafusion/variation06.py`。

| 操作 | 当前保证 |
| --- | --- |
| 只重排目标、通道或候选项 | 选择结果不变 |
| 增加一个不重叠的无关目标 | 既有构件选择不变 |
| 修改 weathering 的通道 seed | material 通道不变 |
| 修改全局 seed | 所有未冻结通道可能变化 |
| 修改某个 component ID | 该构件获得新的随机地址 |
| 修改候选项或权重 | 相应通道的选择可能变化；原地址摘要可以不变 |
| 已冻结构件修改 seed | 保持显式给出的既有选择 |

“可能变化”不意味着每次一定抽到不同选项。如果候选项只有两个，两个 seed 也可能选中同一项。

重排输入仍可能改变**请求摘要**，因为请求快照保留数组顺序；上表承诺的是随机选择的独立性。创建时间也会变化，因此不应要求两个 run 的 manifest 字节完全一致。

## 如何给构件起稳定名字

使用能在局部返工中继续指向同一构件的名称，例如 `facade.west.panel.01`。新增一块面板时给它新 ID，不要为了保持数组顺序把所有旧编号重新编号。

ID 区分大小写，不自动合并同名或近似名。重复构件、通道、候选项或目标通道会失败；前后空格、控制字符及空 ID 也会失败。名称不会被当作文件路径或可执行代码。

## 通道与条件怎样表达

以下是附带教学请求的一部分；实际运行请使用完整的 `examples/workflow06/library-request.json`：

```json
{
  "id": "weathering",
  "seed": 4,
  "choices": [
    {"id": "maintained", "weight": 8},
    {"id": "light_rain_mark", "weight": 2}
  ]
}
```

目标用 `channels` 指定允许应用哪些通道。例如窗户仅保留确认值，而其他墙面应用材质和维护状态。若朝雨面与背雨面的候选不同，可以显式建立两个通道，再把相应构件分配给它们。

这是通过候选表和目标归属表达条件。程序没有自动识别朝向、建筑年代、排水路径、风化因果、相邻构件相关性或植物生态。不要把教学的 8:2 权重当作真实环境统计；它只是演示参数。

全局 seed 和通道 seed 必须是整数，`true`、`1.0`、字符串、NaN、Infinity 都不接受。权重必须是 `1..1000000` 的整数。JSON 读取也拒绝重复 key、NaN/Infinity 和 `1e999` 这类溢出到无穷大的数。若在 JavaScript 等宿主里传递 seed，应使用该宿主能精确表示的整数，避免宿主先把数值舍入。

整数摘要取模存在极小的取模偏差，本实现用于设计变化，不用于密码学抽签或统计无偏采样。

## 范围、禁入区和冻结

variation 必须显式声明 `editable_regions`；在完整 workflow 中，它必须和 handoff 的授权区域完全一致，keepout 也必须一致，锁定名单不能移除 handoff 的锁定项。

每个目标的 `bounds_xyz` 必须满足：

1. 六个整数，三个方向均有正体积。
2. 整体落在至少一个授权区域内。
3. 不与任何 keepout 相交。
4. 不与另一个 variation 目标相交。

它使用调用方给出的盒子，不会自动核对方块占用或实测地形；variation 目标的互斥检查也不等于与所有 handoff 模块、地形和建筑的完整碰撞检测。

冻结有两种入口：目标指定 `frozen: true`，或 component ID 与锁定 ID 相等/为其点号前缀下的子构件。例如锁定 `facade.windows` 会覆盖 `facade.windows.approved.01`。

冻结目标必须为每个启用通道提供 `existing_choices`：

```json
{
  "component_id": "facade.windows.approved.01",
  "bounds_xyz": [0, 10, 4, 1, 15, 10],
  "channels": ["material", "weathering"],
  "existing_choices": {
    "material": "approved_cyan_glass",
    "weathering": "maintained"
  }
}
```

该例通过父锁定名单冻结。已有 choice 可以不在新候选表里，因为冻结的含义是保留确认结果。没有既有值时程序会失败，不自行抽取一个值来伪装成保留。

这与 `frozen_module_ids` 分工不同：后者保护模型提案里的整个模块 JSON，包括位置等字段；前者保护 variation 的逐通道 choice。

## 查看结果并做一个受控实验

```sh
python -X utf8 tools/haf.py demo --runs-root runs/student-random --run baseline-001
python -X utf8 tools/haf.py verify --runs-root runs/student-random --run baseline-001
```

打开 `runs/student-random/baseline-001/variation_plan.json`，查看 `entries`。每项记录 component、channel、choice、范围、状态和随机地址摘要；冻结项的地址摘要是 `null`，状态为 `frozen_existing`。

复制**源请求**到一个新文件，仅修改 `weathering` 的通道 seed，再用新的 run ID 执行 `plan`。比较两个结果中的 material 条目，它们应保持相同；再检查冻结窗户，其既有 choice 也应保持相同。不要直接改已完成 run 里的结果文件。

```sh
python -X utf8 tools/haf.py plan examples/workflow06/my-request.json --runs-root runs/student-random --run weathering-002
python -X utf8 tools/haf.py verify --runs-root runs/student-random --run weathering-002
python -X utf8 -m unittest discover -s tests -p test_workflow06.py -v
```

`my-request.json` 是你在上一步自行复制并修改的文件，仓库不会自动创建它。回归测试覆盖顺序、增量目标、独立通道、冻结、类型和边界等规则。测试通过仍只说明选择与合同检查一致，不能替代建筑的视觉判断和游戏验收。
