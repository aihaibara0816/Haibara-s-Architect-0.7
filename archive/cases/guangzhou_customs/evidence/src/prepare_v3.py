"""Prepare the V3 case without modifying any V1/V2 asset."""
from pathlib import Path
import json, hashlib, shutil
CASE=Path(__file__).resolve().parents[1]
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
p=json.loads((CASE/'params_v2.json').read_text())
p['case_version']='0.3.0'
p['podium']['rect']=[13,16,114,87] # bounding box, not a filled rectangle
p['podium']['glass_pavilions']=[[31,24,50,36],[77,24,96,36]]
p['podium']['roof_tinted_regions']=[[27,18,100,43]]
p['podium']['roof_surface_note']='后部居中屋面的绿灰色代理；不推定草坪或铜材质。'
p['tower']['central_rect']=[50,52,77,76]
p['v2']['podium_masses']=[[13,72,114,87],[25,16,102,72]]
p['v2']['upper_center_rect']=[50,52,77,76]
p['v2']['rear_window_bands'][-1]['z']=52
p['v2'].pop('side_portal',None)
p['v2'].pop('podium_window_segments',None)
p['v2']['geometry_intent']='V3保留V2塔身细节消费者；主体轮廓由倒T裙楼和收进中央后墙重新约束。'
p['v3']={
 'podium_components':[
  {'component_id':'podium.front_bar','rect':[13,72,114,87]},
  {'component_id':'podium.centered_stem','rect':[25,16,102,72]}],
 'symmetry_axis_x':63,
 'rear_portal':{'wall_z':16,'span_x':[43,84],'centres_x':[51,63,75],
                'confidence':'中低：中轴后门按用户形态解释；三拱细节来自img-nc-11，具体朝向/位置未测绘'},
 'podium_window_segments':[
  {'id':'stem_left','normal':[-1,0],'wall':25,'centres':list(range(22,71,6))},
  {'id':'stem_right','normal':[1,0],'wall':101,'centres':list(range(22,71,6))},
  {'id':'front_bar_left','normal':[-1,0],'wall':13,'centres':[76]},
  {'id':'front_bar_right','normal':[1,0],'wall':113,'centres':[76]},
  {'id':'left_return','normal':[0,-1],'wall':72,'centres':[17,22]},
  {'id':'right_return','normal':[0,-1],'wall':72,'centres':[104,109]},
  {'id':'rear_flanks','normal':[0,-1],'wall':16,'centres':[30,36,90,96]}],
 'coordinates':'前+Z，后-Z，左右以模型坐标为准；东北拍摄假设未据此强行旋转全模型',
 'evidence_priority':['user annotated oblique satellite: topology only','OSM way 313905695: coarse footprint','img-nc-11: roof pavilions, green-gray roof and three arches','front photos: preserved front facade'],
 'dimension_status':'101格前横段、77格居中后段、左右各12格退让；为整数化建模假设，不是地理配准测量',
 'feedback_status':'V2单侧突起被用户否定；V3待用户审阅',
 'not_claimed':['实测正射平面','自动照片配准','全部细节严格对称','Minecraft游戏内通过']}
p['estimates']=[
 '保持V1/V2的137格总高、126×148×116包围盒和相机，便于比较；不是精确1:1。',
 '倒T平面由用户标注与OSM粗轮廓共同支持；具体边长与拐点是本版建模假设。',
 '高层屋顶在斜卫星图中的偏移不直接转成裙楼轮廓；不同标高分开建模。',
 '中央体后墙由z44收至z52，中央下段与上段均27×24格，钟室13×13格；精确尺寸仍待核实。',
 '三拱后入口沿模型中轴布置，照片支持拱券形式，绝对朝向与具体位置仍需核实。',
 '伪内饰、混合暖冷窗灯及小型地景沿用游戏设计；未进Minecraft测试。']
dump(CASE/'params_v3.json',p)
out=CASE/'research/v3';out.mkdir(parents=True,exist_ok=True)
uploads=CASE.parents[3]/'upload'
sources=[('user-plan','0f51e3e64ac62293a0ab954ff2792c09.jpg'),('user-v2-top','image(20261024-055003).png'),('user-v2-oblique','image(20261024-055044).png'),('user-photo','image(20261024-055204).png')]
refs=[]
for ident,name in sources:
    src=uploads/name
    if not src.exists():
        refs.append({'id':ident,'status':'missing','original_name':name});continue
    dest=out/'images'/(ident+src.suffix);dest.parent.mkdir(exist_ok=True)
    shutil.copyfile(src,dest)
    refs.append({'id':ident,'path':str(dest.relative_to(CASE)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source':'user supplied','viewed':True,'licence':'user supplied for this case'})
dump(out/'feedback_and_decisions.json',{
 'version':'V3','previous_fidelity':'V2 podium rejected by user; offline technical checks did not validate footprint fidelity',
 'feedback':'斜卫星有高层投影偏移。整体采用对称倒T：前横向展开，后部居中收窄；不要保留单侧突出。',
 'references':refs,
 'reuse':'11张V2已查看照片及原来源记录全部保留；本轮新增用户标注，不把模型截图算独立实景。',
 'components':[
  {'id':'podium.front_bar','change':'前横段宽101格、主体进深15格；前柱廊独立向前延伸','evidence':['user-plan','OSM way313905695'],'parameter':'v3.podium_components[0]','consumer':'CustomsV3.masks / inherited shell_and_floors','confidence':'topology medium-high; dimensions estimated'},
  {'id':'podium.centered_stem','change':'后段宽77格，左右各退12格，延伸至轴线后门；删除V2单边翼','evidence':['user-plan','OSM way313905695'],'parameter':'v3.podium_components[1]','consumer':'CustomsV3.masks','confidence':'topology medium-high; dimensions estimated'},
  {'id':'tower.central','change':'中央后墙退入8格，下段深度32→24，避免把偏移屋顶解释成后伸实体','evidence':['user-plan','user-photo'],'parameter':'tower.central_rect','consumer':'masks / tower_facades','confidence':'medium; no metric registration'},
  {'id':'podium.roof','change':'两座玻璃房落在居中后段，绿灰屋面跟随承托面，不再构成单侧突起','evidence':['user-photo','img-nc-11'],'parameter':'podium.glass_pavilions / roof_tinted_regions','consumer':'CustomsV3.podium','confidence':'presence confirmed; placement estimated'},
  {'id':'podium.rear_portal','change':'三拱与后门移至中轴末端，去除侧面孤立突出','evidence':['user-photo','user interpretation'],'parameter':'v3.rear_portal','consumer':'CustomsV3.podium','confidence':'provisional position; arch morphology photo-supported'}],
 'acceptance':'pending user visual review; not game tested'})
# Freeze all pre-existing code and V1/V2 run assets for post-change comparison.
paths=list((CASE.parents[1]/'hafusion').rglob('*.py'))+list((CASE.parents[1]/'support').rglob('*.py'))
paths += [CASE/'params.json',CASE/'params_v2.json',CASE/'src/build_case.py',CASE/'src/build_v2.py',CASE/'cameras.json']
paths += [q for run in ['V1_r04','V2_r06'] for q in (CASE/'runs'/run).rglob('*') if q.is_file()]
proof=out/'baseline_hashes.json'
if not proof.exists():dump(proof,{str(q.relative_to(CASE.parents[1])):hashlib.sha256(q.read_bytes()).hexdigest() for q in paths})
print('Prepared V3; V1/V2 parameters, source and runs unchanged.')
