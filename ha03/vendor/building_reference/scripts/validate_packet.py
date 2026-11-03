#!/usr/bin/env python3
"""Validate GAFAcraft packet structure and consistency; cannot verify web truth or image quality."""
import argparse
import datetime as dt
import json
import re
import sys
from math import isclose
from urllib.parse import urlparse
from scale import positive, convert, packet_bound
import reference_set

TITLES=['建筑概览与核心识别点','可靠尺度与Minecraft比例建议','设计语言/材料/幕墙','参考图片候选分类','最终推荐4张图','完整生成提示词','短版提示词','规模/质量/高度/附属广场与内部空间建议','风险与失败排查','复杂项目拆分顺序']
TOP_KEYS=['schema_version','packet_id','collected_at','subject','provenance','sources','facts','components','images','selection','scale','prompts','guidance','risks','staging','report_sections','experiments','gaps']
PLACEHOLDER=re.compile(r'\{\{[^}]*\}\}|\bTODO\b|\bTBD\b|<building>|<建筑名称>',re.I)


def text_value(x): return isinstance(x,str) and bool(x.strip())
def url_value(x): return isinstance(x,str) and urlparse(x).scheme in ('http','https') and bool(urlparse(x).netloc)
def iso_date(x):
    if not isinstance(x,str): return False
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',x): dt.date.fromisoformat(x); return True
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',x): dt.datetime.fromisoformat(x.replace('Z','+00:00')); return True
        return False
    except ValueError: return False

def close(a,b):
    if a is None or b is None: return a is b
    if isinstance(a,list) and isinstance(b,list): return len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool): return isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
    return a==b


