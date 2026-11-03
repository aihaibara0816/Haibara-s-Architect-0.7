"""Create the V5 ten-section source and decision report from retained inputs."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parents[1]
refs=json.loads((ROOT/'inputs/podium_images.json').read_text())
old=json.loads((ROOT/'inputs/image_manifest.json').read_text())
chosen=[]
for r in refs['images']:
    if r['image_id'] in ['N05','N04','N03','N06','P08','P09','P10','FB-U03','H01']:
        chosen.append(r)
for r in old['images']:
    if r['image_id'] in ['R08','R14','R16']:
        chosen.append({'image_id':r['image_id'],'title':r['title'],'image_url':r['direct_image_url'],'source_page_url':r['page_url'],'local_path':r['file'],'sha256':r['sha256'],'width':r['pixels'][0],'height':r['pixels'][1],'photographer':r['credit'],'publication_date':None,'visual_status':'viewed in inherited study','verification_status':r['verification_state'],'selection_status':'design_reference' if r['image_id']=='R14' else 'selected','evidence_role':'inherited tower constraint','license':r['license_status'],'observation':r['observation'],'media_type':r['media_type']})
manifest={'title':'广州塔 V5｜融合采用的参考资料','images':chosen,'scope':'8 current podium core views + 1 historical interface photo + 3 inherited tower constraints. R14 is a design drawing, not an as-built photograph. Other retained candidates remain in inputs but are not all uploaded as core references.'}
(ROOT/'inputs/v5_reference_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
e=html.escape
cards=''.join(f'<figure><h3>{e(r["image_id"])} · {e(r["title"])}</h3><img data-gafa-image-id="{e(r["image_id"])}" src="{e(r.get("image_url") or r["local_path"])}" alt="{e(r["title"])}"><figcaption>{e(r.get("observation",""))}<small>{e(r.get("photographer") or "用户提供；原始作者待核实")} · 发布日期 {e(str(r.get("publication_date") or "待核实"))} · <a href="{e(r.get("source_page_url") or "#")}">来源页</a>。尺寸与朝向未作实测标定。</small></figcaption></figure>' for r in chosen)
sources='<ul>'+''.join(f'<li>{k}：<a href="{e(v["url"])}">{e(v["title"])}</a>（{v["date"]}）— {e(v["role"])}</li>' for k,v in refs['sources'].items())+'</ul>'
body='''<h1>广州塔 V5<br>构件融合与场地层级记录</h1><p>2026-10-21 · 最终 V5_r02 · 图片研究 / 可选模型研究 / 方块几何</p>
<p class="note">本版依据用户当前范围：制作广州塔及其广场，只保留一楼往上的结构与设计；省略 −1F 下沉区域和地下内部。这里将两个椭圆底面截在一楼，并保留通向上层平台的台阶和边缘。这是明确的范围适配，不能把它称为现实广场的完整竣工复原。</p>
<h2>① 建筑概览与核心识别点</h2><p>主塔沿用经核查的 SKP 构件走势、V3a 镂空楼层和 V4 内侧环梁，塔冠沿用 V2A 的斜面拟合。V5 的主要修订集中在塔脚与广场：同一首层地面、上层平台承托、独立绿地分区、曲线步道、差异化椭圆边缘和池边斜玻璃顶。</p><p>资料没有“全部取平均”。主柱空间走势依模型，局部层次依照片，年代与范围冲突按本次任务裁决。下文记录哪些信息被采用，哪些仍然只是估算。</p>
<h2>② 可靠尺度与 Minecraft 比例建议</h2><table><tr><th>对象</th><th>执行值</th><th>依据与限制</th></tr><tr><td>塔体高度</td><td>280 格，结构最低单元 Y=2，尖端 Y=281</td><td>沿用研究实验条件；相对既有 600 m 口径约 0.4667 格/m，SKP 路线保留原归一化</td></tr><tr><td>整体包围盒 X/Y/Z</td><td>128 × 282 × 232</td><td>工程坐标，不等于实测用地长宽</td></tr><tr><td>首层 / 上层平台</td><td>行走面 Y=2 / Y=7</td><td>本次可编辑估算；每层 5 格差不是现场层高结论</td></tr><tr><td>屋面绿地</td><td>主要表面 Y=8，下方有土层与平台</td><td>8 组独立曲线区域；另有地面绿化，不把所有绿地统称为二楼</td></tr><tr><td>两个椭圆底面</td><td>统一截在首层行走面 Y=2</td><td>用户排除 −1F 的适配，不向下挖商业层</td></tr></table><p>方向沿用研究坐标 +Z 朝南广场，未标定地理北向。核心图 N05 是近垂直航拍，不能当作有比例尺的正射总平图。</p>
<h2>③ 设计语言、材料与结构</h2><p>塔身外斜柱、内侧环梁、核心筒和局部玻璃层分别表达。除低位首层接口外，Y≥12 的塔身方块状态与 V4 对齐后完全一致；不会为优化广场同时重做塔冠或把开放段重新封成幕墙。</p><p>场地以灰色铺装、浅色边缘、自然绿和透光玻璃形成层次。曲线种植区先建立承托，再放树木；首层玻璃立面与上层种植屋面区分。雨棚采用薄台阶边与玻璃，中轴池边使用两条斜玻璃顶，不再把所有小玻璃体量解释为同一种入口亭。</p><p>设计方的早期主题“珠水涟漪、舞动花城”仅用来辅助理解曲线语言，不能替代建成照片中的边界。来源 S3；平台与商业层级以 S1/S2 交叉核对，实景细节依 S4/S7。夜景暖色不直接变成日间材质，活动橙色地毯不加入永久方案。</p>
<h2>④ 参考图片候选分类</h2><table><tr><th>任务</th><th>采用</th><th>限制</th></tr><tr><td>总体与多标高</td><td>N05、N04、N03、N06</td><td>2024 开业实景；没有精确尺寸和相机配准</td></tr><tr><td>雨棚、台阶与池边</td><td>P08、P09、P10、FB-U03</td><td>2025 照明案例与用户图；夜景仅判层次与灯位</td></tr><tr><td>塔脚历史关系</td><td>H01</td><td>2019 年照片；不直接复制其旧广场总平</td></tr><tr><td>塔身镂空与顶部</td><td>R08、R14、R16</td><td>沿用已有核查；R14 是设计图，不是已测定楼层表</td></tr></table><p>旧文件、原始 SKP、所有已保存候选图保留在 inputs。重复裁剪 FB-U02 与 N03 不当作两份独立证据；未定位的室内图不转换成准确内装或房间图。SKP 背景地形不能冒充新广场。</p>
<h2>⑤ 核心参考图与覆盖分析</h2><p>以下 12 张收录资料由 8 张场地核心、1 张历史接口补充和 3 张继承塔体约束组成。逐图保持原字节、尺寸和来源；未取得的图纸仍是缺口。多向参考盒用于关联构件和遮挡关系，没有进行像素自动拼接、摄影测量或语义模型训练。</p>__CARDS__
<h2>⑥ 完整生成提示词</h2><pre>以中国广州的广州塔及本次确定的 2024–2025 南广场实景为标准进行复刻，必须依据本次已核验且入选的参考资料，不能擅自修改原型设计。允许的适配仅包括本轮明确的 280 格统一研究尺度、方块化取整，以及用户要求省略地下与 −1F 区域。缺少实测的尺度和层高用估算参数保留，不能说成实测事实。

先恢复 V4_r02 主塔，保持 24 条经审查的模型主柱路径、内侧环梁、独立核心筒、3×3 预留竖井、功能区分段玻璃和倾斜塔冠。采用 R08/R14/R16 判断核心、镂空与围护的关系；开放高度不增加连续幕墙。塔冠保留 V2A 斜面及 16 个示意球舱。模型中的球舱候选与背景不能未经核对直接复制。

用 N05 控制场地整体顺序及两侧曲线绿地，用 N04/N03/N06 交叉理解塔脚、首层与上层平台。明确首层行走面 Y=2，上层平台 Y=7，这是本次估算的方块参数。首层及以上保留，椭圆底面截在一楼，不生成负一层房间、向地下的台阶或深坑；保留上层平台边缘和向上的通路。建立塔脚与平台接口，再拼入塔体，不把整座塔简单放在一张平板上。

按构件分开处理。两椭圆使用不同半径与方向；上方轻质波形棚由 P08/FB-U03 约束，保留浅色边缘、玻璃与斜支承。P09 约束映塔池与两侧斜玻璃顶。绿地分成曲线区域，记录每一片的承托平台、标高、边界、穿行路径和树木，不用规则直草条代替整个景观。H01 只用来确认塔脚与抬高平台的历史连接关系，不复制 2019 旧场地布局。商业内部只做可见边缘和简化支承，不编造完整商铺。

材料统一为克制的灰色铺装、浅色结构边缘、自然绿与透光玻璃。只在真实功能层、首层檐下、雨棚和步道布置发光方块，禁止让整片玻璃发光，排除活动地毯和夜景偏色。外部道路、滨江新改造、无关建筑与地下内部不纳入。

生成新 run，保存稳定构件归属、参数、来源与采用理由。独立回读最终 NBT，检验 280 格塔高、上部塔身保持、开放楼层和竖井、台阶两格净空、树根承托、水池围合、灯源及分块精确拼合。用最终 NBT 生成日夜全景、近景、正交俯视和显示剖切；所有隐藏与示意材质必须说明。材料按回读数据统计，游戏导入未做就标 pending。</pre>
<h2>⑦ 短版提示词</h2><pre>以广州塔和本次已核验南广场实景为标准复刻，必须使用入选参考，不得擅改原型。保留 280 格 SKP 主柱走势、内侧环梁、分段镂空与 V2A 斜冠；按 N05/N04/N03/N06 构建塔脚—首层—上层平台，P08/P09/P10/FB-U03 校正雨棚、池边与材质。绿地按承托面分区。只做一楼往上，双椭圆底面截在一楼，不生成 −1F；尺寸与高差标估算。实际灯源、NBT 回读、分块拼合、材料统计、全景／俯视／近景／夜景及反馈记录一并交付。</pre>
<h2>⑧ 规模、质量、场地与内部空间</h2><p>V5_r02：118,566 个非空气单元，其中水源 696 个，固体材料 117,870 个，实际发光方块 354 个。整包 NBT 为 359,037 bytes；另分成 5 个塔段与 4 个场地区块，每块不超过 1M 包围盒单元与 256 KiB。分块偏移见 placement_manifest.json，整包与分块二选一。</p><p>仅含一层薄基础底皮，不包含地下使用空间。稀疏 NBT 不清除原有方块，请在净空区域测试。如果世界上界是 Y=320，整体原点 Y 需 ≤38，同时核对世界下界。原版结构方块尺寸不适合直接放置本体量；具体导入器尚未在用户游戏环境验证。</p>__MATERIALS__
<h2>⑨ 风险、失败排查与查漏补缺</h2><p class="warn">15 项文件与几何检查通过，不等于现实精度或 Minecraft 游戏验收。首轮发现南端两组阶梯交接错一级，V5_r02 已修正。独立运行重放与最终预览按同一几何哈希核对。</p><p>遗留限制：46 道等距环梁未恢复真实倾角和变间距，旧核心筒与部分内环仍有接触，独立闭环不能宣称解决。玻璃、墙/栏杆邻接、台阶碰撞、流体更新与真实照明待游戏测试。此版没有 RGB 灯光秀、物理池面倒影、完整商业室内或实测场地曲线。</p><p>本轮美学目标是层级、空实、色彩和边缘表达一致。是否比 V4 更符合你的审美仍等待反馈；不能以测试数量、照片数量或“融合”一词代替视觉评价。</p>
<h2>⑩ 拆分顺序、代码入口与下一次反馈</h2><table><tr><th>层次</th><th>文件 / 构件 ID</th><th>下一步如何改</th></tr><tr><td>模型与已稳定塔身</td><td>src/model_route.py、hybrid_geometry.py、open_lattice.py、v4_geometry.py</td><td>本轮继承；上部不随广场改动</td></tr><tr><td>塔基、平台与绿化</td><td>src/v5_geometry.py、inputs/v5_parameters.json</td><td>按 tower.base.interface、podium.*、landscape.*、court.* 局部修改</td></tr><tr><td>生成与验证</td><td>src/build_v5.py、runs/V5_r02/</td><td>用新 run，独立回读与重组，保留失败记录</td></tr><tr><td>来源与取舍</td><td>inputs/v5_reference_manifest.json、runs/V5_r02/component_decisions.json</td><td>保留采用、排除、年代和未知；不改原图</td></tr><tr><td>审美反馈</td><td>全景细节与反馈 HTML、feedback/feedback_template.json</td><td>记录构件、图号、保留/调整/替换及理由，导出 JSON</td></tr></table><p>后续优先用同相机游戏截图检查塔脚关系和首层通行，再校对绿地走向、雨棚厚度、环梁与核心筒。只有新证据才能提升真实性评级；本次把观察整理为 Skill 规则，不声称训练出全自动审美融合引擎。</p>
<h3>来源索引与版本边界</h3>__SOURCES__<p>照片与模型权利保持原状；归档用于本次建筑研究与可回顾交付，不代表公开再发布或训练授权。</p>'''
body=body.replace('__CARDS__',cards).replace('__SOURCES__',sources)
out='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州塔 V5｜融合取舍与参考资料</title><style>__FONT_CSS____CSS__</style></head><body><main>'+body+'</main></body></html>'
(ROOT/'reports/research_draft.html').write_text(out)
print('V5 ten-section source report; 12 original references')
