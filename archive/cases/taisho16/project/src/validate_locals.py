from pathlib import Path
import sys,json,subprocess,concurrent.futures
root=Path(__file__).resolve().parents[1];run=sys.argv[1];r=root/'runs'/run
ids=[p.stem for p in r.glob('*.nbt')if p.stem not in['Taisho15','Terrain_Input']]
def task(g):
 p=subprocess.run([sys.executable,str(root/'src/audit_more.py'),run,g],capture_output=True,text=True)
 if (r/(g+'_audit.json')).exists():q=json.loads((r/(g+'_audit.json')).read_text());return {'id':g,'errors':q['errors']}
 return {'id':g,'error':p.stderr[-2000:]}
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
 for q in pool.map(task,ids):print(json.dumps(q),flush=True)