class Validator:
    def __init__(self,p,mode,base_dir=None): self.base_dir=base_dir; self.p=p; self.report=mode=='report'; self.errors=[]; self.gaps=[]; self.maps={}
    def err(self,path,message): self.errors.append(f'{path}: {message}')
    def gap(self,path,message): self.gaps.append(f'{path}: {message}')
    def reqtext(self,obj,key,path):
        if not text_value(obj.get(key)): self.err(path+'.'+key,'required nonempty text')
    def refs(self,ids,group,path):
        if not isinstance(ids,list): self.err(path,'must be an array'); return
        for i in ids:
            if not isinstance(i,str) or i not in self.maps.get(group,{}): self.err(path,f'dangling {group} reference {i!r}')
    def collection(self,key,idkey,prefix):
        values=self.p.get(key)
        self.maps[key]={}
        if not isinstance(values,list): self.err(key,'must be an array'); return []
        for index,item in enumerate(values):
            path=f'{key}[{index}]'
            if not isinstance(item,dict): self.err(path,'must be an object'); continue
            ident=item.get(idkey)
            pattern=(r'[A-Za-z][A-Za-z0-9_.-]*' if self.p.get('schema_version')=='1.1' else prefix[:-1]+r'[-_][A-Za-z0-9_-]+')
            if not isinstance(ident,str) or not re.fullmatch(pattern,ident): self.err(path+'.'+idkey,f'use stable {prefix} identifier'); continue
            if ident in self.maps[key]: self.err(path+'.'+idkey,'duplicate ID')
            self.maps[key][ident]=item
        return [v for v in values if isinstance(v,dict)]
    def run(self):
        p=self.p
        if not isinstance(p,dict): return {'status':'FAIL','errors':['root must be an object'],'gaps':[]}
        for k in TOP_KEYS:
            if k not in p: self.err(k,'missing top-level field')
        if p.get('schema_version') not in ('1.0','1.1'): self.err('schema_version','expected 1.0 or 1.1')
        expected={'subject':dict,'provenance':dict,'selection':dict,'scale':dict,'prompts':dict,'guidance':dict,'staging':dict,'risks':list,'report_sections':list,'experiments':list,'gaps':list}
        for k,kind in expected.items():
            if not isinstance(p.get(k),kind): self.err(k,f'must be {kind.__name__}')
        if any(not isinstance(p.get(k),kind) for k,kind in expected.items()): return self.result()
        sources=self.collection('sources','source_id','src-')
        facts=self.collection('facts','fact_id','fact-')
        images=self.collection('images','image_id','img-')
        components=self.collection('components','component_id','component-')
        for s in sources:
            path=s.get('source_id','source')
            self.reqtext(s,'type',path)
            if self.p.get('schema_version')=='1.1' and s.get('title') is None and s.get('accessed_at') is None:self.gap(path+'.title','source page title not inspected')
            else:self.reqtext(s,'title',path)
            if not url_value(s.get('url')): self.err(path+'.url','must be original source HTTP(S) page')
            if self.p.get('schema_version')=='1.1' and s.get('accessed_at') is None:self.gap(path+'.accessed_at','source access date unknown; discovery only')
            elif not iso_date(s.get('accessed_at')): self.err(path+'.accessed_at','ISO date required')
        for f in facts:
            path=f.get('fact_id','fact'); kind=f.get('kind')
            if kind not in ('fact','observation','estimate','suggestion','user_observation'): self.err(path+'.kind','unknown epistemic kind')
            if f.get('status') not in ('verified','unverified','conflicted','proposed','user_reported'): self.err(path+'.status','unknown status')
            self.reqtext(f,'field',path)
            self.refs(f.get('source_ids',[]),'sources',path+'.source_ids')
            self.refs(f.get('image_ids',[]),'images',path+'.image_ids')
            self.refs(f.get('derived_from_fact_ids',[]),'facts',path+'.derived_from_fact_ids')
            if kind=='fact' and f.get('value') is not None and not f.get('source_ids'): self.err(path,'non-null factual claim requires source_ids')
            if self.p.get('schema_version')=='1.1' and kind=='fact' and f.get('status')=='verified' and not any(iso_date(self.maps['sources'].get(x,{}).get('accessed_at')) for x in f.get('source_ids',[])):self.err(path,'verified fact requires an actually accessed source')
            if kind=='fact' and f.get('status')=='verified' and f.get('value') is None: self.err(path,'verified fact cannot be null')
            if kind=='observation' and not f.get('image_ids') and not f.get('source_ids'): self.err(path,'observation requires viewed evidence')
            if kind=='observation':
                for ident in f.get('image_ids',[]):
                    if self.maps['images'].get(ident,{}).get('verification_state') not in ('page_viewed','full_image_viewed'): self.err(path,'image observation requires actually viewed page/image evidence')
            if kind in ('estimate','suggestion','user_observation') and not text_value(f.get('basis')): self.err(path+'.basis','estimate/suggestion/user observation must state basis')
            if kind=='estimate' and not (f.get('source_ids') or f.get('image_ids') or f.get('derived_from_fact_ids')): self.err(path,'estimate requires evidence refs')
            if kind=='user_observation' and f.get('status')!='user_reported': self.err(path,'user observations must remain user_reported')
            if f.get('status')=='conflicted' and not text_value(f.get('conflict_group')): self.err(path,'conflicting values need conflict_group; preserve each value separately')
            if f.get('status') in ('unverified','conflicted'): self.gap(path,'fact unresolved')
        for c in components:
            path=c.get('component_id','component'); self.reqtext(c,'name',path)
            self.refs(c.get('fact_ids',[]),'facts',path+'.fact_ids')
            if c.get('parent_component_id') is not None: self.refs([c['parent_component_id']],'components',path+'.parent_component_id')
        for im in images: self.check_image(im)
        self.check_selection()
        self.check_scale()
        self.check_staging()
        self.check_report()
        for i,e in enumerate(p['experiments']):
            path=f'experiments[{i}]'
            if not isinstance(e,dict): self.err(path,'must be object'); continue
            if e.get('evidence_type')!='user_feedback' or not text_value(e.get('feedback_quote')): self.err(path,'results require actual user_feedback and recorded feedback_quote')
            if e.get('claim_scope')!='user_observation': self.err(path,'must not generalize user observations into model benchmark')
            if 'feedback_date' not in e or (e.get('feedback_date') is not None and not iso_date(e['feedback_date'])): self.err(path+'.feedback_date','ISO date or explicit null required')
            provenance=e.get('provenance',{})
            if not isinstance(provenance,dict) or provenance.get('type') not in ('user_message','provided_context') or not text_value(provenance.get('reference')): self.err(path+'.provenance','actual user-message/context reference required')
        return self.result()
    def check_image(self,im):
        path=im.get('image_id','image'); local_ok=reference_set.local_image(self,im)
        if im.get('media_type') not in ('photo','site_plan','roof_plan','elevation','section','render','model','ai_image','unknown'): self.err(path+'.media_type','invalid media group')
        self.refs(im.get('source_ids',[]),'sources',path+'.source_ids')
        self.refs(im.get('component_ids',[]),'components',path+'.component_ids')
        if im.get('page_url') is None and not local_ok: self.gap(path+'.page_url','original image page not yet located; discovery candidate only')
        elif not local_ok and not url_value(im.get('page_url')): self.err(path+'.page_url','must be original HTTP(S) page URL or null when unknown')
        state=im.get('verification_state')
        if state not in ('discovered','page_viewed','full_image_viewed','inaccessible'): self.err(path+'.verification_state','invalid state')
        if im.get('built_state') not in ('constructed','design','unknown'): self.err(path+'.built_state','constructed/design/unknown required')
        if state in ('page_viewed','full_image_viewed') and not im.get('source_ids') and not local_ok: self.err(path,'viewed images require original-page source_ids')
        q=im.get('quality',{})
        if not isinstance(q,dict): self.err(path+'.quality','must be object'); q={}
        pixels=im.get('actual_pixels')
        if pixels is not None and (not isinstance(pixels,list) or len(pixels)!=2 or not all(isinstance(v,int) and not isinstance(v,bool) and v>0 for v in pixels)): self.err(path+'.actual_pixels','must be [actual width px, actual height px] or null')
        if state!='full_image_viewed' and pixels is not None: self.err(path,'actual_pixels cannot be asserted before viewing full image')
        quality_claim=q.get('assessment')
        claims_high_quality=isinstance(quality_claim,str) and bool(re.search(r'high[ _-]?quality|高质量|高清已核验',quality_claim,re.I))
        if (q.get('eligible') is True or claims_high_quality) and state!='full_image_viewed': self.err(path,'cannot claim eligible/high_quality before full image inspection')
        if q.get('eligible') is True:
            if not local_ok and not url_value(im.get('page_url')): self.err(path+'.page_url','eligible image needs actual original HTTP(S) page; search thumbnail alone insufficient')
            if pixels is None: self.err(path,'eligible image needs observed actual pixel dimensions')
            if im.get('building_match_confirmed') is not True: self.err(path,'eligible image needs confirmed identity')
            for k in ('view','covers','orientation','version'):
                if not im.get(k): self.err(path+'.'+k,'eligible image needs inspected metadata')
            if not text_value(q.get('assessment')): self.err(path+'.quality.assessment','eligible image needs qualitative assessment')
        if not isinstance(q.get('limitations',[]),list): self.err(path+'.quality.limitations','must be array')
        if im.get('license_status') not in ('unknown','permission_granted','licensed','public_domain','restricted'): self.err(path+'.license_status','state unknown rather than assuming permission')
        if im.get('training_authorized') is True and not text_value(im.get('training_authorization_basis')): self.err(path,'training use requires explicit authorization basis')
        if im.get('license_status') in ('unknown','restricted') and im.get('training_authorized') is True: self.err(path,'unknown/restricted license cannot imply training authorization')
        if state in ('page_viewed','full_image_viewed') and not iso_date(im.get('checked_at')): self.err(path+'.checked_at','inspection date required')
        if state!='full_image_viewed': self.gap(path,'full image unverified or inaccessible')
    def check_selection(self):
        if self.p.get('schema_version')=='1.1':return reference_set.check_selection(self)
        sel=self.p['selection']; slots=sel.get('slots')
        self.selected=[]
        if not isinstance(slots,list) or len(slots)!=4: self.err('selection.slots','exactly four slots required (null gaps allowed)'); return
        if [s.get('slot') if isinstance(s,dict) else None for s in slots]!=[1,2,3,4]: self.err('selection.slots','upload order must be slots 1,2,3,4')
        for i,s in enumerate(slots):
            path=f'selection.slots[{i}]'
            if not isinstance(s,dict): self.err(path,'must be object'); continue
            ident=s.get('image_id')
            if ident is None:
                if self.report and not text_value(s.get('missing_search')): self.err(path+'.missing_search','missing slot needs a targeted search direction')
                self.gap(path,'qualified image missing'); continue
            self.refs([ident],'images',path+'.image_id'); self.selected.append(ident)
            im=self.maps['images'].get(ident,{})
            if im.get('verification_state')!='full_image_viewed' or im.get('quality',{}).get('eligible') is not True: self.err(path,'selected image must pass full-image quality gate')
            if im.get('media_type') in ('render','model','ai_image','unknown'): self.err(path,'selected real-reference images cannot be render/model/AI/unknown; keep these as separate candidates')
            for k in ('purpose','rationale'): self.reqtext(s,k,path)
        if len(self.selected)!=len(set(self.selected)): self.err('selection.slots','four complementary images cannot repeat same ID')
        limit=sel.get('target_image_limit')
        if limit is not None and (not isinstance(limit,int) or isinstance(limit,bool) or limit<1): self.err('selection.target_image_limit','must be positive integer or null')
        omitted=sel.get('omitted_constraints',[])
        if not isinstance(omitted,list): self.err('selection.omitted_constraints','must be an array'); omitted=[]
        if isinstance(limit,int) and not isinstance(limit,bool) and limit>0 and len(self.selected)>limit:
            for ident in self.selected[limit:]:
                if not any(isinstance(note,str) and ident in note for note in omitted): self.err('selection.omitted_constraints','limited tool input needs omitted geometric constraint explanation for '+ident)
        checks=sel.get('consistency_checks')
        if not isinstance(checks,dict): self.err('selection.consistency_checks','must be object'); return
        for k in ('same_version','clean_subject','orientation_aligned'):
            if checks.get(k) not in (True,False,None): self.err('selection.consistency_checks.'+k,'must be boolean or null')
            if self.report and checks.get(k) is not True: self.gap('selection.consistency_checks.'+k,'unresolved or failed image consistency check')
        for k in ('layout_basis_image_ids','podium_closeup_image_ids','shell_crosscheck_image_ids'): self.refs(checks.get(k,[]),'images','selection.consistency_checks.'+k)
    def check_scale(self):
        sc=self.p['scale']; dim_groups={}
        for group,keys in [('building_dimensions',['width','length','overall_height','architectural_height','roof_height','tip_height']),('site_dimensions',['width','length'])]:
            dims=sc.get(group)
            if not isinstance(dims,dict): self.err('scale.'+group,'must be object'); continue
            for k in keys:
                path='scale.'+group+'.'+k; m=dims.get(k)
                if not isinstance(m,dict): self.err(path,'measurement object required'); continue
                dim_groups[group+'.'+k]=m
                value=m.get('value_m'); interval=m.get('range_m'); fid=m.get('fact_id'); f=self.maps['facts'].get(fid,{})
                if fid is not None: self.refs([fid],'facts',path+'.fact_id')
                if value is not None or interval is not None:
                    allowed_fields={k,group+'.'+k} if group=='building_dimensions' else {'site_'+k,group+'.'+k}
                    if f.get('field') not in allowed_fields: self.err(path+'.fact_id','measurement fact field must match '+ ' or '.join(sorted(allowed_fields)))
                if value is not None:
                    if not positive(value): self.err(path+'.value_m','finite positive meters required')
                    if f.get('kind')!='fact' or f.get('status')!='verified' or not close(f.get('value'),value) or f.get('unit')!='m': self.err(path,'precise dimension requires matching verified fact in meters; estimates use range_m')
                    if f.get('conflict_group') and not text_value(f.get('adoption_reason')): self.err(path,'adopted conflict value needs reason')
                if interval is not None:
                    if value is not None: self.err(path,'value and interval mutually exclusive')
                    if not isinstance(interval,list) or len(interval)!=2 or not all(positive(v) for v in interval) or interval[0]>interval[1]: self.err(path+'.range_m','must be positive [lower,upper]')
                    if f.get('kind') not in ('estimate','fact') or f.get('unit')!='m' or not close(f.get('value'),interval): self.err(path,'interval needs matching evidence-bearing fact/estimate')
                    if not text_value(m.get('basis')): self.err(path+'.basis','interval needs basis/sensitivity explanation')
                    self.gap(path,'only interval available; do not claim a precise dimension')
                if value is None and interval is None and self.report: self.gap(path,'dimension unverified')
        overall=sc.get('building_dimensions',{}).get('overall_height',{}).get('value_m')
        for key in ('architectural_height','roof_height','tip_height'):
            height=sc.get('building_dimensions',{}).get(key,{}).get('value_m')
            if positive(overall) and positive(height) and height>overall: self.err('scale.building_dimensions.'+key,'cannot exceed overall envelope height')
        budget=sc.get('world_budget')
        if not isinstance(budget,dict): self.err('scale.world_budget','must be object'); budget={}
        for axis in ('width','depth','height'):
            b=budget.get(axis)
            if not isinstance(b,dict): self.err('scale.world_budget.'+axis,'object required'); continue
            if b.get('blocks') is not None and (not isinstance(b['blocks'],int) or isinstance(b['blocks'],bool) or b['blocks']<=0): self.err('scale.world_budget.'+axis,'blocks must be positive integer or null')
            if b.get('confirmed') is True and (b.get('blocks') is None or not text_value(b.get('basis'))): self.err('scale.world_budget.'+axis,'confirmed budget needs blocks and confirmation basis')
            if self.report and b.get('confirmed') is not True: self.gap('scale.world_budget.'+axis,'available build allowance unconfirmed')
        s=sc.get('selected_s')
        if s is not None and not positive(s): self.err('scale.selected_s','finite positive blocks per meter required')
        if sc.get('rounding')!='half_up': self.err('scale.rounding','expected half_up')
        conversions=sc.get('conversions')
        if not isinstance(conversions,list): self.err('scale.conversions','must be array'); conversions=[]
        for i,c in enumerate(conversions):
            path=f'scale.conversions[{i}]'
            if not isinstance(c,dict): self.err(path,'must be object'); continue
            target=c.get('target'); m=dim_groups.get(target)
            if m is None: self.err(path+'.target','unknown measurement'); continue
            if m.get('value_m') is None and m.get('range_m') is None: self.err(path,'cannot derive block dimensions from missing measurements'); continue
            if not positive(c.get('s')): self.err(path+'.s','positive s required'); continue
            try: result=convert(m.get('value_m'),m.get('range_m'),c['s'])
            except ValueError as e: self.err(path,str(e)); continue
            for key in ('blocks','blocks_range','error_m','error_range_m'):
                if not close(c.get(key),result[key]): self.err(path+'.'+key,'inconsistent with half_up conversion and backfilled meter error')
        if not self.errors:
            bound=packet_bound(sc)['maximum_s']
            if not close(sc.get('uniform_scale_max'),bound): self.err('scale.uniform_scale_max','must equal confirmed constraint bound, or null when no computable bound')
            if s is not None and bound is not None and s>bound+1e-9: self.err('scale.selected_s','exceeds confirmed uniform scale bound')
        areas=self.p['subject'].get('areas')
        if not isinstance(areas,dict): self.err('subject.areas','separate area objects required'); areas={}
        for key in ('land_area','gross_floor_area','footprint_area'):
            if key not in areas: self.err('subject.areas.'+key,'keep land/floor/footprint areas separate, unknown is null')
        for key,area in areas.items():
            if not isinstance(area,dict): self.err('subject.areas.'+key,'must be object'); continue
            v=area.get('value_m2'); fid=area.get('fact_id')
            if fid is not None: self.refs([fid],'facts','subject.areas.'+key)
            if v is not None:
                f=self.maps['facts'].get(fid,{})
                if not positive(v) or f.get('kind')!='fact' or f.get('status')!='verified' or f.get('unit')!='m2' or not close(v,f.get('value')): self.err('subject.areas.'+key,'area needs matching verified fact in m2')
    def check_staging(self):
        st=self.p['staging']; required=st.get('required'); stages=st.get('stages')
        if required not in (True,False,None): self.err('staging.required','must be boolean or null')
        if self.report:
            if required is None: self.err('staging.required','decide whether staging is needed')
            self.reqtext(st,'reason','staging')
        if not isinstance(stages,list): self.err('staging.stages','must be array'); return
        if required is True and not stages: self.err('staging.stages','required staging needs ordered stages')
        if required is False and stages: self.err('staging.stages','single-stage/no split should leave stages empty')
        coord=st.get('coordinate_system')
        if not isinstance(coord,dict): self.err('staging.coordinate_system','must be object'); coord={}
        ids=[]; ready_by_id={}
        for i,stage in enumerate(stages):
            path=f'staging.stages[{i}]'
            if not isinstance(stage,dict): self.err(path,'must be object'); continue
            sid=stage.get('stage_id')
            if not text_value(sid) or sid in ids: self.err(path+'.stage_id','stable unique stage ID required')
            deps=stage.get('depends_on',[])
            if not isinstance(deps,list) or any(d not in ids for d in deps): self.err(path+'.depends_on','dependencies must be earlier stages')
            ids.append(sid)
            if stage.get('readiness')=='ready' and isinstance(deps,list) and any(ready_by_id.get(d) is not True for d in deps): self.err(path,'ready stage cannot depend on blocked or missing stage')
            if text_value(sid): ready_by_id[sid]=stage.get('readiness')=='ready'
            if 's' in stage and not close(stage['s'],coord.get('s')): self.err(path+'.s','stage scale must match shared coordinate-system scale')
            if 'coordinate_system' in stage and stage['coordinate_system']!=coord: self.err(path+'.coordinate_system','stage must use shared coordinate frame; express offsets via stage.origin')
            for key in ('name','origin','orientation','bbox','interfaces','acceptance','readiness','component_ids'):
                if key not in stage: self.err(path+'.'+key,'missing stage field')
            self.refs(stage.get('component_ids',[]),'components',path+'.component_ids')
            if stage.get('readiness') not in ('ready','blocked'): self.err(path+'.readiness','ready or blocked required')
            if not isinstance(stage.get('acceptance'),list) or not stage['acceptance']: self.err(path+'.acceptance','specific acceptance criteria required')
            if not isinstance(stage.get('interfaces'),list): self.err(path+'.interfaces','array required, use [] for none')
            else:
                for j,face in enumerate(stage['interfaces']):
                    fp=f'{path}.interfaces[{j}]'
                    if not isinstance(face,dict): self.err(fp,'interface object required'); continue
                    for key in ('interface_id','description'): self.reqtext(face,key,fp)
                    self.refs(face.get('with_component_ids',[]),'components',fp+'.with_component_ids')
                    if stage.get('readiness')=='ready' and face.get('location') is None: self.err(fp+'.location','ready interface requires coordinates or named geometric boundary')
            for key in ('origin','bbox'):
                value=stage.get(key)
                if value is not None and (not isinstance(value,list) or len(value)!=3 or not all(isinstance(v,int) and not isinstance(v,bool) for v in value)): self.err(path+'.'+key,'must be [x,y,z] integer blocks or null')
            if isinstance(stage.get('bbox'),list) and any(v<=0 for v in stage['bbox'] if isinstance(v,int)): self.err(path+'.bbox','all dimensions positive')
            if stage.get('readiness')=='ready':
                if any(stage.get(k) is None for k in ('origin','orientation','bbox')): self.err(path,'ready stage needs concrete origin, orientation and bbox')
                if not text_value(stage.get('orientation')): self.err(path+'.orientation','ready stage needs nonempty orientation')
                if not positive(coord.get('s')) or not close(coord.get('s'),self.p['scale'].get('selected_s')): self.err(path,'ready stage must share selected uniform scale')
                shared_origin=coord.get('origin')
                if not isinstance(shared_origin,list) or len(shared_origin)!=3 or not all(isinstance(v,int) and not isinstance(v,bool) for v in shared_origin): self.err(path,'ready stage needs shared origin of three integer coordinates')
                if any(not text_value(coord.get(k)) for k in ('x_axis','y_axis','z_axis','north')): self.err(path,'ready stage needs nonempty shared axis/north directions')
                axes=[coord.get(k) for k in ('x_axis','y_axis','z_axis')]
                if all(text_value(v) for v in axes) and len(set(v.strip().casefold() for v in axes))!=3: self.err(path,'shared x/y/z axis directions must be distinct')
            elif not text_value(stage.get('blocked_reason')): self.err(path+'.blocked_reason','blocked stage needs missing constraint explanation')
            else: self.gap(path,stage['blocked_reason'])
        if required is True and len(stages)<2: self.err('staging.stages','split requires at least two phases')
    def check_report(self):
        p=self.p; subject=p['subject']; sections=p['report_sections']; prompts=p['prompts']
        if subject.get('kind') not in ('single','complex',None): self.err('subject.kind','single/complex/null required')
        if self.report:
            for key in ('packet_id','collected_at'):
                if not text_value(p.get(key)): self.err(key,'required in report mode')
            if p.get('collected_at') and not iso_date(p['collected_at']): self.err('collected_at','ISO date required')
            self.reqtext(subject,'name','subject')
            if subject.get('kind') is None: self.err('subject.kind','single/complex decision required')
            if subject.get('identity_status') not in ('confirmed','provisional'): self.err('subject.identity_status','confirmed/provisional required')
            if subject.get('identity_status')=='provisional': self.gap('subject.identity_status','identity provisional')
            if p['provenance'].get('research_status') not in ('complete','incomplete'): self.err('provenance.research_status','complete/incomplete required')
        if len(sections)!=10 or [s.get('number') if isinstance(s,dict) else None for s in sections]!=list(range(1,11)): self.err('report_sections','exactly ten numbered sections in order required')
        for i,sec in enumerate(sections):
            path=f'report_sections[{i}]'
            if not isinstance(sec,dict): self.err(path,'must be object'); continue
            if i<10 and sec.get('title')!=('核心参考图与覆盖分析' if i==4 and p['schema_version']=='1.1' else TITLES[i]): self.err(path+'.title','fixed section title required')
            for key,group in [('source_ids','sources'),('fact_ids','facts'),('image_ids','images')]: self.refs(sec.get(key,[]),group,path+'.'+key)
            if self.report:
                self.reqtext(sec,'content',path)
                if isinstance(sec.get('content'),str) and PLACEHOLDER.search(sec['content']): self.err(path+'.content','unfilled placeholders are not a usable report')
        self.refs(prompts.get('image_ids',[]),'images','prompts.image_ids')
        excluded=prompts.get('excluded_image_ids',[])
        self.refs(excluded,'images','prompts.excluded_image_ids')
        if not isinstance(excluded,list): excluded=[]
        if len(excluded)!=len(set(excluded)): self.err('prompts.excluded_image_ids','excluded IDs must be unique')
        if set(excluded)&set(self.selected): self.err('prompts.excluded_image_ids','excluded images cannot also be selected/used')
        if set(prompts.get('image_ids',[]))!=set(self.selected): self.err('prompts.image_ids','must exactly match selected non-null image IDs')
        for k,minlen in [('full',100),('short',35)]:
            content=prompts.get(k)
            if self.report:
                if not text_value(content) or len(content.strip())<minlen: self.err('prompts.'+k,'must contain a useful copyable prompt, not only template fields'); continue
                if PLACEHOLDER.search(content): self.err('prompts.'+k,'unfilled template placeholders prohibited')
                if text_value(subject.get('name')) and subject['name'] not in content: self.err('prompts.'+k,'building identity must be explicit')
                for ident in self.selected:
                    if ident not in content: self.err('prompts.'+k,f'missing selected image reference {ident}')
                mentioned=set(re.findall(r'img[-_][A-Za-z0-9_-]+',content))
                if mentioned-set(self.selected)-set(excluded): self.err('prompts.'+k,'references nonselected images without listing excluded_image_ids')
        if self.report and len(sections)==10:
            for index,key in [(5,'full'),(6,'short')]:
                if isinstance(sections[index],dict) and sections[index].get('content')!=prompts.get(key): self.err('report_sections',f'section {index+1} must contain the actual {key} prompt exactly')
        for i,r in enumerate(p['risks']):
            if not isinstance(r,dict): self.err(f'risks[{i}]','must be object'); continue
            for key in ('risk','symptom','correction'): self.reqtext(r,key,f'risks[{i}]')
    def result(self):
        status='FAIL' if self.errors else ('PASS_WITH_GAPS' if self.report and self.gaps else 'PASS')
        return {'status':status,'errors':self.errors,'gaps':self.gaps,'coverage':getattr(self,'coverage',[]),'limits':'Structural/provenance/consistency validation only; not independent web, image or generated-building verification.'}


def validate(packet,mode='report',base_dir=None):
    try: return Validator(packet,mode,base_dir).run()
    except (KeyError,TypeError,ValueError,AttributeError) as e:
        return {'status':'FAIL','errors':['Malformed nested input: '+str(e)],'gaps':[]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('packet'); ap.add_argument('--mode',choices=['template','report'],default='report')
    args=ap.parse_args()
    try:
        with open(args.packet,encoding='utf-8') as f: p=json.load(f,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('non-finite JSON number '+x)))
        result=validate(p,args.mode,__import__('pathlib').Path(args.packet).parent)
    except (OSError,ValueError) as e: result={'status':'FAIL','errors':[str(e)],'gaps':[]}
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return 1 if result['status']=='FAIL' else 0

if __name__=='__main__': sys.exit(main())
