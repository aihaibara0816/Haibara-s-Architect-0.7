"""Lightweight offline HTML, original geometry only. No CDN, canvas or WebGL."""
from pathlib import Path
import sys,json,base64,io,html,hashlib,collections
from PIL import Image,ImageDraw,ImageFont
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];RUN=sys.argv[1];OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
R=C/'runs'/RUN;P=C/'review/previews'/RUN;D=C/'review/diagrams'/RUN
spec=json.loads((R/'params_used.json').read_text());sp=spec['spatial_spec'];vf=json.loads((R/'verification.json').read_text());wc=json.loads((R/'world_check.json').read_text());mf=json.loads((R/'manifest.json').read_text())
def asset(path,width=1500):
 im=Image.open(path).convert('RGB');im.thumbnail((width,1800));buf=io.BytesIO();im.save(buf,'JPEG',quality=86,optimize=True);return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
def fig(path,title,text='',width=1500):return '<figure><img loading="lazy" src="'+asset(path,width)+'" alt="'+html.escape(title)+'"><figcaption><strong>'+html.escape(title)+'</strong>'+(' · '+html.escape(text) if text else '')+'</figcaption></figure>'
def section(num,title,content):return f'<section id="s{num}"><div class="kicker">{num:02d} / CASE STUDY</div><h2>{title}</h2>{content}</section>'
def table(headers,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(str(x))+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'

colors={'home':'#c7a57d','grocer':'#98718d','cafe':'#7785a0','clinic':'#afc3a7','community':'#bea468','koban':'#b89483'}
svg=['<svg viewBox="-3 -7 166 145" role="img" aria-label="老街12栋功能布局"><rect width="160" height="128" fill="#e8e9d9"/>']
for r in sp['roads']:
 pts=' '.join(f'{x},{z}' for x,z in r['path']);svg.append(f'<polyline points="{pts}" fill="none" stroke="#77817f" stroke-width="{r["width"]}"/>')
for h in sp['buildings']:
 svg.append(f'<g><title>{h["id"]} {h["name"]}</title><rect x="{h["x"]}" y="{h["z"]}" width="{h["w"]}" height="{h["d"]}" fill="{colors[h["use"]]}" stroke="#fff" stroke-width=".8"/><text x="{h["x"]+h["w"]/2}" y="{h["z"]+h["d"]/2+1}" text-anchor="middle" font-size="3.5" fill="#30251f">{h["id"]}</text></g>')
svg.append('<rect x="3" y="57" width="11" height="5" fill="#846b4b"/><text x="3" y="55" font-size="3.5">BUS</text><text x="4" y="5" font-size="4">N ↑</text><text x="1" y="137" font-size="3.5">160 × 128 blocks · 东 +X / 北 -Z</text></svg>');plan=''.join(svg)
hero='<header><div class="eyebrow">HAF · FREEDOM-INSPIRED OLD STREET</div><h1>日和旧街<span>十二栋，老式日式街道。</span></h1><p>这次从木构、灰瓦和连续街面重新做起。保留马路、公交站与公共建筑，把宽前院的独栋住宅改成贴近街道的町屋与店铺。</p><div class="badges"><b>原创 Minecraft 街区</b><b>Java 1.21.1</b><b>'+RUN+'</b><b>2026.10.29</b></div>'+fig(P/'walk.png','从西端走进老街','最终方块的透视预览；未裁掉两侧建筑，非游戏截图')+'</header>'
contents=[]
oldP=C/'review/previews/J05'
contents.append(section(1,'从现代住宅区，改成老街','<div class="two">'+fig(oldP/'overview.png','上一版 J05','用户反馈：太现代；房子分散，前院与绿地较多')+fig(P/'overview.png','本版 '+RUN,'12栋用途配额保留；地块靠街，统一灰瓦，以木构为主')+'</div>'+table(['观察点','J05','本版'],[
 ('街道组织','176 × 160；独栋散落、前场宽','160 × 128；沿主街布置，后侧留庭院'),
 ('建筑语言','白墙、蓝窗、阳台，部分平屋顶','木柱梁、淡色格子窗、双层深檐，全数瓦坡屋顶'),
 ('商业与公共建筑','杂货、面包咖啡、现代诊所','和菓子铺、茶屋、木造老诊所与会所'),
 ('路面与设施','较宽道路、连续标线、停车与车辆','7格主街、5格支巷、一处小横道、木瓦候车亭'),
 ('灯光','顶内嵌灯、门灯','室内悬灯、檐下灯与木灯柱；实际承托与链条'),
 ])+'<p class="note">灵感来自已经采样的 Freedom 日式作品。这里是原创街区，未声称复刻某一教程或读取作者世界存档。现有预览为无纹理的方块近似渲染。</p>'))
contents.append(section(2,'布局：街面收紧，庭院留到后方','<div class="two"><div class="map">'+plan+'</div><div><h3>商业与日常用途共存</h3><p>7栋住宅、2栋商业和3栋公共建筑沿主街排布，公交站设在西端入口。地块宽度、屋脊朝向与一层/两层体量有差别；H04和H07有低侧翼，H05上层后退。</p><h3>空地有具体用途</h3><p>后侧布置围合小院、碎石小径、菜地和树群，会所后方有井台与公告栏；东侧保留排水渠。大树集中在后部与街区边缘，店前用小盆栽。</p><h3>马路仍然保留</h3><p>这版是有沥青路的旧街，石板步行街作为后续分支。传统建筑并不要求把道路全部变成石板。</p></div></div>'))
contents.append(section(3,'十二栋清单',table(['编号','用途 / 名称','层数','占地（格）','地坪 Y'],[(h['id'],h['name'],h['floors'],f'{h["w"]} × {h["d"]}',h['g']) for h in sp['buildings']])+'<p>共 <b>'+str(len(sp['rooms']))+' 个使用楼层</b>，均设灯具。住宅的家具、厨房与睡眠区为初步陈设；卫浴、私密隔间和可交互家具尚未细化。公交亭、井台不计入12栋。</p>'))
contents.append(section(4,'店铺、木格与夜间街景',fig(P/'walk_night.png','相同走街机位 · 夜景','灰瓦深檐与暖光；真实游戏光照仍需验证')+'<div class="two">'+fig(P/'shops.png','紫帘和菓子铺','同一NBT局部范围裁切，突出不对称售卖面和暖帘')+fig(P/'tea_house.png','松影茶屋','同一NBT局部范围裁切，保留木格、低座与蓝帘')+'</div><div class="two">'+fig(P/'upper_homes.png','北侧町屋街面','按建筑组裁切范围，避免前排遮挡')+fig(P/'civic.png','老诊所与木造交番','公共用途不再采用现代平屋顶')+'</div>'+fig(P/'south_homes.png','南侧高低体量','会所、低侧翼与平屋；局部范围裁切')+'<p class="note">局部图的显示裁切已标注，完整总览与走街视角保留整镇。瓦片、木纹、布帘摆动及彩色光在离线预览中简化，不等于资源包或光影包截图。</p>'))
contents.append(section(5,'随机性、布局与分布，分别做到哪一步',table(['层级','本版实际实现','仍未实现'],[
 ('布局','固定主街、支巷、地块位置和功能配额','没有任意 seed 自动重新排镇'),
 ('体量与分布','手工安排宽窄、单层/两层、侧翼、后退与屋脊方向','没有自动搜索最优街道密度'),
 ('材料','每栋稳定 ID 决定木材色调；灰瓦为共享约束','没有逐方块噪声旧化'),
 ('植物与院落','独立随机通道控制树冠边缘、边缘树位置与作物长势','没有植被生态仿真'),
 ('灯光','全部使用楼层设灯；按檐口、室内、候车与巷道设置','没有以随机熄灯模拟无人住宅'),
 ])+'<p>种子 <code>2026102912</code>；本版同种子复跑 NBT 字节完全一致。更换某一栋的细节通道，原则上不应连带重排其它栋的结构。当前仍有相似窗组和屋顶比例，下一步应优先扩充建筑家族，再引入地块随机。</p>'))
contents.append(section(6,'同源图纸与内部样板','<p>这些图读取最终 NBT。整镇有两张楼层切层图；H01另外提供剖面、爆炸图与四向立面。这里只将H01作为详细图纸样板，不把它当成12栋完整施工图。</p><div class="two">'+fig(D/'floor_1.png','12栋首层切层图','橙线为入户路线')+fig(D/'floor_2.png','各栋二层切层图','四栋单层建筑在此图留空')+'</div><div class="two">'+fig(P/'H01_cut.png','H01 首层剖切','楼梯与生活空间')+fig(P/'H01_upper.png','H01 二层剖切','上层初步陈设')+'</div><div class="two">'+fig(D/'section.png','H01 楼梯剖面','X=14，读取真实方块位置')+fig(C/'review/previews'/f'{RUN}_exploded'/'exploded.png','H01 分层爆炸','仅增加展示竖向间距；水平坐标不变')+'</div><details><summary>H01 四向等尺度立面</summary><div class="two">'+''.join(fig(D/f'elevation_{f}.png','H01 · '+lab) for f,lab in [('south','南'),('east','东'),('north','北'),('west','西')])+'</div></details>'))
contents.append(section(7,'整镇四向与真俯视','<div class="two">'+''.join(fig(P/f'{f}_day.png',lab+' · 日景') for f,lab in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')])+'</div><details><summary>相同尺度的四向夜景</summary><div class="two">'+''.join(fig(P/f'{f}_night.png',lab+' · 夜景') for f,lab in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')])+'</div></details>'+fig(P/'top_day.png','垂直正交俯视','北为 -Z，四个斜视相机共用尺度与俯角')))
contents.append(section(8,'检查结果',table(['检查','状态','范围'],[
 ('NBT文件独立回读','通过',f'{mf["non_air_blocks"]:,} 非空气方块；位置与状态一致'),
 ('楼栋与用途配额','通过','12栋，7住宅+2商业+3公共'),
 ('几何检查','通过',str(len(vf['checks']))+'项；入口、楼梯、道路、灯具支撑、植物、水体等'),
 ('世界存档回读','通过',f'{wc["checked_cells"]:,} 格位，差异 {wc["mismatches"]}'),
 ('布帘方块实体','已写入','纯色旗帜包含原版 banner 方块实体；游戏显示待验'),
 ('相同种子复跑','通过','主NBT字节哈希一致'),
 ('人工预览检查','已检查','走街、店面、四向、夜间与技术图；简化材质'),
 ('游戏客户端 / 用户风格验收','待验收','未执行Minecraft客户端测试'),
 ])+'<p>J06建立老街体量；J07修正瓦坡转角；J08移开占到车道的灯柱；J09补齐悬灯与檐口之间的链条。旧输出保留，问题不从历史中抹除。</p><details><summary>主NBT哈希与检查详情</summary><code class="hash">'+mf['sha256']+'</code><pre>'+html.escape(json.dumps(vf,ensure_ascii=False,indent=2))+'</pre></details>'))
