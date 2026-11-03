"""Persistable case archive; excludes reproducible mesh caches and source photos."""
from pathlib import Path
import hashlib,json,zipfile
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1];OUT=CASE/'deliverables'

def main():
    OUT.mkdir(exist_ok=True)
    import_zip=OUT/'Namsan_Tower_HAF_V1_Build.zip'
    with zipfile.ZipFile(import_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted((CASE/'runs/V1_r02/import_pack').rglob('*')):
            if p.is_file():z.write(p,'Namsan_Tower_HAF_V1/'+str(p.relative_to(CASE/'runs/V1_r02/import_pack')))
        for name in ['overview','night','site_top','podium','observation_pod','antenna']:
            p=CASE/'review/previews/V1_r02'/(name+'.png');z.write(p,'Namsan_Tower_HAF_V1/previews/'+p.name)
    files=[]
    for sub in ['hafusion','support/vendor','support/detail_lab']:
        files.extend(p for p in (HAF/sub).rglob('*.py') if '__pycache__' not in p.parts)
    files.extend(HAF/p for p in ['agent_config.json','AGENTS.md','tools/agent.py','docs/haf_0_2_capabilities.json','learning/namsan_site_v1.md'])
    files.extend(HAF/'tests'/n for n in ['test_site_scene.py','test_lighting.py','test_light_slots.py'])
    for p in CASE.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(CASE)
        if any(v in rel.parts for v in ['__pycache__','deliverables']):continue
        if rel.parts[:2] in [('research','images'),('research','pages')]:continue
        if 'scene' in rel.parts and p.name!='scene.json':continue
        if p.suffix=='.bin':continue
        # Test feedback text is a harness output, not actual user feedback.
        if p.name in ['feedback_export_test.json','review_scripts.js']:continue
        files.append(p)
    source_zip=OUT/'Namsan_Tower_HAF_V1_Source.zip';checks=[]
    with zipfile.ZipFile(source_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(files)):
            rel=str(p.relative_to(HAF));z.write(p,'HAF_Namsan_V1/'+rel)
            checks.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
        z.writestr('HAF_Namsan_V1/README_CASE_KIT.txt','''HAF 0.2 / Namsan Tower V1 case kit

This archive contains the new Namsan case and its required shared HAF modules.
The original complete HAF 0.2 source and historical buildings remain unchanged
in the earlier HAF_0.2_Source.zip release. This kit can overlay that tree, or
reproduce Namsan independently. It is not a replacement for the full history.

Requirements: Python 3.12, numpy, Pillow; matplotlib for the terrain figure.
Linux libEGL.so.1 / Mesa is required only for offline image rendering.

Run from this directory:
  python3 tools/agent.py --case namsan_tower --run MY_NEW_RUN
  python3 cases/namsan_tower/src/render_case.py --run MY_NEW_RUN
  python3 cases/namsan_tower/src/package_import.py --run MY_NEW_RUN
  python3 -m unittest discover -s tests -v

The included 9 unit tests exercise the dependencies shipped in this kit.
The full-tree 26-test result is saved in the case validation folder.
Historical preservation checks inside validate_case.py require the full HAF
tree, because the earlier building NBT files are deliberately not duplicated.
Independent generation requires no network or original gallery photographs.

See cases/namsan_tower/README.md for scope, fidelity limits, replay hashes,
source records, feedback and import details. Final baseline: V1_r02.

Map data: OpenStreetMap contributors, ODbL 1.0
https://www.openstreetmap.org/copyright
https://opendatacommons.org/licenses/odbl/1-0/
Original and converted map data is included in research/terrain.
Terrain: SRTM via OpenTopoData. Original image copyrights remain with sources;
only URL/hash/observation records are redistributed here.
''')
        z.writestr('HAF_Namsan_V1/requirements-namsan.txt','numpy\nPillow\nmatplotlib\n')
        z.writestr('HAF_Namsan_V1/FILE_MANIFEST.json',json.dumps(checks,ensure_ascii=False,indent=2))
    outputs=[]
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name!='delivery_manifest.json':outputs.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (OUT/'delivery_manifest.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
    print(json.dumps({'source_members':len(files),'outputs':outputs},ensure_ascii=False))

if __name__=='__main__':main()
