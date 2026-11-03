# 开发状态 · GAFAcraft Architect v0.1

日期：2026-10-20。当前可直接下载并验证的成果以`output/`、`reports/`和`REVIEW.html`为准。

## 已完成

- 读取三份交接、复用两份Skills和旧廊柱资料；118项继承测试通过。
- BuildingSpec v0.1 JSON Schema、语义门槛、packet到施工协议的有来源映射。
- 本地确定性参数引擎：box、凹多边形拉伸、定向减法开洞、多体量、矩形/椭圆变截面、楼板和简化竖梃。
- 便利店与塔楼主要样例完成NBT写出、独立读回、同源固定五视图与静态检查。
- 历史R002照片和明确标注的旧研究参数已接成第三个可执行样例；旧实现仍保存。
- 便利店r2局部雨棚修改，6个可见格变化，区域外0；r1保留。
- 新测试、失败修复记录、离线审阅页、源码与交接说明已交付。

## 未完成 / 不能宣称

- `pending_game_test`：Java客户端实际放置、Create导入、当前NeoForge/Create版本和注册表核实。
- 一句话/图片的自动模型服务：目前两个主要样例由本轮助手明确编写构件参数，不是已部署的自主图片理解流程。
- 严格现实复原：案例现实宽深高未知，均为study；没有测绘或多视角尺度证据。
- 塔楼的完整入口、楼梯、电梯、消防、室内和楼层间通达性；当前只是变截面结构段。
- 新引擎中的半砖/楼梯/栅栏/模组方块、方块实体、自动切片、任意曲面、内部增量重算。
- 网站真实源码审查、任务队列、用户账号、上传和发布；没有线上改动。
- 更新的Build_Engine_v0.1压缩包内容、历史711原文件未取得，未擅自推断它们的能力。

## 恢复工作时的命令

先按README安装依赖，然后：

```bash
python tools/run_tests.py
python tools/build.py examples/retail_store/building_spec.json --out output/next_store_v1
python tools/build.py examples/tower_segment/building_spec.json --out output/next_tower_v1
python tools/build.py examples/legacy_gafa_research/building_spec.json --out output/next_legacy_v1
python tools/revise_canopy.py --out output/next_canopy_v2
```

原始输出目录不可复用。修改参数须写新版本，运行后对照NBT、build_report、geometry_report与五视图。最终测试计数及运行时间见`reports/tests_final.json`，不得用本说明代替实际日志。

## 已发生的问题

第一轮新测试出现两项错误：旧网页型packet契约无法表示已查看的本地照片；一张塔楼右视图在后续检查时是零字节。前者用明确标注的本地资料接入扩展解决，保留旧验证器FAIL，不伪造URL；后者从不变的NBT重新渲染，字节哈希与原报告完全一致，加入缓存写入和PNG完整性检查。原因与修复记录见`reports/tests_first_run.txt`、`reports/preview_repair.json`。

旧工具审计日志、新引擎最终日志、修订差分、人工视觉检查说明同时保存。未通过的旧研究“完整交付门槛”不是引擎单元测试失败；必须保持这一区分。

下一轮首先做测试世界导入，然后开发可追溯的几何约束提取层，详见NEXT_STEPS。