contents.append(section(9,'历代变化、工作流程与已有 Skill',table(['阶段','内容 / 状态'],[
 ('JapanTown01','Freedom系列目录65条；实际仅采样其中少数视频，目录不代表已学完'),
 ('J01–J02','建立12栋道路小镇，并修入口与路线冲突'),
 ('J03–J05','增加庭院、阳台与窗组，修路径高差；用户反馈仍太现代，记为风格待修正'),
 ('J06–J09 · 当前','按老式木构街道重排体量，灰瓦双檐、木格、暖帘、传统公共建筑；检查与导出'),
 ])+'<p><b>现行流程：</b>恢复最新文件与反馈 → 参考分解 → 用途与空间设定 → 固定地块和楼栋ID → 写入方块与细节随机 → NBT独立回读 → 日夜及技术图复核 → 世界导出 → 用户风格与游戏验收。</p><p><b>沿用的Skill：</b>gafacraft-ha-research 负责证据与不确定性；gafacraft-concept-design 负责原创空间及图纸；gafacraft-architect 负责案例建造、回读与交付。gafacraft-building-reference继续用于外部建筑AI资料包。本次未新增个人Skill，未训练模型权重。</p><p>HAF 0.4是当前工程主线，HAF05是研究整合编号，J09是这一个案例的运行编号。旧现代版与新老街版均作为风格对照案例保留。</p>'))
