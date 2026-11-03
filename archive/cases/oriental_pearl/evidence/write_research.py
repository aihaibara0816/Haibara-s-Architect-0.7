from pathlib import Path
import json,hashlib,sys
from PIL import Image
C=Path(__file__).parent;D=C/'research';DAY='2026-10-26'
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
base='https://commons.wikimedia.org/wiki/File:'
rows=[
('01_overall','2008_Shanghai_Oriental_Pearl_Tower.jpg','下球、斜撑与基座','Nicholas Hartmann / Nhartmannphotos','2008-08-04','CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/','低位斜视，方向未核实',['sphere.lower','structure','podium'],'塔顶出框，旧基座不能当作2026竣工总平'),
('02_overhead','20170130从上海中心大厦观景台俯瞰东方明珠电视塔.jpg','高位俯瞰','MasaneMiyaPA','2017-01-30','CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/','上海中心观景台向下斜视',['sphere.upper','structure','podium'],'透视俯瞰而非正交俯视；前景建筑遮住基座，景深有雾'),
('03_northbund','Oriental_Pearl_Tower_view_from_the_North_Bund,_Oct._21st,_2026.jpg','北外滩全塔','Bechology','2026-10-21','CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/','北外滩远景，来源说明拍摄位置',['sphere.lower','sphere.upper','sphere.capsule','structure','mast'],'低层被树木遮挡，不能量测塔脚平面'),
('04_east','20191114_Oriental_Pearl_Tower-1.jpg','主筒与五个中间小球','BalonGreyjoy','2019-11-14','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/','东侧仰视；来源页有拍摄坐标',['sphere.upper','sphere.lower','structure','mast'],'近大远小，塔脚出框，不直接用像素高度推全塔尺度'),
('05_detail','Cleaner_on_Oriental_Pearl_Tower.JPG','球面三角框与银灰壳','Casliber','2006-01-23','CC BY-SA 3.0','https://creativecommons.org/licenses/by-sa/3.0/','球面侧向特写，方位未知',['sphere.lower'],'只覆盖局部，不能证明全塔所有球体同一种构造'),
('06_base','The_Pearl_Tower_(2874763137).jpg','下球底面与窗带','Alan Levine / cogdogblog','2008-09-21','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/','近距离仰视，方位未知',['sphere.lower','structure'],'底面纹理可见，强透视；圆形孔洞未逐个复原'),
('07_nightwest','Oriental_Pearl_Tower_at_night_20260417_(1).jpg','夜间全塔分区','DvTor8303','2026-04-17','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/','黄浦江上远景，来源有拍摄坐标',['lighting','sphere.lower','sphere.upper','mast'],'代表当晚红色模式，不代表永久固定颜色；周边灯光不复制'),
('08_nightclose','Oriental_Pearl_Tower_at_night_20260418_(2).jpg','夜间底面与支柱','DvTor8303','2026-04-18','CC0 1.0','https://creativecommons.org/publicdomain/zero/1.0/','丰和路近距离仰视',['lighting','sphere.lower','structure'],'树木遮挡塔脚；紫红泛光非原版彩色光传播')]
original=json.loads((D/'images/downloads.json').read_text());images=[];sources=[]
for i,row in enumerate(rows,1):
 fn,page,title,author,date,lic,lurl,view,cids,lim=row;f=D/'images'/(fn+'.jpg');sha=hashlib.sha256(f.read_bytes()).hexdigest();size=list(Image.open(f).size);sid='src-photo'+str(i);iid='img-'+str(i).zfill(2)
 sources.append(dict(source_id=sid,type='original_photograph',title=title,url=base+page,accessed_at=DAY,author=author))
 images.append(dict(image_id=iid,title=title,media_type='photo',source_ids=[sid],component_ids=cids,page_url=base+page,image_url=original[i-1]['url'],local_file='images/'+f.name,local_sha256=sha,actual_pixels=size,verification_state='full_image_viewed',checked_at=DAY,built_state='constructed',building_match_confirmed=True,view=view,covers=cids,orientation={'geographic_bearing':None,'basis':view},version='建成建筑，照片日期'+date,photo_date=date,photographer=author,license=lic,license_url=lurl,license_status='public_domain' if lic.startswith('CC0') else 'licensed',training_authorized=False,quality={'eligible':True,'assessment':'已查看原图；对列出的构件有研究价值','limitations':[lim]}))
