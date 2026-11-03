"""Self-contained review report; all geometry pictures are NBT readbacks."""
from report_base import *
from collections import Counter
NAMES={'home':'住宅','grocery':'小卖部','laundry':'洗衣店','restaurant':'食店','repair':'维修铺','barber':'理发店','tea':'街坊茶座'}
EQ=load(R/'equipment.json');WEATHER=load(R/'weathering.json');ROOMS=load(R/'interiors.json');PLANS=load(P/'plans/index.json');LIGHT=load(R/'lighting_assignment.json');ENTRIES=load(R/'entries.json');MASKS=load(R/'floor_masks.json');TERRAIN=load(R/'terrain.json')
HOMES=[u for u in UNITS if u['kind']=='home'];SHOPS=[u for u in UNITS if u['kind']!='home'];NSHAPE=sum(t['shape']!='rect' for t in PAR['buildings']);WC=Counter(w['security'] for w in load(R/'windows.json'));WE=Counter(w['kind'] for w in WEATHER)
def imagefig(path,title,desc=''):
 q=pic(path,1800);return '<figure><a href="'+q+'" download="'+Path(path).stem+'.webp"><img loading="lazy" src="'+q+'" alt="'+esc(title)+'"></a><figcaption><b>'+esc(title)+'</b><span>'+esc(desc)+'</span></figcaption></figure>'
def F(name,title,desc=''):return imagefig(P/name,title,desc)
def outline(cells):
 cells={tuple(q) for q in cells};edges={}
 for x,z in cells:
  for adj,a,c in [((x,z-1),(x,z),(x+1,z)),((x+1,z),(x+1,z),(x+1,z+1)),((x,z+1),(x+1,z+1),(x,z+1)),((x-1,z),(x,z+1),(x,z))]:
   if adj not in cells:edges[a]=c
 start=min(edges);a=start;path=[a]
 while True:
  a=edges[a]
  if a==start:break
  path.append(a)
 return ' '.join(f'{x},{z}' for x,z in path)
def siteplan():
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1070" role="img" aria-label="东南主街、西北高地与二十栋实际建筑轮廓"><rect width="1000" height="1070" fill="#eeeade"/><text x="40" y="42" font-size="22" fill="#304c43">北 ↑ −Z　东 → +X　·　最终建筑轮廓与入口</text><g transform="translate(42,88) scale(4.2)">'
 hm={(x,z):y for x,z,y in TERRAIN['heights_xzy']}
 for z in range(PAR['size_xyz'][2]):
  start=0;last=None
  for x in range(PAR['size_xyz'][0]+1):
   col=None if x==PAR['size_xyz'][0] else ('#778082' if 193<=x<208 or 182<=z<197 else '#d8d6c9' if x>=184 or z>=172 else {3:'#dce1c4',4:'#cdd6af',5:'#bdca99',6:'#aebe88',7:'#a0b079'}[hm[x,z]])
   if col!=last:
    if last:s+=f'<rect x="{start}" y="{z}" width="{x-start}" height="1" fill="{last}"/>'
    start=x;last=col
 for x,z in load(R/'paths.json')['cells_xz']:s+=f'<rect x="{x}" y="{z}" width="1" height="1" fill="#b0b9b0"/>'
 for m in MASKS:
  t=next(t for t in PAR['buildings'] if t['id']==m['building']);col={'ivory':'#e0d8bc','sand':'#c9ab79','gray':'#a5b5b2','rose':'#bd907f','mud':'#aa9274'}[t['palette']]
  s+=f'<polygon points="{outline(m["cells_xz"])}" fill="{col}" stroke="#58695d" stroke-width=".55"/><text x="{t["x"]+2}" y="{t["z"]+6}" font-size="3.3" fill="#2c4942">{t["id"]} · {t["floors"]}F</text><text x="{t["x"]+2}" y="{t["z"]+11}" font-size="2.7" fill="#40564a">{NAMES[t["ground"]]}</text><text x="{t["x"]+2}" y="{t["z"]+15}" font-size="2.4" fill="#65735c">首层 Y={t["base_y"]}</text>'
 for e in ENTRIES:
  x,y,z=e['entry'];col='#bf6137' if 'shop' in e['id'] else '#246e80';s+=f'<circle cx="{x+.5}" cy="{z+.5}" r=".8" fill="{col}"/>'
 for q in load(R/'trees.json'):
  x,y,z=q['root'];s+=f'<circle cx="{x}" cy="{z}" r="2.6" fill="#627d4f"/>'
 s+='<text x="2" y="8" font-size="3.5" fill="#47633c">西北留空 · Y=7</text><text x="196" y="166" font-size="3.5" fill="white" transform="rotate(-90 196 166)">东侧主街</text><text x="80" y="192" font-size="3.5" fill="white">南侧主街</text></g><text x="42" y="1008" font-size="17" fill="#465e52">橙：商铺门　蓝：住宅独立入口　灰：街巷　绿：高差地形与植被</text><text x="42" y="1038" font-size="15" fill="#687767">场地为原创设定；标高以方块格计，不是现实测绘或道路规范尺寸。</text></svg>'
 return s

