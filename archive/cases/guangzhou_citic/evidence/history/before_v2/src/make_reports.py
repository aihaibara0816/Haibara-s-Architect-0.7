from pathlib import Path
import base64,json,re,zlib,io,html,hashlib,shutil,os
from PIL import Image
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];OUT=Path(os.environ.get('CITIC_OUTPUT',str(ROOT/'deliverables/citic')));OUT.mkdir(parents=True,exist_ok=True)
RUN='V1_r04';R=C/'runs'/RUN;P=C/'review/previews'/RUN
E=json.loads((C/'input/evidence.json').read_text());V=json.loads((R/'validation.json').read_text());PAR=json.loads((R/'params_used.json').read_text());PLAN=json.loads((R/'resolved_plan.json').read_text());META=json.loads((P/'scene/scene.json').read_text())
esc=lambda s:html.escape(str(s),quote=True)
def data(path,mime=None):
 p=Path(path);mime=mime or {'.jpg':'image/jpeg','.png':'image/png','.html':'text/html','.json':'application/json','.nbt':'application/octet-stream'}.get(p.suffix,'application/octet-stream')
 return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def pic(path,maxsize=1600):
 im=Image.open(path).convert('RGB');im.thumbnail((maxsize,maxsize));f=io.BytesIO();im.save(f,'WEBP',quality=90)
 return 'data:image/webp;base64,'+base64.b64encode(f.getvalue()).decode()
