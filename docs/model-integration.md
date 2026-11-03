# Haibara’s Architect 0.7：模型接入

模型负责提出结构化建议，宿主负责基线、目录、执行开关和结果回传。无需先接某家 SDK，即可用以下离线工具调用演练。

```sh
python -X utf8 tools/haf.py scene-dispatch examples/habitat07/model-call.json --base-request examples/habitat07/reading-garden.json --runs-root runs/model07 --run added-001
python -X utf8 tools/haf.py scene-dispatch examples/habitat07/model-call.json --base-request examples/habitat07/reading-garden.json --runs-root runs/model07 --run added-001 --execute
python -X utf8 tools/haf.py scene-verify --runs-root runs/model07 --run added-001
```

第一条只返回候选计划；第二条由宿主明确执行建造。模型工具名是 `ha_scene_add_modules`，唯一参数是新增模块列表。宿主提供经批准的基线，模型不能改 seed、高程、水域、禁放区或既有模块，也不能指定脚本和路径。重复 ID、未知配方、越界、碰撞、悬空和被阻塞的使用点会被拒绝。

| 宿主步骤 | 内容 |
|---|---|
| 上下文 | 读取 `knowledge/workflow07.json`、相关案例与 `recipes`，提供允许范围和现有模块 |
| 工具定义 | 使用 [tool-schema.json](../examples/habitat07/tool-schema.json)；按所用模型平台的函数工具格式包裹 |
| 输出解析 | 解析为 JSON 对象，拒绝脚本/命令；仅交给 `dispatch_scene` |
| 预检 | `dispatch_scene(call, base_request, runs_root, run_id, execute=False)` |
| 执行 | 在用户已授权的范围内由宿主设置 `execute=True`；每次新 run |
| 反馈 | 把验证错误或实际 manifest 回传模型；视觉/游戏结果由实际执行者填写 |

这提供了模型中立执行端，未附网络模型 SDK、密钥管理、预算、自动重试或无人值守闭环。现有 0.6 的冻结模块修订/父链方案继续可用，协议如下。

---
# Haibara’s Architect 0.6：把模型接到可检查的设计流程

本层把模型当成“提出结构化修改的协作者”。模型输出 JSON，由宿主选择父 run 和工作目录，Python 验证规则，最后保存新的规划版本。你可以先用仓库附带的 JSON 完整演练，不需要密钥、网络连接或某个最新 SDK。

它已经具备工具调用的数据边界和执行入口；联网模型调用、鉴权、预算、自动重试、视觉评价及自动建造闭环仍由宿主实现。不要把离线提案导入演示描述为已经完成的自主建筑 Agent。

## 无模型也能运行的接入演练

在仓库根目录执行：

```sh
python -X utf8 tools/haf.py demo --runs-root runs/student-model --run demo-001
python -X utf8 tools/haf.py dispatch examples/workflow06/model-call.json --runs-root runs/student-model --parent demo-001
python -X utf8 tools/haf.py verify --runs-root runs/student-model --run model-001
```

`model-call.json` 是一次模拟模型工具调用：提出新的完整模块列表，将阅读桌移动到另一个有效范围，保留已冻结书架；新 run ID 为 `model-001`。`dispatch` 返回规划清单，最后一条验证新 run 及父 run。它不会调用语言模型或生成建筑。

如果重复练习，换一个新的 `--runs-root`。示例提案的 hash 对应原始演示请求；修改请求后必须从新父 run 的 manifest 读取 `request_sha256`，不能继续使用旧 hash。

## 模型应该收到哪些资料

提供宿主已经核对的父 run `request.json`、`manifest.json`、`handoff_plan.json`，以及 `examples/workflow06/tool-schema.json`。如本任务涉及参考图或未解决的判断，还应补充这些证据和不确定性；仅有 JSON 并不意味着模型已经看过建筑。

可使用以下任务说明作为起点：

> 根据给定父 run 提出室内模块调整。只替换 proposed_modules 的完整列表，保留所有 frozen_module_ids 对应模块的全部字段。楼层、房间、授权范围、通行禁入区和随机规则以父请求为准。先通过 haf_validate_proposal 检查；若有错误，依据错误修正提案。仅输出符合工具 schema 的 JSON，不提供 shell 命令，不声称已生成几何或通过游戏验收。

这个说明帮助模型理解任务；保护范围和冻结检查由代码落实，不靠模型自觉。

## 提案合同

提案只允许三个顶层字段：

