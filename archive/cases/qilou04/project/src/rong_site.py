"""Six-sided district, anchored terraces and graded public streets."""
import math,collections,heapq
from detail_lab import states
M=states.make
DIRS=[(1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')]
def local(t,x,z):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);r=t['rotation']
 if r==0:a,c=x,z
 elif r==1:a,c=D-1-z,x
 elif r==2:a,c=W-1-x,D-1-z
 else:a,c=z,W-1-x
 return t['x']+a,t['z']+c

def mask(t):
 W,D=(t['w'],t['d']) if t['rotation']%2==0 else (t['d'],t['w']);s=t['shape'];k=t['cut']
 cells={(x,z) for x in range(W) for z in range(D) if (s!='front_cut' or x-z<=W-1-k) and (s!='rear_cut' or x+z<=W+D-2-k) and (s!='notch' or x<W-k or z<D-k)}
 for q in t.get('edge_recesses',[]):
  dep=q['depth']
  if q['face']=='right':cells={v for v in cells if not(v[0]>=W-dep and q['start']<=v[1]<q['end'])}
  if q['face']=='rear_right':cells={v for v in cells if not(v[0]>=W-dep and v[1]>=D-dep)}
 return cells

def inside(x,z,poly):
 yes=False
 for (a,c),(A,C) in zip(poly,poly[1:]+poly[:1]):
  if (c>z)!=(C>z) and x<(A-a)*(z-c)/(C-c)+a:yes=not yes
 return yes


def setup(b,p):
 w,h,d=p['size_xyz'];hm={(x,z):3 for x in range(w) for z in range(d)};foot=set()
 for t in p['buildings']:
  cells={local(t,x,z) for x,z in mask(t)}
  assert not foot&cells,('overlap',t['id']);foot|=cells
 b.site_surface=hm
 return set(),{},foot,hm
