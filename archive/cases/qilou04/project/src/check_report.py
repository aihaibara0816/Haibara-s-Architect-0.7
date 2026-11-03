"""Verify offline atlas embeds the exact exported structures and original game PNGs."""
from pathlib import Path
from html.parser import HTMLParser
import base64, hashlib, io, json, re, subprocess, sys, tempfile, zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'runs'/sys.argv[1]
D=ROOT/'deliverables'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.current=None
        self.scripts=[]
        self.external=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script':
            self.current={'attrs':a,'text':''}
            self.scripts.append(self.current)
        if tag in ('img','script','iframe','link'):
            for key in ('src','href'):
                if re.match(r'^https?://',a.get(key,'')):
                    self.external.append(a[key])
    def handle_data(self,data):
        if self.current is not None:self.current['text']+=data
    def handle_endtag(self,tag):
        if tag=='script':self.current=None

p=Page();p.feed((D/'Qilou04.html').read_text())
assert not p.external,p.external
scripts={s['attrs'].get('id'):s['text'] for s in p.scripts if s['attrs'].get('id')}
c=json.loads(scripts['caseData']);v=json.loads(scripts['viewerDoc'])
assert v==(D/'Qilou04_Model.html').read_text()
assert len(c['houses'])==44
assert base64.b64decode(c['masterNBT'])==(R/'Qilou04.nbt').read_bytes()
assert base64.b64decode(c['worldZip'])==(D/'Qilou04_World_1.21.1.zip').read_bytes()
with zipfile.ZipFile(io.BytesIO(base64.b64decode(c['worldZip']))) as z:assert z.testzip() is None
for h in c['houses']:assert base64.b64decode(h['nbt'])==(R/(h['id']+'.nbt')).read_bytes()
expected={hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'review/game').glob('*.png') if f.name!='startup_proof.png'}
actual=set();count=0
def walk(x):
    global count
    if isinstance(x,dict):
        for y in x.values():walk(y)
    elif isinstance(x,list):
        for y in x:walk(y)
    elif isinstance(x,str) and x.startswith('data:image/'):
        data=base64.b64decode(x.split(',',1)[1])
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        count+=1
        if x.startswith('data:image/png'):
            with Image.open(io.BytesIO(data)) as im:assert im.size==(1920,1080)
            actual.add(hashlib.sha256(data).hexdigest())
walk(c)
assert actual==expected,(len(actual),len(expected))
node='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node'
for i,s in enumerate(p.scripts):
    if s['attrs'].get('type')=='application/json':continue
    with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as f:
        f.write(s['text']);f.flush();subprocess.run([node,'--check',f.name],check=True,capture_output=True)
browser=json.loads((R/'browser_report_check.json').read_text());assert browser['pass']
checks=json.loads((D/'Qilou04_checks.json').read_text());checks['browser_report_check']=browser
(D/'Qilou04_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
result={'pass':True,'images_decoded':count,'exact_original_game_pngs':len(actual),'exact_nbt_downloads':len(c['houses'])+1,'exact_world_zip':True,'exact_viewer_html':True,'external_runtime_dependencies':p.external,'browser_report_check':browser}
(D/'report_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
