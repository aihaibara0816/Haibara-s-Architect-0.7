"""Portable source release including byte-identical original archives."""
from pathlib import Path
import hashlib,json,zipfile,argparse
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(destination):
    files=[]
    for f in sorted(ROOT.rglob('*')):
        if not f.is_file():continue
        r=f.relative_to(ROOT)
        if any(x.startswith('cache') or x=='__pycache__' for x in r.parts[:-1]) or f.suffix in ['.pyc','.tmp']:continue
        if r.as_posix()=='reports/archive_result.json':continue
        if r.parts[0]=='previews' and ('scene' in r.parts or f.suffix=='.bin'):continue
        if r.parts[:2]==('case','deliverables'):continue
        if f.suffix=='.zip' and r.parts[0]=='deliverables':continue
        files.append((f,r.as_posix()))
    for name in ['GAFAcraft_Architect_v0.3_ModelResearch_20261020.zip','广州塔_V5_代码建筑与反馈记录.zip']:
        f=ROOT.parent/'originals'/name;files.append((f,'preserved_originals/'+name))
    manifest={name:{'sha256':sha(f),'bytes':f.stat().st_size} for f,name in files}
    destination=Path(destination);destination.parent.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f,name in files:z.write(f,'HAFusion-0.1/'+name)
        z.writestr('HAFusion-0.1/MANIFEST.sha256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(destination) as z:
        assert z.testzip() is None
        for name,meta in manifest.items():
            b=z.read('HAFusion-0.1/'+name);assert hashlib.sha256(b).hexdigest()==meta['sha256']
    print(json.dumps({'path':str(destination),'bytes':destination.stat().st_size,'sha256':sha(destination),'members':len(manifest)+1},ensure_ascii=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
