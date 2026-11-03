> 当前新项目使用 v1.1，参见 [reference-box.md](reference-box.md)。本文件保留 v1.0 兼容契约；四槽规则仅适用于 v1.0。v1.1 继承来源、事实、尺度、十节与许可规则，替换 selection 并改第五节标题。

# GAFAcraft 资料包数据契约 v1.0

目录：启动与校验｜身份、来源与事实｜候选图与四图｜尺度｜生成提示词与十节｜阶段与接口｜用户实验反馈｜限制。

这是 `references/packet-template.json` 的字段说明。复制模板形成每个项目的 `packet.json`，随后填充真实调查结果。模板不是已完成的建筑资料包，不含选定建筑、已核验图片或模型测试结果。所有未知标量保留 `null`，未知集合保留 `[]`，不要用 0、空字符串、“约100米”冒充数值；说明和缺口写在相邻的说明字段。ID 创建后稳定保留，不随排序变更，不复用给其他证据。新 ID 推荐使用连字符（如 `src-001`、`fact-001`、`img-001`、`component-001`）；已有下划线形式（如 `img_001`）同样合法并原样保留，不因格式偏好重命名来源身份。

## 1. 启动与校验

```bash
python scripts/validate_packet.py references/packet-template.json --mode template
python scripts/validate_packet.py /absolute/path/packet.json --mode report
python scripts/selftest.py
python scripts/scale.py --meters 100.5 --s 0.5
python scripts/scale.py --range 90 110 --s 0.5
python scripts/scale.py --packet /absolute/path/packet.json
```

以上 Python 脚本只使用标准库，不访问网络。`template` 模式允许尚未开始研究时的空值，但仍检查已填字段的矛盾；`report` 模式要求完整十节、能复制使用的长短提示词、四个选图槽位、必要的拆分决定。报告不完整并非失败：`PASS_WITH_GAPS` 允许缺图、尺寸待核实、世界余量未确认、阶段被前置条件阻塞。`FAIL` 表示存在矛盾、无效引用、伪核验或必要内容缺失。`PASS` 和 `PASS_WITH_GAPS` 退出码均为 0；`FAIL` 为 1。报告中的 `gaps[]` 为人工缺口，校验输出 `gaps` 为脚本发现的缺口，交付时合并说明。

脚本通过不等于资料被独立核验，也不等于建筑 AI 的成品已通过验证。网页、实图、引用是否支持结论、提示词对事实的忠实程度，仍需按 SKILL.md 人工检查。不要为取得 PASS 而补造缺失字段。

## 2. 身份、来源与事实

| 顶层字段 | 内容 |
|---|---|
| `schema_version` | 固定 `"1.0"` |
| `packet_id` | 项目资料包稳定 ID；模板为 null |
| `collected_at` | 本次采集日期；`YYYY-MM-DD` 或含时区的 ISO 时间，如 `2026-10-17T02:11:47+08:00` |
| `subject` | 名称、中外文别名、城市、`kind: single/complex`、身份确认状态、建成/设计版本、识别点、场地边界、三种面积 |
| `provenance` | 用户原始需求、来源对话 ID、`research_status: complete/incomplete` |
| `sources[]` | 来源页面与访问日期；每项使用 `src-…` |
| `facts[]` | 事实、图片观察、估算、建议、用户观察；每项使用 `fact-…` |
| `components[]` | 塔楼、裙楼、基座等对象；每项使用 `component-…` |

`subject.identity_status` 使用 `confirmed` 或 `provisional`。有重名时先结合上下文定位；确实仍有歧义再询问。临时识别不得写成确认事实。`subject.core_identifiers[]` 建议每条包含 `text` 与 `fact_ids`，按事实/观察/建议分别说明。`subject.boundary` 写研究和复原边界，不把背景建筑纳入主体。

一个来源条目结构：

```json
{
  "source_id": "src-001",
  "title": "原始页面实际标题",
  "url": "https://example.invalid/original-page",
  "publisher": null,
  "type": "architect",
  "accessed_at": "2026-10-17"
}
```

示例 URL 仅说明字段，不能进入真实研究成果。`type` 建议使用 architect / owner / government / drawing / professional_media / other。优先事务所、业主、政府、公示和正式图纸；专业媒体补充。未知发布者保留 null。

一个事实条目结构：

