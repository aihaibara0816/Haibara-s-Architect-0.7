# 0.7 验证入口

当前验证记录见 [validation07.md](validation07.md)。下文是 0.6 的历史验证，不能直接计作本次测试。


# Haibara’s Architect 0.6 本次验证

日期：2026-11-01。平台：Windows，Python 3.12。以下为本次整理公开副本后实际运行的结果；历史报告仍保留原时间和范围。

| 项目 | 结果 | 实际范围 |
|---|---|---|
| 新运行层回归 | **35/35通过** | 稳定随机、通道隔离、冻结、越界、keepout、不可覆盖run、提案与父链、JSON/路径/非有限数防护 |
| 原内核测试 | **61通过，1项依赖错误** | 当前环境缺jsonschema，原BuildingSpec schema测试未完成；没有伪装为通过 |
| 合并测试总计 | **97项：96通过、1错误** | 错误即上项缺失依赖；requirements.txt已声明该依赖，但本环境网络限制未完成安装 |
| 新CLI实跑 | **7条命令通过** | 版本、demo、verify、import-proposal、修订verify、dispatch、模型run verify |
| 真实钟塔建造 | **通过** | 新建HAF06_smoke_01，112,474非空气方块，100×200×96，152组窗，最终NBT完整回读一致 |
| 历史案例公开路径审核 | **通过** | 75个案例文档链接、23条索引、11个入口、20个NBT/PNG哈希、36个明确读取依赖 |
| 概念实验 | **有限通过** | 两个纯规划器CLI可跑；15项正常属性通过，同时发现固定窄窗等反例，未宣称全部规则正确 |
| 游戏内导入/碰撞/实际照明 | **待完成** | 本次未操作Minecraft存档 |

钟塔新产物：[`building.nbt`](../cases/elizabeth_tower/runs/HAF06_smoke_01/building.nbt)。SHA-256：

`79d482b4ec9cb955cb4cf3b197af9efc8dd3f58e4d0ce2b3c39853623925ec83`

它使用保留的0.4共享内核与既有钟塔适配器，manifest中的内核版本如实保留。新增代码不等于新增建筑算法。

CLI结构化结果见 [validation-workflow06.json](validation-workflow06.json)。公开包文件摘要见根目录 `SHA256SUMS.json`，该清单用于检查文件一致性，不提供作者身份签名。

完整套件复现：

```sh
python -m pip install -r requirements.txt
python -X utf8 -m unittest discover -s tests -v
```

仓库附带Windows/Linux的CI配置，上传GitHub后才会执行；本地存在配置不代表已经通过远端CI。旧 `validate_release_04.py` 要求原始完整档案，不能用于这个精选公开包。
