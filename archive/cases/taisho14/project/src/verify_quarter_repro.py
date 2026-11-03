"""Compare independently generated S05, REPLAY and ALT runs."""
from pathlib import Path
import hashlib,json,sys,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
base,replay,alt=(sys.argv[1:4] if len(sys.argv)>3 else ['Q03','REPLAY14','ALT14'])
eq={f.stem:hashlib.sha256(f.read_bytes()).hexdigest()==hashlib.sha256((ROOT/'runs'/replay/f.name).read_bytes()).hexdigest()for f in(ROOT/'runs'/base).glob('*.nbt')}
a=load_build(ROOT/'runs'/base/'Taisho14.nbt',Limits(cells=4000000,nodes=20000000));b=load_build(ROOT/'runs'/alt/'Taisho14.nbt',Limits(cells=4000000,nodes=20000000));changes=[];pairs=collections.Counter();bad=[]
allowed={'minecraft:air','minecraft:cobblestone','minecraft:andesite','minecraft:mossy_cobblestone','minecraft:short_grass','minecraft:fern','minecraft:oxeye_daisy','minecraft:dandelion'}
for q in a.blocks.keys()|b.blocks.keys():
 av=a.blocks.get(q,'minecraft:air');bv=b.blocks.get(q,'minecraft:air')
 if av!=bv:
  changes.append(q);pairs[av+' -> '+bv]+=1
  if not all(v.split('[')[0]in allowed or v.startswith('minecraft:potted_')for v in[av,bv]):bad.append(q)
assert all(eq.values())and not bad
out={'seed':141145,'alternate_seed':141146,'identical_replay':eq,'changed_cells':len(changes),'scope_violations':bad,'material_pairs':dict(pairs),'scope':'Seed varies surface patches and allowed planting; building layout is authored, not randomized.'}
(ROOT/'runs'/base/'repro_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('reproducible',all(eq.values()),'changed',len(changes),'violations',len(bad))
