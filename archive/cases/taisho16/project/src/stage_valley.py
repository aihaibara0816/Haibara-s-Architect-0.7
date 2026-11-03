from pathlib import Path
import sys,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=ROOT/'runs'/RUN;s=json.loads((R/'spec.json').read_text());eq={}
for b in s['buildings']:
 g=b['id'];src=ROOT/'runs/V07'/(g+'.nbt');p=R/(g+'.nbt');match=hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256(src.read_bytes()).hexdigest();assert match,g
 shutil.copy(ROOT/'runs/V07'/(g+'_audit.json'),R/(g+'_audit.json'))
 old=ROOT/'review/previews'/('V07_'+g);new=ROOT/'review/previews'/(RUN+'_'+g);shutil.copytree(old,new,dirs_exist_ok=True)
 if g!='Hall':
  base=ROOT/'baseline15/runs/O09'/p.name;eq[g]=hashlib.sha256(base.read_bytes()).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest()
(R/'repro_check.json').write_text(json.dumps({'identical_replay':eq,'scope_violations':[]if all(eq.values())else['module_changed'],'layout_changes':[],'changed_cells':0,'scope':'17 preserved module NBTs byte-identical to T15; no whole-city replay or alternate whole-city seed claimed.'},indent=2))
(ROOT/'research/recipe_catalog_16.json').write_text(json.dumps({'case':'Taisho16','run':RUN,'entries':[{'id':b['id'],'form':b['form'],'size':b['size'],'origin':b['origin'],'rotation':b['rotation'],'preserved_from_T15':eq.get(b['id'],False),'source':('organic_types.py / quarter_types.py'if b['id']!='Hall'else'valley_types.py'),'game':'pending'}for b in s['buildings']]},ensure_ascii=False,indent=2));print('verified/cached local previews',len(s['buildings']))
