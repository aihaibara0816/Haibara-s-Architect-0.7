from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];b=load_build(R/'Machiya08.nbt',Limits(cells=2_000_000,nodes=6_000_000));sp=json.loads((R/'spec.json').read_text());cache={}
def boxes(st):
 if st not in cache:cache[st]=states.boxes(st)
 return cache[st]
def hit(x,y,z):
 lo=[x-.299,y+.001,z-.299];hi=[x+.299,y+1.799,z+.299];hits=[]
 for xx in range(math.floor(lo[0]),math.ceil(hi[0])):
  for zz in range(math.floor(lo[2]),math.ceil(hi[2])):
   for yy in range(math.floor(lo[1]),math.ceil(hi[1])):
    st=b.blocks.get((xx,yy,zz),'minecraft:air')
    for bb in boxes(st):
     v=[bb[i]+[xx,yy,zz][i%3] for i in range(6)]
     if all(lo[i]<v[i+3] and hi[i]>v[i] for i in range(3)):hits.append([xx,yy,zz,st])
 return hits
def support(x,z,low,high):
 top=low
 for xx in range(math.floor(x-.299),math.ceil(x+.299)):
  for zz in range(math.floor(z-.299),math.ceil(z+.299)):
   for yy in range(low-1,high):
    for bb in boxes(b.blocks.get((xx,yy,zz),'minecraft:air')):
     if xx+bb[0]<x+.299 and xx+bb[3]>x-.299 and zz+bb[2]<z+.299 and zz+bb[5]>z-.299:top=max(top,yy+bb[4])
 return top
results=[]
for rec in sp['stairs']:
 f=rec['floor'];path=[]
 for i in range(33):
  z=rec['start_z']-i*.125;path.append([rec['lower_x'],support(rec['lower_x'],z,f+1,f+4),z])
 for i in range(25):path.append([rec['lower_x']+i*.125,f+4,rec['turn_z']])
 for i in range(33):
  z=rec['turn_z']+i*.125;path.append([rec['upper_x'],support(rec['upper_x'],z,f+4,f+6),z])
 bad=[{'at':p,'hits':hit(*p)} for p in path if hit(*p)];step=max(abs(path[i+1][1]-path[i][1]) for i in range(len(path)-1));results.append({'id':rec['id'],'samples':len(path),'max_step':step,'collisions':bad,'end':path[-1]})
out={'results':results,'pass_offline':all(not r['collisions'] and r['max_step']<=.5 for r in results),'method':'0.125-block support-top sampling with 0.598 x 1.798 body. Approximate preview shapes, not game physics.','game':'pending'}
(R/'stair_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False)[:6000]);sys.exit(not out['pass_offline'])
