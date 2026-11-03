"""Reproducible V2 parameter/evidence decisions; never mutate V1 parameters."""
from pathlib import Path
import json, shutil, hashlib
CASE=Path(__file__).resolve().parents[1]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
p=json.loads((CASE/'params.json').read_text())
p['case_version']='0.2.0'
p['identity']['user_location_conflict']='沿用用户标注照片所示花城大道83号新海关；非沿江旧海关'
p['tower']['central_rect']=[50,44,77,76]
p['tower']['main_rect']=[25,45,102,74]
p['crown']['clock_center_xz']=[63,64]
p['podium']['glass_pavilions']=[[24,29,43,40],[61,29,80,40]]
p['podium']['roof_tinted_regions']=[[92,17,112,39],[15,29,88,43]]
p['podium']['side_arcades']['note']='V2不消费此V1字段；由v2.side_portal替代，保留以对照历史'
p['v2']={
 'podium_masses':[[13,43,114,87],[90,16,114,43],[13,27,90,43],[10,44,13,82]],
 'tower_masses':[[25,45,38,74],[38,54,50,71],[77,54,89,71],[89,45,102,74]],
 'upper_center_rect':[50,52,77,76],
 'rear_window_bands':[{'xs':[29,34,93,98],'z':45},{'xs':[41,46,80,85],'z':54},{'xs':[53,58,63,68,73],'z':44}],
 'side_window_zs':[49,54,59,64,69],
 'side_portal':{'wall_x':10,'span_z':[44,82],'centres_z':[50,62,74],'confidence':'中：img-nc-11侧后拱门与img-nc-13普通侧墙互为不同侧，映射模型-X与+X；绝对地理方位未测绘'},
 'podium_window_segments':[
  {'id':'left_side','normal':[-1,0],'wall':13,'centres':[32,38]},
  {'id':'right_side','normal':[1,0],'wall':113,'centres':list(range(29,80,6))},
  {'id':'projecting_rear_wing','normal':[0,-1],'wall':16,'centres':[95,101,107]},
  {'id':'recessed_rear_wall','normal':[0,-1],'wall':27,'centres':[19,25,31,37,52,58,64,70,76,82,87]},
  {'id':'notch_return','normal':[-1,0],'wall':90,'centres':[21,25]}],
 'dimension_status':'block hypotheses from multiple views; not measured ratios',
 'geometry_intent':'先按构件形成明确进退；中央上段与下段分开，避免V1通高长条；入口与普通窗墙分开'
}
p['estimates']=[
 '137格总高保持V1对照条件；103/114/137米资料冲突尚未解决，非精确1:1',
 '中央下段27×32格、上段27×24格、钟室13×13格；为多视角解释后的可调假设，非透视图直接测量',
 '上段进深48→24格；下段48→32格；不是将照片里投影宽度强制等同实体尺寸',
 '侧后拱门、退入墙、外挑翼关系有照片支持；精确方位和尺寸仍待实测/清晰平面核对',
 '卫星影像与OSM轮廓已检查，但高楼倾倒、遮挡及轮廓口径不一致；未据此宣称获得屋顶测绘图',
 '未见处围护按连续性补齐；伪内饰和固定种子暖冷混合灯光为游戏设计',
 '无同楼可靠夜景证据；无SKP/其他模型；未进行Minecraft客户端验证'
]
dump(CASE/'params_v2.json',p)
components=[
 ('central_mass',['img-nc-11','img-nc-13','user-feedback-032226'],'长条中央体令钟冠显得过小','下段27×32、上段27×24；钟室移至新上段中心，新增21→19→17阶梯底座',['tower.central_rect','v2.upper_center_rect','crown.clock_center_xz'],'masks / shell_and_floors / crown','中：进退可靠，尺寸待核'),
 ('front_facade',['img-nc-04','img-nc-07','img-nc-08'],'不能因侧面过宽而误缩正面多组窗列','保留正面77格总宽、中央五列细窗与两侧分组；加深后侧凹槽',['v2.tower_masses','v2.rear_window_bands'],'masks / tower_facades','中高：正面；中：背面'),
 ('upper_band',['img-nc-11','img-nc-13','user-feedback-031839'],'V1横带仅前方短线，侧后断失','94格标高绕各翼连续横带；103/112格两级檐口',['v2.tower_masses'],'shell_and_floors','中高'),
 ('podium_massing',['img-nc-11','img-nc-13','user-feedback-031839'],'单矩形基座不能表达突出翼与内退墙','四个体块组合；后侧留11格进退；独立屋顶玻璃亭',['v2.podium_masses','podium.glass_pavilions'],'masks / podium','中低：缺可靠平面'),
 ('side_portal',['img-nc-11','img-nc-13','user-feedback-031839'],'普通窗墙、拱门与台阶混在错误连续立面','模型-X侧独立三拱门与外凸门廊、宽台阶；+X侧普通窗格；后侧内退墙与外挑翼',['v2.side_portal','v2.podium_window_segments'],'podium','中：相对侧向关系；地理方向待核'),
 ('front_colonnade',['img-nc-02','img-nc-03','img-nc-04','img-nc-05','img-nc-12'],'V1只有中央四柱，遗漏整排侧柱与通高空间','中央成对柱保留；两侧连续柱廊、退后玻璃、上层小拱窗、栏杆',['entrance'],'entrance','高：可见结构；柱数与半格表达近似'),
 ('door_soffit',['img-nc-02','img-nc-04','img-nc-12'],'入口门框/吊顶层次少','内缩门厅、半砖吊顶格栅、细铁框圆形纹样代理',['entrance'],'entrance','中：小尺度抽象'),
 ('roof_finish',['img-nc-11'],'绿灰屋面误当统一铺草','限制绿色表面范围，区分灰屋面和两座深玻璃亭',['podium.roof_tinted_regions','podium.glass_pavilions'],'podium','中；不认定具体屋面用途/材料'),
 ('interior_lighting',[],'不能用亮灯数量代替还原','保留V1种子、占用规则、暖冷比例，按新几何重排合格房间',['lighting'],'interiors (V1 shared)','游戏方案，真实室内和夜景待核')
]
dump(CASE/'research/v2/component_decisions.json',{'research_policy':'不限照片；按有效构件覆盖，重复照与细节裁切不计新方向','photos_reviewed':11,'photos_new_to_v1_use':7,'independent_view_count':'不作11个独立方向的承诺；02/12近重复，03/05遮挡严重','rows':[dict(zip(['component_id','evidence','problem','decision','parameters','consumer','confidence'],r)) for r in components],'remaining_gaps':p['estimates'],'visual_status':'awaiting_v2_render_review','model_training':False})
recs=json.loads((CASE/'research/v2/downloads.json').read_text())
uses={'img-nc-01':'旧正面低清佐证','img-nc-02':'入口/柱廊/门/吊顶主要证据','img-nc-03':'近景补充，遮挡严重','img-nc-04':'正面全楼/柱廊主要证据','img-nc-05':'近景尺度佐证，遮挡严重','img-nc-06':'历史低清斜前体块佐证','img-nc-07':'正面塔身窗列','img-nc-08':'正面分段与比例','img-nc-11':'侧后体块/裙楼/凹槽/拱门主要证据','img-nc-12':'02近重复，仅细节核对'}
for r in recs:
 r['viewed_v2']=True;r['adoption']=uses[r['image_id']];r['near_duplicate_group']='2024-front-entrance' if r['image_id'] in ('img-nc-02','img-nc-12') else None
