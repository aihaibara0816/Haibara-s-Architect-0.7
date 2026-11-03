# 广州塔离线参考盒使用记录

已保留 13 个候选图片 ID（R01–R13）、7 个旧入选记录及原来源、credit、像素/哈希记录、回查原文。三个输入对象完整保存在 `reference_box.json`，`checks.json` 记录与原文件的语义及哈希核对结果。

- `packet.json`：按 Skill v1.1 模板建立的结构化包；十节、受限资料指令、候选注释及覆盖缺口。
- `reference_box.json`：原始输入、旧选图顺序、按原用途整理的资料组与全部旧回查记录。它是归档附录，不是 Skill 新增官方协议。
- `validation.json`：实际官方 report 模式输出。
- `checks.json`：实际命令、退出码、校验脚本哈希、字段映射和保留检查。

复验命令：

工程包内可用相对命令（在工程根目录执行）：`python vendor/building_reference/scripts/validate_packet.py examples/canton_reference_v11/packet.json --mode report`。以下保留本次运行时的原绝对命令作为记录。

```bash
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python -B /root/.codex/skills/remote-skills/skill-6ad26bc8a18081918d5339dd69880ed2/scripts/validate_packet.py /workspace/scratch/cfe8adbb046e/forward_reference/packet.json --mode report
```

本次结果：`PASS_WITH_GAPS`，退出码 0，0 errors，48 gaps；19 项保留与一致性检查全部通过。结构通过不代表照片、网页、许可或模型已核验。

正式 `core` / `detail_groups` 为空：旧记录缺少大图查看、质量、版本和身份核验依据。旧选图仍按原顺序完整保留；全部照片 `face=unknown`，前/后/左/右/顶部/斜向/内部七项要求均缺失。旧 `front/right/iso45` 是模型回查镜头，不能作为照片定向依据。

`review_status`、`review_finding`、`priority`、`component` 原文不变。缺少同一 build_id 的预览、真实组件ID与相机可比性，规范化模型回查状态保持 null。来源标题/访问日期、图片查看日期、照片许可保持未知；280 格目标和旧尺度参数仅归档，不充当实测或可建余量。

三份输入不是 v1.0 packet，因此未调用只接受旧 packet 的 `migrate_packet.py`。初始兼容问题只做过静态读码，未执行旧版验证，也没有虚构“第一次 FAIL”日志；本结果来自执行时现有校验器。

本任务没有联网、查看图片、读取图片原字节、下载照片或生成模型。未修改输入或 Skill，产出仅位于当前目录。
