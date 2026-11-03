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
 import sys
 sys.path[:0]=[str(ROOT),str(ROOT/'support')]
 import site20
 s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1010" role="img" aria-label="六边形街区边界、八格高差与二十栋实际建筑轮廓"><rect width="1200" height="1010" fill="#eeeade"/><text x="36" y="38" font-size="22" fill="#304c43">北 ↑ −Z　东 → +X　·　六边街区 / 实际入口与台地</text><g transform="translate(38,65) scale(3.9)">'
 hm={(x,z):y for x,z,y in TERRAIN['heights_xzy']};colors=['#e5e3c6','#d9dfbe','#cfdab3','#c2d0a4','#b4c599','#a8bb8d','#9caf7d','#8da16c','#7c925e','#6d8454']
 for z in range(PAR['size_xyz'][2]):
  start=0;last=None
  for x in range(PAR['size_xyz'][0]+1):
   col=None
   if (x,z) in hm:
    road,paved=site20.road_kind(x,z,PAR);col='#778082' if road else '#d8d6c9' if paved else colors[max(0,min(9,hm[x,z]-2))]
   if col!=last:
    if last:s+=f'<rect x="{start}" y="{z}" width="{x-start}" height="1" fill="{last}"/>'
    start=x;last=col
 for x,z in load(R/'paths.json')['cells_xz']:s+=f'<rect x="{x}" y="{z}" width="1" height="1" fill="#adb8b0"/>'
 s+='<polygon points="'+' '.join(f'{x},{z}' for x,z in PAR['site']['boundary_xz'])+'" fill="none" stroke="#aa5b3e" stroke-width=".7"/>'
 for m in MASKS:
  t=next(t for t in PAR['buildings'] if t['id']==m['building']);col={'ivory':'#e0d8bc','sand':'#c9ab79','gray':'#a5b5b2','rose':'#bd907f','mud':'#aa9274'}[t['palette']]
  s+=f'<polygon points="{outline(m["cells_xz"])}" fill="{col}" stroke="#58695d" stroke-width=".55"/><text x="{t["x"]+2}" y="{t["z"]+6}" font-size="3.3" fill="#2c4942">{t["id"]} · {t["floors"]}F</text><text x="{t["x"]+2}" y="{t["z"]+11}" font-size="2.7" fill="#40564a">{NAMES[t["ground"]]}</text><text x="{t["x"]+2}" y="{t["z"]+15}" font-size="2.4" fill="#65735c">Y={t["base_y"]}</text>'
 for e in ENTRIES:
  x,y,z=e['entry'];col='#bf6137' if 'shop' in e['id'] else '#246e80';s+=f'<circle cx="{x+.5}" cy="{z+.5}" r=".8" fill="{col}"/>'
 for q in load(R/'trees.json'):
  x,y,z=q['root'];s+=f'<circle cx="{x}" cy="{z}" r="2.6" fill="#627d4f"/>'
 s+='<text x="3" y="48" font-size="3.5" fill="#47633c">西北高地 Y=11</text><text x="254" y="178" font-size="3.5" fill="#9c4f33">Y=3</text><text x="270" y="165" font-size="3.5" fill="white" transform="rotate(-90 270 165)">东侧主街</text><text x="116" y="196" font-size="3.5" fill="white">南侧主街</text><path d="M255 24h6v60h-6" fill="none" stroke="#aa5b3e" stroke-width=".6"/><text x="262" y="62" font-size="3.5" fill="#aa5b3e" transform="rotate(-90 262 62)">E1 长边 60格</text></g><text x="38" y="944" font-size="17" fill="#465e52">橙：商铺门　蓝：住宅入口　灰：街巷　绿底：地形标高（不等于全部草地）</text><text x="38" y="978" font-size="15" fill="#687767">红线表示整个街区的六边轮廓；单栋楼可另有切角与多处凹入。尺寸均以方块格计。</text></svg>'
 return s

