"""Self-contained reviewed report and source package. No game-run claim."""
from pathlib import Path
import sys,json,base64,io,html,hashlib,zipfile,shutil
from PIL import Image,ImageOps
P=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=P/'runs'/RUN;V=P/'review/previews'/(RUN+'_RailDepot01');D=P/'deliverables'
sp=json.loads((R/'spec.json').read_text());check=json.loads((R/'check.json').read_text());audit=json.loads((R/'rail_audit.json').read_text());world=json.loads((R/'world_check.json').read_text());sch=json.loads((R/'schem_check.json').read_text());net=json.loads((R/'rail_network.json').read_text());views=json.loads((R/'cameras.json').read_text());IMAGES={}
surface=json.loads((R/'surface_revision.json').read_text())
for v in views:
 p=V/(v['id']+'.png');im=Image.open(p);assert im.info.get('source_nbt_sha256',sp['source_nbt_sha256'])==sp['source_nbt_sha256'];b=io.BytesIO();im.save(b,format='WEBP',quality=89,method=6);IMAGES[v['id']]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
for n in ['day_NW','top']:
 im=Image.open(P/'assets/baseline_R05'/(n+'.png'));b=io.BytesIO();im.save(b,format='WEBP',quality=89,method=6);IMAGES['baseline_'+n]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
