from pathlib import Path
import sys,json,hashlib,re,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs'/sys.argv[1];g=ROOT/'review/game';runtime=ROOT.parent/'game_runtime';original=runtime/'instance/screenshots';src=json.loads((R/'spec.json').read_text());names=[v['name']for f in['capture_plan.json','interior_plan.json']for v in json.loads((g/f).read_text())];required=[n+s for n in names for s in['','_night']]
assert all((g/(n+'.png')).exists()for n in required)
from PIL import Image
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();orig={sha(p):p.name for p in original.glob('*.png')};records=[]
for name in required+['startup_proof']:
 p=g/(name+'.png');im=Image.open(p);assert im.size==(1920,1080);h=sha(p);assert h in orig;records.append({'name':name,'file':p.name,'source_f2_file':orig[h],'sha256':h,'dimensions':list(im.size),'bytes':p.stat().st_size,'unaltered_client_png':True})
log=(runtime/'client.log').read_text(errors='replace');assert'Starting integrated minecraft server version 1.21.1'in log and'Q04Preview joined the game'in log
assert all(r['source_f2_file']in log for r in records), 'Every delivered photo must be captured during this final client session'
excerpt='\n'.join(l for l in log.splitlines()if any(x in l for x in['Starting integrated minecraft server version','Preparing start region','joined the game','Teleported Q04Preview','The time is','Saved screenshot as','Time elapsed:']))
(g/'client_capture_log.txt').write_text(excerpt+'\n')
report={'pass':True,'game':'Minecraft Java 1.21.1','mode':'actual unmodified vanilla client; local singleplayer preview world','resolution':[1920,1080],'external_shaders':False,'resource_pack':'vanilla','capture_method':'Minecraft built-in F2 screenshot; original PNG bytes copied without resizing or recompression','source_nbt_sha256':src['source_nbt_sha256'],'source_world':'Qilou04 exported world copy; original deliverable not overwritten by play session','exterior_views':len(json.loads((g/'capture_plan.json').read_text())),'interior_views':len(json.loads((g/'interior_plan.json').read_text())),'day_night_pairs':len(names),'gallery_screenshots':len(required),'startup_proof':True,'coverage':'Loaded world, real client render, painting/bed/furniture visuals at sampled viewpoints; not exhaustive per-house interactive gameplay test','audio':'disabled in capture environment','records':records}
(R/'game_capture_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(g/'capture_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
wc=json.loads((R/'world_check.json').read_text());wc['game']='loaded in vanilla Java 1.21.1; real F2 screenshots captured; interactions not exhaustively tested';(R/'world_check.json').write_text(json.dumps(wc,ensure_ascii=False,indent=2))
worlddir=Path(sys.argv[2])if len(sys.argv)>2 else ROOT/'world/Qilou04';readme=worlddir/'READ_ME.txt';t=readme.read_text().replace('离线回读检查完成，未运行客户端。','离线回读检查完成，并已用Java1.21.1客户端载入截图；未逐户测试全部交互。');readme.write_text(t)
d=ROOT/'deliverables';shutil.copyfile(g/'plaza.png',d/'Qilou04_Game_Preview.png')
with zipfile.ZipFile(d/'Qilou04_World_1.21.1.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(worlddir.rglob('*')):
  if p.is_file():z.write(p,'Qilou04/'+str(p.relative_to(worlddir)))
print(json.dumps({'original_F2_PNGs':len(records),'resolution':[1920,1080],'source_nbt_sha256':src['source_nbt_sha256']}))
