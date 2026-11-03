"""Finalize checks and self-contained report after rendering and world export."""
from pathlib import Path
import sys,json,hashlib,subprocess
C=Path(__file__).resolve().parents[1];run,replay,world,out=sys.argv[1:];R=C/'runs'/run
subprocess.run([sys.executable,str(C/'src/verify_banners.py'),run,world],check=True)
a=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest();b=hashlib.sha256((C/'runs'/replay/'building.nbt').read_bytes()).hexdigest();assert a==b
spec=json.loads((R/'params_used.json').read_text())
(R/'replay_check.json').write_text(json.dumps(dict(seed=spec['design_brief']['seed'],source_run=run,replay=replay,source_sha256=a,replay_sha256=b,exact=True),indent=2))
p=R/'verification.json';v=json.loads(p.read_text());v['preview']='offline NBT renders complete; see visual_review.json for manually inspected views';p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
subprocess.run([sys.executable,str(C/'src/report_detailtown.py'),run,out],check=True)
