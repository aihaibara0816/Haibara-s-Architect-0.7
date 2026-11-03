from pathlib import Path
import sys,json,math,base64,html,io,collections,hashlib,zipfile,os,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'deps'),str(P/'src')]
import nbtlib as n
from link_geometry import read_connection
R=P/'runs/B03S1';D=P/'deliverables/B03S1';B=P/'runs/B03'
m=json.loads((R/'manifest.json').read_text());qa=json.loads((R/'validation.json').read_text());plan=json.loads((R/'triangle_proposal.json').read_text());owners=json.loads((R/'parts_owner.json').read_text());spec=json.loads((B/'spec.json').read_text());assert not qa['errors']
font=P/'research/dongguanxi/NotoSansCJKsc-Regular.otf';ft=lambda size:ImageFont.truetype(str(font),size)
colors={'E01':'#177d9a','E02':'#465e99','M01':'#d4a64c','M02':'#be8729','M03':'#9d641d','S01':'#6a9484','S02':'#356a58'}
ink='#213949';muted='#617784';light='#f4f6f3'
full=n.load(B/'GuangzhouEast_Complete.nbt');off=np.array(spec['variants'][0]['origin_in_station_coordinates']);segments=collections.defaultdict(list);curves=collections.defaultdict(list)
for e in full['blocks']:
 st=full['palette'][int(e['state'])]
 if str(st['Name'])!='create:track':continue
 p=np.array(e['pos'],int)+off;key=','.join(map(str,p));group=owners.get(key,'context');axis=np.array({'xo':[1,0,0],'zo':[0,0,1],'nd':[-1,0,1],'pd':[1,0,1]}[str(st['Properties']['shape'])])
 segments[group].append(((p+[.5,0,.5]-axis*.5)[[0,2]],(p+[.5,0,.5]+axis*.5)[[0,2]]))
 for c in e.get('nbt',{}).get('Connections',[]):
  if c['Primary']:curves[group].append(read_connection(p,c,321)[:,[0,2]])
foot=collections.defaultdict(set)
for k,id in owners.items():x,y,z=map(int,k.split(','));foot[id].add((x,z))
# Compress exact projected occupied cells into horizontal runs.
runs={}
for id,cells in foot.items():
 rows=collections.defaultdict(list)
 for x,z in cells:rows[z].append(x)
 result=[]
 for z,xs in rows.items():
  xs=sorted(xs);start=prev=xs[0]
  for x in xs[1:]:
   if x>prev+1:result.append((start,z,prev-start+1));start=x
   prev=x
  result.append((start,z,prev-start+1))
 runs[id]=result
# Interactive vector plan, with each module drawn from its actual final-NBT rails.
svg=['<svg id="map" viewBox="-350 -180 1120 1140" role="img" aria-label="广州东分段和三角地区划，北向上">','<rect x="-350" y="-180" width="1120" height="1140" fill="#f4f6f3"/>','<g stroke="#dce4e4" stroke-width=".8">']
for x in range(-350,751,50):svg.append(f'<path d="M{x},-160V940"/>')
for z in range(-150,951,50):svg.append(f'<path d="M-340,{z}H750"/>')
svg+=['</g>','<rect x="0" y="0" width="150" height="220" fill="#d9e3e9" stroke="#7a96a7" stroke-width="2"/>','<g class="landuse-layer" style="display:none">']
poly=lambda pts:' '.join(f'{x},{z}'for x,z in pts)
for zone in plan['spatial_spec']['zones']:
 svg.append(f'<polygon data-zone="{zone["id"]}" points="{poly(zone["polygon"])}" fill="{zone["color"]}" stroke="#82948f" stroke-width="1.5"/>')
for road in plan['spatial_spec']['roads']:
 svg.append(f'<polyline points="{poly(road["path"])}" fill="none" stroke="#9ba5a4" stroke-width="{road["width"]}" stroke-linejoin="round"/>')
