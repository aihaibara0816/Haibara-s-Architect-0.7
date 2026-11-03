"""Check the requested massing/colour/roof/landscape changes from final source records."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs'/sys.argv[1]
s=json.loads((R/'spec.json').read_text());homes=[b for b in s['buildings']if b['family']=='village'];shops=[b for b in s['buildings']if b['family']=='qilou'];trees=s['trees'];land=s['landscape']
assert len(s['buildings'])==44 and len(homes)==32 and len(shops)==12
tall={b['id']:b['levels']for b in homes if b['levels']>10};assert tall=={'A3':11,'E2':12}
large={b['id']:b['w']for b in shops if b['kind']=='large'};assert large=={'N03':46,'S01':38,'S04':51}
roofs=collections.Counter(b['facade_revision']['roof']for b in shops);assert roofs['flat']>=4 and len(roofs)>=3
palette=collections.Counter(b['facade_revision']['palette']for b in s['buildings']);assert len(palette)>=7
assert land['planted_ground_cells']>1000
assert not(set(map(tuple,land['planting_cells']))&set(map(tuple,s['road_cells'])))
assert not(set(map(tuple,land['planting_cells']))&set(map(tuple,s['lane_cells'])))
assert all(t['wood_blocks']>0 and t['leaf_blocks']>10 for t in trees)
main=next(t for t in trees if t['id']=='plaza_banyan');assert main['branch_segments']>=20 and main['leaf_clusters']>=8
assert all(b['facade_revision']['covered_front_strip']for b in shops)
result={'pass':True,'source_nbt_sha256':s['source_nbt_sha256'],'buildings':44,'qilou':12,'homes':32,'tall_homes':tall,'large_qilou_frontages':large,'qilou_roof_types':dict(roofs),'whole_building_palette_counts':dict(palette),'planted_ground_cells':land['planted_ground_cells'],'trees':len(trees),'banyan_branch_segments':main['branch_segments'],'banyan_leaf_clusters':main['leaf_clusters'],'scope':'Record and geometry ownership checks; tree silhouette still requires actual image review. This case is original design, not a botanical simulation.'}
(R/'revision_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