| 字段 | 要求 |
| --- | --- |
| `schema_version` | 固定为 `"0.6-model-proposal"` |
| `source_request_sha256` | 与宿主绑定父 run 的请求摘要一致 |
| `proposed_modules` | 完整替换列表，保留全部冻结模块；每个 component ID 唯一 |

提案不能携带新的 `handoff`、`authorized_scope`、`variation`、`frozen_module_ids` 或 `command` 顶层字段。模块本身仍按原 0.4 消费者检查所属房间、边界、锁定组件、通行禁入区和模块重叠。原合同可能保留额外模块描述字段；保留文本不表示执行其中内容。

这里的“完整列表”很重要：提交一张新桌子并不会自动保留旧书架。如果书架被冻结，漏交会失败；如果未冻结，漏交意味着它不在新版本的模块列表中。因此模型必须明确区分“替换全部列表”和“局部补丁”。

## 宿主暴露的三个工具

`tool-schema.json` 使用中立的 `name` / `description` / `input_schema` 结构，输入 schema 使用 JSON Schema 2020-12。接入具体服务时由宿主映射成该服务的工具注册格式；文件本身不宣称兼容任意供应商 SDK。

| 工具 | 模型可提供的参数 | 行为 |
| --- | --- | --- |
| `haf_verify_parent` | 空对象 `{}` | 验证宿主绑定的父 run |
| `haf_validate_proposal` | `proposal` | 检查候选请求，不写文件 |
| `haf_import_proposal` | `run_id`、`proposal` | 检查后创建新的规划 run |

工具调用外层必须是 `{"name": "工具名", "arguments": {...}}`。`runs_root` 和 `parent_id` 不属于模型参数，宿主必须在函数调用或 CLI 参数中绑定。未知工具和多余参数会失败；build-case、shell、任意 Python 表达式没有暴露给模型。

## 最小 Python 宿主示例

为此练习单独建立一个父 run，然后把以下代码保存到仓库根目录的 `host_demo.py` 并运行。它只读取附带的模拟调用，不访问模型服务。

```sh
python -X utf8 tools/haf.py demo --runs-root runs/student-model-host --run demo-001
```

```python
import json
from pathlib import Path

from hafusion.workflow06 import dispatch_call, load_json

repo = Path(__file__).resolve().parent
# 这两项由宿主选择，不从模型返回的 JSON 读取。
trusted_runs_root = repo / "runs/student-model-host"
trusted_parent_id = "demo-001"

call = load_json(repo / "examples/workflow06/model-call.json")
result = dispatch_call(call, trusted_runs_root, trusted_parent_id)
print(json.dumps(result, ensure_ascii=False, indent=2))
```

```sh
python -X utf8 host_demo.py
```

连接真实模型时，用解析后的模型工具调用替换 `call` 的来源即可。不要把模型输出拼进命令行、传给 `eval`，或允许它自定宿主目录。模型返回的未知字段或无效坐标应作为可解释的校验错误返回给模型；重试次数和新 run ID 分配由宿主控制。

最小演示不包含网络重试、凭据管理或自动批准。若希望一次模型调用只评估而不落盘，宿主只暴露 `haf_validate_proposal`；导入是另一个明确操作。

## 成功、失败和历史

- 结构或范围错误、重复 ID、锁定模块变化、过期 hash：失败，不生成新的成功 run。
- 合法修订：保存新的请求和提案，父 run 保持不变。
- 同名 run：失败，要求新的 ID。
- 完整性验证：重算输入、计划和父链关系；拒绝清单之外的文件、循环父引用和缺失父 run。
- 模型输出被接受：仅代表规划合同通过。几何、视觉和游戏状态仍待完成。

SHA-256 可发现文件与清单不一致，不能证明内容是谁写的，也不能证明根请求得到过用户授权。宿主应保护可信父 run 及其外部审批记录。本层拒绝危险路径和未注册工具，但不替代操作系统隔离、网络服务的访问控制或对外部资料的审查。

## 如何连接真正的建造器

现有 `tools/agent.py` 和 `agent_config.json` 继续运行已注册的 0.4 案例适配器。新 CLI 的 `build-case` 提供显式桥接，但不接收模型提案，也不会把任意模块列表转换成 NBT。

要补成更完整的 Agent，下一步应实现有明确合同的“规划到几何”适配器：规定哪些模块和 choice 可消费、如何记录输出构件 ID、如何回读边界与占位、哪些视觉和游戏证据才能升级状态。先用一个小案例验证这些环节，再扩大风格和建筑类型。
