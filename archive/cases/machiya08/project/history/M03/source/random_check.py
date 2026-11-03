from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from vendor.inspect_build import load_build,Limits
from vanilla_preview import applications
A=ROOT/'runs'/sys.argv[1];B=ROOT/'runs'/sys.argv[2];C=ROOT/'runs'/sys.argv[3]
a=load_build(A/'Machiya08.nbt',Limits(cells=2_000_000,nodes=6_000_000));c=load_build(C/'Machiya08.nbt',Limits(cells=2_000_000,nodes=6_000_000));oa=json.loads((A/'owners.json').read_text());oc=json.loads((C/'owners.json').read_text())
same=(A/'Machiya08.nbt').read_bytes()==(B/'Machiya08.nbt').read_bytes();diff=[];bad=[]
for p in set(a.blocks)|set(c.blocks):
 av=a.blocks.get(p,'minecraft:air');cv=c.blocks.get(p,'minecraft:air')
 if av==cv:continue
 key=','.join(map(str,p));owners=[oa.get(key,''),oc.get(key,'')];ok=any(o.startswith(('plant.',)) for o in owners);r={'pos':p,'before':av,'after':cv,'owners':owners,'allowed':ok};diff.append(r)
 if not ok:bad.append(r)
invalid=[]
for st in set(a.blocks.values()):
 if st=='minecraft:air':continue
 try:
  if not applications(st):invalid.append(st)
 except Exception as e:invalid.append([st,str(e)])
out={'same_seed_byte_identical':same,'seed_a':1145,'seed_b':2718,'changed_cells':len(diff),'changes':diff,'out_of_scope':bad,'official_blockstate_model_resolution_failures':invalid,'scope':'same-seed NBT bytes; alternate seed constrained to plant groups; official JSON model selection available. Not client execution.'}
(A/'random_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='changes'},ensure_ascii=False));assert same and not bad and not invalid
