"""Check key interior connections on the final independent NBT readback."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'support')]
from vendor.inspect_build import load_build,Limits
R=P/'runs'/sys.argv[1];b=load_build(R/'ModernFactory01.nbt',Limits(cells=12_000_000,nodes=50_000_000,decoded_bytes=256*1024*1024));sp=json.loads((R/'spec.json').read_text());ac=json.loads((R/'access.json').read_text());rooms=json.loads((R/'rooms.json').read_text());errors=[]
def clear(x,y,z):return all((x,y+dy,z) not in b.blocks for dy in [0,1]) and (x,y-1,z) in b.blocks
for fy in [4,12,20,28,36]:
 for z in range(273,278):
  if not clear(51,fy,z):errors.append(['office_wing',51,fy,z])
for x0 in [268,328]:
 for fy in [20,28,36,44]:
  for x in range(x0+10,x0+14):
   if (x,fy,253) not in b.blocks or 'glass_pane' not in b.blocks.get((x,fy+1,253),''):errors.append(['upper_dorm_facade',x,fy,253])
for pos in [(88,4,274),(188,4,306),(280,4,312),(340,4,312)]:
 if not clear(*pos):errors.append(['entry',*pos])
for door in ac['doors']:
 x,y,z=door['pos']
 for xx in [x-1,x+1]:
  if not clear(xx,y,z):errors.append(['room_door_side',xx,y,z])
q={'source_nbt_sha256':sp['source_nbt_sha256'],'office_wing_portals':5,'upper_dorm_closed_facades':8,'main_entries':4,'room_door_sides':len(ac['doors'])*2,'errors':errors,'scope':'discrete geometry and support, not game collision or full route simulation'}
(R/'access_audit.json').write_text(json.dumps(q,indent=2));print(json.dumps(q));assert not errors
q={'status':'as_built_offline_verified','source_nbt_sha256':sp['source_nbt_sha256'],'site':sp,'rooms':rooms,'access':ac,'original_design':True,'game_status':'not_run','planned_interior_level':'L2, not game-certified','baseline':'M03 visual feedback requires revision; earlier file version retains original technical evidence'}
(R/'as_built_handoff.json').write_text(json.dumps(q,ensure_ascii=False,indent=2))
