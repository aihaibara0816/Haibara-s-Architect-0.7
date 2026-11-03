"""Portable HAF + CTF source, reviewed evidence, original states and feedback."""
from pathlib import Path
import json,hashlib,zipfile
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1];DEST=CASE/'deliverables'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[]
 for p in HAF.rglob('*'):
  if not p.is_file():continue
  q=p.relative_to(HAF);t=q.parts
  if any(x in t for x in ['__pycache__','.git','cache','cache_replay','scene','game_templates','deliverables']):continue
  if t[0] in ['hafusion','research_lab','tests','tools']:ok=p.suffix=='.py'
  elif t[0]=='support':ok=True
  elif t[0]=='case':ok=len(t)>1 and t[1] in ['src','vendor'] and p.suffix in ['.py','.md','.txt']
  elif t[0]=='ha03':ok=len(t)>1 and t[1] in ['architect','schema','docs','tools','vendor','examples'] and p.suffix in ['.py','.json','.md','.txt']
  elif t[0]=='upstream':ok=p.suffix in ['.py','.md','.txt'] or 'LICENSE' in p.name
  elif t[0]=='learning':ok=True
  elif t[0]=='cases' and len(t)>1 and t[1]=='guangzhou_ctf':
   ok=True
   if 'runs' in t:
    run=t[t.index('runs')+1];ok=run in ['V1','V1_replay','V1_other_seed','facade_sample_v2']
    if run in ['V1_r04','V1_r05','V1_review01']:ok=p.name in ['building.nbt','build_report.json','params_used.json']
    if run in ['V1_replay','V1_other_seed'] and p.name in ['blocks.json','components.json','rooms.json']:ok=False
   if 'previews' in t:ok=t[t.index('previews')+1] in ['V1','facade_sample_v2'] and p.suffix in ['.png','.json']
   if 'history' in t:ok=p.suffix in ['.py','.json','.md','.txt']
   if p.name in ['report_script.js','final_contact.jpg']:ok=False
  elif t[0]=='cases' and len(t)>1 and t[1]=='shenzhen_press':
   ok=(len(t)>2 and t[2]=='src') or str(q) in ['cases/shenzhen_press/research/parameters.json','cases/shenzhen_press/input/manifest.json','cases/shenzhen_press/runs/V2/building.nbt','cases/shenzhen_press/runs/V2/build_report.json','cases/shenzhen_press/README.md','cases/shenzhen_press/release.json']
  else:ok=len(t)==1 and p.name in ['README.md','AGENTS.md','agent_config.json','ATTRIBUTION.md','CHANGELOG.md','requirements-core.lock.txt','requirements-model-optional.txt']
  if ok:files.append(p)
 inventory=[{'path':str(p.relative_to(HAF)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]
 dest=DEST/'HAF_CTF_V1_Source.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(files):z.write(p,'HAF_Mainline/'+str(p.relative_to(HAF)))
  z.writestr('HAF_Mainline/SOURCE_INVENTORY.json',json.dumps(inventory,ensure_ascii=False,indent=2))
  z.writestr('HAF_Mainline/ARCHIVE_SCOPE.txt','HAF core, CTF V1 runnable source, photos/plans, params, NBT, actual previews, revisions and feedback. Shenzhen V2 includes minimal reproducible source and baseline NBT; use its earlier full archive for old photos/reviews. Original HA0.3 and Canton V5 history remains in the earlier archives; large SKP inputs are not duplicated. Reference images retain original copyright and are research evidence, not a new training dataset. Preview textures and Minecraft runtime acceptance remain unverified.\n')
 print(json.dumps({'file':str(dest),'bytes':dest.stat().st_size,'members':len(files),'sha256':sha(dest)},ensure_ascii=False))
if __name__=='__main__':main()