sources += [
 dict(source_id='src-wfgt',type='member_organization',title='世界塔楼联合会：上海东方明珠广播电视塔',url='https://www.great-towers.com/zh/塔楼/上海东方明珠广播电视塔',accessed_at=DAY),
 dict(source_id='src-paper',type='original_designer_paper',title='江欢成：设计创新对东方明珠和雅加达塔的贡献，中国工程科学1999，1(1):30–35',url='https://www.engineering.org.cn/sscae/CN/1160104412205081051',accessed_at=DAY),
 dict(source_id='src-sketch',type='designer_interview',title='东方明珠设计者江欢成院士：从地标打造到地标更新（清华校友总会转载访谈，含作者手绘结构图）',url='https://www.tsinghua.org.cn/info/1014/37890.htm',accessed_at=DAY),
 dict(source_id='src-archive',type='official_archive',title='上海市档案馆：东方明珠建设历史资料',url='https://www.shda.gov.cn/dawh/csjy/202509/t20250919_75918.html',accessed_at=DAY)]
components=[dict(component_id=id,name=name,fact_ids=[]) for id,name in [('sphere.lower','下球'),('sphere.upper','上球'),('sphere.capsule','太空舱'),('structure','三主筒、斜撑、五小球及横梁'),('mast','天线'),('podium','简化大厅和研究广场'),('lighting','分区照明')]]
facts=[
 dict(fact_id='fact-height',kind='fact',status='verified',field='overall_height',value=468,unit='m',source_ids=['src-wfgt','src-paper'],conflict_group='height-datum',adoption_reason='采用联合会标示总高；原设计论文附图也标468m，正文463.85m注明从天然地坪算起，保留口径差异，不擅自统一'),
 dict(fact_id='fact-natural-height',kind='fact',status='conflicted',field='natural_ground_height',value=463.85,unit='m',source_ids=['src-paper'],conflict_group='height-datum'),
 dict(fact_id='fact-lower',kind='fact',status='verified',field='lower_diameter',value=50,unit='m',source_ids=['src-paper','src-sketch']),
 dict(fact_id='fact-upper',kind='fact',status='verified',field='upper_diameter',value=45,unit='m',source_ids=['src-sketch']),
 dict(fact_id='fact-support',kind='fact',status='verified',field='main_tube_diameter',value=9,unit='m',source_ids=['src-paper','src-sketch']),
 dict(fact_id='fact-joint',kind='fact',status='verified',field='slant_axis_joint',value=93,unit='m',source_ids=['src-paper']),
 dict(fact_id='fact-shell',kind='observation',status='verified',field='spherical_envelope_zones',value='粉色面板、深色窗带和银灰下壳分区；细三角格构与球面叠置',image_ids=['img-05','img-06'],source_ids=[]),
 dict(fact_id='fact-positions',kind='estimate',status='proposed',field='unverified_component_placement',value={'upper_center':272.5,'capsule_center':342,'capsule_diameter':16,'tube_axis_radius':10.4,'small_centers':[136,162,188,214,240]},unit='m',source_ids=['src-sketch'],image_ids=['img-03','img-04'],basis='上球中心采用示意图上缘295与直径45推算；太空舱与中间小球按照片及公开资料线索取研究参数，缺完整实测图，不作为核实尺寸。')]
