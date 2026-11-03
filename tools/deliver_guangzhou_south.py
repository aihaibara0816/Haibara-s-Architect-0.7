"""Self-contained review report, user feedback form, and reproducible case archives."""
from pathlib import Path
import base64,csv,hashlib,html,io,json,math,shutil,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];CASE=ROOT/'cases/guangzhou_south';RUN=CASE/'runs/V1_r02';PRE=CASE/'review/previews/V1_r02';OUT=ROOT.parent/'deliverables';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(p):return base64.b64encode(p.read_bytes()).decode()
def jpeg(p):
 im=Image.open(p).convert('RGB');im.thumbnail((2400,2400));b=io.BytesIO();im.save(b,format='JPEG',quality=89,optimize=True);return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
M=read(RUN/'manifest.json');V=read(RUN/'validation.json');I=read(RUN/'import_pack/import_manifest.json');RE=read(PRE/'render_report.json');E=read(CASE/'research/component_evidence.json');IM=read(CASE/'research/image_manifest.json');S=read(CASE/'research/sources.json')
labels={'overview':'全景 · 日间','night':'全景 · 夜间','top':'正投影俯视','south_roof':'轨道侧屋盖轮廓','west_entrance':'西入口 · 三层落客','east_entrance':'东入口 · 二层落客','entrance_night':'入口夜景','roof_detail':'采光带与金属屋面','platform':'站台与支撑近景','platform_night':'站台夜景','hall':'候车大厅','hall_night':'候车大厅夜景','soffit':'桁架与吊顶仰视','arrivals':'地面到达大厅','section':'剖切 · 内部层次','platform_plan':'站台层剖切俯视','waiting_plan':'候车层剖切俯视','plaza':'广场与入口近景'}
for q,cn in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]:
 for mode,c in [('day','日间'),('night','夜间')]:labels[q+'_'+mode]=cn+'45° · '+c
assert len(RE)==26 and {q['camera']['id'] for q in RE}==set(labels)
for q in RE:
 p=PRE/q['image'];assert sha(p)==q['sha256'] and q['source_nbt_sha256']==M['sha256'];Image.open(p).verify()
