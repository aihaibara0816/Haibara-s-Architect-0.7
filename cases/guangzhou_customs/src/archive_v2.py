"""Package final V2 and auditable source without generated mesh caches."""
from pathlib import Path
import json,zipfile,hashlib,shutil
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1];RUN='V2_r06';OUT=ROOT/'deliverables/guangzhou_customs_v2';STEM='Guangzhou_Customs_HAF_V2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
history=[
 {'run':'V2_r01','status':'internal','change':'中央分段、柱廊、裙楼分区首轮；非最终采用'},
 {'run':'V2_r02','status':'rejected','change':'侧面5列窗、栏杆降高；检查发现旧楼梯穿后墙、窗和灯被覆盖','evidence':'runs/V2_r02/validation_v2.json'},
 {'run':'V2_r03','status':'superseded','change':'内部楼梯迁移、灯位后分配、去除被檐口占据的4个窗登记'},
 {'run':'V2_r04','status':'superseded','change':'两侧照片对应后，将拱门移至独立-X侧；突出翼改相对位置'},
 {'run':'V2_r05','status':'superseded','change':'旧绿化清除移至台阶施工之前'},
 {'run':RUN,'status':'delivered_for_visual_review','change':'补齐侧台阶与门之间连续平台；19项案例检查及27视角'}]
dump(CASE/'history/v2_revisions.json',history)
baseline=ROOT.parent.parent/'customs_feedback_audit/Guangzhou_Customs_HAF_V1_Source.zip'
proof={'baseline_archive_sha256':sha(baseline),'v1_nbt_sha256':sha(CASE/'runs/V1_r04/building.nbt'),'shared_core_unchanged':True,'files':[]}
with zipfile.ZipFile(baseline) as z:
 for n in z.namelist():
  rel=Path(n).parts[1:]
  if not rel:continue
  path=Path(*rel)
  if path.parts[0] in ('hafusion','support','tests') and (ROOT/path).is_file() or str(path) in ('cases/guangzhou_customs/src/build_case.py','cases/guangzhou_customs/params.json'):
   ok=hashlib.sha256(z.read(n)).hexdigest()==sha(ROOT/path);proof['files'].append({'file':str(path),'unchanged':ok});proof['shared_core_unchanged'] &= ok
assert proof['shared_core_unchanged'] and proof['files']
dump(CASE/'validation/v2_preservation.json',proof)
with zipfile.ZipFile(OUT/(STEM+'_Build.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted((CASE/'runs'/RUN/'import_pack').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(CASE/'runs'/RUN/'import_pack'))
 for p in [CASE/'README_V2.md',CASE/'runs'/RUN/'validation_v2.json',CASE/'runs'/RUN/'manifest.json']:
  z.write(p,p.name)
# Keep reproducible source, V1/final run, research, and intermediate decisions.
with zipfile.ZipFile(OUT/(STEM+'_Source.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT);parts=rel.parts
  if any(x in parts for x in ('__pycache__','.git','deliverables','scene','node_modules')):continue
  if p.suffix in ('.pyc','.log') and 'validation' not in parts:continue
  if 'review' in parts and 'previews' in parts:
   lab=parts[parts.index('previews')+1]
   if lab not in ('V1_r04','V1_compare_extra',RUN):continue
  if 'runs' in parts:
   lab=parts[parts.index('runs')+1]
   if lab not in ('V1_r04',RUN) and p.suffix not in ('.json','.py'):continue
  z.write(p,Path('HAF_Guangzhou_Customs_V2')/rel)
with zipfile.ZipFile(OUT/(STEM+'_Source.zip')) as z:assert z.testzip() is None
report={'run':RUN,'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix!='.json'],'v1_preserved':True,'core_files_compared':len(proof['files']),'core_unchanged':True}
dump(OUT/(STEM+'_Delivery.json'),report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':pass
