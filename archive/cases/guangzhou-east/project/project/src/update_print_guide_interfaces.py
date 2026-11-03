"""Produce the B03-specific construction datum sheet and update the existing guide."""
from pathlib import Path
import json,io,os,re,base64,hashlib,html as esc
from PIL import Image,ImageDraw,ImageFont
from fontTools import subset
from fontTools.ttLib import TTFont
P=Path(__file__).resolve().parents[1];D=P/'deliverables/B03S1';R=P/'runs/B03S2'
s=json.loads((R/'interface_spec.json').read_text());font=P/'research/dongguanxi/NotoSansCJKsc-Regular.otf';ft=lambda z:ImageFont.truetype(str(font),z)
ink='#243e4d';muted='#647e89';blue='#167f9f';indigo='#5366a3';gold='#bc8a38';green='#427766';bg='#f5f7f4'
im=Image.new('RGB',(2200,2480),bg);dr=ImageDraw.Draw(im)
def text(x,y,t,size=28,fill=ink):dr.text((x,y),t,font=ft(size),fill=fill)
def card(box):dr.rounded_rectangle(box,20,fill='white',outline='#d2dfe1',width=2)
def pnt(p):return(110+(p[0]-440)*3.1,278+(p[2]+15)*3.1)
def dot(p,lab,dx=12,dy=-40,col=blue):
 x,y=pnt(p);dr.ellipse((x-7,y-7,x+7,y+7),fill=col,outline='white',width=2);text(x+dx,y+dy,lab,25,col)
text(65,40,'广州东联络线 · 标准接口放样',49)
text(68,110,'B03S2｜按轨道方块数格，原朝向 X 东 / Z 南 / Y 上；原联络线线形不变。',29,muted)
card((55,175,2145,1160));text(85,195,'01  东侧：从标准 144 格直道末端定位',36)
# Exact endpoint and curve plan, rather than a generated illustration.
for xx in range(440,731,20):
 a,b=pnt((xx,0,-5)),pnt((xx,0,230));dr.line((a,b),fill='#e2e9e9',width=1)
for zz in range(0,231,20):dr.line((pnt((440,0,zz)),pnt((730,0,zz))),fill='#e2e9e9',width=1)
for z in [30,36]:dr.line((pnt((440,33,z)),pnt((720,33,z))),fill='#7f929b',width=6)
for c in s['curves']:
 if c['module']in ['E01','E02']:
  pts=[pnt(p)for p in c['points']if p[2]<=230]
  if len(pts)>1:dr.line(pts,fill=blue if c['module']=='E01'else indigo,width=7)
dot((462,33,30),'P0',-44,18,ink);dot((464,33,30),'P1',8,-41,blue)
dot((624,23,6),'P2',-25,-44,blue);dot((688,23,70),'P3',-70,3,blue)
dot((654,33,36),'R0',-25,18,indigo);dot((694,33,76),'R1',18,8,indigo)
text(130,1045,'北 ↑　　右为东 →',28,muted);text(130,1090,'俯视按比例绘制；点名代表轨道方块，不是蓝图外框。',25,muted)
notes=[('P0 · 施工第 0 格','东侧 144 格直道最后一排的北股轨道。',ink),
 ('P1 · E01 出岔点','从 P0 向东 2 格；横移 0，高差 0。',blue),
 ('P2 · 北侧外弯控制点','从 P1 向东 160、向北 24、向下 10。',blue),
 ('P3 · 下穿后转向控制点','从 P2 向东 64、向南 64；同高。',blue),
 ('R0 · E02 南转西回接点','从 P0 向东 192、向南 6；同高。',indigo),
 ('R1 · E02 回弯控制点','从 R0 向东 40、向南 40；同高。',indigo)]
for i,(title,body,col)in enumerate(notes):
 y=280+i*119;text(1125,y,title,31,col);text(1125,y+46,body,27)
