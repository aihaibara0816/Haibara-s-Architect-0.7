"""Portable Nanshan Cloud source kit and game import pack."""
from pathlib import Path
import hashlib,json,zipfile
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
OUT=ROOT/'deliverables/nanshan_cloud_v1';STEM='Nanshan_Cloud_HAF_V1'
def main():
    OUT.mkdir(parents=True,exist_ok=True);run=CASE/'runs/V1_r04'
    with zipfile.ZipFile(OUT/(STEM+'_Build.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted((run/'import_pack').rglob('*')):
            if f.is_file():z.write(f,STEM+'/'+str(f.relative_to(run/'import_pack')))
        for f in sorted((CASE/'review/previews/V1_r04').glob('*.png')):z.write(f,STEM+'/previews/'+f.name)
        for f,name in [(run/'manifest.json','build_manifest.json'),(CASE/'validation/acceptance.json','validation.json'),(CASE/'review/feedback_template.json','feedback_template.json'),(CASE/'README.md','README.md')]:z.write(f,STEM+'/'+name)
    files=[]
    for sub in ['hafusion','support/vendor','support/detail_lab']:
        files.extend(f for f in (ROOT/sub).rglob('*.py') if '__pycache__' not in f.parts)
    files.extend(f for f in (ROOT/'tests').glob('*.py') if f.name!='test_hafusion.py')
    for name in ['AGENTS.md','docs/HAF_0.2.md','docs/haf_0_2_capabilities.json','learning/nanshan_cloud_v1.json','tools/agent.py','tools/render_building_case.py','tools/package_building_case.py','cases/namsan_tower/src/render_egl_site.py','cases/guangzhou_ctf/research/detail_study_v2/vanilla/template_anvil.json','cases/guangzhou_ctf/research/vanilla/template_wall_post.json','cases/guangzhou_ctf/research/vanilla/template_wall_side.json','upstream/PlanCraft/LICENSE']:
        files.append(ROOT/name)
    files.extend(f for f in (ROOT/'history/before_nanshan_cloud').rglob('*') if f.is_file())
    for f in CASE.rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(CASE)
        if any(v in rel.parts for v in ['__pycache__','images','raw','scene']):continue
        if f.suffix=='.bin':continue
        files.append(f)
    config=json.loads((ROOT/'agent_config.json').read_text());synthetic={'history/full_agent_config_at_delivery.json':json.dumps(config,ensure_ascii=False,indent=2).encode()}
    config['cases']={'nanshan_cloud':config['cases']['nanshan_cloud']};config['default_case']='nanshan_cloud'
    synthetic['agent_config.json']=json.dumps(config,ensure_ascii=False,indent=2).encode()
    synthetic['requirements-case.txt']=b'numpy\nPillow\n'
    synthetic['README_CASE_KIT.txt']='''HAF 0.2 / Nanshan Cloud V1 case kit

Delivery baseline V1_r04. Historical r01/r02/r03 and exact replay are retained.
This kit contains the new case and required shared code, not every old project.
The original HAF tree and previous case outputs have not been replaced.
The local registry is narrowed to nanshan_cloud; the full registry is in history.
Some preserved older shared modules and the broad control catalog need historical
project fixtures and are not claimed runnable from this reduced case kit.

Python 3.12, numpy, Pillow. Generation needs no network.
Linux rendering additionally needs EGL/Mesa; avoid parallel mesh/export jobs
on low-memory hosts. Generated mesh caches are intentionally excluded.

python3 tools/agent.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/render_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/package_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 cases/nanshan_cloud/src/validate_case.py
python3 -m unittest discover -s tests -v

The full tree passed 30 unit tests. This portable kit includes 20 relevant tests;
test_hafusion.py requires old Canton/HA0.3 integration fixtures and is excluded.
Case checks validate saved V1_r04, V1_replay and final source-bound previews.
The unchanged miniature vanilla shape fixtures retain their Mojang provenance.
No Minecraft client, resource pack, or original reference-photo archive included.
Existing third-party notices are retained where bundled; no new blanket license
is asserted for upstream materials.

Research contains URL/hash/viewing-status/evidence records. The source kit omits
raw third-party HTML/photos; make_review.py still runs with source links when
reference photos are absent. The standalone review delivered with this case
contains two attributed reference images and 13 actual model previews.
Feedback is initially empty. Learning files are construction/evaluation notes,
not evidence that a neural model was trained or arbitrary buildings solved.

Important limits: all previews are untextured NBT meshes, not game screenshots.
Actual north, third tower height, hidden interfaces, office floorplans, landscape
and night-light calibration remain approximate. Game import/lighting/navigation
are pending. Do not treat this V1 as a surveyed model or automatic SU fusion.
'''.encode()
    manifest=[];prefix='HAF_Nanshan_Cloud_V1/'
    with zipfile.ZipFile(OUT/(STEM+'_Source.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(set(files)):
            rel=str(f.relative_to(ROOT));raw=f.read_bytes();z.writestr(prefix+rel,raw);manifest.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        for rel,raw in synthetic.items():z.writestr(prefix+rel,raw);manifest.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        z.writestr(prefix+'FILE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    records=[]
    for f in sorted(OUT.iterdir()):
        if f.is_file() and f.name!='delivery_manifest.json':records.append({'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    (OUT/'delivery_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps({'source_files':len(manifest),'outputs':records},ensure_ascii=False))
if __name__=='__main__':main()
