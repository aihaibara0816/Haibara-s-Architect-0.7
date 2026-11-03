from pathlib import Path
import sys,subprocess,json
P=Path(__file__).resolve().parents[1];run=sys.argv[1];R=P/'runs'/run;V=P/'review/previews'/(run+'_ModernFactory01');reports=[]
for f in sorted(R.glob('camera_batch_*.json'),key=lambda p:int(p.stem.rsplit('_',1)[1])):
 subprocess.run([sys.executable,str(P/'src/preview.py'),run,str(f)],check=True)
 reports.extend(json.loads((V/'render_report.json').read_text()))
(V/'render_report.json').write_text(json.dumps(reports,indent=2));print('rendered',len(reports))
