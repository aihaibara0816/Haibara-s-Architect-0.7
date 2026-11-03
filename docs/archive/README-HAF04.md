# HAF 0.4.0

2026-10-27。以完整 HAF03 归档为基础，合并市民服务中心 V0.3.3/R16、原创设计与功能内饰研究，并增加可执行交接计划检查。只整合与核验，没有新建整栋建筑，也没有训练模型权重。

先读 START_HAF.md、docs/haf_0_4_workflow.md 和 learning/case_registry.json。

```bash
python tools/agent.py --version
python tools/agent.py --catalog
python tools/agent.py --list-cases
python tools/agent.py --handoff examples/handoff/library.json --out /absolute/new/plan.json
PYTHONPATH=support/deps python tools/agent.py --review --case civic_center --run v03_r16_ceiling_landscape
PYTHONPATH=support/deps python -m unittest discover -s tests -v
```

`--handoff` 只产生设计计划，不能通过改建筑名称调用通用生成器。`--review` 只读旧run。`--run NEW_ID` 会运行明确注册的案例脚本，旧run不能覆盖。Civic入口只按固定R13基线重建当前方案，不接受通用 `--params`。

本发布含11个案例生成入口、2个历史对照；原0.3各案例以当时登记的快照保留，不宣称覆盖所有外部更新。12类用途、6类园林和18个内饰研究卡片是设计目录；另存图书馆小样，不是新增通用生成入口。

主要新增代码：hafusion/design_handoff.py、tools/agent.py交接入口、Civic只读复核、原生竹及已验证方块状态合并。原有核心、参数、旧输出、负例和验收边界保留。

验证记录见 release/haf04_unit_tests.txt 与 release/haf04_release_validation.json；失败尝试也留存。旧715个run文件及Civic195个run文件须保持哈希不变。

游戏导入/碰撞/真实光照/容器交互仍pending。Civic为稀疏NBT；研究图书馆为含空气全体积NBT，放置含空气会清除相应位置。请区分文件语义，不将近似预览当成游戏截图。

原始归档来源：release/original_archives.json、release/haf04_inputs.json。旧HAF03说明留于release/README_HAF03.md。完整Civic交互展示与原始大预览资产仍在对应独立交付中；本工程仅保留最终PNG、回读剖面及R13/R15/R16验证所需光场，不收录所有历史mesh缓存。预览可用工具重新生成。
