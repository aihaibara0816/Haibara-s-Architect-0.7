"""Self-contained review and portable study archive; never overwrite V1 release."""
from pathlib import Path
import sys,json,base64,html,hashlib,io,zipfile,csv
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;CASE=ROOT.parents[1];HAF=CASE.parents[1]
PRE=ROOT/'review/previews';DEST=ROOT/'deliverables';RES=CASE/'research/detail_study_v2'
DEST.mkdir(exist_ok=True)
FONT=HAF/'support/fonts/NotoSansCJKsc-Regular.otf'
def font(n):return ImageFont.truetype(str(FONT),n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def uri(p):
 mime='image/png' if p.suffix=='.png' else 'image/jpeg' if p.suffix.lower() in ['.jpg','.jpeg'] else 'application/octet-stream'
 return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def preview(p):
 im=Image.open(p).convert('RGB');buf=io.BytesIO();im.save(buf,format='JPEG',quality=93)
 return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
def figure(p,title,note=''):
 return f'<figure><img class="zoom" src="{preview(p)}" alt="{html.escape(title)}"><figcaption><b>{html.escape(title)}</b><br>{html.escape(note)}</figcaption></figure>'
def rawfigure(p,title,note=''):
 return f'<figure><img class="zoom ref" src="{uri(p)}" alt="{html.escape(title)}"><figcaption><b>{html.escape(title)}</b><br>{html.escape(note)}</figcaption></figure>'
def fit(canvas,p,box,crop=None):
 im=Image.open(p).convert('RGB');im=im.crop(crop) if crop else im
 im=ImageOps.contain(im,(box[2],box[3]));canvas.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2))
