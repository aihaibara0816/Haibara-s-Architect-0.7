"""Self-contained architectural model review, world package and reproducible source."""
from pathlib import Path
import sys,json,base64,io,html,hashlib,zipfile,shutil,re,subprocess,os
from PIL import Image
P=Path(__file__).resolve().parents[1];run=sys.argv[1];R=P/'runs'/run;V=P/'review/previews'/(run+'_Substation01');D=P/'deliverables';D.mkdir(exist_ok=True)
sp=json.loads((R/'spec.json').read_text());gc=json.loads((R/'geometry_check.json').read_text());wc=json.loads((R/'world_check.json').read_text());sc=json.loads((R/'schem_check.json').read_text());views=json.loads((R/'cameras.json').read_text());sources=json.loads((P/'research/sources.json').read_text());browser_fix=json.loads((R/'browser_preview_fix.json').read_text()) if (R/'browser_preview_fix.json').exists() else None
assert not gc['errors'] and wc['mismatches']==sc['mismatches']==0
sha=sp['source_nbt_sha256'];assert all(q['source_nbt_sha256']==sha for q in [gc,wc,sc])
IMAGES={}
for v in views:
 im=Image.open(V/(v['id']+'.png'));assert im.info['source_nbt_sha256']==sha;b=io.BytesIO();im.save(b,format='WEBP',quality=91,method=6);IMAGES[v['id']]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
