"""Append video research to v0.1; no building mutation or automatic placement."""
from pathlib import Path
import json,html,base64,re,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
old=json.loads((R/'history/catalog_v01.json').read_text());d=json.loads(json.dumps(old))
d['schema_version']='0.2';d['scope']='HAF 0.4 参考研究库：三条视频＋jiejao；新增预制组合与区域组织。无新整栋生成，无自动放置消费者。'
chapters=[['预览','00:00–00:40'],['墙面材质','00:40–01:17'],['窗户样式','01:17–01:40'],['围墙样式','01:40–02:13'],['外部装饰','02:13–04:12'],['窗户放置','04:12–04:33'],['杂项','04:33–05:28'],['例子演示','05:28–13:12']]
d['source']['rural_video']={'id':'V02','title':'[Minecraft] 如何像预制菜一样预制农村自建房','author':'Bad_Door','url':'https://www.bilibili.com/video/BV1TpGw6JEHQ/','published':'2026-07-31','duration_seconds':792,'chapters':chapters,'method':'登录后播放器关键帧观察；章节表来自页面。并非逐秒观看或完整字幕转录。','coverage':'墙材、窗型、围墙、外饰、窗口放置、收边与整栋组合。','not_covered':'完整村落规划、完整室内户型与家具、NBT 源工程、原版无光影验证。'}
d['source']['hk_video']={'id':'V03','title':'用MC方块打造一个“小香港”#01','author':'赵相机咔咔一顿拍','url':'https://www.bilibili.com/video/BV1Hf421Q7iq/','published':'2024-06-30','duration_seconds':215,'method':'登录后播放器关键帧观察。页面简介说明为直播建设成果展示，区域计划继续扩建。','coverage':'街面、高低体量、街角、立面进退、招牌、路面与屋顶。','not_covered':'施工顺序、精确尺寸、完整内饰、实际通行、整区完工。自动播放进入的 #02 不纳入本轮证据。'}
def obs(id,at,text,limit,kind='video_visual'):
 return {'id':id,'at':at,'kind':kind,'observation':text,'limit':limit}