def plates():
 bg='#f2efe6';fg='#193c44';out=Image.new('RGB',(2400,2200),bg);d=ImageDraw.Draw(out)
 d.text((55,30),'周大福 · 夜景先有布局，再有随机',font=font(48),fill=fg)
 d.text((55,104),'同一 V1 形体与相机：固定暖色横带 + 上部竖向照明试验。屋顶未改。',font=font(28),fill=fg)
 for i,(lab,title) in enumerate([('v1_material_light','V1 / 修正光源显示'),('night_pattern_candidate','局部照明布局候选')]):
  d.text((45+i*610,185),title,font=font(28),fill=fg)
  fit(out,PRE/lab/'night.png',(20+i*610,245,585,1650),(220,0,1350,2600))
 for j,(lab,title) in enumerate([('v1_material_light','同机位近景 / 原布局'),('night_pattern_candidate','同机位近景 / 加入暖色横带')]):
  d.text((1260,185+j*890),title,font=font(28),fill=fg)
  fit(out,PRE/lab/'night_detail.png',(1250,240+j*890,1110,810))
 d.text((55,2010),'观察：横带已可辨；上部灯槽仍有断点，窗灯和预览散射偏亮，尚未通过视觉定稿。',font=font(29),fill=fg)
 d.text((55,2070),'实际 NBT 回读 · 0.5 格/米 · 306 个灯位变化 · 玻璃、主竖肋与旧文件保持不变',font=font(28),fill=fg)
 d.text((55,2120),'离线状态盒与近似光照；尚未进 Minecraft 验收。',font=font(26),fill='#546a70')
 out.save(DEST/'CTF_Night_Study.png')
 out=Image.new('RGB',(3600,2600),bg);d=ImageDraw.Draw(out)
 d.text((60,25),'周大福 V1 · 四个工作坐标方向',font=font(54),fill=fg)
 d.text((60,107),'相机统一：正投影 / 同尺度 / 同目标高度。地理北待核实；四张都是同一个原始 V1。',font=font(32),fill=fg)
 for i,(tag,title) in enumerate([('pos_z','+Z 方向看向塔楼'),('neg_z','−Z 方向看向塔楼'),('pos_x','+X 方向看向塔楼'),('neg_x','−X 方向看向塔楼')]):
  d.text((50+i*900,190),title,font=font(34),fill=fg);fit(out,PRE/'four_directions_v1'/(tag+'_day.png'),(20+i*900,260,860,2260))
 out.save(DEST/'CTF_Four_Views.png')
 out=Image.new('RGB',(2800,1840),bg);d=ImageDraw.Draw(out)
 d.text((50,25),'塔顶斜面 · 同一屋顶换方向观察',font=font(50),fill=fg)
 d.text((50,95),'当前冠部最高与最低网格相差 5 格；真实倾角待校正，不能把视图变化算作几何改进。',font=font(29),fill=fg)
 for i,(tag,title) in enumerate([('pos_z','+Z'),('neg_z','−Z'),('pos_x','+X'),('neg_x','−X')]):
  x=(i%2)*1400;y=170+(i//2)*800
  d.text((x+35,y),title,font=font(34),fill=fg);fit(out,PRE/'four_directions_v1'/('roof_'+tag+'.png'),(x+25,y+55,1350,710),(180,50,1250,870))
 out.save(DEST/'CTF_Roof_Four_Views.png')

def nbt_pack():
 readme='''HAF / CTF detail study, Java 1.21.1 (DataVersion 3955)
These are experimental NBT structures, not an accepted CTF V2 release.
Each run contains building.nbt, inspection.json and materials.csv.
facade_*: same room content and light seed; only fin material differs.
beacon_board: construction demonstration; recessed lamp source visible underneath on board.
beacon_context_*: same V1 with ONE trial fixture, location not verified against reality.
night_pattern_candidate: original V1 plus fixed lights on +Z/-X working faces; exact geographical mapping and other faces pending. Roof unchanged. Read diff.json.
NBT is a Java structure, NOT a .schem. A compatible importer is required.
The full-tower examples exceed vanilla structure-block dimensions and may exceed some importers' file-size limits. Do not assume direct single-template placement works. Use a compatible structure importer or implement/retest chunk packaging before in-game use. Existing V1 chunk pack is NOT the new lighting candidate.
Keep a test world backup and use a clear area. Sparse structures do not clear old blocks.
Previews use simplified state-box geometry, no original resource-pack textures, approximate scalar light propagation. No colored-light or blinking claim. In-game tests pending.
Material counts are placed cells, not crafting costs.
'''
 (DEST/'STUDY_IMPORT.txt').write_text(readme)
 with zipfile.ZipFile(DEST/'CTF_Detail_NBT_Samples.zip','w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('README.txt',readme)
  for d in sorted((ROOT/'runs').iterdir()):
   if 'rejected' in d.name:continue
   for p in sorted(d.iterdir()):
    if p.is_file():z.write(p,d.name+'/'+p.name)

CSS='''*{box-sizing:border-box}body{margin:0;background:#f3efe6;color:#213d45;font:16px/1.7 system-ui,sans-serif}header,main{max-width:1450px;margin:auto}header{padding:65px 30px 30px}h1{font-size:clamp(34px,5vw,64px);line-height:1.25;margin:15px 0}h2{font-size:29px;margin:0 0 16px}h3{font-size:20px}.eyebrow{font-size:12px;letter-spacing:.14em;color:#6b807e}main{padding:0 25px 45px}section{padding:28px;border:1px solid #d9d8ca;border-radius:16px;background:#fffcf6;margin:24px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.three{grid-template-columns:repeat(3,1fr)}figure{margin:0;min-width:0}figure img{width:100%;display:block;cursor:zoom-in;max-height:760px;object-fit:contain;background:#e0e6e4}figcaption{font-size:14px;padding:10px 1px;color:#5a7277}.ref{height:510px}.note{border-left:3px solid #b68c47;background:#f5edda;padding:12px 18px}.small{font-size:14px}.button,button,select{font:inherit;padding:9px 15px;border-radius:7px;border:1px solid #8ca09f;cursor:pointer}button,.button{background:#244f59;color:#fff;text-decoration:none;display:inline-block;margin:4px}.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:15px 0}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:11px;border-bottom:1px solid #d4dcda;text-align:left;vertical-align:top}.scroll{overflow:auto}a{color:#247580}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:#e9eeea;padding:14px}textarea{width:100%;min-height:130px;font:inherit;padding:12px}dialog{width:96vw;height:96vh;background:#142631;color:white;border:0}dialog img{display:block;max-width:100%;max-height:86vh;object-fit:contain;margin:auto}dialog::backdrop{background:#000b}#compareA,#compareB{height:850px}footer{font-size:13px;color:#60787c;margin:35px 0}@media(max-width:780px){.grid,.three{grid-template-columns:1fr}header{padding:35px 24px}section{padding:20px}#compareA,#compareB{height:680px}}'''

def report():
 dirlabels={'pos_z':'+Z','neg_z':'−Z','pos_x':'+X','neg_x':'−X'}
 data={}
 for tag in dirlabels:
  for day in ['day','night']:
   p=PRE/'four_directions_v1'/f'{tag}_{day}.png';data[tag+'_'+day]={'a':preview(p),'b':preview(PRE/'night_pattern_candidate'/f'{tag}_night.png') if day=='night' else preview(p)}
  data['roof_'+tag]={'a':preview(PRE/'four_directions_v1'/f'roof_{tag}.png')}
 old=CASE/'review/previews/V1'
 sources='https://www.lighting.co.jp/en/projects/guangzhou-ctf-finance-centre/'
 sections=[]
 sections.append('<section><h2>01 / 先读实景，再做夜景</h2><p>你提供的夜景中，暖色横带与上部偏冷的竖向照明属于固定图案；普通窗灯的亮暗才适合有节奏地变化。补看 LPA 的两张照片后，裙楼暖色竖向构件也有了更明确的依据。</p><div class="grid three">'+rawfigure(RES/'U02_night.png','你的夜景参考','原图 243×432；拍摄日期、地理方位及原摄影者未知。')+rawfigure(RES/'LPA01.jpg','LPA / 塔冠与横带','Christoph Kuegler；目标楼在画面右侧，左侧 IFC 的多道金环不套到东塔。')+rawfigure(RES/'LPA02.jpg','LPA / 裙楼暖光','Christoph Kuegler；本轮记录证据，裙楼尚未按此重做。')+'</div><p class="small">来源：<a href="'+sources+'">LPA 灯光设计项目页</a>。设计说明强调渐变、退台顶部重点照明与陶板间接线光。照片版权归原权利人；资料用于本次研究，不声明开放训练许可。</p></section>')
 sections.append('<section><h2>02 / 把显示修正与建筑修改分开</h2><div class="grid three">'+figure(old/'night_detail.png','A · V1 原预览','原 NBT，旧着色器：不同发光材质被强制近似同色。')+figure(PRE/'v1_material_light/night_detail.png','B · 同 NBT，修正材质显示','V1 本来含 641 海晶灯、544 萤石；修正不是增加暖灯。')+figure(PRE/'night_pattern_candidate/night_detail.png','C · 固定灯光布局候选','沿用 B 的渲染器，新增/替换 306 个光源格位。')+'</div><p class="note">C 的暖色横带约 198 米标高是本轮试验锚点，不是实测；依据照片与现有标高表给出的工作区间约 185–210 米。只在工作坐标 +Z/−X 这组可见面试放，真实方位与背面延续待核实。玻璃和主竖肋保持原状态，屋顶没有改动。上部竖向亮区仍有断点，还未达到照片的连贯度。</p><div class="grid">'+figure(PRE/'v1_material_light/night.png','原布局 / 修正后的统一渲染器')+figure(PRE/'night_pattern_candidate/night.png','固定横带与上部照明试验')+'</div><p>近似传播仍是标量亮度，不能据此判断游戏中的彩色投射光；当前窗灯和周围散射也显得偏亮。下一步应检查实际游戏环境，并按证据压低普通窗灯对固定灯带的竞争，而不是无限加灯。</p></section>')
 options=''.join(f'<option value="{tag}">{label} 方向</option>' for tag,label in dirlabels.items())
 sections.append('<section><h2>03 / 四向看整体</h2><p>四张统一正投影、尺度与目标高度。地理北尚未标定，不能把它们直接称为东南西北。</p><div class="controls"><select id="direction">'+options+'</select><select id="daynight"><option value="day">白天 / 两边同一 V1</option><option value="night">夜间 / 原布局与候选</option></select></div><div class="grid"><figure><img id="compareA" class="zoom" alt="原 V1"><figcaption>原 V1；修正后的统一渲染器</figcaption></figure><figure><img id="compareB" class="zoom" alt="夜景布局候选"><figcaption id="compareCaption"></figcaption></figure></div><p class="small">−Z 与 +X 未试放固定灯带，主要用于检查保留的背面；不能把“本轮未改”误认为这些面的真实夜景已经验证。</p></section>')
 sections.append('<section><h2>04 / 屋顶确实有视角差异，坡度仍待校正</h2><div class="grid">'+rawfigure(RES/'U01_roof.png','你的白天参考','顶部高低边清晰；单张透视照片不能给真实倾角。')+rawfigure(RES/'model_candidate_nanORay.jpg','NanoRay / Sketchfab 模型预览','模型缩略图已查看；尚未获得网格，不能称已经融合 SU。')+'</div><div class="grid">'+''.join(figure(PRE/'four_directions_v1'/f'roof_{tag}.png',label+' 方向 / 同一 V1 屋顶') for tag,label in dirlabels.items())+'</div><p>从 ±X 方向可以清楚看到当前斜边，从 ±Z 更容易看成平顶。原参数名义高差 6 格，实际冠部屋面网格最高与最低相差 5 格。照片的斜切表达仍比这一版强，真实坡度和高低边定义继续保留为待校正；没有把换相机当成屋顶修复。</p><p>已找到 <a href="https://3dwarehouse.sketchup.com/model/70a2c2e2-d818-4bd6-8c2a-74ba6b9199e6/Guangzhou-CTF-Finance-Centre">3D Warehouse 条目</a>（访问 403）和 <a href="https://sketchfab.com/3d-models/guangzhou-ctf-finance-centre-7b2d05b74aa64d1f9f7b4f56171536f7">NanoRay 的 Sketchfab 模型</a>（公开 API 标 CC BY 4.0、2022 年发布；下载接口 401）。缩略图只是简化模型线索；取得文件后仍需检查年代、比例、坐标和与照片的一致性。</p></section>')
 sections.append('<section><h2>05 / 分隔粗细：不能全楼一键换铁栅栏</h2><div class="grid three">'+''.join(figure(PRE/f'facade_{k}/front.png',t,n) for k,t,n in [('wall','原浅色墙柱','主竖肋清楚，但较厚。'),('bars','全部铁栅栏','正面更细、更暗，白色陶板特征削弱。'),('hybrid','保留主肋＋细次分隔','作为后续候选；主次构件需要重新划分，非定稿。')])+'</div><div class="grid three">'+''.join(figure(PRE/f'facade_{k}/oblique.png',t) for k,t in [('wall','墙柱 / 斜视'),('bars','铁栅栏 / 斜视'),('hybrid','混合 / 斜视')])+'</div><p>三个样板保留相同 24 个窗后单元与种子，只改变竖向分隔。铁栅栏与邻接玻璃的连接也会产生深度，斜视不能只看正面宽度。当前是简化状态盒，尚未模拟原版铁栅栏透明纹理；真实观感必须进游戏核对。</p></section>')
 sections.append('<section><h2>06 / 障碍灯：先看它在整栋上的大小</h2>'+figure(PRE/'beacon_board/night.png','构造展示：左红石火把 / 中嵌入罩 / 右玻璃片环','中间光源在样板台下部外露是拆解展示；屋顶场景中嵌入屋面。')+'<div class="grid three">'+''.join(figure(PRE/f'beacon_context_{k}/roof.png',t,n) for k,t,n in [('glass_ring','3×3 玻璃片环罩','本比例占地约 6×6 米，作为普通单灯偏大。'),('recessed_cap','1×1 嵌入红玻璃罩','体量更克制，可作为待游戏验证候选。'),('torch','红石火把','细小，但远景辨识弱；没有闪烁电路。')])+'</div><p>三个灯都只在同一试验位置放一盏，实际障碍灯位置尚未确认。红玻璃包住萤石可以表现红色灯体，不保证原版产生红色投射光。</p></section>')
 sections.append('<section><h2>07 / 房间要有变化，也要放得下</h2><div class="grid">'+figure(PRE/'rooms_cut/cut.png','实际样板剖切','工作台/铁砧、书架、休息座位、叶块盆栽分房间选择。')+figure(PRE/'facade_hybrid/night.png','同一批窗后的夜间状态','暖冷光源与暗窗保留；随机结果可复现。')+'</div><p>一格净高的窗后单元不放两格高盆栽；两格净高才允许木质底座与叶块叠放。样板是伪内饰补全，没有声称是真实东塔户型，也不保证所有单元可供玩家通行。书架预览暂用色块，没有原版纹理。</p></section>')
 brief='以广州周大福金融中心为原型，保持既有体量、统一比例与幕墙层次。根据已查看夜景，分开处理上部偏冷的竖向照明、可见立面的暖色横带、离散室内窗灯和暖色裙楼。先将固定灯带按照片的起止和转角关系定位，再把萤石藏入玻璃后的槽位；保留主竖肋与暗缝。上部线性照明按退台分区，不能变成整面发光墙。普通窗灯按稳定房间 ID、区域与种子改变亮暗和冷暖；没有证据的背面、精确标高和障碍灯位置保留待核实。'
 sections.append('<section><h2>08 / 已落实到 Skill 的规则</h2><p>HA 高保真研究规则 0.2 增加夜景证据到灯光构件的对应；外部建筑 AI 资料 Skill 增加夜景关键词要求，同时保留其六图上传默认。HA 研究仍不限图片数量。这里改的是工作规则，不是训练新的视觉模型。</p><pre>'+html.escape(brief)+'</pre><div class="scroll"><table><tr><th>检查</th><th>结果</th></tr><tr><td>公共代码</td><td>23 项测试通过；包含材质显示策略、铁砧状态盒与室内净高约束。</td></tr><tr><td>原版保护</td><td>29 份 V1 文件哈希未变；所有新样板从 NBT 回读核对。</td></tr><tr><td>夜景局部修改</td><td>306 个格位仅用于本轮声明的光源；玻璃与主竖肋状态未变。首轮试验引起 13 个玻璃片连接变化，已拒绝并加邻接保护后重跑。</td></tr><tr><td>视觉与游戏</td><td>样板已查看；屋顶、灯槽连续性、真实北向、游戏内灯光与材质仍待验收。</td></tr></table></div></section>')
 sections.append('<section><h2>09 / 下载与反馈</h2><p>这里是可回顾的局部实验，不替换已发布 V1。完整塔楼样本尺寸较大，尚未为新候选制作并验收分片；应使用兼容 NBT 的导入方式，不能把旧 V1 分片包当作本轮新夜景。</p><a class="button" download="CTF_Detail_NBT_Samples.zip" href="'+uri(DEST/'CTF_Detail_NBT_Samples.zip')+'">下载 NBT 样板与各版材料表</a><a class="button" download="STUDY_IMPORT.txt" href="'+uri(DEST/'STUDY_IMPORT.txt')+'">导入说明</a><h3>记录下一轮修改</h3><select id="component"><option>塔顶斜面</option><option>暖色横带</option><option>竖向照明</option><option>主肋与次分隔</option><option>障碍灯</option><option>窗后内饰</option><option>裙楼夜景</option></select><textarea id="feedback" placeholder="哪处值得保留？哪处还不接近？"></textarea><button id="exportFeedback">导出反馈 JSON</button><span id="feedbackStatus"></span></section>')
 js='''const V=DATA;const $=id=>document.getElementById(id);function update(){const key=$('direction').value+'_'+$('daynight').value;$('compareA').src=V[key].a;$('compareB').src=V[key].b;$('compareCaption').textContent=$('daynight').value==='day'?'白天保持同一 V1：用于排除形体变化':'固定灯光候选；只有 +Z/−X 试放了固定照明';} $('direction').onchange=update;$('daynight').onchange=update;update();document.querySelectorAll('.zoom').forEach(im=>im.onclick=()=>{$('zoomImage').src=im.src;$('zoomTitle').textContent=im.alt;$('zoom').showModal()});$('closeZoom').onclick=()=>$('zoom').close();$('exportFeedback').onclick=()=>{const row={case:'guangzhou_ctf',study:'detail_v2',component:$('component').value,view:$('direction').value,feedback:$('feedback').value,candidate_nbt_sha256:HASH,time:new Date().toISOString()};let a=document.createElement('a');let u=URL.createObjectURL(new Blob([JSON.stringify(row,null,2)],{type:'application/json'}));a.href=u;a.download='CTF_detail_study_feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),2000);$('feedbackStatus').textContent='反馈已导出';};'''.replace('DATA',json.dumps(data)).replace('HASH',json.dumps(sha(ROOT/'runs/night_pattern_candidate/building.nbt')))
 txt='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>周大福 · 夜景与细部研究</title><style>'+CSS+'</style></head><body><header><div class="eyebrow">HAF / DETAIL STUDY / 2026.10.23</div><h1>让夜景有建筑自己的秩序。</h1><p>四向视图、固定灯带、材质冷暖、细分隔、红灯与窗后空间。保存 V1，用局部对照决定下一步。</p><p class="note">实际 NBT 回读预览；不是游戏截图。屋顶未改、模型网格未取得、不是完整 V2 定稿。</p></header><main>'+''.join(sections)+'<footer>固定证据优先于随机补全 · 几何、渲染、视觉与游戏验收分开记录</footer></main><dialog id="zoom"><button id="closeZoom">关闭</button><span id="zoomTitle"></span><img id="zoomImage" alt="放大图"></dialog><script>'+js+'</script></body></html>'
 (DEST/'CTF_Night_and_Detail_Study.html').write_text(txt);(ROOT/'review_script.js').write_text(js)
 print('html',len(txt.encode()))

if __name__=='__main__':plates();nbt_pack();report()