```json
{
  "fact_id": "fact-001",
  "field": "overall_height",
  "value": null,
  "unit": "m",
  "kind": "fact",
  "status": "unverified",
  "source_ids": [],
  "image_ids": [],
  "derived_from_fact_ids": [],
  "basis": null,
  "conflict_group": null,
  "adoption_reason": null
}
```

- `field` 可记录 location、function、designer、completion_year、floor_count、overall_height、roof_height、tip_height 等。年份和层数使用整数，设计单位/地点/功能用字符串，未知用 null；各项分别关联来源。
- `kind` 为 `fact` / `observation` / `estimate` / `suggestion` / `user_observation`；`status` 为 `verified` / `unverified` / `conflicted` / `proposed` / `user_reported`。非空事实须有 `source_ids`；图片观察须有图片或页面证据；估算须写 basis 并关联证据或派生事实；建议须写依据；用户观察必须保持 `user_reported`，不得升格为独立实测。
- 冲突数值逐条保留，使用同一 `conflict_group`；说明为什么暂采某值。被尺度换算采用的精确值须另行满足 verified 及 `adoption_reason`，不能静默删掉其他值。
- `subject.areas` 固定区分 `land_area`、`gross_floor_area`、`footprint_area`；每项 `{value_m2, fact_id}`。不要把总建筑面积当建筑占地，或用面积开平方捏造长宽。
- `components[]` 最少含 `component_id, name, parent_component_id, fact_ids`；未知父级为 null。可添加体量关系、识别点与外壳说明，标明其证据性质。

## 3. 候选图、核验与四图

每个候选图保留以下字段；真正缺失的文字用 null。仅搜索发现但原始页面尚未定位时，`page_url:null`、`source_ids:[]` 合法并列为缺口；不要填假链接或建立虚构来源。通过质量门槛并进入最终四图前，必须找到原始 HTTP(S) 页面：

```json
{
  "image_id": "img-001",
  "source_ids": ["src-001"],
  "page_url": "https://example.invalid/original-page",
  "direct_image_url": null,
  "creator": null,
  "media_type": "photo",
  "built_state": "constructed",
  "version": null,
  "view": null,
  "orientation": null,
  "covers": [],
  "component_ids": [],
  "verification_state": "discovered",
  "checked_at": null,
  "building_match_confirmed": null,
  "actual_pixels": null,
  "quality": {"eligible": null, "assessment": null, "limitations": []},
  "license_status": "unknown",
  "license_url": null,
  "training_authorized": false,
  "training_authorization_basis": null,
  "candidate_value": null
}
```

`media_type`：photo / site_plan / roof_plan / elevation / section / render / model / ai_image / unknown。建成状态 `built_state`：constructed / design / unknown。真实照片、图纸、渲染、模型、AI 图分别分组，图纸还要区分建成/设计版本。

| `verification_state` | 可以声称什么 | `actual_pixels` |
|---|---|---|
| `discovered` | 仅搜索发现，尚未核查原始页面 | null |
| `page_viewed` | 页面已访问，大图未核实 | null |
| `full_image_viewed` | 已查看实际大图，逐项记录视角、内容与限制 | 实际可见 `[宽px, 高px]`；无法确认仍为 null |
| `inaccessible` | 已知无法访问；写明限制，不绕过登录/访问控制 | null |

`quality.eligible:true` 仅在看过大图、记录实际像素尺寸、确认同一建筑且视角/朝向/覆盖内容/版本可说明时使用。未看到大图不得声称 high_quality。限制包括遮挡、透视强、画质低、主体小、后期过度、设计版本不同等；“正面”不足以说明朝向时，把可确认的相对方向写清并说明无法对应地理北向。`version` 可以是“同一建成版本待日期确认”这类带限制的实际观察，不编造日期。

`license_status`：unknown / permission_granted / licensed / public_domain / restricted。公开访问不代表训练授权；未知或受限许可不得设置 `training_authorized:true`。有训练授权仍需 `training_authorization_basis` 明确依据。只保存链接和元数据也能形成有效资料包，不要求下载图片。

`selection.slots` 固定四个槽位，编号就是建议上传顺序：

```json
{"slot": 1, "image_id": null, "purpose": null, "rationale": null, "missing_search": "查找同一建成版本、可辨识全部主体相对位置的总平/屋顶俯视"}
```