def download(path,label=None):return f'<a class="btn" download="{esc(Path(path).name)}" href="{data(path)}">{esc(label or Path(path).name)}</a>'
def figure(name,label,desc='',source=P):return f'<figure><a href="{data(source/name)}" download="{esc(name)}"><img loading="lazy" src="{pic(source/name)}" alt="{esc(label)}"></a><figcaption><b>{esc(label)}</b><span>{esc(desc)}</span></figcaption></figure>'
def table(head,rows):return '<div class="table"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def section(id,n,title,body):return f'<section id="{id}"><div class="section-title"><small>{n}</small><h2>{title}</h2></div>{body}</section>'
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f3f2ed;color:#1e343d;font:15px/1.8 "Noto",system-ui,sans-serif}a{color:#147d83;text-decoration:none}a:hover{text-decoration:underline}header,main,footer{max-width:1250px;margin:auto;padding:0 36px}header{padding-top:42px}.eyebrow{letter-spacing:.15em;font:12px/1.6 monospace;color:#4d777e}h1{font-size:clamp(33px,5vw,62px);line-height:1.12;letter-spacing:-.04em;margin:24px 0}h2{font-size:29px;font-weight:550;margin:0}h3{font-size:20px;margin:0 0 12px}.intro{max-width:730px;font-size:18px;color:#50646a}.tag{display:inline-block;border:1px solid #bdc9c7;padding:3px 11px;border-radius:30px;font-size:12px;margin:0 6px 6px 0}.hero{display:grid;grid-template-columns:.78fr 1.22fr;gap:30px;align-items:center;min-height:650px;margin:24px 0}.hero img{width:100%;max-height:820px;object-fit:contain;background:#e1e6df;border-radius:3px}.stat{font:48px/1.1 monospace;letter-spacing:-.05em}.stats{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid #bbc7c5;border-bottom:1px solid #bbc7c5;padding:24px 0;gap:20px}.stats small{display:block;color:#64767b;margin-top:8px}nav{display:flex;flex-wrap:wrap;gap:18px;padding:20px 0;border-top:1px solid #becac7;border-bottom:1px solid #becac7}nav a{font-size:13px}section{padding:60px 0;border-bottom:1px solid #c7d0cc;scroll-margin-top:20px}.section-title{display:flex;gap:25px;align-items:baseline;margin-bottom:28px}.section-title small{font:13px monospace;color:#22888c}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}figure{margin:0;background:#fff;border:1px solid #dae1dc;overflow:hidden}figure img{width:100%;height:420px;object-fit:contain;display:block;background:#e2e7e0}figure.tall img{height:700px}figcaption{padding:18px 20px}figcaption b,figcaption span{display:block}figcaption span{font-size:13px;color:#62787d;margin-top:5px}.card{padding:26px;background:#fff;border:1px solid #d4ddda}.dark{background:#163944;color:#e9efed;padding:32px}.dark a{color:#92d2cc}.note{padding:18px 24px;border-left:3px solid #c09d6a;background:#eae8df;margin:24px 0}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #ccd5cf;padding:15px 12px;vertical-align:top;min-width:100px}th{color:#41717a;font-weight:500}.btn,button,select{display:inline-block;border:1px solid #8ba6a6;background:#fff;padding:9px 17px;font:inherit;cursor:pointer;border-radius:3px;margin:4px 8px 4px 0;color:#1d535d}.btn.primary,button.primary{background:#176c73;color:white;border-color:#176c73}.controls{display:flex;flex-wrap:wrap;align-items:center;margin-bottom:20px}.controls label{margin-right:20px}.controls input{accent-color:#15777a}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.ref img{height:280px}.ref a{overflow-wrap:anywhere;font-size:12px}.ref details{font-size:13px}.step{border-left:1px solid #9eb4b1;padding:2px 0 22px 26px;margin-left:8px}.step b{font-size:19px}.pill{font:11px monospace;display:inline-block;background:#dce9df;color:#27634e;padding:1px 7px}.warn{background:#efe3cd;color:#795426}code,pre{font-family:monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:20px;background:#e6ece7;font-size:12px}details{padding:14px 0;border-bottom:1px solid #d5dfd8}summary{cursor:pointer}iframe{width:100%;height:720px;border:0;background:#17333e}footer{padding-top:28px;padding-bottom:40px;font-size:12px;color:#62787d}svg{max-width:100%;height:auto}.mobile-hide{display:block}img{color:#1a494f}.allcaps{letter-spacing:.12em;font-size:12px}.split{display:grid;grid-template-columns:1fr 1fr;gap:28px}.chipline{margin:20px 0}@media(max-width:760px){header,main,footer{padding-left:19px;padding-right:19px}header{padding-top:28px}.hero,.grid,.grid.three,.split,.gallery{grid-template-columns:1fr}.hero{min-height:0}.hero img{max-height:660px}.stat{font-size:33px}.stats{gap:10px}h2{font-size:24px}.section-title{gap:14px}section{padding:38px 0}figure img{height:330px}.ref img{height:270px}iframe{height:620px}.table{max-width:100%}.btn{font-size:13px}.card{padding:20px}}'''
def shell(title,subtitle,nav,body,script=''):
 return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body><header><div class="eyebrow">GAFAcraft / HAF 0.4 · GUANGZHOU · 2026.10.27</div><h1>{title}</h1><p class="intro">{subtitle}</p><nav>'+''.join(f'<a href="#{i}">{t}</a>' for i,t in nav)+f'</nav></header><main>{body}</main><footer>海扒拉 · HAF 0.4 实验 / CITIC V1 · 最终迭代 R04<br>近似方块状态渲染，不是 Minecraft 游戏截图；现实证据、设计补全与游戏待测分开记录。</footer><script>{script}</script></body></html>'

