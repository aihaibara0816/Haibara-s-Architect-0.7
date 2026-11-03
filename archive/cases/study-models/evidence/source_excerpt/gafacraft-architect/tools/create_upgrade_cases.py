"""Migrate existing specimens; no new architectural design or fabricated observations."""
import sys,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.legacy import ROOT
from architect.spec_loader import load_spec
from architect.geometry import generate
from migrate_spec import migrate

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

def main():
    out=ROOT/'examples/upgrade'
    reports=[]
    for name in ['retail_store','retail_store_revision','tower_segment','legacy_gafa_colonnade']:
        old=load_spec(ROOT/'output'/name/'building_spec.json');new=migrate(old)
        dump(out/name/'building_spec.json',new)
        reports.append({'case':name,'geometry_unchanged':generate(old)[0].fingerprint()==generate(new)[0].fingerprint(),'sha256':generate(new)[0].fingerprint()})
    before=load_spec(out/'retail_store/building_spec.json');after=copy.deepcopy(before);after['revision']=2
    next(c for c in after['components'] if c['component_id']=='canopy')['parameters']['min_m'][2]=2
    dump(out/'retail_edit.json',after)
    dump(out/'revision_request.json',{'allowed_parameter_paths':{'canopy':['/min_m/2']},'allowed_region':[14,6,2,19,6,5],'protected_regions':[[0,0,6,33,11,25]],'allowed_changed_components':['canopy']})
    # Prior user photo is real; camera mismatch remains explicit, no new inspection claimed.
    root=ROOT/'output/legacy_gafa_colonnade';spec=load_spec(root/'building_spec.json');br=json.loads((root/'build_report.json').read_text());iid=spec['evidence']['images'][0]['image_id']
    comps=[c['component_id'] for c in spec['components'] if 'column' in c['component_id']]
    if not comps:comps=[spec['components'][0]['component_id']]
    dump(out/'legacy_review.json',{'schema_version':'0.1','build_id':br['build_id'],'method':'manual','game_status':'pending_game_test','required_image_ids':[iid],'pairs':[{'pair_id':'legacy-photo-review','image_id':iid,'component_ids':comps,'view':'front','camera_match':'unverifiable','status':'unverifiable','severity':None,'finding':'旧照片仅支持局部柱列观察；实际拍摄机位和方块正交视图未标定，不能声称完成精确外观验收。此条为原资料限制的结构化登记。','checkpoints':['柱列节奏','投影差异','范围覆盖']}]})
    dump(ROOT/'reports/upgrade_migration.json',reports)
    print(json.dumps(reports,ensure_ascii=False))
if __name__=='__main__':main()