不足四张时 image_id 保持 null，missing_search 给出具体方向；有图时填写用途和筛选理由，引用通过质量门槛的稳定 ID。最终四图仅使用照片及明确标注的正式几何图纸，render/model/ai_image/unknown 保持独立候选，不得拿来填真实参考图缺口。先过质量门槛，再比较新增几何信息，不能只因清晰就选四张相似图。

依据本轮实际生成单元选图。单体争取3—4张合格互补的主体图，优先完整全貌、不同方向全貌、关键结构近景、尚缺主体部位；不固定占一槽给场地，不用附属图或重复近似图填补主体缺口。四槽可不足，不能为达到数量降低质量门槛。整体综合体的总平阶段优先总平/俯视、整体鸟瞰、主塔近景、裙楼/基座近景；单体阶段重新选该单体的主体图，共享总平仅在确有定位必要时占最多一槽。纯场地/附属图默认仅为补充，用户明确聚焦场地或有不可替代布局/连接约束时才占槽，并在 rationale 解释。

沿用 `images[].covers`、`candidate_value`、`quality.limitations` 与 `selection.slots[].purpose/rationale` 说明主体覆盖、互补角度和未入选原因；在 `consistency_checks.notes` 记录整体视角不足、主体过小或附属图过多等问题。不要虚构测得的主体面积百分比或网站图片权重，不需要为这一选图策略新增数据字段。脚本不能判断图片是否真正聚焦主体，必须人工看图核对。

`consistency_checks` 对版本、主体干净程度、朝向统一给 true / false / null；关联总平依据、裙楼近景及至少两个互证外壳视角的 image_ids。失败或未知写入 notes 与第⑨节。`target_image_limit` 只填用户已确认的工具限制，未知 null；少图上传时取槽位前 N 张，在 `omitted_constraints[]` 写明每个未上传 image_id 及因此缺失的几何约束，提示词同步解释。

## 4. 尺度、范围与误差

`scale.building_dimensions` 分别记录 width、length、overall_height、architectural_height、roof_height、tip_height；`site_dimensions` 单独记录 width、length。`overall_height` 是本次主体包围盒的总高；天线/尖顶纳入范围时必须含其顶端。architectural_height、roof_height、tip_height 各自保持原始来源定义；不要假定它们相等。

每个测量为 `{value_m:null, range_m:null, fact_id:null, basis:null}`。精确 `value_m` 仅连接同值、单位 m 的已核实事实；估算使用 `[下限,上限]` 的 `range_m`，匹配事实/估算 value，填写依据、误差来源与端点敏感性。两者不可同时填。测量还必须匹配事实的 field：建筑字段允许同名（如 `overall_height`）或限定名（如 `building_dimensions.overall_height`）；场地字段必须用 `site_width` / `site_length` 或 `site_dimensions.width` / `site_dimensions.length`。数值恰好相等不能用 width 事实证明 height，也不能拿建筑宽度冒充场地宽度。没有可靠尺度和估算依据时两个都 null，不勉强给区间。

`s` = 每米方块数。可在 `ratio_candidates[]` 比较 `{label:"1:1",s:1}`、`{label:"1:2",s:0.5}`、`{label:"2:1",s:2}`；模板保留空数组。取整固定 `half_up`，例如 2.5→3。每条 `conversions[]` 结构：

```json
{
  "target": "building_dimensions.width",
  "s": 0.5,
  "blocks": null,
  "blocks_range": null,
  "error_m": null,
  "error_range_m": null
}
```

有已核实值：`blocks=round_half_up(value_m*s)`，`error_m=blocks/s-value_m`；有范围则分别计算端点到 `blocks_range` 和 `error_range_m`。不要用缺失实际尺寸导出精确方块数。`scale.py` 返回可复用计算结果；调用后把目标字段补入转换记录。`uncertainty[]` 记录敏感性和缺口；`local_exaggerations[]` 记录仅供选择的可读性夸张、影响部位及偏离比例，默认不启用。

`world_budget` 按 width / depth / height 记录 `{blocks,confirmed,basis}`，它代表用户明确确认的可用建造余量，不是版本总高度。`confirmed:true` 需要具体方块数和确认依据。未确认约束不参与比例上限计算。

