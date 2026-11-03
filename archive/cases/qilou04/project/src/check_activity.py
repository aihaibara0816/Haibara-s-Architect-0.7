"""Inspect source NBT storefront access, activity fixtures and preservation of R18 shells."""
from pathlib import Path
import json,sys,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT/'pydeps')]
import qilou_states, rong_site as VS
from vendor.voxel_core import parse_state
from q04_activity import NEW_GROUND
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];s=json.loads((R/'spec.json').read_text());d=json.loads((R/'urban_records.json').read_text());lim=Limits(cells=12_000_000,nodes=25_000_000)
current=load_build(R/'Qilou04.nbt',lim).blocks;old=load_build(ROOT/'runs/R18/Qilou04.nbt',lim).blocks
before=json.loads((ROOT/'runs/R18/spec.json').read_text());byid={b['id']:b for b in before['buildings']}
errors=[];shellcount=0;allowed=0;joins=0;signs=0
for b in s['buildings']:
 prev=byid[b['id']]
 if b['family']=='village':
  for key in ['x','z','w','d','floors','shape','rotation','palette']:
   if b['lot'][key]!=prev['lot'][key]:errors.append(['unrequested_massing_change',b['id'],key])
  t=b['lot'];rect=[t['x']-2,t['z']-2,t['x']+t['w']+2,t['z']+t['d']+2]
 else:
  if b['facade_revision']!=prev['facade_revision']:errors.append(['qilou_facade_change',b['id']])
  bb=b['geometry_bounds'];rect=[bb[0][0],bb[2][0],bb[0][1],bb[2][1]]
 signcells=set()
 if b['id']in NEW_GROUND:
  t=b['lot'];W,D=(t['w'],t['d'])if t['rotation']%2==0 else(t['d'],t['w']);end=W-t['cut']if t['shape']=='front_cut'else W
  for yy in[8,9]:
   for zz in[-3,-2]:
    xx,zz2=VS.local(t,end-1,zz);signcells.add((xx,yy,zz2))
  xx,zz=VS.local(t,end-1,-1);signcells.add((xx,10,zz))
 # Compare the actual authored module blocks, excluding trees and street fixtures.
 def worldmap(folder,rec):
  out={}
  for (x,y,z),st in load_build(folder/(rec['id']+'.nbt'),lim).blocks.items():
   if y<8:continue
   W,D=rec['w'],rec['d']
   for _ in range(rec['turn']):x,z=D-1-z,x;W,D=D,W
   out[x+rec['origin'][0],y+rec['origin'][1],z+rec['origin'][2]]=st
  return out
 oa=worldmap(ROOT/'runs/R18',prev);na=worldmap(R,b)
 for q in set(oa)|set(na):
  a=oa.get(q,'minecraft:air');v=na.get(q,'minecraft:air');shellcount+=1
  if a==v:continue
  if {a,v}<={'minecraft:white_concrete','minecraft:sea_lantern','minecraft:glowstone'}:allowed+=1;continue
  if q in signcells and a=='minecraft:air':signs+=1;continue
  an,ap=parse_state(a);vn,vp=parse_state(v)
  if an==vn and an=='minecraft:iron_bars' and {k:w for k,w in ap.items()if k not in ['north','south','east','west']}=={k:w for k,w in vp.items()if k not in ['north','south','east','west']}:joins+=1;continue
  errors.append(['upper_geometry',b['id'],q,a,v])
for f in d['shopfronts']:
 for name in ['entry','inside','outside']:
  x,y,z=f[name]
  for yy in[y,y+1]:
   if current.get((x,yy,z),'minecraft:air')!='minecraft:air':errors.append(['shop_opening',f['unit_id'],name,[x,yy,z]])
 if not f['residential_entry_separate']:errors.append(['mixed_entry',f['unit_id']])
 assert f['frontage_width']>=4
for u in d['evening_activity']:
 if u['activity']=='asleep'and u['fixtures']:errors.append(['dark_home_has_fixture',u['unit_id']])
 for q in u['fixtures']:
  if current.get(tuple(q))not in['minecraft:sea_lantern','minecraft:glowstone']:errors.append(['missing_activity_light',u['unit_id'],q])
for light in s['street_lighting']['fixtures']:
 x,y,z=light['light'];cap=current.get((x,y+1,z),'')
 if 'slab'not in cap or 'type=bottom'not in cap:errors.append(['floating_lamp_head',[x,y,z],cap])
 bx,_,bz=light['base']
 if current.get((bx,light['height'],bz))!='minecraft:smooth_stone':errors.append(['missing_arm_joint',light['base']])
counts=collections.Counter(u['activity']for u in d['evening_activity']);assert len(counts)>=5
assert s['street_lighting']['counts'].get('road',0)>=20 and s['street_lighting']['counts'].get('lane',0)>=10
assert len(d['shopfronts'])>=20
result={'pass':not errors,'source_nbt_sha256':s['source_nbt_sha256'],'street_shopfronts':len(d['shopfronts']),'commercial_ground_floors':sum(b['family']=='village'and b['program']!='home'for b in s['buildings']),'activity_states':dict(counts),'street_lights':s['street_lighting']['counts'],'upper_cells_compared':shellcount,'intentional_upper_light_changes':allowed,'new_shop_blade_cells':signs,'adjacent_bar_connection_changes':joins,'errors':errors[:100],'error_count':len(errors),'scope':'Actual NBT openings, light blocks and upper-building geometry compared to approved R18; general navigation independently checked by audit_district. Visual quality still needs real-client night inspection.'}
(R/'activity_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False));raise SystemExit(bool(errors))