def viewer():
 src=(ROOT/'support/templates/voxel_viewer.html').read_text()
 bins={n:base64.b64encode(zlib.compress((P/'scene'/n).read_bytes(),9)).decode() for n in ['opaque.bin','glass.bin','blocklight.bin']}
 src=re.sub(r'const BINS=.*?;\s*const META=.*?;\s*async function inflate',lambda m:'const BINS='+json.dumps(bins)+';\nconst META='+json.dumps(META)+';\nasync function inflate',src,flags=re.S)
 src=src.replace('市民服务中心 · NBT 几何查看','中信广场 · NBT 几何查看')
 opts='<option value="all">整体</option><option value="crown">塔冠</option><option value="entry">入口广场</option><option value="top">真俯视</option><option value="lobby">大厅切层</option><option value="office_A">办公示范层</option><option value="office_B">协作示范层</option><option value="lounge">共享休息层</option>'
 src=re.sub(r'<select id="mode">.*?</select>',lambda m:'<select id="mode">'+opts+'</select>',src,flags=re.S)
 src=src.replace('JSON.stringify([o.cutY??null,o.cutX??null])','JSON.stringify([o.cutY??null,o.cutX??null,o.minY??null])')
 src=src.replace('o.cutY==null&&o.cutX==null','o.cutY==null&&o.cutX==null&&o.minY==null')
 src=src.replace('(o.cutX!=null&&m.data[i+k]>o.cutX))','(o.cutX!=null&&m.data[i+k]>o.cutX)||(o.minY!=null&&m.data[i+k+1]<o.minY))')
 a=src.index('function displayCut(o)');bb=src.index('window.render=async function',a)
 src=src[:a]+'''function displayCut(o){
 const key=JSON.stringify([o.cutY??null,o.cutX??null,o.minY??null,o.focusTower??false]);if(key===currentCut)return;
 if(opaque!==originalOpaque){gl.deleteVertexArray(opaque.vao);gl.deleteBuffer(opaque.buf)}
 if(glass!==originalGlass){gl.deleteVertexArray(glass.vao);gl.deleteBuffer(glass.buf)}
 const filter=m=>{if(o.cutY==null&&o.cutX==null&&o.minY==null&&!o.focusTower)return m;let out=[];
 for(let i=0;i<m.data.length;i+=30){let keep=true;for(let k of [0,10,20]){const x=m.data[i+k],y=m.data[i+k+1],z=m.data[i+k+2];if((o.cutY!=null&&y>o.cutY)||(o.cutX!=null&&x>o.cutX)||(o.minY!=null&&y<o.minY)||(o.focusTower&&(x<32||x>57||z<52||z>77)))keep=false;}if(keep)for(let j=0;j<30;j++)out.push(m.data[i+j]);}return mesh(new Float32Array(out));};opaque=filter(originalOpaque);glass=filter(originalGlass);currentCut=key;
 }
 '''+src[bb:]
 start=src.index('let pending=false;function update()');end=src.index("for(const el of document.querySelectorAll('input,select'))",start)
 update='''let pending=false;function update(){if(!window.ready||pending)return;pending=true;requestAnimationFrame(async()=>{try{const yaw=Number(document.getElementById('yaw').value)*Math.PI/180,zoom=Number(document.getElementById('zoom').value),mode=document.getElementById('mode').value,width=Math.min(1250,innerWidth),height=Math.max(320,Math.min(1050,innerHeight-125));let target=[46,90,49],spanZ=215/zoom,rise=85,dist=270,extra={};if(mode==='crown'){target=[45,163,64];spanZ=54/zoom;rise=25;dist=130}if(mode==='entry'){target=[45,8,68];spanZ=60/zoom;rise=65;dist=170}if(mode==='lobby'){target=[45,6,64];spanZ=31/zoom;rise=130;extra={cutY:10.9,minY:3}}if(['office_A','office_B','lounge'].includes(mode)){const fy={office_A:25,office_B:81,lounge:130}[mode];target=[45,fy+2,64];spanZ=32/zoom;rise=160;extra={cutY:fy+3.9,minY:fy-1}}let eye=[target[0]+Math.sin(yaw)*dist,target[1]+rise,target[2]+Math.cos(yaw)*dist];if(mode==='top'){target=[46,3,49];eye=[46,420,49];spanZ=110/zoom}if(mode==='all')spanZ=Math.max(spanZ,155*height/width/zoom);if(mode==='top')spanZ=Math.max(spanZ,100*height/width/zoom);await window.render({width,height,spanZ,spanX:spanZ*width/height,eye,target,ortho:true,night:document.getElementById('night').checked,concept:false,...extra});document.getElementById('msg').textContent='最终 NBT 同源几何 · 拖动旋转 · 内饰为设计补全，光照为近似';}catch(e){window.error=e.stack;document.getElementById('msg').textContent='实时预览不可用：'+e.message}pending=false})}
'''
 src=src[:start]+update+src[end:]
 src=src.replace('extra={cutY:10.9,minY:3}','extra={cutY:10.9,minY:3,focusTower:true}').replace('extra={cutY:fy+3.9,minY:fy-1}','extra={cutY:fy+3.9,minY:fy-1,focusTower:true}')
 from fontTools import subset
 ff=subset.load_font(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),subset.Options());ss=subset.Subsetter();ss.populate(text=''.join(set(src)));ss.subset(ff);ff.flavor='woff';fb=io.BytesIO();ff.save(fb)
 src=re.sub(r'data:font/woff;base64,[A-Za-z0-9+/=]+',lambda m:'data:font/woff;base64,'+base64.b64encode(fb.getvalue()).decode(),src)
 src=src.replace('</style>','body,select,input,button{font-family:"Noto Sans CJK SC",system-ui,sans-serif}</style>',1)
 (C/'review/viewer.html').write_text(src)
 return src

