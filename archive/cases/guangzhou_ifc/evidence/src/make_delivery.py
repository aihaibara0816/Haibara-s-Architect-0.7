"""Self-contained IFC review HTML and compact import archive. No web runtime."""
from pathlib import Path
import json,base64,io,zipfile,csv,html,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
RUN='V1_r02';run=CASE/'runs'/RUN;pre=CASE/'review/previews'/RUN;out=CASE/'delivery';out.mkdir(exist_ok=True)

def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def data(p,mime):return 'data:'+mime+';base64,'+base64.b64encode(Path(p).read_bytes()).decode()
def webp(p,maxside=None):
    im=Image.open(p).convert('RGB')
    if maxside:im.thumbnail((maxside,maxside))
    b=io.BytesIO();im.save(b,format='WEBP',quality=92,method=5);return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()

labels={'overview':'全景 · 日景','night':'全景 · 夜景','front':'正面正投影','se_day':'东南45° · 日景','sw_day':'西南45° · 日景','ne_day':'东北45° · 日景','nw_day':'西北45° · 日景','se_night':'东南45° · 夜景','sw_night':'西南45° · 夜景','ne_night':'东北45° · 夜景','nw_night':'西北45° · 夜景','top_day':'真俯视 · 完整建筑','crown':'塔顶 · 日景','crown_night':'塔顶 · 夜景','facade':'玻璃与斜撑 · 日景','facade_night':'玻璃与斜撑 · 夜景','entrance':'酒店入口 · 日景','entrance_night':'酒店入口 · 夜景','hotel_section':'酒店中庭 · 剖切','hotel_plan':'酒店层 · 水平剖切','office_plan':'办公层 · 水平剖切','base_plan':'基座 · 水平剖切'}
views={k:webp(pre/(k+'.png')) for k in labels}
materials=list(csv.DictReader((run/'materials.csv').read_text(encoding='utf-8-sig').splitlines()))
zh={'polished_deepslate_slab':'磨制深板岩台阶','gray_stained_glass':'灰色染色玻璃','gray_stained_glass_pane':'灰色染色玻璃板','smooth_quartz_slab':'平滑石英台阶','gray_concrete':'灰色混凝土','light_gray_concrete':'淡灰色混凝土','stone_bricks':'石砖','smooth_stone':'平滑石','smooth_stone_slab':'平滑石台阶','diorite_wall':'闪长岩墙','smooth_quartz':'平滑石英块','glass_pane':'玻璃板','polished_andesite':'磨制安山岩','oak_leaves':'橡树树叶','glowstone':'荧石','sea_lantern':'海晶灯','glass':'玻璃','dark_oak_slab':'深色橡木台阶','iron_bars':'铁栏杆','moss_block':'苔藓块','bookshelf':'书架','white_concrete':'白色混凝土','polished_andesite_slab':'磨制安山岩台阶','iron_trapdoor':'铁活板门','anvil':'铁砧','oak_log':'橡木原木','quartz_slab':'石英台阶','redstone_torch':'红石火把','dark_oak_planks':'深色橡木木板'}
with (out/'materials.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['材料','block_id','数量','整组64','余数'])
    for r in sorted(materials,key=lambda r:-int(r['count'])):w.writerow([zh.get(r['block_id'].split(':')[1],r['block_id']),r['block_id'],r['count'],r['stacks'],r['remainder']])

readme='''广州西塔IFC V1 / HAF 0.3 / 2026-10-24
最终运行：V1_r02。主塔约220格；全包围尺寸 X92 × Y224 × Z100。
整栋优先：Guangzhou_IFC_HAF03_V1.schem（Sponge v3，含空气）。
整栋NBT和两个NBT分块也已提供。parta偏移(0,0,0)，partb偏移(0,112,0)。不要旋转或翻转；以同一原点相加。
模块不是原版结构方块尺寸保证；需支持这些尺寸及NBT/Sponge v3的导入工具。NBT稀疏，不会清除既有方块；schem包含空气。
材料统计见materials.csv；方块状态见blockstates.csv。
DataVersion=3955。已离线读回并核对整栋与分块，未进行Minecraft游戏内导入、碰撞、纹理及光照测试。
地面、裙楼仅紧邻塔身的估算范围；不包括地下及公寓配楼。内部是示意楼层/窗后陈设，不是真实房间全还原。
预览是最终NBT近似离线渲染，不是游戏截图。方向为模型坐标（+X东，-Z北），非已测地理方位。
'''
(out/'README.txt').write_text(readme)
with zipfile.ZipFile(out/'IFC_V1_Build.zip','w',zipfile.ZIP_DEFLATED,9) as z:
    for p in sorted((run/'import_pack').rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(run/'import_pack')))
    z.write(out/'materials.csv','materials_zh.csv');z.write(out/'README.txt','README.txt')
    z.write(run/'validation.json','validation.json');z.write(CASE/'feedback_template.json','feedback_template.json')

