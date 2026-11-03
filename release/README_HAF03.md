# HAF 0.3.0

2026-10-24。把广州塔至广州南站的研究、失败与修复整理为可执行的下一阶段基线。原 HAF 0.2、HA0.3、各建筑 run 与用户原件保留；本次没有重新设计或生成一栋建筑，没有修改网站、正式仓库或游戏世界。

优先打开交付的 `index.html`。本工程的逐栋证据见 `learning/case_registry.json`，开放反馈见 `learning/feedback_ledger.json`，能力分级见 `docs/haf_0_3_capabilities.json`。

## 本次实际变化

- 合并10个真实案例入口：深圳报业、广州周大福、首尔南山塔、大本钟、白金汉宫、南山云科技、广州新海关、中山纪念堂、珠江帝景、广州南站。广州塔/琶洲作为两个历史对照登记，完整原工程从归档清单恢复。
- 新增共享最终输出采样检查 `hafusion/review.py`：显式空气、完整方块承托、指定材料灯位；目前接入纪念堂与南站。未接入的案例保留各自既有检查，不假报全通过。
- 公共渲染入口新增 `ensure_review_views`，保留同框四向45°并强制真俯视 `top_day`；相机元数据可检查视角、框幅与NBT来源。旧专用渲染器需单独补齐，旧图按真实相机参数识别（兼容top/plan等名称），真正缺图仍pending。
- 更新两项已安装 Skill 为0.3.0：Architect编排与HA不限图研究。外部建筑AI六图资料Skill独立保留。灯光、裙楼、内饰等是模块，不另计Skill。
- 合并此前案例中已有的古典细部、场地预算、绿色玻璃/水体、原子网格写入与大场景渲染修复；不将其重复宣称为本次首次研发。

## 运行

使用 Python 3.12 与 NumPy、Pillow；历史依赖锁定文件保留，`support/deps`有原项目轻依赖。预览另需 Linux EGL/Mesa。当前环境实测信息在 `release/environment.json`。

```bash
python tools/agent.py --version
python tools/agent.py --list-cases
python tools/agent.py --catalog
python tools/agent.py --case guangzhou_south --run V1_r02 --review
python tools/agent.py --case guangzhou_south --run NEW_RUN
python tools/render_building_case.py --case guangzhou_south --run NEW_RUN
PYTHONPATH=support/deps python -m unittest discover -s tests -v
```

新生成必须用新run名。`--review`只读：缺契约或缺视图为pending，有已知错误为fail；不评定建筑还原度。导出后继续运行各案例README指定的完整验证和分块打包，不能只依赖共享采样。

`tools/validate_release.py`本次已执行，检查10份基线读回、10个入口导入、纪念堂/南站失败-修复对照及原run完整性。为保留已存报告，复跑前在新工作副本改报告输出路径；原报告不能被覆盖。它不是10栋整栋重建回放测试。

## 经验落地顺序

研究对象与范围 → 不限图证据/可选模型 → 分层平面与形体 → 占用和留空/接口 → 关键细部样板 → 完整生成 → 最终NBT与局部差分 → 日夜四向+真俯视/细节 → 用户分项反馈 → 游戏验收。

优先保存形体：主楼宽深/收分、露台占比、主次层级和镂空。然后处理幕墙、底面、背面围护、屋面接缝与柱脚；灯光在形体返工后独立复核。固定灯带有来源，窗灯/陈设可稳定随机；灯位存在不等于场景足够明亮。

## 真实验证边界

本次48个单元测试、25项发布检查通过。715个导入run文件哈希保持不变。共享规则检出纪念堂旧版166个无承托样点与567个缺失平台样点，修复版均为0；检出南站旧版4个门洞阻挡格位，修复版为0。另复验纪念堂原8项修复检查，旧版8项失败、新版8项通过。

这些数字不是还原准确率。海关只有形体获用户认可，裙楼和钟楼灯光仍待修；南站只在当前体量下获认可，细节继续保留。琶洲壳体感、伦敦纹理、周大福整栋夜景等没有被本次总结自动修好。

目前是人工研究驱动、可复用函数与多个案例适配器；通用自动语义分割、照片相机恢复、任意SU自动融合仍未实现。Minecraft运行、资源包真实纹理、碰撞和可玩性均待验。没有训练神经网络权重。

## 包装与来源

源码ZIP保留可执行代码、参数、研究记录、必要数据、基线/负例NBT、既有测试、许可和报告；为减小下载体积，不重复全部原图与大型预览缓存。`release/package_scope.json`逐项记录包含与排除，原图/旧完整工程可用 `release/original_archives.json` 的12份原归档恢复。当前截图缩略图只用于回顾，来源哈希单列在 `release/report_images.json`。

`ha03`、BuildKit序列化与PlanCraft依赖保留；开源来源和许可见 `ATTRIBUTION.md`，不把照片、字体、用户模型统一重新授权。所有原始ZIP保持原字节，发布清单记录其哈希。
