"""Verify exact replay and constrained alternate variation from independently built NBTs."""
from pathlib import Path
import hashlib,json,sys,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
base,replay,alt=sys.argv[1:4];R=ROOT/'runs'/base
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
eq={f.stem:h(f)==h(ROOT/'runs'/replay/f.name)for f in R.glob('*.nbt')}
a=load_build(R/'Taisho15.nbt',Limits(cells=4000000,nodes=20000000));b=load_build(ROOT/'runs'/alt/'Taisho15.nbt',Limits(cells=4000000,nodes=20000000))
changed=sum(a.blocks.get(q,'minecraft:air')!=b.blocks.get(q,'minecraft:air')for q in a.blocks.keys()|b.blocks.keys())
s=json.loads((R/'spec.json').read_text());t=json.loads((ROOT/'runs'/alt/'spec.json').read_text());ta=json.loads((ROOT/'runs'/alt/'terrain_audit.json').read_text());baseby={x['id']:x for x in s['buildings']}
layout=[{'id':x['id'],'base':baseby[x['id']]['origin'],'alternate':x['origin'],'base_rotation':baseby[x['id']]['rotation'],'alternate_rotation':x['rotation']}for x in t['buildings']if x['origin']!=baseby[x['id']]['origin']or x['rotation']!=baseby[x['id']]['rotation']]
bad=[]
if ta['protected_changed']:bad.append('protected terrain changed')
if h(R/'Terrain_Input.nbt')!=h(ROOT/'runs'/alt/'Terrain_Input.nbt'):bad.append('terrain input changed')
if len(t['buildings'])!=18:bad.append('building count')
assert all(eq.values()) and not bad and changed>0
out={'seed':s['seed'],'alternate_seed':t['seed'],'identical_replay':eq,'changed_cells':changed,'layout_changes':layout,'scope_violations':bad,'alternate_terrain_protected_changes':ta['protected_changed'],'scope':'Same seed identical NBT including entities. Alternate seed changes candidate selection, road material and clustered plants; terrain input and program recipes remain fixed. One alternate sample is not a universal solver test.'}
(R/'repro_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'identical':all(eq.values()),'changed_cells':changed,'layout_changes':len(layout),'errors':bad}))