def map_svg():
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 1030"><rect width="920" height="1030" fill="#edf0e9"/>'
 cols={'157418073':'#99bab9','157418082':'#c4c4af','157418084':'#c4c4af','926228208':'#1e6b7b'}
 for k,col in cols.items():
  points=' '.join(f'{x*9+35:.1f},{z*9+35:.1f}' for x,z in PAR['map_polygons'][k]['polygon']);s+=f'<polygon points="{points}" fill="{col}" stroke="#48616a" stroke-width="2"/>'
 for txt,x,y in [('北 N ↑',730,40),('西翼公寓',120,215),('东翼公寓',600,215),('弧形商业裙楼',340,385),('主塔',400,625),('入口广场 · 设计补全',300,825)]:s+=f'<text x="{x}" y="{y}" fill="#153f4b" font-size="23">{txt}</text>'
 s+='<path d="M435 840L435 720" stroke="#c78342" stroke-width="10"/><text x="40" y="945" font-size="17" fill="#5c767b">© OpenStreetMap contributors · ODbL 1.0</text><text x="40" y="975" font-size="17" fill="#5c767b">投影到同一方块坐标；地图轮廓不等于测绘精度。</text></svg>'
 return s
def box_svg():
 pts=[(x,y,z) for y in [3,185] for z in [53,76] for x in [33,56]]
 xy=[(230+(x-z)*3,570-y*2.6+(x+z-100)*.75) for x,y,z in pts]
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 680"><rect width="480" height="680" fill="#edf0e9"/>'
 for i,a in enumerate(pts):
  for j,b in enumerate(pts):
   if j>i and sum(a[k]!=b[k] for k in range(3))==1:s+=f'<line x1="{xy[i][0]}" y1="{xy[i][1]}" x2="{xy[j][0]}" y2="{xy[j][1]}" stroke="#528e91" stroke-width="2"/>'
 for i,(x,y) in enumerate(xy):s+=f'<circle cx="{x}" cy="{y}" r="5" fill="#ce975e"/><text x="{x+8}" y="{y-6}" font-size="15" fill="#234b54">{i+1}</text>'
 s+='<text x="270" y="325" font-size="22" fill="#24515b">182 格</text><text x="270" y="350" font-size="15" fill="#53737b">含两根尖杆</text><text x="45" y="630" font-size="17" fill="#53737b">几何八角包围盒；未做照片相机反求</text></svg>'
 return s
def plan_overlay(fid):
 cam=next(x for x in json.loads((P/'cameras.json').read_text()) if x['id']==fid+'_plan');fy=next(x['floor_y'] for x in PAR['synthetic_levels'] if x['id']==fid)
 s='<svg viewBox="0 0 1300 1300" xmlns="http://www.w3.org/2000/svg"><image width="1300" height="1300" href="'+pic(P/(fid+'_plan.png'))+'"/>'
 def proj(x,z):return (x-45+14.5)/29*1300,(z-64+14.5)/29*1300
 names={'work':'工区 / 协作','meeting':'会议 / 茶水','rest':'休息','tea':'茶水','reading':'阅读'}
 for r in PLAN['input_snapshot']['rooms']:
  if r['floor_id']!=fid:continue
  a,y,z,b,_,d=r['bounds_xyz'];px,py=proj(a,z);qx,qy=proj(b,d);s+=f'<rect x="{px}" y="{py}" width="{qx-px}" height="{qy-py}" fill="#f9e4b5" fill-opacity=".1" stroke="#b8762d" stroke-width="3" stroke-dasharray="8 5"/><rect x="{px}" y="{py-34}" width="200" height="36" fill="#f9f6ec"/><text x="{px+7}" y="{py-7}" font-size="25" fill="#8c591f">{names.get(r["id"].split(".")[-1],r["function"])}</text>'
 s+='<rect x="430" y="1200" width="450" height="65" fill="#f4f0e5"/><text x="455" y="1240" font-size="23" fill="#345961">Y='+str(fy)+' · 示范标高，非现实楼层编号</text></svg>'
 return s