统一比例上限为已知约束中的最小值：宽度用建筑与场地已知宽的较大值，进深用二者已知 length 的较大值，高度用 overall_height；范围测量用上界保守计算。`uniform_scale_max` 保存结果，完全无法计算时 null；`selected_s` 不得超过它。没有上限不等于任意比例都能落地，必须说明尚未确认哪些余量。

## 5. 提示词、指导与十节报告

`prompts.full` 与 `prompts.short` 都必须在开头用具体建筑实名声明原型复刻标准、强制使用本次已核验入选参考、禁止擅改原型设计。锁定有证据的关键几何、立面、材质配色及标志性地景，并与 `subject`、事实、选图和尺度一致；另写用户授权的统一缩放/改色/范围调整、方块化与标注为合理补全的未知内部/场地。不得凭该措辞补造事实、掩盖缺图或越过 blocked 阶段。沿用现有文本字段，不新增伪造核验状态；这些约束需人工语义核对，脚本通过不表示外部模型会遵守。

`prompts.full` 和 `prompts.short` 在模板里为 null；真正报告必须写出可复制的具体文本，不能原样输出模板字段。脚本用完整提示词至少100字符、短版至少35字符作最低空壳筛查；这只是启发式检查，不证明内容完整或提示词有效，仍须人工核对。允许明确的“长度未核实，先保留统一比例，不进入尺寸定稿”等待定约束，禁止擅自补事实。两段都要包含建筑身份与每个已选 image_id 的用途关系；`prompts.image_ids` 必须正好对应四槽中非空 ID。若提示词需要明确警告某候选图不可使用，在 `prompts.excluded_image_ids[]` 列出该已有候选 ID；它不能同时入选四图。正文必须明确说明该图未核实/不合格并禁止其作为生成依据。脚本检查 ID 与排除记录的结构一致性，排除语义仍需人工审读；不要把已排除 ID 写在肯定的参考图指令中。未入选且未列入 excluded 的 ID 不得出现在提示词中。引用的材料、内部、照明建议要保持生成建议性质。

完整版默认采用 `architectural-brief.md` 的详细建筑说明策略；以上100/35字符仅用于发现空壳，绝不是写作长度目标。设计风格、构思、外墙层次、空间体验与方块化动作沿用现有 `facts[]`、`report_sections[2]`、`prompts.full` 和 `guidance` 字段，不引入另一套互相漂移的事实表。可用 `field: design_style / design_intent / facade_layers / spatial_experience / construction_translation` 区分内容，但仍逐条标注 kind、status、依据与来源。声称“建筑师的灵感”必须有明确归属的来源；媒体解读保留媒体归属，图片观察不能自动成为动机事实，施工建议使用 suggestion。第⑥节应独立承载必要建筑说明，不能只依赖第③节；第⑦节精简时保留所有决定生成边界的硬约束。缺构思或构造资料时用 null/未核实，不为增加篇幅把猜想填成事实。

`report_sections` 固定十节，每项 `{number,title,content,fact_ids,image_ids,source_ids}`；编号顺序与模板一致，不删除空缺章节。第⑥⑦节 content 分别等于完整/短版提示词正文。其他章节通过就近 `[src-001]` 等标记或最终可点击来源链接，使事实和图片能回到证据；section refs 用于机器追溯，不能取代面向用户的就近引用。

`guidance` 保存 scope / quality / height / site / landscape / interior / lighting 与 material_mappings。区分轮廓、节奏、细节的保真顺序；未给工具参数时用通用语义，不编造网站控件/范围。内部未知内容明确“合理补全”；玻璃幕墙不要整面发光，照明不改变外壳轮廓。默认范围是建筑＋配套地景，包含入口铺装、步道/道路衔接、绿化及适用的台阶、高差、边界过渡；有证据才把水体等写成现实特征，背景建筑只定位。

`guidance.landscape` 是 v1.0 的向后兼容扩展，旧资料包可缺省；新资料包从更新模板填写。`enabled:true` 是用户指定的默认交付策略，不是已经完成地景的事实；仅在用户明确要裸模、仅建筑主体或不含场地时设为 false，并在 `omission_reason` 记录要求，其他内容不能因此推断。`boundary` 描述地景范围（未知 null）；`elements[]` 每项写 `{name,kind,fact_ids,basis}`，kind 使用 fact / observation / estimate / suggestion 并遵守事实证据契约，缺证据的布局标 suggestion 和合理补全，不填虚假事实引用。`reference_image_ids[]` 可关联已记录的地景补充图，不会自动加入 `prompts.image_ids` 或四图上传组。`access_connections[]` 写入口到步道/道路的连接，`terrain_notes` 写地形、高差、共用地面基准及未知项，`acceptance[]` 写通行、地面衔接、绿化不遮挡主体和范围预算等验收条件。未知标量 null，尚未形成的集合 []；不编造精确用地大小。

