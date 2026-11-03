from pathlib import Path
import os,json,base64,zlib,re,io,html,shutil
from PIL import Image
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];RUN=os.environ.get('VILLAGE_RUN','V3_r04');R=C/'runs'/RUN;P=C/'review/previews'/RUN;OUT=ROOT/'deliverables';OUT.mkdir(exist_ok=True)
load=lambda p:json.loads(Path(p).read_text());PAR=load(R/'params_used.json');MAN=load(R/'manifest.json');VAL=load(R/'validation.json');META=load(P/'scene/scene.json');UNITS=load(R/'units.json');MODS=load(R/'module_consumption.json');LAMPS=load(R/'lamps.json')
esc=lambda s:html.escape(str(s),quote=True)
def data(p,mime=None):
 p=Path(p);mime=mime or {'.png':'image/png','.jpg':'image/jpeg','.json':'application/json'}.get(p.suffix,'application/octet-stream');return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()

def pic(p,size=1600):
 im=Image.open(p).convert('RGB');im.thumbnail((size,size));f=io.BytesIO();im.save(f,'WEBP',quality=91);return 'data:image/webp;base64,'+base64.b64encode(f.getvalue()).decode()

def dl(p,label=None):return '<a class="btn" download="'+esc(Path(p).name)+'" href="'+data(p)+'">'+esc(label or Path(p).name)+'</a>'

def fig(name,title,desc='',folder=P):return '<figure><a href="'+data(folder/name)+'" download="'+name+'"><img loading="lazy" src="'+pic(folder/name)+'" alt="'+esc(title)+'"></a><figcaption><b>'+esc(title)+'</b><span>'+esc(desc)+'</span></figcaption></figure>'

def table(head,rows):return '<div class="table"><table><tr>'+''.join('<th>'+esc(x)+'</th>' for x in head)+'</tr>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'

def section(id,n,title,body):return '<section id="'+id+'"><div class="section-title"><small>'+n+'</small><h2>'+title+'</h2></div>'+body+'</section>'

CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f0e7;color:#303b31;font:15px/1.8 Noto,system-ui,sans-serif}header,main,footer{max-width:1280px;margin:auto;padding:0 32px}header{padding-top:44px}.eyebrow{font:12px monospace;letter-spacing:.15em;color:#916646}h1{font-size:clamp(36px,5vw,66px);font-weight:550;line-height:1.15;letter-spacing:-.04em;margin:24px 0}h2{font-size:29px;font-weight:550;line-height:1.4;margin:0}h3{font-size:20px;margin:0 0 12px}.intro{font-size:18px;max-width:780px;color:#66705f}.tags{margin:20px 0}.tag{display:inline-block;border:1px solid #c5b59f;border-radius:30px;padding:3px 13px;margin:0 8px 7px 0;font-size:12px}nav{display:flex;flex-wrap:wrap;gap:22px;padding:19px 0;border-top:1px solid #cfc5b4;border-bottom:1px solid #cfc5b4}a{color:#a25334;text-decoration:none}a:hover{text-decoration:underline}.hero{margin:28px 0}.hero img{width:100%;display:block;border-radius:4px}.hero p{font-size:12px;color:#687061}.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid #cec2ad;border-bottom:1px solid #cec2ad;padding:22px 0;gap:20px}.stat{font:38px/1.2 monospace;color:#754f34}.stats small{display:block;font-size:12px;color:#707969;margin-top:8px}section{padding:55px 0;border-bottom:1px solid #cec6b5;scroll-margin-top:20px}.section-title{display:flex;align-items:baseline;gap:24px;margin-bottom:28px}.section-title small{font:13px monospace;color:#9f5c3d}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.card{background:#fffaf1;border:1px solid #d9ccba;padding:26px}.dark{background:#394b40;color:#f7f1e1;padding:30px;margin:28px 0}.dark p{color:#d2dfd1}.note{padding:18px 23px;border-left:3px solid #ad7650;background:#eae2d1;margin:24px 0}figure{margin:0;background:#fffaf1;border:1px solid #d9ccba;overflow:hidden}figure img{display:block;width:100%;height:420px;object-fit:contain;background:#dce1d5}figcaption{padding:16px 20px}figcaption b,figcaption span{display:block}figcaption span{font-size:12px;color:#6c7865;margin-top:5px}figure.wide img{height:auto}.table{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:14px 12px;border-bottom:1px solid #d2c9b7;text-align:left;vertical-align:top;min-width:100px}th{color:#795a41;font-weight:500}.btn,button,select{display:inline-block;border:1px solid #ae9980;background:#fffcf5;padding:8px 15px;color:#6f4a32;font:inherit;border-radius:3px;cursor:pointer;margin:4px 7px 4px 0}.primary{background:#74593d;color:#fff9ec}.controls{display:flex;align-items:center;flex-wrap:wrap;gap:15px;margin-bottom:18px}.controls input{accent-color:#8c643b}.pill{display:inline-block;background:#dce7d8;color:#48623d;padding:1px 8px;font:11px monospace}iframe{width:100%;height:760px;border:0;background:#1b302c}code,pre{font-family:monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e8e4d8;padding:20px;font-size:12px}details{padding:14px 0;border-bottom:1px solid #d5ccbc}summary{cursor:pointer}svg{max-width:100%;height:auto}footer{padding-top:30px;padding-bottom:40px;font-size:12px;color:#6b7767}.foot{font-size:12px;color:#687563}@media(max-width:760px){header,main,footer{padding-left:18px;padding-right:18px}.grid,.grid.three{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}h2{font-size:24px}section{padding:38px 0}.card{padding:20px}figure img{height:340px}.section-title{gap:14px}iframe{height:660px}.btn{font-size:12px}.table{max-width:100%}}'''

