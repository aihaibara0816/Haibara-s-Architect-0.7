# 来源与许可说明

本轮自行编写的是 lab 中的小型适配/研究代码和报告；不将上游实现改称原创，也不改变用户既有工程的归属或授权范围。

## 实际随包代码

PlanCraft：Gabor Wnuk，MIT License。固定提交 b0746140cf378d7e03b16887ef64ff9d99991f86。`upstream/PlanCraft/LICENSE` 原样保留；其源码文件逐个核验 Git blob SHA。工具源码与测试未改动。根 README、工具说明和 backend guide 用于溯源；图标、照片、游戏纹理、后端 JAR 和安装 Skill 不在本交付中。root README 中图标的 CC BY-NC-ND 条款不能被 MIT 覆盖。

Architect/BuildKit 最小桥接 runtime：来自用户提供的 Architect 0.3 归档，保留文件内容及原模块说明，只供本研究复跑。没有以新许可重新授权整个旧项目。逐文件来源哈希见 evidence/runtime_snapshot.json；完整原工程从原研究包恢复。

## 未随包复制的第三方代码/资产

Arnis（Apache-2.0）、ObjToSchematic（BSD-3-Clause）：只提供本轮技术分析和固定源码链接。新缓存原型为独立实现，不是 Rust/TypeScript 源码搬运。

threed2vox、minecraft-schematic-maker：固定公开提交中未见明确许可证，交付不包含其源码或图片，只保留链接与概念分析。

VGGT、VGGT-Ω：不包含代码、checkpoint 或数据；有关许可和访问要求以本报告固定版本和上游相应文件为依据。没有训练或运行其模型。

用户已有建筑照片、模型及网页摘要仍保持各自来源与使用边界。本研究不会因为它们可公开访问，就将其变成允许训练或公开再发布的数据集。
