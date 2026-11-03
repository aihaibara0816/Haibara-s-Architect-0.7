"""Additional whole-floor access and 2-wide stair sampling against final NBT."""
from pathlib import Path
import sys,json,argparse,collections,gzip,hashlib
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from vendor.inspect_build import load_build,Limits
from detail_lab import states
def main(run):
 R=C/'runs'/run;read=lambda f:json.loads((R/f).read_text());b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));p=read('params_used.json');checks=[]
 def clear(x,y,z):return (x,y,z) not in b.blocks and (x,y+1,z) not in b.blocks
 def support(x,y,z):return (x,y,z) in b.blocks and (states.support_cube(b.blocks[x,y,z]) or states.family(b.blocks[x,y,z])=='stairs')
 stairs=[]
 for r in read('stairs.json'):
  t=next(t for t in p['towers'] if r['id'].startswith(t['id']+'.'));cx=t['x']+(1 if t['type']=='A' else 14);cz=t['z']+(0 if t['type']=='A' else 1)
  for x,y,z in r['trace']:
   offsets=[0,1] if x in [cx+1,cx+6] and z>=cz+3 else [0]
   for off in offsets:
    if not support(x+off,y-1,z) or not clear(x+off,y,z):stairs.append([r['id'],x+off,y,z])
 checks.append({'id':'two_wide_stair_sampling','status':'pass' if not stairs else 'fail','errors':stairs})
 unreachable=[];units=read('units.json')
 for t in p['towers']:
  cx=t['x']+(1 if t['type']=='A' else 14);cz=t['z']+(0 if t['type']=='A' else 1)
  for f in range(t['storeys']):
   y=3+f*5;todo=collections.deque([(cx+6,cz+7)]);seen=set()
   while todo:
    x,z=todo.popleft()
    if (x,z) in seen or not (t['x']<x<t['x']+t['w']-1 and t['z']<z<t['z']+t['d']-1) or not clear(x,y,z) or not support(x,y-1,z):continue
    seen.add((x,z));todo.extend([(x-1,z),(x+1,z),(x,z-1),(x,z+1)])
   for u in units:
    if u['tower']==t['id'] and u['floor']==f+1 and (u['entry'][0],u['entry'][2]) not in seen:unreachable.append(u['id'])
 checks.append({'id':'all_75_landings_reach_120_homes','status':'pass' if not unreachable else 'fail','unreachable':unreachable})
 own=json.loads(gzip.decompress((R/'component_ownership.json.gz').read_bytes()));ids=own['owner_names'];counts=collections.Counter(ids[r[3]] for r in own['xyz_owner']);bad=[]
 for m in read('module_consumption.json'):
  count=sum(n for k,n in counts.items() if k==m['component_id'] or k.startswith(m['component_id']+'.'))
  if count!=m['placed_cells']:bad.append([m['component_id'],m['placed_cells'],count])
 checks.append({'id':'1110_module_counts_survive_final_assembly','status':'pass' if not bad else 'fail','mismatches':bad})
 out={'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'passed':all(v['status']=='pass' for v in checks),'game_status':'pending'}
 (R/'access_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False));return out['passed']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();raise SystemExit(0 if main(a.run) else 1)
