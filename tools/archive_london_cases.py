"""Persistable London case kit; no generated mesh caches or source-photo copies."""
from pathlib import Path
import hashlib,json,zipfile,shutil
from document_london_cases import DATA
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/london_v1'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for key,d in DATA.items():
    c=ROOT/'cases'/key;run=c/'runs/V1_r02';out=OUT/(d['stem']+'_Build.zip')
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
      for p in sorted((run/'import_pack').rglob('*')):
        if p.is_file():z.write(p,d['stem']+'/'+str(p.relative_to(run/'import_pack')))
      for p in sorted((c/'review/previews/V1_r02').glob('*.png')):z.write(p,d['stem']+'/previews/'+p.name)
      z.write(c/'validation/acceptance.json',d['stem']+'/validation.json')
      z.write(run/'manifest.json',d['stem']+'/build_manifest.json')
 files=[]
 for sub in ['hafusion','support/vendor','support/detail_lab']:
    files.extend(p for p in (ROOT/sub).rglob('*.py') if '__pycache__' not in p.parts)
 for p in (ROOT/'tests').glob('*.py'):
    if p.name!='test_hafusion.py':files.append(p)
 # Saved Mojang model fixtures used by the unchanged wall/anvil unit checks.
 files.extend(ROOT/p for p in ['cases/guangzhou_ctf/research/detail_study_v2/vanilla/template_anvil.json','cases/guangzhou_ctf/research/vanilla/template_wall_post.json','cases/guangzhou_ctf/research/vanilla/template_wall_side.json'])
 files.extend(ROOT/'tools'/n for n in ['agent.py','render_building_case.py','package_building_case.py','document_london_cases.py','validate_london_cases.py','make_london_review.py','archive_london_cases.py'])
 files.extend(ROOT/p for p in ['AGENTS.md','docs/HAF_0.2.md','docs/haf_0_2_capabilities.json','learning/london_western_v1.json','cases/namsan_tower/src/render_egl_site.py'])
 files.extend(p for p in (ROOT/'history/before_london_v1').rglob('*') if p.is_file())
 for key in DATA:
    case=ROOT/'cases'/key
    for p in case.rglob('*'):
      if not p.is_file():continue
      rel=p.relative_to(case)
      if any(v in rel.parts for v in ['__pycache__','deliverables','images']):continue
      if rel.parts[:2]==('research','raw') and p.name!='bp_osm.xml':continue
      if 'scene' in rel.parts or p.suffix=='.bin':continue
      files.append(p)
 source=OUT/'London_Western_HAF_V1_Source.zip';checks=[]
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    prefix='HAF_London_V1/'
    for p in sorted(set(files)):
      rel=str(p.relative_to(ROOT));z.write(p,prefix+rel);checks.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    config=json.loads((ROOT/'agent_config.json').read_text());z.writestr(prefix+'history/full_agent_config_at_delivery.json',json.dumps(config,ensure_ascii=False,indent=2))
    config['cases']={k:v for k,v in config['cases'].items() if k in DATA};config['default_case']='elizabeth_tower';z.writestr(prefix+'agent_config.json',json.dumps(config,ensure_ascii=False,indent=2))
    z.writestr(prefix+'requirements-london.txt','numpy\nPillow\n')
    z.writestr(prefix+'README_CASE_KIT.txt','''HAF 0.2 / London Western V1 / case kit

This kit contains both new London cases, their final and first runs, replay
files, evidence decisions, source snapshots and required shared modules.
It is a portable case extension, not a replacement for the complete historical
HAF release. The live HAF tree and all prior cases remain preserved.
The kit registry lists only these two cases. The original registry is copied
under history/full_agent_config_at_delivery.json. Some older HAF modules are
preserved for provenance and require the full historical tree to execute.

Python 3.12, numpy, Pillow. Offline renders need Linux EGL/Mesa.
From this directory:
 python3 tools/agent.py --case elizabeth_tower --run MY_NEW_RUN
 python3 tools/agent.py --case buckingham_palace --run MY_NEW_RUN
 python3 tools/render_building_case.py --case elizabeth_tower --run MY_NEW_RUN
 python3 tools/package_building_case.py --case elizabeth_tower --run MY_NEW_RUN
 python3 -m unittest discover -s tests -v
 python3 tools/validate_london_cases.py

All 30 tests passed in the full working tree. This portable kit excludes the
10 legacy integration tests in test_hafusion.py, whose fixtures depend on the
older Canton and HA0.3 distributions. The remaining 20 tests are included.
Case-level checks compare final files with preserved replay files and include
the NBT source hashes embedded in PNG previews. Missing game verification is
explicitly recorded in each case README and import guide.

Final baseline: V1_r02. V1_r01 is a preserved prototype, not another completed
building version. Its generator and helper snapshots are under that run.
Current generation uses each case src/build_case.py plus hafusion/classical.py.
Feedback templates are empty until the user enters actual feedback.

The rendered images have no Minecraft resource-pack textures. They are actual
state-box meshes from NBT, not photographs and not image-generation output.

Map data: copyright OpenStreetMap contributors, ODbL 1.0.
https://www.openstreetmap.org/copyright
https://opendatacommons.org/licenses/odbl/1-0/
Original map data and transformed plan are included. Source photos/PDFs are
not redistributed; URL/hash/viewing/decision records remain in research/.
The three saved vanilla shape fixtures retain their upstream Mojang origin.
This work does not distribute a Minecraft client or resource pack.
''')
    z.writestr(prefix+'FILE_MANIFEST.json',json.dumps(checks,ensure_ascii=False,indent=2))
 outputs=[]
 for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!='delivery_manifest.json':outputs.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (OUT/'delivery_manifest.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
 print(json.dumps({'source_members':len(files),'outputs':outputs},ensure_ascii=False))
if __name__=='__main__':main()
