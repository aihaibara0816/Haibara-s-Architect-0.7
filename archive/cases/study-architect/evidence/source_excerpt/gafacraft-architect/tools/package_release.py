"""Archive all source and real outputs with checksums; exclude runtime caches."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.legacy import ROOT
from architect import __version__

def include(path):
    rel=path.relative_to(ROOT)
    return path.is_file() and not any(part in ("__pycache__",".git",".venv") or part.startswith(".architect-build-") for part in rel.parts) and path.suffix!=".pyc" and rel.as_posix()!="DELIVERY_MANIFEST.json"

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);args=p.parse_args()
    if args.out.exists():raise ValueError("Release archive already exists; use a new filename")
    files=sorted(p for p in ROOT.rglob("*") if include(p))
    manifest={"release":"GAFAcraft Architect "+__version__,"date":"2026-10-20","note":"SHA-256 over each uncompressed member; manifest itself excluded. No model weights or game runtime bundled. UPGRADE_REVIEW.html is the current release report; REVIEW.html and other v0.1 reports are retained baseline history.","files":[{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    m=ROOT/"DELIVERY_MANIFEST.json";m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with zipfile.ZipFile(args.out,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for path in files+[m]:z.write(path,"gafacraft-architect/"+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(args.out) as z:
        if z.testzip() is not None:raise ValueError("ZIP CRC check failed")
        for entry in manifest["files"]:
            raw=z.read("gafacraft-architect/"+entry["path"])
            if len(raw)!=entry["bytes"] or hashlib.sha256(raw).hexdigest()!=entry["sha256"]:raise ValueError("Archive content mismatch")
    print(json.dumps({"file":str(args.out.resolve()),"files":len(files)+1,"bytes":args.out.stat().st_size,"sha256":hashlib.sha256(args.out.read_bytes()).hexdigest(),"crc_and_member_hashes":"pass"},ensure_ascii=False))
if __name__=="__main__":main()
