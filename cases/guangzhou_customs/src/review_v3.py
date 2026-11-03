"""V3 review from exact read-back renders; no synthetic building imagery."""
from pathlib import Path
import argparse,base64,html,io,json,hashlib,os,shutil
from PIL import Image,ImageDraw,ImageFont
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
RUN='V3_r02';STEM='Guangzhou_Customs_HAF_V3';OUT=ROOT/'deliverables/guangzhou_customs_v3'
def j(p):return json.loads(p.read_text())
def uri(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def photo(p):
    im=Image.open(p).convert('RGB');im.thumbnail((1600,1600));b=io.BytesIO();im.save(b,'JPEG',quality=88)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
def esc(x):return html.escape(str(x))
LABEL={'top':'正俯视 · 完整模型','plan_25':'裙楼水平剖切 · y25','plan_65':'主楼水平剖切 · y65','plan_110':'中央上段剖切 · y110','overview':'前斜向全景','night':'前斜向夜景','front':'正面','rear':'背面','left':'左侧','right':'右侧','crown':'钟楼前斜向','crown_rear':'钟楼后斜向','crown_front':'钟楼正面','entrance':'主入口近景','entrance_night':'主入口夜景','podium_rear':'裙楼后右斜向','podium_oblique':'裙楼后左斜向','facade':'立面近景','section':'纵向剖切'}
for q,n in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]:
    for mode,s in [('day','日景'),('night','夜景')]:LABEL[q+'_'+mode]=n+'45° · '+s+'（模型坐标）'