def comparison():
 return section('compare','00','六边街区，长楼与坡巷','<p>延续已认可的V3，把整片街区边界改为用户草图的六边轮廓；扩展东侧长楼与台地高差，同时打开D5街角上层。下图均来自各版实际NBT，方向相同、完整展示各自范围，显示比例不同。</p><div class="grid">'+imagefig(C/'review/previews/V3_r04/top_day.png','上一版 V3 · 完整范围','各版自动适配画幅，不能直接用屏幕宽度比较尺寸。')+F('top_day.png','新版 V4 · 六边坡街','场地地面实际裁切为六边形；西北留空。')+'</div>'+table(['变化','V3','V4'],[['整体边界','矩形地面','六个主转折点，北侧折线与斜边'],['最长临街楼','49格','E1长边60格，E2长边41格'],['西北至东南人行道','4格','8格：Y=11 → Y=3'],['D5斜面','连续实墙与楼层带','二至六层内凹阳台、玻璃与栏杆'],['单栋轮廓','矩形、单切角为主','A2 / B3 / E3补侧面凹槽或连续转折']]))

def building(v):
 hero=pic(P/'se_day.png',1900);homes=len(HOMES);lit=len(LIGHT['lit_home_ids']);ratio=lit/homes
 body='<div class="tags">'+''.join('<span class="tag">'+q+'</span>' for q in ['20 栋 · 2–8 层','东南两面临街',str(NSHAPE)+' 栋非矩形楼板','西北高 8 格','约70%住宅亮灯'])+'</div><div class="hero"><img src="'+hero+'" alt="东南两面主街与二十栋商住楼"><p>本页图片来自最终 NBT 几何。材质、格栅和灯光为近似预览，未使用生成图代替建筑结果。</p></div>'
 body+='<div class="stats">'+''.join('<div><span class="stat">'+a+'</span><small>'+b+'</small></div>' for a,b in [('20','逐栋不同的宽深与高度'),(str(homes),'有家具的住宅单元'),(str(len(SHOPS)),'大小不同的底层店铺'),('8 格','西北高地至东南人行道')])+'</div>'
 body+=comparison()
 body+=section('site','01','朝向城市，也连接村内','<p>东侧和南侧设置主街、人行道、树池、路灯与过街带；西侧和北侧保留开放地形。东南两侧安排长条铺楼与窄面商住楼；内侧用深进深楼、夹缝小宅、低矮茶座构成不等大的地块。巷道绕过宅地折转，以3格窄巷和5格较宽巷相接；住宅保持独立上楼入口。</p><div class="grid"><div>'+siteplan()+'</div>'+F('top_day.png','实际屋顶与道路俯视','北为 −Z，东为 +X。东南道路属于模型，西北为空地。')+'</div><div class="grid">'+F('east_street.png','东侧临街面')+F('south_street.png','南侧生活街')+'</div>')
 body+=section('form','02','长楼、凹入宅地与开放街角','<p>'+str(NSHAPE)+'栋采用非矩形楼板。A2与B3结合侧面凹入和后角退让，E3试用中段凹槽，变化贯穿楼板、墙面与屋顶。E1为24×60格，E2为29×41格，D1为47×27格；小楼E3为20×18格。D5二至六层改为可从室内进入的内凹转角阳台，二、四、六层使用低栏杆，三、五层加全高窗网，玻璃门窗后退。</p><div class="grid">'+F('corner_facade.png','D5 东南街角','六层商住楼，斜角和侧面都面向城市街道。')+F('corner_loggia_cut.png','D5 二层转角阳台','玻璃后退、室内出入口与外侧栏杆均为实际方块。')+F('corner_shop.png','D5 小卖部首层','两个顾客入口连接同一店内空间；北侧保留后场门和独立住宅入口。')+'</div>')
 body+=section('street','03','从高地走到人行道','<p>西北完成面最高Y=11，东南人行道Y=3，两点相差8格；东南角车道Y=2。道路随地形分级变化。建筑各自找平，内部街巷通过石阶处理标高变化；主街加入路缘、落客及过街位置、分段路面标线、雨水口、井盖、停放车辆形态和垃圾桶。树池、灯杆避开已经声明的行走路线。</p><div class="grid">'+F('northwest_slope.png','西北留空与高地')+F('street_cut.png','街区切低查看','显示道路、台地与建筑入口；仅为展示剖切，实际模型保留全部楼层。')+F('lane_eye.png','走进村巷')+F('terrain_section.png','低位切片与街道标高')+'</div>')
 body+=section('inside','04','不同经营规模，独立回家的路径','<p>'+str(len(SHOPS))+'家底商覆盖小卖部、食店、洗衣、维修、理发和茶座。6家店铺设置额外外门；D5保留两个面向东南的顾客入口及后场门。'+str(homes)+'户住宅包含小开间、家庭户与长楼分户。长楼上层经公共后廊逐户进入；深进深住宅增加后卧室。厨房、卫生空间、睡眠与起居陈设按房间安排，全部'+str(len(MODS))+'组家具设施写入NBT。</p><div class="grid">'+F('food_shop.png','E2 食店首层','侧门与临街门连接用餐区域；住宅经独立入口上楼。')+F('family_cut.png','E1 长楼二层分户','前侧四户与核心旁小户分开入户；后侧共用走廊连接同一楼梯。')+'</div><p class="note">家具、设备、床形、水管和招牌均为装饰表达。没有声称实现床交互、给排水、商业经营或真实彩色光。</p>')
 body+=section('plans','05',str(len(PLANS))+'个楼层，逐栋逐层看','<div class="controls"><label>楼栋 <select id="planHouse">'+''.join('<option value="'+t['id']+'">'+t['id']+' · '+t['name']+'</option>' for t in PAR['buildings'])+'</select></label><label>楼层 <select id="planFloor"></select></label><a class="btn" id="planDownload" download>下载当前平面</a></div><div class="hero"><img id="floorImage" alt="最终NBT分层平面" style="max-height:850px;object-fit:contain"></div><p>所有平面采用各栋自身首层标高，蓝线为离线净空路径。下方爆炸只对D5二层的原方块进行可逆竖向分离。</p>'+imagefig(C/'review/previews'/(RUN+'_exploded')/'exploded.png','D5 二层分层爆炸'))
 body+=section('details','06','外饰与旧化仍然分层控制','<div class="grid">'+F('facade_detail.png','外机、窗网、管线和墙面')+F('roof_detail.png','屋顶设施与生活空间')+'</div>'+table(['项目','最终记录'],[['已登记常规窗组（切角与店面玻璃另按构件生成）',str(sum(WC.values()))+'组：无网'+str(WC['none'])+'，薄网'+str(WC['flush'])+'，笼式网'+str(WC['cage'])],['近色穿插',str(WE['near_colour'])+'个孤立近色块'],['局部修补与缺角',str(WE['exposed_infill'])+'处露底修补，'+str(WE['backed_chipped_edge'])+'处带背衬缺角'],['住宅照明',str(lit)+' / '+str(homes)+' 户，'+f'{ratio:.1%}'],['室内构造','3格净高 + 吊顶灯光层 + 上层地板；公共与商铺照明保持开启']]))
 body+=section('interactive','07','旋转、切低和逐层内饰','<button class="primary" id="load3d">打开交互模型</button><div id="threeD"></div><p class="foot">模型较大，首次解压需等待。浏览器性能不足时，可直接看上方分层平面与下方固定机位。</p>')
 body+=section('views','08','同尺度日夜与四向立面','<div class="controls"><label>方向 <select id="face"><option value="se">东南</option><option value="sw">西南</option><option value="ne">东北</option><option value="nw">西北</option></select></label><label><input type="checkbox" id="nightToggle">夜景</label></div><div class="hero"><img id="mainView" src="'+hero+'" alt="四向日夜预览"></div><div class="grid">'+''.join(F('elevation_'+a+'.png',b+'向正交立面') for a,b in [('front','南'),('back','北'),('left','西'),('right','东')])+'</div>')
 body+=section('download','09','建筑文件与检查范围','<p>'+str(MAN['non_air_blocks'])+'个非空气方块。'+str(len(VAL['checks']))+'项离线检查：'+('全部通过' if VAL['passed'] else '仍有未通过项目')+'。包含楼板切角、楼梯、家具接近面、街巷净空、商铺门内连通、独立入口和场地高差。实机导入、楼梯碰撞、照明与用户审美验收仍待确认。</p>'+dl(R/'building.nbt','下载建筑 NBT')+dl(R/'params_used.json','空间参数')+dl(R/'validation.json','检查记录')+'<details><summary>导入条件</summary><p>Java Structure NBT · DataVersion 3955 · 288×72×216格。需要支持大尺寸结构的导入方式；稀疏NBT不清除原有方块，先在空场地放置。放置原点Y+72须不超过目标世界最高Y排他上界。</p><pre>'+MAN['sha256']+'</pre></details>')
 js='const VIEWS='+json.dumps({q+'_'+m:pic(P/(q+'_'+m+'.png')) for q in ['se','sw','ne','nw'] for m in ['day','night']})+';const VIEWER='+json.dumps(v)+';const PLAN_IMAGES='+json.dumps({q['building']+'-'+str(q['floor']):pic(P/'plans'/q['file'],1200) for q in PLANS})+';const BUILDINGS='+json.dumps(PAR['buildings'])+';'
 js+='''function swap(){document.getElementById('mainView').src=VIEWS[document.getElementById('face').value+'_'+(document.getElementById('nightToggle').checked?'night':'day')]}document.getElementById('face').addEventListener('change',swap);document.getElementById('nightToggle').addEventListener('change',swap);
document.getElementById('load3d').addEventListener('click',function(){const f=document.createElement('iframe');f.title='榕荫里 · 最终NBT交互模型';f.srcdoc=VIEWER;document.getElementById('threeD').append(f);this.remove()});
function showPlan(){let k=document.getElementById('planHouse').value+'-'+document.getElementById('planFloor').value;document.getElementById('floorImage').src=PLAN_IMAGES[k];const a=document.getElementById('planDownload');a.href=PLAN_IMAGES[k];a.download=k+'.webp'}
function setFloors(){const t=BUILDINGS.find(t=>t.id===document.getElementById('planHouse').value),s=document.getElementById('planFloor');s.replaceChildren();for(let i=1;i<=t.floors;i++){const o=document.createElement('option');o.value=i;o.textContent=i+'F';s.append(o)}showPlan()};document.getElementById('planHouse').addEventListener('change',setFloors);document.getElementById('planFloor').addEventListener('change',showPlan);setFloors();'''
 return shell('榕荫里 · 六边坡街 / V4','20栋商住楼，60格临街长楼与8格台地高差；D5转角阳台面向街口。',[('compare','新旧对比'),('site','总图'),('form','体块'),('street','道路'),('inside','内饰'),('plans','分层'),('interactive','交互'),('download','下载')],body,js)

