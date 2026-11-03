# 资产审计 · 2026-10-20

先检查已提供文件与可获得历史资料，再开发；没有把“训练过小模型”作为前提。

| 资产 | 实际获得的内容 | 验证 / 本轮处理 |
|---|---|---|
| 三份项目交接文档 | `docs/handoff/01_项目目标与完整工作流.md`、`02_已有成果与待核实资产.md`、`03_给ChatGPT_Work的立即执行任务书.md` | 已逐份读取，按P0–P3实现；P4只读尝试 |
| Haibara_BuildKit_v0.3.zip | `vendor/buildkit_v03/`完整保留 | 实际代码是参数化生成/导出/检查工具，不是神经模型权重；28项测试通过 |
| real-to-minecraft v0.2 | 旧包`.agents/skills/real-to-minecraft/` | SKILL已读取；31项检查器测试通过；复用事实/试值区分及静态/游戏验收分离 |
| gafacraft-building-reference | `vendor/building_reference/`当前安装副本 | SKILL、data-contract、packet-template及脚本已读取；59项自测通过；模板校验和比例换算通过 |
| 历史记录版号9bac699e… | 交接书列出的标识 | 当前可访问Skill已包含后续改进，不能证明与该历史提交逐字一致；实际副本以`reports/source_manifest.json`哈希为准 |
| GAFAcraft-building-workflow.html | `docs/research/GAFAcraft-building-workflow.html` | 找到完整文本快照并阅读；保留历史流程，不当作已有模型功能证明 |
| 广美廊柱R002 | 旧evidence、parameters、dimensions和colonnade.jpg | 实际照片已查看；原参数明确为assumed，真实尺寸未测；迁移到`examples/legacy_gafa_research/` |
| 历史廊柱生成器/NBT exporter | voxel_core.py、gafa_colonnade.py、旧输出 | 复用确定性NBT exporter和独立inspect_build读取器；案例专用几何由新通用构件替代 |
| Haibara_Build_Engine_v0.1.zip | 找到文件条目，未成功取得字节 | 资料获取返回403；不能审计内部代码，不声称已合并该包。已提供v0.3包足以继续本轮 |
| 711 / 罗森旧实验 | 交接书提到历史成果 | 两份已取得附件内未找到对应可验证工程与原NBT；当前便利店是新工程样板，不是假称恢复的711 |
| 神经网络权重、训练日志、训练数据集 | 当前取得工程中未发现 | 不宣称模型已训练；后续可接现成多模态模型，无须先训练小模型 |

两个Skills保持原样副本，没有改写已安装版本，没有推送远端仓库。源目录相对路径与内容哈希记录在source_manifest中，便于后续核对到底复用了哪一份文件。

## 本次复用的具体能力

- 研究侧：来源/事实/图片稳定ID、未知值保留、比例换算、选图门槛与原packet校验器。
- 构建侧：Scene字典、确定性gzip/NBT写出、独立且带边界限制的NBT解析、文件检查与区域差分。
- 保留旧代码的半砖、栏杆案例实现；新预览暂只支持整立方体，未把旧功能全部声称迁移完成。

新开发的是BuildingSpec协议和适配层、通用体量/开洞/变截面生成器、同源五视图深度渲染、静态通路与截面检查及可重复交付管线。

## 环境

Python 3.12.14、Linux；依赖版本见`requirements-tested.txt`。未接入Minecraft客户端、服务器配置或存档，历史版本号仍为未核实目标。`gafacraft.cn`的公开只读打开未成功且搜索无可用结果，无法据此判断现有站点技术栈。