def building(vhtml):
 M=V['metrics'];hero='<div class="hero"><div><div class="chipline"><span class="tag">现实复原 + 设计补全</span><span class="tag">V1 · R04</span></div><h2>从一座塔，<br>做到一片可辨认的场地。</h2><p>主塔、弧形裙楼、两翼公寓和入口前场，使用同一坐标与缩尺。四个重点标高展示大厅、办公、项目协作与共享休息。</p><div class="note">本版先验收轮廓、幕墙层次与空间分区。示范内饰不对应真实租户；电梯为静态表达，尚未接通整塔楼层交通。</div>'+download(R/'building.nbt','下载最终 NBT')+'<a class="btn" href="#interiors">查看内饰</a></div><img src="'+pic(P/'se_day.png')+'" alt="广州中信广场整体 NBT 日景预览"></div>'
 hero+='<div class="stats"><div><div class="stat">182</div><small>主塔高度 / 格 · 含尖杆</small></div><div><div class="stat">99,129</div><small>非空气方块</small></div><div><div class="stat">4</div><small>功能示范标高</small></div></div>'
 gal='<div class="controls"><label>方位 <select id="face"><option value="se">东南</option><option value="sw">西南</option><option value="ne">东北</option><option value="nw">西北</option></select></label><label><input id="nightToggle" type="checkbox"> 夜景</label><span>四向保持同尺度与同框。</span></div><figure class="tall"><img id="mainView" src="'+pic(P/'se_day.png')+'" alt="四向日夜预览"><figcaption>最终 NBT 回读 · 玻璃透明度、颜色与光传播为近似</figcaption></figure><div class="grid" style="margin-top:24px">'+figure('front_day.png','轴向正面','双尖杆与中间招牌')+figure('top_day.png','真正俯视','屋顶及整体关系；不是倾斜卫星图')+'</div>'
 body=hero+section('views','01','四向日夜与俯视',gal)
 body+=section('interactive','02','旋转、近看与切层','<p>内嵌最终 NBT 的几何。点击加载后，可旋转、切换日夜，并分别查看示范层。</p><button id="load3d" class="primary">打开三维查看器</button><div id="threeD"></div><p class="minor">浏览器需支持 WebGL 2 与解压流；固定图集始终可用。</p>')
 body+=section('detail','03','幕墙与入口纵深','<div class="grid">'+figure('crown_day.png','双杆、招牌与顶部凹槽','链条横框 / 铁栏竖框 / 蓝青玻璃分组')+figure('entry_day.png','高门框与弧形大厅','椭圆雨棚下保留金属肋，入口通路最后回查')+'</div>')
 ints='<p>楼层标高是缩尺模型里的设计示范位置。其余空间主要用窗后片段表达深度和夜间占用，不把 80 层全部压成可进入房间。</p><div class="grid">'+figure('lobby_cut.png','大厅 · Y4','接待、等候、静态电梯厅')+'<div class="card"><h3>用途先行，再放家具</h3><p>办公层有成组工作台、会议桌和独立休息角；协作层改用项目桌与茶水台；共享层以休息、阅读与茶水为主。</p><p>16 根视觉柱连接楼面与吊顶。它们用来组织视线和区域，不宣称真实承重。</p><p>现代示范层采用两格层间构造，灯块与下层吊顶齐平。高层普通窗后的冷暖与暗窗另按稳定 ID 分配。</p></div></div><div class="grid" style="margin-top:24px">'
 for fid,label in [('office_A','办公示范层 · Y25'),('office_B','项目协作层 · Y81'),('lounge','共享休息层 · Y130')]:ints+='<figure>'+plan_overlay(fid)+f'<figcaption><b>{label}</b><span>虚线为交接数据中的功能范围；底图来自最终 NBT。</span></figcaption></figure>'
 ints+=figure('section.png','竖向剖切','示范层之外的密集窗后片段不具备正常层高')+'</div>'
 body+=section('interiors','04','公共、工作与休息',ints)
 body+=section('site','05','广场作为一个整体','<p>入口中轴保持开敞，浅池、树荫座椅和连续植床分置两侧。棕榈与乔木借用现场可见的植物层次，具体铺地、池形与种植位置属于补全设计。</p><div class="grid">'+figure('plaza_day.png','入口场地日景','上部切除只用于看清场地，不是缺失建筑')+figure('plaza_night.png','相同机位夜景','入口与步道有功能照明，不靠整栋全亮')+'</div>')
 checks=table(['项目','结果'],[['最终 NBT 独立回读','通过；内容与导出场景一致'],['几何专项检查',str(len(V['checks']))+' 项通过'],['共享引擎回归','62 项测试通过'],['实际模块消费',str(M['modules'])+' 个模块 / '+str(M['designed_rooms'])+' 个功能区'],['游戏、碰撞与真实照明','待测；未宣称完成'],['建筑视觉验收','本轮自检完成，等待海扒拉评审']])
 body+=section('delivery','06','文件与验收边界',checks+'<div class="note">保留现实证据不足的部分：塔冠细部高差、公寓高度、局部入口朝向和场地边界。图集不代表测绘还原或游戏验收。</div>'+download(R/'building.nbt','NBT')+download(R/'validation.json','检查记录 JSON')+download(C/'input/handoff.json','内饰交接 JSON')+download(R/'params_used.json','建造参数 JSON')+'<details><summary>导入与模型尺寸</summary><p>Java Structure NBT，DataVersion 3955；范围 92 × 188 × 98 格，X 向东、Z 向南。稀疏文件不写入空气，不会主动清除空白单元。应在空场地测试。具体导入器的大尺寸限制和 Java 1.21.1 环境尚待实际验证。</p><code>SHA256 '+V['source_nbt_sha256']+'</code></details>')
 views={q+'_'+m:pic(P/(q+'_'+m+'.png')) for q in ['se','sw','ne','nw'] for m in ['day','night']}
 script='const VIEWS='+json.dumps(views)+';const VIEWER='+json.dumps(vhtml)+';function swap(){document.getElementById("mainView").src=VIEWS[document.getElementById("face").value+"_"+(document.getElementById("nightToggle").checked?"night":"day")]};document.getElementById("face").addEventListener("change",swap);document.getElementById("nightToggle").addEventListener("change",swap);document.getElementById("load3d").addEventListener("click",function(){const f=document.createElement("iframe");f.title="中信广场三维查看器";f.srcdoc=VIEWER;document.getElementById("threeD").append(f);this.remove()});'
 # Escape end-script text embedded in viewer to avoid closing the parent script.
 script=script.replace('</script','<\\/script')
 return shell('广州中信广场','HAF 0.4 写字楼与场地测试 · 建筑成果文件',[('views','日夜'),('interactive','三维'),('detail','细部'),('interiors','内饰'),('site','广场'),('delivery','下载')],body,script)

