"""Optional model provenance and field-level adoption. No model I/O or inference."""
import copy, math, re

def resolve(obj,pointer):
    if not isinstance(pointer,str) or not pointer.startswith('/'):raise ValueError('Expected JSON pointer')
    for token in pointer[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        if isinstance(obj,list):
            if not token.isdigit():raise ValueError('Array pointer needs nonnegative index')
            obj=obj[int(token)]
        else:obj=obj[token]
    return obj

def legacy_projection(spec):
    p=copy.deepcopy(spec);p['schema_version']='0.1'
    p.pop('research',None);p.pop('assembly',None)
    return p

def validate_research(spec):
    r=spec['research'];cm={c['component_id']:c for c in spec['components']}
    models={m['model_id']:m for m in r['models']}
    if len(models)!=len(r['models']):raise ValueError('Duplicate model ID')
    if r['model_status'] in ('not_requested','not_found') and models:raise ValueError('Model status contradicts model records')
    rs=r.get('reference_set')
    if rs is not None:
        known={x['image_id'] for x in spec['evidence']['images']}
        if any(not isinstance(rs.get(k),list) for k in ('core','detail_groups','views','coverage_requirements')):raise ValueError('Malformed reference set')
        selected={x['image_id'] for x in rs['core']}|{i for g in rs['detail_groups'] for i in g['image_ids']}
        if not selected<=known or selected!=set(spec['evidence']['selected_image_ids']):raise ValueError('Reference selection differs from evidence')
        if any(x['image_id'] not in known for x in rs['views']):raise ValueError('Unknown reference annotation')
    sources={s['source_id'] for s in spec['evidence']['sources']}
    for m in models.values():
        if m['source_id'] is not None and m['source_id'] not in sources:raise ValueError('Dangling model source')
        if m['status']=='checked' and m['transform'] is None:raise ValueError('Checked model needs coordinate transform evidence')
        t=m['transform']
        if t is not None:
            a=t['matrix_to_local_m']
            if a[3]!=[0,0,0,1]:raise ValueError('Transform must be affine')
            cols=[[a[i][j] for i in range(3)] for j in range(3)]
            lengths=[math.sqrt(sum(v*v for v in c)) for c in cols]
            if min(lengths)<=0 or max(lengths)-min(lengths)>1e-6*max(lengths):raise ValueError('Transform must have uniform scale')
            if any(abs(sum(x*y for x,y in zip(cols[i],cols[j])))>1e-6*lengths[i]*lengths[j] for i,j in [(0,1),(0,2),(1,2)]):raise ValueError('Transform axes not orthogonal')
            if abs(lengths[0]-t['metres_per_source_unit'])>1e-6*lengths[0]:raise ValueError('Unit scale conflicts with transform')
            if len(t['anchor_ids'])<3 or len(t['anchor_ids'])!=len(set(t['anchor_ids'])):raise ValueError('At least three distinct anchor records required; non-collinearity must be reviewed')
    maps={'image':{x['image_id']:x for x in spec['evidence']['images']},'fact':{x['fact_id']:x for x in spec['evidence']['facts']},'model':models}
    seen=set()
    def refs(items):
        if not items:raise ValueError('Binding needs evidence references')
        for ref in items:
            if ref['id'] not in maps[ref['kind']]:raise ValueError('Dangling parameter evidence')
            if ref['kind']=='model':
                if models[ref['id']]['status']!='checked' or not ref['node_id']:raise ValueError('Model measurement needs checked model and node ID')
            elif ref['node_id'] is not None:raise ValueError('Only model evidence has node_id')
    for b in r['parameter_bindings']:
        cid=b['component_id'];key=(cid,b['parameter_path'])
        if cid not in cm or key in seen:raise ValueError('Duplicate/dangling parameter binding')
        seen.add(key)
        try:value=resolve(cm[cid]['parameters'],b['parameter_path'])
        except (KeyError,IndexError,TypeError) as ex:raise ValueError('Invalid parameter path') from ex
        if value!=b['adopted_value']:raise ValueError('Adopted value differs from executed parameter')
        if b['status']=='conflicted':raise ValueError('Unresolved evidence conflict blocks execution')
        refs(b['evidence_refs'])
        if b['status'] in ('observed','resolved'):
            for ref in b['evidence_refs']:
                item=maps[ref['kind']][ref['id']]
                if ref['kind']=='image' and item.get('verification_state')!='full_image_viewed':raise ValueError('Observation requires actually viewed image')
                if ref['kind']=='fact' and item.get('status')!='verified':raise ValueError('Observation requires verified fact')
        for alt in b['alternatives']:refs(alt['evidence_refs'])
    assembly=spec['assembly'];meta=assembly['components'];ids=[x['component_id'] for x in meta]
    if len(ids)!=len(set(ids)) or set(ids)!=set(cm):raise ValueError('Assembly must map each executable component exactly once')
    parents={x['component_id']:x['parent_id'] for x in meta}
    for cid,parent in parents.items():
        seen={cid}
        while parent is not None:
            if parent not in parents or parent in seen:raise ValueError('Invalid parent hierarchy')
            seen.add(parent);parent=parents[parent]
    order={c['component_id']:i for i,c in enumerate(spec['components'])};pairs=set()
    for o in assembly['allowed_overlaps']:
        key=(o['earlier'],o['later'])
        if key in pairs or any(i not in cm for i in key) or order[key[0]]>=order[key[1]]:raise ValueError('Invalid overlap authorization')
        pairs.add(key)
    return {'parameter_bindings':len(r['parameter_bindings']),'models':len(models),'model_status':r['model_status'],'automatic_fusion':False}
