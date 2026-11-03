"""Package the expanded, NBT-derived campus review and reproducible artifacts."""
from pathlib import Path
import sys,json,base64,io,html,hashlib,zipfile,shutil
from PIL import Image,ImageOps
P=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=P/'runs'/RUN;V=P/'review/previews'/(RUN+'_ModernFactory01');D=P/'deliverables'
sp=json.loads((R/'spec.json').read_text());check=json.loads((R/'check.json').read_text());world=json.loads((R/'world_check.json').read_text());sch=json.loads((R/'schem_check.json').read_text());surface=json.loads((R/'surface_revision.json').read_text());views=json.loads((R/'cameras.json').read_text());IMAGES={}
for name,path in [(v['id'],V/(v['id']+'.png')) for v in views]+[('baseline',P/'assets/baseline_M03.png'),('baseline_E06',P/'assets/baseline_E06/day_NE.png')]:
 im=Image.open(path);buf=io.BytesIO();im.save(buf,format='WEBP',quality=89,method=6);IMAGES[name]='data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()
payload=json.loads((R/'interactive_payload.json').read_text())
for b in payload['buildings']:b['floors']=list(range(b['geometry_bounds'][1][0],b['geometry_bounds'][1][1],4));b['levels']=len(b['floors'])
opts=''.join('<option value="'+b['id']+'">'+html.escape(b['name'])+'</option>' for b in payload['buildings'])
model=(P/'assets/industrial_shell.html').read_text().replace('@@OPTIONS@@',opts).replace('@@DATA@@',json.dumps(payload,ensure_ascii=False,separators=(',',':'))).replace('@@JS@@',(P/'assets/industrial_viewer.js').read_text())
(D/'ModernFactory01_Model.html').write_text(model);vb64=base64.b64encode(model.encode()).decode()
style=(P/'assets/report_style.css').read_text()+'\n.flow{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.flow span{padding:8px 13px;background:#dee8ed;font-size:14px;border-radius:4px}.gallery img{object-fit:contain}.mainimage{object-fit:contain}.pill{font-size:12px;color:#5b786b}.comparison{background:#e6edf0;padding:20px;border-radius:5px}a.download-link{display:inline-block;margin:8px 16px 0 0}@media(max-width:520px){.gallery{grid-template-columns:1fr}}'
labels={'day_NE':'日景 · 罐区与露天生产设施','day_NW':'日景 · 原料堆场一侧','day_SE':'日景 · 办公生活区一侧','day_SW':'日景 · 办公楼与主厂房','top':'完整园区 · 垂直俯视','night_NE':'夜景 · 罐区一侧','night_NW':'夜景 · 料场一侧','night_SE':'夜景 · 员工生活区','night_SW':'夜景 · 办公楼一侧'}
tabs=''.join('<button data-view="'+n+'" class="viewtab'+(' active' if n=='day_NE' else '')+'">'+s+'</button>' for n,s in labels.items())
def fig(n,s):return '<figure><img loading="lazy" data-img="'+n+'" alt="'+s+'"><figcaption>'+s+'</figcaption></figure>'
fac=[('rawyard','01','原料堆场','四组材料堆、卸料围挡与装载机。'),('silos','02','筒仓与输送','六座高架筒仓，接入封闭输送廊。'),('process','03','露天加工设施','六组罐式设备、钢架平台与管线。'),('tankfarm','04','集中储罐区','四座大罐、连接管道和检修围界。'),('production','05','连续生产主厂房','两条长生产线，附控制夹层。'),('packing','06','包装检测车间','包装机组、物料暂存与搬运通道。'),('warehouse','07','成品库与月台','多层货架、五个装卸口及货车前场。'),('office','08','独立办公楼','八层主楼、五层侧翼和入口挑空门厅。'),('canteen','09','食堂与活动中心','两层；厨房取餐、餐位、阅读与休息。'),('dormA','10','员工宿舍 A','六层、60 间双人房、120 个床位。'),('dormB','11','员工宿舍 B','六层、60 间双人房、120 个床位。'),('bridges','12','员工连廊','二层联系办公、食堂、宿舍和主厂房。'),('amenities','13','员工配套','庭院、球场、休息座椅与服务小屋。'),('utilities','14','动力及循环水','成组动力柜、水池与检修设施。'),('entry','15','门卫与入口','入口门架、值班室和停车位。')]
cards=''.join('<button class="facility" data-fac="'+id+'"><span>'+num+'</span><div><b>'+name+'</b><p>'+s+'</p></div><i>↗</i></button>' for id,num,name,s in fac)
plan=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 336" style="width:100%;background:#e9eee7;border-radius:4px" role="img" aria-label="按模型坐标绘制的园区功能分区与连接关系">']
for x,z,w,d in [(8,8,432,15),(8,23,15,306),(425,23,15,306),(23,114,402,19),(8,216,432,19),(8,315,432,14),(217,23,18,193)]:plan.append(f'<rect x="{x}" y="{z}" width="{w}" height="{d}" fill="#bcc5ca"/>')
for n,x,z,w,d,col in [('01',30,29,102,81,'#d8c7a9'),('02',148,30,57,81,'#9bbdc8'),('03',244,29,91,81,'#8ba7b7'),('04',350,29,70,81,'#b7cdd8'),('05',31,143,179,64,'#aac8db'),('06',246,144,76,63,'#8dbdc6'),('07',339,143,78,64,'#a2bcd1'),('08',32,249,95,26,'#bbc9d2'),('09',147,255,84,52,'#ded1b2'),('10',268,253,24,60,'#c5d7c6'),('11',328,253,24,60,'#c5d7c6'),('13',363,262,56,44,'#b5d7be')]:plan.append(f'<rect x="{x}" y="{z}" width="{w}" height="{d}" fill="{col}" stroke="#6b8390" stroke-width=".8"/><text x="{x+w/2}" y="{z+d/2+3}" text-anchor="middle" fill="#274f68" font-size="9" font-family="sans-serif">{n}</text>')
plan.append('<rect x="32" y="275" width="30" height="34" fill="#bbc9d2" stroke="#6b8390" stroke-width=".8"/><path d="M117 252V244H343M182 244V257M280 244V255M340 244V255M193 244V205" fill="none" stroke="#bf8d43" stroke-width="4"/><path d="M448 123H226V227H408" fill="none" stroke="#3479b8" stroke-width="2" stroke-dasharray="5 3"/><path d="M226 336V307" fill="none" stroke="#3c8a68" stroke-width="3"/><text x="401" y="322" font-size="8" fill="#274f68">入口侧 ↓</text></svg>');plan=''.join(plan)
schemdata=base64.b64encode((R/'ModernFactory01.schem').read_bytes()).decode()
worldurl='https://chatgpt.com/library?file_id=libfile_8c8340c2b6248191855dce484707a663&account_id=personal';projecturl='https://chatgpt.com/library?file_id=libfile_b72ffac6559481919d35378943831b5d&account_id=personal'
body='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新港制造园 · 综合生产基地</title><style>@@STYLE@@</style></head><body><header><nav><b>GAFAcraft / MODERN INDUSTRY 01 · V3</b><a href="#model">打开旋转模型 ↗</a></nav><div class="hero"><div><div class="eyebrow">AN INTEGRATED MATERIALS CAMPUS</div><h1>新港制造园<br>综合生产基地</h1><span class="tag">新建 · 维护良好</span><span class="tag">Java 1.21.1</span><span class="tag">硬质场地修订 · 原创设计</span></div><p class="intro">把原料堆场、筒仓、罐式设备、长生产线和成品库组织成一片有生产过程感的新工厂。前场增加独立办公楼、食堂、宿舍与员工连廊，形成完整的工作和生活配套。</p></div></header><main><div class="frame"><img class="mainimage" id="heroImage" data-img="day_NE" alt="新港制造园扩建后整体预览"></div><div class="strip">@@TABS@@</div><p class="caption" id="viewcaption">日景 · 罐区与露天生产设施</p><p class="caption">所有新视图来自同一个最终 Minecraft 方块模型；材质与光照为离线近似，并非游戏截图。</p><div class="stats"><div class="stat"><strong>448 × 336</strong><span>占地，约为上一版的 2.47 倍</span></div><div class="stat"><strong>8 层</strong><span>独立办公主楼，附五层侧翼</span></div><div class="stat"><strong>2 × 6 层</strong><span>两栋宿舍，共 240 个床位</span></div><div class="stat"><strong>2 层食堂</strong><span>餐饮、培训、阅读与员工活动</span></div></div>
<section id="model"><div class="sectionhead"><h2>走进扩建后的园区</h2><p>拖动旋转、缩放，切换昼夜；选择设施可单独查看，水平切片可检查室内布置。</p></div><div class="modelbox"><div class="modelcover" id="modelcover"><div><button class="primary" id="loadModel">打开可旋转模型</button><p class="small">模型资源全部内嵌，下载本页后也可离线打开。</p></div></div><iframe id="modelFrame" title="新港制造园完整旋转模型" hidden allow="fullscreen"></iframe></div></section>
<section><div class="sectionhead"><h2>让工作场地占据主画面</h2><p>根据本次反馈，把生产区残留的大块草地改为石质设备维护场地，员工前区改为灰色硬质铺装。绿化集中在边界窄带、树池、入口和员工休息处。</p></div><div class="gallery">@@GROUND_COMPARE@@</div><p>建筑、罐体、料场和生产设备的位置保持一致。道路与连廊继续承担原有通行关系，绿化作为点缀，场地以生产和后勤使用为主。</p></section><section><div class="sectionhead"><h2>原料、加工、仓储连成一片</h2><p>露天设备集中在后场，主车间与成品库位于中段，员工配套集中在入口侧。厂区保留浅灰围护、蓝色标识与清楚的维护边界。</p></div><div class="flow"><span>原料堆场</span><span>→ 筒仓给料</span><span>→ 加工设备与罐区</span><span>→ 连续生产</span><span>→ 检测包装</span><span>→ 成品仓储</span></div><div class="twocol"><div>@@PLAN@@<p class="caption">按实际模型坐标绘制。金色为二层员工连廊，蓝虚线为主要货运到达路径，绿线为员工入口。示意线不代表车辆转弯或工程工艺验证。</p>@@TOP@@</div><div class="facilities">@@CARDS@@</div></div><div class="note">这是一座按“综合新材料工厂”创作的 Minecraft 园区。设备和流程用于组织建筑场景，不对应某一座现实工厂或工程设计。</div><div class="gallery">@@PLANT@@</div></section>
<section><div class="sectionhead"><h2>车间与仓库都有内部内容</h2><p>主厂房放入两条长生产线和控制夹层；成品库设置多层货架、装卸月台和货车停靠前场。</p></div><div class="gallery">@@PRODUCTION@@</div></section>
<section><div class="sectionhead"><h2>把员工配套真正建进去</h2><p>二层连廊连接办公、食堂、两栋宿舍与主厂房。食堂一层布置厨房、取餐及 144 个座位，二层设 48 个餐饮／培训座位及休息阅读区。</p></div><div class="gallery">@@LIFE@@</div><details><summary>食堂与宿舍的平面布置</summary><div class="gallery" style="margin-top:18px">@@LIFEPLANS@@</div><p class="small">宿舍每栋六层，每层 10 间双人房；两栋合计 120 间房。A、B 栋采用相同布局。床、房门、木桶和厨房熔炉已写入原版方块状态及对应数据，尚待游戏内检查互动。</p></details></section>
<section><div class="sectionhead"><h2>独立办公楼也有足够的体量</h2><p>八层主楼配五层侧翼，上部两层退台；入口采用三层挑空门厅，内部安排接待、办公、会议和休息空间。</p></div><div class="gallery">@@OFFICE@@</div><details><summary>办公楼代表楼层平面</summary><div class="gallery" style="margin-top:18px">@@OFFICEPLANS@@</div><p class="small">展示一层入口、四层标准办公和八层退台会议层；完整逐层几何可在旋转模型中切片查看。爆炸图只在展示时把楼层竖向分开。</p></details><details><summary>园区四向正投影</summary><div class="gallery" style="margin-top:18px">@@ELEVATIONS@@</div></details></section>
<section><div class="sectionhead"><h2>园区此前的扩建基础</h2><p>从车间与库房为主的小园区，扩展为生产设施和员工配套同时可见的综合工厂。</p></div><div class="gallery comparison">@@COMPARISON@@</div><table><thead><tr><th>项目</th><th>上一版</th><th>本次扩建</th></tr></thead><tbody><tr><td>占地</td><td>272 × 224</td><td>448 × 336，约 2.47 倍</td></tr><tr><td>工业特征</td><td>装配／加工厂房、成品库</td><td>增加露天料场、筒仓、加工塔架、储罐及输送管廊</td></tr><tr><td>办公</td><td>三层研发办公</td><td>八层主楼＋五层侧翼</td></tr><tr><td>员工设施</td><td>局部连廊与庭院</td><td>跨楼员工廊网、两层食堂、两栋宿舍、运动休闲配套</td></tr></tbody></table><p class="caption">对照图片分别适配画幅，未采用相同缩尺；面积变化以上表为准。</p></section>
<section><div class="sectionhead"><h2>在 Minecraft 中查看</h2><p>可下载完整世界直接查看，也可以取出整体 schematic 放进测试区域。</p></div><div class="downloadgrid"><div class="downloadcard"><h3>独立世界 · Java 1.21.1</h3><p>解压 <b>ModernFactory01_World_1.21.1.zip</b>，将 <code>ModernFactory01_@@RUN@@_1.21.1</code> 文件夹放进 <code>saves</code>。</p><p>出生点 <code>2 65 161</code>，创造模式。首次加载需要计算光照；可用 <code>/time set night</code> 看夜景。</p><a class="download-link" href="@@WORLDURL@@" target="_blank" rel="noopener">打开世界存档 ↗</a><a class="download-link" href="@@PROJECTURL@@" target="_blank" rel="noopener">打开项目源文件 ↗</a></div><div class="downloadcard"><h3>整体 schematic</h3><p>Sponge v2，以主入口为粘贴原点，包含完整包围盒的空气。先粘贴到空白测试区，避免覆盖已有建筑；WorldEdit 导入尚未实测。</p><a class="primary" download="ModernFactory01.schem" href="data:application/octet-stream;base64,@@SCHEM@@">下载 .schem</a><p>不依赖必装模组；生产设备、管道和车辆是静态建筑造型。</p></div></div></section>
<section><h2>交付核对</h2><table><thead><tr><th>项目</th><th>已完成的检查</th></tr></thead><tbody><tr><td>结构模型</td><td>@@BLOCKS@@ 个非空气方块，@@PALETTE@@ 个状态；独立回读与构建结果一致。</td></tr><tr><td>世界与 schematic</td><td>分别回读比较 @@WORLD_CELLS@@ 和 @@SCHEM_CELLS@@ 个单元，差异为 0；@@BES@@ 个方块实体的数据一致。</td></tr><tr><td>通行几何</td><td>主要道路、员工连廊的中心路线和连续地板通过检查；跨路桥下七格净空，@@STAIRS@@ 段楼梯逐级净空及侧向出口检查通过。</td></tr><tr><td>宿舍与家具</td><td>240 张宿舍床＋1 张服务小屋床，120 套双格门；床头床尾、支撑及门框检查通过。</td></tr><tr><td>预览</td><td>@@VIEWS@@ 个固定视图与旋转模型同源；包含昼夜四向、俯视、剖切、平面、爆炸和立面。</td></tr><tr><td>尚待实测</td><td>未运行 Minecraft 客户端或 WorldEdit；真实碰撞、交互、游戏照明和服务器环境兼容性仍需现场确认。旋转预览已核对数据及脚本语法，未进行浏览器运行测试。</td></tr></tbody></table><details><summary>设计关键词与项目说明</summary><p><b>短提示词：</b>大型现代综合工厂，露天原料堆场，高架筒仓，白灰储罐，深灰加工塔架，连续生产线，包装车间与成品库，八层独立办公楼，两层食堂，两栋六层员工宿舍，二层步行连廊，新建维护状态。</p><p><b>长提示词：</b>448 × 336 方块的综合新材料工厂。后场以四组原料堆场、六座高架筒仓、六组罐式加工设备和四座大储罐形成工业天际线，设备间通过输送廊与管线连接。中段布置长生产车间、包装检测车间与多层货架成品库，设置独立装卸前场。入口侧为八层独立办公主楼及五层侧翼，两层食堂包含厨房、取餐、餐饮、阅读和活动，两栋六层宿舍按双人房布置。二层玻璃步行廊联系办公、食堂、宿舍与主车间控制夹层，跨路处保留七格净空。白灰墙面和罐体、深灰结构、蓝色分区标识，清楚的门窗、维护平台和地面分区，辅以门卫、停车、球场、循环水和动力配套，保持新建且维护良好的外观。</p><p class="small">项目包包含案例生成器、参数交接、房间清单、HAF 方块核心、独立读取、预览、世界与 schematic 导出。当前适配器针对本案例，不代表任意工厂的通用自动生成器。</p><p class="small">Schematic 格式参考：<a href="https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md" target="_blank" rel="noopener">Sponge Schematic v2 specification</a>。最终 NBT SHA-256：<br><code>@@HASH@@</code></p></details></section></main><footer>GAFAcraft / HAF · ModernFactory01 · @@RUN@@<br>新港制造园 · 综合生产基地 · 原创扩建版</footer><script>const IMAGES=@@IMAGES@@;const LABELS=@@LABELS@@;const MODEL=@@MODEL@@;let loaded=false;function loadModel(){const f=document.getElementById('modelFrame');if(!loaded){f.srcdoc=new TextDecoder().decode(Uint8Array.from(atob(MODEL),c=>c.charCodeAt(0)));f.hidden=false;document.getElementById('modelcover').style.display='none';loaded=true;}return f;}document.getElementById('loadModel').onclick=loadModel;document.querySelectorAll('[data-img]').forEach(e=>e.src=IMAGES[e.dataset.img]);document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.getElementById('heroImage').src=IMAGES[b.dataset.view];document.getElementById('viewcaption').textContent=LABELS[b.dataset.view];document.querySelectorAll('[data-view]').forEach(q=>q.classList.toggle('active',q===b));});document.querySelectorAll('[data-fac]').forEach(b=>b.onclick=()=>{const f=loadModel();document.getElementById('model').scrollIntoView({behavior:'smooth'});let tries=0;const t=setInterval(()=>{if(f.contentWindow?.modelReady){f.contentWindow.postMessage({type:'m01_view',id:b.dataset.fac},'*');clearInterval(t);}else if(++tries>100)clearInterval(t);},150);});</script></body></html>'''
repl={'@@GROUND_COMPARE@@':fig('baseline_E06','调整前：扩建版中仍有较多连续草地。')+fig('day_NE','本版：生产区以石质地面、员工前区以硬质铺装为主，保留树池和边界绿化。'),'@@STYLE@@':style,'@@TABS@@':tabs,'@@PLAN@@':plan,'@@CARDS@@':cards,'@@TOP@@':fig('top','完整模型垂直俯视：后场设备、中段厂房、入口侧办公生活区。'),'@@PLANT@@':fig('rawyard_detail','原料堆场、高架筒仓与封闭输送廊。')+fig('process_detail','露天罐式加工设备与钢架检修平台。')+fig('tank_detail','集中储罐区：四座大罐、检修廊及循环水设施。'),'@@PRODUCTION@@':fig('production_cut','主厂房切低：两条长生产线、操作通道和控制夹层。')+fig('production_inside','主厂房内部视角：生产设备、屋架与条形照明。')+fig('warehouse_cut','成品库切低：多层货架与装卸前场。'),'@@LIFE@@':fig('bridge_detail','二层员工廊网：连接办公、食堂、宿舍与主厂房。')+fig('canteen_cut','食堂一层剖切：后侧厨房、取餐和成组餐位。')+fig('dorm_room','双人宿舍样间：真实原版床、储物、书桌和房门。'),'@@LIFEPLANS@@':fig('canteen_F1','食堂一层：厨房、取餐、洗消与 144 个座位。')+fig('canteen_F2','二层：48 个餐饮／培训座位、阅读及休息。')+fig('dorm_F2','宿舍二层：双面走廊、10 间双人房及北侧共用设施。'),'@@OFFICE@@':fig('office_section','办公楼剖切：入口挑空、侧翼与上部楼层。')+fig('office_exploded','办公楼分层拆解：八层主楼及五层侧翼。'),'@@OFFICEPLANS@@':''.join(fig('office_F'+str(n),f'办公 {n} 层：同源模型平面切片。') for n in [1,4,8]),'@@ELEVATIONS@@':''.join(fig('elevation_'+n,s+'正投影。') for n,s in [('front','入口侧'),('back','设备后场侧'),('left','料场及办公侧'),('right','储罐及宿舍侧')]),'@@COMPARISON@@':fig('baseline','上一版：小型现代车间与仓储园区。')+fig('day_NE','本次扩建：设备、厂房与办公生活区同时呈现。'),'@@BLOCKS@@':f"{check['blocks']:,}",'@@PALETTE@@':str(check['palette']),'@@WORLD_CELLS@@':f"{world['checked_cells']:,}",'@@SCHEM_CELLS@@':f"{sch['checked_cells']:,}",'@@BES@@':str(world['block_entities']),'@@STAIRS@@':str(check['stair_routes']),'@@VIEWS@@':str(len(views)),'@@SCHEM@@':schemdata,'@@HASH@@':sp['source_nbt_sha256'],'@@IMAGES@@':json.dumps(IMAGES,separators=(',',':')),'@@LABELS@@':json.dumps(labels,ensure_ascii=False),'@@MODEL@@':json.dumps(vb64),'@@RUN@@':RUN,'@@WORLDURL@@':worldurl,'@@PROJECTURL@@':projecturl}
for k,v in repl.items():body=body.replace(k,v)
assert '@@' not in body
(D/'ModernFactory01.html').write_text(body);shutil.copy2(V/'day_NE.png',D/'ModernFactory01_Preview.png')
W=D/f'ModernFactory01_{RUN}_1.21.1';ImageOps.fit(Image.open(V/'day_NE.png'),(64,64)).save(W/'icon.png')
readme=f'''ModernFactory01 V3 / 新港制造园 · 综合生产基地
硬质场地修订版：植被仅作边界、树池和休息区点缀。\n原创园区 448 × 336，高度容器 72；最终运行 {RUN}。相对上一版用地约 2.47 倍。
后场：原料堆场、筒仓、加工塔架、储罐及管廊。
中段：连续生产、包装检测、成品库及装卸区。
前场：八层办公主楼＋五层侧翼、两层食堂、两栋六层宿舍、员工连廊和配套。
宿舍 120 间双人房 / 240 个床位；食堂一层 144 席，二层 48 席及休息活动。
Java 1.21.1 / DataVersion 3955，原版方块，无必需模组。
世界目录 ModernFactory01_{RUN}_1.21.1 放入 saves，出生点 2 65 161。
Sponge v2 schematic 的粘贴原点为主入口，包含空气，先在空白测试区导入。
没有运行客户端或 WorldEdit；设备和车辆为静态造型，原版床/门/容器互动待实机验证。
预览使用真实 NBT 几何；材质、玻璃、照明为近似，水平切片按四格分段。

