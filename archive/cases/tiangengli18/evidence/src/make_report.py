from pathlib import Path
import sys,json,base64,io,html,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
run=sys.argv[1];OUT=Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
R=C/'runs'/run;P=C/'review/previews'/run;p=json.loads((R/'params_used.json').read_text());qa=json.loads((R/'checks.json').read_text());world=json.loads((R/'world_check.json').read_text())
B=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000)).blocks
fontpath=ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'
def font(n):return ImageFont.truetype(str(fontpath),n)
def dataimage(path,maxsize=(1800,1800),quality=90):
 im=Image.open(path).convert('RGB');im.thumbnail(maxsize);f=io.BytesIO();im.save(f,format='JPEG',quality=quality,optimize=True)
 return 'data:image/jpeg;base64,'+base64.b64encode(f.getvalue()).decode()
def fig(path,title):return '<figure><img loading="lazy" src="'+dataimage(path)+'" alt="'+html.escape(title)+'"><figcaption>'+title+'</figcaption></figure>'

# Labels on the final NBT's true orthographic top view, using recorded camera bounds.
top=Image.open(P/'top_day.png').convert('RGB');draw=ImageDraw.Draw(top)
cams={q['id']:q for q in json.loads((P/'cameras.json').read_text())};cam=cams['top_day'];sx,sz=cam['spanX'],cam['spanZ'];tx,tz=cam['target'][0],cam['target'][2]
for h in p['buildings']:
 x=(h['x']+h['w']/2-tx+sx/2)/sx*top.width;z=(h['z']+h['d']/2-tz+sz/2)/sz*top.height
 label=h['id'];color='#bb6844' if h['kind'] in ['brick','frame','hybrid'] else '#796745' if h['kind']=='old' else '#2b5d55'
 draw.rounded_rectangle((x-29,z-18,x+29,z+18),radius=5,fill=color);draw.text((x,z),label,font=font(21),fill='white',anchor='mm')
top.save(P/'top_labeled.png')

zh={'finished':'成宅','old':'旧宅','frame':'裸框架','brick':'砌筑中','hybrid':'下层入住，顶层待续建'}
plans=[];house_panels=[]
for h in p['buildings']:
 cards=[];x,z,w,d,g=h['x'],h['z'],h['w'],h['d'],h['base']
 for level in range(h['floors']):
  fy=g+1+level*6;scale=15;im=Image.new('RGB',((w+4)*scale,(d+4)*scale+55),'#eeeadd');dr=ImageDraw.Draw(im)
  dr.text((20,12),f'{h["id"]} · {level+1}F',font=font(22),fill='#254237')
  for zz in range(z-2,z+d+2):
   for xx in range(x-2,x+w+2):
    found=next((B[xx,y,zz] for y in range(fy+2,fy-2,-1) if (xx,y,zz) in B),None)
    if found is None:continue
    c=tuple(states.color(found));X=(xx-x+2)*scale;Z=(zz-z+2)*scale+55
    dr.rectangle((X,Z,X+scale-1,Z+scale-1),fill=c)
  path=P/f'{h["id"]}_F{level+1:02}.png';im.save(path);plans.append(dict(house=h['id'],floor=level+1,image=path.name,cut_y=fy+2))
  cards.append(fig(path,f'{level+1}层 · 方块俯视切片'))
 house_panels.append(f'<details><summary>{h["id"]}　{zh[h["kind"]]}　<span>{w} × {d} 格 / {h["floors"]} 层</span></summary><div class="plans">'+''.join(cards)+'</div></details>')
