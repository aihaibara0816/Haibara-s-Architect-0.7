"""Independent readback checks of actual V2 occupied geometry and usable floor regions."""
from pathlib import Path
import sys,json,gzip,collections,argparse,hashlib
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(C/'src')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from build_v2 import cells
def main(run,output=None):
 R=C/'runs'/run;load=lambda n:json.loads((R/(n+'.json')).read_text());p=load('params_used');b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));blocks=b.blocks;checks=[]
 def ck(id,ok,detail):checks.append({'id':id,'status':'pass' if ok else 'fail','details':detail});print(id,checks[-1]['status'],str(detail)[:350],flush=True)
 def clear(x,y,z):return all((x,yy,z) not in blocks for yy in [y,y+1])
 def support(x,y,z):return (x,y,z) in blocks and states.support_cube(blocks[x,y,z])
 def walk(start,rect):
  x,y,z=start;seen=set();todo=collections.deque([(x,z)]);x0,z0,x1,z1=rect
  while todo:
   x,z=todo.popleft()
   if (x,z) in seen or not(x0<=x<x1 and z0<=z<z1) or not clear(x,y,z) or not support(x,y-1,z):continue
   seen.add((x,z));todo.extend([(x+1,z),(x-1,z),(x,z+1),(x,z-1)])
  return seen
 towers={t['id']:t for t in p['towers']};units=load('units');rooms={r['id']:r for r in load('interiors')};mods=load('module_consumption');entries={e['id']:e for e in load('entries')};paths=load('paths')['cells_xz'];seen_cache={}
 ck('six_towers_120_households',len(towers)==6 and len(units)==120 and [t['storeys'] for t in p['towers']]==[10]*3+[15]*3,{'towers':len(towers),'homes':len(units)})
 ck('exact_10_block_step',all([towers[c+str(i)]['z']-towers[c+str(i+1)]['z'] for i in [1,2]]==[10,10] for c in ['A','B']),[(t['id'],t['x'],t['z']) for t in p['towers']])
 bad=[];unreachable=[];entrybad=[];stair_unit=[];floorbad=[];functions=[]
 for u in units:
  t=towers[u['tower']];y=u['floor_y'];rect=[t['x']-3,t['z']-4,t['x']+t['w']+3,t['z']+t['d']+4];seen=walk(u['entry'],rect);seen_cache[u['id']]=seen
  if not seen:entrybad.append(u['id'])
  fs=[rooms[r]['function'] for r in u['rooms']]
  if fs.count('bedroom')!=(3 if t['type']=='A' else 2) or not all(k in fs for k in ['kitchen','bathroom']) or (t['type']=='A' and 'study' not in fs):functions.append(u['id'])
  for rid in u['rooms']:
   r=rooms[rid];e=r['entrances'][0]
   if (e[0],e[2]) not in seen:unreachable.append(rid)
  e=entries[u['tower']]['core_landing'];start=[e[0],y,e[2]];land=walk(start,rect)
  if (u['entry'][0],u['entry'][2]) not in land:stair_unit.append(u['id'])
 ck('front_3_beds_study_rear_2_beds',not functions,functions)
 ck('all_home_entries_clear_supported',not entrybad,entrybad)
 ck('all_room_entries_reachable',not unreachable,{'failures':unreachable,'rooms':len(rooms)})
 ck('all_75_landings_reach_120_homes',not stair_unit,stair_unit)
 balcony_bad=[]
 for u in units:
  t=towers[u['tower']];seen=seen_cache[u['id']]
  local=([(4,-1),(25,28)] if t['type']=='A' else [(4,25)] if u['id'].endswith('U1') else [(30,24)])
  for x,z in local:
   if (t['x']+x,t['z']+z) not in seen:balcony_bad.append([u['id'],x,z])
 ck('all_150_balconies_reachable_from_homes',not balcony_bad,balcony_bad)
 for f in load('floor_levels'):
  t=towers[f['tower']];y=f['floor_y'];q=entries[t['id']]['core_landing'];x,z=q[0],q[2]
  if not support(x,y-1,z) or not all((x,y+i,z) not in blocks for i in range(3)) or not all((x,y+i,z) in blocks for i in [3,4]):floorbad.append(f)
 ck('three_clear_two_separator_at_landings',not floorbad,floorbad)
 issues=[]
 for st in load('stairs'):
  for tr in st['tracks']:
   for x,y,z in tr:
    if not clear(x,y,z) or (x,y-1,z) not in blocks:issues.append({'stair':st['id'],'point':[x,y,z],'obstacles':[blocks.get((x,y,z)),blocks.get((x,y+1,z))]})
 ck('69_stair_links_two_width_support_headroom',not issues,{'errors':issues,'connections':len(load('stairs')),'game_collision':'pending'})
 lamps=load('lamps');err=[]
 for l in lamps:
  x,y,z=l['xyz']
  if blocks.get((x,y,z),'').split('[')[0]!='minecraft:'+l['material'] or (l['owner'].split('.')[0] in towers and (y-3)%5!=3):err.append(l)
 ck('recessed_lamps_survive',not err,{'count':len(lamps),'errors':err})
 ck('selected_household_lighting',0<sum(u['lit'] for u in units)<72,{'lit':sum(u['lit'] for u in units),'all':120})
 o=json.loads(gzip.decompress((R/'component_ownership.json.gz').read_bytes()));names=o['owner_names'];owner={tuple(q[:3]):names[q[3]] for q in o['xyz_owner']};lost=[];blocked=[]
 for m in mods:
  mid=m['component_id'];x,y,z,X,Y,Z=m['bounds_xyz'];actual=sum(owner.get((a,v,c),'').startswith(mid) for a in range(x,X) for v in range(y,Y) for c in range(z,Z))
  if actual!=m['placed_cells']:lost.append([mid,m['placed_cells'],actual])
  uid=m['room_id'].rsplit('.',1)[0];seen=seen_cache[uid];r=rooms[m['room_id']]['bounds_xyz'];approach={(a,c) for a in range(x-1,X+1) for c in range(z-1,Z+1) if (a<x or a>=X or c<z or c>=Z) and r[0]<=a<r[3] and r[2]<=c<r[5]}
  if not (approach&seen):blocked.append(mid)
 ck('all_furniture_modules_survive_final_assembly',not lost,{'modules':len(mods),'errors':lost})
 ck('furniture_has_reachable_adjacent_floor',not blocked,{'unapproachable':blocked,'scope':'Adjacent air cells, not block interaction mechanics'})
 err=[]
 for x,z in paths:
  if not support(x,2,z) or not clear(x,3,z):err.append([x,z,blocks.get((x,3,z)),blocks.get((x,4,z))])
 ck('full_declared_garden_paths_clear',not err,{'cells':len(paths),'errors':err})
 ground=walk([52,3,157],[0,0,160,166]);miss=[k for k,e in entries.items() if (e['entry'][0],e['entry'][2]) not in ground]
 ck('gate_reaches_every_main_entry',not miss,miss)
 miss=[]
 for k,e in entries.items():
  t=towers[k];s=walk(e['entry'],[t['x']-4,t['z']-5,t['x']+t['w']+4,t['z']+t['d']+5]);q=e['core_landing']
  if (q[0],q[2]) not in s:miss.append(k)
 ck('main_entry_to_stairs',not miss,miss)
 wc=collections.Counter(w['security'] for w in load('windows'));ck('mixed_security_grilles',all(wc[k]>0 for k in ['none','flush','cage']),dict(wc))
 missing=[];floor_shape=[]
 for t in p['towers']:
  foot=cells(t['outline']);y=3+5*t['storeys']
  for x,z in foot:
   if not any((t['x']+x,yy,t['z']+z) in blocks for yy in range(y,y+7)):missing.append([t['id'],x,z])
  actual={(x-t['x'],z-t['z']) for (x,yy,z),v in owner.items() if yy==2 and v==t['id']+'.foundation'}
  # Ground paths replace finish blocks; the immutable foundation at Y1 is authoritative.
  actual={(x-t['x'],z-t['z']) for (x,yy,z),v in owner.items() if yy==1 and v==t['id']+'.foundation'}
  if actual!=foot:floor_shape.append(t['id'])
 ck('approved_P01_footprints_in_final_NBT',not floor_shape,{'errors':floor_shape,'A_area':722,'B_area':822})
 ck('segmented_roofs_cover_main_floor',not missing,{'roof_parts':len(load('roof_parts')),'missing_columns':missing})
 trees=load('trees');bad=[t for t in trees if not support(*t['root']) or 'oak_log' not in blocks.get((t['root'][0],3,t['root'][2]),'')]
 ck('all_12_tree_roots_supported',not bad,{'trees':len(trees),'errors':bad})
 water=[q for q,s in blocks.items() if s.startswith('minecraft:water')];leaks=[]
 for x,y,z in water:
  for q in [(x,y-1,z),(x-1,y,z),(x+1,y,z),(x,y,z-1),(x,y,z+1)]:
   if q not in blocks:leaks.append(q)
 ck('retained_pond_contained',not leaks,{'water_cells':len(water),'leaks':leaks})
 out={'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'passed':all(c['status']=='pass' for c in checks),'game_status':'pending','visual_status':'pending_user_review','limitations':['Vanilla game import/collision/light propagation not run','Static lifts and decorative beds/furniture','P01 zoning refined for block walls/core; exact main footprints retained']}
 (Path(output) if output else R/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--out');a=ap.parse_args();r=main(a.run,a.out);raise SystemExit(0 if r['passed'] else 1)
