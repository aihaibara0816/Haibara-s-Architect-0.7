"""Research decisions and editable feedback for the two authored London cases."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
DATA={
'elizabeth_tower':{
 'name':'大本钟 · 伊丽莎白塔','stem':'Elizabeth_Tower_HAF_V1',
 'scope':'192 格钟楼、四面钟盘、钟室、塔内楼梯候选与截断的邻接翼楼。邻翼用于连接关系测试，不是完整威斯敏斯特宫。',
 'sources':[
  ['parliament_dimensions','https://www.parliament.uk/about/living-heritage/building/palace/big-ben/facts-figures/','议会官方：塔高 96 米、四面钟盘，每面直径 7 米。'],
  ['restoration','https://purcellarchitecture.com/project/elizabeth-tower/','修复建筑师图库：整塔、钟盘、钟室、金属屋顶、内部及夜景。'],
  ['blue_restoration','https://www.parliament.uk/about/living-heritage/building/palace/big-ben/elizabeth-tower-and-big-ben-conservation-works-2017-/turning-big-bens-clock-dials-blue/','修复后蓝色与金色装饰的证据。']],
 'decisions':[
  ['tower','高 96 米 × 2 = 192 格；横断面与分段高度由照片估计。','parliament_dimensions;bb_purcell_02','frame; tower','Tower.shaft / belfry_roof','高；局部分段中'],
  ['clock','四个 14 格直径乳白钟面，蓝色静态指针、金色边框，统一背光。','parliament_dimensions;bb_purcell_03;bb_purcell_08','tower.dial_diameter_blocks; tower.clock_time','Tower.clock','高；数字简化'],
  ['belfry','实体角部围合开敞钟室，窄开口、铁栅屏和五个静态钟形。','bb_purcell_01;bb_purcell_07','tower.belfry','Tower.belfry_roof','中'],
  ['roof','深色分段金属屋顶；上尖顶拉高，灯笼缩短，蓝金集中在饰带。','bb_purcell_02;bb_purcell_10','tower.lower_roof; lantern; upper_spire','Tower.belfry_roof','中；不是精确铸铁花饰'],
  ['night','钟面与 Ayrton 灯为重点；塔身较暗，内部有服务灯。','bb_purcell_11','seed; material emission','Tower.clock / belfry_roof / shaft','中；非游戏光照'],
  ['context','仅制作邻接翼楼片段；内部楼梯为可检视候选。','bb_site;bb_purcell_04','case source constants','Tower.context / shaft','低；不复刻真实楼梯步数']
 ],
 'limits':['14 格钟盘不能完整写出罗马数字，刻度与浮雕均简化。','尖顶、钟室分段高度、邻翼细节仍是照片解释；未使用测绘模型。','塔内楼梯未做玩家通行、碰撞或消防式通路验收；钟不会走时或报时。'],
 'changes':['r01 → r02：缩短钟室与灯笼，拉高上尖顶，去掉宽蓝色屋顶条纹。','r01 → r02：钟盘加入连续背衬，避免透出零散灯块；补齐邻翼端面的窗列。'],
 'next':['钟面数字与花饰的更细尺度局部样板。','对照正视照片校准各段高度与屋顶折点。','游戏内检查钟室开口、楼梯和夜景亮度。']},
'buckingham_palace':{
 'name':'白金汉宫','stem':'Buckingham_Palace_HAF_V1',
 'scope':'216 格宽主正面、地图轮廓内院与侧翼、前庭、简化维多利亚纪念碑和花园边缘。不是全园、全部街区或真实 775 间室内。',
 'sources':[
  ['royal_dimensions','https://www.royal.uk/royal-residences-buckingham-palace','王室官方：主立面宽 108 米，主体进深约 120 米（含内院）、高 24 米。'],
  ['listing','https://historicengland.org.uk/listing/the-list/list-entry/1239087','Historic England：正面 3—7—3—7—3 窗列、中央与两端构图；花园面有弧形凸部。'],
  ['east_history','https://www.rct.uk/visit/buckingham-palace/history-of-the-east-wing-of-buckingham-palace','Royal Collection Trust：东翼与内院的历史关系。'],
  ['bp_access','https://media.rct.uk/sites/default/files/2025-08/Buckingham%20Palace%20-%20Access%20Guide_Photo%20Journey_2025.pdf','官方参观图解：只查看第 10、18 页，采用入口雨篷关系。'],
  ['osm','https://www.openstreetmap.org/copyright','平面数据 © OpenStreetMap contributors，ODbL 1.0；非测绘、非内部实测。']],
 'decisions':[
  ['plan','公开地图轮廓对齐主正面；保留开敞内院、侧翼位置和高差。','bp_osm;bp_aerial_royal','plan; frame.plan_offset_xz','Palace.__init__ / mass','平面中高；各翼高度中低'],
  ['east_front','23 窗列分成 3—7—3—7—3；柱、山花、檐口、阳台分层，玻璃内退。','listing;bp_aerial;bp_balcony','front','Palace.east_front','中高；纹饰近似'],
  ['west_front','较暖石色；大窗、小上窗、成对柱、弧形中央凸部与绿色半穹顶。','bp_west;bp_west_2019','case source: west_front','Palace.west_front','中；位置与装饰还需精修'],
  ['court','内院独立柱廊，入口玻璃雨篷有黑色骨架、下表面与支撑。','bp_access p10;bp_aerial','case source: courtyard_portico','Palace.courtyard_portico','中；尺寸为照片估计'],
  ['rooms','窗洞贯穿外墙后接有深度的小开间；家具与占灯基于稳定 ID。','bp_access p18;HAF interior rules','seed','Facade.window; hafusion.interiors / lighting','仅伪内饰；真实房间还原未实施'],
  ['night','固定檐口灯与随机窗灯分别控制；前庭灯和纪念碑灯独立。','bp_night','seed; case fixture constants','Palace.east_front / gates_and_memorial','中低；灯具点位估算'],
  ['site','红色前庭、金属围栏、浅色石墩、简化纪念碑与花园边缘。','bp_aerial_royal;bp_aerial','site','Palace.site / gates_and_memorial / landscape','中低；喷泉用静态玻璃代理']
 ],
 'limits':['地图高度不等于测绘高度；主正面按 108 米宽校准，屋顶、各翼和局部雕饰为估计。','窗后家具是可重复的伪内饰；不宣称还原真实房间布局或全部房间。','维多利亚纪念碑雕塑、喷泉和种植被简化；不是完整景观还原。','静态英国旗只是模型标识，不表示当日王室是否在宫内。'],
 'changes':['r01 → r02：修复厚墙后没有连通开间的问题；可检查玻璃、墙厚、房间空隙的前后关系。','r01 → r02：花园立面改用独立大窗、小窗、柱列和半穹顶构图；补上高低屋面之间的外露窗墙。','r01 → r02：主正面相机移入前庭，防止纪念碑挡住中央阳台。'],
 'next':['先检验庭院与侧翼屋面高度，避免地图库标签导致体块偏厚。','继续细化后立面窗位、柱式和雕饰；不要用增加随机细节代替照片比对。','游戏内检查入口、门窗、栏杆连接、伪内饰通行及窗灯亮度。']}}

def main():
 for key,d in DATA.items():
    c=ROOT/'cases'/key;r=c/'research';run=c/'runs/V1_r02'
    dump(r/'component_evidence.json',{'method':'图片与文字人工核对 + HAF 案例构件生成；非自动重建、非模型训练','scale_blocks_per_metre':2,'model_source':None,'image_limit':None,'coordinate_frame':'局部坐标；白金汉宫主面朝 -Z，真实东北向；X 对应东南，Z 对应西南','sources':d['sources'],'decisions':[dict(zip(['component_id','decision','source_ids','parameters','consumer','confidence'],row)) for row in d['decisions']],'limitations':d['limits']})
    dump(r/'reference_box.json',{'status':'已建立多视角证据索引；未恢复相机、未拼接成标定三维参考盒','views':['整体现状','正面/钟面','斜视','花园面/屋顶','内部构件','夜景','地图/平面'],'relation':'按构件手工对应；方向不明的照片不强行标为东南西北','model_alignment':'no external model used','scale_anchor':d['sources'][0]})
    src=json.loads((r/'image_sources.json').read_text())
    for row in src:
      row['included_in_delivery']='URL、哈希与观察；不附原站照片副本'
      if row['id']=='bp_reservicing':row.update(selected=False,review_status='downloaded only; not relied on for geometry')
      if row['id']=='bp_access':row.update(viewed_pages=[10,18],review_status='partial PDF visual review only')
      if row['id']=='bp_osm':row.update(license='ODbL 1.0',review_status='parsed polygons and inspected derived footprint plot')
      if row['id']=='bb_clock':row['observed_subject']='屋顶盾徽和饰带特写；文件名不代表钟盘照片'
    dump(r/'image_sources.json',src)
    manifest=json.loads((run/'manifest.json').read_text())
    component_ids=[row[0] for row in d['decisions']]
    dump(c/'feedback_template.json',{'case':key,'baseline_run':'V1_r02','baseline_nbt_sha256':manifest['sha256'],'status':'awaiting user review','component_ids':component_ids,'items':[],'item_schema':{'component_id':'choose one ID','view_id':'overview/front/detail/night/top/section','problem':'具体哪里不像','evidence_url':'可选参考来源','requested_change':'保留/增厚/变薄/调整比例/重排窗列等','priority':'high/medium/low'}})
    shutil.copy2(ROOT/'hafusion/classical.py',run/'classical_snapshot.py')
    text=f'''# {d['name']} / HAF 0.2 / V1

{d['scope']}

交付基线 `V1_r02`。`V1_r01` 保留首轮结果；`V1_replay` 用于重跑核对。全景、近景、夜景、俯视、剖切都从导出的 NBT 回读，属于离线方块预览，不是游戏截图。

## 复现

从工程根目录执行：

```bash
python3 tools/agent.py --case {key} --run MY_NEW_RUN
python3 tools/render_building_case.py --case {key} --run MY_NEW_RUN
python3 tools/package_building_case.py --case {key} --run MY_NEW_RUN
```

Python 3.12、NumPy、Pillow；渲染另需 Linux Mesa / libEGL。状态连接和 NBT 工具保留于 `support/`。`params.json` 是尺度、位置、种子的入口，构件细部在 `src/build_case.py`；不是每一个硬编码常量都已参数化。

## 依据和边界

'''+''.join('- '+s[2]+' '+s[1]+'\n' for s in d['sources'])+'\n'+''.join('- '+t+'\n' for t in d['limits'])+'''
## 反馈修改

先在 HTML 中选构件记录反馈并导出 JSON，或编辑 `feedback_template.json`。每次修改使用新的 run 名，记录所用照片、参数、保留项和修改项，再用同一相机比较。反馈不会自动执行改造或训练模型。历史 run 不覆盖。

## 本轮修正

'''+''.join('- '+x+'\n' for x in d['changes'])+'\n## 下一轮验收\n\n'+''.join('- '+x+'\n' for x in d['next'])+'''
## 数据与版权

图片来源、文件哈希和观察保存在 research/；原站照片与 PDF 不随源码包分发。地图及转换后的平面属于 OpenStreetMap 数据衍生，保留 ODbL 1.0 说明。代码规则是案例解释，不是任意西方建筑的自动识别器。
'''
    (c/'README.md').write_text(text)
    sz=manifest['size_xyz'];p=run/'import_pack'
    if p.exists():
      imp=json.loads((p/'import_manifest.json').read_text())
      guide=f'''{d['name']} / HAF 0.2 / V1_r02

首选文件：{d['stem']}.schem（Sponge v3，DataVersion 3955，Java 1.21.1 格式目标）。
另有完整稀疏 NBT 和 {imp['module_count']} 个每个不超过 256 KiB 的 NBT 模块。
包围盒 X×Y×Z：{sz[0]} × {sz[1]} × {sz[2]}。
比例 2 格/米。地坪相对工程原点 Y=3，建筑地上起点 Y=4。
对默认 -64..319 的世界高度，整个包围盒原点 Y 要在 -64..{320-sz[1]}；这是静态高度核算，不是游戏导入验收。

在空白测试区域使用支持 Sponge v3 的 WorldEdit/兼容工具。
将 schem 放入你的工具配置的 schematics 目录，然后：
  //schem load {d['stem']}.schem
  //paste -n
先查看选择框位置，再决定 //paste；需要跳过空气时使用 //paste -a。
本文件以局部包围盒最小角为参考点。不同工具对原点的处理应先在测试区核验。
在已有建筑上使用 -a 不会清除原有方块，窗洞与内院可能被旧方块填住。
使用默认 //paste 会包含空气、覆盖包围盒内的既有内容。

完整 NBT 与模块 NBT 都省略空气，不会替你清空原场地。
模块放置：工程原点 + module_offsets.csv 的 offset_xyz，禁止各自居中。
256 KiB 仅是本项目分包约束，不代表满足原版结构方块的尺寸限制；NBT 需兼容导入工具。
没有实体、箱子物品、红石时钟或动态喷泉。

materials.csv 按物品 ID 合并数量；blockstates.csv 保留半砖/楼梯/玻璃片/墙等状态。
原版没有彩色光传播；荧石与海晶灯体现材质差异，预览的光晕不等于游戏实际照明。

已完成：NBT 回读、schem 回读、模块按坐标拼回的全量方块与状态一致性。
尚未完成：Minecraft 导入、碰撞/行走、真实夜间亮度、服务器性能与游戏内视觉验收。

WorldEdit 官方说明：https://worldedit.enginehub.org/en/latest/usage/clipboard/
Sponge v3：https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-3.md

范围：{d['scope']}
'''
      (p/'IMPORT_README.txt').write_text(guide)
      shutil.copy2(c/'feedback_template.json',p/'feedback_template.json')
    # Unit-test logs are recorded by the test runner, not synthesized here.
 (ROOT/'learning/london_western_v1.json').write_text(json.dumps({'status':'two case studies, not a trained model','preserved_core':['HAF lighting and interiors','state mesh and NBT core','Namsan EGL renderer','all previous cases'],'added':['authored classical facade helper','two building adapters','case export/render/package tools'],'observed_failure_modes':['Uniform rows lose hierarchy','Large walls hide window-back rooms','Roof silhouette needs fixed-view review','Map footprints do not verify elevations'],'case_decisions':DATA},ensure_ascii=False,indent=2))
 print('research decisions, README, feedback and import guides updated')

if __name__=='__main__':main()