def building(v):
 hero=pic(P/'se_day.png',1900);homes=len(HOMES);lit=len(LIGHT['lit_home_ids']);ratio=lit/homes
 body='<div class="tags">'+''.join('<span class="tag">'+q+'</span>' for q in ['20 栋 · 2–8 层','东南两面临街',str(NSHAPE)+' 栋非矩形楼板','西北高 4 格','约70%住宅亮灯'])+'</div><div class="hero"><img src="'+hero+'" alt="东南两面主街与二十栋商住楼"><p>本页图片来自最终 NBT 几何。材质、格栅和灯光为近似预览，未使用生成图代替建筑结果。</p></div>'
 body+='<div class="stats">'+''.join('<div><span class="stat">'+a+'</span><small>'+b+'</small></div>' for a,b in [('20','逐栋不同的宽深与高度'),(str(homes),'有家具的住宅单元'),(str(len(SHOPS)),'大小不同的底层店铺'),('4 格','西北高地至东南人行道')])+'</div>'
 body+=section('site','01','朝向城市，也连接村内','<p>东侧和南侧设置主街、人行道、树池、路灯与过街带；西侧和北侧保留开放地形。沿街铺面朝东南开口，住宅使用独立楼梯；内部街巷连接食店、理发店和小茶座。20栋分为临街商住、内巷住宅和低层生活节点。</p><div class="grid"><div>'+siteplan()+'</div>'+F('top_day.png','实际屋顶与道路俯视','北为 −Z，东为 +X。东南道路属于模型，西北为空地。')+'</div><div class="grid">'+F('east_street.png','东侧临街面')+F('south_street.png','南侧生活街')+'</div>')
 body+=section('form','02','斜切转角，楼板也随之改变','<p>'+str(NSHAPE)+'栋采用斜切或L形轮廓，变化贯穿各层楼板与屋顶；其余矩形楼形成对比。切角周围重排家具、灯位和屋顶设施，避免沿用矩形户型导致堵门、悬空。</p><div class="grid">'+F('corner_facade.png','D5 东南街角','六层商住楼，斜角和侧面都面向城市街道。')+F('corner_shop.png','D5 小卖部首层','两个顾客入口连接同一店内空间；北侧保留后场门和独立住宅入口。')+'</div>')
 body+=section('street','03','从高地走到人行道','<p>西北完成面最高Y=7，东南人行道Y=3，主街车道Y=2。建筑各自找平，内部街巷通过石阶处理标高变化；主街加入路缘、落客及过街位置、分段路面标线、雨水口、井盖、停放车辆形态和垃圾桶。树池、灯杆避开已经声明的行走路线。</p><div class="grid">'+F('northwest_slope.png','西北留空与高地')+F('street_cut.png','街区切低查看','显示道路、台地与建筑入口；仅为展示剖切，实际模型保留全部楼层。')+F('lane_eye.png','走进村巷')+F('terrain_section.png','低位切片与街道标高')+'</div>')
 body+=section('inside','04','不同经营规模，独立回家的路径','<p>'+str(len(SHOPS))+'家底商覆盖小卖部、食店、洗衣、维修、理发和茶座。6家店铺设置额外外门；D5保留两个面向东南的顾客入口及后场门。'+str(homes)+'户住宅分为紧凑开间、一房及部分两房；厨房、卫生空间、睡眠与起居陈设按房间安排，全部'+str(len(MODS))+'组家具设施写入NBT。</p><div class="grid">'+F('food_shop.png','E2 食店首层','侧门与临街门连接用餐区域；住宅经独立入口上楼。')+F('family_cut.png','B2 住宅剖切','紧凑户与较大户同层，共用楼梯但分开入户。')+'</div><p class="note">家具、设备、床形、水管和招牌均为装饰表达。没有声称实现床交互、给排水、商业经营或真实彩色光。</p>')
 body+=section('plans','05',str(len(PLANS))+'个楼层，逐栋逐层看','<div class="controls"><label>楼栋 <select id="planHouse">'+''.join('<option value="'+t['id']+'">'+t['id']+' · '+t['name']+'</option>' for t in PAR['buildings'])+'</select></label><label>楼层 <select id="planFloor"></select></label><a class="btn" id="planDownload" download>下载当前平面</a></div><div class="hero"><img id="floorImage" alt="最终NBT分层平面" style="max-height:850px;object-fit:contain"></div><p>所有平面采用各栋自身首层标高，蓝线为离线净空路径。下方爆炸只对D5二层的原方块进行可逆竖向分离。</p>'+imagefig(C/'review/previews'/(RUN+'_exploded')/'exploded.png','D5 二层分层爆炸'))
 body+=section('details','06','外饰与旧化仍然分层控制','<div class="grid">'+F('facade_detail.png','外机、窗网、管线和墙面')+F('roof_detail.png','屋顶设施与生活空间')+'</div>'+table(['项目','最终记录'],[['已登记常规窗组（切角与店面玻璃另按构件生成）',str(sum(WC.values()))+'组：无网'+str(WC['none'])+'，薄网'+str(WC['flush'])+'，笼式网'+str(WC['cage'])],['近色穿插',str(WE['near_colour'])+'个孤立近色块'],['局部修补与缺角',str(WE['exposed_infill'])+'处露底修补，'+str(WE['backed_chipped_edge'])+'处带背衬缺角'],['住宅照明',str(lit)+' / '+str(homes)+' 户，'+f'{ratio:.1%}'],['室内构造','3格净高 + 吊顶灯光层 + 上层地板；公共与商铺照明保持开启']]))
 body+=section('interactive','07','旋转、切低和逐层内饰','<button class="primary" id="load3d">打开交互模型</button><div id="threeD"></div><p class="foot">模型较大，首次解压需等待。浏览器性能不足时，可直接看上方分层平面与下方固定机位。</p>')
 body+=section('views','08','同尺度日夜与四向立面','<div class="controls"><label>方向 <select id="face"><option value="se">东南</option><option value="sw">西南</option><option value="ne">东北</option><option value="nw">西北</option></select></label><label><input type="checkbox" id="nightToggle">夜景</label></div><div class="hero"><img id="mainView" src="'+hero+'" alt="四向日夜预览"></div><div class="grid">'+''.join(F('elevation_'+a+'.png',b+'向正交立面') for a,b in [('front','南'),('back','北'),('left','西'),('right','东')])+'</div>')
 body+=section('download','09','建筑文件与检查范围','<p>'+str(MAN['non_air_blocks'])+'个非空气方块。'+str(len(VAL['checks']))+'项离线检查：'+('全部通过' if VAL['passed'] else '仍有未通过项目')+'。包含楼板切角、楼梯、家具接近面、街巷净空、商铺门内连通、独立入口和场地高差。实机导入、楼梯碰撞、照明与用户审美验收仍待确认。</p>'+dl(R/'building.nbt','下载建筑 NBT')+dl(R/'params_used.json','空间参数')+dl(R/'validation.json','检查记录')+'<details><summary>导入条件</summary><p>Java Structure NBT · DataVersion 3955 · 216×64×205格。需要支持大尺寸结构的导入方式；稀疏NBT不清除原有方块，先在空场地放置。放置原点Y+64须不超过目标世界最高Y排他上界。</p><pre>'+MAN['sha256']+'</pre></details>')
 js='const VIEWS='+json.dumps({q+'_'+m:pic(P/(q+'_'+m+'.png')) for q in ['se','sw','ne','nw'] for m in ['day','night']})+';const VIEWER='+json.dumps(v)+';const PLAN_IMAGES='+json.dumps({q['building']+'-'+str(q['floor']):pic(P/'plans'/q['file'],1200) for q in PLANS})+';const BUILDINGS='+json.dumps(PAR['buildings'])+';'
 js+='''function swap(){document.getElementById('mainView').src=VIEWS[document.getElementById('face').value+'_'+(document.getElementById('nightToggle').checked?'night':'day')]}document.getElementById('face').addEventListener('change',swap);document.getElementById('nightToggle').addEventListener('change',swap);
document.getElementById('load3d').addEventListener('click',function(){const f=document.createElement('iframe');f.title='榕荫里 · 最终NBT交互模型';f.srcdoc=VIEWER;document.getElementById('threeD').append(f);this.remove()});
function showPlan(){let k=document.getElementById('planHouse').value+'-'+document.getElementById('planFloor').value;document.getElementById('floorImage').src=PLAN_IMAGES[k];const a=document.getElementById('planDownload');a.href=PLAN_IMAGES[k];a.download=k+'.webp'}
function setFloors(){const t=BUILDINGS.find(t=>t.id===document.getElementById('planHouse').value),s=document.getElementById('planFloor');s.replaceChildren();for(let i=1;i<=t.floors;i++){const o=document.createElement('option');o.value=i;o.textContent=i+'F';s.append(o)}showPlan()};document.getElementById('planHouse').addEventListener('change',setFloors);document.getElementById('planFloor').addEventListener('change',showPlan);setFloors();'''
 return shell('榕荫里 · 东南街角','20栋商住建筑，沿东南主街展开；转过切角店面，走进略向西北升高的生活巷道。',[('site','总图'),('form','体块'),('street','道路'),('inside','内饰'),('plans','分层'),('interactive','交互'),('download','下载')],body,js)

