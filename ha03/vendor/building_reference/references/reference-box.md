# 多向参考盒 v1.1

保留旧来源、事实、尺度、许可与十节机制。不是自动相机恢复/图片识别器，方位、内外层和遮挡由实际看图后标注。复杂建筑核心约十张是目标而非配额；细节图单独分组，不能用同角度重复图片凑覆盖。

## 输入与迁移

新建使用 packet-v1.1-template.json；旧 packet-template.json / schema_version=1.0 继续按四槽校验。运行 `python scripts/migrate_packet.py old.json new.json` 保留原包和 legacy_slots，不编新增照片。迁移图默认 face=unknown，补充实际判断后才填已知方向。

## selection 字段

- core：`{image_id,purpose,rationale}` 数组，可为空。不含重复ID或已声明duplicate_of的图片。同SHA字节不能多次进入核心组。
- detail_groups：`{component_id,image_ids,purpose}`。组件必须存在，图ID保持原身份。
- views：每张候选可有一条标注，所有入选核心/细节图必须有。字段为 `image_id,face,orientation_basis,layer,occlusion,component_ids,duplicate_of,sha256`。
- face：front/back/left/right/top/oblique/interior/unknown；前后是项目局部轴，不默认等于南北。已知face必须记录判定依据。layer为outer/inner/mixed/unknown；occlusion为none/partial/heavy/unknown。
- duplicate_of 指向保留的图ID。字节SHA用于完全相同图，裁剪/压缩/近似图由人工比对后记录关系；程序不提供感知去重。重复不增加coverage，heavy遮挡也不算该方向已覆盖。
- coverage_requirements：`{face,component_id,missing_search}`；component_id可null。程序以入选图和标注计算coverage。缺图写gap；unknown永远不能被视为已覆盖。
- consistency_checks、target_image_limit、omitted_constraints继承v1.0。约十图不是下游单次请求配额；按任务分批引用，限制确实存在时记录省略的信息。
- prompts.image_ids 必须等于core和detail_groups的并集；长短提示词逐个关联实际使用ID。第⑤节标题为“核心参考图与覆盖分析”，其余九节不变。

本地上传图可带local_file（packet目录内相对路径）和local_sha256。验证器必须获得packet所在目录并核对字节，不能虚构网页来源。实际查看、尺寸、身份和许可门槛仍适用；本地文件哈希通过不等于已看图或已获训练许可。

## 操作与回查

运行 `python scripts/validate_packet.py packet.json --mode report`；template仅检查已填字段，不代表十节交付完成。所有图有来源/限制/不确定性；浏览器照片的透视不能变成假正交坐标。内外层标注是观察，不推断隐藏构造。

生成后，将参考ID关联实际component_id与同一build_id的预览。真实对照需要人工finding、相机可比性和pass/needs_revision/unverifiable/pending状态。程序只能检验引用及状态一致性，不能证明“像”。若采用Architect 0.2，可使用其reference_review工具；本Skill不自带建模器或游戏客户端。

评估：旧4槽迁移、单图711缺背面、4–6图店铺、十图塔楼+额外塔冠、重复/裁剪图、年代冲突、重遮挡、未知朝向、本地上传哈希错误。不得把合成夹具测试标成真实建筑精度评测。

历史ID（如R01）在v1.1原样保留；新ID仍推荐img-等前缀。来源访问日期未知用null并记gap，不能据此声称已核实事实；verified事实至少需要实际访问日期的来源。