for n in ['source_cross_section','maintenance_section','consist']:IMAGES[n]='data:image/svg+xml;base64,'+base64.b64encode((P/'research'/(n+'.svg')).read_bytes()).decode()
payload=json.loads((R/'interactive_payload.json').read_text());assert payload['source_nbt_sha256']==sp['source_nbt_sha256']
opts=''.join('<option value="'+b['id']+'">'+html.escape(b['name'])+'</option>' for b in payload['buildings'])
model=(P/'assets/industrial_shell.html').read_text().replace('@@OPTIONS@@',opts).replace('@@DATA@@',json.dumps(payload,ensure_ascii=False,separators=(',',':'))).replace('@@JS@@',(P/'assets/industrial_viewer.js').read_text())
(D/'RailDepot01_Model.html').write_text(model);vb64=base64.b64encode(model.encode()).decode()
style=(P/'assets/report_style.css').read_text()+'''\n.gallery img{object-fit:contain}.mainimage{object-fit:contain}.tag{margin:4px}.diagram{margin:22px 0}.diagram img{width:100%}.small{line-height:1.8}code{overflow-wrap:anywhere}.source-list li{margin:13px 0}.pills{display:flex;flex-wrap:wrap;gap:8px}.pills span{padding:8px 12px;background:#e6eee9;border-radius:5px}.downloadgrid{gap:20px}.gallery figcaption{line-height:1.6}table{width:100%}details{margin:18px 0;padding:18px;background:#edf2ef}summary{cursor:pointer}button{cursor:pointer}.run-pending{border-left:4px solid #bc9047;background:#f5f0e5;padding:18px;line-height:1.8}@media(max-width:650px){.gallery,.twocol{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.hero h1{font-size:42px}}'''
labels={'day_NW':'日景 · 咽喉与检修库','day_SW':'日景 · 员工入口与综合楼','day_NE':'日景 · 库区与配套','day_SE':'日景 · 研发生活区','top':'完整基地 · 俯视','night_NW':'夜景 · 轨道与检修库','night_SW':'夜景 · 员工入口','night_NE':'夜景 · 库区','night_SE':'夜景 · 综合楼一侧'}
def fig(n,s):return '<figure><img loading="lazy" data-img="'+n+'" alt="'+s+'"><figcaption>'+s+'</figcaption></figure>'
def section(title,sub,body):return '<section><div class="sectionhead"><h2>'+title+'</h2><p>'+sub+'</p></div>'+body+'</section>'
tabs=''.join('<button class="viewtab'+(' active' if n=='day_NW' else '')+'" data-view="'+n+'">'+s+'</button>' for n,s in labels.items())
body='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新港列车所 · 检修与研发基地</title><style>@@STYLE@@</style></head><body><header><nav><b>GAFAcraft / RAIL DEPOT 01</b><a href="#model">旋转查看 ↗</a></nav><div class="hero"><div><div class="eyebrow">MAINTENANCE · STABLING · RESEARCH</div><h1>新港列车所<br>检修与研发基地</h1><span class="tag">Create 6.0.10</span><span class="tag">Minecraft 1.21.1</span><span class="tag">原创复合设施</span></div><p class="intro">从附件里的两端驾驶编组与车站出线关系出发，把缓弯咽喉、长检修工位、车顶平台和车底坑组织成一座新建列车所。十五层综合楼与低层库房形成高低对比，调度、能源、食堂和宿舍一并建入。</p></div></header><main><div class="frame"><img class="mainimage" id="heroImage" data-img="day_NW" alt="新港列车所整体"></div><div class="strip">@@TABS@@</div><p class="caption" id="viewcaption">日景 · 咽喉与检修库</p><p class="caption">本页所有建筑视图来自最终 NBT 方块几何；材质、模组外形和灯光为离线近似，不是游戏截图。</p><div class="stats"><div class="stat"><strong>120 格</strong><span>连续有效检修区</span></div><div class="stat"><strong>52.7–56.7 格</strong><span>七段实际曲线长度</span></div><div class="stat"><strong>八条库线</strong><span>停放、双线检修、重修、洗车</span></div><div class="stat"><strong>十五层</strong><span>独立研发综合楼</span></div></div>
<section id="model"><div class="sectionhead"><h2>在完整模型里看比例</h2><p>拖动旋转、缩放，选择设施查看；切换昼夜或水平切片。模型包含真实 Create 轨道连接所对应的曲线几何。</p></div><div class="modelbox"><div class="modelcover" id="modelcover"><div><button class="primary" id="loadModel">打开可旋转模型</button><p class="small">模型内嵌于本页，可下载后离线查看。需支持 WebGL2。</p></div></div><iframe id="modelFrame" title="列车所旋转模型" hidden allow="fullscreen"></iframe></div></section>'''
body+=section('逐级收束，硬质地面为主','这版按你的反馈同时收紧咽喉，并减少工业用地的大面积绿色。','<div class="gallery">'+fig('baseline_day_NW','调整前：咽喉展开较早，空地大部分为草地。')+fig('day_NW','本版：上下两组连续向内并线，道床连成原石地面，前区采用硬质铺装。')+'</div><p>库线的检修间距继续满足平台和车辆需要；变化集中在汇入段，最外侧线路推迟展开，连续三次并线形成阶梯式收束。为保留末端平顺段，库房前端适当后退，120 格有效检修区完整保留。</p><p>铁路作业区以圆石、石头和少量安山岩连成完整地面；调度、研发和宿舍前场改成灰色硬质铺装。绿色集中在外围窄带、入口小树池和员工休息角。</p>')
body+=section('先核对你们的编组','三份附件都已逐个读取。first_floor 中有一列三节车；canton_east 文件中有两组同样的三节编组。',fig('consist','按车厢实体内的方块与驾驶控制器计数：两端各一套控制器，中间无控制器。图中长度是方块包络，不是铁路工程车辆长度。')+'''<table><thead><tr><th>测量项</th><th>附件结果</th><th>本次采用</th></tr></thead><tbody><tr><td>编组</td><td>23 + 22 + 23 ≈ 68 格，2 端车 + 1 中车</td><td>同时留出约 90 格编组的空间</td></tr><tr><td>车宽</td><td>5 格占用包络；Copycats 细部可能薄于整格</td><td>直线库门 7 格宽，库内轴距 12 格</td></tr><tr><td>车顶</td><td>主要车体与设备合计至轨道基准约 +6</td><td>高位平台脚面 +5；跨线桥底 +10</td></tr><tr><td>长度区分</td><td>附件汇入段与车辆长度分别读取</td><td>汇入曲线 50–60，连续检修 120；不把两者混为同一长度</td></tr></tbody></table>''')
body+=section('轨道、道床与站台','轨道方块的一格位置只是存储与定位基准，不能据此把轨道画成一格宽。', '<div class="twocol">'+fig('source_cross_section','样本截面：平滑石上承轨，下面为石英块；边侧圆石半砖。它是样本中的结构与表达方式，不认定为现实碎石道床构造。')+'''<div><h3>从样本中量到的关系</h3><p>普通相邻轨道轴距可见 6 格，隔着较宽站台的轴距可见 15 格。15 格是两条线路之间的关系，不是铁轨本身的宽度。</p><p>Create 6.0.10 官方直轨模型的枕木横向包络约 2.744 格，轨面最高约为轨道方块底面 +0.35。样本站台完成面是 +2，与样本车门底部所在高度对应。</p><p>人物按 Minecraft 常规玩家约 1.8 格高作比例参考，通行空间按至少两格检查。不能仅凭站台高度反推所有车辆和玩家尺寸。</p><p class="small">原始文件的列车还包含 Steam ’n’ Rails、Copycats 等额外模组；本基地的必需模组方块只使用 Create。未把缺少外部 TrainId 数据的原车实体直接复制进世界。</p></div></div>''')
body+=section('外侧汇入内侧，形成列车所咽喉','上下两组各自连续三次“2 并 1”：外线先并入邻线，合并后再向内并，最后接回两条进出线。',fig('throat','所有曲线端点数据成对写入。七段曲线实长为 56.72、52.67、52.67、52.67、52.67、52.67、52.67 格；每段端点的 X 向间距为 52 格。')+'''<p>出入口侧留下约 120 格的直线折返空间，让较长编组能够整体离开咽喉后换向。八条库线自外向内分为四线停放、两线检修、一线重修与一线洗车；末端均有车挡。整座基地占地 480 × 240 格，长直线可以分段铺设，不要求一次拉满。</p><p class="small">你提供的 256 格作为服务器能力记录。这版无需用到该上限，也没有替你改写服务器配置；官方基础 Create 6.0.10 的相关配置上限与服务器扩展值可能不同。</p>'''+fig('top','整体俯视：上部铁路与库区，下部调度、研发和员工配套。'))
body+=section('检修平台与坑，围绕车辆来布置','双线检修工作区各 120 格，平台、照明、坑内通道和侧向出口有明确对应。', '<div class="gallery">'+fig('maintenance_cut','移去上部屋盖后：两条带高位平台的检修线，旁边为重修线及起重设备。')+fig('maintenance_inside','库内视角保留屋盖、屋架与照明，观察库门、平台和作业空间。')+'</div><div class="twocol">'+fig('maintenance_section','设计截面：虚线车体只是尺度叠加。坑脚面 −2，高位平台脚面 +5；具体站姿和碰撞仍待实机检查。')+fig('pit_detail','最终方块模型截面：轨道下方保留坑内空间，平台独立承托。此图未放入示意车体。')+'</div><p>检修坑的有效区间为本地 X=312 至 432。两端侧向出口让人员先走出轨道下方再登阶。车站目标点设置在 X=420，距离作业区末端留 12 格，避免把停站标记直接当成车头最前缘。</p><div class="gallery">'+fig('stabling_cut','四线整备库：低位侧平台按车门高度布置。')+fig('wash_detail','洗车门架、独立管线位置和循环水池；设备造型属于静态建筑。')+'</div>')
body+=section('信号与自动列车：已写入什么','信号和车站采用实际 Create 方块，并写入对应轨道目标。自动运行状态留待加载游戏后核验。','''<div class="pills"><span>2216 个轨道定位方块</span><span>7 对曲线连接</span><span>10 个车站</span><span>20 个信号</span><span>1 份示范循环时刻表</span></div><p>咽喉进入方向使用交叉信号，离开方向使用普通区段信号，整个交汇区作为需要保持畅通的区域。信号颜色由游戏中的区段占用决定；离线预览中的黄色壳体仅用于辨认设施。</p><p>调度楼一层木桶中放入 Create 时刻表：<code>RD-LEAD-A → RD-STABLE-02 → RD-LEAD-A → RD-INSPECT-01 → RD-LEAD-A → RD-WASH-01</code>，每站等待 20 秒并循环。折返经引出线完成，使用前需有可双向运行的已装配列车与对应驾驶员。</p><p>木桶世界坐标 <code>-18 65 62</code>。轨道、车站、信号与时刻表已做字段及目标检查；世界存档还写入了轨道更新，供区块加载时建立 Create 轨道网络。</p><div class="run-pending"><b>尚未实机验收：</b>没有运行 Minecraft / NeoForge 客户端或服务端。当前交付没有活动列车实体；轨道图建立、站名迁移、信号方向、时刻表执行、倒车条件和区块加载都需要在独立世界确认。不能把离线连通检查理解为自动调度已经跑通。</div>''')
body+=section('高楼、低库与员工设施','研发综合楼十五层；另有三层技术培训楼、三层调度楼、两层食堂、四层乘务宿舍，以及低层能源和备件库。','<div class="gallery">'+fig('tower_section','综合楼剖面：十五层、连续楼板与楼梯，接待、办公、会议和休息按层配置。')+fig('tower_exploded','分层爆炸仅改变展示间距；实际模型楼层间距 6 格。')+fig('bridge_detail','跨线步桥：桥底高于轨道基准 10 格，人员通过桥跨越股道。')+fig('dispatch_plan','调度楼二层：控制席、显示墙和侧向交通核心。')+'</div><details><summary>查看研发、食堂、宿舍与综合楼平面</summary><div class="gallery">'+''.join(fig(n,s)for n,s in [('research_plan','技术研发楼代表层'),('canteen_F1','食堂一层：厨房、取餐与餐位'),('canteen_F2','食堂二层：餐饮和活动布局'),('dorm_F1','乘务宿舍一层'),('dorm_F2','乘务宿舍标准层'),('tower_F1','综合楼入口层'),('tower_F2','综合楼标准办公层'),('tower_F4','综合楼会议休息层'),('tower_F15','综合楼十五层')])+'</div></details><details><summary>四向等类正投影</summary><div class="gallery">'+''.join(fig('elevation_'+n,lab+'立面；长边与短边分别适配幅宽，尺寸以模型为准。')for n,lab in [('south','南'),('north','北'),('west','西'),('east','东')])+'</div></details>')
body+=section('现实参考与证据边界','现实资料用于确定设施关系；尺寸以你提供的 NBT 与本次 Minecraft 设计为依据。','''<ul class="source-list"><li><a href="https://openjicareport.jica.go.jp/pdf/12111563_03.pdf" target="_blank" rel="noopener">JICA · Hanoi Line 5 / Maintenance Center</a>：参考停放、检修、重修、洗车、材料及供能的分区关系，以及车顶与车底的不同作业位置。资料中的项目规模不直接套用到本模型。</li><li><a href="https://www.karch.com.au/projects/craigieburn-train-maintenance-facility/" target="_blank" rel="noopener">Kyriacou Architects · Craigieburn Train Maintenance Facility</a>：参考检修道路、轮对作业、屋顶通道、仓储及员工配套的组合。</li><li><a href="https://www.cairncross.uk.com/projects/canton-high-level-platforms/" target="_blank" rel="noopener">Cairn Cross · Canton High Level Platforms</a>：参考连续高位维护平台、下方照明与支柱避让。此处 Canton 是英国 Cardiff 的车辆段，不是广州东站。</li><li><a href="https://github.com/Creators-of-Create/Create/tree/mc1.21.1-6.0.10" target="_blank" rel="noopener">Create 官方 6.0.10 源码</a>：核对轨道、Bezier 连接、站台目标、信号与时刻表组件格式。轨道外形基于模型尺寸独立绘制近似网格。</li></ul><p class="small">本次研究不把生成图作为现实证据；来源报告使用了可读取正文，未把未能取得图像像素的页面当作已看过的现场照片。附件原文件保留不变，测量与设计建议在项目的 research/findings.json 中分开记录。</p>''')
nbt64=base64.b64encode((R/'RailDepot01.nbt').read_bytes()).decode();schem64=base64.b64encode((R/'RailDepot01.schem').read_bytes()).decode()
body+=section('下载与打开','需要 Minecraft 1.21.1、Create 6.0.10 和对应 NeoForge 环境；服务器目标记录为 NeoForge 21.1.244。',f'''<div class="downloadgrid"><div class="downloadcard"><h3>世界存档</h3><p>将 <code>RailDepot01_{RUN}_Create6.0.10</code> 文件夹放入 <code>saves</code>。出生点 <code>-50 65 111</code>，创造模式。第一次打开需要计算光照和加载轨道区块。</p><p>世界 ZIP 和完整项目 ZIP 与本页一并交付。原始三份参考 NBT 在项目的 input/source 目录中。</p></div><div class="downloadcard"><h3>直接取出蓝图</h3><p>Create 原生结构 NBT 保留模组连接与方块实体；Sponge v3 保留完整空气包围盒及嵌套数据。</p><a class="primary" download="RailDepot01.nbt" href="data:application/octet-stream;base64,{nbt64}">下载 .nbt</a> <a class="primary" download="RailDepot01.schem" href="data:application/octet-stream;base64,{schem64}">下载 .schem</a><p class="small">两种导入途径都尚未实机验证。先在独立测试区域加载；包含空气的 schem 会替换包围盒内已有方块。</p></div></div>''')
body+=section('本版交付核对','将“数据正确”“几何检查”和“游戏运行”分开报告。',f'''<table><thead><tr><th>范围</th><th>结果</th></tr></thead><tbody><tr><td>结构 NBT</td><td>{check['blocks']:,} 个非空气方块；独立读回与生成场景一致。</td></tr><tr><td>轨道关系</td><td>1 个离线连通网络；7 对曲线互相引用；30 个车站/信号 ID 不重复，目标均存在。</td></tr><tr><td>几何净空</td><td>曲线车体包络、直线检修通道、两条 120 格坑及侧出口、22 段楼梯与主要连廊路线通过对应检查；不等于游戏碰撞认证。</td></tr><tr><td>世界 / schem</td><td>{world['checked_cells']:,} / {sch['checked_cells']:,} 个单元回读差异为 0；261 个方块实体内容保留。</td></tr><tr><td>视图</td><td>32 张同源固定图，加离线旋转模型与三张数据示意图。</td></tr><tr><td>待验项目</td><td>Minecraft 实机、WorldEdit 导入、Create 自动列车；浏览器模型已核对数据与脚本语法，未做浏览器运行验收。</td></tr></tbody></table><details><summary>设计关键词与复现信息</summary><p><b>短关键词：</b>现代大型列车所，两进八出，50–60 格缓弯咽喉，120 格检修段，车顶双侧维护平台，车底检修坑，十五层研发综合楼，低层调度能源及员工设施，Create 实际轨道信号。</p><p><b>长关键词：</b>在 480 × 240 方块的场地内建立新建铁路复合基地；以两端驾驶三节编组为尺度，保留约 90 格编组校核空间。西侧双线进出，外侧线路分三级逐条汇入内侧，七段 Create 曲线控制在 50–60 格。东侧为四线整备库、双线检修库、重修与洗车线，工作区连续 120 格，坑内两格高度、侧向逃出，车顶平台脚面相对轨道 +5 格。员工侧设置十五层研发综合楼、技术培训、三层调度、低层能源备件库、食堂和宿舍；通过前区连廊和跨线步桥联系，白灰围护、蓝色标识、连续天窗与简洁维护状态。</p><p class="small">所有几何视图从最终 NBT 读取；摄像机、截面位置、分层参数在 runs/{RUN}/cameras.json。当前生成器针对本案例，不是通用任意铁路生成系统。</p><p class="small">NBT SHA-256：<code>{sp['source_nbt_sha256']}</code></p></details>''')
body+='''</main><footer>GAFAcraft / HAF · RailDepot01 · @@RUN@@<br>新港列车所 · 检修与研发基地</footer><script>const IMAGES=@@IMAGES@@;const LABELS=@@LABELS@@;const MODEL=@@MODEL@@;let loaded=false;document.getElementById('loadModel').onclick=()=>{if(loaded)return;const f=document.getElementById('modelFrame');f.srcdoc=new TextDecoder().decode(Uint8Array.from(atob(MODEL),c=>c.charCodeAt(0)));f.hidden=false;document.getElementById('modelcover').style.display='none';loaded=true;};document.querySelectorAll('[data-img]').forEach(e=>e.src=IMAGES[e.dataset.img]);document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.getElementById('heroImage').src=IMAGES[b.dataset.view];document.getElementById('viewcaption').textContent=LABELS[b.dataset.view];document.querySelectorAll('[data-view]').forEach(q=>q.classList.toggle('active',q===b));});</script></body></html>'''
for k,v in {'@@STYLE@@':style,'@@TABS@@':tabs,'@@IMAGES@@':json.dumps(IMAGES,separators=(',',':')),'@@LABELS@@':json.dumps(labels,ensure_ascii=False),'@@MODEL@@':json.dumps(vb64),'@@RUN@@':RUN}.items():body=body.replace(k,v)
assert '@@' not in body
(D/'RailDepot01.html').write_text(body);shutil.copy2(V/'day_NW.png',D/'RailDepot01_Preview.png');shutil.copy2(R/'RailDepot01.nbt',D/'RailDepot01.nbt');shutil.copy2(R/'RailDepot01.schem',D/'RailDepot01.schem')
W=D/f'RailDepot01_{RUN}_Create6.0.10';ImageOps.fit(Image.open(V/'day_NW.png'),(64,64)).save(W/'icon.png')
readme=f'''RailDepot01 / 新港列车所 / {RUN}
Minecraft 1.21.1 + Create 6.0.10；目标 NeoForge 21.1.244。
新建原创场地 480×240，高度容器104；15层综合楼、低层库房与员工配套。
两进八出；7段曲线52.668–56.722格；有效检修120格；以约90格编组校核。
原附件：两端驾驶+中间车厢，车体包络约68格，宽5格。原始参考与校核尺度分开。
新世界不含活动列车；只有Create的轨道、车站、信号与示范时刻表。
调度楼一层木桶 -18 65 62：循环时刻表，20秒停站。
不要将离线检查理解为自动运行已通过。需要实机验证区块加载、轨道图、站名、双向驾驶、信号方向与时刻表。
独立世界目录 RailDepot01_{RUN}_Create6.0.10 放入 saves；出生点 -50 65 111。
原生 .nbt 用于Create蓝图导入测试；.schem 为Sponge v3，保留完整空气和嵌套数据。WorldEdit导入未实测。
使用v3是为了让Sponge的实体类型Id与Create内部UUID Id各自保留，不能压成同一个字段。

