# BuildingSpec v0.1

Schema：`schema/building_spec.schema.json`，Draft 2020-12。协议源定义为 `tools/make_schema.py`，执行可重新生成Schema。本次使用真正的 jsonschema 库进行结构检查，再做跨字段语义校验。

## 顶层字段

| 字段 | 解释 |
|---|---|
| schema_version / spec_id / revision | 固定0.1、稳定项目ID和显式修订号 |
| mode / building | study或strict_reconstruction；名称、身份状态、现实指代和边界 |
| coordinates | 米制、局部坐标、front=-Z、blocks_per_metre、extent_m和size_blocks |
| environment | 游戏目标版本、DataVersion、是否真实核实、世界高度/原点、生成预算 |
| real_dimensions | 现实宽深高；值或范围、状态、依据和证据IDs；未知保留null |
| study_parameters | 单独的试建包围盒和假设依据；不得污染real_dimensions |
| evidence | packet哈希、原sources/facts/images、图像选择、旧构件ID及说明 |
| materials | 局部材质ID → 完整方块state、预览色和角色 |
| components | 稳定ID、类型、操作、参数、依赖、减法目标和证据性质 |
| levels / lighting | 声明楼层净空、照明构件位置；不意味着已做游戏光照或楼梯验收 |
| acceptance | 空气区、平面可达点对、最低声明净空、塔楼截面关系 |
| unresolved / deviations / review | 未知、适配偏差和严格复原人工审核状态 |
| output | Java结构NBT、是否写空气、固定5视角 |

`size_blocks=[X,Y,Z]`，与现实尺度表的宽/深/高顺序不同。`extent_m`是包含场地与余量的包围盒，不假称建筑实测尺寸。全部尺寸由统一 `s` 换算，`Q(v)=Decimal(str(v))*Decimal(str(s))` 再half-up；分别量化累计端点，不能逐段舍入后累加。真实尺寸、边界和比例冲突即报错，不暗中缩放。

## 旧研究包到施工协议

| packet v1.0 | BuildingSpec / 适配结果 | 规则 |
|---|---|---|
| packet_id / schema_version / 原始字节 | evidence.packet_id / packet_schema_version / packet_sha256 | 原包保持不变 |
| subject.name | building.name | 必须与overlay一致；不能把他楼资料接到当前案例 |
| sources / facts / images | evidence对应集合 | 原ID、状态、链接、许可字段及扩展原样保留 |
| scale.building_dimensions.width | real_dimensions.width | 精确确认值需对应verified事实；null保持未知 |
| scale.building_dimensions.length | real_dimensions.depth | 同上 |
| scale.building_dimensions.overall_height | real_dimensions.height | 不用roof/tip等其他高度偷换 |
| scale.selected_s | coordinates.blocks_per_metre | 有值则必须一致；无值由显式施工参数选择 |
| selection.slots | evidence.selected_image_ids | 只记录合格选择；不补造缺失图片 |
| components[].component_id | evidence.upstream_component_ids | 研究构件与可执行构件分开；不假装自然语言就是坐标 |
| gaps | unresolved | 原缺口合并保留 |
| prompts / report_sections / guidance | 保留在原包中 | 不能直接执行；用于AI/人工审核生成overlay |

施工overlay提供体量、开洞、楼板、材质与工程假设，不允许覆盖evidence或real_dimensions。该分层使接下来替换自然语言/多模态决策层时，生成引擎仍确定、可测试。

## 来源性质与模式

构件provenance允许 `confirmed / observed / estimated / design_choice / unknown / conflicted`。执行时unknown/conflicted必须先解决；confirmed要有关联verified事实。尺寸confirmed还必须匹配米制字段和值，不能用一句建筑风格描述替代尺度证据。程序只能检查证据结构与状态一致性，不能证明来源内容真的支持该数值；人工审核仍必要。

study允许现实尺寸未知，但必须有独立study_parameters与工程依据。严格模式要求身份已确认、真实宽深高有证据、没有试值覆盖、组件均确认、真实环境配置和放置边界已核实、人工审核通过。本次所有输出都是study，不冒充严格复原。

## 本地历史照片扩展

旧Skill假设已查看图片都具有网页source_ids，而R002是用户本地历史照片，公开原页未知。没有添加虚构URL，也没有修改旧Skill。

`packet_adapter.py`接受一个受限的**本地资料接入扩展**：图片声明local_file及local_sha256，路径必须在packet目录内且字节哈希相符，不能进入最终四图，quality.eligible必须false。只对旧验证器的“本地已查看图无网页来源”这一条明确报错提供接入处理；其他报错仍阻断。

结果记录 `partial_local_evidence_intake`，同时嵌入旧验证器原始FAIL；不是声称旧资料包通过完整研究交付门槛。原R002映射到img-R002并记录legacy_reference_id，原evidence.json和照片同时留存。照片支持四条局部形态观察；尺度仍全为null。工程overlay复用历史parameters.json中已标明assumed的值，新增构件仍为design_choice。

该扩展只支持局部研究上下文和明确工程假设；不授予照片公开展示、训练授权或现实身份确认。旧许可状态保持unknown、training_authorized=false。
