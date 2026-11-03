from pathlib import Path
import hashlib,json,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'delivery';R=ROOT/'runs/A06'
sha=lambda b:hashlib.sha256(b).hexdigest()
final=json.loads((R/'Taisho12_spec.json').read_text())['source_nbt_sha256'];assert sha((R/'Taisho12.nbt').read_bytes())==final
keep_src={'prototype_base.py','build_more.py','audit_more.py','render_more.py','report_more.py','export_world.py','vanilla_preview.py','modules.py','interior_kit.py','fetch_vanilla_assets.py','check_more.cjs','package_more.py'}
entries={}
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts:continue
 rel=p.relative_to(ROOT);parts=rel.parts;ok=False
 if parts[0]=='src':ok=p.name in keep_src or p.name.endswith('_states.py')
 elif parts[0]in['support','hafusion']:ok=p.suffix in ['.py','.json','.txt','.md']
 elif parts[0]=='assets':ok=p.name in ['render_shader_reference.html','vanilla_source.json']
 elif parts[0]=='input':ok=p.name=='template_level.dat'
 elif parts[0]=='runs':ok=len(parts)>2 and parts[1]=='A06' and p.suffix in ['.json','.nbt']
 elif parts[0]=='research':ok=p.suffix=='.json' or len(parts)>1 and parts[1]=='photos' and p.suffix=='.jpg'
 elif parts[0]=='review':ok=len(parts)==4 and parts[1]=='previews' and parts[2].startswith('A06_') and (p.suffix=='.png' or p.name in ['cameras.json','all_views.json'])
 elif parts[0]=='delivery':ok=len(parts)==2 and p.name in ['Taisho12.html','Taisho12_Preview.png','Taisho12_World_1.21.1.zip']
 elif p.name in ['README.txt','requirements.txt']:ok=True
 if ok:entries[str(rel)]=p.read_bytes()
for g in ['Bookshop','Pharmacy','Inn','Taisho12']:entries['structures/'+g.lower()+'.nbt']=(R/(g+'.nbt')).read_bytes()
# Preserve small failure/iteration evidence, never substitute outdated NBT.
for run in ['A02','A03','A04','A05']:
 for p in (ROOT/'runs'/run).glob('*audit.json'):entries['research/diagnostics/'+run+'_'+p.name]=p.read_bytes()
manifest={'case':'Taisho12','final_run':'A06','minecraft':'Java 1.21.1','mainline':'HAF 0.4','source_nbt_sha256':final,'game_client':'not run','video_reference':'BV1Dx41187iG, partial frame review added after A06; changes pending','entries':[{'path':k,'bytes':len(v),'sha256':sha(v)}for k,v in entries.items()]}
entries['manifest.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
with zipfile.ZipFile(D/'Taisho12_Project.zip','w',zipfile.ZIP_DEFLATED)as z:
 for k,v in entries.items():z.writestr('Taisho12_Project/'+k,v)
with zipfile.ZipFile(D/'Taisho12_Project.zip')as z:
 assert z.testzip()is None
 for e in manifest['entries']:assert sha(z.read('Taisho12_Project/'+e['path']))==e['sha256']
print(json.dumps({'files':len(entries),'zip_bytes':(D/'Taisho12_Project.zip').stat().st_size,'source_nbt_sha256':final,'zip_crc':'pass'},indent=2))