contents.append(section(10,'使用方式与下一步','<ol><li>解压 <b>JapanTown12_World_1.21.1.zip</b>，将世界文件夹放入Minecraft的 <code>saves</code>。</li><li>用Java 1.21.1打开，默认创造模式。出生点 <code>-74 65 4</code> 在老街西端。</li><li>白天 <code>/time set day</code>；夜景 <code>/time set night</code>。首次加载让游戏重算光照。</li></ol><p class="note">原版方块，无需模组。随机刻、天气与昼夜循环默认关闭以稳定样板，可在游戏中重新开启。家具为装饰，门、楼梯、布帘与实际亮度仍需实机走查。</p><ol><li><b>先确认街道气质：</b>重点比较檐口高度、街宽和木格密度；再按反馈调整屋顶与立面比例。</li><li><b>扩充町屋家族：</b>加窄面深进的町屋、旅馆门厅、转角茶店、低平屋和后部小院，减少相似窗组。</li><li><b>做三组受约束布局：</b>固定12栋用途配额，比较地块宽度、退距和建筑分布；检查入口连通、檐口碰撞、视线和公共点距离。</li><li><b>再开石板路分支：</b>保留这版马路旧街，另做8栋左右步行老街，研究巷道与庭院的层次。</li></ol>'))
short='Freedom日式作品启发的原创老街，12栋，木构町屋，灰瓦双檐，木格窗，暖帘，和菓子铺、茶屋、老诊所、会所、木造交番；窄沥青路与木瓦公交亭，暖灯，后院树群。'
long=short+' 160×128格场地，7住宅+2商业+3公共；主街7格，支巷5格。固定地块与功能配额，通过楼层、宽深、上层后退、低侧翼和屋脊方向建立体量差异。材料、树冠与作物随机按稳定ID分通道；全体使用楼层保留照明，保护入口、楼梯、车道和悬灯支撑。不是教程精确复刻，不用噪声替代建筑逻辑。'
contents.append('<section><h2>参考与设计数据</h2><p>本次重看Freedom店铺#104的外观画面，参考木柱梁、两道灰瓦檐、格子窗与不对称售卖口；旅馆#101和庭院宅#39沿用上一轮已记录的局部观察。未宣称完整学习65集，百度存档仍未读取。</p><ul><li><a href="https://www.youtube.com/watch?v=I40jEm-xIsU">Freedom · #104 原始视频</a></li><li><a href="https://www.youtube.com/watch?v=QRdePpYnhBw">Freedom · #101 旅馆</a></li><li><a href="https://www.youtube.com/watch?v=kBoXoy8_i4I">Freedom · #39 庭院宅</a></li><li><a href="https://chatgpt.com/library?file_id=libfile_663d4d014de08191a97fdef972408368&account_id=personal">JapanTown01 风格研究</a></li><li><a href="https://chatgpt.com/library?file_id=libfile_a02e02ce0d4881918ecd59ccedcb81fa&account_id=personal">HAF05 研究总档</a></li></ul><button id="saveSpec">下载本版空间参数JSON</button><details><summary>长短设计关键词</summary><p>'+short+'</p><p>'+long+'</p></details></section>')
css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f1e9;color:#352e29;font:16px/1.8 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}main{max-width:1160px;margin:auto;padding:38px 24px 80px}header{padding-top:15px}.eyebrow,.kicker{color:#a17654;font-size:12px;font-weight:700;letter-spacing:.15em}h1{font-size:clamp(38px,6vw,76px);font-weight:650;line-height:1.13;letter-spacing:-.04em;margin:20px 0}h1 span{display:block;font-size:.48em;letter-spacing:.02em;margin-top:15px;color:#91694d}header>p{max-width:730px;color:#65736c;font-size:18px}h2{font-size:30px;line-height:1.3;margin:12px 0 24px}h3{font-size:19px;margin:18px 0 8px}p{margin:12px 0 18px}section{padding:45px 0;border-top:1px solid #d8ded2}nav{display:flex;gap:18px;overflow:auto;white-space:nowrap;margin:25px 0 40px;padding:10px 0;border-block:1px solid #d8ded2}a{color:#8c593f;text-underline-offset:4px}.badges{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.badges b{font-size:12px;border:1px solid #bcc8ba;border-radius:20px;padding:4px 13px;font-weight:500}figure{margin:22px 0 30px;background:#e4e8de;border-radius:12px;overflow:hidden;border:1px solid #dbe1d6}img{width:100%;height:auto;display:block}figcaption{padding:12px 16px;font-size:13px;color:#637166;background:#faf9f5}strong{color:#684e3c}.two{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}.two figure{margin-top:12px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding:22px 0}.stats b{display:block;font-size:32px;font-weight:600}.stats span{font-size:13px;color:#6b7b71}.note{font-size:14px;color:#68796f;border-left:3px solid #bdc9b8;padding:5px 16px;background:#eaf0e7}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:540px;font-size:14px}th,td{padding:13px 14px;text-align:left;border-bottom:1px solid #dae0d4}th{background:#e4eadf}tr:nth-child(even){background:#f8f7f2}details{margin:22px 0;background:#ecf0e7;padding:15px;border-radius:9px}summary{cursor:pointer;font-weight:600}pre{overflow:auto;font-size:12px;max-height:420px;background:#e1e9dd;padding:18px}code{font-size:.88em;background:#e5eadf;padding:2px 6px;border-radius:3px}.hash{display:block;word-break:break-all;margin-top:20px}.map{background:#fffef8;padding:15px;border-radius:14px}.map svg{display:block;width:100%}button{border:0;border-radius:8px;background:#7a4b36;color:#fff;padding:13px 20px;font:inherit;cursor:pointer}footer{font-size:12px;color:#6d7e71;margin-top:35px}li{margin:9px 0}@media(max-width:650px){main{padding:22px 15px 50px}.two{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}h2{font-size:25px}section{padding:32px 0}figure{border-radius:8px}.stats b{font-size:28px}header>p{font-size:16px}}'''

