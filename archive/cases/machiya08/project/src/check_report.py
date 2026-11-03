"""Check standalone report payloads, source views, links, and export DOM for JS harness."""
from pathlib import Path
from html.parser import HTMLParser
import sys, json, base64, io, re, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
run, report, temp = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
R = ROOT / 'runs' / run
D = ROOT / 'review/previews' / run
temp.mkdir(parents=True, exist_ok=True)
text = report.read_text()

class Parse(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.images, self.buttons, self.links, self.stack = [], [], [], [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
        if tag == 'img': self.images.append(a)
        if tag == 'a': self.links.append(a)
        if tag == 'button':
            a['parent'] = next((x[1]['id'] for x in reversed(self.stack)
                                if x[1].get('id', '').endswith('-controls')), '')
            self.buttons.append(a)
        if tag not in ['meta', 'link', 'img', 'br', 'hr', 'input']:
            self.stack.append((tag, a))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

p = Parse(); p.feed(text)
assert len(p.ids) == len(set(p.ids))
assert all(a['href'][1:] in p.ids for a in p.links if a.get('href','').startswith('#'))
uris = set(re.findall(r'data:image/(?:webp|svg\+xml);base64,[A-Za-z0-9+/=]+', text))
for uri in uris:
    data = base64.b64decode(uri.split(',', 1)[1], validate=True)
    if uri.startswith('data:image/svg'):
        import xml.etree.ElementTree as ET
        ET.fromstring(data)
    else:
        Image.open(io.BytesIO(data)).verify()
expected = {name: (R/name).read_bytes() for name in
            ['Machiya08.nbt', 'design_contract.json', 'design_prompts.txt']}
expected['Freedom_frontage_research.json'] = (ROOT/'input/Freedom_frontage_research.json').read_bytes()
downloads = [a for a in p.links if 'download' in a]
assert len(downloads) == len(expected)
for a in downloads:
    assert base64.b64decode(a['href'].split(',',1)[1], validate=True) == expected[a['download']]
sp = json.loads((R/'spec.json').read_text())
source_hash = hashlib.sha256((R/'Machiya08.nbt').read_bytes()).hexdigest()
assert source_hash == sp['source_nbt_sha256']
records = json.loads((D/'render_report.json').read_text())
assert len(records) == 42
for rec in records:
    path = D/rec['image']
    assert rec['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert Image.open(path).info['source_nbt_sha256'] == source_hash
    assert json.loads(Image.open(path).info['camera']) == rec['camera']
old_cameras = {v['id']:v for v in json.loads((ROOT/'review/previews/M06/cameras.json').read_text())}
new_cameras = {v['id']:v for v in json.loads((D/'cameras.json').read_text())}
for key in ['front_eye','exterior_SE','elevation_south','top']:
    assert old_cameras[key] == new_cameras[key]
result = dict(ids_unique=True, fragment_links_resolve=True,
              embedded_images_decoded=len(uris), payload_downloads=len(downloads),
              current_source_images_verified=len(records), historical_comparison_images=8,
              facade_comparison_cameras_exact=True, source_nbt_sha256=source_hash,
              full_browser_test=False)
(R/'report_check.json').write_text(json.dumps(result, indent=2))
(temp/'dom.json').write_text(json.dumps(dict(ids=p.ids, images=p.images, buttons=p.buttons)))
scripts = re.findall(r'<script>(.*?)</script>', text, re.S)
assert len(scripts) == 1
(temp/'script.js').write_text(scripts[0])
print(json.dumps(result))