newobs=[
 obs('V02-22','00:22','成组展示浅色或黄色墙面的自建房，屋顶有边缘叠层、箱罐状设施、设备盒，楼体之间有间隔。','这是样板预览；没有可测量的完整村落道路、宅地或院落总图。'),
 obs('V02-49','00:49–00:50','并排展示墙材样板；字幕建议该教程采用每层约 7 格的尺度。','仅为作者案例建议；不能替换我们现有楼盘层高。'),
 obs('V02-60','01:00–01:01','墙材章节提出混合接近颜色的方块。','只学习颜色接近与表面变化关系，不把某一组材料或混合比例设成全局默认。'),
 obs('V02-90','01:30–01:31','凹入窗洞中组合玻璃、竖向锁链与水平细件；画面说明此组窗型使用 2 格墙厚。','模块必须记录依赖墙厚与进深；2 格是此组样板条件，不是所有建筑的最低墙厚。'),
 obs('V02-115','01:55–01:56','围墙样板有节奏性镂空和柱头；物品名显示使用平滑砂岩楼梯。','镂空轮廓、方向与收口应单独建模；不能用整方块填平。'),
 obs('V02-137','02:14–02:18','展示具有削角/阶梯轮廓的罐状设备，外侧组合细杆、栅栏与竖向梯状附件。','字幕有戏谑命名，不能当真实设施说明。暂记水箱/储罐外形候选，工程用途未知。'),
 obs('V02-150','02:30–02:31；02:55–02:56','罐状外饰施工中使用磨制闪长岩楼梯等形成边缘层次，后续添加苍白橡木栅栏附件。','未获得可完整复现的每格布置；苍白橡木类材料与目标游戏版本及引擎支持须另核对。'),
 obs('V02-210','03:30–03:31','浅色竖向细杆贴墙布置，字幕演示在连接部位使用楼梯形方块作过渡。','管线全部材料与连接状态未确认，保留形态和接头关系，不冒充完整配方。'),
 obs('V02-222','03:42–03:43','附墙设备盒有顶部/侧面薄盖、按钮状细件和管线转接，风扇状开口与箱体相互区分。','可借作空调外机表达；模组/资源包及全部状态不能只凭画面确认。'),
 obs('V02-238','03:58–03:59','双扇门两侧用红黄色竖向图案强调门面，上方另有纹样面板。','登记为门口装饰变体；不把节庆装饰铺到每栋、每个入口。'),
 obs('V02-265','04:25–04:26','安装示例让厚窗有清楚的墙洞与侧边，字幕给出该窗型之间至少 2 格间隔的做法。','这是特定尺度下的间距提示；最终必须按净墙段和结构/功能边界检查。'),
 obs('V02-300','05:00–05:01','阳台或楼层边缘有水平红褐色薄装饰带，和浅色栏墙产生层次。','保留为檐口/腰线表达；不认定每条装饰带都等于一层楼。'),
 obs('V02-350','05:50–05:51','整栋示例先在灰色基础体块上向外伸出一段，再继续组织外轮廓。','画面中的 3 格外伸属于作者本例，迁移时由阳台功能和比例决定。'),
 obs('V02-440','07:20–07:21','示例通过复制已有楼层继续形成第三层，窗洞随层重复。','复制须带着核心、楼板与门洞关系核对；视频片段不证明完整楼梯/户型。'),
 obs('V02-600','10:00–10:01','后期选区替换灰色墙面，字幕给出石头/安山岩/砂砾的混合示例，说明材质变体晚于体量。','屏幕命令处于操作中，不把某一帧命令当最终完整配方；不照搬其色差强度。'),
 obs('V02-675','11:15–11:16','局部进一步混入矿石、苔色或其他粗糙纹理，在窗侧形成较强表面变化。','这是作者的强纹理变体。当前住宅用户指定近色单块穿插，默认不引入明显黑斑/大片苔痕。'),
 obs('V02-780','13:00–13:01','成品可见浅色主墙、红褐横带、外凸防盗网、屋顶设备和高低楼体的邻接。','足以研究成品组合，不足以证明完整乡村片区与内部设施已建设。'),
 obs('V03-31','00:31','街道有连续建筑界面、沿街大幅面板和挑出竖牌，路灯、车流、斑马线与人行道共同呈现尺度。','只有表面展示；道路尺寸、实际交通规则、标牌内容未测量。'),
 obs('V03-50','00:50','紫白相间的中层转角楼与更高的窄塔相邻，横带连续转角，窗侧挂有设备盒。','属于作者香港风格作品，不代表香港建筑的统一模板或现实建筑复原。'),
 obs('V03-80','01:20–01:21','相邻建筑高度与窗墙系统不同；底部大檐口、竖牌和车辆强化近景，外机重复成为立面节奏。','重复外机不能自动推成每间房都必须有一台；内饰只见窗后灯点。'),
 obs('V03-105','01:45–01:46','街角楼逐层收退，上部露台保留种植槽和晾晒状杆架；邻侧道路与待建空地清楚可见。','该段说明空间层次，不支持整个区域已经建满或完工的结论。'),
 obs('V03-130','02:10–02:11','实体横带、粗糙竖肋、后退玻璃形成层次，街角用折线转角；底层另设彩色店招状区域。','可见窗后灯具不等于完整功能内饰，横带也不直接证明真实楼板。'),
 obs('V03-158','02:38–02:39','较窄街道两侧有连续商住界面、不同高低的挑出招牌、小雨棚、边界栏杆和少量植被。','需要保持人行道和入口可读，不能把此效果简化成到处塞招牌。'),
 obs('V03-188','03:08–03:09','一栋采用折面蓝玻璃与红褐实体横带的建筑插在其他竖向体量之间，立面进退形成阴影。','这是另一种立面体系；不能将同样玻璃比例用于农村自建房。')]
d['observations']+=newobs
def comp(id,name,zone,ev,form,anchor,params,avoid,transfer,status='observed_recipe'):
 return dict(id=id,name=name,zone=zone,evidence=ev,form=form,anchor=anchor,parameters=params,avoid=avoid,transfer=transfer,status=status,sample_id=None,consumer=None,game_validation='pending')
