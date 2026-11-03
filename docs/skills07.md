# 0.7 可复用规则与 Skill 接续

六个领域已写入 `knowledge/workflow07.json`，可用 `workflow --domain ID` 或 `skill show --name ID` 读取。每条包含输入、规则、执行消费者、案例、验收和未实现项。

| ID | 规则范围 | 阅读 |
|---|---|---|
| reconstruction | 现实图片/模型、构件证据、尺度与不确定性 | [建筑研究](knowledge07/reconstruction.md) |
| scene | 地形、街道、院界、聚落、功能与变化 | [场景](knowledge07/scene.md) |
| interior | 完整墙地顶、活动组、家具、门床、嵌灯 | [内饰](knowledge07/interior.md) |
| vegetation | 树、盆器、植物层次、承托、水域和通路 | [植被](knowledge07/vegetation.md) |
| industrial | 厂房、罐体、管廊、铁路、电力和接口 | [工业](knowledge07/industrial.md) |
| orchestrator | 需求、研究、建造、验收、返工和归档 | [编排](knowledge07/orchestrator.md) |

这些规则已可在仓库内使用。已有个人技能 `gafacraft-architect`、`gafacraft-ha-research`、`gafacraft-concept-design` 与外部资料包技能各有自己的版本；本次并未改写它们。

个人 Skill 安装/同步未完成：本环境无法写入其管理目录，备用 Git 同步亦无法连接。不要把 `skill list` 的仓库输出当作个人技能安装结果。规则是否可执行，以列出的 CLI 消费者为准；“规则已归纳”与“通用生成能力已完成”分别记录。

下一次可写入技能管理仓库时，应把这些来源与回归用例接入对应技能，运行前向测试，再提交同步；不复制旧版“当前主线 0.4”的背景描述作为新版本结论。