`guidance.site` 保留场地摘要，与 landscape、尺度及阶段内容一致。长短提示词都包含具体且简洁的地景要求，主体验收后再完成地景；默认不能只生成裸建筑或空白底板，也不扩建大片附属区域。`landscape.enabled:true` 不要求用地景图占据上传槽位。总平缺失时仍可提供可编辑的合理补全地景方案，但真实坐标/高差保持未核实，不能越过依赖准确总平的阶段。该扩展目前依靠人工语义核对，结构校验器通过不表示地景字段或成品已验收。

`risks[]` 每条 `{risk,symptom,correction}`；写具体风险→可见症状→纠正措施。可附 evidence_ids，但不得把尚未生成或用户未反馈的现象写成已发生实测。

## 6. 分阶段坐标与接口

`staging.required` 在报告里必须 true/false，并提供 reason。简单单体无需强行拆分：false、充分理由、stages=[] 即可。综合体是否拆分依据塔数、相对位置、复杂裙楼与工具混淆风险，不仅看标签。

`coordinate_system` 统一 origin、x_axis、y_axis、z_axis、north、s；约定坐标数组 `[x,y,z]`，y 竖向；包围盒 `[宽,高,深]`。方位尚未确认可保持 null，使阶段 blocked，不编造项目实际方位。

每阶段必含：

```json
{
  "stage_id": "phase-1",
  "name": "统一坐标、比例、总平与占位",
  "depends_on": [],
  "component_ids": [],
  "origin": null,
  "orientation": null,
  "bbox": null,
  "interfaces": [],
  "acceptance": ["总平、同一比例和各体量相对位置确认后进入单体阶段"],
  "readiness": "blocked",
  "blocked_reason": "实际尺度和统一朝向尚未核实"
}
```

阶段顺序依需求为总平占位→各单体主结构→裙楼/基座/连接→外壳细节→场地/内部/照明。depends_on 只能引用前置阶段。ready 阶段不得依赖 blocked 阶段，必须有具体整数 origin / bbox、orientation、完整共享坐标系与同一 selected_s。共享 origin 必须恰好为三个整数，x/y/z 轴说明和 north 均须非空，三轴不得用相同方向说明；每阶段 orientation 也必须非空。脚本仅能排除空方向和字面相同的轴，真实正交关系及地理方位需人工确认。blocked 仍必须记录字段及验收条件，但未知几何可 null；这使研究不完整时仍能交付可信阶段方案。

接口项使用 `{interface_id,with_component_ids,location,description}`；location 可为明确坐标或几何边界描述，ready 阶段不得留空。无接口使用 [] 并在正文说明无连接。阶段原点是共享坐标中的位置；可选阶段字段 s/coordinate_system 必须与共享值一致，不通过另建独立坐标偷偷缩放。

## 7. 只记录实际用户实验反馈

`experiments[]` 留空直至得到用户实际反馈；创建本工作流不产生实验结果，也不等于训练模型。用户既往观察可在 workflow 的经验说明中保留，不自动转换成独立性能测试。

每条结果需要 `evidence_type:"user_feedback"`、`feedback_quote`（保留实际反馈原文）、`claim_scope:"user_observation"`、`feedback_date`（未知为 null）、`provenance:{type:"user_message"或"provided_context",reference:"实际消息/来源上下文定位"}`。可增建筑名称、工具及版本（未知 null）、采用图集 IDs、用户描述的结果和后续建议；结果与建议分开。没有真实反馈来源，不写“已测试成功”“还原度提高”等结果。

## 8. 校验能力边界

脚本检查十节结构、状态与引用、空缺与补检方向、未核验图进入最终推荐、事实来源、缺尺度却导出精确数值、换算与约束、阶段前置/坐标一致性、反馈溯源。它不能代替真实页面阅读、看图、建筑专业判断、版权许可审查或 Minecraft / 外部生成器实测。对纯文本中隐蔽的未核实事实需人工复核；不得宣传为自动事实核查器。