newcomponents=[
 comp('C16','带墙厚的窗户预制单元','墙面',['V02-90','V02-265'],'把墙洞、玻璃、细杆、窗框与侧边作为完整模块，保留前后层次。','指定厚度的墙段；朝向与窗台标高固定',['墙厚档','洞口尺寸','窗框外包络','周边留墙','朝向'],'不能只存一张正面；复制时要包含需要挖空的区域。','模块写出占用包络和清空包络，再按净墙段分配。'),
 comp('C17','镂空围墙与栏墙段','围护',['V02-115'],'实体、镂空与柱头分工；楼梯形方块塑造重复空隙。','院界、屋顶或阳台边界，按用途选高度',['重复单元','墙高','柱距','转角和端头'],'禁止把防护、游戏碰撞与视觉镂空混为一谈。','建立直段、端头、转角三类参考，分别查相接。'),
 comp('C18','削角罐体与外侧附件','屋顶',['V02-137','V02-150'],'通过楼梯/半砖式层次塑造罐体轮廓，细杆/梯状件附在外侧。','屋顶设备位或独立设备台',['圆筒感／方形','边缘削角','支脚','侧向附件','管口'],'用途未明确时保持罐状设备标签，不误用戏谑字幕。','补充水箱候选的形态来源；精确方块配方待小样板。'),
 comp('C19','细管与转接头','设备',['V02-210','V02-222'],'浅色细杆贴墙，并通过阶梯形接头与设备箱连接。','实体墙或设备带',['管径档','颜色','竖横转接','贴墙距离'],'材料版本/引擎支持未知时不默认可生成；不横穿窗洞。','与 C06 闪长岩墙粗管形成不同粗细选项，连接和支持分别检查。'),
 comp('C20','门口对联式装饰','底层',['V02-238'],'入口两侧竖向色板，上缘纹样板，门洞仍清楚。','真正的主入口两侧',['有／无','图案密度','色彩','上缘面板'],'不把节庆标记放满所有门窗，不让装饰侵入门洞。','住宅按住户选择性采用，公共现代建筑不默认继承。'),
 comp('C21','薄腰线与边缘饰板','墙面',['V02-300','V02-780'],'薄横带在浅色主墙、阳台边缘形成收边与阴影。','已确定楼层/阳台边缘',['带宽','突出深度','连续／中断','转角接头'],'装饰横带不能代替楼板或改变楼层标高。','维持整栋统一色系，再小范围调整端头。'),
 comp('C22','复制楼层与体量变体','空间',['V02-350','V02-440','V02-600'],'先组合基础体量和楼层，再替换表皮材料与设备。','同一层高和核心体系中的标准层',['层数','面宽','进深','阳台位置','顶层退台'],'不能只换色就宣称多栋不同户型；复制后必须查交通核心。','先建立两三种可用平面，再做楼栋/住户级变化。'),
 comp('C23','转角楼的横带与折面','空间',['V03-50','V03-130','V03-188'],'连续横带经过折线/削角转折，玻璃、竖肋与实体带各有进退。','街角或需要转向的立面区域',['转角轮廓','带深','窗后退','竖肋间隔'],'不能只给直角盒子加彩色带就声称完成折面。','先画平面转角与层高，再装立面组件；适合城市街区。'),
 comp('C24','挑出招牌与支架','底层',['V03-31','V03-80','V03-158'],'不同方向和高低的招牌从店铺段挑出，成为街道中景。','对应商铺门面或建筑侧墙',['横牌／竖牌','尺寸','标高','突出深度','支架'],'不无差别塞满窗户；与路灯、树、雨棚和行人净空避让。','用店铺 ID 绑定样式，街道全段控制总密度。'),
 comp('C25','人行道与沿街设施组合','街道',['V03-31','V03-158'],'铺地、灯杆、低栏、雨棚、路口标记一起建立行走界面。','道路边与入口前方',['铺地分区','路灯间距','栏杆开口','雨棚端部'],'不把路边空位全变成树或设备；保持入口和穿行通道。','先定通路及入口，再摆设施；车辆只作尺度参考，不证明模拟交通功能。'),
 comp('C26','退台屋顶与生活设施','屋顶',['V03-105'],'收退楼体提供露台，种植与晾晒状设施占用局部，保留空白。','真实有楼板承托且能到达的露台',['收退范围','核心出口','设备／生活分区','留白'],'没有通路就不能声称可使用；不把全部露台塞满。','与 C07/C09/C10 共用关系，适用密集街区顶层。'),
 comp('C27','小片乡村的宅地组合','空间',['V02-22','V02-780'],'设计推演：共享村路连接独立宅地，各宅地包含房子、入口前场及服务边界。','道路—宅地—院门—主入口',['原型数量','宅地朝向','前场退让','支巷','菜地/公共空地'],'不是视频测绘，不套整齐小区排布；不能默认每栋都有同样的大院。','优先做可达的路与院，再用 C16–C22 组合自建房。','proposed_variant')]