(P/'plans.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2))

items=[('village_close','村心近景'),('village_night','村心夜景'),('top_labeled','总平面与编号'),('se_day','东南 · 日景'),('se_night','东南 · 夜景'),('sw_day','西南 · 日景'),('sw_night','西南 · 夜景'),('ne_day','东北 · 日景'),('ne_night','东北 · 夜景'),('nw_day','西北 · 日景'),('nw_night','西北 · 夜景')]
gallery={key:dict(src=dataimage(P/(key+'.png')),label=title) for key,title in items}
source=Path(sys.argv[3]);gallery['source_plan']=dict(src=dataimage(source),label='P3 原布局图 · 设计来源')
options=''.join(f'<option value="{key}">{title}</option>' for key,title in items)+ '<option value="source_plan">对照 P3 原图</option>'
gallery_json=json.dumps(gallery,ensure_ascii=False).replace('<','\\u003c')
detail=''.join(fig(P/(name+'.png'),label) for name,label in [('field_close','不同田块、成长阶段与休耕区'),('greenhouse_close','4座拱棚 · 玻璃与支架近似薄膜构造'),('construction','R04 · 框架、楼梯与脚手架'),('home_cut','R01 首层剖切 · 起居、睡眠与交通空间')])
rows=''.join(f'<tr><td>{h["id"]}</td><td>{zh[h["kind"]]}</td><td>{h["floors"]}F</td><td>{dict(core="村心",transition="过渡",outer="田边")[h["group"]]}</td></tr>' for h in p['buildings'])
doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>田埂里 · P3 建造版</title><style>
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f2efe4;color:#243d32;font-family:system-ui,-apple-system,"Microsoft YaHei",sans-serif;font-size:16px;line-height:1.8}a{color:inherit}header{padding:54px max(5vw,22px) 37px;background:#263f34;color:#f7f2df}.eyebrow{font-size:12px;letter-spacing:.18em;color:#bbc9a7}h1{font-size:clamp(42px,7vw,88px);line-height:1.2;margin:18px 0 22px;font-weight:500}header p{max-width:820px;color:#e2e7d7}.stats{display:flex;gap:40px;flex-wrap:wrap;margin-top:30px}.stats b{font-size:30px;font-weight:500}.stats small{display:block;font-size:12px;color:#c6d1b9}nav{display:flex;gap:26px;flex-wrap:wrap;padding:14px 5vw;background:#e7e7d9;position:sticky;top:0;z-index:5;border-bottom:1px solid #c8cdbb}nav a{text-decoration:none;font-size:14px}main{max-width:1440px;padding:22px;margin:auto}section{padding:24px 0 40px;scroll-margin-top:62px}h2{font-weight:500;font-size:29px;line-height:1.4;margin:5px 0 18px}p{max-width:1000px}.muted,figcaption{color:#68725e;font-size:14px}.tools{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:0 0 14px}select,button,.button{padding:9px 14px;border:1px solid #aeb9a1;background:#faf8f0;color:#2d4d3d;font:inherit;border-radius:4px;text-decoration:none;cursor:pointer}select{max-width:100%}button.active{background:#355746;color:white}figure{margin:0;background:#fffdf8;overflow:hidden;border:1px solid #d8dacb;border-radius:6px}figure img{display:block;width:100%}figcaption{padding:12px 18px}.hero{height:min(72vw,810px);min-height:310px;background:#b1bbaa;display:flex;align-items:center;justify-content:center;overflow:auto}.hero img{display:block;max-width:100%;max-height:100%;object-fit:contain}.hero img.full{max-width:none;max-height:none;width:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.notes{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:25px 0}.note{padding:22px;background:#e7e8d9;border-top:3px solid #77825b}.note b{font-size:19px;font-weight:500;display:block;margin-bottom:10px}.note p{font-size:14px;line-height:1.8;margin:0}.banner{padding:18px 22px;background:#e2e7d4;border-left:3px solid #63794c;margin:20px 0}.plans{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding:18px 0}.plans figure img{image-rendering:auto}.plans figure{max-width:500px}details{border-top:1px solid #c7cdbb;padding:16px 0}summary{cursor:pointer;font-weight:550}summary span{font-size:13px;font-weight:400;color:#65745f;margin-left:14px}table{width:100%;border-collapse:collapse;background:#faf8f0}td,th{text-align:left;padding:9px 16px;border-bottom:1px solid #d7dbcd}code{background:#dfe4d4;padding:2px 5px;border-radius:3px;word-break:break-word}footer{padding:25px 0;border-top:1px solid #c7cdbb;color:#65745f;font-size:13px}.two{columns:2;column-gap:35px}.mobile-note{display:none}@media(max-width:760px){main{padding:14px}header{padding-top:35px}.grid,.notes{grid-template-columns:1fr}.plans{grid-template-columns:1fr 1fr}.stats{gap:25px}.hero{height:68vw;min-height:250px}.two{columns:1}nav{gap:18px}.tools{font-size:14px}summary span{display:block;margin:4px 0}.mobile-note{display:block}}
</style></head><body><header><div class="eyebrow">HAIBARA’S ARCHITECT · TIANGENGLI · P3 BUILD</div><h1>田埂里</h1><p>村心成组，田边散开。沿用上一版的18栋疏密布局，把房屋、农田、村路和农业棚实际写成方块；旧宅、成宅与施工中的楼房共同组成生活中的村落。</p><div class="stats"><div><b>18</b><small>栋房屋 / 9成宅 · 5旧宅 · 4施工</small></div><div><b>32</b><small>片耕作区 / 分区成长与收割</small></div><div><b>6</b><small>座农业棚 / 4拱棚 · 2育苗棚</small></div><div><b>1.21.1</b><small>Minecraft Java 存档</small></div></div></header><nav><a href="#view">昼夜预览</a><a href="#changes">随机与灯光</a><a href="#details">局部细节</a><a href="#homes">逐栋逐层</a><a href="#world">打开存档</a></nav><main>
<section id="view"><div class="tools"><label for="viewSelect">视角</label><select id="viewSelect">__OPTIONS__</select><button id="dayBtn" class="active">日景</button><button id="nightBtn">夜景</button><button id="zoomBtn">原尺寸</button><a class="button" id="downloadImage" download="Tiangengli18_View.jpg">下载当前图</a></div><figure><div class="hero"><img id="mainImage" src="__HERO__" alt="田埂里村心近景"></div><figcaption id="caption">村心近景</figcaption></figure><p class="muted">所有建造预览均由最终 NBT 读回生成；近似材质与离线照明，不是 Minecraft 客户端截图。东为 +X，北为 −Z；四个方向共用尺度和俯角。</p></section>
<section id="changes"><h2>变化落在不同的尺度上</h2><div class="notes"><div class="note"><b>聚落：保持疏密</b><p>8栋村心、4栋过渡、6栋田边。维持 P3 的位置、朝向与连通路网；宅前保留短接入和小门坪。R18增加暖色墙体、青色收口、蓝玻璃与屋顶遮棚。</p></div><div class="note"><b>农田：成片变化</b><p>原田块内分成大小不同的32片，行向、成熟度、少量缺苗和收割带各有变化。田边做短装运缺口，休耕地以连续土色斑块呈现；固定种子可重做同一结果。</p></div><div class="note"><b>照明：按使用安排</b><p>34个已使用楼层保留功能灯位；灯嵌在吊顶层，上方有楼板。入口和路口补灯，施工层与大田保持较暗。冷暖为材料意图，原版不产生真实彩色光传播。</p></div></div><p>建筑有1–4层的高低变化，保留局部L形、凹廊、防盗网、屋顶生活设施与施工脚手架。灯光、花槽、玻璃色差和屋顶遮棚采用独立固定种子，后续修改局部不会把全部随机结果重洗。</p></section>
<section id="details"><h2>田间生产与屋内生活</h2><div class="grid">__DETAILS__</div><p class="muted">拱棚以玻璃、铁件表达薄膜与骨架；育苗遮阳棚以薄活板门近似遮阳网，离线预览将其简化成薄板。家具为方块陈设，床与工作台不代表原生睡眠或容器功能。</p></section>
<section id="homes"><h2>打开每一栋，查看各层</h2><p>以下平面直接取自最终建筑方块。剖切显示楼板、隔墙、楼梯、家具与窗洞；灰色空白处不等于尚未建造，而是切片内的地面或空气。</p>__HOMES__<details><summary>18栋分布与状态表</summary><table><thead><tr><th>编号</th><th>状态</th><th>层数</th><th>分组</th></tr></thead><tbody>__ROWS__</tbody></table></details></section>
<section id="world"><h2>存档已单独打包</h2><ol><li>解压 <strong>Tiangengli18_World_1.21.1.zip</strong>。</li><li>把内含 <code>level.dat</code> 和 <code>region</code> 的 <code>Tiangengli18</code> 文件夹放入所用启动器实例的 <code>.minecraft/saves</code>。</li><li>用 <strong>Java 1.21.1</strong> 打开世界。出生点在村中主路，坐标约 <code>-15 64 -9</code>，创造模式、允许指令。</li></ol><p><code>/time set night</code> 查看夜景；<code>/time set day</code> 返回白天。为保留本次成熟度分布，作物随机生长默认冻结；需要恢复生长时用 <code>/gamerule randomTickSpeed 3</code>。</p><div class="banner"><strong>检查结果：</strong>18户门口净空、单一连通路网、34个使用楼层灯位、24,950格作物承托与灌溉范围检查通过。存档360个建筑区块已读回，对4,423,680个位置逐格比较，方块状态与空气位置均吻合。</div><p>本次未运行 Minecraft 客户端或服务端。存档首次加载需由游戏重算光照；玩家完整楼梯碰撞、实际光照与交互仍待游戏内验收。这版是可继续返工的首轮建造，不把文件检查当作游戏验收。</p><details><summary>可复跑工程与来源</summary><p>工程包含最终 NBT、P3空间参数、原有13栋与历史房型来源、各阶段检查、构件归属、种子、建造脚本及最终预览。P3_B1—B3保留为修订记录，最终为 <strong>__RUN__</strong>。这次依据已存在的 P3 图片与方块资料接续，没有重新观看早期参考视频。</p><p>场地 <strong>320 × 288</strong> 格；NBT包围盒 <strong>320 × 48 × 288</strong>。世界平移 <code>(-160,60,-144)</code>。NBT是稀疏结构文件，不会自动清除其他世界中的空气位置；整片体验优先使用附带存档。</p><p>最终 NBT SHA-256：<code>__HASH__</code></p></details></section><footer>2026-10-29 · 田埂里 / P3 建造版 · 完整建造与复核记录随工程包提供。</footer></main><script>
const gallery=__GALLERY__;const select=document.getElementById('viewSelect'),img=document.getElementById('mainImage');
function show(key){select.value=key;img.src=gallery[key].src;img.alt=gallery[key].label;document.getElementById('caption').textContent=gallery[key].label;document.getElementById('downloadImage').href=gallery[key].src;document.getElementById('downloadImage').download='Tiangengli18_'+key+'.jpg';const night=key.includes('night');document.getElementById('nightBtn').classList.toggle('active',night);document.getElementById('dayBtn').classList.toggle('active',!night)}
select.addEventListener('change',()=>show(select.value));document.getElementById('zoomBtn').onclick=()=>{const z=img.classList.toggle('full');document.getElementById('zoomBtn').textContent=z?'适应画面':'原尺寸'};
function light(night){let key=select.value;if(key.startsWith('village_'))key=night?'village_night':'village_close';else if(/^(se|sw|ne|nw)_/.test(key))key=key.split('_')[0]+(night?'_night':'_day');else key=night?'se_night':'se_day';show(key)}
document.getElementById('dayBtn').onclick=()=>light(false);document.getElementById('nightBtn').onclick=()=>light(true);show('village_close');
</script></body></html>'''
doc=doc.replace('24,950',format(qa['crop_count'],','))
for key,val in {'OPTIONS':options,'HERO':gallery['village_close']['src'],'DETAILS':detail,'HOMES':''.join(house_panels),'ROWS':rows,'RUN':run,'HASH':qa['source_nbt_sha256'],'GALLERY':gallery_json}.items():doc=doc.replace('__'+key+'__',val)
(OUT/'Tiangengli18.html').write_text(doc,encoding='utf-8')
# Compact visual card, assembled only from this final NBT's actual renders.
canvas=Image.new('RGB',(1800,1440),'#f2efe4');dr=ImageDraw.Draw(canvas)
dr.text((50,26),'田埂里',font=font(66),fill='#294337');dr.text((310,43),'18栋 · P3 建造版',font=font(36),fill='#53674b')
dr.text((55,115),'村心成组，田边散开。32片耕作区 · 6座农业棚 · Java 1.21.1',font=font(26),fill='#6a765f')
im=Image.open(P/'village_close.png');im.thumbnail((1700,1060));canvas.paste(im,((1800-im.width)//2,177))
dr.text((55,1270),'住人的楼层亮灯，田地保持夜晚的安静。',font=font(29),fill='#294337')
dr.text((55,1323),'最终方块模型预览 · 近似材质与光照 · 非游戏客户端截图',font=font(23),fill='#6a765f')
canvas.save(OUT/'Tiangengli18_Preview.jpg',quality=92,optimize=True)
print(json.dumps({'html_bytes':(OUT/'Tiangengli18.html').stat().st_size,'floor_plans':len(plans),'gallery_views':len(gallery)},ensure_ascii=False))
