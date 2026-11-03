#!/usr/bin/env python3
"""Synthetic contract tests. No real building, web request, downloaded image, or model evaluation."""
import copy
import json
import sys
import unittest
from pathlib import Path
from validate_packet import validate
from scale import convert, packet_bound, uniform_bound

ROOT=Path(__file__).resolve().parents[1]

def template(): return json.loads((ROOT/'references/packet-template.json').read_text(encoding='utf-8'))

def report():
    p=template(); p.update(packet_id='synthetic-fixture',collected_at='2026-10-16')
    p['subject'].update(name='合成校验对象',kind='single',identity_status='provisional')
    p['provenance'].update(user_input='仅验证结构，不研究实际建筑。',research_status='incomplete')
    p['staging'].update(required=False,reason='仅一个简单体量，本轮只校验数据结构，无需拆分。')
    for i,s in enumerate(p['selection']['slots']): s['missing_search']=['寻找同版本总平图','寻找建成整体照片','寻找侧立面实景','寻找基座细节照片'][i]
    p['prompts']['full']='请为合成校验对象准备Minecraft可复原体量。当前对象仅为合成结构测试，不代表真实建筑，现无合格参考图和已核实尺度；不要自行补齐长宽高或世界高度上限。先保留统一比例与朝向待确认，分别检查体量位置、立面节奏、屋顶外壳、场地边界；内部只保留入口和主交通的待定要求，灯光不得使整面玻璃发光。缺图时暂停几何定稿，不复制周边建筑，不把透视照片当总平。完成比例和图像核验后再细化材料与内部。'
    p['prompts']['short']='为合成校验对象建立Minecraft复原约束，尺寸、朝向和四图均待核实；先补总平及互补视角，保持统一尺度，不复制周边建筑，不将透视当摆位。'
    for s in p['report_sections']: s['content']='合成校验：当前资料不完整，未知保持未核实，下一步按缺口核验。'
    p['report_sections'][5]['content']=p['prompts']['full']; p['report_sections'][6]['content']=p['prompts']['short']
    return p

def source(p):
    if not p['sources']: p['sources'].append({'source_id':'src-synthetic','title':'Synthetic fixture, not evidence','publisher':None,'type':'synthetic','url':'https://example.invalid/fixture','accessed_at':'2026-10-16'})

def image(p,ident='img-one',state='full_image_viewed'):
    source(p)
    im={'image_id':ident,'source_ids':['src-synthetic'],'page_url':'https://example.invalid/fixture','direct_image_url':None,'creator':None,'media_type':'photo','built_state':'constructed','version':'synthetic-v1','view':'正面','orientation':'朝北','covers':['外壳'],'component_ids':[],'verification_state':state,'checked_at':'2026-10-16','building_match_confirmed':True,'actual_pixels':[1600,1200] if state=='full_image_viewed' else None,'quality':{'eligible':state=='full_image_viewed','assessment':'clear' if state=='full_image_viewed' else None,'limitations':[]},'license_status':'unknown','license_url':None,'training_authorized':False,'training_authorization_basis':None,'candidate_value':'测试视角'}
    p['images'].append(im); return im

def select(p,ident='img-one',slot=0):
    p['selection']['slots'][slot].update(image_id=ident,purpose='约束正面轮廓',rationale='新增正面几何信息',missing_search=None)
    p['prompts']['image_ids'].append(ident)
    for k,index in [('full',5),('short',6)]:
        p['prompts'][k]+=' 使用'+ident+'约束主体轮廓。'
        p['report_sections'][index]['content']=p['prompts'][k]

def dimension(p,key='overall_height',value=100):
    source(p); fid='fact-'+key
    p['facts'].append({'fact_id':fid,'field':key,'value':value,'unit':'m','kind':'fact','status':'verified','source_ids':['src-synthetic'],'image_ids':[],'derived_from_fact_ids':[],'basis':None,'conflict_group':None,'adoption_reason':None})
    p['scale']['building_dimensions'][key].update(value_m=value,fact_id=fid)
    return p['facts'][-1]

def stages(p,ready=False):
    p['subject']['kind']='complex'; p['staging'].update(required=True,reason='两个体量相对位置需要统一坐标。')
    p['staging']['stages']=[{'stage_id':'phase-1','name':'统一坐标与占位','depends_on':[],'component_ids':[],'origin':[0,0,0] if ready else None,'orientation':'统一朝北' if ready else None,'bbox':[50,100,60] if ready else None,'interfaces':[],'acceptance':['核实统一比例和相对位置后才进入单体阶段'],'readiness':'ready' if ready else 'blocked','blocked_reason':None if ready else '缺少经核验的总平尺度。'}, {'stage_id':'phase-2','name':'各单体主结构','depends_on':['phase-1'],'component_ids':[],'origin':[0,0,0] if ready else None,'orientation':'统一朝北' if ready else None,'bbox':[50,100,60] if ready else None,'interfaces':[],'acceptance':['各单体包围盒不得重叠；接口保留同一坐标'],'readiness':'ready' if ready else 'blocked','blocked_reason':None if ready else '待第一阶段确认坐标。'}]
    if ready:
        p['scale']['selected_s']=1
        p['staging']['coordinate_system'].update(origin=[0,0,0],x_axis='东',y_axis='上',z_axis='南',north='-Z',s=1)