d['components']+=newcomponents
newrules=[
 {'id':'R09','rule':'预制件要带接口','detail':'同时保存占用包络、清空包络、墙厚/楼层条件、安装点、朝向、支撑与端部。一个正面贴图不等于可复用模块。'},
 {'id':'R10','rule':'先复用关系，再复用外观','detail':'核心与功能平面先成立，楼层复制保持接口，楼栋差异再作用于阳台、顶层、窗型与材质。'},
 {'id':'R11','rule':'乡村先组织宅地与留空','detail':'我们的推演：村路和支巷连接院门/前场，菜地、停车、晒场与树荫空地有用途。建筑数量不能代替区域组织。'},
 {'id':'R12','rule':'港式氛围来自街面组合','detail':'从该作品推得：连续底层界面、高低建筑相接、转角处理、近中远景细节共同作用。招牌和外机只是其中一层。'},
 {'id':'R13','rule':'尺度参数跟随样板','detail':'该自建房教程的 7 格层高、2 格墙厚/窗间距属于其案例，不改写既有楼盘参数；导入前按所需细部和空间重新定尺度。'},
 {'id':'R14','rule':'材质变化有强弱分支','detail':'近色混合可复用；明显矿石斑点、苔痕属于强纹理分支。当前住宅坚持用户指定的近色单块穿插。'},
 {'id':'R15','rule':'成果展示不反推全部施工','detail':'小香港 #01 提供最终视觉关系，不能据此虚构原作者的施工算法、精确参数或全内饰。视频新变体仍为 research_only。'}]
d['rules']+=newrules
d['placement_contract'].update({'clear_volume_policy':'preserve | clear_listed_cells | reject_if_occupied','host_wall_thickness':'required_for_window_module','end_cap_or_corner_type':'required_for_repeating_edge','material_version_support':'must_be_checked','source_sample_dimensions':'case_specific_not_global_default'})
d['regional_patterns']=[
 {'id':'P01','name':'乡村宅地小片区','status':'proposed','source_evidence':['V02-22','V02-780'],'basis':'作者展示自建房预制组合；路网与宅地关系由我们另行推演。','sequence':['道路与公共空地','独立宅地及入口','两三类平面与核心','不同层数/阳台/屋顶','设备与近色墙材','通路和细部复核'],'functional_zones':['居住','前场/晒场','菜地或服务后场','小卖部候选','公共树荫空地'],'consumer':None,'generated_nbt':False,'diagram_scale':'topological_not_metric'},
 {'id':'P02','name':'城市沿街高低组合','status':'inferred_design_rule','source_evidence':['V03-31','V03-50','V03-105','V03-158'],'basis':'根据成品关系归纳，非原作者施工说明。','sequence':['道路与沿街建筑线','高低体量与街角','底商/入口','立面区域','招牌/雨棚/外机','屋顶与街道设施'],'consumer':None,'generated_nbt':False,'diagram_scale':'topological_not_metric'}]
