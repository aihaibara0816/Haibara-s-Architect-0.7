"""V3 feedback regression checks on independently read-back NBT."""
from pathlib import Path
import sys,json,hashlib,collections,gzip
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(CASE/'src')]
from vendor.inspect_build import load_build,Limits
from build_v3 import CustomsV3
from detail_lab.states import validate
run=CASE/'runs'/sys.argv[1];p=json.loads((run/'params_used.json').read_text());g=p['frame']['ground_y']
b=load_build(run/'building.nbt',Limits(cells=40000000,nodes=16000000));rows=[]
def check(n,v,e):rows.append({'test':n,'pass':bool(v),'evidence':e})
def air(q):return q not in b.blocks
baseline=json.loads((CASE/'research/v3/baseline_hashes.json').read_text())
changed=[s for s,h in baseline.items() if hashlib.sha256((ROOT/s).read_bytes()).hexdigest()!=h]
check('V1/V2 source, runs, cameras and shared core unchanged',not changed,{'files_compared':len(baseline),'changed':changed})
check('comparison frame and study height preserved',b.size==(126,148,116) and max(q[1] for q in b.blocks)==140,'126×148×116; ground y4; nominal height 137')
# Wide continuous front floor, centered continuous rear roof, and genuinely empty side setbacks.
check('front horizontal bar present',all(not air((x,g+20,80)) for x in range(13,114)),'101-block cross section from actual NBT')
check('rear stem centered and continuous',all(not air((x,g+21,40)) for x in range(25,102)),'77-block roof cross section, x25..101')
for side,xs in [('left',range(15,23)),('right',range(104,112))]:
 check(side+' rear setback is clear',all(air((x,y,z)) for x in xs for y in range(g+3,g+19) for z in range(20,69)),'entire side setback sampled, not only one empty point')
check('old V2 one-sided green bump removed',all(air((108,y,22)) for y in range(g+2,g+25)),'previous V2 rear wing interior location')
check('center tower rear overextension removed',all(air((63,y,z)) for y in range(g+33,g+94) for z in range(44,51)),'8-block setback; excludes podium pavilion height')
check('front door clear',all(air((x,y,84)) for x in range(61,66) for y in range(g+3,g+7)),'5×4 open passage')
check('rear axial door clear',all(air((x,y,16)) for x in range(61,66) for y in range(g+3,g+7)),'5×4 open passage at rear of stem')
check('rear stair landing continuous',all(not air((63,g+2,z)) for z in range(13,23)),'top stair to interior landing, no gap')
check('rear arch piers are closed',all(not air((x,y,16)) for x in (58,68) for y in range(g+4,g+17)),'walls between three arched bays remain')
check('pavilions supported by roof',all(not air((x,g+21,z)) for x0,z0,x1,z1 in p['podium']['glass_pavilions'] for x in range(x0,x1) for z in range(z0,z1)),'all roof enclosure footprint cells have support below')
check('colonnade void retained',all(air((20,y,z)) for y in range(g+6,g+12) for z in range(86,91)),'front colonnade is open behind the columns')
windows=json.loads((run/'windows.json').read_text());rooms=json.loads((run/'interiors.json').read_text())
bad=[]
for w in windows:
 x,y,z=w['anchor'];dx,dz=w['normal_xz']
 if 'glass' not in b.blocks.get((x-dx,y,z-dz),''):bad.append(w['id'])
check('all registered window anchors contain recessed glass',not bad,{'exceptions':bad,'windows':len(windows)})
counts=collections.Counter(r['actual_lamp'] or 'off' for r in rooms)
check('dark warm and cool rooms retained',all(counts[k]>0 for k in ('off','glowstone','sea_lantern')),dict(counts))
check('room lights match saved coordinates and materials',all(b.blocks.get(tuple(r['lamp_position']),'').split('[')[0]=='minecraft:'+r['actual_lamp'] for r in rooms if r['actual_lamp']),'every recorded room light')
for s in set(b.blocks.values()):validate(s)
check('all block states valid in existing HAF validator',True,len(set(b.blocks.values())))
model=CustomsV3(p).build();model.finish()
check('deterministic source regeneration matches exported NBT',model.s.blocks==b.blocks,{'nonair':len(b.blocks)})
for level in (g+10,g+50,g+109):
 occupied={(int(x),int(z)) for z,x in zip(*model.mass[level].nonzero())}
 check('mass mirror symmetry y='+str(level),{(126-x,z) for x,z in occupied}==occupied,'mass geometry only; no requirement that lights or vegetation mirror')
# Actual block changes in tower-front/clock are kept narrow and recorded.
old=load_build(CASE/'runs/V2_r06/building.nbt',Limits(cells=40000000,nodes=16000000))
oldowners=json.loads(gzip.decompress((CASE/'runs/V2_r06/component_ownership.json.gz').read_bytes()))
clock={tuple(row[:3]):old.blocks[tuple(row[:3])] for row in oldowners['xyz_owner'] if oldowners['owner_names'][row[3]].startswith(('clock.','lighting.clock.','lighting.aviation.'))}
check('clock and spire preserved exactly',all(b.blocks.get(q)==s for q,s in clock.items()),{'checked_blocks':len(clock)})
delta=collections.Counter('removed' if q not in b.blocks else 'added' if q not in old.blocks else 'state_changed' for q in set(b.blocks)|set(old.blocks) if old.blocks.get(q)!=b.blocks.get(q))
report={'run':run.name,'checks':rows,'passed':sum(r['pass'] for r in rows),'total':len(rows),'all_passed':all(r['pass'] for r in rows),'delta_from_V2':dict(delta),'visual_acceptance':'pending user review; technical tests cannot certify architectural fidelity','minecraft_import':'not run','geographic_bearing':'unverified'}
(run/'validation_v3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['all_passed'] else 1)
