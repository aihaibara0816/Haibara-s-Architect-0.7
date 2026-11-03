"""Independent NBT checks; conservatively treat occupied blocks as obstacles to 2-cell clear walking."""
from pathlib import Path
import sys,json,argparse,hashlib,collections,gzip
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
def main(run):
 R=C/'runs'/run;read=lambda f:json.loads((R/f).read_text());p=read('params_used.json');b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));blocks=b.blocks;checks=[]
 def check(id,ok,details):checks.append(dict(id=id,status='pass' if ok else 'fail',details=details));print(id,checks[-1]['status'],str(details)[:500],flush=True)
 def clear(x,y,z):return (x,y,z) not in blocks and (x,y+1,z) not in blocks
 def full(x,y,z):
  s=blocks.get((x,y,z));return bool(s and states.support_cube(s))
 def floor_walk(start,rect):
  x0,z0,x1,z1=rect;y=start[1];seen=set();todo=collections.deque([(start[0],start[2])])
  while todo:
   x,z=todo.popleft()
   if (x,z) in seen or not(x0<=x<x1 and z0<=z<z1) or not clear(x,y,z) or not full(x,y-1,z):continue
   seen.add((x,z));todo.extend([(x+1,z),(x-1,z),(x,z+1),(x,z-1)])
  return seen
 check('exactly_six_towers_10_15',len(p['towers'])==6 and [t['storeys'] for t in p['towers']]==[10,10,10,15,15,15],[(t['id'],t['storeys']) for t in p['towers']])
 units=read('units.json');counts=collections.Counter(u['tower'] for u in units)
 check('120_units_one_two_per_floor',len(units)==120 and all(counts[t['id']]==t['storeys']*t['units_per_floor'] for t in p['towers']),dict(counts))
 rooms={r['id']:r for r in read('interiors.json')};missing=[];blocked=[];unreachable=[];reachable_cache={}
 for u in units:
  t=next(t for t in p['towers'] if t['id']==u['tower']);f=u['floor_y'];entry=u['entry']
  seen=floor_walk(entry,[t['x']+1,t['z']+1,t['x']+t['w']-1,t['z']+t['d']-1]);reachable_cache[u['id']]=seen
  if not clear(*entry) or not full(entry[0],f-1,entry[2]):blocked.append(u['id'])
  funcs=[rooms[r]['function'] for r in u['rooms']]
  if funcs.count('bedroom')!=2 or not all(v in funcs for v in ['kitchen','bathroom']) or not any(v in funcs for v in ['living','living_dining']):missing.append(u['id'])
  for rid in u['rooms']:
   e=rooms[rid]['entrances'][0]
   if (e[0],e[2]) not in seen:unreachable.append(rid)
 check('all_units_have_home_functions',not missing,{'rooms':len(rooms),'missing':missing})
 check('unit_entries_supported_and_clear',not blocked,blocked)
 check('all_room_entries_reachable_on_floor',not unreachable,unreachable)
 # Space plan confirms 3 clear cells; lamps must be in the lower of the 2 separator layers.
 floor_errors=[]
 for f in read('floor_levels.json'):
  t=next(t for t in p['towers'] if t['id']==f['tower']);fy=f['floor_y'];sample=(t['x']+11 if t['type']=='A' else t['x']+21,t['z']+11 if t['type']=='A' else t['z']+20)
  if not full(sample[0],fy-1,sample[1]) or not all((sample[0],yy,sample[1]) not in blocks for yy in range(fy,fy+3)) or not all((sample[0],yy,sample[1]) in blocks for yy in [fy+3,fy+4]):floor_errors.append(f)
 check('75_levels_three_clear_two_separator',not floor_errors,floor_errors)
 stale=[];wrong=[]
 for l in read('lamps.json'):
  q=tuple(l['xyz']);s=blocks.get(q,'')
  if s.split('[')[0]!='minecraft:'+l['material']:stale.append(l)
  if l['owner'].split('.')[0][0] in ['A','B'] and (q[1]-3)%5!=3:wrong.append(l)
 check('all_lamps_survive_and_are_recessed',not stale and not wrong,{'lamps':len(read('lamps.json')),'lost':stale,'wrong_height':wrong})
 check('selective_home_lighting',0<len([u for u in units if u['lit']])<len(units)*.6,{'lit_units':sum(u['lit'] for u in units),'all_units':120})
 # Stairs: final-NBT tread/landing support plus whole recorded 2-wide ascent and headroom.
 stair_errors=[]
 for st in read('stairs.json'):
  for x,y,z in st['trace']:
   under=blocks.get((x,y-1,z),'')
   if not under or not clear(x,y,z):stair_errors.append({'stair':st['id'],'xyz':[x,y,z],'under':under,'obstacle':[blocks.get((x,y,z)),blocks.get((x,y+1,z))]})
 check('stairs_69_connections_support_headroom',not stair_errors,{'connections':len(read('stairs.json')),'errors':stair_errors[:50],'error_count':len(stair_errors),'scope':'Centre-cell routes; vanilla collision and stair shapes remain game-pending.'})
 entry_errors=[]
 for e in read('entries.json'):
  t=next(t for t in p['towers'] if t['id']==e['id']);x,y,z=e['entry']
  seen=floor_walk((x,y,z),[t['x']-1,t['z']-1,t['x']+t['w']+1,t['z']+t['d']+1]);land=e['core_landing']
  if (land[0],land[2]) not in seen:entry_errors.append(e['id']+'.stairs')
  for u in units:
   if u['tower']==e['id'] and u['floor']==1 and (u['entry'][0],u['entry'][2]) not in seen:entry_errors.append(u['id'])
 check('ground_lobbies_reach_stairs_and_units',not entry_errors,entry_errors)
 path=read('paths.json');err=[]
 for x,z in path['cells_xz']:
  if not full(x,2,z) or not clear(x,3,z):err.append([x,z,blocks.get((x,3,z)),blocks.get((x,4,z))])
 check('entire_declared_path_width_clear',not err,{'cells':len(path['cells_xz']),'blocked':err[:60],'error_count':len(err)})
 ground=floor_walk((52,3,p['size_xyz'][2]-9),[0,0,p['size_xyz'][0],p['size_xyz'][2]]);unreached=[e['id'] for e in read('entries.json') if (e['entry'][0],e['entry'][2]) not in ground]
 check('gate_reaches_six_entries',not unreached,unreached)
 windows=read('windows.json');wc=collections.Counter(w['security'] for w in windows)
 check('mixed_grilles_and_open_windows',all(wc.get(k,0)>0 for k in ['none','cage','flush']),dict(wc))
 mods=read('module_consumption.json');empty=[m['component_id'] for m in mods if not m['placed_cells']]
 check('compiled_furniture_modules_consumed',not empty,{'modules':len(mods),'empty':empty})
 roots=[t for t in read('trees.json') if not full(*t['root']) or 'oak_log' not in blocks.get((t['root'][0],3,t['root'][2]),'')]
 check('tree_roots_supported',not roots,{'trees':len(read('trees.json')),'errors':roots})
 water=[q for q,s in blocks.items() if s.startswith('minecraft:water')];leaks=[]
 for x,y,z in water:
  for q in [(x,y-1,z),(x+1,y,z),(x-1,y,z),(x,y,z+1),(x,y,z-1)]:
   if q not in blocks:leaks.append(q)
 check('pond_cells_contained',not leaks,{'water_cells':len(water),'leaks':leaks[:20]})
 roof_errors=[]
 for t in p['towers']:
  top=3+t['storeys']*5
  for x in range(t['x'],t['x']+t['w']):
   for z in range(t['z'],t['z']+t['d']):
    if not any((x,y,z) in blocks for y in range(top,top+7)):roof_errors.append([x,z])
 check('six_roofs_cover_footprints',not roof_errors,{'missing_columns':roof_errors})
 result={'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'passed':all(x['status']=='pass' for x in checks),'game_status':'pending','visual_status':'pending_user_review','limitations':['Static elevators and decorative furniture; no redstone lift or functional beds/doors','Block-cell traversal is conservative geometry review, not a Minecraft simulation','No real engineering, daylight, fire or planning compliance claim']}
 (R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();r=main(a.run);raise SystemExit(0 if r['passed'] else 1)