text(1125,1020,'蓝图外框：E01 相对 P0 = 西3 / 北28 / 下33',26)
text(1125,1065,'蓝图外框：E02 相对 P0 = 东32 / 北4 / 下33',26)
text(1125,1110,'E01 向站内覆盖 4 排；无需再空出一段。',26,muted)
card((55,1190,2145,1705));text(85,1210,'02  南侧：补接 144 + 144 + 2，再接南枢纽',36)
text(90,1270,'Q0 = 南侧原 144 格直道末端的西股轨道。下图为沿南向的累计尺寸链。',28,muted)
x0=190;scale=5.1;y=1370
for start,end,label,col in [(1,144,'A01 · 144 格',blue),(145,288,'A02 · 144 格',green),(289,290,'A03',gold)]:
 xa=x0+(start-1)*scale;xb=x0+end*scale;dr.rectangle((xa,y,xb,y+70),fill=col)
 if end-start>2:text(xa+30,y+16,label,29,'white')
for index,label in [(0,'Q0 / 第0格'),(144,'第144格'),(288,'第288格')]:
 x=x0+index*scale;dr.line((x,y-12,x,y+90),fill=ink,width=2);text(x-62,y+98,label,25)
x=x0+290*scale;dr.line((x,y-25,x,y+70),fill=gold,width=4);text(x+28,y-26,'A03：第289–290格',27,gold);text(x+28,y+32,'S01：第291格起',29,green)
text(90,1560,'A01：Z364–507　　A02：Z508–651　　A03：Z652–653　　南枢纽首排：Z654',27)
text(90,1610,'相对原站，双股轨道 X = 122 / 128，Y = 7；补接件统一截面 15 × 8 格。',27)
text(90,1652,'已有完整 B03 正线时不重复补接。三件从完整展示中提取，桥面外观沿用 B03。',25,muted)
card((55,1735,2145,2340));text(85,1755,'03  先核对两个基准，再按端点拼接',36)
text(90,1823,'从 P0 向西 340、向南 333、向下 26，应当到达 Q0。',34,blue)
text(90,1878,'若现场不满足这组关系，应先检查车站、收束段和原 144 格直道的摆放。',28)
text(90,1940,'数格标准',31)
text(90,1987,'• 以 F3 的目标轨道方块整数坐标为准，不用人物脚下坐标或轨道外沿。',28)
text(90,2034,'• 144 格模块含首尾共 144 个位置，首尾坐标差 143；下一件起点再向外 1 格。',28)
text(90,2081,'• 斜接缝是“西 1 + 南 1”，不是沿斜线量 1 米；两股轨道分别核对。',28)
text(90,2128,'• 主线轨道锚点间距为 6 格；沿用原模板，不自行把坐标间距改为 3。',28)
text(90,2175,'• 只对齐外框不够：还要核对定位轨道的高度、方向和另一股轨道。',28)
text(90,2222,'• 每个文件的轨道定位点、局部坐标和世界放置坐标见配套 HTML / CSV。',28)
text(90,2280,'本页为这套 B03 的固定接口标准，尚未进行游戏内蓝图炮打印验证。',27,muted)
text(70,2395,'P0 相对原站：(462, 33, 30)　　Q0 相对原站：(122, 7, 363)　｜　尺寸均为格',28,muted)
png=D/'GuangzhouEast_Interface_Standard.png';temp=png.with_suffix('.partial');im.save(temp,format='PNG');os.replace(temp,png)

