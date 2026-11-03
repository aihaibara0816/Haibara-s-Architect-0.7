"""Offline artifact integrity checks; does not claim a game/browser run."""
from pathlib import Path
import sys,json,base64,zlib,hashlib,re,subprocess,zipfile,collections,tempfile
from PIL import Image
P=Path(__file__).resolve().parents[1];run=sys.argv[1];R=P/'runs'/run;V=P/'review/previews'/(run+'_ModernFactory01');D=P/'deliverables';sha=hashlib.sha256((R/'ModernFactory01.nbt').read_bytes()).hexdigest()
payload=json.loads((R/'interactive_payload.json').read_text());views=json.loads((R/'cameras.json').read_text());checks=[]
for f in ['check.json','access_audit.json','world_check.json','schem_check.json','interactive_metrics.json']:
 q=json.loads((R/f).read_text());assert q['source_nbt_sha256']==sha;checks.append(f)
for kind in ['opaque','glass']:
 b=zlib.decompress(base64.b64decode(payload['bins'][kind]));stats=payload['stats'][kind];assert len(b)==stats['raw_bytes']==stats['vertices']*14;assert hashlib.sha256(b).hexdigest()==stats['sha256'];ranges=payload['ranges'][kind];end=0
 for off,count in ranges:assert off==end;end=off+count
 assert end==stats['vertices']
light=zlib.decompress(base64.b64decode(payload['bins']['light']));assert light==(V/'scene/blocklight.bin').read_bytes();assert len(light)==448*72*336
for v in views:
 im=Image.open(V/(v['id']+'.png'));assert im.info['source_nbt_sha256']==sha;assert im.size==(v['width'],v['height']);assert max(b-a for a,b in im.getextrema())>30
report=json.loads((V/'render_report.json').read_text());assert len(report)==len(views);assert {x['image'] for x in report}=={x['id']+'.png' for x in views}
for e in report:assert e['sha256']==hashlib.sha256((V/e['image']).read_bytes()).hexdigest()
rooms=json.loads((R/'rooms.json').read_text());bedrooms=[x for x in rooms if x['function']=='bedroom'];assert len(bedrooms)==120 and sum(x['capacity'] for x in bedrooms)==240
srcs=[]
for name in ['ModernFactory01.html','ModernFactory01_Model.html']:
 s=(D/name).read_text();assert '@@' not in s;assert sha in s if name.endswith('_Model.html') else True
 for i,t in enumerate(re.findall(r'<script>(.*?)</script>',s,re.S)):
  with tempfile.TemporaryDirectory(prefix='campus_js_') as tmp:
   q=Path(tmp)/'check.js';q.write_text(t);subprocess.run(['node','--check',str(q)],check=True)
 if name=='ModernFactory01.html':
  ids=set(re.findall(r'data-img="([^"]+)"',s));assert ids<=set([v['id'] for v in views]+['baseline'])
for name in ['ModernFactory01_World_1.21.1.zip','ModernFactory01_Project.zip']:
 with zipfile.ZipFile(D/name) as z:assert z.testzip() is None
q={'source_nbt_sha256':sha,'packed_mesh_hashes_exact':True,'light_volume_exact':True,'views_metadata_and_hashes':len(views),'bedroom_count':len(bedrooms),'dorm_capacity':240,'html_scripts_syntax':'pass','zip_crc':'pass','game':'not_run','browser_runtime':'not_run'}
(R/'delivery_qa.json').write_text(json.dumps(q,indent=2));print(json.dumps(q))
