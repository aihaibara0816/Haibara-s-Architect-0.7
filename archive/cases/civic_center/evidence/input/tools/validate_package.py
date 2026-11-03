#!/usr/bin/env python3
"""Validate the frozen design handoff, not an HAF build or Minecraft world."""
from pathlib import Path
import hashlib,json,re,sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def check(condition,label):
 if not condition:raise ValueError(label)
 checks.append(label)
checks=[]
try:
 doc=(ROOT/'Civic.html').read_text()
 m=read('data/spatial.json'); handoff=read('data/handoff.json')
 embedded=json.loads(re.search(r'<script type="application/json" id="spatial-data">(.*?)</script>',doc,re.S)[1])
 check(m==embedded,'spatial JSON equals the confirmed HTML data')
 check(hashlib.sha256((ROOT/'Civic.html').read_bytes()).hexdigest()==handoff['source_sha256'],'confirmed source HTML hash')
 check(m['version']=='0.3-offset-openings','V0.3 opening geometry selected')
 groups=m['facade_opening_groups']['groups']; floors={f['floor']:f for f in m['floors']}
 check(len(floors)==7 and len(m['cores'])==3 and len(m['voids'])==2,'floor core and void inventory')
 check(m['facade_opening_groups']['seed']==20261026,'fixed opening seed')
 counts={'floors':len(floors),'window_groups':len(groups),'openings':sum(len(g['openings']) for g in groups),'ledges':sum(len(g['ledges']) for g in groups),'planted_ledges':sum(l['planted'] for g in groups for l in g['ledges']),'roof_equipment':len(m['roof_equipment'])}
 check(counts==handoff['counts'],'frozen geometry counts')
 ids=[g['id'] for g in groups]+[w['id'] for g in groups for w in g['openings']]+[l['id'] for g in groups for l in g['ledges']]
 check(len(ids)==len(set(ids)),'unique opening and ledge IDs')
 for g in groups:
  a,b=g['allowed_u_m']; h=floors[g['floor']]['height']
  check(all(a<=w['u0_m']<w['u1_m']<=b and 0<=w['sill_m']<w['head_m']<=h for w in g['openings']),g['id']+' opening envelope')
  check(all(a<=l['u0_m']<l['u1_m']<=b for l in g['ledges']),g['id']+' ledge envelope')
 resolved=read('data/facade-resolved.json')['groups']
 check([g['id'] for g in groups]==[g['id'] for g in resolved],'derived facade group correspondence')
 for src,out in zip(groups,resolved):
  base=floors[src['floor']]['elevation']; face=src['face']
  plane=(src['depth_cell']+(face in 'NE'))*m['grid']
  check(out['plane_m']==plane and len(src['openings'])==len(out['openings']),src['id']+' facade depth and count')
  for w,v in zip(src['openings'],out['openings']):
   check(all(v[k]==value for k,value in w.items()),w['id']+' frozen window fields')
   bounds=v['surface_bounds_xyzxyz_m']
   expected=([w['u0_m'],base+w['sill_m'],plane,w['u1_m'],base+w['head_m'],plane] if face in 'SN' else [plane,base+w['sill_m'],w['u0_m'],plane,base+w['head_m'],w['u1_m']])
   check(bounds==expected,w['id']+' local surface coordinates')
  for l,v in zip(src['ledges'],out['ledges']):
   check(all(v[k]==value for k,value in l.items()) and v['absolute_top_y_m']==base+l['top_m'],l['id']+' frozen ledge fields')
 for room in read('data/interior-handoff.json')['rooms']:
  actual=sorted([[i,j] for i,j,kind,rid in floors[room['floor']]['cells'] if rid==room['id']])
  check(actual==room['occupied_cells'] and room['occupied_area_m2']==len(actual)*m['grid']**2,room['id']+' actual interior occupancy')
 floor2={(c[0],c[1]) for c in floors[2]['cells']}
 check(all((i,j) not in floor2 for i in range(9,17) for j in range(13,19)),'second floor atrium is empty')
 check(all((i,j) in floor2 for i in range(22,26) for j in range(19,21)),'second floor bridge retained')
 check(all((i,j) not in floor2 for i in range(22,26) for j in list(range(13,19))+list(range(21,24))),'second floor passage open outside bridge')
 views=read('data/view-index.json')
 for v in views:
  if 'svg' not in v:continue
  svg=(ROOT/v['svg']).read_text(); ET.fromstring(svg)
  from_doc=re.search(r'<div class="drawing" id="'+v['id']+r'">(<svg\b[\s\S]*?</svg>)</div>',doc)[1]
  check(svg==from_doc,v['id']+' exact current diagram')
 check(len([v for v in views if 'svg' in v])==15,'all fifteen technical diagrams included')
 manifest=read('manifest.json')
 for item in manifest['files']:
  p=ROOT/item['path']
  check(p.is_file() and p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']+' integrity')
 print(json.dumps({'status':'pass','scope':'handoff integrity and same-source consistency only','checks_passed':len(checks),'counts':counts,'checks':checks,'not_checked':['HAF adapter implementation','voxelized building','actual doors/stairs/collisions','structural or code compliance','Minecraft import or lighting']},ensure_ascii=False,indent=2))
except Exception as e:
 print(json.dumps({'status':'fail','error':str(e),'checks_passed_before_failure':len(checks)},ensure_ascii=False,indent=2))
 sys.exit(1)
