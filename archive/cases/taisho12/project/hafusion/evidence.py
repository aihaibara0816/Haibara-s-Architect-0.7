"""Reviewed proposals to existing JSON contracts, without mutating inputs."""
import copy
from research_lab.evidence import arbitrate
from research_lab.stage_cache import digest
from .bootstrap import ROOT

def apply_reviewed(document, proposals, expected_hash, validator, allowed_paths):
    if digest(document) != expected_hash:
        raise ValueError('Stale baseline; re-review required')
    out=copy.deepcopy(document); seen=set()
    for p in proposals:
        path=p['path']
        if path not in allowed_paths or path in seen:
            raise ValueError('Undeclared or duplicate parameter path')
        seen.add(path)
        if p.get('review')!='accepted' or not p.get('reason') or not p.get('evidence'):
            raise ValueError('An explicit reviewed decision and evidence are required')
        if p.get('status') not in ('estimated','observed','confirmed'):
            raise ValueError('Unresolved evidence cannot be executed')
        parts=path.strip('/').split('/'); cur=out
        for t in parts[:-1]: cur=cur[int(t)] if isinstance(cur,list) else cur[t]
        key=int(parts[-1]) if isinstance(cur,list) else parts[-1]
        if cur[key]!=p['old']: raise ValueError('Old value differs from baseline')
        cur[key]=copy.deepcopy(p['new'])
    validator(out)
    return out

def apply_building_spec(spec, proposals, expected_hash):
    """Parameters AND binding values are validated by unchanged HA0.3 schema.

    Caller supplies reviewed evidence_refs already present in the source spec.
    This is for supported parameterized primitives, not arbitrary Canton meshes.
    """
    from architect.spec_loader import validate_spec
    out=copy.deepcopy(spec); changes=[]; allowed=set()
    for p in proposals:
        idx=next((i for i,c in enumerate(out['components']) if c['component_id']==p['component_id']),None)
        if idx is None: raise ValueError('Unknown component')
        pp='/components/'+str(idx)+'/parameters'+p['parameter_path']
        allowed.add(pp); changes.append({**p,'path':pp})
    out=apply_reviewed(out,changes,expected_hash,lambda _:None,allowed)
    for p in proposals:
        key=(p['component_id'],p['parameter_path'])
        binding={'component_id':key[0],'parameter_path':key[1], 'adopted_value':p['new'],
                 'status':p['status'], 'evidence_refs':p['evidence_refs'],
                 'alternatives':p.get('alternatives',[]),'basis':p['reason']}
        old=out['research']['parameter_bindings']
        out['research']['parameter_bindings']=[b for b in old if (b['component_id'],b['parameter_path'])!=key]+[binding]
    validate_spec(out)
    return out