assert V['failed']==0 and I['module_union_exact'] and I['schematic']['nonair_readback_exact']
assert 'Ran 29 tests' in (CASE/'validation/shared_tests_final.txt').read_text()
baseline=read(CASE/'history/dependency_baseline.json');changed=[{'file':f,'before':h,'after':sha(ROOT/f)} for f,h in baseline.items() if sha(ROOT/f)!=h]
dump(CASE/'validation/dependency_changes.json',{'unchanged_count':len(baseline)-len(changed),'changed':changed,'added_tests':['tests/test_mesh_write.py'],'reason':'Fix large preview cache partial writes and reject incomplete mesh buffers; no building geometry/state/lighting engine rewrite'})
dump(CASE/'history/render_recovery.json',{'run':'V1_r02','failure':'opaque cache 167772160 bytes, expected 870749280 bytes; renderer rejected triangle reshape','fix':'bounded atomic writes, fsync, exact size check; renderer validates declared triangle byte count','NBT_unchanged':True,'source_nbt_sha256':M['sha256'],'regressions':'short writes complete; failed write preserves previous cache; 29 shared tests pass'})
import_readme='''广州南站 V1 / HAF 0.2 / V1_r02

优先使用 Guangzhou_South_HAF02_V1.schem（Sponge v3，DataVersion3955）。
尺寸 X640 × Y64 × Z660，1,339,157个非空气方块；约1格/米研究尺度。

在备份后的空白测试场地导入；本场景很大，建议先测试小模块。
schem包含明确空气，会清除包络中的原有方块；不要在现有建筑上试贴。
完整NBT不含明确空气，不能负责清除场地旧方块。模块同样不含空气。
主NBT/模块给能读结构NBT的工具使用，不保证原版结构方块能加载大尺寸模块。
兼容 Sponge v3 的 WorldEdit 等工具可读schem；本次未进行客户端/服务端实测。

分块大小≤256KiB只代表压缩文件字节数，不能等同Create尺寸/范围兼容认证。
modules目录的每个文件按 module_offsets.csv 的 x,y,z 偏移相对同一原点导入；不旋转。
完整schem与所有模块的坐标和方块状态离线回读完全相同。

轨道由铁链等组成，列车为静态景观，非可运行铁路；Create轨道、列车组装和信号不包含。
Minecraft原版荧石和海晶灯都是光源，冷暖色预览不能保证无光影时的实际光色。
游戏内光更新、透明材质、门洞/楼梯碰撞、落客坡道需要实测。

materials.csv为材料计数，blockstates.csv包含半砖/楼梯/玻璃片/铁栏杆等方向状态。
本目录的图像与模型来自最终NBT，非游戏截图。
'''
(RUN/'import_pack/README.txt').write_text(import_readme)
shutil.copy2(CASE/'feedback.json',RUN/'import_pack/feedback.json');shutil.copy2(RUN/'validation.json',RUN/'import_pack/validation.json')
views={id:jpeg(PRE/(id+'.png')) for id in labels};refs=[{**q,'src':'data:image/jpeg;base64,'+data(CASE/'research'/q['local_file'])} for q in IM]
schem=RUN/'import_pack'/I['schematic']['file'];materials=(RUN/'materials.csv').read_text();matrows=list(csv.DictReader(io.StringIO(materials)))
payload={'views':views,'labels':labels,'refs':refs,'sources':S,'evidence':E['components'],'checks':V['checks'],'materials':matrows,'schem':data(schem),'schemName':schem.name,'materialsCSV':materials,'hash':M['sha256'],'feedback':read(CASE/'feedback.json')}
html_text='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州南站 V1 · HAF 0.2</title>
<style>:root{color-scheme:dark;--bg:#0e1921;--panel:#172732;--ink:#edf3f4;--muted:#adc0ca;--gold:#e6c184}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}header,main,footer{max-width:1440px;margin:auto;padding:32px}header{padding-top:52px}.eyebrow{letter-spacing:.18em;color:var(--gold);font-size:13px}h1{font-size:clamp(32px,5vw,64px);line-height:1.15;margin:12px 0}h2{font-size:28px;margin:0 0 12px}h3{font-size:18px;margin:0}p{color:var(--muted)}.lead{max-width:900px;font-size:19px}nav{display:flex;gap:10px;flex-wrap:wrap;margin:26px 0}a{color:var(--gold)}nav a,button,.pill{border:1px solid #425967;border-radius:8px;background:var(--panel);color:var(--ink);padding:10px 15px;text-decoration:none;font:inherit}button{cursor:pointer}button:hover,button[aria-pressed=true]{border-color:var(--gold);background:#30434a}.stats,.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat,.card{background:var(--panel);border:1px solid #2b414f;border-radius:12px;padding:20px}.stat strong{display:block;font-size:26px}.stat span{color:var(--muted)}section{margin:0 0 56px}.frame{border:1px solid #344b59;border-radius:12px;overflow:hidden;background:#cfdcde}.frame img{width:100%;display:block;cursor:zoom-in}.controls{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card img{width:100%;display:block;border-radius:6px;cursor:zoom-in}.caption{font-size:14px;color:var(--muted);margin:10px 0 0}.tag{color:var(--gold);font-size:12px}.wide{grid-column:1/-1}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid #344b59;text-align:left;padding:10px;vertical-align:top}th{color:var(--gold)}.scroll{overflow:auto}details{background:var(--panel);padding:18px;border-radius:10px;margin:12px 0}summary{cursor:pointer;font-size:18px}textarea,select{width:100%;background:#0d1c25;color:var(--ink);border:1px solid #425967;border-radius:6px;padding:12px;font:inherit}textarea{min-height:140px}small{color:var(--muted)}dialog{border:0;background:#081116;color:white;max-width:98vw;max-height:98vh;padding:16px}dialog::backdrop{background:#000d}dialog img{max-width:92vw;max-height:83vh;object-fit:contain;display:block}dialog .close{float:right}.muted{color:var(--muted)}.ok{color:#93dcad}.note{border-left:3px solid var(--gold);padding:12px 20px;background:#1e3039}.thumbgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}code{word-break:break-all}footer{border-top:1px solid #344b59;font-size:13px;color:var(--muted)}@media(max-width:800px){header,main,footer{padding:22px}.stats{grid-template-columns:repeat(2,1fr)}.two,.thumbgrid{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}h2{font-size:24px}}@media print{body{background:white;color:black}p,.caption,small{color:#333}button,nav,#feedback{display:none}.card,.stat,details{background:white}section{break-inside:avoid}}</style>
<header><div class="eyebrow">HAIBARA’S ARCHITECT · HAF 0.2 / CLOSING CASE</div><h1>广州南站 <span style="color:var(--gold)">V1</span></h1><p class="lead">六跨曲面屋盖 · 中央采光带 · 高架站台与候车大厅。把大跨度交通建筑作为 0.2 的收尾练习，先看形体，再看屋面、结构、吊顶和灯光如何组合。</p><nav><a href="#preview">全景与四向</a><a href="#details">内部与细节</a><a href="#research">图像证据</a><a href="#delivery">模型与材料</a><a href="#feedback">记录反馈</a></nav><div class="stats"><div class="stat"><strong>27</strong><span>资料图 / 其中22张逐图复核</span></div><div class="stat"><strong>640×64×660</strong><span>X / Y / Z 场景尺寸，格</span></div><div class="stat"><strong>133.9 万</strong><span>非空气方块 / 29种材料</span></div><div class="stat"><strong>V1_r02</strong><span>当前交付 · 用户验收待定</span></div></div></header>
<main><section id="preview"><h2>先看整体</h2><p>所有模型图均从交付 NBT 回读生成。点击放大；四个45°视角保持相同尺度。方位标签为模型坐标，尚未完成测绘坐标配准。</p><div class="controls" id="views"></div><div class="frame"><img id="mainView" alt="广州南站模型全景"></div><p id="viewCaption" class="caption"></p><div class="note">薄壳屋盖下方保留空气层；中央采光带连接两端入口。列车和轨道是静态景观，周边只做有限范围广场与落客道路。</div></section>
<section id="details"><h2>从屋面走到站台</h2><p>屋盖、幕墙、支撑、吊顶和灯具分别构建；候车层在站台之上，地面保留到达大厅。西侧落客平台高于东侧。</p><div class="two" id="detailGallery"></div></section>
<section id="research"><h2>本轮研究依据</h2><p>使用建筑师、结构工程方、公开设计图、铁路运营资料，以及白天/夜间与屋面维护照片。没有六张图片限制，也没有以设计效果图冒充竣工实景。</p><div class="two" id="compare"></div><details><summary>27张资料图及来源 · 点开逐张检查</summary><p>斜航拍不等于正射俯视；设计图不等于竣工测绘。R05/06/07/09/10仅通过接触表复核，未单独决定几何。</p><div id="referenceGallery" class="thumbgrid"></div></details><details><summary>构件 → 证据 → 参数对应</summary><div class="scroll"><table><thead><tr><th>构件</th><th>依据与处理</th><th>未闭合问题</th></tr></thead><tbody id="evidenceTable"></tbody></table></div></details><details><summary>资料来源与尺寸口径</summary><div id="sources"></div></details></section>
<section><h2>这版保留了什么，哪里还不够</h2><div class="two"><div class="card"><h3>已实现</h3><p>六跨不等宽屋盖、前后错落的雨棚端头、两端加宽的斜格采光带；玻璃片幕墙与铁栏杆分隔；Y/V形支撑和条状吊顶；站台、候车座位、服务台与道路/广场。</p><p>公共大厅和站台按规律布灯，商业小单元以固定种子控制少量暖光。门洞已同时切开玻璃与外竖杆。</p></div><div class="card"><h3>下一步重点看</h3><p>屋盖曲率和端头还不是精测结果；中央采光带的348m文字尺寸，与本模型含入口端头的442格包络尚未严格对齐。广场、道路曲线、柱位与内部设施数量有估算。</p><p>图中材质为方块几何近似，没有原版纹理；ETFE斜格在1格尺度下偏粗。夜景中央地面与入口比参考照片偏暗，后续要复核灯位高度和间距。游戏中的碰撞、楼梯可走性、光照更新与实际观感仍待导入测试。</p></div></div></section>
<section id="delivery"><h2>模型、材料与验证</h2><p>报告可离线打开，图片全部内嵌；下方可直接取出同一份 schem 和材料表。</p><div class="controls"><button id="getSchem">下载 .schem</button><button id="getMaterials">下载材料 CSV</button><button id="getFeedbackTemplate">下载反馈模板</button></div><p class="note">Sponge v3 / Java DataVersion 3955。schem包含明确空气，导入会清除包络内旧方块；先在空白测试场地试贴。分块NBT的≤256KiB限制仅是文件大小，不代表已通过Create或结构方块兼容测试。</p><div class="stats"><div class="stat"><strong>17 / 17</strong><span>本案例结构/状态检查</span></div><div class="stat"><strong>29 / 29</strong><span>共享代码回归检查</span></div><div class="stat"><strong>一致</strong><span>NBT / schem / 分块坐标状态回读</span></div><div class="stat"><strong>待实测</strong><span>Minecraft游戏导入</span></div></div><details><summary>材料清单</summary><div class="scroll"><table id="materials"></table></div></details><details><summary>检查记录与交付追踪</summary><p>r01发现东西中心入口被幕墙竖杆阻挡；r02修复。预览缓存曾写入不完整，已增加原子写入及字节数检查并重新生成；模型NBT没有因此改变。</p><div class="scroll"><table><thead><tr><th>检查</th><th>结果</th></tr></thead><tbody id="checks"></tbody></table></div><p>交付NBT SHA256：<code id="hash"></code></p><small>结构抽样检查不等于真实建筑还原评分；这些结果不构成游戏内验证。</small></details></section>
<section id="feedback"><h2>留一个能回顾的修改入口</h2><p>选择构件，记录“哪里不对、看的是哪个视角、希望怎样调整”。保存后仍留在此浏览器，也可以导出JSON随下一轮反馈一起发来。原始r01/r02均保留，后续另建run。</p><label>构件<select id="component"><option>roof.bay* 屋盖形体</option><option>roof.spine 中央采光带</option><option>roof.*.truss* 桁架支撑</option><option>facade 幕墙入口</option><option>interior 候车/到达/站台</option><option>lighting 灯光</option><option>entrance 落客道路</option><option>site 广场</option></select></label><p><textarea id="comment" placeholder="例如：南侧视角的雨棚端头需要更薄；请对照N01……"></textarea></p><div class="controls"><button id="saveNote">加入反馈</button><button id="exportNotes">导出我的反馈</button></div><div id="notes"></div><small id="noteStatus">反馈只保存在本地，不会自动发送。</small></section></main>
<footer>广州南站 V1 · HAF0.2 · 2026-10-24。人工证据研究 + 案例参数化生成；无SU输入、无自动模型融合、无神经网络训练。此例作为0.2收尾，尚未发布HAF0.3。图片来源与权利见资料卡；N03 © Shujianyang，CC BY-SA4.0，原图未修改。</footer>
<dialog id="zoom"><button class="close">关闭</button><p id="zoomLabel"></p><img id="zoomImage" alt="放大预览"></dialog>
<script id="data" type="application/json">__PAYLOAD__</script><script>
'use strict';const D=JSON.parse(document.getElementById('data').textContent);const $=id=>document.getElementById(id);const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function zoom(src,title){$('zoomImage').src=src;$('zoomLabel').textContent=title;$('zoom').showModal()}$('zoom').querySelector('button').onclick=()=>$('zoom').close();
function bindImages(root){root.querySelectorAll('img').forEach(im=>im.onclick=()=>zoom(im.src,im.alt))}
function card(src,title,desc){return `<div class="card"><img loading="lazy" src="${src}" alt="${esc(title)}"><h3>${esc(title)}</h3><p class="caption">${desc||''}</p></div>`}
const overviewIDs=['overview','night','top','se_day','sw_day','ne_day','nw_day','se_night','sw_night','ne_night','nw_night'];function choose(id){$('mainView').src=D.views[id];$('mainView').alt=D.labels[id];$('viewCaption').textContent=D.labels[id]+' · 最终NBT回读预览，非游戏截图';$('views').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===id)))}
overviewIDs.forEach(id=>{const b=document.createElement('button');b.textContent=D.labels[id];b.dataset.view=id;b.onclick=()=>choose(id);$('views').append(b)});choose('overview');$('mainView').onclick=()=>zoom($('mainView').src,$('mainView').alt);
const detailIDs=['south_roof','roof_detail','west_entrance','east_entrance','entrance_night','platform','platform_night','hall','hall_night','soffit','arrivals','section','platform_plan','waiting_plan','plaza'];$('detailGallery').innerHTML=detailIDs.map(id=>card(D.views[id],D.labels[id],id.includes('plan')||id==='section'?'剖切显示，便于检查内部层次；交付模型本身未切除。':'')).join('');bindImages($('detailGallery'));
$('compare').innerHTML=['A01','N01','F03','N03'].map(id=>{const r=D.refs.find(q=>q.image_id===id);return card(r.src,id+' · '+r.observation,`<a href="${esc(r.source_page)}" target="_blank" rel="noopener">原始来源</a>`)}).join('');bindImages($('compare'));
$('referenceGallery').innerHTML=D.refs.map(r=>card(r.src,r.image_id+' · '+r.role,`${esc(r.observation)}<br><a href="${esc(r.source_page)}" target="_blank" rel="noopener">来源</a> · ${esc(r.license)}${r.author?' · '+esc(r.author):''}${r.license_url?` · <a href="${esc(r.license_url)}">许可</a>`:''}`)).join('');bindImages($('referenceGallery'));
$('evidenceTable').innerHTML=D.evidence.map(e=>`<tr><td><code>${esc(e.component_id)}</code></td><td>${esc(e.evidence_ids.join(', '))}<br>${esc(e.decision)}<br><small>${esc(e.parameter_paths.join(', '))}</small></td><td>${esc(e.limits)}</td></tr>`).join('');$('sources').innerHTML=D.sources.map(s=>`<p><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a><br>${esc(s.adopt)}${s.caution?'<br><small>'+esc(s.caution)+'</small>':''}</p>`).join('');
$('checks').innerHTML=D.checks.map(c=>`<tr><td>${esc(c.id)}</td><td class="ok">${esc(c.status)}</td></tr>`).join('');$('hash').textContent=D.hash;const keys=Object.keys(D.materials[0]);$('materials').innerHTML='<thead><tr>'+keys.map(k=>'<th>'+esc(k)+'</th>').join('')+'</tr></thead><tbody>'+D.materials.map(r=>'<tr>'+keys.map(k=>'<td>'+esc(r[k])+'</td>').join('')+'</tr>').join('')+'</tbody>';
function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000)}$('getSchem').onclick=()=>{const raw=atob(D.schem),b=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)b[i]=raw.charCodeAt(i);download(new Blob([b],{type:'application/octet-stream'}),D.schemName)};$('getMaterials').onclick=()=>download(new Blob(['\ufeff'+D.materialsCSV],{type:'text/csv;charset=utf-8'}),'materials.csv');$('getFeedbackTemplate').onclick=()=>download(new Blob([JSON.stringify(D.feedback,null,2)],{type:'application/json'}),'feedback_template.json');
const storeKey='haf-guangzhou-south-'+D.hash;let notes=[];try{notes=JSON.parse(localStorage.getItem(storeKey)||'[]');if(!Array.isArray(notes))notes=[]}catch(e){}function showNotes(){$('notes').innerHTML=notes.map(n=>`<div class="card"><strong>${esc(n.component)}</strong><p>${esc(n.comment)}</p><small>${esc(n.created)}</small></div>`).join('')}showNotes();$('saveNote').onclick=()=>{const text=$('comment').value.trim();if(!text){$('noteStatus').textContent='先填写观察。';return}notes.push({component:$('component').value,comment:text,created:new Date().toISOString()});try{localStorage.setItem(storeKey,JSON.stringify(notes));$('noteStatus').textContent='已保存至此浏览器，可继续记录或导出。'}catch(e){$('noteStatus').textContent='浏览器未允许本地保存，请直接导出反馈。'}$('comment').value='';showNotes()};$('exportNotes').onclick=()=>download(new Blob([JSON.stringify({case:'guangzhou_south',run:'V1_r02',source_nbt_sha256:D.hash,feedback:notes},null,2)],{type:'application/json'}),'guangzhou_south_feedback.json');
</script></html>'''
text=html_text.replace('__PAYLOAD__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
(OUT/'index.html').write_text(text)
for name in ['overview','top','night']:shutil.copy2(PRE/(name+'.png'),OUT/(name+'.png'))
fontpath=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');font=ImageFont.truetype(str(fontpath),28)
def board(ids,name):
 tilew,tileh=1200,800;canvas=Image.new('RGB',(tilew*2,(tileh+52)*math.ceil(len(ids)/2)),(14,25,33));draw=ImageDraw.Draw(canvas)
 for n,id in enumerate(ids):
  im=Image.open(PRE/(id+'.png')).convert('RGB');im.thumbnail((tilew,tileh));x=(n%2)*tilew;y=(n//2)*(tileh+52);canvas.paste(im,(x+(tilew-im.width)//2,y));draw.text((x+20,y+tileh+8),id.upper().replace('_',' '),font=font,fill=(230,193,132))
 canvas.save(OUT/name,optimize=True)
board(['se_day','sw_day','ne_day','nw_day'],'four_views.jpg');board(['hall','soffit','platform','hall_night'],'details.jpg')
buildzip=OUT/'South_Build.zip'
with zipfile.ZipFile(buildzip,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted((RUN/'import_pack').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(RUN/'import_pack'))
sourcezip=OUT/'South_Source.zip';members=[]
with zipfile.ZipFile(sourcezip,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file() or any(q in p.parts for q in ['__pycache__','.git','scene']):continue
  if p.suffix in ['.pyc','.tmp']:continue
  name=str(p.relative_to(ROOT));z.write(p,'HAF_Guangzhou_South/'+name);members.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
 z.writestr('HAF_Guangzhou_South/SOURCE_MANIFEST.json',json.dumps(members,indent=2))
for p in [buildzip,sourcezip]:
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
dump(OUT/'delivery_manifest.json',{'case':'guangzhou_south','run':'V1_r02','source_nbt_sha256':M['sha256'],'preview_count':len(RE),'case_checks':V['passed'],'shared_tests':29,'module_count':I['module_count'],'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='delivery_manifest.json']})
print(json.dumps({'output':str(OUT),'html_bytes':(OUT/'index.html').stat().st_size,'source_bytes':sourcezip.stat().st_size,'build_bytes':buildzip.stat().st_size,'modules':I['module_count']},ensure_ascii=False))