basepath=R/'GuangzhouEast_Print_Guide_B03S1.html'
if not basepath.exists():basepath.write_bytes((D/'GuangzhouEast_Print_Guide.html').read_bytes())
page=basepath.read_text();page=page.replace('B03S1 · Minecraft','B03S2 · Minecraft').replace('联络线拆开，打印更好安排','联络线 · 分段打印与标准接法')
page=page.replace('保留这次认可的 B03 线形，把东枢纽、南枢纽和中间直道分开。三角地的设施仅做用途建议，没有加入任何铁路蓝图。','按轨道方块定基准，明确每件向外多少格、横移多少格、抬高多少格。原七份联络线分件不变，本次补齐南侧 144＋144＋2 格连接段。')
page=page.replace('<span>61,119 方块原样拼合</span>','<span>原联络线 61,119 方块不变</span><span>新增南侧补接 3 件</span>')
rows=''.join(f'<tr><td>{a["id"]}</td><td>{esc.escape(a["instruction"])}</td><td class="coords">({", ".join(map(str,a["rail_pin_local"]))})</td></tr>'for a in s['anchors']if len(a['id'])>1)
seamrows=''.join(f'<tr><td>{j["a"]} → {j["b"]}</td><td class="coords">{tuple(j["pa"])}</td><td class="coords">{tuple(j["pb"])}</td><td class="coords">{tuple(j["delta"])}</td></tr>'for j in s['seams'])
curverows=''.join(f'<tr><td>{c["module"]} / {c["id"]}</td><td class="coords">{tuple(c["p"])}</td><td class="coords">{tuple(c["q"])}</td><td class="coords">{tuple(c["delta"])}</td></tr>'for c in s['curves'])
section='''<section id="interfaceStandard" class="datumSection"><div class="eyebrow">先按这张表施工 · B03S2 新增</div><h2>从轨道端点数格，不从蓝图外框猜位置</h2>
<p><b>P0：</b>东侧原 144 格直道末端的北股轨道。<b>Q0：</b>南侧原 144 格直道末端的西股轨道。两点都取目标轨道方块的整数坐标，原方块算第 0 格，紧挨着的新方块算第 1 格。</p>
<div class="notice"><b>上一版说明缺少的两个接口条件：</b>东侧 E01 向站内覆盖原直道末端 4 排；南侧 Q0 到南枢纽首排之间需补 290 个正线位置。现在补接件按 A01（144）＋A02（144）＋A03（2）提供。已经有完整 B03 正线时，无需重复补接。</div>
<p>北侧两个转向在本版分别属于 E01「西转南」和 E02「南转西」。以下同时标注出岔与回接，避免只凭“北边那个弯”选错一股。</p>
<img class="datumSheet" src="@@DIAGRAM@@" alt="标准接口放样图：东侧出岔、北侧外弯与回接，南侧144加144加2的累计尺寸链，以及基准核对规则">
<div class="buttons"><button id="datumPNG">下载接口放样图</button><button id="datumCSV">下载接口坐标 CSV</button><a href="https://chatgpt.com/library?file_id=libfile_47b851f846d881918b4e62554a7a4b1f&amp;account_id=personal">完整分段包（含三件补接）</a></div>
<h2>输入一个实际轨道坐标，算出每件该放哪里</h2>
<p>选择你能准确找到的轨道定位点，输入 F3 目标方块坐标。表中同时给出轨道点与蓝图最小角；按原朝向放置，不要单独旋转分件。默认数值仅演示原站原点为 (0,0,0) 的情况。</p>
<div class="panel anchor"><label>已知轨道点<select id="datumRef"></select></label><label>世界 X<input id="datumX" type="number" step="1" value="462"></label><label>世界 Y<input id="datumY" type="number" step="1" value="33"></label><label>世界 Z<input id="datumZ" type="number" step="1" value="30"></label><label>打印组合<select id="datumSet"><option value="parts">七件联络线＋三件补接</option><option value="groups">三组联络线＋三件补接</option></select></label></div>
<p id="datumReferenceNote" class="muted"></p><div class="notice" id="datumCrosscheck"></div>
<div class="tablewrap"><table><thead><tr><th>文件</th><th>定位轨道世界坐标</th><th>蓝图最小角世界坐标</th><th>下载</th></tr></thead><tbody id="datumTable"></tbody></table></div>
<h2>逐件接法</h2><p>下表里的固定数值都以原站坐标系为准；游戏内可直接用上方换算结果。定位轨道在 NBT 内的坐标，从该件最小角起算。</p>
<div class="tablewrap"><table><thead><tr><th>分件</th><th>从哪里数、数多少</th><th>定位轨道在 NBT 内 X / Y / Z</th></tr></thead><tbody>@@ROWS@@</tbody></table></div>
<details><summary>展开：每一股轨道接缝的精确坐标</summary><p>坐标为轨道方块位置。所有列出的接缝均不重叠，下一轨道块只相邻一步。斜线为 X 与 Z 各变一格；切缝位置可能错开一格，须按两股各自端点核对，不能把两股强行裁到同一排。</p><div class="tablewrap"><table><thead><tr><th>两件</th><th>前件轨道方块</th><th>后件轨道方块</th><th>ΔX / ΔY / ΔZ</th></tr></thead><tbody>@@SEAMS@@</tbody></table></div></details>
<details><summary>展开：全部曲线端点尺寸链</summary><p>这些是端点方块的坐标差，不是弧长，也不是一段直坡的长度。曲线已包含在对应蓝图中，通常无需现场重拉；保留该表用于放样复核。</p><div class="tablewrap"><table><thead><tr><th>曲线 / 所属件</th><th>起点</th><th>终点</th><th>ΔX / ΔY / ΔZ</th></tr></thead><tbody>@@CURVES@@</tbody></table></div></details>
<p class="muted">三件补接从 B03 完整展示的南侧正线提取，轨道接口与原 144 格模块相接；它们不是原 standard_144 文件的改名副本。新旧文件的坐标与方块均已回读核对，游戏内打印与信号试跑仍待验证。</p></section>'''
newfiles={a['id']:base64.b64encode((D/a['file']).read_bytes()).decode()for a in s['extra_modules']}
newfiles['datum_png']=base64.b64encode(png.read_bytes()).decode();newfiles['datum_csv']=base64.b64encode((D/'GuangzhouEast_Interface_Coordinates.csv').read_bytes()).decode()
for key,value in {'DIAGRAM':'data:image/png;base64,'+newfiles['datum_png'],'ROWS':rows,'SEAMS':seamrows,'CURVES':curverows}.items():section=section.replace('@@'+key+'@@',value)
page=page.replace('<main>','<main>'+section,1)
css='.datumSection{padding-bottom:35px;margin-bottom:40px;border-bottom:2px solid #c5d7dc}.datumSheet{display:block;width:100%;height:auto;border:1px solid #d6e0df;border-radius:10px;margin:20px 0}.datumSection select{max-width:min(100%,510px)}.datumSection .anchor label{max-width:100%}.datumSection .buttons a{align-self:center}@media(max-width:720px){.datumSection .anchor label{width:100%}.datumSection .anchor input{width:100%}.datumSection .anchor select{width:100%}}'
page=page.replace('</style>',css+'</style>',1)
data={k:s[k]for k in ['datums','datum_Q0_minus_P0','anchors','extra_modules']}
script='''<script>
const DOCKING=@@DATA@@;Object.assign(FILES,@@NEWFILES@@);
const datumOptions=[...DOCKING.datums,...DOCKING.anchors.filter(a=>a.id!=='E01').map(a=>({id:a.id,name:a.id+' · '+a.name+' · 定位轨道',p:a.rail_pin_station}))];
document.getElementById('datumRef').innerHTML=datumOptions.map(a=>`<option value="${a.id}">${a.name}</option>`).join('');
function datumCoords(){const ref=datumOptions.find(a=>a.id===$('datumRef').value),raw=['datumX','datumY','datumZ'].map(k=>$(k).value),val=raw.map(Number);if(raw.some(v=>v.trim()==='')||val.some(v=>!Number.isInteger(v))){$('datumTable').innerHTML='<tr><td colspan="4">请输入整数轨道方块坐标。</td></tr>';return;}
 const world=p=>p.map((v,i)=>v+val[i]-ref.p[i]),fmt=p=>'('+p.join(', ')+')';const group=$('datumSet').value==='groups';
 const list=DOCKING.anchors.filter(a=>a.id.startsWith('A')||(group?a.id.length===1:a.id.length>1));
 $('datumTable').innerHTML=list.map(a=>`<tr data-datum-row="${a.id}"><td><b>${a.id} · ${a.name}</b></td><td class="coords railWorld">${fmt(world(a.rail_pin_station))}</td><td class="coords originWorld">${fmt(world(a.origin))}</td><td><button data-interface-download="${a.id}">NBT</button></td></tr>`).join('');
 $('datumReferenceNote').textContent='当前基准：'+ref.name+'；该轨道点在原站坐标系为 '+fmt(ref.p)+'。世界最小角 = 已知轨道世界坐标 + 分件原点 − 基准轨道原坐标。';
 const p=world(DOCKING.datums[0].p),q=world(DOCKING.datums[1].p);$('datumCrosscheck').innerHTML='<b>现场交叉核对：</b>P0 应在 <span class="coords">'+fmt(p)+'</span>，Q0 应在 <span class="coords">'+fmt(q)+'</span>。两点关系固定为：西 340、南 333、下 26。若不吻合，先核对原站、收束段与 144 格直道。';}
for(const id of ['datumRef','datumX','datumY','datumZ','datumSet'])$(id).addEventListener('input',datumCoords);
document.addEventListener('click',e=>{const b=e.target.closest('[data-interface-download]');if(!b)return;const a=DOCKING.anchors.find(a=>a.id===b.dataset.interfaceDownload);download(a.id,a.file.split('/').pop());});
$('datumPNG').onclick=()=>download('datum_png','GuangzhouEast_Interface_Standard.png','image/png');$('datumCSV').onclick=()=>download('datum_csv','GuangzhouEast_Interface_Coordinates.csv','text/csv;charset=utf-8');datumCoords();window.interfaceReady=true;
</script>'''.replace('@@DATA@@',json.dumps(data,ensure_ascii=False,separators=(',',':'))).replace('@@NEWFILES@@',json.dumps(newfiles,separators=(',',':')))
page=page.replace('</html>',script+'</html>')
# Rebuild the embedded font subset to cover the newly added construction labels.
page=re.sub(r'@font-face\{font-family:GuideCJK;.*?\}body,svg text\{[^}]*\}','',page,flags=re.S)
webfont=TTFont(font);options=subset.Options();options.name_IDs=['*'];options.name_legacy=True;options.name_languages=['*'];ss=subset.Subsetter(options=options);ss.populate(text=''.join(sorted(set(page))));ss.subset(webfont);webfont.flavor='woff';buf=io.BytesIO();webfont.save(buf)
fontcss='@font-face{font-family:GuideCJK;src:url(data:font/woff;base64,'+base64.b64encode(buf.getvalue()).decode()+') format("woff");font-weight:100 900;font-display:swap;}body,svg text{font-family:GuideCJK,system-ui,sans-serif;}'
page=page.replace('</style>',fontcss+'</style>',1);dest=D/'GuangzhouEast_Print_Guide.html';temp=dest.with_suffix('.partial');temp.write_text(page);os.replace(temp,dest)
instructions='''B03S2 标准接口补充
本次新增的是施工定位说明及南侧补接直道。原七件联络线和三份整组 NBT 全部保持原字节。
P0：东侧原144格直道最后一排的北股轨道；相对原站 (462,33,30)。
Q0：南侧原144格直道最后一排的西股轨道；相对原站 (122,7,363)。
P0 向西340、向南333、向下26，应当到 Q0。以轨道目标方块坐标为准，勿用人物坐标。
已有末端为第0格，新轨道从第1格开始。144个方块位置首尾差143。
东侧：E01外框相对P0为西3/北28/下33，覆盖原直道末端4排；出岔点在P0东2。
北侧外弯：出岔点再东160/北24/下10到P2；再东64/南64/同高到P3。
E02回接点在P0东192/南6/同高；其外框相对P0为东32/北4/下33。
南侧：A01为Q0向南第1–144格；A02为第145–288格；A03为第289–290格；S01第一排正线在第291格。
A01/A02/A03统一轨道局部坐标：西股(4,7,0)、东股(10,7,0)，截面15×8；A03包括未填充的下部空间。
这三件来自完整B03正线，已建完整B03正线时不用重复打印。并非原standard_144模板的直接复制。
蓝图均按原朝向使用。不要把外框位置当轨道端点，不要单件旋转，不要把稀疏NBT空白当清空指令。
HTML含逐件轨道锚点、世界坐标换算、全部18处普通轨道接缝与12段曲线端点尺寸。
Minecraft实机打印未执行；请先在副本对接口和信号进行试跑。
'''
(D/'标准接法说明.txt').write_text(instructions)
delivery={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.rglob('*')if p.is_file()and p.suffix not in ['.zip','.partial']}
(R/'delivery_manifest.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2))
print(json.dumps({'guide_bytes':dest.stat().st_size,'diagram':png.name,'extra_modules':3,'existing_nbt_unchanged':True}))
