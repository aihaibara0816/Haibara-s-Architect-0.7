from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import room_states,nbtlib as n
from detail_lab import states as S
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import parse_state
run=sys.argv[1];R=ROOT/'runs'/run
old=load_build(ROOT/'runs/M06/Machiya08.nbt',Limits(cells=2000000,nodes=6000000));new=load_build(R/'Machiya08.nbt',Limits(cells=2000000,nodes=6000000))
f=n.load(R/'Machiya08.nbt');of=n.load(ROOT/'runs/M06/Machiya08.nbt');changed=[];unexpected=[]
for q in set(old.blocks)|set(new.blocks):
 a=old.blocks.get(q,'minecraft:air');b=new.blocks.get(q,'minecraft:air')
 if a==b:continue
 x,y,z=q;changed.append({'pos':q,'before':a,'after':b})
 interior=8<=x<=22 and 3<=y<=11 and 8<=z<=21
 entry_interface=x in range(14,19) and z==21 and y in [3,4,5]
 if interior and not entry_interface:unexpected.append(q)
assert not unexpected,unexpected
for x in range(9,13):
 for y in [4,5]:assert new.blocks.get((x,y,22),'minecraft:air')=='minecraft:air'
for z in [14,15,16,20,21]:
 for y in [4,5]:assert new.blocks.get((23,y,z),'minecraft:air')=='minecraft:air'
# Explicit head/feet clear cells for the widened entrance, allowing its carpet at feet.
for x in [15,16,17]:
 for z in [21,22,23,24]:
  for y in [3,4]:assert new.blocks.get((x,y,z),'minecraft:air').split('[')[0] in ['minecraft:air','minecraft:brown_carpet']
for x in range(8,13):
 for y in range(3,9):
  for z in range(9,18):assert old.blocks.get((x,y,z))==new.blocks.get((x,y,z))
assert f['entities']==of['entities']
for e in f['blocks']:
 if 'nbt' not in e:continue
 q=tuple(map(int,e['pos']));name,_=parse_state(new.blocks[q]);be=str(e['nbt']['id'])
 expected='minecraft:banner' if name.endswith('_wall_banner') else 'minecraft:sign' if name.endswith('_wall_sign') else 'minecraft:bed' if name.endswith('_bed') else name
 assert expected==be,(q,expected,be)
 if name.endswith('_wall_sign'):
  _,pr=parse_state(new.blocks[q]);d=S.DIRS[pr['facing']];support=tuple(q[i]-d[i]for i in range(3));assert new.blocks.get(support,'minecraft:air')!='minecraft:air'
# Every old interior entity outside the sole removed front-door block region is retained.
ob={tuple(map(int,e['pos'])):e['nbt']for e in of['blocks']if 'nbt'in e};nb={tuple(map(int,e['pos'])):e['nbt']for e in f['blocks']if 'nbt'in e}
for q,be in ob.items():
 x,y,z=q
 if 8<=x<=22 and 3<=y<=11 and 8<=z<=21:assert nb[q]==be
out={'source_nbt_sha256':hashlib.sha256((R/'Machiya08.nbt').read_bytes()).hexdigest(),'baseline':'M06','changed_cells':len(changed),'changes':changed,'unexpected_interior_changes':unexpected,'protected_stair_and_understair':True,'paintings_exactly_preserved':True,'interior_block_entities_preserved':True,'open_front_counter_cells':8,'open_side_window_cells':10,'clear_entry_width':3,'entry_closing_mechanism':False,'game':'pending','scope':'Actual final NBT difference and explicit openings, supports, entity continuity; visual quality needs feedback.'}
(R/'revision_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='changes'},ensure_ascii=False))