def shell(title,sub,nav,body,script=''):
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+CSS+'</style></head><body><header><div class="eyebrow">GAFAcraft / HAF 0.4 · ORIGINAL RESIDENTIAL · 2026.10.28</div><h1>'+title+'</h1><p class="intro">'+sub+'</p><nav>'+''.join('<a href="#'+a+'">'+b+'</a>' for a,b in nav)+'</nav></header><main>'+body+'</main><footer>海扒拉 · HAF 0.4 · 榕荫里 · 广式城中村 '+RUN+'<br>方块几何与近似灯光预览；不是 Minecraft 游戏截图。原创建筑意向，不是现实建筑施工或合规方案。</footer><script>'+script.replace('</script',r'<\/script')+'</script></body></html>'

def box_svg():
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 460"><rect width="760" height="460" fill="#e8eadf"/>'
 def pr(x,y,z):return (380+(x-z)*1.8,130+(x+z)*.75-y*2)
 for t in PAR['buildings']:
  x,z=t['x'],t['z'];pts=[(X,Y,Z) for Y in [3,3+t['floors']*5] for Z in [z,z+t['d']] for X in [x,x+t['w']]]
  for i,a in enumerate(pts):
   for j,bb in enumerate(pts):
    if j>i and sum(a[k]!=bb[k] for k in range(3))==1:
     u,v=pr(*a);U,V=pr(*bb);s+=f'<path d="M{u} {v}L{U} {V}" stroke="#8c6b4a" fill="none" stroke-width="1.6"/>'
  u,v=pr(x+t['w']/2,5+t['floors']*5,z+t['d']/2);s+=f'<text x="{u}" y="{v}" font-size="16" fill="#536548">{t["id"]}</text>'
 s+='<text x="28" y="430" font-size="16" fill="#65705a">8 个角点 / 楼栋包围盒 · 实际参数投影 · 无自动相机恢复</text></svg>';return s

