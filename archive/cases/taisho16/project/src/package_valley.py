from pathlib import Path
import zipfile,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];D=ROOT/'delivery';files=[]
for folder in ['src','support','hafusion','runs/'+RUN,'research']:
 for p in(ROOT/folder).rglob('*'):
  if p.is_file()and '__pycache__'not in p.parts and p.suffix not in['.pyc','.pkl','.tmp']and not(folder=='research'and p.name.endswith('_15.json')):files.append(p)
files += [ROOT/'README_Taisho16.txt',ROOT/'requirements.txt']
files += [ROOT/'input'/s for s in ['template_level.dat','selected_layout.json','T07_reference.png','t07_height.json','t07_water.json']]
files += [ROOT/'assets'/s for s in ['vanilla_source.json','render_shader_reference.html','viewer_v1.js','quarter_report.html']]
for vd in(ROOT/'review/previews').glob(RUN+'_*'):
 files += [p for p in vd.iterdir()if p.is_file()and(p.suffix=='.png'or p.name in['views_full.json','cameras_full.json','mesh_source.txt'])]
files += [D/'Taisho16.html',D/'Taisho16_Preview.png',D/'Taisho16_World_1.21.1.zip']
files=sorted(set(files));assert all(p.is_file()for p in files)
manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in files}
(D/'manifest16.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
out=D/'Taisho16_Project.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)as z:
 for p in files:z.write(p,'Taisho16/'+str(p.relative_to(ROOT)))
 z.write(D/'manifest16.json','Taisho16/manifest.json')
with zipfile.ZipFile(out)as z:assert z.testzip()is None
with zipfile.ZipFile(D/'Taisho16_World_1.21.1.zip')as z:assert z.testzip()is None
print({'files':len(files)+1,'bytes':out.stat().st_size,'zip_crc':'pass'})