svg.append('</g>')
for id in ['context',*colors]:
 col=colors.get(id,'#71828b');svg.append(f'<g class="railgroup" data-part="{id}">')
 if id in runs:
  d=''.join(f'M{x},{z}h{w}v1h-{w}z'for x,z,w in runs[id]);svg.append(f'<path d="{d}" fill="{col}" opacity=".20"/>')
 d=''.join(f'M{a[0]:.2f},{a[1]:.2f}L{b[0]:.2f},{b[1]:.2f}'for a,b in segments[id]);svg.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.0 if id=="context"else 2.9}"/>')
 for arr in curves[id]:svg.append(f'<polyline points="{poly(np.round(arr,3))}" fill="none" stroke="{col}" stroke-width="{2.0 if id=="context"else 2.9}"/>')
 svg.append('</g>')
svg+=['<g fill="#344f60" font-family="system-ui,sans-serif" font-size="17">','<text x="12" y="120">广州东</text>','<text x="12" y="143" font-size="12">原站 150 × 220</text>','<text x="-313" y="-22">← 长宁</text>','<text x="690" y="-20">东 →</text>','<text x="145" y="-125">北 ↑</text>','<text x="143" y="915">南薰 ↓</text>','</g>']
labelcoords={'E01':(478,-20),'E02':(613,164),'M01':(401,260),'M02':(316,354),'M03':(229,434),'S01':(156,627),'S02':(24,810)}
svg.append('<g id="partlabels" font-size="18" font-family="system-ui,sans-serif" font-weight="700">')
for id,(x,z)in labelcoords.items():svg.append(f'<text x="{x}" y="{z}" fill="{colors[id]}">{id}</text>')
svg.append('</g><g class="landuse-layer" style="display:none" font-size="25" font-weight="700" fill="#345161" font-family="system-ui,sans-serif">')
for zone in plan['spatial_spec']['zones']:
 center=np.mean(zone['polygon'],axis=0);svg.append(f'<text x="{center[0]}" y="{center[1]}" text-anchor="middle">{zone["id"]}</text>')