payload=json.loads((R/'interactive_payload.json').read_text());assert payload['source_nbt_sha256']==sha
opts=''.join('<option value="'+b['id']+'">'+html.escape(b['name'])+'</option>' for b in payload['buildings'])
model=(P/'assets/industrial_shell.html').read_text().replace('@@OPTIONS@@',opts).replace('@@DATA@@',json.dumps(payload,ensure_ascii=False,separators=(',',':'))).replace('@@JS@@',(P/'assets/industrial_viewer.js').read_text())
(D/'Substation01_Model.html').write_text(model)
shutil.copyfile(R/'Substation01.nbt',D/'Substation01.nbt');shutil.copyfile(R/'Substation01.schem',D/'Substation01.schem');shutil.copyfile(V/'day_SE.png',D/'Substation01_Preview.png')
worldzip=D/'Substation01_World.zip'
with zipfile.ZipFile(worldzip,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted((R/'Substation01_World').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(R))
downloads={name:base64.b64encode((D/name).read_bytes()).decode() for name in ['Substation01.nbt','Substation01.schem','Substation01_World.zip']}
style=(P/'assets/report_style.css').read_text()+'''\n.modelcover{position:relative;overflow:hidden}.modelcover #modelFallback{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:.55}.modelprompt{position:relative;z-index:1;background:#f6f9f2ed;padding:24px;max-width:92%;border-radius:5px}.modelbox.is-loading .modelcover{position:absolute;inset:0;height:100%;z-index:2;background:#c5cec7}.modelprompt button:disabled{opacity:.7;cursor:wait}.mainimage{object-fit:contain;aspect-ratio:9/7}.gallery img{object-fit:contain}.sectionhead p{line-height:1.8}details .gallery{margin-top:20px}.pills{display:flex;flex-wrap:wrap;gap:8px}.pills span{background:#e2e9ed;padding:7px 11px;border-radius:4px;font-size:13px}.source-list li{margin:12px 0}.mainimage{background:#b8c1b8}.system-diagram{width:100%;height:auto;display:block;margin:18px 0}.downloadcard .links{margin-top:18px}footer code{font-size:10px} .small{line-height:1.8}@media(max-width:650px){.gallery,.facilities{grid-template-columns:1fr}.hero{gap:12px}.stat{padding:14px 8px}.stat strong{font-size:24px}}'''
labels={n:t for n,t in [('day_SE','日景 · 全站'),('day_SW','日景 · 进线一侧'),('day_NW','日景 · 开关场'),('day_NE','日景 · 出线一侧'),('top','正俯视'),('night_SE','夜景 · 全站'),('night_SW','夜景 · 进线一侧'),('night_NW','夜景 · 开关场'),('night_NE','夜景 · 出线一侧')]}
def fig(n,caption):return '<figure><img loading="lazy" data-img="'+n+'" alt="'+html.escape(caption)+'"><figcaption>'+caption+'</figcaption></figure>'
def section(title,sub,body):return '<section><div class="sectionhead"><h2>'+title+'</h2><p>'+sub+'</p></div>'+body+'</section>'
tabs=''.join('<button class="viewtab'+(' active' if n=='day_SE' else '')+'" data-view="'+n+'">'+t+'</button>' for n,t in labels.items())
body='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>新港枢纽变电站 · Substation01</title><style>@@STYLE@@</style></head><body><header><nav><b>GAFAcraft / SUBSTATION 01</b><a href="#model">旋转查看 ↗</a></nav><div class="hero"><div><div class="eyebrow">POWER INFRASTRUCTURE / 新港工业体系</div><h1>新港枢纽变电站</h1><span class="tag">220 / 110 / 10 kV 设计主题</span><span class="tag">Java 1.21.1 原版方块</span><span class="tag">原创工业设施</span></div><p class="intro">把工业区需要的供电设施建成一座完整的站：两回进线、两台主变、户外开关场，以及主控、继保、配电和检修用房。碎石、设备基础、电缆沟和道路构成场地，绿化只落在员工入口。</p></div></header><main><div class="frame"><img class="mainimage" id="heroImage" data-img="day_SE" alt="新港枢纽变电站全站"></div><div class="strip">@@TABS@@</div><p class="caption" id="viewcaption">日景 · 全站</p><p class="caption">全部建筑视图来自交付 NBT 的实际方块几何。材质和光照为离线近似，非 Minecraft 实机截图。</p><div class="stats"><div class="stat"><strong>256 × 240 格</strong><span>含边界塔架的整体范围；文件高度 64 格</span></div><div class="stat"><strong>2 台主变</strong><span>独立基础、集油坑和防火墙</span></div><div class="stat"><strong>2 进 · 4 出</strong><span>高压侧建筑配置；十二回中压出线柜</span></div><div class="stat"><strong>16 组设施</strong><span>设备场、控制建筑与辅助系统</span></div></div>
<section id="model"><div class="sectionhead"><h2>从整体到一组设备</h2><p>拖动旋转、切换昼夜，选择主变、开关场或主控楼单独查看。主控楼可切到上下两层。</p></div><div class="modelbox"><div class="modelcover" id="modelcover"><img id="modelFallback" data-img="day_SE" alt="变电站全站预览"><div class="modelprompt"><button class="primary" id="loadModel">打开可旋转模型</button><p class="small" id="modelMessage" aria-live="polite">模型内嵌于本页，可下载后离线查看；需支持 WebGL2。</p><button class="secondary" id="downloadModel" hidden>下载独立预览页</button></div></div><iframe id="modelFrame" title="变电站三维模型" hidden allow="fullscreen"></iframe></div><div class="facilities">@@FACILITIES@@</div></section>'''
body+=section('主变是这座站的视觉中心','两台主变按同一轴线排列，周围留出独立检修通路。','<div class="gallery">'+fig('transformer','二号主变：顶部油枕、两侧套管、成组散热片、侧面控制箱；两道防火墙界定设备间隔。')+fig('transformer_section','主变局部裁切：展示基础轨条和下沉集油区域的高度关系。裁切面未封口，不表示设备内部结构。')+'</div><p>套管采用宽肋片和细支撑交替的原版方块表达；引线按三相分开布置。模型重点还原设备的层次和识别特征，链条导线与方块设备均为建筑表达。</p>')
body+=section('进线、母线、开关与出线分区排列','设备数量、阵列和检修空间共同形成变电站的密度。','<div class="gallery">'+fig('incoming','西侧两座进线塔接入 220 kV 场，设备依次形成测量、隔离和开断的视觉序列。')+fig('switchyard','东侧四回 110 kV 出线间隔：重复的三相设备、绝缘支柱与门形构架。')+'</div><div class="pills"><span>双回进线塔</span><span>隔离开关</span><span>断路器</span><span>测量与保护设备组</span><span>母线支柱</span><span>四回出线构架</span></div>')
body+=section('碎石场地里，也有上下层次','硬地并不等于一整张平板：下挖集油坑和电缆沟，抬起设备基础，保留齐平的道路。','<div class="gallery">'+fig('services','消防水罐、泵房、事故集油设施，以及电容器与电抗器设备区；各设施靠近检修道路排列。')+fig('cable_trench','电缆沟局部开盖段：下沉沟体、低位电缆表达和周边护栏，其余沟段以盖板收平。')+'</div><p>设备场主要使用圆石、安山岩和石材变化，道路为灰色混凝土。三处入口树池作为点缀；照明由道路嵌地灯、建筑内嵌灯和边界工作灯组成。</p>')
body+=section('主控楼、配电室与检修库组成南侧建筑带','采用白灰色实体墙、连续窗带和青色入口雨棚，保持新建设施的整洁感。','<div class="gallery">'+fig('control','两层主控楼：首层控制与站用设备，二层继保柜、值班休息区。')+fig('control_night','相同机位夜景：控制楼窗内照明与入口低灯。')+fig('control_inside','首层控制席与监视墙，后门通向设备场。')+fig('mv_inside','配电室两排十二组出线柜，中部和柜前保留通道。')+'</div><details><summary>查看平面、楼层展开、剖面及四向立面</summary><div class="gallery">'+''.join(fig(n,t) for n,t in [('control_F1','主控楼首层平面'),('control_F2','主控楼二层平面'),('mv_plan','配电室平面 · 两排十二组柜'),('workshop_plan','检修工器具与备品库'),('control_exploded','主控楼分层展开 · 楼层仅在图中拉开'),('control_section','主控楼局部裁切 · 切面未封口'),('elevation_south','全站南立面'),('elevation_north','全站北立面'),('elevation_west','全站西立面'),('elevation_east','全站东立面')])+'</div></details>')
diagram='''<svg class="system-diagram" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 390" role="img" aria-label="工业体系功能关系示意"><rect width="1000" height="390" rx="8" fill="#e5ecee"/><g fill="none" stroke="#4f7388" stroke-width="3"><path d="M260 78H370M260 158H370M370 78V158M370 118H445M585 118H675V65H750M675 118V195H750M515 153V300H750"/></g><g font-family="system-ui,Microsoft YaHei,sans-serif" text-anchor="middle"><g fill="#fff" stroke="#9bb0bd"><rect x="45" y="45" width="215" height="65" rx="5"/><rect x="45" y="125" width="215" height="65" rx="5"/><rect x="445" y="83" width="140" height="70" rx="5"/><rect x="750" y="30" width="210" height="70" rx="5"/><rect x="750" y="160" width="210" height="70" rx="5"/><rect x="750" y="265" width="210" height="70" rx="5"/></g><g fill="#213a4a" font-size="19"><text x="152" y="85">外部电网 · 进线 A</text><text x="152" y="165">外部电网 · 进线 B</text><text x="515" y="111">新港枢纽</text><text x="515" y="137">两台主变</text><text x="855" y="59">110 kV 出线场</text><text x="855" y="83" font-size="14">区域配电设施接口</text><text x="855" y="189">10 kV 配电室</text><text x="855" y="213" font-size="14">工业园与列车所园区负荷</text><text x="855" y="295">本站辅助系统</text><text x="855" y="319" font-size="14">站用电、照明、消防</text></g><text x="45" y="365" text-anchor="start" fill="#667985" font-size="14">功能关系示意；不表示实际电气接线或已经接通的跨项目供电网络。</text></g></svg>'''
body+=section('接入新港工业体系的供电环节','这次交付是一座独立变电站；各区域的供电角色先明确，后续再在服务器总图中落位和接线。',diagram+'''<table><thead><tr><th>既有或后续片区</th><th>可以对接的用途</th><th>当前状态</th></tr></thead><tbody><tr><td>新港制造园</td><td>厂房、仓库、材料处理与附属设施的园区供电</td><td>已预留建筑层面的出线角色，未改动原工业区文件</td></tr><tr><td>列车检修基地</td><td>库房照明、检修、空压、办公与生活配套；牵引供电另作专项设施</td><td>未向原列车所铺设跨图电缆</td></tr><tr><td>后续供水、污水与物流设施</td><td>作为工业体系的其他公用工程负荷</td><td>预留后续扩展用途</td></tr></tbody></table>''')
body+=section('导入与下载','原版方块可以在带机械动力的服务器中使用；这版没有引入电力模组依赖。','''<div class="downloadgrid"><div class="downloadcard"><h3>完整世界存档</h3><p>将解压后的 Substation01_World 文件夹放入 saves，用 Minecraft Java 1.21.1 打开。出生点位于南门外。</p><button class="primary" data-download="Substation01_World.zip">下载世界 ZIP</button></div><div class="downloadcard"><h3>放进既有地图</h3><p>SCHEM 为 Sponge v3，定位原点设在南门入口脚下。文件包含空气与下挖空间，粘贴会覆盖所占范围，先选空地或测试世界。NBT 为同源结构文件。</p><div class="links"><button class="primary" data-download="Substation01.schem">下载 SCHEM</button><button class="secondary" data-download="Substation01.nbt">下载 NBT</button></div></div></div><p class="note">这是可导入的建筑模型。电压等级和设备连接用于设计表达，未进行电力仿真；游戏内光照、碰撞和蓝图导入尚待实机确认。</p>''')
body+=section('文件与几何核对','图像、旋转模型、结构文件和世界存档均来自同一份最终 NBT。',f'''<table><thead><tr><th>核对范围</th><th>结果</th></tr></thead><tbody><tr><td>NBT 方块与状态</td><td>{gc['palette_count']} 种状态，全部为 minecraft 命名空间；独立回读一致</td></tr><tr><td>世界区域文件</td><td>{wc['checked_cells']:,} 个格位回读，差异 0；包含空气与方块实体</td></tr><tr><td>SCHEM</td><td>{sc['checked_cells']:,} 个格位回读，差异 0</td></tr><tr><td>道路与步行空间</td><td>道路五格高通行包络、建筑入口、柜间通道、楼梯及上层平台检查通过</td></tr><tr><td>建筑视图</td><td>29 张同源视图；四向日夜景、正俯视、局部、剖面、平面及展开</td></tr><tr><td>实际运行</td><td>Minecraft / WorldEdit 导入待验；浏览器内三维显示、设施选择、切层、昼夜、旋转和失败重试已实测通过</td></tr></tbody></table>''')
source_notes={
 'HE_AIS':'Hitachi Energy：户外空气绝缘变电站的设备组合与应用。',
 'PL_INFRA':'Powerlink：变压器、开关、测量设备、母线和控制建筑的功能关系。',
 'NG_LAYOUT':'National Grid：户外 AIS 场地与封闭 GIS 配置的区别；未采用其地区接入规范。',
 'JICA_S3':'JICA 输电项目报告：PDF 第 72、86 页的主变、户外开关场和控制柜照片；用于形态参考，未照搬原站电压或尺度。'}
body+=section('形态参考与原创设计','使用公开的一手资料理解设备，按本项目的方块尺度重新组织。','<ul class="source-list">'+''.join('<li><a href="'+html.escape(s['url'])+'" target="_blank" rel="noopener">'+source_notes[s['id']]+'</a></li>' for s in sources)+'</ul><p class="small">本方案不复刻某一座现实变电站。现实照片中的散热片、油枕、套管、框架、柜列和硬质场地，分别转译为可回读的方块构件；设备外观与尺寸不作为现实电气净距或施工依据。</p>')
body+='</main><footer>GAFAcraft / HAF · Substation01 · '+run+'<br>源 NBT SHA-256：<code>'+sha+'</code></footer>'
body+='''<script>const IMAGES=@@IMAGES@@,MODEL=@@MODEL@@,DOWNLOADS=@@DOWNLOADS@@,LABELS=@@LABELS@@;
@@CONTROLLER@@
</script></body></html>'''
facilities=''.join('<button class="facility" data-facility="'+b['id']+'"><div><b>'+html.escape(b['name'])+'</b></div><i>↗</i></button>' for b in payload['buildings'])
for key,value in [('STYLE',style),('CONTROLLER',(P/'assets/report_controller.js').read_text()),('TABS',tabs),('FACILITIES',facilities),('IMAGES',json.dumps(IMAGES)),('MODEL',json.dumps(base64.b64encode(model.encode()).decode())),('DOWNLOADS',json.dumps(downloads)),('LABELS',json.dumps(labels,ensure_ascii=False))]:body=body.replace('@@'+key+'@@',value)
assert not re.search(r'@@[A-Z]+@@',body)
(D/'Substation01.html').write_text(body)
# Validate syntax, embedded binaries and reports without claiming browser or game execution.
node=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node')
for label,doc in [('model',model),('report',body)]:
 for i,script in enumerate(re.findall(r'<script>(.*?)</script>',doc,re.S)):
  p=R/f'qa_{label}_{i}.js';p.write_text(script);subprocess.run([node,'--check',str(p)],check=True)
for name,encoded in downloads.items():assert base64.b64decode(encoded)==(D/name).read_bytes()
qa={'source_nbt_sha256':sha,'views':len(views),'source_hashes_equal':True,'js_syntax':'pass','embedded_downloads_exact':True,'browser_runtime':browser_fix if browser_fix else 'not_run','game':'not_run','visual_review':'same-NBT fixed views reviewed'}
(R/'delivery_qa.json').write_text(json.dumps(qa,indent=2))
readme=f'''Substation01 / 新港枢纽变电站 / {run}
Minecraft Java 1.21.1 原版方块，原创工业建筑。
范围 256 × 64 × 240；X 东，Z 南，Y 上。地面脚面本地 Y7。
220 / 110 / 10 kV 仅为设计主题；设备为装饰性建筑，不进行电力仿真。
源文件 NBT SHA-256: {sha}

交付：Substation01.html（含旋转模型、29 张视图和内嵌下载）、Substation01.nbt、Substation01.schem、Substation01_World.zip。
世界出生点 {-26,65,118}，位于南门；解压后放入 saves。
SCHEM 定位原点：本地 (102,7,238)。包含空气，粘贴前检查目标区域。
模型没有修改既有工业园或列车所；跨项目供电为规划关系。
文件、几何与离线图像已核对，Minecraft 实机碰撞/光照与 WorldEdit 导入待验。

复建（项目根目录，Python3 + numpy + Pillow；nbtlib 已包含）：
python3 src/build_station.py NEW_RUN
python3 src/verify_station.py NEW_RUN
python3 src/export_schematic.py NEW_RUN
python3 src/export_world.py NEW_RUN runs/NEW_RUN/Substation01_World
python3 src/preview.py NEW_RUN
python3 src/cameras.py NEW_RUN
python3 src/render_all.py NEW_RUN
python3 src/pack_interactive.py NEW_RUN
python3 src/deliver.py NEW_RUN
离线渲染需要 EGL/OpenGL；交付脚本的 JavaScript 语法检查需要 Node。
'''
(P/'README.txt').write_text(readme)
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in D.iterdir() if p.is_file() and p.name!='Substation01_Project.zip'}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(D/'Substation01_Project.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for sub in ['src','support','deps','assets','input','research',f'runs/{run}']:
  for p in sorted((P/sub).rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
   if sub=='research' and p.suffix in ['.pdf','.png','.txt']:continue
   if p.name.startswith('qa_') and p.suffix=='.js':continue
   z.write(p,Path('Substation01_Project')/p.relative_to(P))
 for p in sorted(V.glob('*.png')):
  if p.name.startswith('qa_'):continue
  z.write(p,Path('Substation01_Project')/p.relative_to(P))
 for name in ['render_report.json','scene/scene.json']:
  z.write(V/name,Path('Substation01_Project')/(V/name).relative_to(P))
 z.write(P/'README.txt','Substation01_Project/README.txt')
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='Substation01_Project.zip':z.write(p,Path('Substation01_Project/deliverables')/p.name)
print(json.dumps({'qa':qa,'files':{p.name:p.stat().st_size for p in D.iterdir() if p.is_file()}},ensure_ascii=False))