CSS='''*{box-sizing:border-box}body{margin:0;background:#f2f0e8;color:#233b40;font:16px/1.7 system-ui,sans-serif}header{background:#233b40;color:#f8f3e8;padding:48px 5vw}header small{color:#d3ba83;letter-spacing:.15em}h1{font-size:clamp(34px,4.7vw,64px);line-height:1.2;margin:18px 0}h2{font-size:28px}p{max-width:1050px}nav{position:sticky;top:0;padding:12px 4vw;background:#f2f0e8f5;z-index:2;display:flex;gap:22px;overflow:auto;white-space:nowrap;border-bottom:1px solid #bac7c1}a{color:#386974}main{max-width:1800px;margin:auto;padding:0 26px}section{padding:30px 0;border-bottom:1px solid #b9c7c0;scroll-margin-top:60px}.row{display:flex;gap:14px;align-items:center;flex-wrap:wrap}.pair,.quad{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}figure{margin:0;background:#e0e5dc}figcaption{padding:10px 14px;background:#fcfaf3}img{max-width:100%;display:block;cursor:zoom-in}.pair img,.quad img{width:100%;height:auto}.detail{width:100%;max-height:1000px;object-fit:contain;background:#e0e5dc}.note{padding:15px 20px;border-left:4px solid #ad8245;background:#e9e1d1}.muted{color:#5a7074;font-size:14px}button,select,input,textarea{font:inherit;color:inherit;padding:10px 13px;border:1px solid #83978c;border-radius:4px;background:#fffdf5;max-width:100%}button{cursor:pointer}button:hover{background:#dce7db}select{min-width:0}table{border-collapse:collapse;width:100%}th,td{padding:11px;border-bottom:1px solid #cbd4cb;text-align:left;vertical-align:top}th{background:#e0e7dc}.scroll{overflow:auto}textarea{display:block;width:100%;min-height:100px;margin:10px 0}.download{display:inline-block;padding:10px 15px;margin:5px;border:1px solid #83978c;border-radius:4px;text-decoration:none;background:#fffdf5}pre{white-space:pre-wrap;background:#e2e8dd;padding:18px}dialog{border:0;padding:14px;width:96vw;max-width:96vw;height:95vh;max-height:95vh;background:#f2f0e8}dialog::backdrop{background:#07161ee8}.zoomscroll{overflow:auto;height:calc(100% - 65px)}.zoomscroll img{margin:auto;max-width:100%;max-height:100%;object-fit:contain}.fbitem{border-bottom:1px solid #becdc2;padding:16px 0;white-space:pre-wrap}.fbitem button{float:right}footer{padding:30px 5vw;font-size:13px;color:#5c7377;overflow-wrap:anywhere}@media(max-width:800px){main{padding:0 12px}.pair,.quad{grid-template-columns:1fr}h2{font-size:24px}header{padding:30px 20px}}'''
JS=r'''
const D=JSON.parse(document.getElementById('data').textContent),$=x=>document.getElementById(x),key='haf-customs-v3-'+D.hash;
function options(id,rows){for(const [v,n] of rows){const o=document.createElement('option');o.value=v;o.textContent=n;$(id).append(o)}}
options('view',Object.entries(D.views).map(([k,v])=>[k,v.label]));options('detailView',Object.entries(D.views).map(([k,v])=>[k,v.label]));options('photoView',D.photos.map(p=>[p.id,p.label]));options('fbPart',D.parts.map(c=>[c.id,c.id]));
function compare(){let k=$('view').value,v=D.views[k],base=$('base').value;$('before').src=v[base];$('after').src=v.v3;$('beforeLabel').textContent=base.toUpperCase()+' · '+v.label;$('afterLabel').textContent='V3 · '+v.label;$('viewNote').textContent=k.startsWith('plan_')?'水平剖切：隐藏上方几何，仍会看见更低处的屋面与地面；不能把阴影当作该层实体轮廓。':'同包围盒、同相机、同尺度。正俯视的前方在下，后方在上。'}
$('view').onchange=compare;$('base').onchange=compare;$('view').value='top';compare();
function detail(){const k=$('detailView').value;$('detail').src=D.views[k].v3;$('detailLabel').textContent=D.views[k].label}$('detailView').onchange=detail;$('detailView').value='podium_oblique';detail();
function quad(){for(const q of ['se','sw','ne','nw'])$('q_'+q).src=D.views[q+'_'+$('mode').value].v3}$('mode').onchange=quad;quad();
function reference(){let p=D.photos.find(p=>p.id===$('photoView').value);$('photo').src=p.src;$('photoNote').textContent=p.note;$('source').textContent=p.url?'原始来源 ↗':'用户提供的标注/反馈';if(p.url)$('source').href=p.url;else $('source').removeAttribute('href')}$('photoView').onchange=reference;$('photoView').value='user-plan';reference();
document.querySelectorAll('img').forEach(im=>im.onclick=()=>{$('zoomImage').src=im.src;$('zoomImage').style.maxWidth='100%';$('zoomImage').style.maxHeight='100%';$('zoom').showModal()});$('closeZoom').onclick=()=>$('zoom').close();$('actualSize').onclick=()=>{const im=$('zoomImage'),v=im.style.maxWidth==='none'?'100%':'none';im.style.maxWidth=v;im.style.maxHeight=v};
let feedback=[];try{feedback=JSON.parse(localStorage.getItem(key)||'[]')}catch(e){}
function showFeedback(){const list=$('feedbackList');list.replaceChildren();feedback.forEach((f,i)=>{let row=document.createElement('div');row.className='fbitem';let del=document.createElement('button');del.type='button';del.textContent='删除';del.onclick=()=>{feedback.splice(i,1);showFeedback()};let text=document.createElement('span');text.textContent=f.component_id+' · '+f.view+'\n'+f.problem+'\n期望：'+f.change;row.append(del,text);list.append(row)});try{localStorage.setItem(key,JSON.stringify(feedback))}catch(e){}}
$('feedbackForm').onsubmit=e=>{e.preventDefault();if(!$('problem').value.trim())return;feedback.push({component_id:$('fbPart').value,view:$('view').value,problem:$('problem').value,change:$('change').value,source:$('evidence').value,baseline_nbt_sha256:D.hash,run:D.run,date:new Date().toISOString()});$('problem').value='';$('change').value='';showFeedback()};
$('exportFeedback').onclick=()=>{const b=new Blob([JSON.stringify({version:'V3',run:D.run,items:feedback},null,2)],{type:'application/json'});let a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='Guangzhou_Customs_V3_Feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};showFeedback();
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True);r=CASE/'runs'/RUN;p=CASE/'review/previews'/RUN
    m=j(r/'manifest.json');check=j(r/'validation_v3.json');dec=j(CASE/'research/v3/feedback_and_decisions.json');views={};verified=[]
    report=j(p/'render_report.json')
    oldreports={v['camera']['id']:v for v in j(CASE/'review/previews/V2_r06/render_report.json')}
    for rec in report:
        k=rec['camera']['id'];assert rec['camera']==oldreports[k]['camera']
        new=p/rec['image'];assert hashlib.sha256(new.read_bytes()).hexdigest()==rec['sha256']
        with Image.open(new) as im:im.load()
        paths={'v3':new,'v2':CASE/'review/previews/V2_r06'/(k+'.png')}
        v1=CASE/'review/previews/V1_r04'/(k+'.png')
        if not v1.exists():v1=CASE/'review/previews/V1_compare_extra'/(k+'.png')
        paths['v1']=v1
        views[k]={'label':LABEL.get(k,k),**{a:uri(b) for a,b in paths.items()}}
        verified.append({'view':k,'same_camera_as_V2':True,'sha256':rec['sha256']})
    assert len(views)==27
    photos=[]
    for a in dec['references']:
        if 'path' not in a:continue
        photos.append({'id':a['id'],'label':a['id']+' · 用户输入','src':photo(CASE/a['path']),'url':None,'note':'用户标注是本轮形态解释；斜卫星图有高度投影偏移，不能直接量作屋顶/地面统一平面。' if a['id']=='user-plan' else '用户反馈图；模型截图不算独立实景参考。'})
    for a in j(CASE/'research/v2/image_manifest.json'):
        photos.append({'id':a['image_id'],'label':a['image_id']+' · '+a['adoption'],'src':photo(CASE/a['local_path']),'url':a.get('page_url',a.get('source_page_url')),'note':a['adoption']+'。沿用V2已查看证据；摄影方向并非已测地理方位。'})
    data={'run':RUN,'hash':m['sha256'],'views':views,'photos':photos,'parts':dec['components']}
    changes=''.join('<tr><td>'+esc(c['id'])+'</td><td>'+esc(c['change'])+'</td><td>'+esc(' / '.join(c['evidence']))+'</td><td>'+esc(c['confidence'])+'</td></tr>' for c in dec['components'])
    downloads=''.join('<a class="download" download="'+esc(f.name)+'" href="'+uri(f,'application/octet-stream')+'">'+esc(label)+'</a>' for f,label in [(r/'import_pack'/(STEM+'.schem'),'下载 .schem'),(r/'building.nbt','下载完整 .nbt'),(r/'materials.csv','下载材料表')])
    checks=''.join('<tr><td>'+esc(q['test'])+'</td><td>'+('通过' if q['pass'] else '失败')+'</td><td>'+esc(q['evidence'])+'</td></tr>' for q in check['checks'])
    sections=[
     '''<section id="compare"><h2>01 / 先核对俯视形体</h2><p>前横段展开，后部居中收窄；V2的单侧后伸翼已删除。先看倒T，再看钟楼与主楼各层之间的位置。</p><div class="row"><label>基线 <select id="base"><option value="v2">V2</option><option value="v1">V1</option></select></label><label>视角 <select id="view"></select></label></div><p id="viewNote" class="muted"></p><div class="pair"><figure><figcaption id="beforeLabel"></figcaption><img id="before" alt="历史基线"></figure><figure><figcaption id="afterLabel"></figcaption><img id="after" alt="V3相同相机"></figure></div></section>''',
     '<section id="changes"><h2>02 / 反馈如何进入模型</h2><div class="scroll"><table><tr><th>构件</th><th>执行修改</th><th>依据</th><th>限制</th></tr>'+changes+'</table></div><p>前横段101格，居中后段77格，两侧各退12格。中央主楼下段进深32→24格，与上段一致；钟室仍为13×13格。以上是V3的整数化参数，不是实测尺寸。</p></section>',
     '''<section id="detailSection"><h2>03 / 裙楼、后门与层级细节</h2><div class="row"><select id="detailView"></select></div><figure><figcaption id="detailLabel"></figcaption><img id="detail" class="detail" alt="V3细节"></figure><p class="note">三拱形式来自现有实景，V3将其置于后部轴线末端。这个位置属于当前推定，待更明确的背面/平面证据验证。</p></section>''',
     '''<section id="four"><h2>04 / 四个45°全景</h2><select id="mode"><option value="day">日景</option><option value="night">夜景</option></select><p class="muted">东南、西南、东北、西北为模型坐标标签，地理北未标定。夜景是原有暖冷混合游戏方案，不是实景灯位复原。</p><div class="quad">'''+''.join('<figure><figcaption>'+n+'45°</figcaption><img id="q_'+q+'" alt="'+n+'预览"></figure>' for q,n in [('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')])+'</div></section>',
     '''<section id="research"><h2>05 / 原图与新增反馈</h2><p>保留V2的11张研究照片，以及这轮4张用户输入。它们有近重复、模型截图和同图重传，不等于15个独立实景视角；HAF没有图片数量上限。</p><select id="photoView"></select><img id="photo" class="detail" alt="研究原图"><p id="photoNote"></p><a id="source" target="_blank" rel="noreferrer"></a><p class="muted">原图及原始来源记录均在源码包。V2记录保留旧状态；本轮只纠正已被否定的几何解释。</p></section>''',
     '''<section id="logic"><h2>06 / 这次改变的判断规则</h2><p>先区分地面轮廓、裙楼屋面、主楼和钟冠的高度层，再解释斜卫星影像。高处屋顶的位移不能转成地面突出；轴对称是本轮有依据的体块假设，不要求灯光、绿化和所有小构件强行对称。</p><p>粗轮廓参考来自已保存的OpenStreetMap way 313905695（© OpenStreetMap contributors，ODbL）。它支持宽前段与较窄后段的关系，不能替代实测总平。没有使用新SU模型，也没有进行神经网络训练。</p></section>''',
     f'''<section id="files"><h2>07 / 建筑文件与材料</h2>{downloads}<p>{m['non_air_blocks']:,}个非空气方块，包围盒126×148×116格；地面y=4，研究高度137格。建筑包另有3个分区NBT和放置偏移表。</p><p>DataVersion 3955。完整schem写入空气；稀疏NBT不会清除V2的旧突出部分，请在空白区域导入或先清理旧版本。分区共享原点，按偏移表放置。若使用最高Y排他上界320的世界，完整包围盒的原点Y须≤172，并同时检查世界最低Y。</p></section>''',
     f'''<section id="checks"><h2>08 / 文件与几何验证</h2><p>{check['passed']}/{check['total']}项案例检查通过；23项共享测试通过。NBT、Sponge v3和3个分区的方块状态回读一致；27个视角与V2相机一致。69份旧代码/参数/相机/运行文件哈希保持不变。</p><details><summary>展开检查结果</summary><div class="scroll"><table>{checks}</table></div></details><p class="note">这些结果证明文件一致、约束落实，不能证明建筑已经还原准确。游戏导入、碰撞、植物更新与实际光照均未测试。</p></section>''',
     '''<section id="replay"><h2>09 / 保存源码与重跑</h2><p>新增build_v3.py与params_v3.json，复用V1/V2的立面、柱廊、钟楼和HAF导出。原适配器与原run保留。源码包包含反馈、来源、参数、执行代码、校验和预览。</p><pre>python3 cases/guangzhou_customs/src/build_v3.py --run MY_V3_RUN
