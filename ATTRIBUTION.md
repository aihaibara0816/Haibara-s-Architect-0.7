# 0.7 归档来源补充

`archive/cases` 来源于用户项目的 HAF05 研究总库、各条目记录的历史报告、Room06 专用工程。保留案例反馈、来源 URL 与既有授权说明；整理包不是原始工程完整镜像。第三方参考照片、视频帧和模型未作为新的公共素材库发布。`nbt-orthographic.png` 是从归档 NBT 读取的方块正投影示意；原报告预览不自动等同实机截图。


# 开源来源与本地化范围

PlanCraft：Gabor Wnuk，MIT，固定 commit `b0746140cf378d7e03b16887ef64ff9d99991f86`。
原样复用 `upstream/PlanCraft/tools/building/building/` 中的 Grid、reachable、配对检查及研究夹具所需 compiler；保留 `upstream/PlanCraft/LICENSE`。
来源：https://github.com/GaborWnuk/PlanCraft/tree/b0746140cf378d7e03b16887ef64ff9d99991f86
不附游戏 JAR、游戏纹理、图标、训练权重或上游已安装 Skill。

Arnis（Apache-2.0），固定 commit `a889f68637a18b540816fc41007a7972f7d547b4`。
来源：https://github.com/louis-e/arnis/tree/a889f68637a18b540816fc41007a7972f7d547b4
本地独立实现来源/版本缓存与候选取舍机制，未复制 Arnis 代码；不声称整套引擎集成。

ObjToSchematic（BSD-3-Clause），固定 commit `b611b52c7a87cad99127908598bab019fe9e7c3f`。
来源：https://github.com/LucasDower/ObjToSchematic/tree/b611b52c7a87cad99127908598bab019fe9e7c3f
本地独立实现几何/材质阶段边界，未复制其 TypeScript 代码或声明支持它的全部格式。

`research_lab/` 沿用用户此前保存的 R0.3 独立实验，`research_archive/` 保存来源核查。
`ha03/`、`case/` 是用户原工程的未改副本；HAFusion 新模块位于 `hafusion/`、`tools/` 和 `tests/`。
`tools/export_preview.py` 复用用户 V5 exporter 算法并只适配 I/O；EGL renderer 复用用户 V5 shader，补充无浏览器的执行环境。
原照片/SKP 的使用范围沿用其来源记录，不能因打包推定允许训练或公开再发布。
原字体许可在 `case/views/assets/OFL-NotoSansSC.txt`，保留不变。
不对用户原工程或这些不同来源的资产统一重新授权。
