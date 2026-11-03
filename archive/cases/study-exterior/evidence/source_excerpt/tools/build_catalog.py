from pathlib import Path
import json,html,base64,hashlib,shutil,zipfile
from PIL import Image
R=Path(__file__).resolve().parents[1]
S=R.parent/'study_01_sources'
def dump(name,obj):
 (R/'data'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
source={'video':{'id':'V01','title':'建个广东打工人都很熟悉的楼，纪念我们奋斗的青春~【我的世界Minecraft】','author':'赵相机咔咔一顿拍','url':'https://www.bilibili.com/zh-Hans/video/BV17x42117gm/','duration_seconds':320,'method':'登录后播放器关键施工段与成品画面观察；不是逐字字幕稿，也未取得视频工程。'},'nbt':{'id':'J00','name':'jiejao.nbt','library_file_id':'libfile_690df86adc9881918fce5c41c4e88da2','sha256':'3727667d0add5244a7f5b1bcfdf2706da4c49e16ade743a4de254da15f5b62e6','size_xyz':[108,43,72],'block_records':44127,'palette_states':325,'method':'本轮实际 NBT 只读回读，保留方块状态与局部坐标。'}}
observations=[
 {'id':'V01-12','at':'00:12','kind':'subtitle_and_visual','observation':'红褐色楼以磨制花岗岩为主材；字幕明确材料名。外墙轮廓先于标准层复制。','limit':'31×26 是视频中的 Minecraft 建造尺度，不是真实建筑测量。'},
 {'id':'V01-25','at':'00:25–00:26','kind':'visual','observation':'中部连续通道两侧设置重复隔间；窗洞外有凸出的铁栏围笼，上下分别设置薄水平构件。','limit':'不据此认定厨卫位置、套数、承重体系或完整功能内饰。'},
 {'id':'V01-35','at':'00:34–00:35','kind':'visual','observation':'标准层竖向重复，顶部施工面可见平面分隔与楼梯位置；侧墙保留大段实体面。','limit':'重复层数不作为我们楼盘的楼层参数。'},
 {'id':'V01-106','at':'01:46–01:47','kind':'visual','observation':'屋顶由凸起围护、白色箱体、竖管、成组细杆横线架及种植床组成，各组之间留空。','limit':'细杆横线架形态支持晾晒架判断；白箱的具体设备功能仍待证实。'},
 {'id':'V01-126','at':'02:06–02:07','kind':'visual','observation':'屋顶新增薄顶棚与支柱，女儿墙加浅色压顶，沿街底层出现彩色招牌状面板。','limit':'面板内容及底层实际商铺用途未逐一核实。'},
 {'id':'V01-139','at':'02:18–02:19；02:30–02:31','kind':'visual','observation':'白色小设备盒选择性地挂在窗侧，部分带深色小面板；不同楼层位置有变化。','limit':'可借鉴为空调外机的视觉表达；具体方块 ID、支架和管线不能只凭这几帧断言。'},
 {'id':'V01-186','at':'03:06–03:07','kind':'visual','observation':'第二栋改用浅灰白墙面、红褐色窗顶和深棕窗台，基础分隔仍重复。','limit':'画面纹理不能等同精确材质表。'},
 {'id':'V01-221','at':'03:40–03:41','kind':'visual','observation':'同一正面划分为竖向独立窗列与连续后退开口带，带状窗下沿连续转折；一层另作大开口。','limit':'凹带可作为阳台/外廊表达研究，实际通行功能未验证。'},
 {'id':'V01-281','at':'04:40–04:41；04:57–04:58','kind':'visual','observation':'第二栋屋顶有多个箱体、杆架和低矮盆状设施；侧墙增加连续竖管，屋顶压顶与窗下横带呼应。','limit':'并非所有箱体都是水箱；视频中没有确认到独立电视天线的细部。'},
 {'id':'J00-readback','at':'原文件坐标 X/Y/Z','kind':'nbt_readback','observation':'尺寸 108×43×72，44,127 条方块记录，325 个调色板状态；与历史记录的原文件 SHA256 一致。','limit':'尺寸包含整个模型，材料总数不是某面墙的比例。'},
 {'id':'J01','at':'[92,36,22] → [95,43,25)，高端不含','kind':'nbt_excerpt','observation':'竖杆与侧向附件组成天线状轮廓，含闪长岩墙、铁栏、避雷针等状态。','limit':'形态分类为天线状杆架；实际通信或避雷功能不作承诺。'},
 {'id':'J02','at':'[91,13,3] → [95,16,4)，高端不含','kind':'nbt_excerpt','observation':'两个铁块、侧向梯子、顶部铁活板门和下部拉杆构成一个附墙设备盒组合。','limit':'可以作为空调外机造型参考，原作者设备用途未核实。'},
 {'id':'J03','at':'[91,32,17] → [101,35,20)，高端不含','kind':'nbt_excerpt','observation':'屋顶多个重复单元使用铁块、石英楼梯、横向锁链与避雷针组合，粗细层次不同。','limit':'暂记屋顶设施排，不强行命名水箱或风机。'},
 {'id':'J00-material','at':'全模型与立面回读','kind':'nbt_readback','observation':'白色羊毛、白色混凝土、磨制闪长岩等浅色材料并存，多色玻璃与细部设施共同形成变化。','limit':'只证明模型材料及几何分布；无真实纹理渲染，不能推导污染原因。'},
 {'id':'J00-plan','at':'Y≤12 的俯视剖切','kind':'nbt_readback','observation':'能看到部分隔片/房间边界与窗后细部，大量空间没有完整家具配置。','limit':'这张剖切不证明整栋有连续交通、有效户型或可进入内饰。'}]
def comp(id,name,zone,evidence,form,anchor,params,avoid,transfer,status='observed_recipe',sample=None):
 return dict(id=id,name=name,zone=zone,evidence=evidence,form=form,anchor=anchor,parameters=params,avoid=avoid,transfer=transfer,status=status,sample_id=sample,consumer=None,game_validation='pending')
components=[
 comp('C01','防盗网／凸窗笼','墙面',['V01-25','V01-186'],'玻璃后退，铁栏在外侧形成有侧边的薄笼，上下收口。','房间窗洞边缘；保持开口与窗台关系',['无网／贴面网／外凸笼','宽高随窗洞','突出深度分档','稳定住户 ID 决定变体'],'不要每扇窗同一种笼；不要把玻璃与铁栏并成一个实心层。','千禧住宅保留用户要求的有网／无网混合；先定窗型再选网型。'),
 comp('C02','窗台与小雨棚','墙面',['V01-25','V01-186'],'窗顶薄盖、窗底薄台形成阴影，颜色服从整栋配色。','窗框上缘与下缘',['材质','挑出深度','连续／单窗','上下构件是否同色'],'不为变化随机抬高窗台；不要挡住窗和管线。','可采用半砖与活板门候选做法；具体材料先做样板。'),
 comp('C03','空调外机表达','设备',['V01-139','J02'],'视频用小白盒和深色细部；jiejao 用铁块加梯子、活板门、拉杆构成设备盒。','窗侧／窗下设备位；绑定对应房间',['单／双机','左右侧','尺寸等级','支架与连接管选项'],'避免悬空无依托、正对窗中心、每户同高度同数量。','一梯一户的大户型可按实际房间分配设备位；数量不能等同亮灯户数。','extracted_reference','J02'),
 comp('C04','屋顶水箱候选','屋顶',['V01-106','V01-281'],'画面确认屋顶有白色箱体，水箱的具体身份未确认。','设备台或屋顶承托区，预留到达路径',['方形／圆筒候选','底座','进出水细管','单组／成组'],'不能把每个白箱都标成水箱，也不能从模型箱体断言真实设备规格。','先入待研究条目；水箱精细做法由后续明确来源补齐。','proposed_variant'),
 comp('C05','天线状杆架','屋顶',['J01'],'中心竖杆配多高度侧向附件，细杆与较厚附件共同形成轮廓。','屋顶独立基座，避开出口与设备检修通道',['高度','横臂层数','附件朝向','杆径层级'],'不把晾衣架当作天线；不要给每栋复制同一高度同一坐标。','先用小样本验证四向旋转、承托与邻接更新，再发展电视天线／通信杆等分支。','extracted_reference','J01'),
 comp('C06','外露竖管与转接','设备',['V01-281','J00-material'],'连续竖向细杆附着实体墙，局部连接节点形成厚度。','实体墙带、边角或湿区设备带',['闪长岩墙候选','竖管连续高度','支架间距','上下转接'],'不横穿窗洞与出入口；墙方块连接状态需要核对。','沿用用户提出的闪长岩墙水管表达；默认不是结构柱。'),
 comp('C07','屋顶晾晒架','生活',['V01-106','V01-126'],'成对竖柱与细横线组成开敞架，分组排列。','可到达的屋顶生活区',['列数','柱距','横线高度','有无衣物'],'不能把整片屋顶填满，也不能和天线共用语义标签。','适合旧住宅生活感；现代办公楼按用途禁用或降权。'),
 comp('C08','轻型遮棚','生活',['V01-126'],'薄屋面、少量支柱、下方留空。','屋顶或阳台可用区，与通道相邻',['开间','薄顶材质','柱数','是否贴墙'],'不要把薄棚做成厚实楼层；不堵楼梯出口。','保留轻重对比，不把每栋都做成相同棚。'),
 comp('C09','屋顶种植床与花盆','生活',['V01-106','V01-281'],'种植床成小组，留出空白地面与步行联系。','有使用路径的屋顶生活区',['床数','长宽变化','作物／盆栽','有无边框'],'不要平均点撒；不与管线、天线基座重叠。','园林需先定空间与路径；不是看到空地就塞花盆。'),
 comp('C10','楼梯出屋面体量','屋顶',['V01-106','V01-281'],'主楼之上有偏置的凸起围护，与设备及生活区并置。','必须对齐下面的楼梯或核心',['位置','体量高度','顶面形式','出口方向'],'不凭外观声称内部楼梯连通；不能随意漂移核心。','屋顶轮廓变化要受下面的交通体系约束。'),
 comp('C11','女儿墙与压顶','墙面',['V01-126','V01-281'],'连续边界加薄压顶，材质与窗台/横带产生呼应。','屋顶外轮廓与退台边缘',['墙高','压顶材料','转角收口'],'不能为做压顶抹平已确认的体块变化。','用连续收边统一细节较多的建筑。'),
 comp('C12','底层大开口与招牌','底层',['V01-126','V01-221'],'首层有不同于住宅层的开口比例，彩色面板局部集中。','真正的入口或沿街商业段',['门洞','牌匾宽度','招牌颜色上限','檐口'],'不是所有住区首层都改商铺；不得封住入口。','把街道使用与上层住宅分清；用于社区配套时另定范围。'),
 comp('C13','实体墙／窗列／凹带','墙面',['V01-35','V01-221'],'同栋立面可同时存在大实体面、单窗列和连续后退开口。','先依据房间与公共交通分配区域',['区域边界','窗墙比例','进退层级','横带是否连续'],'不要只随机改变玻璃颜色来解决平面单薄。','总体体块、立面区域、单窗细部三个尺度分别设计。'),
 comp('C14','近色块与次色玻璃','材料',['J00-material'],'同一主色系材料交错，少量不同玻璃色；细部不独占全部表现。','仅在允许的墙面/窗面掩码内',['主材','近色候选','点缀强度','稳定种子','保护边缘'],'本项目按用户要求做近似颜色单块穿插，不改为成片污渍；全模型计数不能变成新立面配额。','按年代和维护程度调强度；需要用原版材质复看真实色差。'),
 comp('C15','屋顶连排设施','设备',['J03'],'重复箱体、台阶形顶部、侧向短杆和连接线构成一组。','屋顶独立设备带',['单元数','间距','连接方向','端部收口'],'具体设备用途待确认；不把研究段直接命名成水箱排。','先保存准确源状态，后续有证据再细分风机／设备柜等类型。','extracted_reference','J03')]
rules=[
 {'id':'R01','rule':'先空间，再装饰','detail':'建筑用途与房间/核心决定窗洞和设备位；重复层形成秩序，附属设施在允许位置产生差异。'},
 {'id':'R02','rule':'随机按层级分工','detail':'体块与立面分区不随机；住户级决定防盗网、空调和少量生活物；单方块级只做受限近色材质变化。'},
 {'id':'R03','rule':'设备需要安装关系','detail':'每个构件记 host、anchor、facing、support、clearance、连接对象；机箱、支架、管线作为组合而非散件撒点。'},
 {'id':'R04','rule':'设备量与开灯量分开','detail':'住宅约 70% 亮灯沿用当前项目的用户偏好；空调外机、晾晒架和屋顶水箱不按这一比例生成。视频无夜景验证。'},
 {'id':'R05','rule':'同一组件按风格改变组合','detail':'城中村可强调外露设备与生活叠加；千禧商品住宅按单元组织并控制杂乱；现代公共建筑减少外露或集中到设备区。'},
 {'id':'R06','rule':'层次要有前后关系','detail':'窗后背景—玻璃—窗框—防盗网—雨棚分别占层；外机与竖管选择实体墙带，转角和端部单独处理。'},
 {'id':'R07','rule':'样本先通过小范围复用','detail':'验证朝向、支撑、玻璃与铁栏连接、两格通行净空及原版材质外观，再将模块接入 HAF。'},
 {'id':'R08','rule':'保留未知与负例','detail':'外观看似水箱/天线不代表用途已证实；缺少内部功能与游戏验证时维持 pending，不用后续新案例替前案验收。'}]
catalog={'schema_version':'0.1','name':'HAF Exterior Study Library','date':'2026-10-28','haf_mainline':'0.4','scope':'视频与 NBT 的参考构件库；不是 HAF 引擎升级或模型权重训练。','source':source,'observations':observations,'components':components,'rules':rules,'sample_manifest':json.loads((R/'samples/manifest.json').read_text()),'placement_contract':{'component_id':'required','building_id':'required','household_or_zone_id':'required','host_surface':'required','anchor_xyz':'required','facing':'required','occupied_envelope':'required','clearance_envelope':'required','support_points':'required','connection_targets':'optional','variant':'required','seed_namespace':'building/zone/component','source_evidence_ids':'required','geometry_status':'observed | inferred | proposed','implementation_status':'reference_only | implemented | game_verified','consumer':None},'current_user_constraints':['当前六栋住区保持前排10层一梯一户、后排15层一梯两户与逐栋后退10格。','保留已确认户型、内饰、园林与体块；这轮研究不自动修改楼盘。','有防盗网和无网窗户混合。','约70%住宅亮灯是项目偏好；允许不同灯具表达。','外墙近似颜色方块穿插，不做成片旧化。','可用闪长岩墙在部分位置模拟水管。'],'next_validation':['一段窗＋防盗网＋雨棚＋空调＋竖管的组合样板，查看正面、斜面与剖切。','一个屋顶分区样板：交通出口、设备、晾晒/休息各有位置和通路。','选一栋未参与本轮学习的新建筑，检验移植效果后再修改楼盘。'],'source_coverage_limit':'当前为关键帧观察及已列 NBT 区域回读，不宣称视频所有细节或整个模型功能已经核实。'}
dump('catalog.json',catalog)
dump('next_source_template.json',{'source_id':'','url_or_library_file_id':'','title':'','creator':'','hash_if_file':'','access_method':'','evidence':[],'observed_elements':[],'inferred_functions':[],'unknowns':[],'component_links':[],'transfer_rules':[],'counterexamples':[],'consumer':None,'verification':'pending'})
if (S/'inspection/stats.json').exists():
 shutil.copyfile(S/'inspection/stats.json',R/'data/jiejao_stats.json')
 shutil.copyfile(S/'inspection/preview_approximations.json',R/'data/preview_approximations.json')
for name in ['overview','reverse','roof','mast','equipment','roof_row','plan_y12']:
 if (S/'inspection/previews/jiejao'/f'{name}.png').exists():
  im=Image.open(S/'inspection/previews/jiejao'/f'{name}.png').convert('RGB');im.save(R/'previews'/f'{name}.jpg',quality=88)
def e(x):return html.escape(str(x))
def data(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
def img(name,caption):return '<figure><img loading="lazy" src="'+data(R/'previews'/f'{name}.jpg','image/jpeg')+'" alt="'+e(caption)+'"><figcaption>'+e(caption)+'</figcaption></figure>'
def table(headers,rows):return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
status={'observed_recipe':'已观察 · 做法待实现','extracted_reference':'实物片段 · 待游戏验证','proposed_variant':'候选 · 待补证据'}
cards=''
for c in components:
 cards+='<article class="card" data-zone="'+c['zone']+'"><div class="eyebrow">'+c['id']+' · '+c['zone']+'</div><h3>'+c['name']+'</h3><span class="pill">'+status[c['status']]+'</span><p>'+c['form']+'</p><dl><dt>安装关系</dt><dd>'+c['anchor']+'</dd><dt>可变参数</dt><dd>'+' / '.join(c['parameters'])+'</dd><dt>迁移方式</dt><dd>'+c['transfer']+'</dd><dt>避免</dt><dd>'+c['avoid']+'</dd></dl><small>依据：'+', '.join(c['evidence'])+'</small></article>'
evidence=table(['证据','时间／坐标','确认内容','边界'],[(e(o['id']),e(o['at']),e(o['observation']),e(o['limit'])) for o in observations])
sample_rows=[]
for m in catalog['sample_manifest']:
 link='<a download="'+m['file']+'" href="'+data(R/'samples'/m['file'],'application/octet-stream')+'">下载 NBT</a>'
 sample_rows.append((m['id']+' '+e(m['label']),' × '.join(map(str,m['size_xyz'])),str(m['blocks'])+' / '+str(m['states']),e(str(m['source_bbox_xyz_exclusive'])),link))
samples=table(['原样摘录','尺寸 X/Y/Z','方块 / 状态','原文件范围（高端不含）','文件'],sample_rows)
readme='''HAF Exterior Study Library 0.1 · 2026-10-28

这是 HAF 0.4 的研究资料，不是新的引擎版本。当前包含 15 类参考条目、视频时间证据、jiejao 实物回读、3 个原样摘录 NBT 与 8 条迁移规则。

打开 HAF_Exterior_Library.html 可离线浏览并下载数据和三个 NBT。data/catalog.json 是可续写的数据目录；data/next_source_template.json 用于登记下一条视频/模型来源。没有自动接入 HAF 放置流程；所有 consumer 均为 null。

samples 是参考片段，状态保持原样。J01 是天线状杆架；J02 是附墙设备盒；J03 是屋顶设施排。用途解释不是原作者命名。J02 需要背后的墙面，J01/J03 需要屋顶承托。空位未导出，不会主动清除目标已有方块；摆放前需安排空间。旋转、承托、邻接更新、碰撞、游戏表现均待测。

原文件由用户提供，未在包中重复包含。用 Python 3 在 tools 目录可重现摘录：
python extract_samples.py /path/to/jiejao.nbt /path/to/output
工具要求原文件 SHA256 与记录一致。导出后用独立读取器核对坐标和状态。

previews 是从 NBT 生成的无纹理诊断图，不是游戏截图。部分不支持的方块用同类几何或盒形近似；详见 data/preview_approximations.json。局部配图含源模型上下文，比摘录范围更大。材质统计是全模型计数，不能当立面配额。模型没有声明现实建筑身份，视频也不是实测图纸。

未保存/转载视频截图；报告链接到原作并记录观察位置。原作：赵相机咔咔一顿拍，BV17x42117gm。
'''
(R/'README.txt').write_text(readme)
doc='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>HAF 外表面构件研究库 0.1</title><style>
:root{--ink:#203b42;--muted:#647170;--paper:#f6f3e9;--line:#d6d9cb;--accent:#b85e35}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.75 system-ui,-apple-system,"Microsoft YaHei",sans-serif}header,main,footer{max-width:1240px;margin:auto;padding:36px 30px}header{padding-top:64px}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--accent);font-weight:700}h1{font-size:clamp(32px,5vw,58px);line-height:1.18;margin:16px 0 22px}h2{font-size:27px;margin:4px 0 15px}h3{font-size:21px;margin:7px 0 12px}p{margin:12px 0}a{color:#9a4826;text-underline-offset:4px}.lead{font-size:21px;max-width:900px}.note,small,figcaption{color:var(--muted);font-size:13px}.notice{border-left:4px solid var(--accent);padding:14px 20px;background:#ede9db}.nav{display:flex;gap:10px;flex-wrap:wrap;margin:25px 0}.nav a,button{border:1px solid var(--line);background:#fffdf6;border-radius:4px;padding:8px 14px;color:var(--ink);font:inherit;cursor:pointer;text-decoration:none}.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:24px;align-items:center}.hero figure{margin:0}.stats{display:flex;gap:35px;margin:24px 0}.stats b{font-size:28px;display:block}.stats span{font-size:12px;color:var(--muted)}section{padding:36px 0;border-top:1px solid var(--line)}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.card{background:#fffdf6;border:1px solid var(--line);padding:22px;border-radius:6px}.pill{font-size:11px;border-radius:30px;background:#e5e9df;padding:4px 9px}.card p{font-weight:550}.card dl{font-size:14px}.card dt{font-size:11px;color:var(--accent);font-weight:700;margin-top:12px}.card dd{margin:2px 0}.card small{font-size:11px}figure{margin:15px 0}figure img{width:100%;display:block;border:1px solid var(--line);border-radius:4px}figcaption{padding:9px 2px}.gallery{display:grid;grid-template-columns:1fr 1fr;gap:20px}.table-scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:13px 10px}th{background:#e5e9df;color:#304e52}li{margin:9px 0}.filter{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}input,select{border:1px solid var(--line);border-radius:4px;padding:11px;font:inherit;background:#fffdf6}input{flex:1;min-width:160px}details{margin:14px 0}summary{cursor:pointer;font-weight:700}code{overflow-wrap:anywhere;font-size:12px}footer{font-size:13px;color:var(--muted);padding-bottom:50px}.hidden{display:none!important}@media(max-width:760px){header,main,footer{padding:25px 18px}.hero,.grid,.gallery{grid-template-columns:1fr}.stats{gap:20px}.lead{font-size:18px}section{padding:25px 0}td{min-width:130px}}@media print{button,.filter,.nav{display:none}.grid{grid-template-columns:1fr 1fr}.card{break-inside:avoid}body{background:white}header,main{padding:10px}details>*{display:block}}
</style></head><body><header><div class="eyebrow">GAFAcraft · HAF 0.4 / REFERENCE LIBRARY 0.1</div><div class="hero"><div><h1>让建筑的表面<br>有使用的痕迹。</h1><p class="lead">外立面、内部组织、墙面材料与附属设施，一起学习；把做法保存为可追溯、可变化的构件。</p><p>广东城中村视频 × jiejao.nbt<br><span class="note">研究日期 2026-10-28 · 原创楼盘的后续迁移资料</span></p><div class="stats"><div><b>15</b><span>构件与表达条目</span></div><div><b>3</b><span>NBT 实物片段</span></div><div><b>8</b><span>组合与迁移规则</span></div></div></div>'''+img('overview','jiejao 原文件回读 · 无纹理诊断图，部分方块几何近似。')+'''</div><nav class="nav"><a href="#learning">四条学习线</a><a href="#components">构件目录</a><a href="#samples">实物摘录</a><a href="#reuse">举一反三</a><a href="#evidence">来源与证据</a></nav><p class="notice">这轮完成研究库与参考摘录。当前楼盘没有改动；构件尚未接入 HAF 自动放置，游戏内表现、连接和旋转仍待验证。</p></header><main>
<section id="learning"><div class="eyebrow">01 / READ THE BUILDING</div><h2>四条学习线，先建立秩序。</h2>'''+table(['学习线','本次看到的关系','迁移到我们的住宅'],[
 ('外立面','红褐主墙＋有厚度的单窗；另一栋浅色墙＋红褐横带，并有实体墙、窗列、凹带之分。','先确定立面区域和开窗，再组合防盗网、雨棚与设备。原有凸凹体块继续保留。'),
 ('内部组织','视频的重复隔间、中部通道和楼梯位置可辨；jiejao 剖切可见部分隔片，功能配置不足。','只借鉴空间与窗的对应。城中村通廊小间不能照搬为前排一梯一户的大户型。'),
 ('整体风格','底层、标准层、屋顶各有职责；统一材料与收边维持秩序，设施和生活物作次级变化。','千禧住宅保留较完整的开发秩序，再加入住户改动，控制杂乱程度。'),
 ('墙面材料','jiejao 有多种浅色墙材和少量次色玻璃，变化与窗、设备、横带叠加。','按用户要求做近似颜色单块穿插；主材仍占主导，窗洞/框/压顶用独立规则保护。')])+'''<div class="gallery">'''+img('reverse','反向回读：主色、横带、设备与局部色差共同形成层次。')+img('plan_y12','Y≤12 的俯视剖切，仅展示本层几何；不能据此认定完整户型或可通行内饰。')+'''</div></section>
<section id="components"><div class="eyebrow">02 / COMPONENT CATALOG</div><h2>外表面设施与装饰目录</h2><p>每条包含证据、安装关系、变化参数和禁用条件。观察到的形态与我们提出的用途/做法分开记录。</p><div class="filter"><input id="search" aria-label="搜索构件" placeholder="搜索：水箱、空调、天线、近色…"><select id="zone" aria-label="按区域筛选"><option value="">所有区域</option>'''+''.join('<option>'+z+'</option>' for z in ['墙面','设备','屋顶','生活','底层','材料'])+'''</select><span id="count" aria-live="polite">15 个条目</span></div><div class="grid" id="cards">'''+cards+'''</div></section>
<section id="samples"><div class="eyebrow">03 / PRESERVED BLOCK STATES</div><h2>三个可下载的 jiejao 原样片段</h2><p>保留原方块状态，移到局部坐标原点。每个导出均已独立回读，核对所有坐标与状态相同。它们是参考件，尚未作为通用预制件接入生成器。</p>'''+samples+'''<div class="gallery">'''+img('mast','J01 所在的原模型上下文；视图含邻近构件，导出仅为表中 3×7×3 范围。')+img('equipment','J02 原墙面上下文：箱体、顶部薄盖、侧件和下部附件。梯子/拉杆在此预览中使用盒形近似。')+img('roof_row','J03 原模型上下文：重复单元与细连接件。具体设备功能仍待确认。')+img('roof','屋顶真俯视回读：设备区域与留空、核心位置的关系。')+'''</div><p class="notice">样本的空气格未写入，摆放时需要安排空位。J02 原安装面在 +Z 侧；J01/J03 需要屋顶承托。复制、旋转或邻居更新后，薄构件连接与支撑要重新验证。</p></section>
<section id="reuse"><div class="eyebrow">04 / TRANSFER RULES</div><h2>把做法变成可组合的规则。</h2><div class="grid">'''+''.join('<article class="card"><div class="eyebrow">'+r['id']+'</div><h3>'+r['rule']+'</h3><p>'+r['detail']+'</p></article>' for r in rules)+'''</div><h3>下一步先做两个样板，再迁移到楼盘</h3><ol>'''+''.join('<li>'+e(s)+'</li>' for s in catalog['next_validation'])+'''</ol><p>新增来源统一登记：网址/文件 → 时间/坐标 → 观察 → 构件 → 变体 → 安装约束 → 验证状态。新视频补充变体和反例，不覆盖已有明确证据。</p><button id="downloadCatalog">下载构件目录 JSON</button> <button id="downloadTemplate">下载下一条来源模板</button></section>
<section id="evidence"><div class="eyebrow">05 / EVIDENCE & LIMITS</div><h2>来源与观察位置</h2><p><a target="_blank" rel="noopener noreferrer" href="'''+source['video']['url']+'''">原视频 · 赵相机咔咔一顿拍 · BV17x42117gm</a><br><span class="note">本报告记录关键施工段与成品画面，不是完整字幕稿，未保存或转载视频截图。</span></p><p><a href="[maintainer archive reference]">jiejao.nbt 原文件</a> · 108×43×72 · 44,127 条方块记录 · 325 个调色板状态<br><code>SHA256 '''+source['nbt']['sha256']+'''</code></p><details><summary>展开全部证据记录</summary>'''+evidence+'''</details><details><summary>预览与实现边界</summary><p>所有模型配图由 NBT 回读生成，无资源包纹理，不是 Minecraft 实机截图。现有预览器不能原样显示全部材料/状态，本次诊断图使用了声明过的几何替代或盒形近似，未更改源 NBT，也未扩大引擎支持承诺。准确材料和状态以下载的数据为准。</p><p>video_only、NBT_readback 和用途推断分开。没有水箱的明确细部证据时先保留候选；不能把避雷针方块名等同真实设备用途。未在这轮更新已安装 skill，未训练模型权重。</p></details></section></main><footer>HAF Exterior Study Library 0.1 · 可继续追加来源与样本。<br>保存关系、适用条件和失败边界，让每个新案例都能帮助下一次设计。</footer>
<script id="catalog-data" type="application/json">'''+json.dumps(catalog,ensure_ascii=False).replace('</','<\/')+'''</script><script id="template-data" type="application/json">'''+(R/'data/next_source_template.json').read_text()+'''</script><script>
const cards=[...document.querySelectorAll('#cards .card')];
function filterCards(){const q=document.getElementById('search').value.trim().toLowerCase();const z=document.getElementById('zone').value;let n=0;for(const c of cards){const show=(!q||c.textContent.toLowerCase().includes(q))&&(!z||c.dataset.zone===z);c.classList.toggle('hidden',!show);if(show)n++;}document.getElementById('count').textContent=n+' 个条目';}
document.getElementById('search').addEventListener('input',filterCards);document.getElementById('zone').addEventListener('change',filterCards);
function downloadJSON(id,name){const blob=new Blob([document.getElementById(id).textContent],{type:'application/json;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
document.getElementById('downloadCatalog').addEventListener('click',()=>downloadJSON('catalog-data','HAF_Exterior_Catalog.json'));
document.getElementById('downloadTemplate').addEventListener('click',()=>downloadJSON('template-data','HAF_Source_Template.json'));
</script></body></html>'''
(R/'HAF_Exterior_Library.html').write_text(doc)
out=R.parent/'HAF_Exterior_Library.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file() and '__pycache__' not in str(p):z.write(p,p.relative_to(R))
print(json.dumps({'html_bytes':(R/'HAF_Exterior_Library.html').stat().st_size,'zip_bytes':out.stat().st_size,'components':len(components),'observations':len(observations),'samples':len(sample_rows)},ensure_ascii=False))
