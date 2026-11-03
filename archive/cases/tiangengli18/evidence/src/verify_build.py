from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from scipy.ndimage import label
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
run=sys.argv[1] if len(sys.argv)>1 else 'P3_B1';R=C/'runs'/run
b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));B=b.blocks
p=json.loads((R/'params_used.json').read_text());entries=json.loads((R/'entries.json').read_text());lights=json.loads((R/'lighting.json').read_text())
road=np.load(R/'roadmask.npy');components,n=label(road);fail=[]
roadbad=[]
for z,x in zip(*np.where(road)):
 for y in [4,5]:
  q=(int(x),y,int(z));st=B.get(q)
  if st and not(y==4 and states.family(st)=='stairs'):roadbad.append([*q,st])
for e in entries:
 x,z=e['x'],e['z'];y=e['floor']
 for yy in [y,y+1]:
  if (x,yy,z) in B:fail.append(['entry_blocked',e['id'],x,yy,z,B[x,yy,z]])
 if (x,y-1,z) not in B:fail.append(['entry_support_missing',e['id']])
 if not road[max(0,z-2):z+3,max(0,x-2):x+3].any():fail.append(['door_road_gap',e['id']])
lampbad=[];flushbad=[]
for floor in lights:
 if not floor['lamps']:lampbad.append([floor['house'],floor['floor'],'no_lamps'])
 for li in floor['lamps']:
  q=tuple(li['xyz'])
  if li['material'] not in B.get(q,''):lampbad.append([floor['house'],floor['floor'],li])
  if (q[0],q[1]+1,q[2]) not in B:flushbad.append([floor['house'],floor['floor'],q])
crops=[(q,s) for q,s in B.items() if states.family(s)=='crop'];soilbad=[];dry=[]
water={q for q,s in B.items() if s.startswith('minecraft:water')};leaks=[]
for (x,y,z),st in crops:
 if 'farmland' not in B.get((x,y-1,z),''):soilbad.append([x,y,z])
 if not any((x+dx,y-1,z+dz) in water or (x+dx,y,z+dz) in water for dx in range(-4,5) for dz in range(-4,5)):dry.append([x,y,z])
for x,y,z in water:
 if (x,y-1,z) not in B:leaks.append([x,y,z,'bottom'])
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  st=B.get((x+dx,y,z+dz),'minecraft:air')
  if states.family(st) in ['air','crop','flower']:leaks.append([x,y,z,'side'])
report=dict(run=run,source_nbt_sha256=hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),size=b.size,non_air=len(B),data_version=3955,house_count=len(p['buildings']),house_types=dict(collections.Counter(h['kind'] for h in p['buildings'])),field_subplots=len(p['fields']),greenhouse_count=len(p['greenhouses']),road_components=n,road_blockers=roadbad,entry_failures=fail,occupied_floors=len(lights),missing_lamps=lampbad,lamps_missing_upper_floor=flushbad,crop_count=len(crops),unsupported_crops=soilbad,unhydrated_crop_count=len(dry),uncontained_water=leaks,light_blocks=dict(collections.Counter(s.split('[')[0] for s in B.values() if any(m in s for m in ['glowstone','sea_lantern','end_rod']))),game_client='pending',game_server='not run this version',collision='pending; road and entrance geometry only')
(R/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v if not isinstance(v,list) or len(v)<5 else {'count':len(v),'sample':v[:5]} for k,v in report.items()},ensure_ascii=False,indent=2))
assert n==1 and not roadbad and not fail and not lampbad and not flushbad and not soilbad and not leaks and not dry
