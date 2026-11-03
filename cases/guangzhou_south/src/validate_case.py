"""Final-NBT checks for this terminal; collision/operations and fidelity are separate."""
from pathlib import Path
import argparse,json,sys,collections
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from hafusion.case_io import dump,sha
CASE=Path(__file__).resolve().parents[1]
def check(run):
 path=CASE/'runs'/run;b=load_build(path/'building.nbt',Limits(cells=40_000_000,nodes=32_000_000));p=json.loads((path/'params_used.json').read_text());r=json.loads((path/'construction_records.json').read_text());checks=[]
 def add(id,ok,detail):checks.append({'id':id,'status':'pass' if ok else 'fail','detail':detail})
 def at(q):return b.blocks.get(tuple(q),'minecraft:air')
 def solid(q):return states.support_cube(at(q))
 add('readback_bounds',all(all(0<=q[i]<b.size[i] for i in range(3)) for q in b.blocks),{'size_xyz':b.size,'nonair':len(b.blocks)})
 add('state_vocabulary',all(states.validate(s) for s in set(b.blocks.values())),{'states':len(set(b.blocks.values()))})
 add('six_unequal_vaults',len(r['roof_sections'])==6 and len(set(x['span_blocks'] for x in r['roof_sections']))>1,r['roof_sections'])
 add('staggered_north_south_roof_edges',len(set(x['north_end_z'] for x in r['roof_sections']))==6 and len(set(x['south_end_z'] for x in r['roof_sections']))==6,{'north':[x['north_end_z'] for x in r['roof_sections']],'south':[x['south_end_z'] for x in r['roof_sections']]})
 pts=[]
 for x in [120,310,500]:
  zs=[z for z in range(280,381) if any('white_stained_glass' in at((x,y,z)) for y in range(45,55))];pts.append({'x':x,'width':max(zs)-min(zs)+1 if zs else 0})
 add('spine_flared_ends',pts[0]['width']>pts[1]['width']>0 and pts[2]['width']>pts[1]['width'],pts)
 failures=[q for q in r['clearance'] if at(q['xyz'])!='minecraft:air'];add('public_axis_and_28_track_clearances',not failures,{'samples':len(r['clearance']),'failed':failures[:10]})
 ts=r['tracks'];add('twenty_eight_track_corridors',len(ts)==28 and len(set(q['x'] for q in ts))==28 and all('chain' in at((q['x']-1,p['rail_y'],330)) for q in ts),{'count':len(ts),'decorative_only':True})
 ps=r['platforms'];add('fifteen_separate_platform_bodies',len(ps)==15 and all('yellow_terracotta' in at((q['xrange'][0],p['platform_y'],150)) for q in ps),{'count':len(ps)})
 gaps=[]
 for c in r['columns']:
  x,y,z=c['xyz']
  for dx in range(c['width']):
   for dz in range(c['width']):
    if not solid((x+dx,y-1,z+dz)):gaps.append([x+dx,y-1,z+dz,c['component_id']])
 add('columns_have_full_bearing',not gaps,{'checked':len(r['columns']),'missing':len(gaps),'examples':gaps[:8]})
 entries=[]
 for e in r['entries']:
  x,y,z=e['x'],e['floor_y'],e['z'];fail=[]
  for xx in range(x-3,x+4):
   if not solid((xx,y,z)) or at((xx,y+1,z))!='minecraft:air' or at((xx,y+2,z))!='minecraft:air':fail.append(xx)
  entries.append({'id':e['component_id'],'z':z,'floor_y':y,'failed_x':fail})
 add('entry_floor_and_headroom',all(not e['failed_x'] for e in entries),entries)
 add('east_west_dropoff_levels_differ',set(e['floor_y'] for e in r['entries'] if 'west' in e['component_id'])=={22} and set(e['floor_y'] for e in r['entries'] if 'east' in e['component_id'])=={14},'west y22; east y14; arrival surface y2')
 lost=[q for q in r['lamps'] if at(q['xyz']).split('[')[0]!='minecraft:'+q['material']]
 add('recorded_lamps_survive_assembly',not lost,{'checked':len(r['lamps']),'lost_count':len(lost),'examples':lost[:8]})
 wrong=[]
 for q,s in b.blocks.items():
  if states.family(s)!='pane':continue
  n,props=states.parse_state(s)
  for name,off in states.DIRS.items():
   other=at(tuple(q[i]+off[i] for i in range(3)));expected=states.family(other)=='pane' or states.support_cube(other)
   if props[name]!=str(expected).lower():wrong.append([q,name])
 add('final_pane_bar_connections',not wrong,{'mismatches':len(wrong)})
 unsupported=[q for q in r['seats'] if not solid((q[0],q[1]-1,q[2]))];add('waiting_seats_have_floors',not unsupported,{'seats':len(r['seats']),'unsupported':unsupported[:5]})
 counts=collections.Counter(s.split('[')[0] for s in b.blocks.values());add('warm_and_cool_lighting',counts['minecraft:sea_lantern']>0 and counts['minecraft:glowstone']>0,{'sea_lantern':counts['minecraft:sea_lantern'],'glowstone':counts['minecraft:glowstone']})
 add('shells_remain_hollow',all(at((x,32,z))=='minecraft:air' for x in [185,210,265,290,335,360,410,435] for z in [301,359]),'16 samples below roof; no solid roof vault')
 add('small_signage_markers',counts['minecraft:gold_block']==8,{'gold_marker_count':counts['minecraft:gold_block'],'literal_voxel_text':False})
 res={'run':run,'source_nbt_sha256':sha(path/'building.nbt'),'checks':checks,'passed':sum(x['status']=='pass' for x in checks),'failed':sum(x['status']=='fail' for x in checks),'visual_status':'separate_review','game_status':'pending','limits':['sampled geometry, not survey accuracy','stairs/road cell slopes do not establish game collision/pathfinding','rail corridors and trains decorative, no Create operations']}
 dump(path/'validation.json',res);print(json.dumps({k:res[k] for k in ['run','passed','failed']}));print(json.dumps([x for x in checks if x['status']=='fail'],ensure_ascii=False));return res
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();raise SystemExit(bool(check(a.run)['failed']))
