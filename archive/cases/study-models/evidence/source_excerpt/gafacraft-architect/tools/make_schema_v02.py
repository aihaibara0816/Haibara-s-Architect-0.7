"""Add a strict, versioned contract while leaving the v0.1 schema immutable."""
from pathlib import Path
import json
from make_schema import obj,arr,enum,ref,text,id_type,ids,string_or_null
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'schema/building_spec.schema.json').read_text())
s['$id']='urn:gafacraft:architect:building-spec:0.2';s['title']='BuildingSpec v0.2';s['properties']['schema_version']={'const':'0.2'}
nullable_id={'oneOf':[id_type,{'type':'null'}]}
eref=obj({'kind':enum('image','fact','model'),'id':id_type,'node_id':string_or_null})
transform=obj({'metres_per_source_unit':{'type':'number','exclusiveMinimum':0},'source_axes':text,'matrix_to_local_m':arr(arr({'type':'number'},minItems=4,maxItems=4),minItems=4,maxItems=4),'anchor_ids':arr(text,minItems=3,uniqueItems=True),'residual_m':{'type':'number','minimum':0},'basis':text})
model=obj({'model_id':id_type,'sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'format':text,'source_id':nullable_id,'license_status':enum('unknown','permission_granted','licensed','public_domain','restricted'),'version':string_or_null,'status':enum('candidate','checked','rejected'),'transform':{'oneOf':[{'type':'null'},transform]}})
binding=obj({'component_id':id_type,'parameter_path':text,'adopted_value':{},'status':enum('observed','estimated','design_choice','resolved','conflicted'),'basis':text,'evidence_refs':arr(eref,minItems=1),'alternatives':arr(obj({'value':{},'evidence_refs':arr(eref,minItems=1),'reason_not_adopted':text}))})
s['properties']['research']=obj({'model_status':enum('not_requested','not_found','available'),'models':arr(model),'parameter_bindings':arr(binding),'reference_set':{'type':['object','null']}})
s['properties']['research']['required'].remove('reference_set')
s['properties']['assembly']=obj({'components':arr(obj({'component_id':id_type,'parent_id':nullable_id,'role':text})),'allowed_overlaps':arr(obj({'earlier':id_type,'later':id_type,'reason':text})),'overlap_policy':enum('report','reject_undeclared')})
s['required']+=['research','assembly']
(root/'schema/building_spec_v0.2.schema.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
