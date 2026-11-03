"""Portable snapshot based on released V1, replacing only actual updated source."""
from pathlib import Path
import zipfile,json,hashlib
ROOT=Path(__file__).resolve().parent;CASE=ROOT.parents[1];HAF=CASE.parents[1];DEST=ROOT/'deliverables'
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 src=CASE/'deliverables/HAF_CTF_V1_Source.zip';files={}
 with zipfile.ZipFile(src) as old:
  for name in old.namelist():
   if not name.startswith('HAF_Mainline/') or name.endswith('/'):continue
   rel=name.removeprefix('HAF_Mainline/')
   if rel in ['SOURCE_INVENTORY.json','ARCHIVE_SCOPE.txt']:continue
   path=HAF/rel;files[rel]=path if path.is_file() else old.read(name)
  rel='support/vendor/render_egl.py';saved=ROOT/'baseline_source'/rel
  if not saved.exists():saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(old.read('HAF_Mainline/'+rel))
 for scope in [ROOT,CASE/'research/detail_study_v2']:
  for p in scope.rglob('*'):
   if not p.is_file():continue
   parts=p.relative_to(HAF).parts
   if any(v in parts for v in ['__pycache__','scene','deliverables']):continue
   if p.name in ['lpa_page.html','review_script.js','archive_validation.json']:continue
   files[str(p.relative_to(HAF))]=p
 for rel in ['hafusion/interiors.py','support/detail_lab/shading.py','tests/test_detail_feedback.py','learning/ctf_night_detail_study.md']:
  files[rel]=HAF/rel
 inventory=[];target=DEST/'HAF_CTF_Detail_Study_Source.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for rel,entry in sorted(files.items()):
   data=entry.read_bytes() if isinstance(entry,Path) else entry
   z.writestr('HAF_Mainline/'+rel,data);inventory.append({'path':rel,'bytes':len(data),'sha256':digest(data)})
  z.writestr('HAF_Mainline/SOURCE_INVENTORY.json',json.dumps(inventory,ensure_ascii=False,indent=2))
  z.writestr('HAF_Mainline/ARCHIVE_SCOPE.txt','HAF + preserved CTF V1 and Shenzhen V2 baseline, current detail-study code, official model excerpts, sources, actual NBT samples, accepted/rejected experiments and renders. Excludes meshes/caches and duplicate deliverables. V1 original files are preserved; newer source is a local study, not an accepted V2 release. SketchUp/Sketchfab mesh NOT included or imported. Skills are saved separately through Skills git; this is not a skill installation ZIP. Photo copyright remains with original rights holders.\n')
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 (ROOT/'archive_validation.json').write_text(json.dumps({'file':target.name,'sha256':digest(target.read_bytes()),'members':len(inventory),'bytes':target.stat().st_size,'zip_crc':'pass'},indent=2))
 print(target.name,len(inventory),target.stat().st_size)
if __name__=='__main__':main()
