"""Portable source, preserved V1 baseline and new V2 game import package."""
from pathlib import Path
import hashlib,json,zipfile
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
OUT=ROOT/'deliverables/nanshan_cloud_v2';STEM='Nanshan_Cloud_HAF_V2'
def main():
    OUT.mkdir(parents=True,exist_ok=True);run=CASE/'runs/V2_r01'
    with zipfile.ZipFile(OUT/(STEM+'_Build.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted((run/'import_pack').rglob('*')):
            if f.is_file():z.write(f,STEM+'/'+str(f.relative_to(run/'import_pack')))
        for f in sorted((CASE/'review/previews/V2_r01').glob('*.png')):z.write(f,STEM+'/previews/'+f.name)
        for f,name in [(run/'manifest.json','build_manifest.json'),(CASE/'validation/v2/acceptance.json','validation.json'),(CASE/'review/feedback_template_v2.json','feedback_template.json'),(CASE/'README.md','README.md'),(CASE/'review/previews/V2_r01/cameras.json','previews/cameras.json')]:z.write(f,STEM+'/'+name)
    files=[]
    for sub in ['hafusion','support/vendor','support/detail_lab']:
        files.extend(f for f in (ROOT/sub).rglob('*.py') if '__pycache__' not in f.parts)
    files.extend(f for f in (ROOT/'tests').glob('*.py') if f.name!='test_hafusion.py')
    for name in ['AGENTS.md','docs/HAF_0.2.md','docs/haf_0_2_capabilities.json','learning/nanshan_cloud_v1.json','learning/nanshan_cloud_v2.json','tools/agent.py','tools/render_building_case.py','tools/package_building_case.py','cases/namsan_tower/src/render_egl_site.py','cases/guangzhou_ctf/research/detail_study_v2/vanilla/template_anvil.json','cases/guangzhou_ctf/research/vanilla/template_wall_post.json','cases/guangzhou_ctf/research/vanilla/template_wall_side.json','upstream/PlanCraft/LICENSE']:
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
    synthetic['README_CASE_KIT.txt']='''HAF 0.2 / Nanshan Cloud V2 case kit

Delivery V2_r01. V1_r04 and original run snapshots are retained unchanged.
New shared behavior: four canonical 45-degree model quadrants on every complete
export, with matched night views. This does not establish geographic bearings.
The current case narrows terrace footprints and uses three equal-width upper
rows; tower dimensions and total heights remain the V1 values.

Python 3.12, numpy, Pillow. Generation requires no network.
Linux rendering additionally requires EGL/Mesa. Mesh caches are excluded;
the renderer bounds memory with batches of up to three views. Do not run
several build/mesh/export jobs concurrently on low-memory hosts.

python3 tools/agent.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/render_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/package_building_case.py --case nanshan_cloud --run MY_NEW_RUN --name Nanshan_Cloud_Custom
python3 cases/nanshan_cloud/src/validate_v2.py
python3 -m unittest discover -s tests -v

validate_v2.py checks the archived V2_r01/V2_replay and saved preview evidence.
Historical V1 scripts are kept as records; do not use them to overwrite this
case. The source kit narrows the executable registry to nanshan_cloud. The
full earlier registry is preserved in history and needs the full HAF project.
Some other shared modules/catalog entries require historical case fixtures
and are not claimed executable from this reduced kit.

23 relevant unit tests are included. The excluded test_hafusion.py requires
legacy Canton/HA0.3 integration fixtures. The full source tree passed 33 tests.
The preserved vanilla miniature shape fixtures retain Mojang provenance.
Third-party notices are retained where bundled; no blanket license is claimed
for upstream materials. Raw research photos/HTML and font binaries are omitted.
To rebuild optional Chinese-labelled contact sheets, provide a local CJK font
through HAF_CJK_FONT. The primary NBT/mesh generation needs no such font.

The self-contained comparison HTML is delivered separately. Its source can be
rerun without raw reference photos, using references/links and included previews.
DOM checks need an external jsdom installation (HAF_JSDOM_MODULE). No browser
executable or game client is included. Source-linked renders are untextured
state-box previews, not game screenshots. North, hidden interfaces, third-tower
height, real rooms and field dimensions remain approximate; Minecraft import,
lighting, textures, collision and neighbour updates remain pending.

This kit records procedural rules and evaluations, not neural training results.
'''.encode()
    manifest=[];prefix='HAF_Nanshan_Cloud_V2/'
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
