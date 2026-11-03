from pathlib import Path
import zipfile,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1]if len(sys.argv)>1 else'O09';D=ROOT/'delivery'
src=['build_organic.py','organic_types.py','validate_locals.py','terrain_plot.py','build_quarter.py','quarter_types.py','street_types.py','baseline_types.py','prototype_base.py','modules.py','interior_kit.py','taisho_states.py','town_states.py','room_states.py','corner_states.py','interior_lab_states.py','terrain_states.py','audit_more.py','audit_quarter.py','render_quarter.py','vanilla_preview.py','export_quarter_world.py','fetch_vanilla_assets.py','report_quarter.py','check_quarter.cjs','verify_quarter_repro.py','package_quarter.py']
files=[ROOT/'README_Taisho15.txt',ROOT/'requirements.txt',ROOT/'input/template_level.dat']+[ROOT/'src'/s for s in src]
files+=[ROOT/'assets'/f for f in ['vanilla_source.json','render_shader_reference.html','viewer_v1.js','quarter_report.html']]
for folder in ['support','hafusion','runs/'+RUN]:
 files.extend(p for p in(ROOT/folder).rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix not in ['.pyc','.tmp'])
files += [ROOT/'research'/s for s in ['BUILD_STATE.json','design_brief_15.json','video_research_15.json','skill_update_15.json','recipe_catalog_15.json','presentation_standard_v1.json']]
for viewdir in (ROOT/'review/previews').glob(RUN+'_*'):
 files.extend(p for p in viewdir.iterdir()if p.is_file()and(p.suffix=='.png'or p.name in ['views_full.json','cameras_full.json','mesh_source.txt']))
files.extend([ROOT/'review/O09_plans.png',ROOT/'review/visual_review_15.json',D/'Taisho15.html',D/'Taisho15_World_1.21.1.zip',D/'Taisho15_Preview.png'])
files=sorted(set(files));assert all(p.exists()for p in files)
manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files};(D/'manifest15.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
dest=D/'Taisho15_Project.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)as z:
 for p in files:z.write(p,'Taisho15/'+str(p.relative_to(ROOT)))
 z.write(D/'manifest15.json','Taisho15/manifest.json')
with zipfile.ZipFile(dest)as z:assert z.testzip()is None
with zipfile.ZipFile(D/'Taisho15_World_1.21.1.zip')as z:assert z.testzip()is None
print(json.dumps({'files':len(files)+1,'project_bytes':dest.stat().st_size,'zip_crc':'pass'}))
