"""Read-only baseline and regression verification; write only a new report file."""
from pathlib import Path
import json,sys,hashlib,importlib.util,subprocess,gc
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(ROOT/'tools')]
from review_case import review_case
from vendor.inspect_build import load_build,Limits

def main():
 reg=json.loads((ROOT/'learning/case_registry.json').read_text());result={'engine':'HAF 0.4.0','date':'2026-10-27','checks':[],'game_status':'pending','scope':'No building redesign or new building generation; preserved NBT readbacks, entry imports, unit tests and historical negative controls'}
 def add(id,ok,detail):
  result['checks'].append({'id':id,'pass':bool(ok),'detail':detail});print(id,ok,flush=True)
 for c in reg['cases']:
  if c['kind']!='current':continue
  p=ROOT/c['nbt_path'];h=hashlib.sha256(p.read_bytes()).hexdigest()
  b=load_build(p,Limits(cells=64_000_000,nodes=64_000_000));info={'sha256':h,'nonair':len(b.blocks),'size_xyz':b.size};del b;gc.collect()
  add(c['case_id']+'_preserved_readback',h==c['nbt_sha256'],info)
  proc=subprocess.run([sys.executable,str(ROOT/c['entrypoint']),'--help'],capture_output=True,text=True,cwd=ROOT)
  add(c['case_id']+'_entry_import',proc.returncode==0,{'exit_code':proc.returncode,'error':proc.stderr[-2000:]})
 pairs=[]
 for cid,old,new in [('guangzhou_memorial','V1_r03','V2_r02'),('guangzhou_south','V1_r01','V1_r02')]:
  a=review_case(cid,old);b=review_case(cid,new)
  add(cid+'_shared_contract_negative_control',a['geometry_status']=='fail' and b['geometry_status']=='pass',{'before':a['geometry_checks'],'after':b['geometry_checks']})
  pairs.extend([a,b]);gc.collect()
 result['review_pairs']=pairs
 path=ROOT/'cases/guangzhou_memorial/src/validate_repairs.py';spec=importlib.util.spec_from_file_location('memorial_repairs',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 before=mod.review(*mod.read('V1_r03'));after=mod.review(*mod.read('V2_r02'))
 add('memorial_original_eight_checks',all(x['pass'] for x in after) and all(not x['pass'] for x in before),{'before':before,'after':after})
 imported=json.loads((ROOT/'release/imported_files.json').read_text());changed=[];count=0
 for rel,d in imported.items():
  if '/runs/' in rel:
   count+=1
   if not (ROOT/rel).exists() or hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=d['sha256']:changed.append(rel)
 add('all_imported_run_files_unchanged',not changed,{'checked_files':count,'changed':changed})
 add('lesson_evidence_paths_exist',all((ROOT/f).exists() for c in reg['cases'] for f in c['evidence']),{'buildings':len(reg['cases']),'adapters':len([x for x in reg['cases'] if x['kind']=='current'])})
 civic_old=review_case('civic_center','v03_r15_ceiling_landscape');civic_new=review_case('civic_center','v03_r16_ceiling_landscape')
 add('civic_R15_negative_and_R16_50_checks',civic_old['geometry_status']=='fail' and civic_new['geometry_status']=='pass' and len(civic_new['geometry_checks'])==50,{'before':civic_old,'after':civic_new})
 imported=json.loads((ROOT/'release/civic_imported_run_files.json').read_text());changed=[rel for rel,d in imported.items() if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=d['sha256']]
 add('all_civic_run_files_unchanged',not changed,{'checked_files':len(imported),'changed':changed})
 lab=ROOT/'research/interior_decoration/library_cafe_rev04.nbt';record=json.loads(lab.with_suffix('.recorded_report.json').read_text());lb=load_build(lab,Limits(cells=64000000,nodes=64000000))
 add('library_lab_preserved_readback',hashlib.sha256(lab.read_bytes()).hexdigest()==record['sha256'] and sum(v.split('[')[0] not in {'minecraft:air','minecraft:cave_air','minecraft:void_air'} for v in lb.blocks.values())==record['non_air'] and list(lb.size)==record['size'],{'sha256':hashlib.sha256(lab.read_bytes()).hexdigest(),'stored_records':len(lb.blocks),'nonair':sum(v.split('[')[0] not in {'minecraft:air','minecraft:cave_air','minecraft:void_air'} for v in lb.blocks.values()),'size':lb.size,'game':'pending','scope':'Independent file readback; original geometric claims not rerun'})
 from hafusion.design_handoff import compile_handoff
 for ex in ['library','civic-scope']:
  plan=compile_handoff(json.loads((ROOT/('examples/handoff/'+ex+'.json')).read_text()))
  add('handoff_'+ex,plan['generated_geometry']==False and plan['game_status']=='pending',{'status':plan['status'],'coverage':plan['lighting_coverage_policy'],'pending':plan['pending']})
 result['passed']=sum(x['pass'] for x in result['checks']);result['failed']=len(result['checks'])-result['passed']
 target=ROOT/'release/haf04_release_validation.json'
 if target.exists():raise ValueError('Refusing to overwrite existing release validation')
 target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result['failed']
if __name__=='__main__':raise SystemExit(bool(main()))
