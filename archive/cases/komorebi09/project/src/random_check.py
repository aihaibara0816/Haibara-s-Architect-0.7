from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import town_states
from vendor.inspect_build import load_build,Limits
from vanilla_preview import applications
A=ROOT/'runs'/sys.argv[1];B=ROOT/'runs'/sys.argv[2];C=ROOT/'runs'/sys.argv[3]
a=load_build(A/'Komorebi09.nbt',Limits(cells=1000000,nodes=8000000));c=load_build(C/'Komorebi09.nbt',Limits(cells=1000000,nodes=8000000));oa=json.loads((A/'owners.json').read_text());oc=json.loads((C/'owners.json').read_text());diff=[];bad=[]
for q in set(a.blocks)|set(c.blocks):
 av=a.blocks.get(q,'minecraft:air');cv=c.blocks.get(q,'minecraft:air')
 if av==cv:continue
 key=','.join(map(str,q));owners=[oa.get(key,''),oc.get(key,'')];ok=all(v.startswith('plant.')or not v for v in owners)or (av.startswith('minecraft:potted_')and cv.startswith('minecraft:potted_'))
 diff.append(q)
 if not ok:bad.append([q,av,cv,owners])
invalid=[]
for st in set(a.blocks.values()):
 if st=='minecraft:air':continue
 try:
  if not applications(st):invalid.append(st)
 except Exception as e:invalid.append([st,str(e)])
same=(A/'Komorebi09.nbt').read_bytes()==(B/'Komorebi09.nbt').read_bytes();r=dict(same_seed_byte_identical=same,changed_cells=len(diff),out_of_scope=bad,official_blockstate_model_resolution_failures=invalid,seed_a=1145,seed_b=2718,scope='Plant-only variation, fixed 18 lots/programs/rooms/roads and lamps; not game execution')
(A/'random_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False)[:2000]);assert same and not bad and not invalid