full='''以上海东方明珠广播电视塔的已建主体为复刻标准，强制使用本包已查看的 img-01 至 img-08（img-01、img-02、img-03、img-04、img-05、img-06、img-07、img-08），不能擅自修改原型设计。采用统一比例 280/600 格每米，总高基准468米，约218格；所有球径、柱径和水平距离同步缩放。场地地面在局部Y=3，包围盒89×223×89格，工作坐标不冒充地理北向。
保留三根分离的竖向主筒、三个斜撑、下球与上球的明显尺度差、五个主筒间的小球及底部三个小球，共十一球。下球直径50米、上球45米、主筒9米有设计者资料支撑；上球中心272.5米、太空舱342米等作为本版研究参数，须保留不确定性。支撑间隙不能填成实心塔杆，横梁连接不能切断通透的竖向节奏。参看img-03全塔和img-04内部构件关系，再用img-01及img-06复核塔脚和球底。
球体采用阶梯球壳。依据img-05、img-06，将粉色与暗玫红实体饰面、独立深灰观景窗带、银灰下壳分区。粉色混凝土与品红陶瓦用于方块化替代；只在窗带用染色玻璃，窗后保留暗色背衬和简化平台。细三角拼缝低于当前尺度表达能力，只保留少量环向铁栅栏收口，不用粗铁栏覆盖整球。上球外露三主筒须收进球壳，天线细段用连续铁栅栏中心线替代，记录局部最小特征适配。
以img-07、img-08记录夜景分区。本版原版光源只提供球缘与柱间辅助照明，不声称复制红紫泛光或完整灯光秀。内部仅作合成观景平台与暗色背衬，不声称真实餐厅、电梯或完整楼层。先验收主体，再做直径约150米的可编辑研究广场：低大厅、三条简短铺装路径、少量低矮绿化、整齐边界，与主体共用坐标和比例。该地景是合理补全，不是2026现状场地测绘；禁止复制周边楼群。
按结构检查点、全玻璃负对照、分层球壳、细杆及接口修正生成独立run，保留旧文件。最后独立读回NBT，验证尺寸、方块状态、天线连续、11球构件记录、塔脚承托和关键空隙；从该NBT生成四个等尺度45度日夜视角、正交俯视、球体近景、仰视和剖切。实际导入Java1.21.1并检查碰撞、材质和照明之前，游戏验收保持pending。'''
short='''复刻上海东方明珠，强制参考img-01、img-02、img-03、img-04、img-05、img-06、img-07、img-08，不能擅自修改原型设计。以280/600格每米统一缩放，保留三主筒、斜撑与十一球；50/45米主球径，粉色实体球面＋独立深色窗带＋银灰下壳。避免全玻璃球和填实柱间空隙；细天线连续、细三角网格暂简化，未知尺寸保留估算标签。主体后完成简洁圆形研究广场、三条接入路径和低矮绿化，未知内饰与地景只作合理补全。输出NBT及同源日夜四面、真俯视和局部，游戏验收待实测。'''
sections=[
'对象是上海陆家嘴的东方明珠广播电视塔。V1以主体结构与球面层次为目标；主体参照2006—2026照片交叉判断，不能把跨年份基座当作一个完整现状模型。保留三筒、三斜撑、上下主球、太空舱、五个中间小球与三个底部小球。',
'联合会总高468m；原设计论文正文463.85m明确从天然地坪起算，附图另标468m。本版保留口径差异。统一s=280/600，468m→218.4格，成品主体约219个占用Y层，含地台223格包围盒。50m下球→23.33格，45m上球→21格；9m筒→4.2格。塔脚平面位置、太空舱尺寸及广场为估算/建议。s=1/0.5/2对应总高468/234/936格，仅比较高度，不编造建筑长宽。',
'设计者手绘图说明三筒与带斜撑空间框架。照片显示粉色球面嵌有细三角框，银灰球底和深色窗带有明确分区。执行时用粉色混凝土/品红陶瓦保实体层次，玻璃只留在观景带，窗后有合成背衬。三角网格尚未复原，环向铁栏只作粗尺度边界。',
'本次取得并逐张查看8张实景原文件：4张主体/结构图、2张球面与底面近景、2张夜景。原设计论文和手绘图作为结构证据，只提供出处与摘要，不随包转载全文。Sketchfab与ModelNet有模型线索，但未取得可用文件，本次没有模型融合。',
'img-03锁定全塔比例；img-04锁定筒间小球和横梁；img-01补斜撑；img-02补高位遮挡关系；img-05、img-06补球面层次；img-07、img-08补夜景分区。没有合格真实正交总平、室内竣工图或完整灯具表。八面参考盒只组织这些观察，不生成深度与尺度。',
full,short,
'交付包围盒89×223×89格，局部地面Y=3。Java1.21.1，DataVersion3955。以结构原点世界Y=64放置时，最高占用约285、排他边界287，小于320；完整包围盒允许原点Y≤97。使用能读此尺寸的NBT导入工具，原版结构方块尺寸限制未实测。稀疏NBT不清空原有地物。大厅和广场、观景平台均属明确标注的简化补全。',
'首轮观察到细天线消失、圆筒原语误带端帽、上球露出主筒顶；后来修正。连接检查又发现天线环四个悬离单元，增加径向连接后重跑。仍缺细三角格构、真实地面入口、彩色泛光、实机碰撞与原版纹理验收。文件检查通过不能当作视觉还原合格。',
'实际顺序：恢复HAF0.3代码→搜集/查看图片和设计者论文→逐构件记录事实/估算→写显式球体和三筒适配器→结构检查点→玻璃负对照/分层壳→修正端帽与细杆→从最终NBT读回→15个固定视角与参数/源代码归档。下一轮先验证无光影原版下的球面局部，再改善三角拼缝与基座。']
template=Path('/root/.codex/skills/remote-skills/skill-6ad26bc8a18081918d5339dd69880ed2/references/packet-v1.1-template.json')
p=json.loads(template.read_text());p.update(packet_id='oriental-pearl-v1-20261026',collected_at=DAY,sources=sources,facts=facts,components=components,images=images)
p['subject'].update(name='东方明珠',aliases=['Oriental Pearl Tower'],city='上海',kind='single',identity_status='confirmed',version='已建主体，多年份图片交叉核对',core_identifiers=['三主筒','斜撑','11球'],boundary='塔体与简化圆形研究广场；不含周边建筑与地下')
p['provenance'].update(user_input='东方明珠',research_status='incomplete')
p['selection'].update(legacy_slots=[],target_image_limit=None,core=[{'image_id':x['image_id'],'purpose':x['title'],'rationale':x['view']} for x in images[:4]],detail_groups=[dict(component_id='sphere.lower',purpose='材质与下壳近景',image_ids=['img-05','img-06']),dict(component_id='lighting',purpose='夜景分区',image_ids=['img-07','img-08'])],views=[dict(image_id=x['image_id'],face='oblique',orientation_basis=x['view'],layer='mixed',occlusion='partial',component_ids=x['component_ids'],duplicate_of=None,sha256=x['local_sha256']) for x in images],coverage_requirements=[dict(face='top',component_id='podium',missing_search='需要现状正交总平或标注尺寸图，斜俯瞰不可代替'),dict(face='interior',component_id='sphere.upper',missing_search='需要带楼层定位的观景廊平面')],consistency_checks=dict(same_version=None,clean_subject=True,orientation_aligned=None,layout_basis_image_ids=['img-02'],podium_closeup_image_ids=['img-01'],shell_crosscheck_image_ids=['img-05','img-06'],notes=['跨年份主塔形态互证；不声明完整同年场地','工作坐标地理朝向未配准']))
p['scale'].update(selected_s=280/600,ratio_candidates=[1,.5,2,280/600],uncertainty=['主体宽深未核实','太空舱、中间小球标高、柱位半径为估算','可建世界余量未知'],local_exaggerations=['细天线不足一格时用一列铁栅栏保证连续；不等于真实截面'])
p['scale']['building_dimensions']['overall_height'].update(value_m=468,fact_id='fact-height',basis='世界塔楼联合会总高口径')
p['prompts'].update(full=full,short=short,image_ids=[x['image_id'] for x in images])
p['guidance'].update(scope='主体+小型研究广场',quality='几何文件pass，视觉细节needs_revision，游戏pending',height='约218格主体',site='简化合理补全',interior='合成观景平台与背衬',lighting='原版白色/暖色照明示意，不声称真实彩色泛光')
p['staging'].update(required=False,reason='单一坐标系的一体结构，保留阶段run；本版不做分块施工',coordinate_system=dict(origin=[44,3,44],x_axis='model X',y_axis='up',z_axis='model Z',north='地理北向未知',s=280/600),stages=[])
for q,c in zip(p['report_sections'],sections):q.update(content=c,source_ids=['src-wfgt','src-paper','src-sketch'],image_ids=[x['image_id'] for x in images])
p['risks']=[dict(risk='球面三角分格被粗网格淹没',symptom='球像网笼或只剩色块',correction='同尺度局部比较细杆/纹理/省略方案'),dict(risk='数据检查被误认为已还原',symptom='把pass当成实景或游戏验收',correction='保留视觉needs_revision和游戏pending')]
p['gaps']=['正交总平缺失','三角格构未实现','室内/电梯未实测','当前场地未完整复原','原版无光影实机未测试','彩色灯光秀未实现']
dump(D/'packet.json',p)
# Stable per-region provenance; normalized rectangles are manual context windows, not segmentation.
regions=[('img-03',[.30,.06,.65,.96],'structure','三筒和上下球的整体比例','structure.tube_axis_radius_m','Pearl.construct','overview / four diagonals'),('img-04',[.38,.35,.63,.74],'structure','五个小球处于两侧主筒间，六道横梁分段','small_spheres.centers_m; structure.beam_levels_m','Pearl.construct','upper_detail + section'),('img-05',[.45,.02,.99,.99],'sphere.lower','细三角框在粉色面板外；下部银灰板有清晰边界','shell_thickness_blocks; sphere.style lower','Pearl.sphere','lower_detail; triangle grid pending'),('img-06',[.01,.02,.98,.96],'sphere.lower','窗带与实体下壳分离，球底穿入主筒','sphere.lower.diameter_m=50','Pearl.sphere + tube','underside / section'),('img-02',[.30,.66,.75,.98],'podium','底部一体空间被前景建筑遮挡','site.radius_m=75 (design suggestion)','Pearl.construct','base_plan; actual plan pending'),('img-07',[.28,.01,.70,.89],'lighting','柱间、球底、天线有不同照明分区','lighting.enabled','Pearl.construct','night views; colour unresolved'),('img-08',[.12,.19,.87,.80],'lighting','下球底面与斜撑被泛光照亮','no colour propagation consumer','research_only','pending')]
dump(D/'evidence_to_geometry.json',[dict(region_id='region-'+str(i+1),image_id=r[0],rect_normalized=r[1],component_id=r[2],observation=r[3],parameter=r[4],consumer=r[5],review=r[6],method='manual context rectangle, not pixel segmentation') for i,r in enumerate(regions)])
dump(D/'images_manifest.json',{'title':'东方明珠 HAF V1 实景参考原图','images':[dict(image_id=x['image_id'],title=x['title'],local_path=str((D/x['local_file']).resolve()),image_url=x['image_url'],source_page_url=x['page_url'],verification_status='原图已查看；'+x['view'],selection_status='selected',photographer=x['photographer'],license=x['license']+' '+x['license_url']) for x in images]})
dump(D/'model_search.json',{'route':'image_only_with_primary_paper','model_acquired':False,'candidates':[{'url':'https://sketchfab.com/3d-models/oriental-pearl-tower-6b4e7f84985b41988dc17a20d4bc0dec','result':'page returned403; no asset retrieved'},{'url':'https://modelnet.cs.princeton.edu/data/antenna/antenna_000000464/antenna_000000464_detail.html','result':'catalog page read; explicit legacy SKP/DAE links returned502; no model used'}]})
print('research records written')
