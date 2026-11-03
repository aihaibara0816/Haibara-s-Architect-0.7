"""Append exact top cut views; preserve every baseline camera unchanged."""
from pathlib import Path
import json
CASE=Path(__file__).resolve().parents[1]
p=CASE/'cameras.json';a=json.loads(p.read_text());ids={v['id'] for v in a}
for level in (25,65,110):
 v=dict(next(v for v in a if v['id']=='top'))
 v.update(id=f'plan_{level}',cutY=level)
 if v['id'] not in ids:a.append(v)
v=dict(next(v for v in a if v['id']=='crown'))
v.update(id='crown_rear',eye=[145,156,-100],target=[63,115,56])
if v['id'] not in ids:a.append(v)
v=dict(next(v for v in a if v['id']=='podium_rear'))
v.update(id='podium_oblique',eye=[-120,70,-90],target=[63,20,42],spanX=130,spanZ=130*1500/2100)
if v['id'] not in ids:a.append(v)
p.write_text(json.dumps(a,indent=2)+'\n')

