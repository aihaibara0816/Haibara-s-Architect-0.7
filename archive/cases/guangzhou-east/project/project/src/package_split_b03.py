"""Atomic, verified delivery archive. Does not modify the accepted B03."""
from pathlib import Path
import hashlib,json,zipfile,os
P=Path(__file__).resolve().parents[1];D=P/'deliverables/B03S1';R=P/'runs/B03S1'
manifest=json.loads((R/'manifest.json').read_text());delivery=json.loads((R/'delivery_manifest.json').read_text());qa=json.loads((R/'browser_qa.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
for rel,meta in delivery.items():
 b=(D/rel).read_bytes();assert len(b)==meta['bytes'] and sha(b)==meta['sha256'],rel
assert qa['guide_sha256']==sha((D/'GuangzhouEast_Print_Guide.html').read_bytes())
for a in manifest['recommended_parts']+manifest['whole_groups_alternative']:
 assert sha((D/a['file']).read_bytes())==a['sha256'],a['file']
assert not json.loads((R/'validation.json').read_text())['errors']
entries={rel:D/rel for rel in delivery}
for rel in ['src/segment_link_b03.py','src/plan_triangle_b03.py','src/deliver_split_b03.py','src/link_geometry.py','src/check_split_browser.cjs','src/package_split_b03.py',
 'runs/B03/spec.json','runs/B03/GuangzhouEast_Complete.nbt','runs/B03/GuangzhouEast_LinkOnly.nbt','runs/B03/GuangzhouEast_LinkOnly_owners.json',
 'runs/B03S1/manifest.json','runs/B03S1/validation.json','runs/B03S1/parts_owner.json','runs/B03S1/triangle_proposal.json','runs/B03S1/browser_qa.json','runs/B03S1/delivery_manifest.json',
 'research/dongguanxi/NotoSansCJKsc-Regular.otf','research/dongguanxi/FONT_OFL.txt']:
 entries['project/'+rel]=P/rel
for p in (P/'deps/nbtlib').rglob('*.py'):entries['project/'+str(p.relative_to(P))]=p
for name in ['LICENSE','METADATA']:entries['project/deps/nbtlib-2.0.4.dist-info/'+name]=P/'deps/nbtlib-2.0.4.dist-info'/name
reproduce='''B03S1 — reproducibility / 复现说明

User files are at the archive root: print_parts (7 parts), whole_groups (3 alternatives), guide HTML, two PNG plans and coordinate CSV.
Choose either the seven print parts or the three whole groups. Do not print both sets on top of one another.
The original station, throats and approaches are only supplied as reference inside project/runs/B03/GuangzhouEast_Complete.nbt. The print parts contain the connector only.

Python 3.12; dependencies: numpy, scipy, Pillow, fonttools. nbtlib 2.0.4 source and MIT license are bundled.
From project/, run in order:
  python3 src/segment_link_b03.py
  python3 src/plan_triangle_b03.py
  python3 src/deliver_split_b03.py
This writes project/deliverables/B03S1. The full B03 source is frozen; SHA is checked before splitting.
Browser verification uses Playwright and Chromium. Adjust the Playwright module path in src/check_split_browser.cjs for a different machine, then pass the Chromium executable as its first argument.

NBT read-back: 61,119 original blocks and exact block entity data, no overlap or missing cells; all curve endpoints and signal targets stay inside their own part.
Browser: offline downloads byte-matched; coordinate conversion, selectors and narrow-screen layout checked.
Minecraft placement, schematic cannon printing and automated train tests are NOT run.
Triangle lots and road corridors are proposed only; no proposed buildings were added to NBT.

Noto Sans CJK font © 2014–2021 Adobe. Licensed under SIL Open Font License 1.1; full license is research/dongguanxi/FONT_OFL.txt. The guide embeds a subset for offline Chinese text.
'''
archive=D/'GuangzhouEast_Segmented_Print_Pack.zip';tmp=archive.with_suffix('.zip.partial')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for name,p in sorted(entries.items()):z.writestr(name,p.read_bytes())
 z.writestr('project/REPRODUCE.txt',reproduce)
with zipfile.ZipFile(tmp)as z:
 assert z.testzip()is None
 assert len(z.namelist())==len(set(z.namelist()))
 for name,p in entries.items():assert z.read(name)==p.read_bytes(),name
os.replace(tmp,archive)
report={'file':archive.name,'file_count':len(entries)+1,'bytes':archive.stat().st_size,'sha256':sha(archive.read_bytes()),'zip_crc_ok':True,'all_entries_byte_exact':True,'sources_unchanged':True,'browser_guide_sha256':qa['guide_sha256']}
(R/'package_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
