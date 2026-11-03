"""Versioned, manually curated reference coverage. No direction/depth inference."""
import copy, hashlib, re
from pathlib import Path
FACES=('front','back','left','right','top','oblique','interior','unknown')

def selected_ids(packet):
    s=packet['selection']
    if packet['schema_version']=='1.0':return [x['image_id'] for x in s['slots'] if x['image_id']]
    return list(dict.fromkeys([x['image_id'] for x in s['core']]+[i for g in s['detail_groups'] for i in g['image_ids']]))

def migrate(packet):
    if packet['schema_version']!='1.0':raise ValueError('Migration requires packet 1.0')
    p=copy.deepcopy(packet);p['schema_version']='1.1';s=p['selection']
    slots=s.pop('slots');s['legacy_slots']=slots
    s['core']=[{k:x[k] for k in ('image_id','purpose','rationale')} for x in slots if x['image_id']]
    s['detail_groups']=[];s['views']=[{'image_id':im['image_id'],'face':'unknown','orientation_basis':None,'layer':'unknown','occlusion':'unknown','component_ids':list(im.get('component_ids',[])),'duplicate_of':None,'sha256':None} for im in p['images']]
    s['coverage_requirements']=[{'face':'unknown','component_id':None,'missing_search':x['missing_search'] or 'Legacy slot has no qualified image; investigate missing coverage.'} for x in slots if not x['image_id']]
    p['report_sections'][4]['title']='核心参考图与覆盖分析'
    return p

def check_selection(v):
    s=v.p['selection'];v.selected=[]
    if any(not isinstance(s.get(k),list) for k in ('core','detail_groups','views','coverage_requirements')):
        v.err('selection','core/detail_groups/views/coverage_requirements must be arrays');return
    if 'slots' in s:v.err('selection.slots','Use migrate(); 1.1 has core, not executable slots')
    core=[]
    for row in s['core']:
        ident=row['image_id'];core.append(ident)
        for k in ('purpose','rationale'):v.reqtext(row,k,'selection.core')
    if len(core)!=len(set(core)):v.err('selection.core','duplicate image ID')
    detail=[];seen_groups=set()
    for g in s['detail_groups']:
        v.refs([g['component_id']],'components','detail_groups.component_id');v.reqtext(g,'purpose','detail_groups')
        if g['component_id'] in seen_groups:v.err('detail_groups','duplicate component group')
        seen_groups.add(g['component_id'])
        if not isinstance(g['image_ids'],list) or len(g['image_ids'])!=len(set(g['image_ids'])):v.err('detail_groups','image_ids must be unique array')
        detail+=g['image_ids']
    v.selected=list(dict.fromkeys(core+detail));v.refs(v.selected,'images','selection')
    for i in v.selected:
        im=v.maps['images'].get(i,{})
        if im.get('verification_state')!='full_image_viewed' or im.get('quality',{}).get('eligible') is not True:v.err(i,'selected image must pass full-image quality gate')
        if im.get('media_type') in ('render','model','ai_image','unknown'):v.err(i,'not an eligible real reference')
    views={};hashes={}
    for a in s['views']:
        i=a['image_id'];v.refs([i],'images','views');v.refs(a.get('component_ids'),'components','views.component_ids')
        if i in views:v.err('views','duplicate image annotation')
        views[i]=a
        if a.get('face') not in FACES:v.err(i,'invalid face')
        if a.get('layer') not in ('outer','inner','mixed','unknown') or a.get('occlusion') not in ('none','partial','heavy','unknown'):v.err(i,'invalid layer/occlusion')
        if a.get('face')!='unknown' and not a.get('orientation_basis'):v.err(i,'known face requires orientation_basis')
        sha=a.get('sha256')
        if sha is not None:
            if not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha):v.err(i,'invalid SHA256')
            else:hashes.setdefault(sha,[]).append(i)
        duplicate=a.get('duplicate_of')
        if duplicate is not None:
            v.refs([duplicate],'images','duplicate_of')
            if duplicate==i:v.err(i,'self duplicate')
    for i in v.selected:
        if i not in views:v.err(i,'selected image needs view annotation')
    for i,a in views.items():
        visited={i};j=a.get('duplicate_of')
        while j in views:
            if j in visited:v.err(i,'duplicate cycle');break
            visited.add(j);j=views[j].get('duplicate_of')
        if a.get('duplicate_of') and i in core:v.err(i,'duplicate image must remain candidate/detail, not core')
    for ids in hashes.values():
        if len(set(ids)&set(core))>1:v.err('selection.core','same bytes selected more than once')
    coverage=[]
    for req in s['coverage_requirements']:
        face=req['face'];cid=req.get('component_id')
        if face not in FACES:v.err('coverage','invalid face')
        if cid is not None:v.refs([cid],'components','coverage.component_id')
        matching=[i for i in v.selected if i in views and not views[i].get('duplicate_of') and views[i]['face']==face and face!='unknown' and views[i]['occlusion']!='heavy' and (cid is None or cid in views[i]['component_ids'])]
        coverage.append({'face':face,'component_id':cid,'image_ids':matching,'status':'covered' if matching else 'missing'})
        if not matching:
            v.reqtext(req,'missing_search','coverage');v.gap('coverage',f'{face}/{cid}: '+str(req.get('missing_search')))
    if not core:v.gap('selection.core','no core images; do not claim complete reconstruction')
    v.coverage=coverage
    # Preserve legacy limits and consistency rules without imposing an image count.
    limit=s.get('target_image_limit')
    if limit is not None and (type(limit) is not int or limit<1):v.err('target_image_limit','positive integer or null required')
    omitted=s.get('omitted_constraints',[])
    if not isinstance(omitted,list):v.err('omitted_constraints','array required');omitted=[]
    if type(limit) is int and limit>0:
        for i in v.selected[limit:]:
            if not any(isinstance(x,str) and i in x for x in omitted):v.err('omitted_constraints','missing omission note for '+i)
    checks=s.get('consistency_checks',{})
    for k in ('same_version','clean_subject','orientation_aligned'):
        if checks.get(k) not in (True,False,None):v.err(k,'boolean/null required')
        if checks.get(k) is not True:v.gap(k,'not confirmed')
    for k in ('layout_basis_image_ids','podium_closeup_image_ids','shell_crosscheck_image_ids'):v.refs(checks.get(k,[]),'images',k)

def local_image(v,im):
    if v.p.get('schema_version')!='1.1' or not im.get('local_file'):return False
    base=getattr(v,'base_dir',None)
    if base is None:v.err(im['image_id'],'local evidence needs packet directory');return False
    root=Path(base).resolve();p=(root/im['local_file']).resolve();sha=im.get('local_sha256')
    if not p.is_relative_to(root) or not p.is_file():v.err(im['image_id'],'local evidence must be a file inside packet directory');return False
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:v.err(im['image_id'],'local evidence hash mismatch');return False
    return True
