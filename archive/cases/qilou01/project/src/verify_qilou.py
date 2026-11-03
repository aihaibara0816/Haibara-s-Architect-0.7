"""Replay/seed-scope and assembly checks; input NBT is read back independently."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support')]
import qilou_states
from vendor.inspect_build import load_build,Limits
RUN=sys.argv[1];R=ROOT/'runs'/RUN
groups=['Qilou01','Grocery','Apothecary','Teahouse']
limits=Limits(cells=2000000,nodes=8000000)
replay={g:(R/(g+'.nbt')).read_bytes()==(ROOT/'runs'/(RUN+'_REPLAY')/(g+'.nbt')).read_bytes() for g in groups}
assert all(replay.values()),replay
whole=load_build(R/'Qilou01.nbt',limits)
variant=load_build(ROOT/'runs'/(RUN+'_VARIANT')/'Qilou01.nbt',limits)
changes=[];bad=[]
for q in set(whole.blocks)|set(variant.blocks):
 a=whole.blocks.get(q,'minecraft:air');b=variant.blocks.get(q,'minecraft:air')
 if a!=b:
  changes.append({'position':q,'before':a,'after':b})
  if not (a.startswith('minecraft:potted_') and b.startswith('minecraft:potted_')):bad.append(q)
assert not bad,bad
sp=json.loads((R/'Qilou01_spec.json').read_text());assembly=[]
for bd in sp['buildings']:
 local=load_build(R/(bd['id']+'.nbt'),limits);missing=[];o=bd['origin']
 for q,st in local.blocks.items():
  p=tuple(q[i]+o[i] for i in range(3))
  if whole.blocks.get(p)!=st:missing.append(p)
 assert not missing,(bd['id'],missing)
 assembly.append({'id':bd['id'],'compared_non_air':len(local.blocks),'mismatches':len(missing)})
out={'source_nbt_sha256':hashlib.sha256((R/'Qilou01.nbt').read_bytes()).hexdigest(),'identical_replay':replay,'seed_base':311145,'seed_variant':311146,'changed_cells':len(changes),'changes':changes,'scope_violations':bad,'assembly':assembly,'scope':'Only plant species vary in these authored samples; no random floorplan or facade generator is claimed.'}
(R/'repro_check.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'replay':replay,'changed_cells':len(changes),'scope_violations':len(bad),'assembly_ok':True}))
