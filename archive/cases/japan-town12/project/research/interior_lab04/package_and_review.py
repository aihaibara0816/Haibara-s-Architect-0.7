from pathlib import Path
import json,io,zlib,hashlib,zipfile,shutil,sys
import nbtlib as n
W=Path('/workspace/scratch/5e56249baf34');P=W/'interior_rework';R=P/'runs/I06';old=P/'runs/I05';h=json.loads((R/'lab.json').read_text())['source_nbt_sha256']
assert hashlib.sha256((old/'InteriorLab.nbt').read_bytes()).hexdigest()==h
for f in ['world_check.json']:
 shutil.copy(old/f,R/f)
views=old/'review/previews/I05';rec=json.loads((views/'render_report.json').read_text());assert len(rec)==17 and all(x['source_nbt_sha256']==h for x in rec)
(R/'render_reuse.json').write_text(json.dumps({'source_nbt_sha256':h,'render_run':'I05','geometry_exact':True,'views':17,'note':'I06 changes component metadata only; identical NBT renders reused'},indent=2))
f=n.load(R/'InteriorLab.nbt');off=(-23,64,-21);expected={}
for e in f['blocks']:
 if 'nbt' in e:expected[tuple(int(e['pos'][i])+off[i] for i in range(3))]=str(e['nbt']['id'])
found={};world=P/'worlds/InteriorLab04_I05'
for p in (world/'region').glob('*.mca'):
 raw=p.read_bytes()
 for i in range(1024):
  loc=int.from_bytes(raw[i*4:i*4+3],'big')*4096
  if not loc:continue
  size=int.from_bytes(raw[loc:loc+4],'big');c=n.File.parse(io.BytesIO(zlib.decompress(raw[loc+5:loc+4+size])))
  for e in c['block_entities']:found[tuple(int(e[k]) for k in ['x','y','z'])]=str(e['id'])
assert found==expected
(R/'block_entity_check.json').write_text(json.dumps({'source_count':len(expected),'world_count':len(found),'positions_and_types_exact':True,'game':'pending'},indent=2))
(R/'visual_review.json').write_text(json.dumps({'source_nbt_sha256':h,'reviewer':'assistant','views_checked':['A_eye_entry','B_bedroom','C_eye_entry','D_eye_entry','four cutaways','J14/J15 door pair'],'finding':'More complete activity groups and surface layers; still prototype quality. Original screenshots are negative evidence. Game and user aesthetic acceptance remain pending.','material':'NBT-derived boxes plus procedural recognition marks; no original game texture','full_ceiling_eye_views':True,'large_blank_regions':'Do not equate open cells to circulation. Main room edge clearances retained; refinements await actual walking feedback.'},indent=2))
out=P/'delivery';out.mkdir(exist_ok=True)
with zipfile.ZipFile(out/'InteriorLab04.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in world.rglob('*'):
  if p.is_file():z.write(p,Path('InteriorLab04')/p.relative_to(world))
 for p in R.glob('*'):
  if p.is_file():z.write(p,Path('Evidence')/p.name)
 z.write(views/'render_report.json','Evidence/render_report.json')
 for p in (P/'clinic_application').glob('*'):
  if p.is_file():z.write(p,Path('PlanningOnly_Clinic')/p.name)
with zipfile.ZipFile(out/'HiyoriTown18_DoorFix.zip','w',zipfile.ZIP_DEFLATED) as z:
 world=P/'worlds/HiyoriTown18_J15'
 for p in world.rglob('*'):
  if p.is_file():z.write(p,Path('HiyoriTown18_J15')/p.relative_to(world))
 case=W/'town12/JapanTown12/cases/japan_town12'
 for fn in ['door_frame_check.json','world_check.json','banner_check.json','verification.json'] :z.write(case/'runs/J15'/fn,'Evidence/'+fn)
 z.write(case/'src/build_detailtown.py','Source/build_detailtown.py')
 z.writestr('READ_FIRST.txt','本存档只修18栋入口：门回到门框平面、补门楣、成对门框。329格变化限定入口。\n内饰全量仍需返工；不是新内饰成品。Java 1.21.1。实机验收 pending。\n')
for p in out.glob('*.zip'):
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
print([(p.name,p.stat().st_size) for p in out.glob('*.zip')])