svg+=['<text x="438" y="9" font-size="13">北侧入口</text>','</g>','<rect id="selectionBox" style="display:none" fill="none" stroke="#1c4d66" stroke-width="2.3" stroke-dasharray="9 5"/>','</svg>']
svg=''.join(svg)
# Read-back based downloadable diagrams.
def diagram(kind):
 im=Image.new('RGB',(2200,1880),light);dr=ImageDraw.Draw(im);scale=1.18;ox=470;oz=360
 pt=lambda x,z:(round(ox+x*scale),round(oz+z*scale))
 title='广州东联络线 · 分段打印图' if kind=='parts' else '广州东三角地 · 用途布局建议'
 dr.text((62,35),title,font=ft(48),fill=ink)
 sub='B03S1｜线形冻结 · 三份整组 / 七份打印分件 · 所有曲线端点留在各自文件内' if kind=='parts' else '概念区划｜原铁路、桥墩位置不变；本页设施尚未生成建筑蓝图'
 dr.text((65,106),sub,font=ft(25),fill=muted)
 for x in range(-350,751,50):dr.line([pt(x,-160),pt(x,940)],fill='#dce4e4',width=1)
 for z in range(-150,951,50):dr.line([pt(-340,z),pt(750,z)],fill='#dce4e4',width=1)
 dr.rectangle((*pt(0,0),*pt(150,220)),fill='#d9e3e9',outline='#7997a5',width=3)
 if kind=='land':
  for zone in plan['spatial_spec']['zones']:dr.polygon([pt(x,z)for x,z in zone['polygon']],fill=zone['color'],outline='#91a39c',width=2)
  for road in plan['spatial_spec']['roads']:dr.line([pt(x,z)for x,z in road['path']],fill='#9ba5a4',width=round(road['width']*scale),joint='curve')
 for id,rr in runs.items():
  c=colors[id] if kind=='parts' else '#cbd4d3'
  # Light muted deck with darker rail on top.
  for x,z,w in rr:
   dr.rectangle((*pt(x,z),*pt(x+w,z+1)),fill='#d3dbd9' if kind=='parts' else '#d1d8d5')
 for id in ['context',*colors]:
  c=colors.get(id,'#7c8c94') if kind=='parts' else '#6f828b'
  for a,b in segments[id]:dr.line([pt(*a),pt(*b)],fill=c,width=3 if id!='context'else 2)
  for arr in curves[id]:dr.line([pt(x,z)for x,z in arr],fill=c,width=4 if id!='context'else 3)
 for x,z,label,size in [(10,108,'广州东',28),(10,136,'150 × 220',18),(-313,-25,'← 长宁',23),(682,-22,'东 →',22),(143,-144,'北 ↑',22),(143,905,'南薰 ↓',23)]:dr.text(pt(x,z),label,font=ft(size),fill=ink)
 if kind=='parts':
  for id,(x,z)in labelcoords.items():dr.text(pt(x,z),id,font=ft(25),fill=colors[id])
  for i,a in enumerate(m['recommended_parts']):
   y=190+i*162;col=colors[a['id']];dr.rounded_rectangle((1450,y,2140,y+142),14,fill='white',outline='#d8e1e2',width=2)
   dr.text((1480,y+15),a['id']+'  '+a['name'],font=ft(26),fill=col)
   x,h,z=a['size_xyz'];dr.text((1480,y+60),f'{x} × {h} × {z} 格（X / Y / Z）',font=ft(21),fill=ink)
   dr.text((1480,y+96),'放置偏移 '+str(tuple(a['origin_station_xyz'])),font=ft(20),fill=muted)
  lines=['偏移以原广州东站蓝图最小角为 (0,0,0)。','X 向东，Z 向南，Y 向上；各分件不要单独旋转。','直道三段按编号拼接；无需再补曲线连接件。','三份整组与七份分件内容相同，选择一套打印。','颜色区分文件，不表示列车方向。']
  for i,t in enumerate(lines):dr.text((1470,1360+i*38),t,font=ft(21),fill=muted)
 else:
  for zone in plan['spatial_spec']['zones']:
   c=np.mean(zone['polygon'],axis=0);dr.text(pt(c[0]-8,c[1]-12),zone['id'],font=ft(31),fill=ink)
  dr.text(pt(435,8),'北侧入口',font=ft(21),fill=ink)
  for i,a in enumerate(plan['spatial_spec']['zones']):
   y=185+i*210;dr.rounded_rectangle((1450,y,2140,y+192),14,fill='white',outline='#d8e1e2',width=2)
   dr.rectangle((1452,y+15,1463,y+174),fill=a['color']);dr.text((1480,y+15),a['id']+'  '+a['name'],font=ft(26),fill=ink)
   for j,t in enumerate(a['program']):dr.text((1480,y+62+j*34),'· '+t,font=ft(21),fill=muted)
  for i,t in enumerate(['采用一条内部主路和几条作业支路。','北侧先从高架下进入，避开现有桥墩。','作业区以硬质铺装为主，绿化放在入口与院内。','具体厂房、地形与城市道路仍需后续确定。']):dr.text((1470,1476+i*35),t,font=ft(21),fill=muted)
 dr.text((65,1590),'等比例平面 · 北向上',font=ft(25),fill=ink);dr.line((65,1650,65+round(scale*100),1650),fill=ink,width=5);dr.text((65,1672),'100 格',font=ft(22),fill=muted)
 note='分件合并后与 B03 的 61,119 个方块及方块实体完全一致；实体打印、区块加载和列车试跑仍待游戏确认。' if kind=='parts' else '此图仅提出功能区和道路意向。已对现有铁路检查平面退让与低位道路净空；未代替真实地形、建筑和交通设计。'
 dr.text((65,1780),note,font=ft(23),fill=muted)
 file=D/('GuangzhouEast_Print_Parts.png' if kind=='parts' else 'GuangzhouEast_Triangle_Proposal.png');tmp=file.with_suffix('.partial');im.save(tmp,format='PNG');os.replace(tmp,file);return file
