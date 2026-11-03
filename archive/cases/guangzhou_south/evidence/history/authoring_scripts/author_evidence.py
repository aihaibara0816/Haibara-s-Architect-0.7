from pathlib import Path
import json,hashlib
P=Path(__file__).parent/'HAF_Guangzhou_South';C=P/'cases/guangzhou_south';R=C/'research'
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
observations={
'F01':'设计效果图：总体屋盖与广场关系；不可作为竣工照片。',
'F02':'实景：站台、列车、白色分叉支撑及较薄的金属雨棚。',
'F03':'实景：候车厅座椅分区、主跨拱形桁架、条状吊顶与顶部采光。',
'F04':'实景：地面到达层 Y 形柱、条状吊顶与规律点灯。',
'F05':'实景：轨道侧低角度轮廓、外伸屋盖与玻璃入口。',
'F06':'实景：中央采光带、斜网格、两侧服务盒子与净空。',
'D01':'设计剖面：屋盖—候车层—轨道/站台—地面到达层。',
'D02':'东西立面设计图：14 个 32m 轴距，共448m；雨棚另有外伸，不把轴线长度等同完整屋盖包络。',
'D03':'南北立面设计图：六跨屋盖，边跨非等宽，中间四跨68m。',
'D04':'概念总平面：两侧广场与城市轴线；不作为现状绿化测绘。',
'D05':'纵剖设计图：主厅与外侧低雨棚、交通层次；地下层不纳入本次。',
'S01':'实景：ETFE 采光脊、入口加宽、斜向格构。',
'S02':'实景：到达大厅 Y 柱与规则灯位。',
'A01':'日间斜航拍：六跨雨棚前后错落、较高的中段候车屋盖及大面积镂空支撑。非正射俯视。',
'N01':'夜间斜航拍：跨间高侧窗冷白光、站台连续照明与周边暖色路灯。非正射俯视。',
'N02':'夜间入口实景：玻璃立面、明亮入口与小尺度金色站名。具体入口朝向待核实。',
'N03':'夜间站台：白色分叉支撑、站台标识、楼梯与雨棚下规律照明。',
'R01':'屋顶实景：膜结构曲边与金属屋面连接。',
'R02':'屋顶实景：ETFE 膜枕与节点细部。',
'R03':'屋顶实景：中央采光脊和两侧拱形金属屋面关系。',
'R04':'屋顶实景：斜向膜枕、细密金属立缝、边缘接缝。',
'R05':'接触表复核：屋面维护人员；重复细节，未独立用于几何。',
'R06':'接触表复核：膜枕接缝；重复细节，未独立用于几何。',
'R07':'接触表复核：膜枕维护；重复细节，未独立用于几何。',
'R08':'屋顶实景：长条中央采光带，左右连接至金属拱壳。',
'R09':'接触表复核：屋面走道与玻璃；未独立用于几何。',
'R10':'接触表复核：玻璃维护节点；未独立用于几何。'}
rows=json.loads((R/'downloads.json').read_text());deferred={'R05','R06','R07','R09','R10'}
for q in rows:
 id=q['image_id'];q.update(observation=observations[id],review_status='contact_sheet_reviewed' if id in deferred else 'full_image_viewed',adopted=id not in deferred,orientation='unresolved unless explicitly labeled on published drawing',uncertainty='No automatic camera calibration or pixel-to-metre measurement',original_bytes_preserved=True)
 q['role']='design_render' if id=='F01' else 'concept_masterplan' if id=='D04' else 'published_design_drawing' if id.startswith('D') else 'roof_detail_photo' if id.startswith('R') else 'photograph'
 q['status']=q.pop('review_status')
 if id=='N03':q.update(author='Shujianyang',photo_date='2024-06-15',license='CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',modifications='none')
 assert hashlib.sha256((R/q['local_file']).read_bytes()).hexdigest()==q['sha256']