def viewer():
 src=(ROOT/'support/templates/voxel_viewer.html').read_text();bins={n:base64.b64encode(zlib.compress((P/'scene'/n).read_bytes(),8)).decode() for n in ['opaque.bin','glass.bin','blocklight.bin']}
 src=re.sub(r'const BINS=.*?;\s*const META=.*?;\s*async function inflate',lambda m:'const BINS='+json.dumps(bins)+';\nconst META='+json.dumps(META)+';\nasync function inflate',src,flags=re.S)
 src=src.replace('市民服务中心 · NBT 几何查看','榕荫里街区 · NBT 查看')
 opts='<option value="all">整体</option><option value="top">俯视总图</option><option value="garden">街巷切低</option><option value="floor">逐层内饰</option><option value="tower">单栋</option>'
 src=re.sub(r'<select id="mode">.*?</select>',lambda m:'<select id="mode">'+opts+'</select>',src,flags=re.S)
 controls='<label>楼栋 <select id="tower">'+''.join('<option value="'+t['id']+'">'+t['id']+'</option>' for t in PAR['buildings'])+'</select></label><label>楼层 <input id="floor" type="number" min="1" max="8" value="2" style="width:44px"></label><label><input id="plan" type="checkbox">正俯视</label>'
 src=src.replace('<label><input id="night"',controls+'<label><input id="night"').replace('height:125px','min-height:150px').replace('max-width:150px','max-width:115px')
 a=src.index('function displayCut(o)');bb=src.index('window.render=async function',a)
 src=src[:a]+'''function displayCut(o){
 const key=JSON.stringify([o.cutY??null,o.minY??null,o.bounds??null]);if(key===currentCut)return;
 if(opaque!==originalOpaque){gl.deleteVertexArray(opaque.vao);gl.deleteBuffer(opaque.buf)}
 if(glass!==originalGlass){gl.deleteVertexArray(glass.vao);gl.deleteBuffer(glass.buf)}
 const filter=m=>{if(o.cutY==null&&o.minY==null&&!o.bounds)return m;let out=[];
 for(let i=0;i<m.data.length;i+=30){let keep=true;for(let k of [0,10,20]){const x=m.data[i+k],y=m.data[i+k+1],z=m.data[i+k+2];if((o.cutY!=null&&y>o.cutY)||(o.minY!=null&&y<o.minY)||(o.bounds&&(x<o.bounds[0]||z<o.bounds[1]||x>o.bounds[2]||z>o.bounds[3])))keep=false;}if(keep)for(let j=0;j<30;j++)out.push(m.data[i+j]);}return mesh(new Float32Array(out));};opaque=filter(originalOpaque);glass=filter(originalGlass);currentCut=key;
 }
 '''+src[bb:]
 a=src.index('let pending=false;function update()');bb=src.index("for(const el of document.querySelectorAll('input,select'))",a)
 updater='''const TOWERS=__TOWERS__;
let pending=false;function update(){if(!window.ready||pending)return;pending=true;requestAnimationFrame(async()=>{try{const yaw=Number(document.getElementById('yaw').value)*Math.PI/180,zoom=Number(document.getElementById('zoom').value),mode=document.getElementById('mode').value,width=Math.min(1280,innerWidth),height=Math.max(300,innerHeight-document.getElementById('controls').offsetHeight);let target=[108,18,102.5],spanZ=Math.max(220,315*height/width)/zoom,rise=210,dist=430,extra={};const t=TOWERS.find(t=>t.id===document.getElementById('tower').value);document.getElementById('floor').max=t.floors;let f=Math.max(1,Math.min(t.floors,Number(document.getElementById('floor').value)||1));document.getElementById('floor').value=f;
if(mode==='garden'){target=[108,6,103];spanZ=Math.max(210,300*height/width)/zoom;rise=115;extra={cutY:17.99}}
if(mode==='tower'){target=[t.x+t.w/2,t.base_y+t.floors*2.5,t.z+t.d/2];spanZ=Math.max(t.floors*5+20,(t.w+t.d)*height/width)/zoom;rise=30;dist=170;extra={bounds:[t.x-5,t.z-5,t.x+t.w+5,t.z+t.d+5]}}
if(mode==='floor'){const fy=t.base_y+(f-1)*5;target=[t.x+t.w/2,fy+1,t.z+t.d/2];spanZ=Math.max(34,(t.w+10)*height/width)/zoom;rise=170;dist=160;extra={cutY:fy+2.95,minY:fy-1,bounds:[t.x-5,t.z-5,t.x+t.w+5,t.z+t.d+5]}}
let eye=[target[0]+Math.sin(yaw)*dist,target[1]+rise,target[2]+Math.cos(yaw)*dist];if(mode==='top'){target=[108,3,102.5];eye=[108,430,102.5];spanZ=Math.max(218,230*height/width)/zoom}if(document.getElementById('plan').checked&&['floor','tower','garden'].includes(mode))eye=[target[0],430,target[2]];
await window.render({width,height,spanZ,spanX:spanZ*width/height,eye,target,ortho:true,night:document.getElementById('night').checked,concept:false,...extra});window.lastMode=mode;window.lastFloor=f;window.lastTarget=target;window.lastCut=extra;document.getElementById('msg').textContent='最终 NBT · '+(mode==='floor'?t.id+' / '+f+'F · ':'')+'拖动旋转；格栅、材质与灯光为近似显示';}catch(e){window.error=e.stack;document.getElementById('msg').textContent='实时查看不可用：'+e.message}pending=false})}
'''.replace('__TOWERS__',json.dumps(PAR['buildings']))
 src=src[:a]+updater+src[bb:]
 src=src.replace("body{margin:0;background:#142f3c", "body{margin:0;background:#293c34")
 src=src.replace('</style>','body,select,input,button{font-family:"Noto Sans CJK SC",system-ui,sans-serif}</style>',1)
 return src