src=CASE.parents[2]/'ctbuh.jpg'
dst=CASE/'research/v2/images/img-nc-13.jpg'
if src.exists():shutil.copy2(src,dst)
elif not dst.exists():raise FileNotFoundError('Fetch img-nc-13 with research_v2.py before preparing V2')
recs=[r for r in recs if r['image_id']!='img-nc-13']
recs.append({'image_id':'img-nc-13','source_page_url':'https://www.skyscrapercenter.com/building/guangzhou-customs-building/23892','direct_image_url':'https://s3.amazonaws.com/images.skyscrapercenter.com/thumbs/54163_500x650.jpg','local_path':str(dst.relative_to(CASE)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'actual_pixels':[500,650],'viewed_v2':True,'adoption':'新侧面证据：5组窄窗、上部环带、柱廊与侧墙区别','attribution':'© Tansri Muliani / CTBUH; source-linked reference study','license':'非开放许可，原网页版权保留'})
dump(CASE/'research/v2/image_manifest.json',recs)
dump(CASE/'research/v2/top_evidence_status.json',{'osm_way':313905695,'osm_source':'https://www.openstreetmap.org/way/313905695','osm_attribution':'© OpenStreetMap contributors, ODbL','osm_use':'地址和粗轮廓候选；不直接当塔楼轮廓','imagery_service':'https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer','imagery_attribution':'Esri, Vantor, Earthstar Geographics, GIS User Community','imagery_use':'查看9张L18邻接切片组成一次区域观察；不计9张建筑参考图，不作尺寸基准','limitations':'强烈高楼倾倒、遮挡、影像与轮廓口径不明；未确认可靠屋顶正投影','top_render_required':True,'plan_sections_required':[25,65,110],'measured_roof_plan_obtained':False})
config=json.loads((CASE.parents[1]/'agent_config.json').read_text());config['cases']['guangzhou_customs']='cases/guangzhou_customs/src/build_v2.py';dump(CASE.parents[1]/'agent_config.json',config)
print('V2 decisions prepared; V1 files untouched')