d['next_validation']=['先做窗洞＋厚墙＋防盗网＋空调＋细管的小样，记录安装接口，检查正面/斜面/剖切。','再做两三种平面成立的自建房原型，改变层数、阳台或顶层，确认变化不破坏楼梯和入口。','最后做一小片乡村试验：先村路、宅地、公共空地，再组合房子；新模块经游戏验证后再用于正式楼盘。']
d['source_coverage_limit']='三条视频均为已记录关键段/帧观察；V02 有章节表，V03 是成品展示。未取得两条新视频的模型文件，新增构件没有 NBT，不宣称已完成村落或港式街区。'
d['changelog']=[{'version':'0.1','summary':'原广东城中村视频＋jiejao，15条目、3实物片段、8规则。'},{'version':'0.2','summary':'增加两条视频，追加12条目、7条组合规则与2种区域推演；保留全部旧证据、原样本和旧版快照。'}]
(R/'data/catalog.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))

village='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 540" role="img" aria-label="乡村宅地关系推演，无尺度"><rect width="900" height="540" fill="#eeeade"/><style>text{font:16px sans-serif;fill:#25444b}.small{font-size:12px}.house{fill:#d5c5a4;stroke:#8a785a;stroke-width:2}.yard{fill:#e0dcca;stroke:#bbb59e;stroke-width:1}.route{fill:none;stroke:#b5beb7;stroke-linecap:round;stroke-linejoin:round}</style><text x="25" y="32" font-weight="bold">P01 · 乡村：路—宅地—前场—房子</text><text x="25" y="54" class="small">建议的空间关系图 / 无尺度 / 非视频平面 / 尚未生成 NBT</text><path class="route" stroke-width="52" d="M0 330 L210 330 L450 290 L660 310 L900 290"/><path class="route" stroke-width="22" d="M450 290 L430 170 L470 70 M660 310 L645 480 M210 330 L205 480"/><path class="route" stroke="#f8f5e9" stroke-width="2" stroke-dasharray="10 9" d="M0 330 L210 330 L450 290 L660 310 L900 290"/><rect class="yard" x="38" y="85" width="155" height="207"/><rect class="house" x="57" y="106" width="111" height="98"/><text x="71" y="150">A1 · 2层</text><text x="67" y="246">入口前场</text><path d="M115 292V330" stroke="#a78c64" stroke-width="12"/><rect class="yard" x="234" y="96" width="155" height="175"/><rect class="house" x="252" y="112" width="112" height="95"/><text x="268" y="157">B1 · 3层</text><text x="252" y="244">小院 / 停车</text><path d="M310 270V311" stroke="#a78c64" stroke-width="12"/><rect class="yard" x="490" y="82" width="150" height="177"/><rect class="house" x="510" y="100" width="109" height="105"/><text x="524" y="151">A2 · 2层</text><text x="510" y="241">半围合前场</text><rect class="yard" x="720" y="74" width="145" height="167"/><rect class="house" x="740" y="92" width="105" height="96"/><text x="751" y="137">C1 · 4层</text><path d="M792 241V296" stroke="#a78c64" stroke-width="12"/><rect class="yard" x="38" y="378" width="144" height="138"/><rect class="house" x="58" y="410" width="104" height="86"/><text x="71" y="453">B2 · 3层</text><rect class="yard" x="252" y="365" width="158" height="151"/><rect class="house" x="274" y="394" width="112" height="93"/><text x="286" y="438">A3 · 2层</text><path d="M331 365V310" stroke="#a78c64" stroke-width="12"/><rect x="455" y="364" width="150" height="145" fill="#b8c6a2"/><path d="M465 388H592 M465 412H592 M465 437H592 M465 464H592 M465 489H592" stroke="#819b70" stroke-width="10"/><text x="480" y="391">菜地 / 后场</text><rect class="yard" x="690" y="361" width="180" height="154"/><rect class="house" x="758" y="400" width="94" height="95"/><text x="775" y="443">小卖部</text><text x="712" y="384">共享门前空地</text><circle cx="663" cy="226" r="33" fill="#6f9271"/><circle cx="682" cy="246" r="23" fill="#88a578"/><text x="626" y="275">树荫节点</text><text x="25" y="355" class="small">村路：承接公共空地与支巷</text><text x="458" y="535" class="small">宅地大小、朝向和楼层应有变化，入口仍必须接上路。</text></svg>'''
urban='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 360" role="img" aria-label="城市街面高低组合推演"><rect width="900" height="360" fill="#eeeade"/><style>text{font:15px sans-serif;fill:#25444b}.s{font-size:12px}</style><text x="25" y="30" font-weight="bold">P02 · 城市：连续底层＋高低相接＋街角转折</text><text x="25" y="51" class="s">从“小香港”成品归纳 / 关系示意，非原作者测量或施工图</text><rect x="35" y="186" width="135" height="100" fill="#d2c8b8"/><rect x="170" y="112" width="152" height="174" fill="#a7a5b6"/><rect x="322" y="72" width="106" height="214" fill="#c68b65"/><path d="M428 286V132H554L582 160V286Z" fill="#aabbbb"/><rect x="610" y="158" width="120" height="128" fill="#cfbd91"/><rect x="730" y="91" width="130" height="195" fill="#a5af9d"/><g stroke="#ece9de" stroke-width="9"><path d="M43 216H162 M43 245H162 M177 143H314 M177 177H314 M177 210H314 M177 244H314 M329 102H420 M329 135H420 M329 168H420 M329 201H420 M329 234H420 M435 166H548L574 185 M435 205H548L574 224 M435 244H574 M618 188H723 M618 222H723 M738 122H852 M738 155H852 M738 188H852 M738 221H852 M738 254H852"/></g><g fill="#506c71"><path d="M35 266H582V291H35Z M610 266H860V291H610Z"/></g><rect x="35" y="294" width="825" height="20" fill="#d9d3c4"/><rect x="35" y="318" width="825" height="30" fill="#8c9994"/><rect x="207" y="212" width="24" height="60" fill="#bc5d3c"/><rect x="473" y="198" width="24" height="66" fill="#bd9654"/><rect x="684" y="224" width="55" height="18" fill="#668b80"/><text x="45" y="282" fill="#fff">底层门面与入口</text><text x="591" y="286" transform="rotate(-90 591 286)" class="s">支街</text><text x="46" y="337" fill="#fff" class="s">行人视角：入口、雨棚和招牌先可读；上部立面再形成节奏。</text></svg>'''
(R/'diagrams/village_pattern.svg').write_text(village);(R/'diagrams/street_pattern.svg').write_text(urban)
def e(s):return html.escape(str(s))
def urlbytes(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
def picture(name,cap):return '<figure><img loading="lazy" src="'+urlbytes(R/'previews'/f'{name}.jpg','image/jpeg')+'" alt="'+e(cap)+'"><figcaption>'+e(cap)+'</figcaption></figure>'
def table(headers,rows):return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def svg_image(s,cap):return '<figure>'+s+'<figcaption>'+e(cap)+'</figcaption></figure>'
statuses={'observed_recipe':'已观察 · 做法待实现','extracted_reference':'实物片段 · 待游戏验证','proposed_variant':'推演/候选 · 待验证'}
cards=''
for c in d['components']:
 new=' · 本轮新增' if c['id'] in {q['id'] for q in newcomponents} else ''
 cards+='<article class="card" data-zone="'+c['zone']+'"><div class="eyebrow">'+c['id']+' · '+c['zone']+new+'</div><h3>'+c['name']+'</h3><span class="pill">'+statuses[c['status']]+'</span><p>'+c['form']+'</p><dl><dt>安装关系</dt><dd>'+c['anchor']+'</dd><dt>可变参数</dt><dd>'+' / '.join(c['parameters'])+'</dd><dt>迁移方式</dt><dd>'+c['transfer']+'</dd><dt>避免</dt><dd>'+c['avoid']+'</dd></dl><small>依据：'+', '.join(c['evidence'])+'</small></article>'
previous_html=(R/'history/HAF_Exterior_Library_v01.html').read_text();css=re.search(r'<style>(.*?)</style>',previous_html,re.S).group(1)
css+='svg{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:4px}.banner{background:#e5e9df;padding:20px;border-radius:6px}.split{display:grid;grid-template-columns:1fr 1fr;gap:20px}@media(max-width:760px){.split{grid-template-columns:1fr}}'
doc='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>HAF 构件与区域研究库 0.2</title><style>'+css+'</style></head><body>'
doc+='''<header><div class="eyebrow">GAFAcraft · HAF 0.4 / REFERENCE LIBRARY 0.2</div><div class="hero"><div><h1>从构件到宅地，<br>再到一片街区。</h1><p class="lead">自建房的预制组合，香港风格的街面关系，与 jiejao 的实物方块状态一起积累。</p><p>本轮新增 2 条视频 · 12 个条目 · 7 条规则<br><span class="note">2026-10-28 / 原有城中村视频与 NBT 摘录全部保留</span></p><div class="stats"><div><b>27</b><span>累计参考条目</span></div><div><b>3</b><span>已有 NBT 实物片段</span></div><div><b>15</b><span>累计组合规则</span></div></div></div>'''+svg_image(village,'先把路、宅地和公共空地组织好，再组合不同的房子。此图为设计推演。')+'</div>'
doc+='''<nav class="nav"><a href="#new">两条新资料</a><a href="#region">区域感觉</a><a href="#components">构件库</a><a href="#samples">原实物片段</a><a href="#reuse">组合规则</a><a href="#evidence">证据索引</a></nav><p class="notice">这一版完成研究与组合推演。没有新增整栋建筑或村落 NBT；新增视频做法没有自动接入 HAF。原住宅楼盘、已安装 skill 和三个源样本均未修改。</p></header><main>'''
doc+='<section id="new"><div class="eyebrow">01 / TWO NEW SOURCES</div><h2>一条教预制组合，一条展示街区成品。</h2><div class="split">'
for key in ['rural_video','hk_video']:
 s=d['source'][key];doc+='<article class="card"><div class="eyebrow">'+s['id']+'</div><h3>'+e(s['title'])+'</h3><p>'+e(s['author'])+' · '+('13:12' if key=='rural_video' else '03:35')+'</p><a href="'+s['url']+'" target="_blank" rel="noopener noreferrer">查看原视频</a><p>'+e(s['coverage'])+'</p><small>尚无：'+e(s['not_covered'])+'</small></article>'
doc+='</div>'+table(['维度','自建房教程 V02','小香港 #01 V03','归入研究库'],[
 ('体量与结构','基础体块外伸、窗洞安装、楼层复制、后期换材。','连续街面中穿插不同高度、宽度和转角的建筑。','楼层接口与区域组合分开；不只复制外壳。'),
 ('外立面','厚窗、薄腰线、围墙镂空、外机与细管。','退入玻璃、实体横带、竖肋、挑出招牌和底商。','前后层次＋安装关系＋端部处理。'),
 ('材料与风格','浅色主墙配红褐收边；混合近色，也展示强粗糙纹理。','多栋不同主色，横带/设备让每栋内部保持秩序。','近色混合为基础；强污损与大斑点设为单独分支。'),
 ('内部证据','能看到局部空间与窗后，但未覆盖完整户型/家具。','以外部游览为主，窗后灯光不能证明功能内饰。','内部功能与通行保持待验证。'),
 ('区域证据','提供房屋样板和邻接预览，没有完整村落总图。','有道路、街角、沿街设施，也有待建设地块。','乡村布局另作建议，不将视频当实测平面。')])
doc+='<details><summary>自建房原视频章节表</summary>'+table(['章节','时间'],chapters)+'</details></section>'
doc+='''<section id="region"><div class="eyebrow">02 / SPATIAL ASSEMBLY</div><h2>“一小片乡村”的感觉，需要房子之间的关系。</h2><p>建议先做少量互有差异的宅地：靠村路的一侧有门前硬地、停车或小卖部，内部支巷连接更安静的入口；菜地、树荫和晒场占据有用途的留空。先建立两三种可用平面，再改变层数、阳台、屋顶和墙材。数量与尺度仍待正式设计确定。</p>'''+svg_image(village,'P01 / 建议的拓扑草案。非真实村落、非视频截图、无测量尺度，也不是已完成的建设方案。')+'''<p>对照“小香港”，同一批设备和细件可以进入另一套组织：底层界面更连续，街角更明确，招牌沿商铺而非随机分布，高低楼体形成层叠。两种区域共用构件，使用密度与放置条件分别配置。</p>'''+svg_image(urban,'P02 / 根据成品关系归纳的沿街组合示意；不代表原作者的施工方法。')+'''<p class="banner"><strong>区域层决定场所，楼栋层决定身份，住户层决定变化。</strong><br>墙面近色穿插属于更细的一层，不能替代前面三层设计。</p></section>'''
doc+='<section id="components"><div class="eyebrow">03 / COMPONENT CATALOG</div><h2>27 个参考条目，保留来源与状态。</h2><p>C01–C15 沿用上一版；C16–C27 为本轮新增。所有 consumer 仍为空，表示尚无自动生成适配器消费这些新规则。</p><div class="filter"><input id="search" aria-label="搜索构件" placeholder="搜索：乡村、厚窗、空调、转角…"><select id="zone" aria-label="按区域筛选"><option value="">所有区域</option>'+''.join('<option>'+z+'</option>' for z in sorted(set(c['zone'] for c in d['components'])))+'</select><span id="count" aria-live="polite">27 个条目</span></div><div id="cards" class="grid">'+cards+'</div></section>'
sample_rows=[]
for m in d['sample_manifest']:
 a='<a download="'+m['file']+'" href="'+urlbytes(R/'samples'/m['file'],'application/octet-stream')+'">下载 NBT</a>'
 sample_rows.append((m['id']+' '+e(m['label']),' × '.join(map(str,m['size_xyz'])),str(m['blocks'])+' / '+str(m['states']),e(str(m['source_bbox_xyz_exclusive'])),a))
doc+='<section id="samples"><div class="eyebrow">04 / EXISTING NBT REFERENCES</div><h2>jiejao 的三个原样片段继续保留。</h2><p>本轮没有从新视频虚构或冒充下载新的 NBT。下列三个文件与 0.1 版字节相同；原方块状态、回读结果与验证边界不变。</p>'+table(['片段','X/Y/Z 尺寸','方块 / 状态','原文件范围，高端不含','文件'],sample_rows)+'<div class="gallery">'+picture('overview','jiejao 原文件回读。模型图无真实材质纹理，部分几何为近似。')+picture('plan_y12','Y≤12 的平面剖切：可观察部分隔片，不能认定完整功能内饰。')+picture('mast','天线状杆架的原上下文；实际摘录只取表中范围。')+picture('equipment','附墙设备盒的原上下文；梯子/拉杆在预览中使用盒形近似。')+'</div><p class="notice">NBT 参考片段需要对应承托或墙面。空气格未写入；旋转、邻接更新、实际碰撞与游戏内外观仍为待验证。</p></section>'
doc+='<section id="reuse"><div class="eyebrow">05 / RULES & NEXT STEP</div><h2>预制的是接口与组合关系。</h2><div class="grid">'+''.join('<article class="card"><div class="eyebrow">'+r['id']+'</div><h3>'+r['rule']+'</h3><p>'+r['detail']+'</p></article>' for r in d['rules'])+'</div><h3>下一轮优先顺序</h3><ol>'+''.join('<li>'+x+'</li>' for x in d['next_validation'])+'</ol><button id="downloadCatalog">下载累计目录 JSON</button> <button id="downloadTemplate">下载新来源模板</button><details><summary>模块应记录的接口字段</summary>'+table(['字段','职责'],[(e(k),e(v)) for k,v in d['placement_contract'].items()])+'</details></section>'
doc+='<section id="evidence"><div class="eyebrow">06 / EVIDENCE INDEX</div><h2>每项结论能回到时间或坐标。</h2><p>本轮观看的是关键施工段和成品帧，没有逐字转录字幕，没有保存或转载视频截图。下面分别保留观察和推断边界。</p>'
for prefix,title in [('V02','自建房 V02 · 本轮新增'),('V03','小香港 #01 V03 · 本轮新增'),('V01','广东城中村 V01 · 既有'),('J','jiejao · 既有实物回读')]:
 oo=[o for o in d['observations'] if o['id'].startswith(prefix)]
 doc+='<details'+(' open' if prefix in ['V02','V03'] else '')+'><summary>'+title+'</summary>'+table(['证据','时间/坐标','观察','边界'],[(e(o['id']),e(o['at']),e(o['observation']),e(o['limit'])) for o in oo])+'</details>'
doc+='<p>其他来源：<a href="'+d['source']['video']['url']+'">广东城中村原视频</a> · <a href="[maintainer archive reference]">jiejao.nbt 原文件</a></p><p><code>jiejao SHA256 '+d['source']['nbt']['sha256']+'</code></p><details><summary>实现、权限与显示边界</summary><p>新视频没有提供给本轮可用的原始模型。构件条目是研究配方，不宣称已支持新方块、任意旋转或邻接。苍白橡木等材料需要核对目标版本及引擎词表；不得静默替换后声称原样复刻。</p><p>视频灯光和镜头效果可能受光影/材质影响，原版外观需另测。数据保存不等于神经网络训练或已安装 skill 更新。本轮未改变旧住宅、其约70%亮灯偏好及近色单块穿插要求。</p></details></section></main><footer>HAF Reference Library 0.2 · 三条视频与一个 NBT 来源。<br>旧版快照、累计数据、示意图和三个 NBT 参考片段均包含在资料包中。</footer>'
doc+='<script id="catalog-data" type="application/json">'+json.dumps(d,ensure_ascii=False).replace('</',r'<\/')+'</script><script id="template-data" type="application/json">'+(R/'data/next_source_template.json').read_text()+'</script>'
js=re.findall(r'<script>(.*?)</script>',previous_html,re.S)[-1]
doc+='<script>'+js+'</script></body></html>'
(R/'HAF_Exterior_Library.html').write_text(doc)
(R/'README.txt').write_text('''HAF 构件与区域研究库 0.2 · 2026-10-28

打开 HAF_Exterior_Library.html 可离线阅读。data/catalog.json 是累计数据：3条视频、jiejao原模型资料、27构件条目、15规则、3个已有NBT片段、2种区域关系推演。

本轮增加农村自建房预制教程与小香港#01研究。新增做法均为研究配方，没有声称新视频提供了NBT或已经接入HAF引擎。没有新建整片村落/城市，也没有修改旧住宅和已安装skill。

history 保留0.1研究页与目录，samples保留0.1的三个实物摘录，方块状态与字节均不变。关于摘录与回读见样本manifest及tools/extract_samples.py。游戏、旋转和邻接验证仍待进行。

diagrams 是本轮提出的关系图，无尺度，不是原视频平面或建造图。previews 是此前jiejao的无纹理诊断图，并非游戏截图。未保存/转载新视频截图。视频的关键帧/章节记录见目录，不是逐秒完整转录。

tools/extend_catalog_v02.py 可以从 history/catalog_v01.json 和已有图片/样本重新生成0.2研究页、目录与关系图；ZIP需另行打包。不要运行旧版 build_catalog.py 来写0.2文件，旧生成脚本仅为历史源代码。
''')
(R/'tools/report_ui.js').write_text(js)
print(json.dumps({'components':len(d['components']),'observations':len(d['observations']),'rules':len(d['rules']),'sample_count':len(d['sample_manifest']),'html_bytes':len(doc.encode())},ensure_ascii=False))