python3 cases/guangzhou_customs/src/validate_v3.py MY_V3_RUN
python3 tools/render_building_case.py --case guangzhou_customs --run MY_V3_RUN
python3 tools/package_building_case.py --case guangzhou_customs --run MY_V3_RUN --name Customs_V3</pre><p>剩余待核实：精确总平尺寸、真实方位、后门位置、中央体与钟室比例，以及103/114/137米的高度口径。源码里的case_version 0.3.0只代表此建筑V3，HAF主引擎仍为0.2。</p></section>''',
     '''<section id="feedback"><h2>10 / 留下可定位的下一条反馈</h2><p>先在上方选定对比视角，再记录构件。反馈保存在当前浏览器，可导出JSON交给下一轮修改；不自动上传。</p><form id="feedbackForm"><label>构件 <select id="fbPart"></select></label><textarea id="problem" required placeholder="哪里仍然不对"></textarea><textarea id="change" placeholder="希望怎样修改"></textarea><input id="evidence" placeholder="原图编号或参考链接"><div class="row"><button type="submit">保存反馈</button><button type="button" id="exportFeedback">导出反馈 JSON</button></div></form><div id="feedbackList"></div></section>'''
    ]
    page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州新海关 V3 · 倒T形体修订</title><style>'+CSS+'</style></head><body><header><small>HAF 0.2 / GUANGZHOU CUSTOMS V3</small><h1>先把平面关系改对。</h1><p>广州新海关 · 花城大道83号<br>保留V1与V2，修正单侧突出，重建居中的倒T裙楼与分层主楼。</p></header><nav><a href="#compare">俯视对比</a><a href="#changes">修改依据</a><a href="#detailSection">局部</a><a href="#four">四向日夜</a><a href="#files">建筑下载</a><a href="#feedback">记录反馈</a></nav><main>'+''.join(sections)+'</main><footer>最终 '+RUN+' · NBT SHA-256 '+m['sha256']+'<br>预览来自真实NBT方块几何，非Minecraft截图。材质和离线夜光为示意；照片版权归原作者。</footer><dialog id="zoom"><div class="row"><button id="closeZoom">关闭</button><button id="actualSize">适应 / 原始大小</button></div><div class="zoomscroll"><img id="zoomImage" alt="放大图"></div></dialog><script id="data" type="application/json">'+json.dumps(data,ensure_ascii=False).replace('</','<\\/')+'</script><script>'+JS+'</script></body></html>'
    (OUT/(STEM+'_Review.html')).write_text(page)
    fontpath=os.environ.get('HAF_CJK_FONT',str(ROOT.parent/'NotoSansCJKsc-Regular.otf'))
    f=ImageFont.truetype(fontpath,40);sm=ImageFont.truetype(fontpath,25)
    # Two original NBT render panels plus coordinate-anchored vector annotations.
    canvas=Image.new('RGB',(2480,1500),'#f2f0e8');d=ImageDraw.Draw(canvas)
    for i,(run,label) in enumerate([('V2_r06','V2 · 被否定的单侧突出'),(RUN,'V3 · 居中倒T裙楼')]):
        x=30+i*1230;src=Image.open(CASE/'review/previews'/run/'top.png').convert('RGB').resize((1190,1190),Image.Resampling.LANCZOS)
        d.text((x,22),label,font=f,fill='#233b40');canvas.paste(src,(x,90))
        def xy(wx,wz):return (x+(wx-63)/133*1190+595,90+(wz-58)/133*1190+595)
        if i==0:
            a,b=xy(102,27);d.ellipse((a-72,b-85,a+72,b+85),outline='#df4d44',width=6)
            d.text((x,1310),'红圈：V2错误的单侧后伸翼',font=sm,fill='#a93530')
        else:
            pts=[(13,87),(114,87),(114,72),(102,72),(102,16),(25,16),(25,72),(13,72),(13,87)]
            d.line([xy(a,b) for a,b in pts],fill='#efb74f',width=5)
            for z in range(8,100,4):d.line([xy(63,z),xy(63,z+2)],fill='#a9e9e1',width=3)
            d.text((x,1310),'黄线：裙楼主体轮廓；虚线：模型中轴',font=sm,fill='#233b40')
    d.text((30,1380),'相同正交相机 / 前方在下、后方在上 / 线条是模型参数定位，不是实测描边',font=sm,fill='#526b70')
    d.text((30,1420),'完整模型包含向前延伸的柱廊；各标高剖切与后门近景见HTML。',font=sm,fill='#526b70')
    canvas.save(OUT/(STEM+'_Top_Compare.png'))
    for mode in ('day','night'):
        canvas=Image.new('RGB',(3200,2250),'#f2f0e8');d=ImageDraw.Draw(canvas)
        d.text((24,15),'广州新海关 V3 · '+('四向日景' if mode=='day' else '四向夜景'),font=f,fill='#233b40')
        for i,(q,n) in enumerate([('se','东南'),('sw','西南'),('ne','东北'),('nw','西北')]):
            x=(i%2)*1600;y=80+(i//2)*1080
            src=Image.open(p/(q+'_'+mode+'.png')).convert('RGB');src.thumbnail((1520,1020))
            d.text((x+25,y),n+'45° · 模型坐标',font=sm,fill='#233b40');canvas.paste(src,(x+(1600-src.width)//2,y+45))
        canvas.save(OUT/(STEM+'_Four_Views_'+mode.title()+'.png'))
    shutil.copyfile(p/'overview.png',OUT/(STEM+'_Overview.png'))
    shutil.copyfile(r/'materials.csv',OUT/(STEM+'_Materials.csv'))
    (CASE/'validation/previews_v3.json').write_text(json.dumps({'run':RUN,'verified_images':verified,'all_decoded':True,'same_camera_as_V2':True},indent=2))
    print(json.dumps({'html_bytes':(OUT/(STEM+'_Review.html')).stat().st_size,'views':len(views),'reference_items':len(photos),'run':RUN}))

if __name__=='__main__':main()
