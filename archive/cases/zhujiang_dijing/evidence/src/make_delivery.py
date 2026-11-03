"""Offline case report and exact-preview boards; no AI-generated pictures."""
from pathlib import Path
import base64,collections,csv,hashlib,html,io,json,os,shutil,sys
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[3];CASE=Path(__file__).resolve().parents[1]
RUN='V1_r03';R=CASE/'runs'/RUN;P=CASE/'review/previews'/RUN;OUT=ROOT/'deliverables/zhujiang_dijing_v1';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def png(path,im):
    q=io.BytesIO();im.save(q,format='PNG');atomic(path,q.getvalue())
def jpguri(path,maxdim=1900):
    im=Image.open(path).convert('RGB');im.thumbnail((maxdim,maxdim));buf=io.BytesIO();im.save(buf,format='JPEG',quality=90);return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,26);small=ImageFont.truetype(fontpath,19)
def board(name,frames,title,cols=2,cell=(1200,920)):
    cw,ch=cell;rows=(len(frames)+cols-1)//cols;im=Image.new('RGB',(cols*cw,80+rows*ch),'#f0eee7');dr=ImageDraw.Draw(im);dr.text((28,22),title,font=font,fill='#19362e')
    for i,(id,label) in enumerate(frames):
        x=(i%cols)*cw;y=80+(i//cols)*ch;src=Image.open(P/(id+'.png')).convert('RGB');src.thumbnail((cw-24,ch-65));im.paste(src,(x+(cw-src.width)//2,y+48+(ch-65-src.height)//2));dr.text((x+18,y+12),label,font=small,fill='#19362e')
    png(OUT/name,im)
def esc(x):return html.escape(str(x))

def main():
    params=read(R/'params_used.json');manifest=read(R/'manifest.json');val=read(R/'validation.json');imgs=read(CASE/'research/image_manifest.json');components=read(CASE/'research/component_evidence.json');imports=read(R/'import_pack/import_manifest.json');records=read(R/'construction_records.json');rooms=read(R/'interiors.json')
    expected=[x['id'] for x in read(CASE/'cameras.json')]+[f'{q}_{m}' for q in ['se','sw','ne','nw'] for m in ['day','night']]
    renders=[]
    for id in expected:
        path=P/(id+'.png')
        with Image.open(path) as im:
            im.load();assert im.info['source_nbt_sha256']==manifest['sha256'];cam=json.loads(im.info['camera']);assert cam['id']==id
        renders.append({'image':path.name,'sha256':sha(path),'source_nbt_sha256':manifest['sha256'],'camera':cam,'metadata_verified':True})
    (P/'verified_render_manifest.json').write_text(json.dumps(renders,indent=2))
    for id,name in [('overview','Zhujiang_Dijing_V1_Overview.png'),('top','Zhujiang_Dijing_V1_Top.png'),('front_night','Zhujiang_Dijing_V1_Night.png')]:shutil.copy2(P/(id+'.png'),OUT/name)
    board('Zhujiang_Dijing_V1_Four_Day.png',[(q+'_day',q.upper()+'  |  MODEL COORDINATES') for q in ['se','sw','ne','nw']],'ZHUJIANG DIJING  /  V1  /  FOUR DAY VIEWS')
    board('Zhujiang_Dijing_V1_Four_Night.png',[(q+'_night',q.upper()+'  |  SYNTHETIC NIGHT STUDY') for q in ['se','sw','ne','nw']],'ZHUJIANG DIJING  /  V1  /  FOUR NIGHT VIEWS')
    board('Zhujiang_Dijing_V1_Details.png',[(q,label) for q,label in [('balcony','BALCONY / RECESSED GLAZING'),('roof','OPEN CROWN / ROUND CORNICES'),('entrance','SUPPORTED ENTRY / SMALL SIGN'),('garden','LAKE / PAVILION / BRIDGE')]],'ZHUJIANG DIJING  /  V1  /  COMPONENT REVIEW')
    shutil.copy2(R/'materials.csv',OUT/'Zhujiang_Dijing_V1_Materials.csv')
    names={'overview':'楼组与园林全景','night':'全景夜景试验','front':'正面','rear':'背面（窗位估算）','top':'强制俯视图','balcony':'弧形阳台近景','roof':'圆形檐冠与开敞顶架','entrance':'首层入口与承托','garden':'湖岸、桥与凉亭','garden_night':'庭园夜景试验','balcony_underside':'阳台底面仰视','residential_section':'楼层剖切（伪内饰）','interior_plan':'楼层平面剖切（非真实户型）','front_night':'平视夜景：住户亮暗','balcony_night':'窗后近景夜景'}
    for q,ch in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]:
        for mode,cn in [('day','日景'),('night','夜景')]:names[q+'_'+mode]=ch+' 45° '+cn+'（模型坐标）'
    viewcards=[]
    for rr in renders:
        id=rr['camera']['id'];group='top' if id=='top' else 'night' if rr['camera'].get('night') else 'four' if id.endswith('_day') else 'detail' if id in ['balcony','roof','entrance','garden','balcony_underside','residential_section','interior_plan'] else 'overview'
        viewcards.append(f'<figure class="model-card" data-group="{group}"><img loading="lazy" src="{jpguri(P/rr["image"])}" alt="{names[id]}"><figcaption>{names[id]}</figcaption></figure>')
    refs=''
    for a in imgs:
        refs+=f'<figure class="ref-card"><img loading="lazy" src="{jpguri(CASE/"research"/a["file"],1000)}" alt="{esc(a["title"])}"><figcaption><b>{a["image_id"]} · {esc(a["title"])}</b><p>{esc(a["observation"])}</p><small>{"采用形态/关系" if a["adopted"] else "排除或仅作位置对照"} · {a["pixels"][0]}×{a["pixels"][1]} · <a href="{esc(a["source_page"])}">来源页</a></small></figcaption></figure>'
    rows=''.join(f'<tr><td><code>{esc(a["component_id"])}</code></td><td>{esc(a["observation_or_proposal"])}</td><td>{esc(a["limitations"])}</td><td>{esc(", ".join(x["image_id"] for x in a["image_regions"]) or "程序化补全")}</td></tr>' for a in components)
    checks=''.join(f'<tr><td>{esc(a["id"])}</td><td class="pass">{a["status"]}</td><td><details><summary>查看依据</summary><pre>{esc(json.dumps(a["detail"],ensure_ascii=False,indent=2))}</pre></details></td></tr>' for a in val['checks'])
    materials=list(csv.DictReader((R/'materials.csv').read_text(encoding='utf-8-sig').splitlines()));materials.sort(key=lambda x:-int(x['count']))
    material_table=''.join(f'<tr><td>{esc(x["block_id"])}</td><td>{int(x["count"]):,}</td><td>{x["stacks"]} 组＋{x["remainder"]}</td></tr>' for x in materials)
    lit=sum(x['actual_lamp'] is not None for x in rooms)
    stats=f'<div class="stats"><div><b>{manifest["non_air_blocks"]:,}</b>非空气方块</div><div><b>232 × 104 × 190</b>场景包围盒 / X,Y,Z</div><div><b>{len(renders)}</b>最终 NBT 同源视图</div><div><b>{imports["module_count"]}</b>可拼合 NBT 分块</div></div>'
    sections=[
    ('01','范围与结果',f'<p>广州珠江帝景苑 · 赏湖轩型湖畔住宅代表楼组 V1。按你选择的“代表楼组＋园林”，完成三段连续住宅立面、局部水景、石桥、圆顶凉亭与绿化。具体栋号、实测楼间距尚未确认，<b>这是一版可修改的研究性近似，不是整个小区或指定栋号的测绘复原。</b></p>{stats}<img class="hero" src="{jpguri(P/"overview.png")}"><p class="note">本报告全部建筑图来自最终 NBT 回读。当前 HAF 0.2；未发布 HAF 0.3。没有使用 SU，也没有神经网络训练。</p>'),
    ('02','对象、年代与来源','<p>以广州海珠区珠江帝景苑既有住宅为对象。园区导览图用于区分赏湖轩、克莱公寓等组团；本轮不采用新组团效果图，不把高塔或酒店穹顶并入住宅。照片以既有实景为主，拍摄年代不齐，无法宣称完整代表当前逐户装修状态。</p><p><a href="https://www.sohu.com/a/515988281_120715667">园区与楼组调查</a> · <a href="https://gz.esf.fang.com/loupan/2812200072.htm">赏湖轩实景相册</a> · <a href="https://gz.esf.fang.com/loupan/2811022276/photo/">同苑立面细节相册</a>。这些是图像与身份研究来源，未取得原设计图或实测资料。</p>'),
    ('03','建筑解读','<p>重点保留米黄色主体、浅绿窗面、浅弧长阳台、半圆端部窗、连续竖向墙柱、圆形檐冠和开敞顶架。住宅玻璃门窗退在栏板后面，中间保留阳台空间。首层门廊落在连续平台上，招牌只用三个单格金色标记。</p><p>湖岸、石桥、圆顶凉亭、棕榈及成片低绿篱分别研究。园林位置是局部裁切后的解释性布置，植被和住户改装的复杂程度仍低于实景。</p>'),
    ('04','尺度、平面与朝向','<p>采用统一研究比例 2 格/米，以约 3 米住宅层高设置 6 格层间距；首层＋12 层住宅作为本轮类型基准。未取得建筑高度测量，不能把游戏尺寸当作实楼测量值。阳台从门窗到外栏最大 5 格（研究尺度约 2.5 米），在第一轮近景复核后收紧。</p><p>场景 232×104×190 格，工作坐标 +X 为东、−Z 为北，住宅正面为 +Z；未标定真实地理朝向。俯视图是输出模型正交投影，导览图只是布局参考，不是正射图。</p>'),
    ('05','多向参考盒与排除记录',f'<p>下载16份图像，字节去重后15份。ref15与ref14完全相同，不增加覆盖；只有支持本轮构件的图参与执行。其他组团、入口、红顶木亭等候选保留排除理由。图像数量没有人为上限。未找到可核对的本楼组夜景，不能用从住宅眺望广州塔的夜景充当证据。</p><div class="refs">{refs}</div>'),
    ('06','构件证据与执行','<div class="table"><table><thead><tr><th>构件 ID</th><th>采用关系</th><th>限制</th><th>证据</th></tr></thead><tbody>'+rows+'</tbody></table></div>'),
    ('07','生成逻辑与修订','<p>沿用 HAF 的方块状态、楼层、房间灯光和窗后陈设能力，新建本案例适配器。共享表达仅补浅绿玻璃／玻璃片和静水：水不会被当成栏杆的实体连接支撑；预览为静态近似，不模拟流体。</p><p>r01 → r02：补足柱脚31个漏承托采样格；移开挡住通行测试区的花盆；打通36处被墙遮挡的门窗采样。r02 → r03：收紧阳台进深，让玻璃、可用空间和栏板比例更接近参考。原始失败 run、参数、源码快照都保留。</p><p>216个窗后房间采用固定ID与种子，书架、台面、座椅、盆栽有承托检查。这些是伪内饰，未建真实户型、完整楼梯电梯或可游玩全楼。夜景保留暗窗，'+str(lit)+'个房间放置灯具，暖冷搭配是住宅效果试验。</p>'),
    ('08','全方位审阅与材料','<p>点击图片放大。四向采用同一尺度和俯角；夜景另给平视近景，以检查被阳台遮挡的室内光。日夜同一份模型，光效不是游戏截图。</p><div class="filters">'+''.join(f'<button data-filter="{x}">{s}</button>' for x,s in [('all','全部'),('overview','全景 / 正背面'),('four','四向日景'),('night','夜景'),('top','俯视'),('detail','细节 / 剖切')])+'</div><div class="views">'+''.join(viewcards)+'</div><details><summary>展开完整材料清单</summary><div class="table"><table><thead><tr><th>方块</th><th>数量</th><th>64格/组</th></tr></thead><tbody>'+material_table+'</tbody></table></div></details>'),
    ('09','验证、导入与未完成项',f'<p>14项案例文件／几何检查通过；23项原有共享测试＋4项新增材料测试通过。Sponge v3 与8个稀疏 NBT 分块均回读核对，分块重组坐标与状态完全一致。<b>游戏导入、碰撞、完整通行和实际灯光仍待验证。</b></p><div class="table"><table><tbody>{checks}</tbody></table></div><p>DataVersion 3955。整栋 .schem（含空气）与稀疏 .nbt／分块（二者不清空未写入位置）择一导入，不叠放。分块原点等于总原点加 module_offsets.csv。世界高度需要满足原点Y＋104≤最高Y排他上界，且原点Y≥最低Y；分块不会增加世界高度。</p><p class="note">主要缺口：精确栋号和平面、背面开窗位置、各户封窗差异、真实夜间灯位、园林密度与岸线测量、资源包材质和流体效果。当前三单元较规则；不能以测试通过替代还原度评价。</p>'),
    ('10','经验、反馈与 HAF 0.3','<p>本轮积累住宅阳台前后层次、开敞顶架、承托复检、静水与玻璃片、窗后灯光可见性。它们已经写入案例学习记录及测试；还不是通用建筑自动识别能力。继续等你审阅，并完成更多独立结构案例后，再整理 HAF 0.3。</p><label for="component">反馈部位</label><select id="component">'+''.join(f'<option>{esc(a["component_id"])}</option>' for a in components)+'</select><label for="feedback">观察和期望修改</label><textarea id="feedback" rows="5" placeholder="例如：阳台还要再浅一点；屋顶圆环太粗；这里应为独立楼栋……"></textarea><button id="download-feedback">下载本轮反馈 JSON</button><p>源码包中保留参数、稳定构件 ID、研究图、原始运行记录、验证脚本和反馈模板。可据具体构件修改并固定相机对照。</p>')]
    nav=''.join(f'<a href="#s{n}">{n} {t}</a>' for n,t,_ in sections)
    body=''.join(f'<section id="s{n}"><div class="eyebrow">{n} / HAF CASE STUDY</div><h2>{t}</h2>{content}</section>' for n,t,content in sections)
    doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>珠江帝景苑 V1 · HAF 住宅楼组研究</title><style>
