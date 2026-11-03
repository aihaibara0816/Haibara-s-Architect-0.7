"""Explicit v0.1 -> v0.2 migration; retain baseline geometry and observed overlaps."""
from pathlib import Path
import copy,json,sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.spec_loader import load_spec,validate_spec
from architect.geometry import generate

def migrate(spec):
    validate_spec(spec)
    if spec['schema_version']!='0.1':raise ValueError('Expected v0.1 input')
    scene,report=generate(spec);p=copy.deepcopy(spec);p['schema_version']='0.2'
    p['research']={'model_status':'not_requested','models':[],'parameter_bindings':[],'reference_set':None}
    p['assembly']={'components':[{'component_id':c['component_id'],'parent_id':None,'role':c['kind']} for c in p['components']], 'allowed_overlaps':[{'earlier':x['earlier'],'later':x['later'],'reason':'Existing v0.1 baseline overlap retained during migration; not a structural engineering approval.'} for x in report['overlaps']], 'overlap_policy':'reject_undeclared'}
    validate_spec(p)
    if generate(p)[0].fingerprint()!=scene.fingerprint():raise ValueError('Migration changed geometry')
    return p
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');a=ap.parse_args()
    p=Path(a.output)
    with p.open('x',encoding='utf8') as f:json.dump(migrate(load_spec(a.input)),f,ensure_ascii=False,indent=2)
