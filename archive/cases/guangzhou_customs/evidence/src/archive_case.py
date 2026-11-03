"""Build package and a narrow, replayable source kit; preserve prior cases."""
from pathlib import Path
import hashlib,json,zipfile
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
OUT=ROOT/'deliverables/guangzhou_customs_v1';STEM='Guangzhou_Customs_HAF_V1'

def main():
    OUT.mkdir(parents=True,exist_ok=True);run=CASE/'runs/V1_r04'
    with zipfile.ZipFile(OUT/(STEM+'_Build.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted((run/'import_pack').rglob('*')):
            if f.is_file():z.write(f,STEM+'/'+str(f.relative_to(run/'import_pack')))
        for f in sorted((CASE/'review/previews/V1_r04').glob('*.png')):z.write(f,STEM+'/previews/'+f.name)
        for f,name in [(run/'manifest.json','build_manifest.json'),(CASE/'validation/acceptance.json','validation.json'),(CASE/'review/feedback_template.json','feedback_template.json'),(CASE/'README.md','README.md'),(CASE/'review/previews/V1_r04/cameras.json','previews/cameras.json')]:z.write(f,STEM+'/'+name)
    files=[]
    for sub in ['hafusion','support/vendor','support/detail_lab']:
        files.extend(f for f in (ROOT/sub).rglob('*.py') if '__pycache__' not in f.parts)
    files.extend(f for f in (ROOT/'tests').glob('*.py') if f.name!='test_hafusion.py')
    for name in ['AGENTS.md','docs/HAF_0.2.md','docs/haf_0_2_capabilities.json','learning/guangzhou_customs_v1.json','tools/agent.py','tools/render_building_case.py','tools/package_building_case.py','cases/namsan_tower/src/render_egl_site.py','cases/guangzhou_ctf/research/detail_study_v2/vanilla/template_anvil.json','cases/guangzhou_ctf/research/vanilla/template_wall_post.json','cases/guangzhou_ctf/research/vanilla/template_wall_side.json','upstream/PlanCraft/LICENSE']:
        files.append(ROOT/name)
    files.extend(f for f in (ROOT/'history/before_guangzhou_customs').rglob('*') if f.is_file())
    for f in CASE.rglob('*'):
        if not f.is_file():continue
        rel=f.relative_to(CASE)
        if any(v in rel.parts for v in ['__pycache__','images','regions','raw','scene']):continue
        if f.suffix=='.bin':continue
        files.append(f)
    config=json.loads((ROOT/'agent_config.json').read_text());synthetic={'history/full_agent_config_at_delivery.json':json.dumps(config,ensure_ascii=False,indent=2).encode()}
    config['cases']={'guangzhou_customs':config['cases']['guangzhou_customs']};config['default_case']='guangzhou_customs'
    synthetic['agent_config.json']=json.dumps(config,ensure_ascii=False,indent=2).encode()
    synthetic['requirements-case.txt']=b'numpy\nPillow\n'
    synthetic['README_CASE_KIT.txt']='''HAF 0.2 / Guangzhou Customs V1 case kit

Delivery baseline V1_r04, adapter 0.1.3. New image-only case. Original HAF
building runs were not overwritten. Internal prototypes are retained as records.

Python 3.12, numpy, Pillow. Building and validation require no network.
Linux preview rendering also needs EGL/Mesa. Mesh caches are excluded.
Do not run several large build, mesh and export jobs on a low-memory machine.

python3 tools/agent.py --case guangzhou_customs --run MY_NEW_RUN
python3 tools/render_building_case.py --case guangzhou_customs --run MY_NEW_RUN
python3 tools/package_building_case.py --case guangzhou_customs --run MY_NEW_RUN --name Guangzhou_Customs_Custom
python3 cases/guangzhou_customs/src/validate_case.py
python3 -m unittest discover -s tests -v

validate_case.py checks the saved delivery baseline and replay, not arbitrary
new geometry. The case has explicit coordinates as well as parameters; broad
dimension changes still require interface review. Registry is narrowed to this
case. The full project registry is retained under history; its other cases need
the complete project and are not executable from this narrow kit.

23 relevant unit tests are included. test_hafusion.py is excluded because it
depends on historical Canton/HA0.3 integration fixtures. Full tree passed 33.
The small vanilla shape fixtures retain Mojang provenance; PlanCraft license
is bundled. No blanket license for third-party material is asserted.

Raw reference photos and font binaries are omitted. Source URLs, hashes and
evidence decisions remain. The separately delivered review HTML includes the
necessary attributed reference crops. To reproduce optional labelled contact
sheets, provide HAF_CJK_FONT with a local CJK font. To run the offline review
DOM checks, set HAF_JSDOM_MODULE to an external installed jsdom module.

Height 137 blocks is an editable study envelope, not a resolved survey: sources
conflict at 103 / 137 metres and an estimated 114 metres. Width/depth, hidden
interfaces and geographic bearing remain approximate. Night lighting, office
furnishings, clock time and two unseen clock faces are interpretive additions.
No SKP/model, automatic reconstruction, image stitching or trained weights.
State-box previews are not textured game screenshots. Actual Minecraft import,
neighbour updates, lighting, textures and full navigation remain untested.

Shared change: optional sun_day/sun_night camera vectors; quadrant views retain
the same sun. Old camera defaults remain unchanged. Original source copies are
kept under history/before_guangzhou_customs.
'''.encode()
    manifest=[];prefix='HAF_Guangzhou_Customs_V1/'
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
