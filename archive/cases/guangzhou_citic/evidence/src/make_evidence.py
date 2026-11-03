from pathlib import Path
import json,hashlib
C=Path(__file__).resolve().parents[1];old=json.loads((C/'input/packet.json').read_text());downloads=json.loads((C/'input/new_downloads.json').read_text());rows=[]
ids=['img-cp-01','img-cp-18','img-cp-19','img-cp-17','img-cp-04','img-cp-22']
for i,iid in enumerate(ids,1):
 r=next(x for x in old['images'] if x['image_id']==iid)
 rows.append({'id':iid,'file':f'ref_{i:02d}.jpg','page_url':r['page_url'],'image_url':r['direct_image_url'],'source':r['source_ids'][0],
  'use':['全高、塔冠与主塔纵向比例','侧面网格、裙楼相对高度','相反斜向、玻璃色带与竖向分区','黑色入口门框及立面细分','弧形大厅、椭圆雨棚与浅池','入口前场、植物及水景'][i-1],
  'status':'adopted','face':'oblique' if i in [2,3,4] else 'front','orientation':'照片局部视向；未独立校准地理朝向','layer':'outer','occlusion':'partial',
  'limits':'透视照片不可直接读绝对尺寸；拍摄时期与当前现场可能不同','licence':'权利状态未知；来源保留，不作为训练授权','viewed_on':'2026-10-27'})
use={
 'dln_lobby.jpg':('DLN','挑空门厅、石材地面、内嵌吊顶','interior'),
 'dln_complex.jpg':('DLN','弧形商业裙楼与折转公寓翼；下部架空','oblique'),
 'dln_detail_a.jpg':('DLN','裙楼弧墙、青玻璃、棕榈、轻薄雨棚','oblique'),
 'dln_detail_c.jpg':('DLN','架空洞口、雨棚底面金属肋及行人通道','oblique'),
 'night_crown.jpg':('张工不在工位 / Bilibili 视频封面','双尖杆、楼顶中信招牌、四角屋顶及中部凹槽','oblique'),
 'complex_aerial.png':('搜狐地产文章图片','远距离正面轮廓、双杆与招牌；并非真正俯视图','front')}
for f,(pub,why,face) in use.items():
 d=next(x for x in downloads if x['file']==f)
 page='https://www.dln.com.hk/en/project/commercial/CITIC-Plaza' if pub=='DLN' else 'https://www.bilibili.com/video/BV1bv41147MM/' if f=='night_crown.jpg' else 'https://www.sohu.com/a/588962505_121484367'
 rows.append({'id':f.split('.')[0],'file':f,'page_url':page,'image_url':d['url'],'source':pub,'use':why,'status':'adopted','face':face,'orientation':'局部观察，未恢复相机','layer':'inner' if face=='interior' else 'outer','occlusion':'partial','viewed_on':'2026-10-27','limits':'视频仅看封面，未观看完整视频' if f=='night_crown.jpg' else '照片年代/绝对尺度未核；用来约束可见构件','licence':'权利状态未知；来源保留，不作为训练授权'})
for r in rows:r['sha256']=hashlib.sha256((C/'input/images'/r['file']).read_bytes()).hexdigest()
e={'case':'广州天河北中信广场','retrieved':'2026-10-27','images':rows,
 'sources':[{'url':'https://www.skyscrapercenter.com/building/citic-plaza/242','publisher':'CVU / CTBUH','observed':'390.2 m 含尖杆、80层、办公用途','status':'accessed'},
 {'url':'https://www.dln.com.hk/en/project/commercial/CITIC-Plaza','publisher':'DLN','observed':'项目身份与原始建筑图库；本案例采用其中6张照片','status':'accessed'},
 {'url':'https://api.openstreetmap.org/api/0.6/map?bbox=113.3177,23.1430,113.3208,23.1460','publisher':'OpenStreetMap contributors','observed':'实际API XML；地图几何用于建筑位置和轮廓','status':'downloaded','licence':'ODbL 1.0; https://www.openstreetmap.org/copyright'}],
 'rejected':[{'file':'office_plan.jpg','url':next(x['url'] for x in downloads if x['file']=='office_plan.jpg'),'reason':'图片聚合检索结果无可核建筑身份；不对称圆角平面与本楼圈方体块不吻合。未用作主塔平面。'},
 {'url':'https://www.scstnt.com/caseinfo.aspx?cid=36&t=20','reason':'检索标题与项目描述混入上海北外滩楼，身份冲突，未采用'},
 {'url':'https://www.media-facade.net/news_Media-Facade-Lights-Up-CITIC-Plaza-Urban-Light-Show-Embraces-National-Games-in-Guangzhou_148.html','reason':'节庆灯光场景，不作为日常办公室开灯比例依据'}],
 'decisions':[
 {'component':'tower','evidence':['img-cp-01','img-cp-17','OSM way 926228208'],'decision':'保留直立瘦长体量，地图平面统一7/15缩尺；不从面积开方猜边长','confidence':'medium'},
 {'component':'crown','evidence':['night_crown','img-cp-01','OSM parts 1548063152-3165'],'decision':'方形翼体叠圆筒、凹槽、横杆、双尖杆和中间招牌分别构造','confidence':'medium; upper heights community estimates'},
 {'component':'podium_annex','evidence':['dln_complex','dln_detail_c','OSM ways 157418073/082/084'],'decision':'弧形裙楼及折转两翼同坐标建造，主塔南侧/裙楼北侧关系由地图决定','confidence':'medium; annex height approximate'},
 {'component':'facade','evidence':['img-cp-17','img-cp-18','img-cp-19'],'decision':'蓝青玻璃分区；细链横框、铁栏竖框和窗后层，减少整面玻璃盒观感','confidence':'photographic pattern, voxel abstraction'},
 {'component':'lobby','evidence':['img-cp-04','dln_lobby'],'decision':'高门框、弧面玻璃、椭圆雨棚、石材地面；接待/等候家具为设计补全','confidence':'mixed'},
 {'component':'office_interior','evidence':['HAF0.4 office catalogue','user interior/light preferences'],'decision':'四个示范标高含办公、项目协作、休息与大厅；非真实租户平面','confidence':'synthetic'},
 {'component':'landscape','evidence':['img-cp-22','dln_detail_a','img-cp-04'],'decision':'连续植床、树荫座椅、棕榈和浅池保留入口轴线；位置与尺寸为补全','confidence':'motifs observed, layout designed'}],
 'reference_box':{'eight_corner_bounds_done':True,'photo_camera_recovery_done':False,'method':'same-coordinate geometric bounding cuboid and manual multi-view component evidence; not inferred 3D from pixels','bounds_xyz':[33,3,53,56,185,76]},
 'uncertainties':['未获取测绘图或原始SKP/GLB模型','OSM仅社区地图；平面可能有偏差，尺寸非测量证明','屋顶321.9 m、圆筒310.8 m仅OSM估计；与官方总高分开','塔冠中缝宽度、薄幕墙细框仍受方块分辨率限制','公寓高度约135 m、裙楼约23 m为图像约束估计','避难/设备暗带按外观估计，非27/47/67层精准定位','南北入口照片对应未完成独立测绘校准','办公示范层不能视为80个真实可进入楼层；静态电梯不提供楼层交通','未验证Java游戏导入、真实碰撞、真实光照和资源包纹理']}
(C/'input/evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2));print(len(rows),'adopted images')