class ContractTests(unittest.TestCase):
    def good(self,p,mode='report',status=None):
        r=validate(p,mode); self.assertNotEqual(r['status'],'FAIL',r)
        if status: self.assertEqual(r['status'],status,r)
    def bad(self,p,needle):
        r=validate(p); self.assertEqual(r['status'],'FAIL',r); self.assertTrue(any(needle in e for e in r['errors']),r)
    def test_template(self): self.good(template(),'template','PASS')
    def test_incomplete_report_and_zero_images(self): self.good(report(),status='PASS_WITH_GAPS')
    def test_ten_sections_required(self):
        p=report(); p['report_sections'].pop(); self.bad(p,'ten numbered')
    def test_fixed_heading(self):
        p=report(); p['report_sections'][2]['title']='错误'; self.bad(p,'fixed section')
    def test_missing_copyable_prompt(self):
        p=report(); p['prompts']['full']='{{building}}'; self.bad(p,'useful copyable')
    def test_prompt_section_must_contain_prompt(self):
        p=report(); p['report_sections'][5]['content']='仅见其他文件'; self.bad(p,'actual full prompt')
    def test_verification_states_allowed(self):
        for state in ('discovered','page_viewed','full_image_viewed','inaccessible'):
            with self.subTest(state=state):
                p=report(); image(p,state=state); self.good(p)
    def test_page_view_not_high_quality(self):
        p=report(); im=image(p,state='page_viewed'); im['quality']['assessment']='high_quality'; self.bad(p,'cannot claim')
    def test_no_pixels_before_full_view(self):
        p=report(); im=image(p,state='page_viewed'); im['actual_pixels']=[640,480]; self.bad(p,'actual_pixels cannot')
    def test_unverified_not_selected(self):
        p=report(); image(p,state='page_viewed'); select(p); self.bad(p,'full-image quality gate')
    def test_one_image_does_not_get_filled_to_four(self):
        p=report(); image(p); select(p); self.good(p,status='PASS_WITH_GAPS'); self.assertEqual(sum(s['image_id'] is not None for s in p['selection']['slots']),1)
    def test_gap_requires_search_direction(self):
        p=report(); p['selection']['slots'][2]['missing_search']=None; self.bad(p,'targeted search')
    def test_selected_image_missing_prompt_reference(self):
        p=report(); image(p); select(p); p['prompts']['short']=p['prompts']['short'].replace('img-one','该图'); p['report_sections'][6]['content']=p['prompts']['short']; self.bad(p,'missing selected image')
    def test_dangling_source(self):
        p=report(); image(p); p['images'][0]['source_ids']=['src-missing']; self.bad(p,'dangling sources')
    def test_missing_dimensions_no_precision(self):
        p=report(); p['scale']['conversions']=[dict(target='building_dimensions.width',s=1,blocks=80,error_m=0,blocks_range=None,error_range_m=None)]; self.bad(p,'missing measurements')
    def test_reliable_dimension_conversion(self):
        p=report(); dimension(p,value=100.5); p['scale']['conversions']=[dict(target='building_dimensions.overall_height',**convert(100.5,s=1))]; self.good(p)
    def test_estimated_point_not_allowed(self):
        p=report(); f=dimension(p); f.update(kind='estimate',basis='照片观察'); self.bad(p,'precise dimension')
    def test_estimated_interval_allowed(self):
        p=report(); f=dimension(p,value=[90,110]); f.update(kind='estimate',status='proposed',basis='合成区间，检验敏感性'); p['scale']['building_dimensions']['overall_height'].update(value_m=None,range_m=[90,110],basis='端点分别换算以表现误差'); p['scale']['conversions']=[dict(target='building_dimensions.overall_height',**convert(range_m=[90,110],s=.5))]; self.good(p)
    def test_fact_requires_source(self):
        p=report(); f=dimension(p); f['source_ids']=[]; self.bad(p,'requires source_ids')
    def test_confirmed_budget_bound(self):
        p=report(); dimension(p,value=200); p['scale']['world_budget']['height'].update(blocks=100,confirmed=True,basis='用户明确当前余量为100格'); p['scale']['uniform_scale_max']=.5; p['scale']['selected_s']=.5; self.good(p)
    def test_exceeds_budget(self):
        p=report(); dimension(p,value=200); p['scale']['world_budget']['height'].update(blocks=100,confirmed=True,basis='明确余量'); p['scale']['uniform_scale_max']=.5; p['scale']['selected_s']=1; self.bad(p,'exceeds confirmed')
    def test_complex_blocked_stages_deliverable(self):
        p=report(); stages(p); self.good(p,status='PASS_WITH_GAPS')
    def test_complex_ready_stages_same_scale(self):
        p=report(); stages(p,True); self.good(p)
    def test_ready_stage_without_bbox_rejected(self):
        p=report(); stages(p,True); p['staging']['stages'][1]['bbox']=None; self.bad(p,'ready stage needs')
    def test_bad_dependency(self):
        p=report(); stages(p); p['staging']['stages'][0]['depends_on']=['phase-2']; self.bad(p,'dependencies must be earlier')
    def test_simple_no_split_reason_required(self):
        p=report(); p['staging']['reason']=None; self.bad(p,'required nonempty text')
    def test_experiment_cannot_invent_performance(self):
        p=report(); p['experiments']=[{'evidence_type':'model_benchmark','feedback_quote':'','claim_scope':'universal'}]; self.bad(p,'actual user_feedback')
    def test_unknown_license_no_training(self):
        p=report(); im=image(p); im.update(training_authorized=True,training_authorization_basis='公开可访问'); self.bad(p,'cannot imply training')
    def test_scale_rounding_and_error(self):
        self.assertEqual(convert(5,s=.5),{'s':.5,'blocks':3,'blocks_range':None,'error_m':1.0,'error_range_m':None})
    def test_scale_range_and_unknown(self):
        self.assertEqual(convert(range_m=[9,11],s=.5)['blocks_range'],[5,6]); self.assertIsNone(convert(s=1)['blocks'])
    def test_uniform_unknown_ignored(self):
        r=uniform_bound({'height':200,'width':50},{'height':{'blocks':100,'confirmed':True},'width':{'blocks':10,'confirmed':False}}); self.assertEqual(r['maximum_s'],.5); self.assertIn('width',r['omitted_axes'])
    def test_site_bound_included(self):
        p=report(); p['scale']['site_dimensions']['width']['value_m']=100; p['scale']['world_budget']['width'].update(blocks=50,confirmed=True); self.assertEqual(packet_bound(p['scale'])['maximum_s'],.5)
    def test_render_not_selected(self):
        p=report(); im=image(p); im['media_type']='render'; select(p); self.bad(p,'selected real-reference')
    def test_ready_cannot_depend_on_blocked(self):
        p=report(); stages(p,True); p['staging']['stages'][0].update(readiness='blocked',blocked_reason='尚未确认'); self.bad(p,'cannot depend on blocked')
    def test_stage_specific_scale_must_match(self):
        p=report(); stages(p,True); p['staging']['stages'][1]['s']=.5; self.bad(p,'stage scale must match')
    def test_tool_image_limit_requires_lost_constraints(self):
        p=report(); image(p); select(p); image(p,'img-two'); select(p,'img-two',1); p['selection']['target_image_limit']=1; self.bad(p,'omitted geometric constraint'); p['selection']['omitted_constraints']=['未上传 img-two，因此基座反侧凹进量仍需核验。']; self.good(p)
    def test_bad_date_suffix_rejected(self):
        p=report(); p['collected_at']='2026-10-16-garbage'; self.bad(p,'ISO date')
    def test_user_feedback_unknown_date_is_explicit(self):
        p=report(); p['experiments']=[{'evidence_type':'user_feedback','feedback_quote':'合成测试用反馈，非真实评测。','claim_scope':'user_observation','feedback_date':None,'provenance':{'type':'provided_context','reference':'synthetic-test-only'}}]; self.good(p)
    def test_feedback_missing_provenance_rejected(self):
        p=report(); p['experiments']=[{'evidence_type':'user_feedback','feedback_quote':'合成文字','claim_scope':'user_observation','feedback_date':None}]; self.bad(p,'actual user-message')
    def test_chinese_high_quality_claim_without_image_rejected(self):
        p=report(); im=image(p,state='page_viewed'); im['quality']['assessment']='高质量已核验'; self.bad(p,'cannot claim')
    def test_observation_cannot_cite_unseen_image(self):
        p=report(); image(p,state='discovered'); p['facts'].append({'fact_id':'fact-observation','field':'facade','value':'条带立面','kind':'observation','status':'proposed','source_ids':[],'image_ids':['img-one']}); self.bad(p,'actually viewed')
    def test_area_categories_must_be_retained(self):
        p=report(); del p['subject']['areas']['footprint_area']; self.bad(p,'keep land/floor/footprint')
    def test_discovered_unknown_original_page_preserves_null(self):
        p=report(); im=image(p,state='discovered'); im.update(page_url=None,source_ids=[]); p['sources']=[]; self.good(p,status='PASS_WITH_GAPS')
    def test_eligible_image_requires_original_page(self):
        p=report(); im=image(p); im['page_url']=None; select(p); self.bad(p,'eligible image needs actual original')
    def test_nonnull_invalid_original_page_rejected(self):
        p=report(); im=image(p,state='discovered'); im['page_url']='unknown'; self.bad(p,'HTTP(S) page URL or null')
    def test_ready_shared_origin_requires_three_integers(self):
        for bad_origin in ([],[0,0],[0,False,0],[0,0,'0']):
            with self.subTest(origin=bad_origin):
                p=report(); stages(p,True); p['staging']['coordinate_system']['origin']=bad_origin; self.bad(p,'shared origin of three integer')
    def test_ready_shared_axes_and_north_nonempty(self):
        for key in ('x_axis','y_axis','z_axis','north'):
            with self.subTest(key=key):
                p=report(); stages(p,True); p['staging']['coordinate_system'][key]=' '; self.bad(p,'nonempty shared axis/north')
    def test_ready_axis_directions_distinct(self):
        p=report(); stages(p,True); p['staging']['coordinate_system']['z_axis']='东'; self.bad(p,'axis directions must be distinct')
    def test_ready_stage_orientation_nonempty(self):
        p=report(); stages(p,True); p['staging']['stages'][0]['orientation']=''; self.bad(p,'nonempty orientation')
    def test_height_cannot_use_width_fact(self):
        p=report(); f=dimension(p); f['field']='width'; self.bad(p,'measurement fact field must match')
    def test_qualified_building_dimension_field(self):
        p=report(); f=dimension(p); f['field']='building_dimensions.overall_height'; self.good(p)
    def test_site_dimension_field_must_be_qualified(self):
        p=report(); f=dimension(p,key='width',value=100); p['scale']['site_dimensions']['width'].update(value_m=100,fact_id=f['fact_id']); self.bad(p,'site_width')
        p['scale']['building_dimensions']['width'].update(value_m=None,fact_id=None); f['field']='site_width'; self.good(p)
        f['field']='site_dimensions.width'; self.good(p)
    def test_prompt_can_explicitly_exclude_unverified_candidate(self):
        p=report(); image(p); select(p); image(p,'img-unverified','page_viewed'); p['prompts']['excluded_image_ids']=['img-unverified']
        for key,index in [('full',5),('short',6)]:
            p['prompts'][key]+=' img-unverified 尚未核实，禁止用作生成依据。'; p['report_sections'][index]['content']=p['prompts'][key]
        self.good(p)
    def test_selected_image_cannot_also_be_excluded(self):
        p=report(); image(p); select(p); p['prompts']['excluded_image_ids']=['img-one']; self.bad(p,'excluded images cannot also')
    def test_prompt_unknown_excluded_id_rejected(self):
        p=report(); p['prompts']['excluded_image_ids']=['img-missing']; self.bad(p,'dangling images')
    def test_prompt_nonselected_mention_requires_exclusion_record(self):
        p=report(); image(p,'img-unverified','page_viewed'); p['prompts']['short']+=' img-unverified 尚未核实，不用于生成。'; p['report_sections'][6]['content']=p['prompts']['short']; self.bad(p,'without listing excluded_image_ids')
    def test_preserve_existing_underscore_ids(self):
        p=report(); image(p); select(p); dimension(p); p['components']=[{'component_id':'component_001','name':'合成体量','parent_component_id':None,'fact_ids':['fact-overall_height']}]
        encoded=json.dumps(p,ensure_ascii=False).replace('img-one','img_001').replace('fact-overall_height','fact_001').replace('src-synthetic','src_001'); p=json.loads(encoded); self.good(p)
    def test_excluded_candidate_with_underscore_id(self):
        p=report(); image(p,'img_001','page_viewed'); p['prompts']['excluded_image_ids']=['img_001']
        for key,index in [('full',5),('short',6)]:
            p['prompts'][key]+=' img_001 尚未核验，禁止用作复原参考。'; p['report_sections'][index]['content']=p['prompts'][key]
        self.good(p)
    def test_malformed_input_is_failure(self):
        self.assertEqual(validate({'subject':None})['status'],'FAIL')

if __name__=='__main__': unittest.main(verbosity=2)
