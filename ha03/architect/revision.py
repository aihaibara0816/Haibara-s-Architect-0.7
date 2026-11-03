"""Guard full-regeneration edits with explicit parameter paths and voxel regions."""
from .spec_loader import validate_spec
from .geometry import generate
from .research_contract import resolve

def changed_paths(a,b,path=''):
    if type(a)!=type(b):return {path}
    if isinstance(a,dict):
        out=set()
        for k in set(a)|set(b):
            p=path+'/'+k.replace('~','~0').replace('/','~1')
            out|={p} if k not in a or k not in b else changed_paths(a[k],b[k],p)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return {path}
        return set().union(*(changed_paths(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))))
    return set() if a==b else {path}

def guard_revision(before,after,request):
    validate_spec(before);validate_spec(after)
    if before['spec_id']!=after['spec_id'] or after['revision']<=before['revision']:raise ValueError('Revision identity must advance')
    cm={c['component_id']:c for c in before['components']};dm={c['component_id']:c for c in after['components']}
    if list(cm)!=list(dm):raise ValueError('This editor preserves component identities and order')
    allowed=request['allowed_parameter_paths']
    if not allowed or not set(allowed)<=set(cm):raise ValueError('Unknown editable component')
    for cid,paths in allowed.items():
        if not paths or len(paths)!=len(set(paths)):raise ValueError('Explicit unique parameter paths required')
        for path in paths:resolve(cm[cid]['parameters'],path);resolve(dm[cid]['parameters'],path)
    # All global data remains locked except revision and parameter bindings.
    a={k:v for k,v in before.items() if k not in ('components','revision','research')}
    b={k:v for k,v in after.items() if k not in ('components','revision','research')}
    if a!=b:raise ValueError('Locked global fields changed')
    if before.get('research')!=after.get('research'):
        import copy
        ra=copy.deepcopy(before.get('research'));rb=copy.deepcopy(after.get('research'))
        if not ra or not rb:raise ValueError('Research version cannot change during edit')
        ba=ra.pop('parameter_bindings');bb=rb.pop('parameter_bindings')
        if ra!=rb or len(ba)!=len(bb):raise ValueError('Model/evidence set changed during edit')
        for x,y in zip(ba,bb):
            key=(x['component_id'],x['parameter_path'])
            if key[1] not in allowed.get(key[0],[]):
                if x!=y:raise ValueError('Unrelated binding changed')
            else:
                x={k:v for k,v in x.items() if k not in ('adopted_value','basis')}
                y={k:v for k,v in y.items() if k not in ('adopted_value','basis')}
                if x!=y:raise ValueError('Evidence refs changed during edit')
    for cid in cm:
        a={k:v for k,v in cm[cid].items() if k!='parameters'};b={k:v for k,v in dm[cid].items() if k!='parameters'}
        if a!=b:raise ValueError('Component metadata changed outside permitted parameters')
        actual=changed_paths(cm[cid]['parameters'],dm[cid]['parameters'])
        if not actual<=set(allowed.get(cid,[])):raise ValueError('Unexpected parameter change: '+cid+str(actual))
    scene1,_=generate(before);scene2,_=generate(after)
    changed={p for p in set(scene1.blocks)|set(scene2.blocks) if (scene1.blocks.get(p),scene1.owners.get(p))!=(scene2.blocks.get(p),scene2.owners.get(p))}
    def region(box):
        if not isinstance(box,list) or len(box)!=6 or any(type(x)is not int for x in box) or any(box[i]>box[i+3] for i in range(3)):raise ValueError('Invalid inclusive region')
        return lambda p:all(box[i]<=p[i]<=box[i+3] for i in range(3))
    inside=region(request['allowed_region']);protected=[region(x) for x in request['protected_regions']]
    outside=[p for p in changed if not inside(p)];protected_hits=[p for p in changed if any(f(p) for f in protected)]
    if outside or protected_hits:raise ValueError('Voxel edit escaped requested/protected region')
    owners=sorted({s.owners[p] for p in changed for s in (scene1,scene2) if p in s.owners})
    if not set(owners)<=set(request['allowed_changed_components']):raise ValueError('Unexpected dependent component change')
    return {'status':'pass','changed_cells':len(changed),'changes_outside_region':0,'protected_changes':0,'changed_components':owners,'before_geometry':scene1.fingerprint(),'after_geometry':scene2.fingerprint(),'execution':'full_regeneration','dependency_rebuild':'not_implemented'}