def process():
 body='<div class="dark"><h2>从村内楼群，推进到面向城市的街区。</h2><p>本轮采用20栋的最新要求，东南两侧主街、西北留空且略高。前轮12栋文件作为历史版本保留；本轮是新布局和新建筑输出。</p></div>'
 body+=section('brief','01','输入与空间决定',table(['输入','本轮落实'],[['20栋','2–8层，宽深和高度组合不同'],['东南临街','两条主街、连续人行道、底商和独立住宅门'],['转角和不规则体块','14栋斜切或L形楼板；D5斜角小卖部'],['双入口与店铺大小','6家店增加外门；其余保留单门或后场分工'],['西北高、东南低','最高Y=7，东南人行道Y=3，车道Y=2'],['道路细节','过街带、路缘、台阶、井盖、雨水口、树池、路灯和少量停放物']])+dl(C/'input/design.json','原创设计参数'))
 body+=section('evidence','02','来源与边界','<p>沿用此前三条视频与jiejao研究目录中的窗网、设备、材质和街面表达方法；本轮没有重新播放视频，没有取得新建筑工程。道路、宅地、层数、房间与设施坐标均为原创决定。没有将视频中的平面当作测绘事实。</p>'+dl(C/'input/exterior_catalog_v02.json','既有研究目录')+'<p>用户反馈促使本轮把“门洞可通行”和“入口朝向合理”分开检查；同样把“大小不同”与“楼板轮廓不同”分开处理。</p>')
 body+=section('geometry','03','真实几何与消费者','<p>input/design.json由本案build_case.py和site20.py消费。切角掩码用于实际楼板、墙体、屋顶及平面，首层台地标高同步进入楼梯、家具、灯光、门洞及回读。HAF交接编译只检查20份设计计划；实际方块由案例适配器生成。</p><div class="grid"><div>'+siteplan()+'</div>'+F('corner_shop.png','切角店铺回读')+'</div>'+dl(R/'floor_masks.json','实际楼板轮廓')+dl(R/'entries.json','全部入口')+dl(R/'terrain.json','地形与台阶'))
 body+=section('iteration','04','实际修订与保留问题',table(['阶段','检查与处理'],[['V2_r01','生成20栋；发现切角卧室的家具阻挡入口、少数店铺家具落入切角、路灯占用巷口和个别屋顶杆架失去承托'],['V2_r02','重排切角卧室与店铺家具，调整灯位、天线和路灯；最小茶座新增桌椅影响卫生间入口'],['V2_r03','按店铺进深控制桌椅数量，调整几栋位置和巷道转折，村内改为硬地；21项检查通过'],['V2_r04','补齐切角空地地坪与过街带两侧路缘台阶；22项检查通过'],['V2_r05','街角小卖部补连续玻璃店面、转角雨棚和绿色招牌，移开遮挡店面的街树'],['当前交付 '+RUN,'结果以本包validation.json为准；不以技术检查代替用户对味道和形态的评价']]))
 body+=section('checks','05','最终离线检查',table(['检查','结果'],[[q['id'],q['status']] for q in VAL['checks']])+'<p>台阶检查属于离散占用和高差检查，不是游戏碰撞模拟。模型为原创街区，不是现实施工、结构或消防合规方案。</p>'+dl(R/'validation.json','验证明细'))
 body+=section('views','06','同一NBT的多种观察','<p>四向同尺度45°日夜、真俯视、四向立面、街道机位、商铺及住宅剖切、105张楼层平面和D5二层可逆爆炸均绑定当前NBT。渲染没有原版资源包纹理，薄构件和灯光采用近似表达。</p><div class="grid">'+F('se_night.png','东南夜景')+imagefig(C/'review/previews'/(RUN+'_exploded')/'exploded.png','D5二层爆炸')+'</div>')
 body+=section('replay','07','复跑与工程范围','<pre>python cases/urban_village20/src/build_case.py --run replay\npython cases/urban_village20/src/validate_case.py --run replay\npython cases/urban_village20/src/render_case.py --run replay\npython cases/urban_village20/src/draw_layers.py --run replay\nVILLAGE_RUN=replay python cases/urban_village20/src/build_reports.py</pre><p>既有run不可覆盖。场地装饰与部分户型规则仍为此案例代码，不是任意城中村的全自动生成能力；已安装技能未改动。游戏测试与用户视觉验收保留pending。</p>'+dl(R/'provenance.json','采用记录')+'<details><summary>建筑生成源码</summary><pre>'+esc((C/'src/build_case.py').read_text())+'</pre></details><details><summary>场地与道路源码</summary><pre>'+esc((C/'src/site20.py').read_text())+'</pre></details>')
 return shell('榕荫里 · 20栋制作记录','设计决定、实际方块、修订过程和验证边界。',[('brief','输入'),('geometry','几何'),('iteration','修订'),('checks','检查'),('replay','工程')],body)
if __name__=='__main__':
 from fontTools import subset
 v=viewer();docs={'Village.html':building(v),'Village_Process.html':process()}
 f=subset.load_font(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),subset.Options());ss=subset.Subsetter();ss.populate(text=''.join(docs.values())+v);ss.subset(f);f.flavor='woff';buf=io.BytesIO();f.save(buf);enc=base64.b64encode(buf.getvalue()).decode()
 css='@font-face{font-family:Noto;src:url(data:font/woff;base64,'+enc+') format("woff");font-display:swap}'
 for name,s in docs.items():(OUT/name).write_text(s.replace('<style>','<style>'+css,1))
 shutil.copy2(R/'building.nbt',OUT/'Village.nbt');print(json.dumps({q.name:q.stat().st_size for q in OUT.glob('Village.*')}))