def process():
 body='<div class="dark" style="margin-top:32px"><h2>每一步都对应实际输入与文件。</h2><p>本次完成了资料核对、同坐标几何、功能交接、案例建造、NBT 回读、失败修复和离线展示。图像没有自动变成建筑；照片取舍和几何规则由本轮逐项编写。</p></div>'
 body+=section('scope','01','先锁定建筑与边界',table(['约束','本次采用'],[['对象','广州天河北路中信广场主办公塔楼及直接相连的场地'],['纳入','主塔、弧形商业裙楼、两翼公寓外观、入口广场和周边步道'],['尺度','各轴统一 7/15 格每米；390.2 m → 182 格，尖杆包含在内'],['不确定','地图不是测绘图；没有取得原始三维模型或办公室施工图'],['内饰','4 个可查看示范标高 + L1 窗后片段；静态电梯']])+'<p>总高和用途核对：<a href="https://www.skyscrapercenter.com/building/citic-plaza/242">CVU / The Skyscraper Center</a>。真实楼层数与游戏可用层数分别记录。</p>')
 refs='<p>本轮实际查看并采用 12 张图片。每张保留页面链接、原图地址和用途；未按固定六张数量截断研究。点击图可下载已核对的原图。</p><div class="grid three">'
 for r in E['images']:
  refs+='<figure class="ref"><a download="'+r['file']+'" href="'+data(C/'input/images'/r['file'])+'"><img loading="lazy" src="'+pic(C/'input/images'/r['file'],900)+'" alt="'+esc(r['use'])+'"></a><figcaption><b>'+esc(r['id'])+'</b><p>'+esc(r['use'])+'</p><a href="'+esc(r['page_url'])+'">来源页面</a> · <a href="'+esc(r['image_url'])+'">原图网址</a><details><summary>观察与限制</summary><p>'+esc(r['limits'])+'</p><p>'+esc(r['orientation'])+' / '+r['face']+' / 遮挡 '+r['occlusion']+'</p><p>'+esc(r['licence'])+'</p><code>'+r['sha256'][:16]+'…</code></details></figcaption></figure>'
 refs+='</div><h3 style="margin-top:28px">检索到但没有采用</h3>'+table(['候选','舍弃理由'],[[f'<a href="{esc(r["url"])}">{esc(r.get("file","来源页面"))}</a>',esc(r['reason'])] for r in E['rejected']])
 body+=section('references','02','从哪个网址，找到了什么',refs)
 body+=section('geometry','03','多视参考盒与伪建模','<div class="split"><div>'+map_svg()+'</div><div>'+box_svg()+'</div></div><p>平面来自实际下载的 OpenStreetMap XML，主塔、两翼与裙楼使用同一局部投影。右侧是 8 个角点的几何包围盒，用于检查尺寸和相对比例；没有把透视照片假装校正成正交立面，也没有执行自动相机恢复。</p><p>实际采用的分体：主塔方形翼体、八边形中部、圆筒、顶部凹口、双尖杆、黑色入口门框、弧形裙楼与折转公寓翼。地图高度标签只作为估计，官方总高优先。</p><p><a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors / ODbL 1.0</a> · <a href="https://www.openstreetmap.org/way/926228208">主塔轮廓</a> · <a href="https://www.openstreetmap.org/way/157418073">裙楼轮廓</a></p>')
 body+=section('decisions','04','证据怎样转成几何',table(['构件','采用判断','证据强度'],[[r['component'],esc(r['decision']),esc(r['confidence'])] for r in E['decisions']]))
 tasks=[('研究 skill','来源/图片/遮挡/身份和未知整理 → input/evidence.json','实际完成；非自动分割'),('无实物设计 + 内饰','11 功能区、通路禁放体积、模块边界、现代双层吊顶 → input/handoff.json','实际完成；内饰为补全'),('HAF 0.4 交接','compile_handoff → resolved_plan.json','规则已消费；单靠计划不生成方块'),('中信案例适配器','消费 resolved modules 并生成主塔、场地、家具与灯位','本次新增消费者，只适配本案例'),('NBT 导出与回读','building.nbt → 独立解析器 → 状态方块网格','实际完成；图片来自最终 NBT'),('真实游戏','导入、上下楼交通、碰撞、照明与水更新','pending')]
 body+=section('skills','05','现有 skill 到底做到了哪一步',table(['环节','本次文件/行为','状态'],tasks)+'<p>没有取得三维模型，因此只有图片 + 地图约束路线，不伪造“有模型 / 无模型”双路线对比。没有训练模型权重。</p>')
 body+=section('interior-rule','06','内饰、光照与园林的具体消费','<div class="grid"><div class="card"><h3>空间与家具</h3><p>办公、协作、共享休息三种不同层型；公共大厅另做接待和等候。环核心通路进入禁放列表，视觉柱避开家具的包围盒。</p><p>模块名称、边界和消费结果可追到 <code>module_consumption.json</code>，不能只把 JSON 放进包里就说接入完成。</p></div><div class="card"><h3>照明与场地</h3><p>4 个重点标高下层吊顶放灯，上层为独立地板。高楼窗后按稳定 ID 分配暗/暖/冷，未套低于 10 层的全亮规则。原版冷暖材料不代表 RGB 彩光。</p><p>树荫、座椅、连续植床、棕榈和浅池组成前场；整条通路按全宽检查，水下和水边有围合。</p></div></div>'+download(C/'input/handoff.json','下载交接输入')+download(R/'resolved_plan.json','下载已解析计划')+download(R/'module_consumption.json','下载实际模块消费'))
 rounds=[['R01','94,602','首次导出；外围幕墙偏整片玻璃，普通窗后灯被后写楼板覆盖，柱位碰家具','保留历史 NBT 与首轮预览'],['R02','99,132','加框、延后灯写入、柱位调整；检查发现路灯占通道、两棵树落入裙楼、1 灯被覆盖','保留失败检查'],['R03','99,129','通路、灯具存活、树根与模块边界检查通过；分出协作层与休息层','发现横框像凸出的小阳台'],['R04','99,129','横框改细链、字形修正、功能地面分区；最终导出并重出全部预览','本次交付']]
 body+=section('iterations','07','本次真实迭代记录',table(['迭代','非空气方块','原因与变化','保留结果'],rounds)+'<div class="grid">'+figure('overview.png','R01 · 早期形体','原始检查用预览；没有覆盖旧版本',source=C/'review/previews/V1_r01')+figure('se_day.png','R04 · 最终方块','同属本次模型，机位略不同；不能作为像素差分')+'</div>')
 body+=section('verification','08','验证了什么，仍没验证什么',table(['检查','结果'],[[r['id'],'<span class="pill">'+r['status']+'</span>'] for r in V['checks']])+'<p>共享引擎 62 项回归测试通过。最终 25 张固定机位图来自同一个 NBT；网格文件字节数、源文件 SHA256 和输出图片哈希均记录。</p><p>这些检查不证明与现实完全一致，也不证明游戏可玩。塔冠中缝宽度、幕墙薄框的视觉比例和场地细节，仍保留给下一轮人工评审。</p>'+download(R/'validation.json','详细检查 JSON'))
 body+=section('gaps','09','下一步有针对性地改','<ol><li>先评审主塔正面与塔冠：中缝、圆筒露出和招牌大小，锁定轮廓后再微调材质。</li><li>在实际游戏中看无光影幕墙和夜景，确认细框是否过密、亮窗是否均匀，并测试大尺寸 NBT 导入。</li><li>若要真正进入写字楼使用，单独完善垂直交通与办公室楼层：当前静态核心和 L1 窗后不承担这项功能。</li><li>补真实场地俯视/测绘资料后，再替换广场设计补全区域，保留已经认可的塔体和坐标。</li></ol><details><summary>全部未解决事项</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in E['uncertainties'])+'</ul></details>')
 files=['params_used.json','manifest.json','resolved_plan.json','module_consumption.json','lamps.json','plants.json','paths.json','validation.json']
 body+=section('files','10','文件索引与复跑入口',table(['文件','用途'],[['CITIC.html','建筑成果、日夜图、交互切层、NBT 下载'],['CITIC_Process.html','本文件：来源、取舍、接口、失败与边界'],['CITIC.nbt','最终稀疏 Java Structure NBT'],['CITIC.zip','本案例独立复跑包：新旧 run、来源、代码、检查和预览；不替代完整 HAF 历史归档']])+'<p>'+''.join(download(R/f) for f in files)+'</p><pre>python -m pip install numpy Pillow\npython tools/agent.py --case guangzhou_citic --run V1_replay\npython cases/guangzhou_citic/src/validate_case.py --run V1_replay\npython tools/render_building_case.py --case guangzhou_citic --run V1_replay</pre><p>Linux 出图依赖 libEGL；游戏不在此流程中自动运行。新 run 不覆盖已有目录。</p><details><summary>查看建造代码</summary><pre>'+esc((C/'src/build_case.py').read_text())+'</pre></details>')
 return shell('从资料到方块','广州中信广场 · 独立的全流程与能力边界记录',[('scope','边界'),('references','来源图'),('geometry','参考盒'),('decisions','判断'),('skills','技能'),('iterations','迭代'),('verification','验证'),('files','文件')],body)

if __name__=='__main__':
 v=viewer();docs={'CITIC.html':building(v),'CITIC_Process.html':process()}
 # Embed a subset of the retained licensed CJK font, including every report/viewer character.
 from fontTools import subset
 f=subset.load_font(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),subset.Options());ss=subset.Subsetter();ss.populate(text=''.join(docs.values())+'中信广场东西南北办公协作休息大厅');ss.subset(f);f.flavor='woff';buf=io.BytesIO();f.save(buf)
 font='@font-face{font-family:Noto;src:url(data:font/woff;base64,'+base64.b64encode(buf.getvalue()).decode()+') format("woff");font-display:swap}'
 for name,s in docs.items():
  s=s.replace('<style>','<style>'+font,1);(OUT/name).write_text(s)
 shutil.copy2(R/'building.nbt',OUT/'CITIC.nbt')
 print(json.dumps({p.name:p.stat().st_size for p in OUT.iterdir() if p.is_file()}))