fontpaths=list(ROOT.glob('**/*NotoSansCJK*'))+list(ROOT.glob('**/*SourceHanSans*'))
def font(size):
    for p in fontpaths:
        try:return ImageFont.truetype(str(p),size)
        except OSError:pass
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
hero=Image.new('RGB',(1400,1450),'#102431');d=ImageDraw.Draw(hero)
d.text((54,30),'GUANGZHOU IFC',font=font(37),fill='#eff3ef');d.text((54,83),'HAF 0.3  /  V1   ·   DAY & NIGHT',font=font(20),fill='#d1b47b')
for i,k in enumerate(['se_day','se_night']):
    im=Image.open(pre/(k+'.png')).convert('RGB');im.thumbnail((668,1230));hero.paste(im,(24+i*690+(668-im.width)//2,135))
d.text((40,1390),'220 BLOCKS  ·  NBT-DERIVED PREVIEW  ·  GAME TEST PENDING',font=font(19),fill='#b8c8cd');hero.save(out/'IFC_V1_Preview.png')

table=''.join(f'<tr><td>{zh.get(r["block_id"].split(":")[1],r["block_id"])}</td><td>{int(r["count"]):,}</td><td>{r["stacks"]}组 + {r["remainder"]}</td></tr>' for r in sorted(materials,key=lambda r:-int(r['count'])))
manifest=json.loads((run/'manifest.json').read_text());validation=json.loads((run/'validation.json').read_text())
sources=json.loads((CASE/'research/sources.json').read_text());source_html=''.join(f'<li><a href="{html.escape(s["url"])}" target="_blank" rel="noopener">{html.escape(s["id"]+" · "+s["type"])}</a></li>' for s in sources)
ref_ids=['WE01','WE09','WE00','WE07','FS01','FS02','WE06']
image_rows=json.loads((CASE/'research/image_manifest.json').read_text())
refs=''.join(f'<figure><img loading="lazy" src="{webp(CASE/"research"/r["path"],1200)}" alt="{html.escape(r.get("alt") or r["id"])}"><figcaption>{r["id"]} · {r.get("publisher","")} · <a href="{html.escape(r.get("source_page",""))}">来源</a></figcaption></figure>' for id in ref_ids for r in image_rows if r['id']==id)
payload={'views':views,'labels':labels,'case':'guangzhou_ifc','run':RUN,'source_nbt_sha256':manifest['sha256']}
doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州西塔 IFC V1 · HAF 0.3</title><style>
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#edf0ee;color:#182d36;font:16px/1.75 system-ui,"Microsoft YaHei",sans-serif}header{padding:42px max(5vw,20px);background:#102431;color:#f4f5ee}header small{letter-spacing:.18em;color:#d8bb82}h1{font-size:clamp(32px,5vw,64px);line-height:1.18;margin:18px 0}header p{max-width:850px;color:#b9cbd0}.pills{display:flex;flex-wrap:wrap;gap:8px}.pills span{border:1px solid #4a6169;padding:5px 13px;border-radius:5px}main{max-width:1400px;margin:auto;padding:24px}section{padding:26px;background:white;border:1px solid #d8e0de;border-radius:12px;margin:22px 0}h2{font-size:24px;margin:0 0 17px}h3{font-size:18px}a{color:#126d7b}nav{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}nav a{font-size:14px;padding:6px 12px;background:#dfe9e7;border-radius:5px;text-decoration:none}button,.btn,select{padding:10px 15px;font:inherit;border:1px solid #b2c5c8;border-radius:6px;background:#f5f8f7;color:#123e4a;cursor:pointer}.btn{display:inline-block;text-decoration:none;margin:4px 8px 4px 0}.primary{background:#126472;color:white;border-color:#126472}.muted,figcaption{font-size:13px;color:#64777c}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.three{grid-template-columns:repeat(3,minmax(0,1fr))}figure{margin:0}figure img{display:block;width:100%;object-fit:contain;background:#edf1ef;cursor:zoom-in}figcaption{padding:8px 2px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;align-items:center}.viewer{position:relative;background:#e0e7e4;text-align:center;overflow:auto}.viewer img{display:block;height:auto;max-width:100%;margin:auto;cursor:crosshair}#mainImage{width:100%;max-height:none}#mainWrap{max-width:1000px;margin:auto}#marker{position:absolute;display:none;border:3px solid #f17152;border-radius:50%;width:34px;height:34px;transform:translate(-50%,-50%);pointer-events:none}details{border-top:1px solid #dce5e3;padding:16px 0}summary{cursor:pointer;font-weight:650}.note{padding:13px 18px;background:#edf5f3;border-left:4px solid #2e7f84}.warn{background:#fbf4e8;border-color:#c89c56}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #dce4e2;padding:9px 12px}th{background:#eaf0ed}textarea,input{width:100%;font:inherit;border:1px solid #b7c7ca;border-radius:6px;padding:10px}textarea{min-height:110px}.form{display:grid;grid-template-columns:1fr 1fr;gap:14px}.full{grid-column:1/-1}dialog{border:0;border-radius:8px;padding:10px;max-width:96vw;max-height:96vh;background:#102431}dialog::backdrop{background:#000b}dialog img{display:block;max-width:90vw;max-height:85vh}dialog button{float:right;margin-bottom:8px}.refs img{height:400px}code{word-break:break-all}footer{font-size:13px;color:#667a7d;padding:20px 0 45px}#saved{color:#166d5c}@media(max-width:750px){main{padding:10px}section{padding:18px}.grid,.three,.form{grid-template-columns:1fr}.full{grid-column:auto}.refs img{height:330px}header{padding:30px 20px}button,select{font-size:14px}}
</style></head><body><header><small>HAIBARA’S ARCHITECT / HAF 0.3 / REAL BUILDING STUDY</small><h1>广州西塔 IFC<br>V1 复原评审</h1><p>圆角三角形、下部鼓腹、玻璃后的斜交网格，以及顶部留空的酒店中庭。此次从现实建筑出发，保留可回顾的参数、来源和两次运行。</p><div class="pills"><span>主塔约220格</span><span>场景92 × 224 × 100</span><span>134,847个非空气方块</span><span>29种材料</span></div></header><main>
<nav><a href="#views">四向日夜</a><a href="#details">俯视与细节</a><a href="#logic">研究与生成</a><a href="#materials">材料</a><a href="#feedback">反馈</a></nav>
<section><h2>先看整体，再扣局部</h2><p>图像由最终NBT回读渲染。塔身保持同一平面方向，沿高度连续收分；两族斜撑位于玻璃后。办公核心在酒店区下方结束，楼板在中庭处留空。</p><div class="grid"><figure><img src="__HERO_DAY__" alt="西塔日景整体"><figcaption>东南45° · 日景</figcaption></figure><figure><img src="__HERO_NIGHT__" alt="同视角西塔夜景"><figcaption>同相机 · 夜景</figcaption></figure></div><p class="muted">离线材质与光照近似，不是Minecraft游戏截图；所有方向均是模型坐标，尚未标定地理北。</p><a class="btn primary" download="IFC_V1_Build.zip" href="__BUILD__">下载建筑包 · schem / NBT / 材料</a><a class="btn" download="IFC_V1.schem" href="__SCHEM__">单独下载 schem</a><a class="btn" download="materials.csv" href="__MATERIALS__">下载材料CSV</a></section>
<section id="views"><h2>同尺度四向查看</h2><div class="toolbar"><select id="viewSelect" aria-label="选择视图"></select><button id="dayToggle">切换日夜</button><button id="zoom">放大当前图</button><a class="btn" id="downloadView">下载当前图</a></div><p class="muted">画面可向下滚动完整查看。点击图中位置可给反馈标点；“放大”打开独立大图。四个45°使用相同相机距离、目标与框幅。</p><div id="mainWrap" class="viewer"><img id="mainImage" alt="当前建筑视图"><span id="marker"></span></div><p id="viewCaption" class="muted"></p></section>
<section id="details"><h2>俯视、幕墙、入口与中庭</h2><p>真俯视保留完整建筑；水平剖切只用于检查不同高度的占用与留空，不把屋顶投影当占地。</p><div id="detailGrid" class="grid"></div></section>
<section id="logic"><h2>这一版采用的逻辑</h2><table><thead><tr><th>构件</th><th>落地方式</th><th>仍需品鉴的地方</th></tr></thead><tbody>
<tr><td>主塔形体</td><td>按建筑师平面人工描线；采用统一1:2尺度和纵向曲率，最宽区中心约72格高。</td><td>最大宽来自图示估算；方块化外包络为37格，顶部29格，非测绘结果。</td></tr>
<tr><td>玻璃 / 斜撑</td><td>灰色玻璃板处理直段，玻璃方块封闭转角；两组反向斜撑与楼板、窗后背景分开。</td><td>斜撑下粗上细有可见材料切换；曲面台阶与实际反射仍受尺度和渲染限制。</td></tr>
<tr><td>日夜灯光</td><td>五组固定横向灯带；荧石与海晶灯；窗灯由稳定房间ID控制，不全楼均匀亮。</td><td>灯带高度为多图估计，照片颜色和日期不一；室内活动率是合理补全。</td></tr>
<tr><td>塔顶 / 酒店</td><td>薄收口、天窗、架高停机坪和静态红色标记；上部中央中庭留空。</td><td>设备位置与停机坪尺寸估算；窗后陈设不是实际房间清单。</td></tr>
<tr><td>入口 / 裙楼 / 场地</td><td>入口净空、柱脚承托、暖色顶棚，连接低层接口与紧凑街边绿化。</td><td>只做紧邻塔身的范围；完整商场、服务公寓与地下未纳入，绿地与铺装仍简化。</td></tr></tbody></table>
<details open><summary>来源、旧资料及本轮边界</summary><p>使用建筑师、四季酒店官方图像和旧研究包，登记22个图像文件，其中两组是相同画面的不同分辨率。没有六图上限；按构件覆盖补图。旧205格方案只复用证据，此次采用近期HAF的1:2尺度。用户旧西塔schem仅作材料表达统计，没有复制体量。本轮没有取得或使用SU模型。</p><p>数据库建筑高度438.6米；建筑师常用440米概述，工程论文为432米。101层与103层属于不同资料口径，未强行统一成游戏可走楼层。</p><ul>__SOURCES__</ul><div class="grid refs">__REFS__</div></details>
<details><summary>第一次预览发现了什么，修了什么</summary><p>r01文件检查通过，但全景画幅裁到顶部，浅色楼板过抢眼，斜撑径向偏移在平缓侧面漏掉部分格位，雨棚灯条露到屋面。r02扩大相机框幅；加深办公楼板与窗后背景；调整斜撑内缩位置；将雨棚灯移到下侧。两份NBT、源码快照和差分记录均保留，形体参数未改。</p></details>
<details><summary>验证结果与导入说明</summary><p>48项既有公共测试、11项本案例检查通过。最终NBT已验证确定性复跑；改变窗灯活动率只改变104个灯位，非灯光格位变化0。声明采样包括70处入口地坪、210处净空、32处柱脚、1410处灯位和305处中庭留空。</p><p>Sponge v3与NBT非空气内容一致；两个NBT模块拼合一致。parta偏移(0,0,0)，partb偏移(0,112,0)。NBT不清除原场景空气区域；schem包含空气。尺寸超过原版结构方块常规范围，需相应导入工具；游戏兼容、碰撞、纹理和可玩性均待测。</p><p>核心316个文件与HAF0.3源码归档一致。新案例文件和登记独立添加；打包器只更新作者版本标签。上述检查不代表整栋还原度已验收。</p><p class="muted">最终NBT SHA256：<code>__SHA__</code></p></details></section>
<section id="materials"><h2>材料清单</h2><p>按最终方块状态合并材料统计，共134,847个非空气方块。台阶数量是放置数量，合成消耗请按游戏配方换算。</p><details><summary>展开全部29种材料</summary><table><thead><tr><th>材料</th><th>放置数量</th><th>64个一组</th></tr></thead><tbody>__TABLE__</tbody></table></details></section>
<section id="feedback"><h2>留一条可以执行的修改意见</h2><p>先选择部位，再指出“哪里不对”和“哪些要保留”。可在上方大图点击标点，避免下一轮改错位置。</p><div class="form"><label>部位<select id="component"><option>tower.profile</option><option>structure.diagrid</option><option>facade.glazing</option><option>crown</option><option>interior.atrium</option><option>lighting</option><option>entry.podium</option><option>site</option></select></label><label>判断<select id="verdict"><option value="needs_revision">需要修改</option><option value="accepted">该部位认可</option><option value="pending">待核实</option></select></label><label class="full">观察<textarea id="observation" placeholder="例如：从西南侧看，斜撑显得过粗；请保留塔身比例。"></textarea></label><label class="full">希望如何修改<textarea id="requested" placeholder="说明目标，不必写代码。"></textarea></label><label class="full">必须保留<input id="preserve" placeholder="已认可的形体、灯光、入口等"></label></div><p id="pointInfo" class="muted">尚未标点</p><button id="saveFeedback" class="primary">保存并下载反馈 JSON</button><span id="saved"></span><p class="muted">只保存在当前浏览器并下载文件，不自动发送给任何人；将JSON带回对话即可接续。</p></section>
<footer>HAF 0.3 / 广州西塔 IFC V1_r02 / 2026-10-24。原工程保留；用户视觉验收与游戏测试待完成。源码与原图证据另附工程包。</footer></main><dialog id="lightbox"><button id="closeDialog">关闭</button><img id="largeImage" alt="放大视图"></dialog><script id="payload" type="application/json">__PAYLOAD__</script><script>
const D=JSON.parse(document.getElementById('payload').textContent),sel=document.getElementById('viewSelect'),img=document.getElementById('mainImage'),dlg=document.getElementById('lightbox');let point=null;
for(const [id,label] of Object.entries(D.labels)){const o=document.createElement('option');o.value=id;o.textContent=label;sel.append(o)}sel.value='se_day';
function update(){img.src=D.views[sel.value];document.getElementById('viewCaption').textContent=D.labels[sel.value]+' · '+D.run+' · 最终NBT回读';const a=document.getElementById('downloadView');a.href=img.src;a.download='IFC_V1_'+sel.value+'.webp';point=null;document.getElementById('marker').style.display='none';document.getElementById('pointInfo').textContent='尚未标点'}
sel.onchange=update;update();document.getElementById('dayToggle').onclick=()=>{let id=sel.value,id2=id.endsWith('_day')?id.replace(/_day$/,'_night'):id.endsWith('_night')?id.replace(/_night$/,'_day'):id==='overview'?'night':id==='night'?'overview':id+'_night';if(!D.views[id2]&&id.endsWith('_night'))id2=id.replace(/_night$/,'');if(D.views[id2]){sel.value=id2;update()}};
function large(src){document.getElementById('largeImage').src=src;dlg.showModal()}document.getElementById('zoom').onclick=()=>large(img.src);document.getElementById('closeDialog').onclick=()=>dlg.close();dlg.onclick=e=>{if(e.target===dlg)dlg.close()};
const detailIds=['top_day','base_plan','facade','facade_night','crown','crown_night','entrance','entrance_night','hotel_plan','office_plan','hotel_section','front'];for(const id of detailIds){const f=document.createElement('figure'),im=document.createElement('img'),c=document.createElement('figcaption');im.src=D.views[id];im.alt=D.labels[id];im.loading='lazy';im.onclick=()=>large(im.src);c.textContent=D.labels[id];f.append(im,c);document.getElementById('detailGrid').append(f)}
document.querySelectorAll('figure img').forEach(im=>{if(!im.onclick)im.onclick=()=>large(im.src)});
img.onclick=e=>{const b=img.getBoundingClientRect();point={x:Number(((e.clientX-b.left)/b.width).toFixed(4)),y:Number(((e.clientY-b.top)/b.height).toFixed(4))};const m=document.getElementById('marker');m.style.display='block';m.style.left=(point.x*100)+'%';m.style.top=(point.y*100)+'%';document.getElementById('pointInfo').textContent=D.labels[sel.value]+' · 标点 '+JSON.stringify(point)};
document.getElementById('saveFeedback').onclick=()=>{const r={case:D.case,baseline_run:D.run,source_nbt_sha256:D.source_nbt_sha256,component_id:document.getElementById('component').value,view_id:sel.value,verdict:document.getElementById('verdict').value,observation:document.getElementById('observation').value,requested_change:document.getElementById('requested').value,must_preserve:document.getElementById('preserve').value,normalized_image_point:point,created_at:new Date().toISOString()};try{localStorage.setItem('haf-ifc-feedback',JSON.stringify(r))}catch(e){}const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'}));a.download='IFC_V1_feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);document.getElementById('saved').textContent=' 已导出反馈'};
</script></body></html>'''
replacements={'__HERO_DAY__':views['se_day'],'__HERO_NIGHT__':views['se_night'],'__BUILD__':data(out/'IFC_V1_Build.zip','application/zip'),'__SCHEM__':data(run/'import_pack/Guangzhou_IFC_HAF03_V1.schem','application/octet-stream'),'__MATERIALS__':data(out/'materials.csv','text/csv'),'__SOURCES__':source_html,'__REFS__':refs,'__SHA__':manifest['sha256'],'__TABLE__':table,'__PAYLOAD__':json.dumps(payload,ensure_ascii=False).replace('</','<\/')}
for key,value in replacements.items():doc=doc.replace(key,value)
(out/'index.html').write_text(doc,encoding='utf-8')
dump(out/'delivery_manifest.json',{'case':'guangzhou_ifc','run':RUN,'files':[{ 'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.iterdir() if p.is_file() and p.name!='delivery_manifest.json'],'source_nbt_sha256':manifest['sha256']})
print('HTML',len(doc.encode()),'ZIP',(out/'IFC_V1_Build.zip').stat().st_size,'views',len(views))
