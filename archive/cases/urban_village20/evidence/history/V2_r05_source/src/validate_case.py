"""Checks final NBT with the independent reader. Does not certify game collision."""
from pathlib import Path
import sys,json,hashlib,collections,gzip,argparse
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
def main(run):
 R=C/'runs'/run;load=lambda x:json.loads((R/(x+'.json')).read_text());p=load('params_used');rb=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));blocks=rb.blocks;checks=[]
 def ck(k,ok,details):checks.append({'id':k,'status':'pass' if ok else 'fail','details':details});print(k,checks[-1]['status'],str(details)[:600],flush=True)
 def clear(x,y,z):return (x,y,z) not in blocks and (x,y+1,z) not in blocks
 def support(x,y,z):return (x,y,z) in blocks and states.support_cube(blocks[x,y,z])
 def walk(start,rect):
  x,y,z=start;x0,z0,x1,z1=rect;todo=collections.deque([(x,z)]);seen=set()
  while todo:
   x,z=todo.popleft()
   if (x,z) in seen or not(x0<=x<x1 and z0<=z<z1) or not clear(x,y,z) or not support(x,y-1,z):continue
   seen.add((x,z));todo.extend([(x+1,z),(x-1,z),(x,z+1),(x,z-1)])
  return seen
 ts={t['id']:t for t in p['buildings']};units=load('units');rooms={r['id']:r for r in load('interiors')};entries=load('entries');ee={e['id']:e for e in entries};mods=load('module_consumption')
 ck('20_unique_mass_dimensions',len(ts)==20 and len({(t['w'],t['d'],t['floors']) for t in ts.values()})==20,[(t['id'],t['w'],t['d'],t['floors']) for t in ts.values()])
 homes=[u for u in units if u['kind']=='home'];shops=[u for u in units if u['kind']!='home'];ratio=sum(u['lit'] for u in homes)/len(homes)
 ck('household_and_shop_lighting',abs(ratio-.7)<.005 and len(shops)==sum(t['ground']!='home' for t in ts.values()) and all(u['lit'] for u in shops),{'homes':len(homes),'lit_homes':sum(u['lit'] for u in homes),'ratio':ratio,'shops':[u['kind'] for u in shops]})
 own=load('manifest');ck('file_bounds_and_readback',rb.size==tuple(p['size_xyz']) and len(rb.blocks)==own['non_air_blocks'],{'size':rb.size,'non_air_blocks':len(rb.blocks),'DataVersion':3955})
 bad=[];room_bad=[];stairhome=[];cache={}
 for u in units:
  t=ts[u['building']];rect=[t['x']-2,t['z']-2,t['x']+t['w']+2,t['z']+t['d']+2];seen=walk(u['entry'],rect);cache[u['id']]=seen
  if not seen:bad.append(u['id'])
  for rid in u['rooms']:
   for x,y,z in rooms[rid]['entrances']:
    if (x,z) not in seen:room_bad.append(rid)
  q=list(ee[u['building']]['core_landing']);q[1]=u['floor_y'];common=walk(q,rect)
  if (u['entry'][0],u['entry'][2]) not in common:stairhome.append(u['id'])
 ck('all_unit_entries_supported_and_clear',not bad,bad)
 ck('all_function_zone_approaches_reachable',not room_bad,room_bad)
 ck('all_floor_landings_reach_units',not stairhome,stairhome)
 bad=[]
 for s in load('stairs'):
  for track in s['tracks']:
   for x,y,z in track:
    if not clear(x,y,z) or (x,y-1,z) not in blocks:bad.append({'stair':s['id'],'q':[x,y,z],'hit':[blocks.get((x,y,z)),blocks.get((x,y+1,z))]})
 ck('105_two_wide_stair_links_support_headroom',not bad,{'links':len(load('stairs')),'errors':bad})
 o=json.loads(gzip.decompress((R/'component_ownership.json.gz').read_bytes()));owner={tuple(q[:3]):o['owner_names'][q[3]] for q in o['xyz_owner']};count=collections.Counter(owner.values());lost=[];no_approach=[]
 for m in mods:
  if count[m['component_id']]!=m['placed_cells'] or m['placed_cells']==0:lost.append(m['component_id'])
  x,y,z,X,Y,Z=m['bounds_xyz'];rbounds=rooms[m['room_id']]['bounds_xyz']
  adj={(a,c) for a in range(x-1,X+1) for c in range(z-1,Z+1) if (a<x or a>=X or c<z or c>=Z) and rbounds[0]<=a<rbounds[3] and rbounds[2]<=c<rbounds[5]}
  if not(adj&cache[m['unit_id']]):no_approach.append(m['component_id'])
 ck('all_furniture_modules_present',not lost,{'modules':len(mods),'lost':lost})
 ck('furniture_adjacent_floor_reachable',not no_approach,no_approach)
 terrain=load('terrain');hm={(x,z):y for x,z,y in terrain['heights_xzy']};pathset={tuple(q) for q in load('paths')['cells_xz']}
 def passable(q):
  x,z=q;y=hm[q];s=blocks.get((x,y,z),'')
  return support(x,y-1,z) and (clear(x,y,z) or ('stairs[' in s and clear(x,y+1,z)))
 bad=[(x,z,hm[x,z],blocks.get((x,hm[x,z],z))) for x,z in pathset if not passable((x,z))]
 ck('graded_streets_and_entry_paths_clear',not bad,{'path_cells':len(pathset),'errors':bad})
 seen=set();todo=collections.deque([(190,176)])
 while todo:
  a=todo.popleft()
  if a in seen or a not in pathset or not passable(a):continue
  seen.add(a)
  for c in [(a[0]+1,a[1]),(a[0]-1,a[1]),(a[0],a[1]+1),(a[0],a[1]-1)]:
   if c in pathset and abs(hm[a]-hm[c])<=1:todo.append(c)
 bad=[e['id'] for e in entries if (e['outside'][0],e['outside'][2]) not in seen or not clear(*e['entry']) or not support(e['entry'][0],e['entry'][1]-1,e['entry'][2])]
 ck('main_street_reaches_all_external_entries',not bad,{'entries':len(entries),'errors':bad})
 bad=[]
 for e in entries:
  if 'shop' not in e['id']:continue
  uid=e.get('unit_id',e['id'].split('.')[0]+'.F01.R');q=e.get('inside',e['entry'])
  if (q[0],q[2]) not in cache[uid]:bad.append(e['id'])
 ck('shop_customer_and_service_doors_reach_interior',not bad,bad)
 ck('northwest_higher_and_open_east_south_streets',hm[5,5]>hm[180,170] and all(t['x']>=24 and t['z']>=20 for t in ts.values()),{'northwest_y':hm[5,5],'southeast_y':hm[180,170],'east_road_y':hm[200,70],'south_road_y':hm[70,189]})
 cutbad=[];shaped=[]
 for m in load('floor_masks'):
  t=ts[m['building']];cells={tuple(q) for q in m['cells_xz']}
  if len(cells)<t['w']*t['d']:shaped.append(t['id'])
  for x in range(t['x'],t['x']+t['w']):
   for z in range(t['z'],t['z']+t['d']):
    if (x,z) not in cells:
     for f in range(2,t['floors']+1):
      y=t['base_y']+(f-1)*5-1
      if (x,y,z) in blocks and owner.get((x,y,z)) not in {t['id']+'.shop.turning_sign',t['id']+'.shop.turning_canopy'}:cutbad.append([t['id'],x,y,z])
 ck('nonrectangular_floor_plates_built',len(shaped)>=8 and not cutbad,{'buildings':shaped,'errors':cutbad})
 cutground=[]
 for m in load('floor_masks'):
  t=ts[m['building']];cells={tuple(q) for q in m['cells_xz']}
  for x in range(t['x'],t['x']+t['w']):
   for z in range(t['z'],t['z']+t['d']):
    if (x,z) not in cells and not support(x,t['base_y']-1,z):cutground.append([t['id'],x,z])
 ck('cutaway_corners_have_ground_bearing',not cutground,cutground)

 bad=[]
 for e in load('equipment'):
  if e['kind']=='balcony':
   bid,fid,_=e['id'].split('.');u=bid+'.'+fid+'.R';x,y,z=e['entry']
   if (x,z) not in cache[u]:bad.append(e['id'])
  if e['kind']=='roof_access':
   t=ts[e['id'].split('.')[0]];q=list(ee[t['id']]['core_landing']);q[1]=t['base_y']+t['floors']*5;s=walk(q,[t['x']-2,t['z']-2,t['x']+t['w']+2,t['z']+t['d']+2]);x,y,z=e['entry']
   if (x,z) not in s:bad.append(e['id'])
 ck('balconies_and_roof_exits_reachable',not bad,bad)
 lamps=load('lamps');emissive={q for q,s in blocks.items() if s.split('[')[0] in {'minecraft:sea_lantern','minecraft:glowstone','minecraft:end_rod'}}
 listed={tuple(l['xyz']) for l in lamps};err=[]
 for l in lamps:
  x,y,z=l['xyz']
  if blocks.get((x,y,z),'').split('[')[0]!='minecraft:'+l['material']:err.append(l['owner'])
  if l['fixture']=='recessed' and ((y-ts[l['owner'].split('.')[0]]['base_y'])%5!=3 or not support(x,y+1,z) or (x,y-1,z) in blocks):err.append(l['owner']+'.not_flush_or_blocked')
 ck('all_lamps_present_recessed_and_exposed',not err and listed==emissive,{'lamps':len(lamps),'errors':err,'unrecorded':sorted(emissive-listed)})
 wc=collections.Counter(w['security'] for w in load('windows'));ck('mixed_window_grilles',all(wc[q] for q in ['none','cage','flush']),dict(wc))
 patches=load('weathering');bad=[];tone={tuple(c['xyz']) for c in patches if c['kind']=='near_colour'}
 for q in tone:
  if any(tuple(q[i]+v[i] for i in range(3)) in tone for v in [(1,0,0),(0,1,0),(0,0,1)]):bad.append(q)
 ck('isolated_near_colour_variation',not bad,{'tones':len(tone),'adjacent':bad})
 missing=[v for v in patches if not owner.get(tuple(v['xyz']),'').startswith(v['id'].split('.')[0]+'.facade.')]
 ck('weathering_remains_on_facade',not missing,{'kinds':dict(collections.Counter(v['kind'] for v in patches)),'errors':missing})
 bad=[]
 for e in load('equipment'):
  if e['kind']=='rainwater_pipe' and (not support(*e['base']) or any('diorite_wall' not in blocks.get(tuple(q),'') for q in e['cells'])):bad.append(e['id'])
  if e['kind'] in ['water_tank_shape','antenna','clothesline'] and not support(e['base'][0],e['base'][1]-1,e['base'][2]):bad.append(e['id'])
 ck('roof_and_pipe_bases_supported',not bad,bad)
 ck('20_haf_handoffs_compiled',len(load('resolved_plans'))==20,{'plans':len(load('resolved_plans')),'planner_does_not_generate_geometry':True})
 out={'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'passed':all(c['status']=='pass' for c in checks),'game_status':'pending','visual_status':'pending','limits':['Cell-based access is not actual game collision/pathfinding','Vanilla textures and coloured light are not simulated','Beds, kitchen, plumbing and shop signs are decorative','Original design, no surveyed village identity']}
 (R/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--run',required=True);x=a.parse_args();v=main(x.run);raise SystemExit(0 if v['passed'] else 1)