nav='<nav>'+''.join(f'<a href="#s{i}">{t}</a>' for i,t in [(1,'新旧对照'),(2,'布局'),(4,'街景'),(5,'随机性'),(6,'图纸'),(8,'检查'),(9,'历代与流程'),(10,'下一步')])+'</nav>'
doc='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>日和旧街 · 12栋老式日式街道 '+RUN+'</title><style>'+css+'</style></head><body><main>'+hero+nav+''.join(contents)+'<footer>JapanTown12 · '+RUN+' · 原创研究案例 / 离线轻量HTML · 非游戏截图</footer></main><script id="case-data" type="application/json">'+json.dumps(spec,ensure_ascii=False).replace('</',r'<\/')+'</script><script>document.getElementById("saveSpec").onclick=()=>{const b=new Blob([document.getElementById("case-data").textContent],{type:"application/json"});const u=URL.createObjectURL(b);const a=document.createElement("a");a.href=u;a.download="JapanTown12_Design.json";a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};</script></body></html>'
(OUT/'JapanTown12.html').write_text(doc,encoding='utf-8')
# Phone-friendly sheet: actual street camera, then the matched night camera.
font=ImageFont.truetype(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),32)
im1=Image.open(P/'walk.png').convert('RGB');im1.thumbnail((1200,900));im2=Image.open(P/'walk_night.png').convert('RGB');im2.thumbnail((1200,900));sheet=Image.new('RGB',(1240,im1.height+im2.height+180),'#f4f1e9');draw=ImageDraw.Draw(sheet);draw.text((30,22),'日和旧街 · 木构 / 灰瓦 / 暖帘 · '+RUN,font=font,fill='#684e3c');sheet.paste(im1,(20,80));sheet.paste(im2,(20,im1.height+110));small=ImageFont.truetype(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),20);draw.text((30,sheet.height-42),'实际方块离线预览 · 非游戏截图 · Java 1.21.1',font=small,fill='#91694d');sheet.save(OUT/'JapanTown12_Preview.jpg',quality=91,optimize=True)
(R/'design_prompts.json').write_text(json.dumps(dict(short=short,long=long),ensure_ascii=False,indent=2))
print('HTML bytes', (OUT/'JapanTown12.html').stat().st_size)
