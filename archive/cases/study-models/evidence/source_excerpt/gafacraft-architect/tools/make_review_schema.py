from pathlib import Path
import json
from make_schema import obj,arr,text,id_type,ids,enum
r=Path(__file__).resolve().parents[1]
pair=obj({'pair_id':id_type,'image_id':id_type,'component_ids':arr(id_type,minItems=1,uniqueItems=True),'view':enum('front','back','left','right','iso45'),'camera_match':enum('matched','approximate','unverifiable'),'status':enum('pass','needs_revision','unverifiable','pending'),'severity':enum('major','minor',None),'finding':text,'checkpoints':arr(text,minItems=1)})
s=obj({'schema_version':{'const':'0.1'},'build_id':text,'method':{'const':'manual'},'game_status':{'const':'pending_game_test'},'required_image_ids':ids,'pairs':arr(pair)})
s['$schema']='https://json-schema.org/draft/2020-12/schema'
(r/'schema/reference_review.schema.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