partpng=diagram('parts');landpng=diagram('land')
allitems=m['recommended_parts']+m['whole_groups_alternative'];downloads={a['id']:base64.b64encode((D/a['file']).read_bytes()).decode()for a in allitems}
for key,path in [('parts_png',partpng),('land_png',landpng),('csv',D/'放置坐标.csv')]:downloads[key]=base64.b64encode(path.read_bytes()).decode()
# The guide uses no network assets, CDNs, service calls or embedded remote frame.
template='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州东 · 分段打印与三角地区划</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f6f3;color:#243e4d;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}header,main,footer{max-width:1440px;margin:auto;padding:28px}header{padding-top:38px}h1{font-size:36px;line-height:1.35;margin:10px 0}h2{font-size:25px}h3{margin:0 0 8px;font-size:19px}p{margin:8px 0}.eyebrow{font-size:13px;letter-spacing:.12em;color:#69818d}.muted,small{color:#687d87}.pills,.tabs,.buttons{display:flex;flex-wrap:wrap;gap:10px}.pills{margin:18px 0}.pills span{background:#e0e9e8;border-radius:6px;padding:8px 13px}button,select,input{font:inherit;border:1px solid #b7c7cd;border-radius:6px;padding:8px 12px;background:#fff;color:#294b5b}button{cursor:pointer}button.active,.primary{background:#1c6b85;border-color:#1c6b85;color:white}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:20px;margin-top:20px}.mapbox{border:1px solid #d4dfe0;border-radius:10px;overflow:hidden;background:#f4f6f3}svg{display:block;width:100%;height:auto;max-height:960px}.railgroup{transition:opacity .15s}.railgroup.dim{opacity:.13}.panel,.card{background:white;border:1px solid #d7e1e3;border-radius:9px;padding:20px;margin-bottom:15px}.partbtn{width:100%;text-align:left;margin:5px 0;padding:12px}.partbtn span{display:block;font-size:12px;color:#6a7f88}.partbtn.active span{color:#dbeef1}.detail{border-left:4px solid #2185a0}.anchor{display:flex;gap:10px;flex-wrap:wrap;align-items:end}.anchor label{display:flex;flex-direction:column;font-size:13px}.anchor input{width:120px}.anchor select{max-width:100%}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white;font-size:14px}th,td{border-bottom:1px solid #dce4e6;text-align:left;padding:12px 10px;vertical-align:top}th{background:#e6edef;white-space:nowrap}.coords{font-variant-numeric:tabular-nums;white-space:nowrap}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.notice{border-left:4px solid #c29c54;background:#f1ebdf;padding:14px 18px;margin:18px 0}.filename{overflow-wrap:anywhere;font-family:ui-monospace,monospace;font-size:13px}.mode-only{display:none}footer{font-size:13px;color:#6b808a}.siteplan{width:100%;border-radius:8px}li{margin:7px 0}a{color:#196b88}details{margin:16px 0}summary{cursor:pointer}@media(max-width:1000px){.workspace{grid-template-columns:1fr 315px}.grid{grid-template-columns:1fr 1fr}}@media(max-width:720px){header,main,footer{padding:18px}h1{font-size:29px}.workspace{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.anchor input{width:95px}svg{max-height:none}.panel{padding:15px}}
</style><header><div class="eyebrow">GAFAcraft · B03S1 · Minecraft 1.21.1 / Create 6.0.10</div><h1>联络线拆开，打印更好安排</h1><p>保留这次认可的 B03 线形，把东枢纽、南枢纽和中间直道分开。三角地的设施仅做用途建议，没有加入任何铁路蓝图。</p><div class="pills"><span>3 份整组蓝图</span><span>7 份打印分件</span><span>曲线两端不跨文件</span><span>61,119 方块原样拼合</span></div></header><main>
<div class="tabs" id="modes"><button data-mode="parts" class="active">七份打印分件</button><button data-mode="groups">三份整组蓝图</button><button data-mode="land">三角地用途建议</button></div>
<div class="workspace"><div class="mapbox">@@SVG@@</div><aside><div class="panel"><h3 id="listTitle">选择分件</h3><p class="muted" id="listHint">颜色表示文件划分。选择后显示该件外包范围。</p><div id="partList"></div><button id="showAll">显示全部</button></div><div class="panel detail" id="detail"></div></aside></div>
<section><h2>按同一个基准摆放</h2><p>输入你在世界中采用的蓝图最小角，表格会计算每份蓝图的放置坐标。X 向东、Z 向南、Y 向上；所有模块沿用原朝向。</p><div class="panel anchor"><label>坐标基准<select id="reference"><option value="station">原广州东站蓝图最小角</option><option value="complete">B03 完整展示蓝图最小角</option><option value="linkonly">B03 独立联络线最小角</option></select></label><label>世界 X<input id="wx" type="number" value="0" step="1"></label><label>世界 Y<input id="wy" type="number" value="0" step="1"></label><label>世界 Z<input id="wz" type="number" value="0" step="1"></label><button id="csv">下载相对坐标 CSV</button></div><p id="coordHint" class="muted"></p><div class="tablewrap"><table><thead><tr><th>编号 / 名称</th><th>尺寸 X × Y × Z</th><th>世界放置最小角</th><th>方块条目</th><th>下载</th></tr></thead><tbody id="coords"></tbody></table></div></section>
<section><h2>怎么选择打印</h2><div class="grid"><div class="card"><h3>日常打印：用七件版</h3><p>E01、E02 组成东枢纽；M01–M03 是中间直道；S01、S02 组成南枢纽。按编号摆放，原始方块没有重复或遗漏。</p></div><div class="card"><h3>整体搬运：用三组版</h3><p>东枢纽、南枢纽和中间直道各有一份完整文件。它们与七件版是同一套内容，选择一套即可。</p></div><div class="card"><h3>接缝留在普通直轨</h3><p>12 段曲线都保留双端数据，信号机与目标轨道也在同一件里。拼接不需要额外连接补丁，也不依赖分件之间合并轨道实体。</p></div></div><div class="notice">分件不会自动加载区块。尤其 S02 长约 381 格，保留了连续的外分、爬升和跨线曲线，仍需让当前施工范围与蓝图炮处于加载状态。若服务器加载距离较短，应调整加载位置；尚未进行实机打印测试。</div><ol><li>先确认 B03 原站、六收二收束段及 144 格直道的位置。这些前置建筑不在本次分件中。</li><li>以同一基准输入坐标，分别放置 E01、E02、M01、M02、M03、S01、S02。不要把每个文件的最小角都放到同一坐标，也不要单独旋转某件。</li><li>蓝图炮使用保留空白的打印方式；本包是稀疏 NBT，不应把整个外包矩形的空白破坏性地打印为空气。已有线路先在副本试放。</li><li>为当前模块准备材料，并用游戏内清单计算曲线轨道消耗；表中的方块条目数不是完整材料数量。</li><li>打印后核对普通直轨接缝、信号目标及两方向试跑，再接入自动运营。</li></ol><details><summary>为什么分段对这套模型有帮助</summary><p>原独立蓝图为 621 × 899 格，占用较大的坐标包围范围。新分件将直道缩到约 75–106 格的平面跨度，两个枢纽再按方向分开。枢纽的连续曲线不能只裁掉一半：本包以曲线完整性为边界，避免得到外部端点缺失的半段蓝图。</p><p>Create 6.0.10 的蓝图炮会在目标区块未加载时暂停，也会检查炮到蓝图锚点的距离（源码阈值 256 格，需小于该值）。这不是说“任何超过 256 格长的蓝图都不能打印”。具体服务器配置和加载方式仍需现场确认。</p><p class="muted">源码依据：<a href="https://github.com/Creators-of-Create/Create/blob/mc1.21.1-6.0.10/src/main/java/com/simibubi/create/content/schematics/cannon/SchematicannonBlockEntity.java">SchematicannonBlockEntity</a>；<a href="https://github.com/Creators-of-Create/Create/blob/mc1.21.1-6.0.10/src/main/java/com/simibubi/create/content/trains/track/TrackBlockEntity.java">TrackBlockEntity</a>。采用固定 6.0.10 源码核查，未宣称游戏验证。</p></details></section>
<section><h2>三角地：铁路服务与轻制造片区</h2><p>我更倾向将这里作为城市里的铁路运维大院和小型制造片区：靠车站安排办公、培训和公共服务，腹部放工坊与备件库，两个尖角留给设备和露天作业。这样能补齐工业体系，也保留将来接入城区的余地。</p><div class="grid" id="zoneCards"></div><div class="notice">图中的地块、层高和道路都是建议，尚未建造。暂按道路完成面 Y=1 做低位净空检查，北侧入口选在高架下、避开现有桥墩的位置；实际地形、城市道路和建筑方案还需后续确定。作业院以硬质铺装为主，入口、休息院与边界做少量绿化。</div><div class="buttons"><button id="partsPNG">下载分段图 PNG</button><button id="landPNG">下载用途建议 PNG</button></div></section>
<details><summary>文件核对范围</summary><p>七件版与三组版分别独立回读，均准确重组出 B03 的全部 61,119 个方块及方块实体。未改变原有轨道形状、标高、桥墩和信号位置。所有曲线两端及信号目标都在各自文件范围内。最大局部坡度仍为原版 9.79%。</p><p>三角地区划只核查了对已有铁路的平面退让，以及建议道路在指定标高的局部净空；不包含建筑施工、车辆扫掠、交通模拟或 Minecraft 实机验证。</p><p class="filename">源联络线 SHA-256：@@HASH@@</p></details></main><footer>蓝图与图纸基于已认可的 B03。分段属于文件组织调整；三角地设施属于待讨论的原创建议。</footer>
<script>const MANIFEST=@@MANIFEST@@,PLAN=@@PLAN@@,FILES=@@FILES@@;const $=id=>document.getElementById(id);let mode='parts',selected=null;
const all=[...MANIFEST.recommended_parts,...MANIFEST.whole_groups_alternative];const item=id=>all.find(a=>a.id===id);const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
function download(key,name,mime='application/octet-stream'){const url=URL.createObjectURL(new Blob([bytes(FILES[key])],{type:mime}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function downloadPart(id){const a=item(id);download(id,a.file.split('/').pop());}
function activeItems(){return mode==='groups'?MANIFEST.whole_groups_alternative:MANIFEST.recommended_parts;}
function select(id){selected=id;const a=item(id);document.querySelectorAll('.railgroup').forEach(g=>{const p=g.dataset.part;g.classList.toggle('dim',!!id&&p!=='context'&&!(id.length===1?p.startsWith(id):p===id));});document.querySelectorAll('.partbtn').forEach(b=>b.classList.toggle('active',b.dataset.id===id));const box=$('selectionBox');if(a){const [x,y,z]=a.origin_station_xyz,[w,h,d]=a.size_xyz;for(const[k,v]of Object.entries({x,y:z,width:w,height:d}))box.setAttribute(k,v);box.style.display='block';$('detail').innerHTML=`<h3>${a.name}</h3><p>${a.description}</p><p><b>${a.size_xyz.join(' × ')} 格</b></p><p class="muted">相对原站偏移 (${a.origin_station_xyz.join(', ')})</p><p class="muted">外包区块最多约 ${a.bounding_chunk_span_worst_alignment_xz.join(' × ')}；实际数量受世界对齐影响。</p><p class="filename">${a.file.split('/').pop()}</p><button class="primary" data-download="${a.id}">下载此蓝图</button>`;}else{box.style.display='none';$('detail').innerHTML=mode==='land'?'<h3>片区建议</h3><p>一条内部主路串联运维、工坊、仓储和公共服务；边角安排水务、能源和露天料场。保留城市接口，不把整片留白铺成草地。</p>':'<h3>同一套线形，两种拆法</h3><p>建议使用七件版逐段打印。三份整组版方便整体放置，内容与七件版一致。</p><p>所有曲线双端都在同一文件中，边界通过普通直轨接续。</p>';}}
function renderList(){const land=mode==='land';$('listTitle').textContent=land?'三角地分区':mode==='groups'?'整组备用':'七份打印分件';$('listHint').textContent=land?'A–F 为建议地块，尚未加入 NBT。':'颜色表示文件划分。选择后显示该件外包范围。';$('partList').innerHTML=land?PLAN.spatial_spec.zones.map(z=>`<p><b>${z.id} · ${z.name}</b><br><small>${z.program.join(' / ')}</small></p>`).join(''):activeItems().map(a=>`<button class="partbtn" data-id="${a.id}"><b>${a.id} · ${a.name}</b><span>${a.size_xyz.join(' × ')} 格 · ${a.block_entries.toLocaleString()} 条方块记录</span></button>`).join('');select(null);coords();}
function coords(){const origin=MANIFEST.reference_origins_station_xyz[$('reference').value],world=['wx','wy','wz'].map(id=>Number($(id).value)||0);const items=mode==='groups'?MANIFEST.whole_groups_alternative:MANIFEST.recommended_parts;$('coords').innerHTML=items.map(a=>{const p=a.origin_station_xyz.map((v,i)=>world[i]+v-origin[i]);return `<tr data-row="${a.id}"><td><b>${a.id} · ${a.name}</b><br><small>${a.file.split('/').pop()}</small></td><td>${a.size_xyz.join(' × ')}</td><td class="coords">(${p.join(', ')})</td><td>${a.block_entries.toLocaleString()}</td><td><button data-download="${a.id}">NBT</button></td></tr>`;}).join('');$('coordHint').textContent='计算方式：世界基准坐标 + 分件相对原站偏移 − 当前所选基准相对原站偏移。';}
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.id)select(b.dataset.id);if(b.dataset.download)downloadPart(b.dataset.download);if(b.dataset.mode){mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.landuse-layer').forEach(g=>g.style.display=mode==='land'?'':'none');$('partlabels').style.display=mode==='land'?'none':'';renderList();}});
$('showAll').onclick=()=>select(null);for(const id of ['reference','wx','wy','wz'])$(id).addEventListener('input',coords);
$('csv').onclick=()=>download('csv','放置坐标.csv','text/csv;charset=utf-8');$('partsPNG').onclick=()=>download('parts_png','GuangzhouEast_Print_Parts.png','image/png');$('landPNG').onclick=()=>download('land_png','GuangzhouEast_Triangle_Proposal.png','image/png');
$('zoneCards').innerHTML=PLAN.spatial_spec.zones.map(z=>`<article class="card" style="border-top:5px solid ${z.color}"><h3>${z.id} · ${z.name}</h3><p>${z.why}</p><p class="muted">${z.character}</p><small>建议建筑高度 ${z.height_blocks_suggested.join('–')} 格；功能与高度尚未冻结。</small></article>`).join('');renderList();window.guideReady=true;
</script></html>'''
repls={'SVG':svg,'MANIFEST':json.dumps(m,ensure_ascii=False,separators=(',',':')),'PLAN':json.dumps(plan,ensure_ascii=False,separators=(',',':')),'FILES':json.dumps(downloads,separators=(',',':')),'HASH':m['source']['sha256']}
for k,v in repls.items():template=template.replace('@@'+k+'@@',v)
# Embed a small CJK subset so the offline guide is legible on font-poor systems.
from fontTools import subset
from fontTools.ttLib import TTFont
webfont=TTFont(font);options=subset.Options();options.name_IDs=['*'];options.name_legacy=True;options.name_languages=['*']
subsetter=subset.Subsetter(options=options);subsetter.populate(text=''.join(sorted(set(template))));subsetter.subset(webfont)
webfont.flavor='woff';fontbuf=io.BytesIO();webfont.save(fontbuf)
fontcss='@font-face{font-family:GuideCJK;src:url(data:font/woff;base64,'+base64.b64encode(fontbuf.getvalue()).decode()+') format("woff");font-weight:100 900;font-display:swap;}body,svg text{font-family:GuideCJK,system-ui,sans-serif;}'
template=template.replace('</style>',fontcss+'</style>',1)
license_text=(P/'research/dongguanxi/FONT_OFL.txt').read_text()
template=template.replace('</html>','<!-- Noto Sans CJK font subset. '+license_text.replace('--','—')+' -->\n</html>')
path=D/'GuangzhouEast_Print_Guide.html';tmp=path.with_suffix('.partial');tmp.write_text(template);os.replace(tmp,path)
readme=['广州东 B03S1 分段打印包','原 B03 线形保留。三份整组与七份打印分件是同一套内容，任选一种打印。','推荐七件版；打印前先用相对坐标表对齐。所有曲线两端都在对应文件中，无外部端点或重叠 BE。','坐标以原广州东站蓝图最小角为零；X东、Y上、Z南。不要单独旋转分件。','三角地设施只是概念建议，未写入 NBT。','']
for a in allitems:readme.append(f"{a['file']} | {a['name']} | 偏移 {tuple(a['origin_station_xyz'])} | 尺寸XYZ {tuple(a['size_xyz'])} | {a['block_entries']} 方块条目")
readme+=['','完整 B03 蓝图最小角相对原站为 (-313,0,-144)；旧独立联络线最小角为 (100,0,2)。','若使用完整 B03 最小角为基准，模块世界位置 = 该基准世界位置 + 模块偏移 - (-313,0,-144)。','HTML 可输入世界基准坐标，下载每个 NBT、两张 PNG 和 CSV；离线可用。','七件版与三组版都经独立回读，准确重组原有61119方块，NBT方块实体数据保持一致。','游戏打印未执行；实际加载范围、炮的位置、接缝及自动列车信号需实机确认。','S02为了保留连续曲线，南北长381格；分件不会自动强加载区块。','保持空白不替换的打印方式，避免大外包范围清掉现有建筑。曲线材料数量以游戏清单为准。','前置车站、六收二和144格直道不包含在本分段包中。','', '三角地区划：A 运维大院 / B 装备工坊 / C 备件库与料场 / D 乘务食堂 / E 配电、水罐、泵房 / F 南端长料和工程车辆场。','入口建议由北侧高架下进入，Y=1只是本轮规划假设；未接入现实地形或市政道路。','', '源码：project/src/segment_link_b03.py；plan_triangle_b03.py；deliver_split_b03.py。','参考原文件与原点数据在project/runs/B03，分段清单、测试及区划在project/runs/B03S1。']
(D/'打印说明.txt').write_text('\n'.join(readme))
(R/'delivery_manifest.json').write_text(json.dumps({str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in D.rglob('*')if p.is_file()and p.suffix not in ['.zip','.partial']},ensure_ascii=False,indent=2))
print(json.dumps({'guide_bytes':path.stat().st_size,'nbt_files':len(allitems),'pngs':[partpng.name,landpng.name]},ensure_ascii=False))
