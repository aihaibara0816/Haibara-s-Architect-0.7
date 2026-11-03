"""Archive reproducible code, inputs, final build, views and feedback; no transient meshes."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert json.loads((ROOT/'history/delivery_file_qa.json').read_text())['pass']
    assert json.loads((ROOT/'history/delivery_browser_qa.json').read_text())['pass']
    assert json.loads((ROOT/'history/portable_replay.json').read_text())['nbt_byte_equal']
    # Compact placement pack with exact module-relative origins and one reader guide.
    modules=OUT/'广州塔_V5_分块与放置说明.zip'
    with zipfile.ZipFile(modules,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted((ROOT/'runs/V5_r02/modules').glob('*.nbt')):z.write(f,'modules/'+f.name)
        z.write(ROOT/'runs/V5_r02/placement_manifest.json','placement_manifest.json')
        z.write(ROOT/'README.txt','README.txt')
    archive=OUT/'广州塔_V5_代码建筑与反馈记录.zip'
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(ROOT);s=rel.as_posix()
        if any(x.startswith('.') for x in rel.parts) or '__pycache__' in rel.parts or p.suffix=='.pyc':continue
        if s.startswith(('views/scene/','views/raw/','reports/reference_assets/')):continue
        if s.startswith('history/') and (p.suffix in ['.png','.jpg'] or p.name in ['qa_feedback_download.json','upload_request.json','upload_results.json','delivery_index.json']):continue
        if s.startswith('deliverables/') and (p.suffix=='.zip' or any('.assets' in part for part in rel.parts)):continue
        # Failed r01 raw block list is recoverable from its source; retain its diagnostics and NBT.
        if s=='runs/V5_r01/blocks.json':continue
        files.append(p)
    manifest={'schema':'gafacraft-archive-0.1','final_run':'V5_r02','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('canton-v5/ARCHIVE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        for p in files:z.write(p,'canton-v5/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert z.read('canton-v5/runs/V5_r02/canton280_plaza_v5.nbt')==(OUT/'GAFAcraft_Canton280_V5.nbt').read_bytes()
        for rec in manifest['files']:assert hashlib.sha256(z.read('canton-v5/'+rec['path'])).hexdigest()==rec['sha256']
    result={'archive':archive.name,'archive_sha256':sha(archive),'bytes':archive.stat().st_size,'members_verified':len(files),'module_archive':{'name':modules.name,'bytes':modules.stat().st_size,'sha256':sha(modules)},'pass':True}
    (ROOT/'history/delivery_index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