复现（Python 3.10+，numpy、Pillow；nbtlib 已在 deps）：
python src/build_expansion.py NEW_RUN
python src/access_audit.py NEW_RUN
python src/cameras.py NEW_RUN
python src/preview.py NEW_RUN
python src/render_all.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新的世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
python src/deliver.py NEW_RUN
EGL 渲染需要 libEGL / OpenGL 3.3；交互页面需要 WebGL2 与 DecompressionStream。
在 deliver.py 打包前，世界目录应为 deliverables/ModernFactory01_NEW_RUN_1.21.1。

input/：设计交接、空间与来源记录。
runs/{RUN}/：最终结构、schem、房间与通行数据、规格、独立检查。
review/：{len(views)} 张同源 PNG 及预览网格。
src/：本案例生成器、预览与导出程序。
support/：复用并针对原版床/木桶/熔炉补齐实体导出的 HAF 核心。
assets/：交互脚本、报告样式、上一版对照图。
ModernFactory01_Model.html：独立离线旋转模型。
本案例为原创建筑场景，不是实际工厂工程方案，也不是通用生成器。
'''
(P/'README.txt').write_text(readme)
manifest={'project':'ModernFactory01','run':RUN,'source_nbt_sha256':sp['source_nbt_sha256'],'geometry':check,'access_audit':json.loads((R/'access_audit.json').read_text()),'world':world,'schematic':sch,'visual_views':len(views),'game':'not_run','interactive':'WebGL2 package; byte integrity and JS syntax checks; browser runtime not tested','baseline_visual_feedback':'needs_revision; previous technical checks preserved in previous version','original_design':True,'surface_revision':surface};(R/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(D/'ModernFactory01_World_1.21.1.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(W.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(D))
with zipfile.ZipFile(D/'ModernFactory01_Project.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 def add(p,a):z.write(p,'ModernFactory01_Project/'+str(a))
 for folder in ['src','support','assets','input','hafusion','docs','deps']:
  for p in sorted((P/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.pyc':add(p,p.relative_to(P))
 for p in sorted(R.iterdir()):
  if p.is_file() and p.name!='interactive_payload.json' and not p.name.startswith('qa_') and not p.name.startswith('.'):add(p,p.relative_to(P))
 for p in sorted(V.rglob('*')):
  if p.is_file() and not p.name.startswith('qa_') and not any(v.startswith('.') for v in p.relative_to(P).parts):add(p,p.relative_to(P))
 add(P/'README.txt','README.txt');add(D/'ModernFactory01_Model.html','ModernFactory01_Model.html')
for name in ['ModernFactory01.html','ModernFactory01_World_1.21.1.zip','ModernFactory01_Project.zip','ModernFactory01_Preview.png']:
 p=D/name;print(name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
