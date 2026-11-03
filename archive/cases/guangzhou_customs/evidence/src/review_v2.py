"""Offline V1/V2 review: exact NBT renders, source-linked photo decisions."""
from pathlib import Path
import base64,html,json,io,shutil,zipfile,hashlib,os
from PIL import Image,ImageDraw,ImageFont
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1];RUN='V2_r06'
OUT=ROOT/'deliverables/guangzhou_customs_v2';OUT.mkdir(parents=True,exist_ok=True)
STEM='Guangzhou_Customs_HAF_V2';R=CASE/'runs'/RUN;P=CASE/'review/previews'/RUN
from make_review import LABEL
LABEL.update(crown_rear='中央上段 / 钟座 · 后斜视',podium_oblique='裙楼 · 突出翼与侧拱门',plan_25='平面剖切 · y=25',plan_65='平面剖切 · y=65',plan_110='平面剖切 · y=110')
def uri(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(Path(p).read_bytes()).decode()
def small_photo(p):
 im=Image.open(p).convert('RGB');im.thumbnail((1800,1800));b=io.BytesIO();im.save(b,'JPEG',quality=88)
 return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
def j(p):return json.loads(p.read_text())
def esc(s):return html.escape(str(s))

CSS='''
:root{--paper:#f3f0e9;--ink:#223b40;--line:#cbd5cf;--gold:#aa8249}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 system-ui,"Noto Sans CJK SC",sans-serif}header{padding:56px 5vw 40px;background:#203b40;color:#f6f0df}header small{color:#cfba8e;letter-spacing:.16em}h1{font-size:clamp(36px,5vw,70px);line-height:1.18;font-weight:600;margin:20px 0}h2{font-size:28px}header p{max-width:850px}nav{position:sticky;top:0;background:#f3f0e9f7;border-bottom:1px solid var(--line);display:flex;gap:24px;overflow:auto;padding:13px 5vw;z-index:5;white-space:nowrap}nav a,a{color:#355f68}main{max-width:1700px;margin:auto;padding:0 28px}section{padding:38px 0;border-bottom:1px solid var(--line);scroll-margin-top:65px}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0}button,select,input,textarea{font:inherit;color:inherit}button,select,.download{padding:9px 15px;border:1px solid #718b90;background:#fffdf7;border-radius:5px;cursor:pointer}.download{display:inline-block;text-decoration:none;margin:5px 8px 5px 0}button:hover,.download:hover{background:#dce8df}button:focus-visible,select:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #ac874a}.pair,.quad{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.pair figure,.quad figure{margin:0;background:#e1e7e2;border:1px solid var(--line)}figcaption{padding:10px 16px;background:#fffdf6}.frame{position:relative}.frame img,.quad img{display:block;width:100%;height:auto;cursor:zoom-in}.marks{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.marks ellipse{fill:none;stroke-width:3}.marks text{font-size:20px;font-weight:bold;paint-order:stroke;stroke:#fff;stroke-width:3px}.note{background:#eae2d3;border-left:4px solid var(--gold);padding:14px 18px}.muted{font-size:14px;color:#596f73}.metrics{display:flex;gap:40px;flex-wrap:wrap}.metrics b{font-size:30px;display:block}.photo{width:100%;max-height:780px;object-fit:contain;background:#dde3de;cursor:zoom-in}.sourcebox{padding:18px;background:#fffdf8}.sourcebox a{word-break:break-all}table{width:100%;border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:12px;text-align:left;vertical-align:top}th{background:#e1e9e3}.scroll{overflow:auto}.chips{display:flex;gap:8px;flex-wrap:wrap}.chips button{font-size:13px;padding:6px 10px}.chips button[aria-pressed=true]{background:#203b40;color:white}.large{font-size:19px}.gallery img{width:100%;max-height:1050px;object-fit:contain;cursor:zoom-in}details{padding:14px 0;border-bottom:1px solid var(--line)}summary{cursor:pointer}pre{padding:20px;background:#e5eae4;white-space:pre-wrap;overflow:auto;font-size:13px}textarea{width:100%;min-height:100px;padding:12px;background:#fffdf8;border:1px solid var(--line)}label{display:block;margin:10px 0 5px}.feedback-item{padding:14px;border-bottom:1px solid var(--line);white-space:pre-wrap}.feedback-item button{float:right}.empty{color:#667c7e}dialog{border:0;padding:0;width:97vw;max-width:97vw;height:95vh;max-height:95vh;background:var(--paper)}dialog::backdrop{background:#071316df}.zoom-head{display:flex;gap:12px;padding:12px;align-items:center}.zoom-head strong{margin-right:auto}.zoom-scroll{height:calc(100% - 70px);overflow:auto;text-align:center}.zoom-scroll img{max-width:100%;max-height:100%;object-fit:contain}footer{padding:35px 5vw;color:#64787b;font-size:13px}#refMeta{min-height:110px}@media(max-width:750px){main{padding:0 14px}.pair,.quad{gap:8px}.photo{max-height:550px}.metrics{gap:20px}th,td{min-width:130px}.zoom-head{flex-wrap:wrap}.toolbar label{width:100%}}'''

CSS+='select{max-width:100%;min-width:0}.marks[hidden]{display:none}'

JS=r'''
const D=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);
let current='nw_day',feedback=[];const storage='haf-customs-v2-'+D.hash;
try{feedback=JSON.parse(localStorage.getItem(storage)||'[]')}catch(e){}
const options=(el,items)=>{for(const [id,name] of items){let o=document.createElement('option');o.value=id;o.textContent=name;el.append(o)}};
options($('view'),Object.entries(D.views).map(([k,v])=>[k,v.label]));options($('detailView'),Object.entries(D.views).map(([k,v])=>[k,v.label]));options($('fbView'),Object.entries(D.views).map(([k,v])=>[k,v.label]));
options($('photoSelect'),D.photos.map(p=>[p.id,p.id+' · '+p.use]));options($('fbPart'),D.decisions.map(p=>[p.component_id,p.component_id]));
function choose(id){current=id;$('view').value=id;const v=D.views[id];$('v1').src=v.v1;$('v2').src=v.v2;$('compareTitle').textContent=v.label;$('compareNote').textContent=D.notes[id]||'相同包围体、相机、正交尺度与日光条件。图片可点击放大。';document.querySelectorAll('.marks').forEach(m=>m.style.display=(id==='nw_day'&&$('annotations').checked)?'':'none');$('fbView').value=id}
$('view').onchange=e=>choose(e.target.value);$('annotations').onchange=()=>choose(current);choose('nw_day');
function detail(id){$('detailView').value=id;$('detail').src=D.views[id].v2;$('detailTitle').textContent=D.views[id].label}
$('detailView').onchange=e=>detail(e.target.value);detail('entrance');
function reference(id){const p=D.photos.find(p=>p.id===id);$('photoSelect').value=id;$('reference').src=p.src;$('refTitle').textContent=p.id+' · '+p.use;$('refMeta').textContent=p.note;let a=document.createElement('a');a.href=p.url;a.target='_blank';a.rel='noreferrer';a.textContent='查看原始来源 ↗';$('refMeta').append(document.createElement('br'),a)}
$('photoSelect').onchange=e=>reference(e.target.value);reference('img-nc-11');
function quads(){for(const q of ['se','sw','ne','nw'])$('q_'+q).src=D.views[q+'_'+$('mode').value].v2} $('mode').onchange=quads;quads();
for(const b of document.querySelectorAll('[data-component]'))b.onclick=()=>{const i=Number(b.dataset.component),c=D.decisions[i];$('fbPart').value=c.component_id;reference(D.photos.some(p=>p.id===c.evidence[0])?c.evidence[0]:'img-nc-11');detail(D.componentViews[c.component_id]||'overview');$('research').scrollIntoView({block:'start'})};
function zoom(src,name){$('zoomImage').src=src;$('zoomName').textContent=name;$('zoomImage').style.maxWidth='100%';$('zoomImage').style.maxHeight='100%';$('zoom').showModal()}
document.querySelectorAll('img[data-zoom]').forEach(im=>im.onclick=()=>zoom(im.src,im.alt));$('zoomClose').onclick=()=>$('zoom').close();$('zoomActual').onclick=()=>{const full=$('zoomImage').style.maxWidth==='none';$('zoomImage').style.maxWidth=full?'100%':'none';$('zoomImage').style.maxHeight=full?'100%':'none'};
function saveFeedback(){try{localStorage.setItem(storage,JSON.stringify(feedback))}catch(e){}renderFeedback()}
function renderFeedback(){$('feedbackList').replaceChildren();for(const [i,f] of feedback.entries()){const box=document.createElement('div');box.className='feedback-item';const b=document.createElement('button');b.textContent='删除';b.onclick=()=>{feedback.splice(i,1);saveFeedback()};box.textContent=f.component_id+' / '+f.view+'\n'+f.problem+'\n建议：'+f.change;box.append(b);$('feedbackList').append(box)}$('feedbackCount').textContent=feedback.length+' 条反馈；保存在当前浏览器，可导出带回下一轮。'}
$('feedbackForm').onsubmit=e=>{e.preventDefault();feedback.push({component_id:$('fbPart').value,view:$('fbView').value,problem:$('problem').value,change:$('change').value,source:$('evidence').value,baseline_nbt_sha256:D.hash,run:D.run,created_at:new Date().toISOString()});$('problem').value='';$('change').value='';saveFeedback()};
$('exportFeedback').onclick=()=>{const a=document.createElement('a'),u=URL.createObjectURL(new Blob([JSON.stringify({schema:'haf-component-feedback-1',case:'guangzhou_customs',run:D.run,baseline_nbt_sha256:D.hash,items:feedback},null,2)],{type:'application/json'}));a.href=u;a.download='Guangzhou_Customs_HAF_V2_Feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};renderFeedback();
'''

def main():
 m=j(R/'manifest.json');checks=j(R/'validation_v2.json');dec=j(CASE/'research/v2/component_decisions.json');photos=j(CASE/'research/v2/image_manifest.json')
 a=j(P/'render_report.json');v1={r['camera']['id']:r for folder in ('V1_r04','V1_compare_extra') for r in j(CASE/'review/previews'/folder/'render_report.json')}
 views={}
 for r in a:
  k=r['camera']['id'];q=CASE/'review/previews/V1_r04'/r['image']
  if not q.exists():q=CASE/'review/previews/V1_compare_extra'/r['image']
  assert k in v1 and v1[k]['camera']==r['camera'],f'camera differs: {k}'
  for fp,rec in [(q,v1[k]),(P/r['image'],r)]:
   with Image.open(fp) as im:im.load()
   assert hashlib.sha256(fp.read_bytes()).hexdigest()==rec['sha256'],f'preview integrity: {fp}'
  views[k]={'label':LABEL[k],'v1':uri(q),'v2':uri(P/r['image'])}
 assert len(views)==27
 ps=[]
 for p in photos:
  ps.append({'id':p['image_id'],'src':small_photo(CASE/p['local_path']),'url':p.get('page_url',p.get('source_page_url')),'use':p['adoption'],'note':'原图 '+str(p['actual_pixels'])+'；'+(p.get('attribution') or p.get('creator') or '版权归原权利人')+'。'+('与 img-nc-02 近重复，不算新增方向。' if p['image_id']=='img-nc-12' else '')})
 notes={'nw_day':'红：普通窗墙突出翼；绿：上部环绕横带；黄：体块之间的竖向进退；蓝：独立侧拱门与宽台阶。画圈是人工检查区域，不是自动误差评分。','crown_rear':'中央上段进深 48→24 格；下段 48→32 格。钟室13×13格保留，补阶梯底座。数值是试作假设，非测绘结论。','top':'正俯视用于检查实际生成的平面关系；不代表已经取得建筑实测屋顶图。模型上方为 -Z，地理北未标定。','plan_25':'y=25 的水平剖切，检查裙楼、入口、内退墙与凸出翼。图是NBT切面，不是建筑图纸。','plan_65':'y=65 的水平剖切，检查中央体与两翼进深；内部房间为游戏伪内饰。','plan_110':'y=110 的水平剖切，检查上段中央体及两肩退台。','podium_oblique':'新增侧照帮助区分两侧：模型-X为大拱门侧，+X为普通窗墙侧；后侧为内退墙及突出翼。精确位置仍需平面证据复核。'}
 data={'hash':m['sha256'],'run':RUN,'views':views,'photos':ps,'decisions':dec['rows'],'notes':notes,'componentViews':{'central_mass':'crown_rear','front_facade':'front','upper_band':'crown','podium_massing':'podium_oblique','side_portal':'podium_oblique','front_colonnade':'entrance','door_soffit':'entrance','roof_finish':'top','interior_lighting':'night'}}
 rows=''.join('<tr><td><button data-component="'+str(i)+'">'+esc(c['component_id'])+'</button></td><td>'+esc(c['decision'])+'</td><td>'+esc(', '.join(c['evidence']) or '游戏表达规则')+'</td><td>'+esc(c['confidence'])+'</td></tr>' for i,c in enumerate(dec['rows']))
 marks='''<svg class="marks" viewBox="0 0 1000 1250" preserveAspectRatio="none"><ellipse cx="250" cy="960" rx="140" ry="95" stroke="#e45d4a"/><text x="115" y="880" fill="#c43c2e">突出翼</text><ellipse cx="680" cy="475" rx="140" ry="35" stroke="#42a96d"/><text x="700" y="440" fill="#237641">横带</text><ellipse cx="555" cy="700" rx="68" ry="230" stroke="#dfb42d"/><text x="590" y="700" fill="#a07800">进退</text><ellipse cx="785" cy="985" rx="135" ry="95" stroke="#368bdb"/><text x="780" y="890" fill="#1768b0">侧入口</text></svg>'''
 downloads=''
 for file,label in [(R/'import_pack'/f'{STEM}.schem','下载 .schem'),(R/'building.nbt','下载 .nbt'),(R/'materials.csv','材料清单 CSV')]:
  downloads+=f'<a class="download" download="{STEM+file.suffix if file.suffix in (".schem",".nbt") else STEM+"_Materials.csv"}" href="{uri(file,"application/octet-stream")}">{label}</a>'
 tests=''.join(f'<tr><td>{esc(c["test"])}</td><td>{"通过" if c["pass"] else "失败"}</td></tr>' for c in checks['checks'])
 parts=[f'''<section id="compare"><h2>01 / 先看形体，再看细节</h2><p class="large">保留 V1；V2 从中央楼体、横带、凹槽和裙楼重新对应照片。相机与高度包络固定。</p><div class="metrics"><div><b>{m['non_air_blocks']:,}</b>实际非空气方块</div><div><b>11 张</b>已逐张查看的建筑照片</div><div><b>27 个</b>每版可对照视角</div></div><div class="toolbar"><label for="view">对照视角</label><select id="view"></select><label><input id="annotations" type="checkbox" checked> 四色检查区（西北日景）</label></div><h3 id="compareTitle"></h3><p class="note" id="compareNote"></p><div class="pair"><figure><figcaption>V1 · 原始基线</figcaption><div class="frame"><img id="v1" alt="V1 同机位" data-zoom>{marks}</div></figure><figure><figcaption>V2 · 构件校正</figcaption><div class="frame"><img id="v2" alt="V2 同机位" data-zoom>{marks}</div></figure></div></section>''',
 '''<section id="research"><h2>02 / 照片 → 构件 → 几何</h2><p>没有四张或六张上限。本轮复核11张建筑照片，其中部分是补用旧资料包中未采用的大图，另新增一张有效侧照；近重复、低清与遮挡图分别标记。不能把11张照片说成11个独立方向。</p><div class="toolbar"><label for="photoSelect">参考照片</label><select id="photoSelect"></select><label for="detailView">V2 对应视角</label><select id="detailView"></select></div><div class="pair"><figure><figcaption id="refTitle"></figcaption><img id="reference" class="photo" alt="实景建筑参考" data-zoom><div id="refMeta" class="sourcebox"></div></figure><figure class="gallery"><figcaption id="detailTitle"></figcaption><img id="detail" alt="V2 构件细节" data-zoom></figure></div><p class="muted">实景与模型采用不同相机，供构件辨认，未做相机恢复或像素级配准。底部可继续记录不准确之处。</p><div class="scroll"><table><thead><tr><th>构件（点选对应图）</th><th>本轮实际修改</th><th>证据</th><th>可信度/限制</th></tr></thead><tbody>'''+rows+'''</tbody></table></div></section>''',
 '''<section id="four"><h2>03 / 四个45°全景</h2><div class="toolbar"><label for="mode">日夜</label><select id="mode"><option value="day">日间</option><option value="night">夜间游戏方案</option></select></div><p class="muted">东南、西南、东北、西北均按模型坐标，东+X、北-Z；真实地理北尚未标定。夜景为暖冷混合、稳定随机占用方案，没有可靠实景夜照支持。</p><div class="quad">'''+''.join(f'<figure><figcaption>{label} 45°</figcaption><img id="q_{q}" alt="{label}四向预览" data-zoom></figure>' for q,label in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')])+'''</div></section>''',
 f'''<section id="files"><h2>04 / 建筑文件与材料</h2>{downloads}<p>建筑包另外含3个分区NBT与偏移表。Sponge v3 schematic包含空气；建议在新的空白区域试导入。稀疏NBT不清除旧方块，不能直接覆盖V1后当作干净的V2。格式 DataVersion 3955；Minecraft客户端兼容性与实际导入仍待测试。</p><p>占用范围 {m['size_xyz']} 格；约定地面 y=4、总高度试作包络137格。{m['material_types']}种材料 / {m['state_types']}种方块状态；半砖、玻璃片、铁栏杆等已进入实际输出。</p><p class="note">源码包保留V1适配器与参数、V2构件代码、逐图记录、反馈依据、测试与内部修订记录。HAF共享核心未改写；旧版本没有被覆盖。</p></section>''',
 '''<section id="limits"><h2>05 / 哪些还不能宣称准确</h2><p>本轮检查了OSM粗轮廓和卫星区域影像，但高层倾倒、遮挡及轮廓口径未解决，没有可靠的实测屋顶平面。V2俯视与剖切展示的是生成结果，不能反过来当实景证据。</p><ul><li>中央体进深、裙楼退入深度与侧入口尺度，仍是多视角解释后的可调参数。</li><li>103/114/137米的高度资料存在不同口径；保持137格便于与V1比较，不声称精确1:1。</li><li>窗列、细小拱券、圆柱、钟面和门的纹样受方块尺度限制，尤其钟面仍较符号化。</li><li>未见完整背面和室内图纸；隐藏围护按连续性补全，房间和灯光为游戏设计。</li><li>没有使用SKP；没有训练神经网络权重；没有完成Minecraft游戏内验收。</li></ul></section>''',
 f'''<section id="checks"><h2>06 / 技术检查与修订记录</h2><p>{checks['passed']}/{checks['total']}项案例检查通过；23项原有共享测试通过。NBT独立回读、Schem回读及分区合并均做精确方块状态对照。技术通过不代表建筑还原度已获认可。</p><details><summary>展开案例检查</summary><table>{tests}</table></details><p>内部修订检查并修复了：收窄中央体后旧楼梯穿出背墙、少量窗位被檐口覆盖、旧绿化与新侧台阶冲突。最终检查直接读取交付NBT，不只检查参数。</p><pre>python3 tools/agent.py --case guangzhou_customs --run MY_V2_RUN
python3 cases/guangzhou_customs/src/validate_v2.py MY_V2_RUN
python3 tools/render_building_case.py --case guangzhou_customs --run MY_V2_RUN
python3 tools/package_building_case.py --case guangzhou_customs --run MY_V2_RUN --name Customs_Custom</pre><p class="muted">案例仍是显式几何规则，尺寸大幅变化时需同步核对窗列、出入口、内部楼梯及相机。不是任意建筑自动建模器。</p></section>''',
 '''<section id="feedback"><h2>07 / 把下一条反馈落在具体位置</h2><form id="feedbackForm"><div class="toolbar"><label for="fbPart">构件</label><select id="fbPart"></select><label for="fbView">视角</label><select id="fbView"></select></div><label for="problem">哪里仍不像，或哪些应保留</label><textarea id="problem" required></textarea><label for="change">希望如何修改</label><textarea id="change" required></textarea><label for="evidence">参考链接 / 图片编号（可选）</label><input id="evidence" style="width:100%;padding:10px"><div class="toolbar"><button type="submit">记录反馈</button><button type="button" id="exportFeedback">导出反馈JSON</button></div></form><p id="feedbackCount"></p><div id="feedbackList"></div></section>''']
 page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州海关 V2 · HAF 构件复核与V1对照</title><style>'+CSS+'</style></head><body><header><small>HAF 0.2 · GUANGZHOU CUSTOMS / V2</small><h1>从四张照片，<br>走向逐个构件的核对。</h1><p>花城大道83号广州新海关 · 2026.10.24<br>中央楼体、两翼、裙楼、柱廊、侧入口和钟冠分开处理。保留原始V1，交付可以比较、追踪与继续返工的V2。</p></header><nav><a href="#compare">V1/V2对照</a><a href="#research">照片与构件</a><a href="#four">四向日夜景</a><a href="#files">建筑与材料</a><a href="#limits">待核实</a><a href="#feedback">记录反馈</a></nav><main>'+''.join(parts)+'</main><footer>最终 '+RUN+' / NBT SHA-256: '+m['sha256']+'<br>图片为真实方块输出的离线几何预览，不是Minecraft截图；参考照片版权归各原作者。</footer><dialog id="zoom"><div class="zoom-head"><strong id="zoomName"></strong><button id="zoomActual">适应 / 原始尺寸</button><button id="zoomClose">关闭</button></div><div class="zoom-scroll"><img id="zoomImage" alt="放大图"></div></dialog><script id="data" type="application/json">'+json.dumps(data,ensure_ascii=False).replace('</','<\/')+'</script><script>'+JS+'</script></body></html>'
 dest=OUT/(STEM+'_Review.html');dest.write_text(page)
 shutil.copy2(R/'materials.csv',OUT/(STEM+'_Materials.csv'))
 shutil.copy2(P/'overview.png',OUT/(STEM+'_Overview.png'))
 # Exact rendered-image layouts, with labels only; no generated architecture.
 fp=os.environ.get('HAF_CJK_FONT',str(ROOT.parent/'NotoSansCJKsc-Regular.otf'))
 font=ImageFont.truetype(fp,42) if Path(fp).exists() else ImageFont.load_default()
 sm=ImageFont.truetype(fp,26) if Path(fp).exists() else ImageFont.load_default()
 for mode in ('day','night'):
  im=Image.new('RGB',(3120,1185),'#f3f0e9');d=ImageDraw.Draw(im);d.text((24,15),'广州新海关 V2 · '+('日间四向' if mode=='day' else '夜间四向'),font=font,fill='#223b40')
  for i,(q,label) in enumerate([('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]):
   src=Image.open(P/f'{q}_{mode}.png').convert('RGB');src.thumbnail((750,1000));x=24+i*774
   d.text((x,80),label+' 45° · 模型坐标',font=sm,fill='#223b40');im.paste(src,(x,130))
  im.save(OUT/(STEM+'_Four_Views_'+mode.title()+'.png'))
 im=Image.new('RGB',(2460,1690),'#f3f0e9');d=ImageDraw.Draw(im)
 for i,(run,label) in enumerate([('V1_r04','V1 原始基线'),(RUN,'V2 中央体与裙楼校正')]):
  src=Image.open(CASE/'review/previews'/run/'nw_day.png').convert('RGB');src.thumbnail((1180,1475));x=30+i*1220
  d.text((x,20),label,font=font,fill='#223b40');im.paste(src,(x,90))
 d.text((30,1600),'同相机 / 同高度包络 / NBT真实几何预览；细节与俯视对照见HTML',font=sm,fill='#223b40');im.save(OUT/(STEM+'_V1_V2_Compare.png'))
 print(json.dumps({'html':str(dest),'bytes':dest.stat().st_size,'views_per_version':len(views),'photos':len(ps),'run':RUN},ensure_ascii=False))

if __name__=='__main__':main()
