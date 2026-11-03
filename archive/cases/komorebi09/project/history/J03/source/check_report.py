"""Validate report assets and export a small DOM for the JS behavior harness."""
from pathlib import Path
from html.parser import HTMLParser
import sys,json,base64,io,re,hashlib,xml.etree.ElementTree as ET
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
run,report,temp,world=sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4])
R=ROOT/'runs'/run;D=ROOT/'review/previews'/run;temp.mkdir(parents=True,exist_ok=True)
class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.elements=[];self.stack=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);a['tag']=tag;a['parents']=[x.get('id') for x in self.stack if x.get('id')]
        if a.get('id') or tag in ['img','button','a'] or 'data-building' in a:self.elements.append(a)
        if tag=='a':self.links.append(a)
        if tag not in ['meta','link','img','br','hr','input']:self.stack.append(a)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):
        if self.stack:self.stack[-1]['textContent']=self.stack[-1].get('textContent','')+data
p=Parser();text=report.read_text();p.feed(text)
ids=[x['id'] for x in p.elements if x.get('id')];assert len(ids)==len(set(ids))
assert all(a['href'][1:] in ids for a in p.links if a.get('href','').startswith('#'))
assert not re.search(r'<(?:script|img)[^>]+(?:src)=[\"\']https?://',text)
uris=set(re.findall(r'data:image/(?:webp|svg\+xml);base64,[A-Za-z0-9+/=]+',text))
for uri in uris:
    data=base64.b64decode(uri.split(',',1)[1],validate=True)
    if uri.startswith('data:image/svg'):ET.fromstring(data)
    else:Image.open(io.BytesIO(data)).verify()
assert len(uris)==105,len(uris)
expected={name:(R/name).read_bytes() for name in ['Komorebi09.nbt','design_contract.json','design_prompts.txt']}
expected[world.name]=world.read_bytes()
downloads=[a for a in p.links if 'download' in a and a.get('id')!='download-view'];assert len(downloads)==4
for a in downloads:assert base64.b64decode(a['href'].split(',',1)[1],validate=True)==expected[a['download']]
source=hashlib.sha256((R/'Komorebi09.nbt').read_bytes()).hexdigest();sp=json.loads((R/'spec.json').read_text());assert source==sp['source_nbt_sha256']
records=json.loads((D/'all_views.json').read_text());assert len(records)==104
assert len({v['image'] for v in records})==104
for rec in records:
    path=D/rec['image'];im=Image.open(path)
    assert rec['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert im.info['source_nbt_sha256']==source
    assert json.loads(im.info['camera'])==rec['camera']
scripts=re.findall(r'<script>(.*?)</script>',text,re.S);assert len(scripts)==1
(temp/'script.js').write_text(scripts[0]);(temp/'dom.json').write_text(json.dumps(p.elements,ensure_ascii=False))
(temp/'buildings.json').write_text(json.dumps(sp['buildings'],ensure_ascii=False))
result=dict(ids_unique=True,fragment_links_resolve=True,external_script_or_image_dependencies=False,embedded_images_decoded=len(uris),payload_downloads_byte_exact=len(downloads),current_source_images_verified=len(records),source_nbt_sha256=source,full_browser_test=False)
(R/'report_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
