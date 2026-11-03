from pathlib import Path
import sys,json,base64,io,html,hashlib,zipfile,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P/'runs/G03';V=P/'review/previews/G03_Guanggang01';D=P/'deliverables';D.mkdir(exist_ok=True)
spec=json.loads((R/'spec.json').read_text());check=json.loads((R/'check.json').read_text());world=json.loads((R/'world_check.json').read_text());schem=json.loads((R/'schem_check.json').read_text())
def data_img(name):
 im=Image.open(V/(name+'.png'));buf=io.BytesIO();im.save(buf,format='WEBP',quality=89,method=6);return 'data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()
names=['day_SE','day_SW','day_NW','day_NE','night_SE','night_SW','night_NW','night_NE','top','furnace_detail','workshop_cut','workshop_exploded','rolling_section','rolling_inside','elevation_front','elevation_back','elevation_left','elevation_right']
imgs={n:data_img(n) for n in names}
payload=json.loads((R/'interactive_payload.json').read_text())
for b in payload['buildings']:b['floors']=list(range(b['geometry_bounds'][1][0],b['geometry_bounds'][1][1],4));b['levels']=len(b['floors'])
options=''.join('<option value="'+b['id']+'">'+html.escape(b['name'])+'</option>' for b in payload['buildings'])
viewer=(P/'assets/industrial_shell.html').read_text().replace('@@OPTIONS@@',options).replace('@@DATA@@',json.dumps(payload,ensure_ascii=False,separators=(',',':'))).replace('@@JS@@',(P/'assets/industrial_viewer.js').read_text())
(D/'Guanggang01_Model.html').write_text(viewer)
vb64=base64.b64encode(viewer.encode()).decode()
labels={'day_SE':'日景 · 入口东侧','day_SW':'日景 · 入口西侧','day_NW':'日景 · 料场一侧','day_NE':'日景 · 煤气柜一侧','night_SE':'夜景 · 入口东侧','night_SW':'夜景 · 入口西侧','night_NW':'夜景 · 料场一侧','night_NE':'夜景 · 煤气柜一侧','top':'垂直俯视 · 完整厂区'}
buttons=''.join('<button class="viewtab'+(' active' if n=='day_SE' else '')+'" data-view="'+n+'">'+s+'</button>' for n,s in labels.items())
fac=[('furnace','01','高炉与检修塔架','中心高耸体量，外框架、环形平台、爬梯与下行煤气管。'),('stoves','02','三座热风炉与除尘','成组穹顶圆筒，与烟囱和管路形成次级轮廓。'),('gas','03','大型煤气柜','低而宽的圆筒罐体，外圈钢架和环形检修道。'),('stock','04','料仓与上料斜廊','三格堆料、集料棚和有支撑的斜向通廊。'),('workshop','05','锯齿顶机修车间','砖墙、高侧窗、天车、检修台与钢料。'),('rolling','06','屋脊采光轧钢厂房','长轴设备线，吊装通道和连续悬吊照明。'),('rail','07','铁路侧线','两条侧线、矿料车与机车静态造型。'),('cooling','08','循环水设施','水池、风机单元与泵送管路。')]
cards=''.join('<button class="facility" data-fac="'+id+'"><span>'+n+'</span><div><b>'+name+'</b><p>'+desc+'</p></div><i>↗</i></button>' for id,n,name,desc in fac)
def fig(n,caption):return '<figure><img loading="lazy" data-img="'+n+'" alt="'+caption+'"><figcaption>'+caption+'</figcaption></figure>'
source_hash=spec['source_nbt_sha256']
schemdata=base64.b64encode((R/'Guanggang01.schem').read_bytes()).decode()
nbtdata=base64.b64encode((R/'Guanggang01.nbt').read_bytes()).decode()
body='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广钢式工业区 · 一号钢厂</title><style>
:root{--ink:#26312d;--paper:#f0eee7;--muted:#6e7770;--rust:#a75136;--line:#d4d7cc;--green:#46695a}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 system-ui,-apple-system,"Microsoft YaHei",sans-serif}a{color:var(--rust)}button{font:inherit;cursor:pointer}header,main,footer{max-width:1420px;margin:auto;padding:0 36px}nav{display:flex;justify-content:space-between;align-items:center;padding:22px 0;border-bottom:1px solid var(--line);font-size:12px;letter-spacing:.12em}nav a{color:var(--ink);text-decoration:none}.hero{display:grid;grid-template-columns:1.25fr 1fr;gap:30px;align-items:end;padding:40px 0 28px}.eyebrow{font-size:13px;letter-spacing:.18em;color:var(--rust);font-weight:700}h1{font-weight:650;font-size:clamp(34px,4vw,62px);letter-spacing:-.04em;line-height:1.18;margin:12px 0}h2{font-size:28px;font-weight:650;margin:0 0 10px}h3{font-size:20px;margin:0 0 8px}.intro{max-width:520px;color:#58635b;margin:0 0 5px}.tag{display:inline-block;border:1px solid #b8c6b9;border-radius:30px;padding:2px 12px;font-size:12px;margin:12px 6px 0 0}.frame{background:#c3cbbf;border:1px solid var(--line);border-radius:5px;overflow:hidden}.mainimage{display:block;width:100%;aspect-ratio:1.44;object-fit:cover}.strip{display:flex;gap:7px;flex-wrap:wrap;padding:15px 0}.viewtab{background:transparent;border:1px solid #c9cfc4;border-radius:4px;padding:6px 12px;font-size:13px;color:var(--ink)}.viewtab.active{background:var(--ink);border-color:var(--ink);color:white}.caption{font-size:12px;color:var(--muted);margin:5px 0}.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:28px 0 0}.stat{padding:20px 16px;border-right:1px solid var(--line)}.stat:last-child{border:0}.stat strong{font-size:29px;font-weight:650;display:block}.stat span{font-size:12px;color:var(--muted)}section{padding:48px 0;border-bottom:1px solid var(--line)}.sectionhead{display:flex;gap:25px;justify-content:space-between;align-items:baseline;margin-bottom:18px}.sectionhead p{font-size:14px;color:var(--muted);max-width:560px;margin:0}.modelbox{position:relative;border:1px solid var(--line);background:#dce3d8;border-radius:5px;overflow:hidden}.modelbox iframe{display:block;width:100%;height:740px;border:0}.modelcover{height:390px;display:flex;justify-content:center;align-items:center;text-align:center;background:linear-gradient(135deg,#dbe2d5,#cad6ca)}.primary{display:inline-block;background:var(--rust);color:#fff;border:0;border-radius:4px;padding:13px 24px;text-decoration:none;font-weight:600}.secondary{display:inline-block;border:1px solid #bec8bb;border-radius:4px;padding:12px 20px;color:var(--ink);text-decoration:none;background:transparent}.small{font-size:13px;color:var(--muted)}.twocol{display:grid;grid-template-columns:1fr 1fr;gap:24px}.plan img{width:100%;display:block;border-radius:4px}.facilities{display:grid;grid-template-columns:1fr 1fr;gap:8px}.facility{display:flex;text-align:left;align-items:start;gap:10px;width:100%;padding:13px 9px;background:transparent;border:0;border-bottom:1px solid var(--line);color:var(--ink)}.facility:hover{background:#e5e8dd}.facility>span{color:var(--rust);font-size:13px;font-weight:700}.facility b{font-size:14px}.facility p{font-size:12px;color:var(--muted);margin:4px 0}.facility i{font-style:normal;margin-left:auto}.gallery{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}figure img{display:block;width:100%;border:1px solid var(--line);border-radius:4px}figcaption{font-size:13px;color:var(--muted);padding:8px 0}.wide{margin-bottom:22px}details{border:1px solid var(--line);padding:14px 18px;border-radius:4px;margin-top:24px}summary{cursor:pointer;font-weight:600}table{border-collapse:collapse;width:100%;margin:15px 0;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}th{font-weight:600;background:#e5e7de}code{font-family:ui-monospace,monospace;font-size:12px;word-break:break-all}.downloadgrid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.downloadcard{border:1px solid var(--line);padding:22px;border-radius:4px}.downloadcard p{font-size:14px;color:var(--muted)}footer{padding-top:24px;padding-bottom:40px;font-size:12px;color:var(--muted)}.note{border-left:3px solid var(--rust);padding:4px 16px;font-size:14px;color:#59635b;margin:22px 0}.links{display:flex;gap:10px;flex-wrap:wrap}@media(max-width:800px){header,main,footer{padding-left:18px;padding-right:18px}.hero,.twocol,.downloadgrid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.stat:nth-child(2){border-right:0}.sectionhead{display:block}.gallery{gap:12px}.facilities{grid-template-columns:1fr 1fr}.modelbox iframe{height:610px}section{padding:32px 0}nav{font-size:10px}h2{font-size:24px}}
</style></head><body><header><nav><b>GAFAcraft / INDUSTRIAL STUDY 01</b><a href="#model">旋转模型 ↗</a></nav><div class="hero"><div><div class="eyebrow">GUANGGANG-INSPIRED STEELWORKS</div><h1>广钢式工业区<br>一号钢厂</h1><span class="tag">原创工业样板</span><span class="tag">Java 1.21.1</span><span class="tag">G03 · 可查看版本</span></div><p class="intro">用高炉的垂直骨架、上料通廊的斜线和煤气柜的厚重圆筒，建立老钢厂的轮廓。砖墙与锯齿屋顶围合生产院落，铁路、检修路和管廊把设施连接起来。</p></div></header><main>
<div class="frame"><img id="heroImage" class="mainimage" data-img="day_SE" alt="广钢式工业区整体模型"></div><div class="strip">@@BUTTONS@@</div><p id="viewcaption" class="caption">日景 · 入口东侧</p><p class="caption">所有图像由交付 NBT 回读渲染。方块形状、材质颜色和光照为离线近似，非游戏截图；方位按模型定义。</p>
<div class="stats"><div class="stat"><strong>240 × 192</strong><span>厂区占地 / 方块</span></div><div class="stat"><strong>11 组</strong><span>设施与场地构件</span></div><div class="stat"><strong>216,068</strong><span>最终非空气方块</span></div><div class="stat"><strong>66 种</strong><span>使用的方块状态</span></div></div>
<section id="model"><div class="sectionhead"><h2>把厂区转过来看</h2><p>拖动旋转、缩放，切换昼夜。可以单独选择高炉、煤气柜或车间，也能逐段查看内部。</p></div><div class="modelbox"><div class="modelcover" id="modelcover"><div><button id="loadModel" class="primary">打开可旋转模型</button><p class="small">模型与资源已内嵌，无需联网。较旧设备可使用上方固定视图。</p></div></div><iframe id="modelFrame" title="一号钢厂可旋转模型" hidden allow="fullscreen"></iframe></div></section>
<section><div class="sectionhead"><h2>一片有秩序的老厂区</h2><p>入口在模型下方；铁路沿左侧，原料区在后场。高炉居中，公用设施偏右，厂房集中在前场。</p></div><div class="twocol"><div class="plan"><img loading="lazy" data-img="top" alt="完整厂区垂直俯视"><p class="caption">真实垂直俯视。点击右侧设施，可跳入对应的独立模型。</p></div><div class="facilities">@@CARDS@@</div></div><p class="note">这是借鉴广钢工业遗存设施语言的原创钢厂。场地布局、设备比例与厂房组合均为此次设计；暂未对应广钢的某一年代或精确厂区总图。</p></section>
<section><div class="sectionhead"><h2>从设备轮廓到厂房内部</h2><p>检修框架保留空隙；厂房门洞真实留空；吊灯有链条支撑。设备和车辆以静态造型表达工业用途。</p></div><div class="gallery">@@DETAILS@@</div><details><summary>查看机修车间：平面切低与分层拆解</summary><div class="gallery" style="margin-top:18px">@@EXPLODED@@</div><p class="small">拆解仅沿标高分离同一模型的地坪、主体与屋顶，方便检查内部关系；没有另画一套概念结构。</p></details><details><summary>查看四向正投影立面</summary><div class="gallery" style="margin-top:18px">@@ELEVATIONS@@</div></details></section>
<section><div class="sectionhead"><h2>放进 Minecraft 看看</h2><p>已提供独立世界存档、Sponge schematic 和项目源文件。整厂尺寸超过原版结构方块常用范围，优先打开世界存档。</p></div><div class="downloadgrid"><div class="downloadcard"><h3>独立世界 · Java 1.21.1</h3><p>使用随附的 <b>Guanggang01_World_1.21.1.zip</b>。解压后把 <code>Guanggang01_G03_1.21.1</code> 文件夹放入 <code>saves</code>，选择“一号钢厂”进入。</p><p>出生点：<code>12 65 83</code>，位于厂门内，创造模式。可用 <code>/time set night</code> 查看夜景。首次加载需计算光照。</p></div><div class="downloadcard"><h3>整体 schematic / 结构源文件</h3><p>Sponge v2 文件以厂门内的站立点为粘贴原点。范围包含空气，适合先粘贴到空白区域；尚未在 WorldEdit 中实测。</p><div class="links"><a class="primary" download="Guanggang01.schem" href="data:application/octet-stream;base64,@@SCHEMDATA@@">下载 .schem</a><a class="secondary" download="Guanggang01.nbt" href="data:application/octet-stream;base64,@@NBTDATA@@">下载源 .nbt</a></div></div></div><p class="small">原版方块，不依赖 Create。高炉、轧线、机车与货车为静态建筑造型；本版未加入可运行的工业机械。</p></section>
<section><h2>交付核对</h2><table><thead><tr><th>检查对象</th><th>结果</th></tr></thead><tbody><tr><td>结构 NBT</td><td>独立解析，216,068 个方块与构建结果完全一致；DataVersion 3955。</td></tr><tr><td>世界 MCA 区域文件</td><td>252 个区块；回读比较 4,325,376 个单元，差异 0。</td></tr><tr><td>Sponge schematic</td><td>回读比较 4,055,040 个单元，差异 0；空气范围完整。</td></tr><tr><td>预览与源文件</td><td>18 个固定视图、可旋转模型使用同一份 NBT；PNG 内记录源文件哈希。</td></tr><tr><td>通行与照明</td><td>主干道两格净空检查通过。已检查整体、剖切、厂房内部与夜景；离线照明有近似。</td></tr><tr><td>游戏验证</td><td>未运行 Minecraft 客户端；实际碰撞、游戏光照与模组环境兼容性待进游戏验证。</td></tr></tbody></table><details><summary>设计依据与可复用资料</summary><p>广州市林业和园林局的广钢相关介绍为高炉、煤气柜、火车头等遗存类型提供参考。<a href="https://lyylj.gz.gov.cn/ztzl/lvst/stsfd/content/post_9910092.html" target="_blank" rel="noopener">打开官方参考资料 ↗</a>。本次没有使用现场测绘、历史设备图纸或直接下载的参考照片。</p><p>材料取向：砖红墙体、深灰钢框、浅灰容器、铜锈色与旧铜色屋顶。旧化按屋面条带和检修分块组织；厂区维持使用状态，绿化集中在边界与入口。</p><p><b>后续设计短提示：</b>岭南老钢厂，广钢式高炉组、三座热风炉、钢架煤气柜，斜向上料通廊，红砖锯齿顶机修车间、屋脊采光轧钢厂房，铁路矿料车，深灰框架与铜锈屋顶，保留检修通道，仍在使用的维护状态。</p><p>项目包包含构建脚本、HAF 构件核心、独立 NBT 读取器、状态盒预览、世界导出与回读检查、原创设计交接数据。工业设施几何由本案例适配器生成。</p><p class="small">最终 NBT SHA-256：<br><code>@@HASH@@</code></p></details></section></main><footer>GAFAcraft / HAF · Guanggang01 · G03<br>原创样板，供服务器建筑设计与后续深化使用。</footer>
<script>const IMAGES=@@IMAGES@@;const LABELS=@@LABELS@@;const MODEL=@@VIEWER@@;let modelLoaded=false;function loadModel(){if(!modelLoaded){const bytes=Uint8Array.from(atob(MODEL),c=>c.charCodeAt(0));document.getElementById('modelFrame').srcdoc=new TextDecoder().decode(bytes);document.getElementById('modelFrame').hidden=false;document.getElementById('modelcover').style.display='none';modelLoaded=true;}return document.getElementById('modelFrame');}document.getElementById('loadModel').onclick=loadModel;document.querySelectorAll('[data-img]').forEach(el=>el.src=IMAGES[el.dataset.img]);document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{document.getElementById('heroImage').src=IMAGES[b.dataset.view];document.getElementById('viewcaption').textContent=LABELS[b.dataset.view];document.querySelectorAll('[data-view]').forEach(q=>q.classList.toggle('active',q===b));});document.querySelectorAll('[data-fac]').forEach(b=>b.onclick=()=>{const frame=loadModel();document.getElementById('model').scrollIntoView({behavior:'smooth'});let tries=0;const timer=setInterval(()=>{if(frame.contentWindow?.modelReady){frame.contentWindow.postMessage({type:'g01_view',id:b.dataset.fac},'*');clearInterval(timer);}else if(++tries>80)clearInterval(timer);},150);});</script></body></html>'''
replacements={'@@BUTTONS@@':buttons,'@@CARDS@@':cards,'@@DETAILS@@':fig('furnace_detail','高炉细部：塔架、检修平台、爬梯与大直径管路。')+fig('rolling_inside','轧钢厂房内部：天车轨道、悬吊照明与设备线。')+fig('rolling_section','轧钢厂房剖切：沿模型 X 标高面切开，观察空间深度。')+fig('day_NW','后场视角：料仓、斜向通廊与铁路的组合。'),'@@EXPLODED@@':fig('workshop_cut','机修车间平面切低：检修台、钢料和中央通道。')+fig('workshop_exploded','机修车间分层拆解：地坪、主体、锯齿屋顶。'),'@@ELEVATIONS@@':''.join(fig('elevation_'+n,'模型'+s+'正投影') for n,s in [('front','入口向'),('back','后场向'),('left','铁路向'),('right','煤气柜向')]),'@@HASH@@':source_hash,'@@IMAGES@@':json.dumps(imgs,separators=(',',':')),'@@LABELS@@':json.dumps(labels,ensure_ascii=False),'@@VIEWER@@':json.dumps(vb64),'@@SCHEMDATA@@':schemdata,'@@NBTDATA@@':nbtdata}
for k,v in replacements.items():body=body.replace(k,v)
body=body.replace('</style>','[hidden]{display:none!important}</style>').replace('沿模型 X 标高面切开','沿模型 X 方向切开')
assert '@@' not in body
(D/'Guanggang01.html').write_text(body)
shutil.copy2(V/'day_SE.png',D/'Guanggang01_Preview.png');shutil.copy2(R/'Guanggang01.schem',D/'Guanggang01.schem')
readme='''Guanggang01 / 广钢式工业区 · 一号钢厂
原创样板，非广钢实测复原。用地 240 × 192 方块，结构容器高 88 方块。
Java 1.21.1 / DataVersion 3955，原版方块，无必需模组。
最终运行 G03。所有图片和旋转模型由最终 NBT 独立回读派生。
世界存档：Guanggang01_G03_1.21.1，放入 saves。出生点 12 65 83。
schem：Sponge v2，厂门内站立点为粘贴原点，包含完整空气范围。WorldEdit 未实测。
NBT：完整场景源数据，超出原版结构方块常用尺寸，优先使用存档或 schem。
未运行 Minecraft 客户端。机器、车辆、生产线都是静态造型。灯光离线近似。