*{box-sizing:border-box}body{margin:0;background:#eeeae1;color:#20332b;font:16px/1.8 system-ui,-apple-system,"Microsoft YaHei",sans-serif}header{padding:54px 6vw 40px;background:#163d32;color:#faf4df}h1{font-size:clamp(30px,4vw,58px);line-height:1.2;margin:15px 0}header p{max-width:850px;color:#d4dfd1}.eyebrow{font-size:12px;letter-spacing:2px;color:#7e937f}nav{position:sticky;top:0;z-index:3;display:flex;gap:20px;overflow:auto;padding:12px 4vw;background:#f7f4ecf5;border-bottom:1px solid #d0d4c9}nav a{white-space:nowrap;font-size:13px;color:#254c3e;text-decoration:none}main{max-width:1500px;margin:auto;padding:20px 3vw}section{padding:42px 0;border-bottom:1px solid #c8cec0;scroll-margin-top:65px}h2{font-size:29px;margin:8px 0 20px}p{max-width:1100px}a{color:#14694a}img{max-width:100%;display:block;cursor:zoom-in}.hero{width:100%;border-radius:10px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:25px 0}.stats div{padding:20px;background:#faf7ef;border:1px solid #d8dccf;border-radius:8px;font-size:12px}.stats b{font-size:25px;display:block}.note{padding:18px 22px;background:#e4e5ce;border-left:4px solid #8a8f55}.refs,.views{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:0;background:#faf7ef;border:1px solid #d5d8cc;border-radius:8px;overflow:hidden}figure img{width:100%;object-fit:contain}.ref-card img{height:350px}.model-card img{aspect-ratio:1.3}.ref-card p{font-size:14px;margin:8px 0}figcaption{padding:14px 18px}small{font-size:12px;color:#647563}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px;background:#f7f4ec}th,td{text-align:left;padding:12px;border-bottom:1px solid #d6dacd;vertical-align:top}th{background:#e4e9dc}code{font-size:12px;word-break:break-word}pre{white-space:pre-wrap;max-height:250px;overflow:auto}.pass{color:#19724f}details{margin:18px 0}summary{cursor:pointer}.filters{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}button{background:#204f3e;color:white;padding:10px 18px;border:0;border-radius:5px;cursor:pointer}label{display:block;margin-top:14px}select,textarea{display:block;width:100%;max-width:1000px;padding:12px;font:inherit;border:1px solid #b2c2ac;border-radius:5px;background:#fbf9f3}textarea{margin-bottom:15px}dialog{border:0;padding:12px;max-width:96vw;max-height:96vh;background:#101b17}dialog::backdrop{background:#000b}dialog img{max-height:86vh;max-width:92vw;object-fit:contain}dialog button{float:right}.hidden{display:none}footer{padding:35px 5vw;color:#61705f;font-size:13px}@media(max-width:760px){.refs,.views{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.ref-card img{height:auto}h2{font-size:24px}main{padding:0 18px}}
</style><header><div>HAIBARAAI / HAF 0.2 / RESIDENTIAL STUDY</div><h1>广州珠江帝景苑<br>湖畔住宅楼组 V1</h1><p>弧形阳台 · 浅绿玻璃 · 开敞顶架 · 园林水景<br>代表楼组研究性近似 / 最终运行 V1_r03 / 等待还原度反馈</p></header><nav>'''+nav+'</nav><main>'+body+'''</main><footer>同源预览与可重放工程。地理朝向未标定；游戏测试 pending。图片来源及限制见第 05 节。</footer><dialog id="zoom"><button id="close">关闭</button><img alt="放大预览"></dialog><script>
const dialog=document.querySelector('#zoom');document.querySelectorAll('main img').forEach(im=>im.addEventListener('click',()=>{dialog.querySelector('img').src=im.src;dialog.showModal()}));document.querySelector('#close').onclick=()=>dialog.close();
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>document.querySelectorAll('.model-card').forEach(c=>c.classList.toggle('hidden',b.dataset.filter!=='all'&&c.dataset.group!==b.dataset.filter)));
document.querySelector('#download-feedback').onclick=()=>{const obj={case:'zhujiang_dijing',baseline:'V1_r03',component_id:document.querySelector('#component').value,feedback:document.querySelector('#feedback').value,status:'user_draft'};const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='Zhujiang_Dijing_V1_Feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
</script></html>'''
    atomic(OUT/'Zhujiang_Dijing_HAF_V1_Review.html',doc.encode())
    print(json.dumps({'files':[x.name for x in OUT.iterdir()],'views':len(renders),'sections':len(sections),'lit_rooms':lit,'source_nbt_sha256':manifest['sha256']},ensure_ascii=False))
if __name__=='__main__':main()