复现：Python3 + numpy、Pillow；项目deps提供nbtlib。EGL/OpenGL用于固定图渲染。
python src/build_depot.py NEW_RUN
python src/audit_rail.py NEW_RUN
python src/cameras.py NEW_RUN
python src/preview.py NEW_RUN
python src/render_all.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
python src/research_views.py
python src/deliver.py NEW_RUN
打包前将世界放在deliverables/RailDepot01_NEW_RUN_Create6.0.10。

input/source/：原始三个NBT；research/：测量、数据示意及证据分层；runs/{RUN}/：最终模型和检查。
src/：本案例生成器及Create适配器；support/：复用HAF核心；reference/create/：MIT许可源码与来源记录。
Create官方美术资产未打包；预览为独立的无纹理近似网格。
Mod运行环境不随包分发。需自行使用服务器对应版本及依赖；未改写用户服务器配置。
完整报告 RailDepot01.html；独立旋转模型 RailDepot01_Model.html。
'''
(P/'README.txt').write_text(readme);(W/'DEPOT_GUIDE.txt').write_text(readme)
manifest={'project':'RailDepot01','run':RUN,'source_nbt_sha256':sp['source_nbt_sha256'],'geometry':check,'rail_audit':audit,'world':world,'schematic':sch,'fixed_views':32,'game':'not_run','browser_runtime':'not_tested','source_references_preserved':True,'surface_revision':surface}
(R/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(D/'RailDepot01_World_Create6.0.10.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(W.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(D))
with zipfile.ZipFile(D/'RailDepot01_Project.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 def add(p,a):z.write(p,'RailDepot01_Project/'+str(a))
 for folder in ['src','support','input','research','deps','reference','assets']:
  for p in sorted((P/folder).rglob('*')):
   if not p.is_file() or '__pycache__' in str(p) or p.suffix=='.pyc' or any(q.startswith('.') for q in p.relative_to(P).parts):continue
   if p.name in ['x_ortho.json','z_ortho.json'] or p.name.startswith('baseline_'):continue
   add(p,p.relative_to(P))
 for p in sorted(R.iterdir()):
  if p.is_file() and p.name!='interactive_payload.json':add(p,p.relative_to(P))
 for p in sorted(V.glob('*.png')):add(p,p.relative_to(P))
 for n in ['render_report.json','scene/scene.json']:add(V/n,(V/n).relative_to(P))
 add(P/'README.txt','README.txt');add(D/'RailDepot01_Model.html','RailDepot01_Model.html')
for n in ['RailDepot01.html','RailDepot01_World_Create6.0.10.zip','RailDepot01_Project.zip','RailDepot01.nbt','RailDepot01_Preview.png']:
 p=D/n;print(n,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