复现（Python 3.10+，numpy、Pillow；nbtlib 已附在 deps）：
python src/build_industrial.py NEW_RUN
python src/preview.py NEW_RUN
python src/export_world.py NEW_RUN /绝对路径/新世界目录
python src/export_schematic.py NEW_RUN
python src/pack_interactive.py NEW_RUN
固定视图：src/preview.py NEW_RUN runs/G03/camera_batch_0.json，依次批次 0..5。
源构建脚本是本案例参数化适配器；不是任意工厂的全自动生成器。

内容：
src / support：本案例脚本与复用的方块核心、独立读取器、EGL 预览工具。
assets：预览着色器与交互模型脚本。
input：原创设计交接、规划核对、来源记录和世界模板。
hafusion / docs：HAF 0.4 交接检查器及本案例扩充的工业用途类别。
runs/G03：NBT、schem、构件归属、规格与检查结果。
review：最终 18 个 PNG 视图及渲染记录；PNG 内含源 NBT 哈希。
Guanggang01_Model.html：离线可旋转模型。

来源参考：广州市林业和园林局 https://lyylj.gz.gov.cn/ztzl/lvst/stsfd/content/post_9910092.html
原型范围：高炉、热风炉、煤气柜、料仓、上料斜廊、厂房、铁路和循环水设施。
尚未覆盖：焦化、烧结、炼钢、能源站等完整联合钢厂系统；未模拟工艺能力。
'''
(P/'README.txt').write_text(readme)
manifest={'project':'Guanggang01','run':'G03','scope':'original compact steelworks inspired by Guanggang heritage','source_nbt_sha256':source_hash,'final_geometry':check,'world':world,'schematic':schem,'visual_review':'18 same-source views reviewed, including interior, section and night','interactive':'WebGL2 package checked structurally and JS syntax checked; browser runtime not executed','source_packages_recovered':['HAF04.zip','Qilou04_Project.zip'],'drafts_preserved_locally':['G01 route lamp collision fixed','G02 roof light hangers and entrance steps added'],'no_game_run':True}
(R/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Archive only current final material. Previous projects/worlds remain untouched.
with zipfile.ZipFile(D/'Guanggang01_World_1.21.1.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted((D/'Guanggang01_G03_1.21.1').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(D))
with zipfile.ZipFile(D/'Guanggang01_Project.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 def add(p,arc):z.write(p,'Guanggang01_Project/'+str(arc))
 for folder in ['src','support','assets','input','hafusion','docs','deps']:
  for p in sorted((P/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.pyc':add(p,p.relative_to(P))
 for p in sorted(R.iterdir()):
  if p.is_file() and p.name!='interactive_payload.json':add(p,p.relative_to(P))
 for p in sorted(V.iterdir()):
  if p.is_file() and p.name not in ['qa_contact.png','render_report_before_interior.json']:add(p,p.relative_to(P))
 add(P/'README.txt','README.txt');add(D/'Guanggang01_Model.html','Guanggang01_Model.html')
 # Bounded, highly compressible final mesh enables replay without rebuilding.
 for p in sorted((V/'scene').iterdir()):
  if p.is_file():add(p,p.relative_to(P))
for p in [D/'Guanggang01.html',D/'Guanggang01_World_1.21.1.zip',D/'Guanggang01_Project.zip',D/'Guanggang01_Preview.png']:
 print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