def process():
 body='<div class="dark"><h2>V4：先明确街区边界，再让高差、长楼与街角进入模型。</h2><p>用户已认可V3的总体组织。本轮明确六边形指整个城中村，保留20栋；最长一边按60格，高差按8格制作，并把D5斜面改为阳台。V3_r04输出及源码快照完整保留。</p></div>'
 body+=section('brief','01','输入与空间决定',table(['输入','本轮落实'],[['20栋','2–8层，101个主要楼层；不同宅地宽深，长条与小宅混合'],['东南临街','两条主街、连续人行道、底商和独立住宅门'],['六边形的对象','整个街区边界；不是把所有单栋改成六边形'],['单栋不规则与街角',str(NSHAPE)+'栋非矩形楼板；三栋新增凹入；D5五层转角阳台'],['双入口与店铺大小','6家店增加外门；其余保留单门或后场分工'],['西北高、东南低','最高Y=11，东南角人行道Y=3，相差8格'],['道路细节','过街带、路缘、台阶、井盖、雨水口、树池、路灯和少量停放物']])+dl(C/'input/design.json','原创设计参数'))
 body+=section('evidence','02','来源与边界','<p>沿用此前三条视频与jiejao研究目录中的窗网、设备、材质和街面表达方法；本轮没有重新播放视频，没有取得新建筑工程。道路、宅地、层数、房间与设施坐标均为原创决定。没有将视频中的平面当作测绘事实。</p>'+dl(C/'input/exterior_catalog_v02.json','既有研究目录')+'<div class="grid">'+imagefig(C/'input/user_hexagon_sketch.png','用户草图：整体街区边界','经用户明确确认，按六个主转折点作方块化近似。')+imagefig(C/'input/user_D5_feedback.png','用户指出：D5斜面太封闭','此图为修改前的输入反馈，不计作新版结果。')+'</div>')
 body+=section('geometry','03','真实几何与消费者','<p>input/design.json由本案build_case.py和site20.py消费。街区多边形直接裁切地面；楼栋掩码用于实际楼板、墙体、屋顶及平面，首层台地标高同步进入楼梯、家具、灯光、门洞及回读。HAF交接编译只检查20份设计计划；实际方块由案例适配器生成。</p><div class="grid"><div>'+siteplan()+'</div>'+F('corner_shop.png','切角店铺回读')+'</div>'+dl(R/'floor_masks.json','实际楼板轮廓')+dl(R/'entries.json','全部入口')+dl(R/'terrain.json','地形与台阶'))
 body+=section('iteration','04','实际修订与保留问题',table(['阶段','检查与处理'],[['V2_r01','生成20栋；发现切角卧室的家具阻挡入口、少数店铺家具落入切角、路灯占用巷口和个别屋顶杆架失去承托'],['V2_r02','重排切角卧室与店铺家具，调整灯位、天线和路灯；最小茶座新增桌椅影响卫生间入口'],['V2_r03','按店铺进深控制桌椅数量，调整几栋位置和巷道转折，村内改为硬地；21项检查通过'],['V2_r04','补齐切角空地地坪与过街带两侧路缘台阶；22项检查通过'],['V2_r05','街角小卖部补连续玻璃店面、转角雨棚和绿色招牌，移开遮挡店面的街树'],['V3_r01','20栋重新分配大小、朝向和位置；长楼增加分户。检查发现两处水管侵入巷道，A2与C1宽深/层数组合仍相同'],['V3_r02','调整C1尺寸、水管位置；深宅增加后卧室；22项离线检查通过'],['V3_r03','补宽窄巷道和匹配巷口的过街带；增加占地差异、临街长度、直线巷道及地块重叠检查'],['V3_r04','视觉复核后补长店后场及长楼第二组水箱，去除巷道周期横条铺装；空间总图不再改动'],['V4_r01','生成六边场地、60格长楼、8格台地和D5阳台；发现A2凹槽影响桌子和灯，E2与D5之间低雨棚及门前地坪影响巷道'],['V4_r02','重新布置A2家具与灯位，E2长度调整为41格并扩展找平台地；30项检查通过，D5五层阳台连通'],['当前交付 '+RUN,'结果以本包validation.json为准；不以技术检查代替用户对味道和形态的评价']]))
 body+=section('checks','05','最终离线检查',table(['检查','结果'],[[q['id'],q['status']] for q in VAL['checks']])+'<p>台阶检查属于离散占用和高差检查，不是游戏碰撞模拟。模型为原创街区，不是现实施工、结构或消防合规方案。</p>'+dl(R/'validation.json','验证明细'))
 body+=section('views','06','同一NBT的多种观察','<p>四向同尺度45°日夜、真俯视、四向立面、街道机位、商铺及住宅剖切、'+str(len(PLANS))+'张楼层平面和D5二层可逆爆炸均绑定当前NBT。渲染没有原版资源包纹理，薄构件和灯光采用近似表达。</p><div class="grid">'+F('se_night.png','东南夜景')+imagefig(C/'review/previews'/(RUN+'_exploded')/'exploded.png','D5二层爆炸')+'</div>')
 body+=section('replay','07','复跑与工程范围','<pre>python cases/urban_village20/src/build_case.py --run replay\npython cases/urban_village20/src/validate_case.py --run replay\npython cases/urban_village20/src/render_case.py --run replay\npython cases/urban_village20/src/draw_layers.py --run replay\nVILLAGE_RUN=replay python cases/urban_village20/src/build_reports.py</pre><p>既有run不可覆盖。场地装饰与部分户型规则仍为此案例代码，不是任意城中村的全自动生成能力；已安装技能未改动。游戏测试与用户视觉验收保留pending。</p>'+dl(R/'provenance.json','采用记录')+'<details><summary>建筑生成源码</summary><pre>'+esc((C/'src/build_case.py').read_text())+'</pre></details><details><summary>场地与道路源码</summary><pre>'+esc((C/'src/site20.py').read_text())+'</pre></details>')
 return shell('榕荫里 · V4 制作记录','设计决定、实际方块、修订过程和验证边界。',[('brief','输入'),('geometry','几何'),('iteration','修订'),('checks','检查'),('replay','工程')],body)
if __name__=='__main__':
 from fontTools import subset
 v=viewer();docs={'Village.html':building(v),'Village_Process.html':process()}
 f=subset.load_font(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),subset.Options());ss=subset.Subsetter();ss.populate(text=''.join(docs.values())+v);ss.subset(f);f.flavor='woff';buf=io.BytesIO();f.save(buf);enc=base64.b64encode(buf.getvalue()).decode()
 css='@font-face{font-family:Noto;src:url(data:font/woff;base64,'+enc+') format("woff");font-display:swap}'
 docs['Village.html']=docs['Village.html'].replace(json.dumps(v).replace('</script',r'<\/script'),json.dumps(v.replace('<style>','<style>'+css,1)).replace('</script',r'<\/script'))
 for name,s in docs.items():(OUT/name).write_text(s.replace('<style>','<style>'+css,1))
 shutil.copy2(R/'building.nbt',OUT/'Village.nbt');print(json.dumps({q.name:q.stat().st_size for q in OUT.glob('Village.*')}))
