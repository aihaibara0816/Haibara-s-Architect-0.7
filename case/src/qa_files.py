"""Validate final file provenance, embedded original references and font coverage."""
from pathlib import Path
import json,hashlib,re,base64,io,zipfile
from html.parser import HTMLParser
from PIL import Image
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.tags=[];self.words=[];self.skip=False;self.feed(text)
    def handle_starttag(self,tag,attrs):
        self.tags.append((tag,dict(attrs)))
        if tag in ['script','style']:self.skip=True
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.skip=False
    def handle_data(self,data):
        if not self.skip:self.words.append(data)
    def elements(self,name):return [a for tag,a in self.tags if tag==name]
def main():
    report=json.loads((ROOT/'runs/V5_r02/build_report.json').read_text());manifest=json.loads((ROOT/'views/view_manifest.json').read_text())
    assert sha(OUT/'GAFAcraft_Canton280_V5.nbt')==report['nbt']['sha256']
    for row in manifest['views']:
        p=OUT/row['file'];assert sha(p)==row['sha256']
        with Image.open(p) as im:
            assert im.info['geometry_sha256']==report['geometry_sha256'];assert json.loads(im.info['camera'])==row['camera'];im.verify()
    report_html=(OUT/'广州塔_V5_融合取舍与参考资料.html').read_text();soup=Document(report_html)
    refs=json.loads((ROOT/'inputs/v5_reference_manifest.json').read_text())['images'];by={r['image_id']:r for r in refs}
    originals=0
    for im in soup.elements('img'):
        id=im['data-gafa-image-id'];blob=base64.b64decode(im['src'].split(',',1)[1]);assert hashlib.sha256(blob).hexdigest()==by[id]['sha256'];originals+=1
    archive=next(a['href'] for a in soup.elements('a') if a.get('href','').startswith('data:application/zip'))
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(archive.split(',',1)[1]))) as z:
        assert z.testzip() is None
        for r in refs:
            n=next(n for n in z.namelist() if Path(n).stem==r['image_id'] and Path(n).suffix.lower() in ['.png','.jpg','.jpeg'])
            assert hashlib.sha256(z.read(n)).hexdigest()==r['sha256']
    font=TTFont(ROOT/'views/assets/ReviewSans.ttf');cmap=font.getBestCmap();missing={}
    for name in ['广州塔_V5_全景细节与反馈.html','广州塔_V5_融合取舍与参考资料.html','广州塔_V5_材料清单.html']:
        d=Document((OUT/name).read_text());chars=set(''.join(d.words));miss=''.join(sorted(ch for ch in chars if '\u4e00'<=ch<='\u9fff' and ord(ch) not in cmap))
        if miss:missing[name]=miss
    result={'nbt_hash':True,'view_pngs':len(manifest['views']),'reference_originals':originals,'reference_zip_bytes_exact':True,'font_missing':missing,'pass':not missing}
    (ROOT/'history/delivery_file_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
    assert not missing,'Missing visible Chinese glyphs'
if __name__=='__main__':main()
