"""Build the offline review and reproducible deliverables from a verified run."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,io,base64,html,hashlib,zipfile,shutil,sys,csv,os
ROOT=Path(__file__).resolve().parents[3];CASE=Path(__file__).resolve().parents[1]
RUN=sys.argv[1];r=CASE/'runs'/RUN;pre=CASE/'review/previews'/RUN
OUT=ROOT/'deliverables/guangzhou_memorial_v2';OUT.mkdir(parents=True,exist_ok=True)
m=json.loads((r/'manifest.json').read_text());v=json.loads((r/'validation.json').read_text());imp=json.loads((r/'import_pack/import_manifest.json').read_text())
refs=json.loads((CASE/'research/image_manifest.json').read_text());rr=json.loads((pre/'render_report.json').read_text())
assert len(rr)==20 and all(x['pass'] for x in v['checks'])
for row in rr:
    f=pre/row['image'];assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
    with Image.open(f) as im:im.load()
def data(f,width=1700):
    im=Image.open(f).convert('RGB');im.thumbnail((width,width*2));buf=io.BytesIO();im.save(buf,format='JPEG',quality=88)
    return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
def figure(f,label):return '<figure><img class="zoom" loading="lazy" src="'+data(f)+'" alt="'+html.escape(label)+'"><figcaption>'+html.escape(label)+'</figcaption></figure>'
fontpath='/root/.local/share/fonts/haf/NotoSansCJKsc-Regular.otf'
def board(ids,name,title,sub,w=1500,h=1300):
    cols=2;rows=(len(ids)+1)//2;im=Image.new('RGB',(cols*w,rows*h+180),'#f3f0e7');d=ImageDraw.Draw(im)
    d.text((56,28),title,font=ImageFont.truetype(fontpath,56),fill='#153350');d.text((58,110),sub,font=ImageFont.truetype(fontpath,28),fill='#586365')
    for i,(fid,label) in enumerate(ids):
        a=Image.open(pre/(fid+'.png')).convert('RGB');a.thumbnail((w-24,h-70));x=(i%cols)*w;y=180+(i//cols)*h
        im.paste(a,(x+(w-a.width)//2,y+58+(h-70-a.height)//2));d.text((x+28,y+7),label,font=ImageFont.truetype(fontpath,32),fill='#153350')
    buffer=io.BytesIO();im.save(buffer,format='PNG');blob=buffer.getvalue()
    with Image.open(io.BytesIO(blob)) as verify:verify.load()
    temporary=OUT/(name+'.tmp')
    with temporary.open('wb') as stream:stream.write(blob);stream.flush();os.fsync(stream.fileno())
    temporary.replace(OUT/name)
board([('overview','建筑与前广场'),('night','冷色檐线与暖色入口'),('front','正面层级'),('top','正俯视：八角顶与四向抱厦')],'Guangzhou_Memorial_V2_Overview.png','广州中山纪念堂 · HAF V2','实际 NBT 离线预览 | 2 格 / 米 | 形体与细节待品鉴',1500,1450)
for mode,title in [('day','四向日景'),('night','四向夜景')]:
    board([(q+'_'+mode,n) for q,n in [('se','东南 · 模型坐标'),('sw','西南 · 模型坐标'),('ne','东北 · 模型坐标'),('nw','西北 · 模型坐标')]],'Guangzhou_Memorial_V2_Four_'+mode+'.png',title,'相同尺度、俯角与目标；不冒称实测地理朝向',1500,1300)
board([('roof','八角顶与屋面交接'),('entrance','柱廊、门窗与匾额'),('entrance_night','门廊与柱脚灯'),('interior_cut','大会堂剖切示意')],'Guangzhou_Memorial_V2_Details.png','细部与内部空间','斗拱、博古、雕像与座席均含方块化简化',1500,1350)
shutil.copy2(pre/'top.png',OUT/'Guangzhou_Memorial_V2_Top.png');shutil.copy2(r/'materials.csv',OUT/'Guangzhou_Memorial_V2_Materials.csv')
titles={'overview':'建筑与前广场','night':'整体夜景','front':'正立面','rear':'背立面','top':'正俯视','roof':'屋顶近景','entrance':'入口近景','entrance_night':'入口夜景','interior_cut':'去屋顶看大会堂','hall_section':'纵向剖切示意','interior_plan':'楼座俯视剖切','roof_night':'屋顶夜景'}
for q,n in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]:
    for mode,label in [('day','日景'),('night','夜景')]:titles[q+'_'+mode]=n+label+'（模型坐标）'
categories={'全景':['overview','night','front','rear'],'四向日景':[q+'_day' for q in ['se','sw','ne','nw']],'四向夜景':[q+'_night' for q in ['se','sw','ne','nw']],'俯视与局部':['top','roof','roof_night','entrance','entrance_night'],'内部':['interior_cut','hall_section','interior_plan']}
gallery=''.join('<div class="group" data-group="'+cat+'">'+''.join(figure(pre/(fid+'.png'),titles[fid]) for fid in ids)+'</div>' for cat,ids in categories.items())
refhtml=''.join('<article>'+figure(CASE/x['path'],x['image_id']+' · '+x['view'])+'<p>'+html.escape(x['observation'])+'</p><small>'+html.escape(x['limitations'])+'</small><p><a href="'+html.escape(x['source_page'],quote=True)+'" target="_blank" rel="noreferrer">来源页 ↗</a> · <a download="'+(Path(x['path']).stem+'.jpg')+'" href="'+data(CASE/x['path'],1400)+'">下载研究图副本</a></p></article>' for x in refs)
materialrows=list(csv.DictReader((r/'materials.csv').read_text(encoding='utf-8-sig').splitlines()))
materialtable=''.join('<tr><td>'+x['block_id'].replace('minecraft:','')+'</td><td>'+f"{int(x['count']):,}"+'</td><td>'+x['stacks']+' 组 + '+x['remainder']+'</td></tr>' for x in sorted(materialrows,key=lambda x:-int(x['count'])))
checks=''.join('<tr><td>'+html.escape(x['check'])+'</td><td>通过</td></tr>' for x in v['checks'])
doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州中山纪念堂 · HAF V2</title>
<style>:root{--navy:#153350;--paper:#f3f0e7;--gold:#b78a37}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:#1c2b34;font-family:system-ui,"Noto Sans CJK SC",sans-serif;line-height:1.75}header{padding:64px 6vw 40px;background:var(--navy);color:white}header small{letter-spacing:.18em;color:#d6b576}h1{font-size:clamp(36px,5vw,72px);line-height:1.22;margin:20px 0}header p{max-width:850px;color:#d7e0e4}nav{background:#fff9;backdrop-filter:blur(8px);position:sticky;top:0;z-index:4;display:flex;gap:20px;overflow:auto;padding:14px 6vw;border-bottom:1px solid #cdd0ca}a{color:#285979}nav a{white-space:nowrap;text-decoration:none}main{max-width:1540px;margin:auto;padding:0 5vw 80px}section{padding-top:44px}h2{font-size:27px;color:var(--navy);border-top:2px solid #d6c5a6;padding-top:24px}h2 span{color:var(--gold);margin-right:12px;font-size:18px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:28px 0}.stat{background:white;padding:18px;border-left:3px solid var(--gold)}.stat b{display:block;font-size:27px;color:var(--navy)}figure{margin:0;background:#e5e8e3;overflow:hidden;border-radius:7px}figure img{display:block;width:100%;cursor:zoom-in}figcaption{padding:10px 16px;background:#fff;color:#43545e;font-size:14px}.group,.refs,.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:20px}.group[hidden]{display:none}.refs{grid-template-columns:repeat(3,minmax(0,1fr))}.refs article{padding:12px;background:white}.refs p{font-size:14px;margin:10px 0}.refs small{color:#687680}.filters{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0}.filters button{border:1px solid #bbc6c6;background:white;color:var(--navy);padding:11px 19px;border-radius:24px;font:inherit;cursor:pointer}.filters button.active{background:var(--navy);color:white}.note{padding:17px 22px;background:#e5e9e4;border-left:3px solid var(--gold)}table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}td,th{text-align:left;padding:12px;border-bottom:1px solid #dde3df;vertical-align:top}th{background:#e1e7e4}.tablewrap{max-height:460px;overflow:auto}.mono{font-family:monospace;word-break:break-all;font-size:12px}details{background:white;padding:15px;margin:10px 0}summary{cursor:pointer;font-weight:600}dialog{max-width:96vw;max-height:96vh;border:0;padding:12px;background:#142434;color:white}dialog::backdrop{background:#000d}dialog img{display:block;max-width:90vw;max-height:84vh;object-fit:contain}dialog button{float:right;background:#fff;color:#17334c;border:0;padding:8px 16px;cursor:pointer}.muted{color:#5c6c73}footer{padding:30px 0;border-top:1px solid #bbb}@media(max-width:780px){.group,.pair,.refs{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}header{padding-top:40px}main{padding:0 18px 60px}}@media print{nav,.filters,dialog{display:none}section{break-inside:avoid}.group[hidden]{display:grid}}</style>
<header><small>HAIBARA’S ARCHITECT · HAF 0.2 · CASE STUDY 2026.10.24</small><h1>广州中山纪念堂<br>蓝瓦、重檐与中央大会堂</h1><p>V2 局部修订 · 根据用户反馈修复构件连接。中央八角高顶、四向抱厦、红柱门廊、纪念像与前广场分别建模；本页图片全部来自最终建筑文件的离线几何预览。</p></header>
<nav><a href="#s1">版本</a><a href="#s2">原型</a><a href="#s3">参考盒</a><a href="#s4">尺度</a><a href="#s5">构件</a><a href="#s6">大图品鉴</a><a href="#s7">灯光</a><a href="#s8">材料导入</a><a href="#s9">验证</a><a href="#s10">反馈</a></nav><main>
<section id="s1"><h2><span>01</span>这一版做到了哪里</h2><p>本版针对 V1 中过大的匾额、八角窗带下方缺口、抱厦屋顶交接和门廊缺失台面进行修订。V1 原始文件保留；尺度、相机、庭院与主体参数沿用，便于直接对照。</p><div class="stats"><div class="stat"><b>2 格 / 米</b>统一比例</div><div class="stat"><b>97 格</b>地坪至顶端</div><div class="stat"><b>20 张</b>日夜、俯视与剖切</div><div class="stat"><b>10 份</b>照片与档案图</div></div>HERO<div class="note">V2 将匾额改为小蓝底与四个单格金色标记；补齐门廊承托平台、檐底、八角窗带下部围护和四处屋顶转角。雕像、斗拱和屋脊细节继续保留简化。</div></section>
<section id="s2"><h2><span>02</span>原型与来源取舍</h2><p>采用广州市林业和园林局公布的高 48.63 米、东西宽 63.32 米、南北深 72.65 米作为尺度依据。越秀区政府资料与航拍共同支持中央八角攒尖顶、四向抱厦和多层出檐关系。另一份文旅局资料写高 52 米，本版保留冲突、不取平均。</p><p><a href="https://lyylj.gz.gov.cn/stly/gyjq/zsjnt/jdjs/content/post_8317825.html">园林局尺寸来源</a> · <a href="https://www.yuexiu.gov.cn/zjyx/yxjd/gzjdgms/content/post_8659223.html">越秀区官方图文</a> · <a href="https://wglj.gz.gov.cn/ztmb/gzhyn/ajjq/4a/content/post_8904608.html">文旅局差异记录</a> · <a href="https://www.gzdaj.gov.cn/gzdt/gnxw/content/post_256825.html">档案馆设计图与博古说明</a></p></section>
<section id="s3"><h2><span>03</span>多向参考盒</h2><p>研究图不设数量上限。这次实际采用的工作组覆盖正面、前后航拍、斜面、室内、夜景和历史剖面；“十份”是本次得到的资料数，不是新限制。所有采用图已逐张查看。隐藏侧面细节仍属于待核实部分。</p><div class="refs">REFS</div><p class="muted">图源仅作本案例研究；许可未明的图片不宣称可用于模型训练。历史设计图不是现状测绘，透视航拍不是正射平面。</p></section>
<section id="s4"><h2><span>04</span>尺度、方向与制作边界</h2><table><tr><th>项目</th><th>本版处理</th></tr><tr><td>建筑尺度</td><td>约 2 格/米，保持均匀比例；出檐包络约 127 × 147 格，建筑高 97 格。分层标高和屋檐曲线按照片估计。</td></tr><tr><td>场地范围</td><td>整包 236 × 108 × 280 格（X/Y/Z）。含前广场、纪念像和局部园林；不等同整个纪念堂园区。</td></tr><tr><td>方向</td><td>入口朝模型 +Z；模型东 +X、北 −Z。原型正面约朝南，未进行测绘级朝向配准。</td></tr><tr><td>资料路线</td><td>图片与档案解释 → 构件参数 → 案例生成器 → HAF 方块导出。没有使用 SU，没有自动相机恢复或模型训练。</td></tr></table></section>
<section id="s5"><h2><span>05</span>构件如何落到模型</h2><table><tr><th>构件</th><th>证据与实际实现</th><th>仍需改进</th></tr><tr><td>八角高顶</td><td>前后航拍 + 档案剖面；八个曲面片、八角窗带、金色顶饰</td><td>瓦垄、檐角、收分仍为离散曲面</td></tr><tr><td>四向抱厦</td><td>八组上下屋面；歇山端部、外伸屋檐和支承带分别生成</td><td>屋面连接已补齐；转角细部为照片解释，博古雕刻仍简化</td></tr><tr><td>入口与围护</td><td>红柱、开门洞、玻璃内退、红色窗格、彩画色带</td><td>字形已改成单格金色标记；柱径和斗拱仍可精修</td></tr><tr><td>大会堂</td><td>舞台、两层弧形楼座、座席、过道、天花环；中央无柱</td><td>座位数、疏散交通和设备区不是实测复刻</td></tr><tr><td>广场园林</td><td>纪念像、中轴铺地、两侧花坛、锥形绿篱、部分草坪</td><td>雕像为轮廓占位；园林尺寸与树种分布近似</td></tr></table></section>
<section id="s6"><h2><span>06</span>大图品鉴</h2><p>点击图片放大。四个斜向全景使用同一尺度、俯角与目标；局部图另设近景相机。剖切图只在显示时裁切，完整导出模型没有被切掉。</p>COMPARE<div class="filters">BUTTONS</div>GALLERY</section>
<section id="s7"><h2><span>07</span>夜景与内部灯光</h2><p>本版以 ref06 的冷色屋面檐线、暖色入口与窗带为主要参考。ref08 的偏暖泛光作为另一种模式存档，没有把两种夜景取平均。</p><p>门廊柱间灯、柱脚灯、中央窗带、檐下灯、楼座与天花灯、纪念像和园路灯分别放置并检查。荧石表现暖光，海晶灯表现偏冷灯具；原版 Minecraft 不会因为玻璃颜色自动产生 RGB 染色光，离线预览也不等于真实游戏照度。</p><div class="pair">LIGHTPAIR</div></section>
<section id="s8"><h2><span>08</span>材料与导入</h2><p>总计 BLOCKCOUNT 个非空气方块，包括场地垫层、植被和建筑。建议先在空白测试场地使用包内 <code>.schem</code>；同时提供稀疏 <code>.nbt</code> 与 MODULECOUNT 个分片及坐标偏移表。</p><p>DataVersion 3955；Java 导入器和游戏内效果尚待验证。现代主世界高度范围假设为 [−64, 320)，整包原点 Y 须落在 −64 至 212。稀疏 NBT 不清空已有方块；Sponge 文件含显式空气。</p><details><summary>展开材料清单</summary><div class="tablewrap"><table><tr><th>方块 ID</th><th>数量</th><th>64 个/组</th></tr>MATERIALS</table></div></details></section>
<section id="s9"><h2><span>09</span>已验证与未验证</h2><table><tr><th>层级</th><th>状态</th></tr><tr><td>文件</td><td>NBT 独立回读、Sponge 非空气逐格回读、分片重组一致：通过</td></tr><tr><td>几何</td><td>CHECKCOUNT 项原案例检查及 8 项新缺陷回归通过；23 项继承 HAF 检查通过</td></tr><tr><td>视觉</td><td>20 张最终 NBT 预览已生成并检查；仍保留屋顶与雕刻简化</td></tr><tr><td>游戏</td><td>待验证：实际导入、碰撞、照明传播、透明排序、通行</td></tr><tr><td>还原度</td><td>等待用户品鉴；技术检查不能代替审美认可</td></tr></table><details><summary>展开几何检查项目</summary><table>CHECKS</table></details><p class="mono">最终 NBT SHA-256: NBTHASH</p><p class="muted">预览使用方块形状与示意颜色，没有加载原版纹理包；不作为游戏截图。</p></section>
<section id="s10"><h2><span>10</span>反馈与 HAF 0.3 计划</h2><p>建议先看：① 八角高顶与下方抱厦的比例；② 屋面交接和出檐厚度；③ 红柱门廊与前广场距离；④ 夜景是否出现过亮檐线、偏暗墙面。以构件为单位记录“图片编号 → 预览视角 → 期望变化”，再改对应参数。</p><p>工程附 <code>feedback_template.json</code>、来源与采用记录、参数、构件归属及生成快照。本次将缺陷记录成可重跑的检查：8 项新增检查在 V1 中都能检出问题，再验证 V2 修复。本版引擎保持 HAF 0.2。按你的安排，继续完成几栋不同结构建筑的练习与还原度反馈后，再整理可复用规则、回归测试与能力边界，发布 HAF 0.3；当前没有提前改版本号，也不宣称进行了模型权重训练。</p><footer>HAF 0.2 · 广州中山纪念堂 V2 · RUNID · 2026-10-24</footer></section></main><dialog id="zoom"><button onclick="this.closest('dialog').close()">关闭 ×</button><p id="caption"></p><img id="large" alt=""></dialog>
<script>const groups=[...document.querySelectorAll('.group')],buttons=[...document.querySelectorAll('.filters button')];function select(k){groups.forEach(g=>g.hidden=k!=='全部'&&g.dataset.group!==k);buttons.forEach(b=>b.classList.toggle('active',b.textContent===k))}buttons.forEach(b=>b.onclick=()=>select(b.textContent));select('全景');const modal=document.querySelector('#zoom');document.querySelectorAll('img.zoom').forEach(im=>im.onclick=()=>{document.querySelector('#large').src=im.src;document.querySelector('#large').alt=im.alt;document.querySelector('#caption').textContent=im.alt;modal.showModal()});modal.onclick=e=>{if(e.target===modal)modal.close()};</script></html>'''
replacements={'HERO':figure(pre/'overview.png','主视角 · 从最终 NBT 读回'),'REFS':refhtml,'BUTTONS':''.join('<button>'+x+'</button>' for x in ['全部',*categories]),'GALLERY':gallery,'LIGHTPAIR':figure(pre/'night.png','整体夜景')+figure(pre/'entrance_night.png','入口夜景'),'BLOCKCOUNT':f"{m['non_air_blocks']:,}",'MODULECOUNT':str(imp['module_count']),'MATERIALS':materialtable,'CHECKCOUNT':str(v['total']),'CHECKS':checks,'NBTHASH':v['source_nbt_sha256'],'RUNID':RUN}
for a,z in replacements.items():doc=doc.replace(a,z)

oldpre=CASE/'review/previews/V1_r03'
comparison='<h3>V1 → V2 · 同机位局部对照</h3><p>左侧 V1，右侧 V2。先看匾额占比，再看窗带下部、屋顶转角和柱础落地。</p>'
for fid,label in [('front','匾额与正面'),('roof','窗带承托与屋面连接'),('entrance','柱廊平台与檐底')]:
    comparison+='<div class="pair">'+figure(oldpre/(fid+'.png'),'V1 · '+label)+figure(pre/(fid+'.png'),'V2 · '+label)+'</div>'
doc=doc.replace('COMPARE',comparison)

(OUT/'Guangzhou_Memorial_HAF_V2_Review.html').write_text(doc)
feedback={'case':'guangzhou_memorial','baseline_run':RUN,'review_status':'awaiting_user','items':[{'component_id':'roof.central','view':'roof','reference_image':'ref01/ref03','observation':'','requested_change':'','acceptance':'','status':'open'},{'component_id':'entry','view':'entrance_night','reference_image':'ref06','observation':'','requested_change':'','acceptance':'','status':'open'}]}
(CASE/'feedback_template.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2))
readme=f'''广州中山纪念堂 HAF V2 / {RUN}
主线 HAF 0.2；图像研究案例；非任意建筑自动生成。
2 格/米；建筑地坪至顶端 97 格；整包 X/Y/Z = 236/108/280。
本包包括 .schem、稀疏 .nbt、{imp['module_count']} 个分片、材料与偏移表。
Sponge .schem 含显式空气；稀疏 NBT 不会清除原场地已有方块。
DataVersion 3955；建议在空白测试世界使用兼容导入器。
原点 Y 范围（现代主世界 -64..319 假设）：-64 至 212。
已做离线逐格回读/分片重组。游戏导入、照明、碰撞、通行均待验证。
场地为前广场和部分园林；未制作整个园区。屋檐、博古、雕像与室内座席含近似。
最终 NBT SHA-256: {v['source_nbt_sha256']}
'''
(r/'import_pack/README_CN.txt').write_text(readme)
(CASE/'README.txt').write_text(readme+'''
复跑（从 HAF_Guangzhou_Memorial 根目录）：
python3 tools/agent.py --case guangzhou_memorial --run NEW_RUN
python3 cases/guangzhou_memorial/src/validate_case.py NEW_RUN
python3 tools/render_building_case.py --case guangzhou_memorial --run NEW_RUN
python3 tools/package_building_case.py --case guangzhou_memorial --run NEW_RUN --name Guangzhou_Memorial_HAF_V2
PYTHONPATH=support/deps python3 -m unittest discover -s tests -v
V2 入口参数：cases/guangzhou_memorial/research/parameters_v2.json
V1 入口保留：python3 tools/agent.py --case guangzhou_memorial_v1 --run NEW_V1_RUN
源图、来源及构件证据：cases/guangzhou_memorial/research/
生成快照与不覆盖历史：cases/guangzhou_memorial/runs/
EGL 预览需要系统 EGL/OpenGL 和 NumPy/Pillow；所有已经生成的大图随包保留。
''')
legacy_learning={'case':'guangzhou_memorial','result':'reviewable V1, awaiting user fidelity feedback','rules':[{'finding':'支承带补洞若不受屋面高度约束会冒出白色方块','evidence':'V1_r02 entrance/top previews','fix':'V1_r03 infill top clipped below lower roof surface','scope':'this case roof intersections'},{'finding':'设置灯块不等于入口可见光充足','evidence':'V1_r01 vs V1_r02 entrance_night','fix':'exposed lamps between columns, inset window lights and pillar-foot lights','scope':'offline visual and adjacency checks, game pending'},{'finding':'传统外观不能推出传统内部柱网','evidence':'official auditorium ref05 and archive ref10','fix':'column-free center, stage and two curved galleries','scope':'estimated layout, no exact seating or egress claim'}]}
# V2 evidence ledger is maintained separately; do not overwrite it here.
with zipfile.ZipFile(OUT/'Guangzhou_Memorial_HAF_V2_Build.zip','w',zipfile.ZIP_DEFLATED,6) as z:
    for f in sorted((r/'import_pack').rglob('*')):
        if f.is_file():z.write(f,f.relative_to(r/'import_pack'))
    for f in ['validation.json','manifest.json','params_used.json','repair_validation.json','adapter_dependencies.json']:z.write(r/f,'verification/'+f)
summary={'case':'guangzhou_memorial','run':RUN,'date':'2026-10-24','nbt_sha256':v['source_nbt_sha256'],'non_air_blocks':m['non_air_blocks'],'size_xyz':m['size_xyz'],'case_checks':f"{v['passed']}/{v['total']}",'shared_tests':'23/23','views':len(rr),'module_count':imp['module_count'],'readback_exact':True,'game_status':'pending','fidelity_status':'awaiting user','repair_checks':'8/8; V1 negative control 8/8 detected','planned_release':'HAF 0.3 after additional independent cases','known_limits':['approximate eaves and gables','simplified bracket and statue','no exact seating layout','partial garden','no surveyed bearing','schematic material preview, not original textures']}
(OUT/'Guangzhou_Memorial_V2_Delivery.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
