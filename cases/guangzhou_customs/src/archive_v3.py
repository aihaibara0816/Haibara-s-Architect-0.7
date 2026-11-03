"""Archive V3 with reproducible source, baseline files and exact rendered views."""
from pathlib import Path
import json,zipfile,hashlib,shutil
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1];RUN='V3_r02'
OUT=ROOT/'deliverables/guangzhou_customs_v3';STEM='Guangzhou_Customs_HAF_V3'
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=json.loads((CASE/'runs'/RUN/'validation_v3.json').read_text());assert checks['all_passed']
assert json.loads((CASE/'validation/ui_v3.json').read_text())['passed']
baseline=json.loads((CASE/'research/v3/baseline_hashes.json').read_text());assert all(sha(ROOT/p)==h for p,h in baseline.items())
dump(CASE/'history/v3_revisions.json',[
 {'run':'V2_r06','fidelity_status':'needs_revision','feedback':'用户否定单侧后伸翼；斜卫星屋顶位移不能直接解释为地面轮廓'},
 {'run':'V3_r01','status':'internal_superseded','change':'倒T裙楼、后部中轴入口、中央体后墙收进；检查发现中央窄窗被旧边界条件跳过、后门内挖范围过宽'},
 {'run':RUN,'status':'delivered_for_review','change':'补5列中央窄窗；保留三拱间实墙；最终23项案例技术检查通过，视觉待用户确认'}])
dump(CASE/'research/v3/visual_review.json',{'run':RUN,'inspected':['top','plan_25','podium_oblique','se_day','sw_day','ne_day','nw_day','front','rear','crown_rear','ne_night','entrance','plan_65'],'observed':'单侧突出消除，倒T与两侧退台可见；后门三拱、两座玻璃房与承托面连续。钟冠保留。','fidelity_status':'pending user review','limits':['后门位置推定','绝对方位未核','屋顶配色代理','钟面细节符号化'],'game':'not tested','preview_repair':'完整night.png第一次批量导出后发现为空，单独重渲染；打包前27张已解码并核SHA'})
dump(ROOT/'learning/guangzhou_customs_v3.json',{'case':'guangzhou_customs','negative_example':'V2 readback/tests passed but footprint rejected','rule':'分开地面、裙楼、高层屋顶的轮廓；斜影像的高度位移不是地面突出。先复核拓扑，再调整细节。','implementation':'cases/guangzhou_customs/src/build_v3.py','validation':'23 case checks + final NBT views; no game test','scope':'one case; not a trained general model','next':'用户复核倒T、后门方向和收窄程度；有测绘图再调整尺寸'})
dump(CASE/'validation/shared_tests_v3.json',{'command':'python3 -m unittest discover -s tests -v','passed':23,'failed':0,'date':'2026-10-24','scope':'existing HAF test suite; executed this V3 task'})
with zipfile.ZipFile(OUT/(STEM+'_Build.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted((CASE/'runs'/RUN/'import_pack').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(CASE/'runs'/RUN/'import_pack'))
 for p in [CASE/'README_V3.md',CASE/'runs'/RUN/'manifest.json',CASE/'runs'/RUN/'validation_v3.json']:
  z.write(p,p.name)
with zipfile.ZipFile(OUT/(STEM+'_Source.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT);parts=rel.parts
  if any(x in parts for x in ('__pycache__','.git','deliverables','scene','node_modules')):continue
  if p.suffix=='.pyc':continue
  if 'runs' in parts:
   label=parts[parts.index('runs')+1]
   if label not in ('V1_r04','V2_r06',RUN) and p.suffix not in ('.json','.py'):continue
  if 'review' in parts and 'previews' in parts:
   label=parts[parts.index('previews')+1]
   if label not in ('V1_r04','V1_compare_extra','V2_r06',RUN):continue
  z.write(p,Path('HAF_Guangzhou_Customs_V3')/rel)
for name in ('Build','Source'):
 with zipfile.ZipFile(OUT/(STEM+'_'+name+'.zip')) as z:assert z.testzip() is None
dump(OUT/(STEM+'_Delivery.json'),{'run':RUN,'source_nbt_sha256':sha(CASE/'runs'/RUN/'building.nbt'),'files':[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix!='.json'],'preserved_files':len(baseline),'V1_V2_unchanged':True,'case_checks':checks['passed'],'shared_tests':23,'game':'not tested','visual_acceptance':'pending'})
print(json.dumps({'run':RUN,'files':[{ 'name':p.name,'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file()]},ensure_ascii=False))
