"""Fetch only the pinned Mojang client assets needed to reproduce the offline preview.
Minecraft client content is not bundled with this project.
"""
from pathlib import Path
import urllib.request,json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'assets/minecraft-source';out.mkdir(parents=True,exist_ok=True)
with urllib.request.urlopen('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json',timeout=30) as r:d=json.load(r)
v=next(x for x in d['versions'] if x['id']=='1.21.1')
with urllib.request.urlopen(v['url'],timeout=30) as r:m=json.load(r)
c=m['downloads']['client'];expected=json.loads((ROOT/'assets/vanilla_source.json').read_text());assert c['sha1']==expected['sha1'];jar=out/'client.jar'
with urllib.request.urlopen(c['url'],timeout=60) as r:jar.write_bytes(r.read())
assert hashlib.sha1(jar.read_bytes()).hexdigest()==c['sha1']
with zipfile.ZipFile(jar) as z:
 for name in z.namelist():
  if name.startswith(('assets/minecraft/blockstates/','assets/minecraft/models/block/','assets/minecraft/textures/block/','assets/minecraft/textures/painting/','data/minecraft/painting_variant/')):z.extract(name,out)
(out/'source.json').write_text(json.dumps({'version':'1.21.1','client_sha1':c['sha1'],'url':c['url']},indent=2))
print('Verified Java 1.21.1 model/texture assets; do not redistribute the client JAR.')