dump(R/'image_manifest.json',rows)
sources=[
{'id':'architect','url':'https://farrells.com/project/guangzhou-south-railway-station/','title':'Farrells — Guangzhou South Railway Station','type':'architect','adopt':'三层交通组织、中央大厅及屋盖/入口关系','caution':'28 intercity platforms 的用词与运营轨道/站台口径不同，不直接当28座站台'},
{'id':'engineer','url':'https://www.sbp.de/en/project/guangzhou-south-railway-station/','title':'sbp — Guangzhou South Railway Station','type':'structural_engineer','adopt':'金属/玻璃/ETFE 曲壳与拉杆；跨度与总体尺度参考','caution':'450×400×40m、26轨等可能对应工程阶段/统计范围；不与运营28轨平均'},
{'id':'drawings','url':'https://www.archdaily.com/267849/guangzhou-south-railway-station-tfp-farrells','title':'ArchDaily — architect-provided project text and drawings','type':'architect_provided','adopt':'六跨不等宽、68m中跨、层次、中央两端加宽采光带；设计图轴线','caution':'中央采光带文字348m与本版含端部入口雨棚的442格包络并非已校准等值；本版保留尺度误差待复核'},
{'id':'operation','url':'https://m.thepaper.cn/newsDetail_forward_32277378','title':'广州铁路 2025-12-29 运营资料','type':'operator','adopt':'28轨道口径与主站体约450m','caution':'主站体/轴线/外伸雨棚/场景边界分开记录'},
{'id':'entry_levels','url':'https://m.thepaper.cn/baijiahao_15266147','title':'广州铁路 2021 进站指南','type':'operator','adopt':'西侧三层、东侧二层落客与进站，不做成同高'},
{'id':'maintenance','url':'https://huacheng.gz-cmc.com/pages/2022/04/20/2e8c89aa86f34bc5971944cc2b5ae620.html','title':'2022-04-20 广州南站屋面维护报道','type':'on_site_reporting','adopt':'铝镁锰屋面、玻璃与ETFE分区；47–52m维护位置仅作高度参照','caution':'11万平方米屋面与其他20万平方米口径不同，不平均'},
{'id':'aerial_day','url':'https://m.winshang.com/news684460.html','title':'2021 广州南站日间斜航拍','type':'secondary_photo','adopt':'竣工轮廓、错落雨棚与外露支撑；不把斜航拍当正射平面'},
{'id':'aerial_night','url':'https://finance.sina.cn/2022-11-30/detail-imqqsmrp8121832.d.html','title':'2022 广州南站夜间斜航拍','type':'secondary_photo','adopt':'高侧窗与站台冷白、道路暖光的分区'},
{'id':'night_platform','url':'https://commons.wikimedia.org/wiki/File:Guangzhou_South_Railway_Station_platform_at_night.jpg','title':'Shujianyang, platform at night, 2024-06-15','type':'photographer_original','license':'CC BY-SA 4.0','adopt':'站台下部结构、吊顶、灯具与标识'}]
dump(R/'sources.json',sources)
def ev(id,refs,region,decision,params,confidence,limits):return dict(component_id=id,evidence_ids=refs,image_region_description=region,decision=decision,parameter_paths=params,consumer='src/build_case.py',confidence=confidence,limits=limits)
evidence=[
ev('roof.bay*',['D02','D03','A01','N01'],'立面屋盖及航拍整片屋面','六个不等宽拱跨；主厅较高，两侧站台雨棚下降且端部错落',['roof_bay_edges_x','roof_north_ends_z','roof_south_ends_z','roof_main_edge_y','roof_main_rise','roof_outer_edge_y'],'medium','竣工端头的具体伸出量与曲率仍为估算'),
ev('roof.spine',['F06','S01','R04','R08'],'中央长条采光带及两端入口','窄中段、加宽端头；白玻璃替代ETFE，石英斜格构',['skylight'],'medium','1m方块的斜格较粗；348m文字长度与含端头包络未闭合'),
ev('roof.*.truss*',['F02','F03','N03','D01'],'檐下白色V叉支撑与弧形弦杆','石英主杆、铁栏杆细弦杆，保持壳下空气',['roof_bay_edges_x','platform_y','departure_y'],'medium','柱位迁就规整站台；非结构计算'),
ev('roof.*.soffit*',['F03','N03','R04'],'候车及雨棚下条状吊顶','活板门条板、拱形主杆、玻璃和金属壳分层',['roof_main_edge_y'],'medium','固定条板间距为Minecraft近似'),
ev('rail.*',['F02','N03','D01'],'站台层、双轨间岛式站台','28装饰轨道通道/15站台体，位于候车厅下方',['track_layout','rail_y','platform_y'],'medium','轨距、站台间距规整；链条轨道和列车均不能运行'),
ev('arrivals.*',['F04','S02','D01'],'地面到达大厅','Y形柱、局部吊顶和有序点灯',['ground_y','rail_y'],'medium','只做主要公共空间，非完整功能流线'),
ev('entrance.*',['D02','F05','N02'],'两侧玻璃大厅与落客平台','西侧三层/东侧二层；门洞切穿玻璃及外竖杆',['departure_y','platform_y','glazing_material'],'medium','道路曲线、实际门洞数量与位置估算；入口层级采用官方文字'),
ev('interior.seating.*',['F03','F06'],'主厅两侧座椅与中轴通道','规则座位岛保留中轴，服务盒子少量暖光',['departure_y','lighting.warm_commercial_activity'],'medium-low','数量、服务台样式为可调整补充'),
ev('lighting.*',['N01','N02','N03'],'高侧窗、入口与站台','公共区域规则冷白；道路与小商铺暖光；随机仅限商业活跃度',['lighting'],'medium','预览暖冷是材质渲染；原版实际光色由游戏/光影决定'),
ev('site.*',['A01','D04'],'两侧广场边缘及概念总图','有限范围的铺装、树阵与花坛',['scope.include'],'low','非完整现状测绘，未还原周边TOD与地下区域')]
dump(R/'component_evidence.json',{'schema':'haf-component-evidence-1','image_count':len(rows),'full_image_reviewed':sum(q['status']=='full_image_viewed' for q in rows),'method':'manual image/drawing interpretation, parameterized case adapter; no ML training','model_research':{'input':None,'route':'pure image and drawing route'},'components':evidence,'research_gaps':['入口雨棚包络与348m文字尺寸对齐','实测屋面端头曲线与平面坐标','东西广场现状铺装/绿化测绘','游戏内门/楼梯/栏杆碰撞及照明更新'],'stop_reason':'V1可检查主形、交通层次、屋盖与下部结构；场地和隐藏构造仍保留估算'} )
dump(C/'history/iterations.json',[{'run':'V1_r01','status':'superseded','result':'16/17 checks; facade mullions blocked center door at west x111 and east x510','preview':'overview/top/hall reviewed'},{'run':'V1_r02','change':'Cut entrance glass and external mullion layers together; wire roof_outer_edge_y to wing geometry','status':'candidate_delivery'}])
dump(C/'feedback.json',{'case':'guangzhou_south','run':'V1_r02','user_acceptance':'pending','instructions':'请按构件记录看到的问题、视角/图片、期望变化；先改参数或局部几何，新建run，不覆盖旧版。','items':[{'component':x,'view':'','observation':'','desired_change':'','priority':'pending','status':'awaiting_user'} for x in ['roof.bay*','roof.spine','roof.*.truss*','facade','interior','lighting','entrance','site']]})
dump(P/'learning/guangzhou_south_v1.json',{'engine':'HAF 0.2.0','release_role':'user-requested final 0.2 case; not a 0.3 release','lessons':['六跨不能复制成六个等宽桶；图纸轴线与完整雨棚外缘分别核对','斜航拍不能当正射俯视；输出模型正投影俯视用于轮廓检查','铁路站房按到达/轨道/候车层解释，公共灯光模式不同于办公楼随机亮窗','洞口必须同时切开玻璃、竖杆和横杆','屋面壳、吊顶、桁架分别构建，保留真实空气层','尺寸口径冲突保留证据与未闭合项，不用取平均值遮蔽差异'],'not_claimed':['automatic model fusion','universal station generator','functional railway','in-game verification','neural training'],'next_acceptance':['user shape/detail review','game import and updates','correct dimensions of central skylight and plaza']})
print('evidence',len(rows),'references;',len(evidence),'component groups')
