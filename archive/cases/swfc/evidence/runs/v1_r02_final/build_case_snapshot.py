"""SWFC explicit image/primary-source adapter. HAF 0.3, no general image reconstruction.
A square prism intersects two circular-arc cut planes; an estimated trapezoidal
opening is subtracted. All stages obey the same protected void predicate.
"""
from pathlib import Path
import argparse, math, json, sys, hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder, M
from hafusion.case_io import save_run,dump
CASE=Path(__file__).resolve().parent
class SWFC:
 def __init__(self,p):
  self.p=p;self.s=p['scale'];self.o=p['origin'];self.b=Builder(p['size'],p['lighting']['seed']);self.H=p['form']['height_m'];self.D=p['form']['square_base_side_m']/math.sqrt(2)
  sag=self.D-p['form']['top_half_thickness_m'];self.radius=(self.H*self.H+sag*sag)/(2*sag)
  self.volume=set();self.audit=[]
 def world(self,x,y,z):return ((x+.5-self.o[0])/self.s,(y+.5-self.o[1])/self.s,(z+.5-self.o[2])/self.s)
 def half_thickness(self,h):return self.D-(self.radius-math.sqrt(max(0,self.radius*self.radius-h*h)))
 def opening(self,x,h,z):
  a=self.p['aperture']
  if not a['lower_m']<=h<a['upper_m']:return False
  t=(h-a['lower_m'])/(a['upper_m']-a['lower_m']);w=a['width_lower_m']*(1-t)+a['width_upper_m']*t
  return abs(x)<w/2
 def inside(self,x,h,z):return 0<=h<self.H and abs(x)+abs(z)<=self.D and abs(z)<=self.half_thickness(h) and not self.opening(x,h,z)
 def q(self,x,h,z):return (round(self.o[0]+x*self.s-.5),round(self.o[1]+h*self.s-.5),round(self.o[2]+z*self.s-.5))
 def put(self,q,mat,owner):
  if self.opening(*self.world(*q)):return
  self.b.put(*q,mat,owner)
 def site(self):
  b=self.b
  def box(lo,hi,mat,owner):b.box(lo,tuple(v+1 for v in hi),mat,owner)
  box((4,0,4),(68,2,68),'stone_bricks','site.foundation');box((4,3,4),(68,3,68),'smooth_stone','site.paving')
  # Short, low podium study: it does not claim a measured plan.
  box((12,4,15),(25,8,52),'gray_concrete','podium.backing')
  for y in range(4,9):
   for z in range(16,52):
    if y in (4,8):b.put(11,y,z,'polished_andesite','podium.band')
    else:b.put(11,y,z,'gray_stained_glass','podium.glass')
  for z in range(13,55):
   for x in range(10,28):b.put(x,9,z,'smooth_stone_slab','podium.roof')
  # Entry interface with supported thin rain canopy; synthetic dimensions.
  for x in range(28,46):
   for z in range(54,59):b.put(x,7,z,'gray_stained_glass','entry.canopy')
  for x in (28,45):
   for z in (54,58):
    for y in range(4,8):b.put(x,y,z,'iron_bars','entry.post')
  for z in range(54,68):
   for x in range(31,43):b.put(x,3,z,'polished_andesite','site.entry_path')
  for x in (8,64):
   for z in (8,22,44,64):
    box((x-2,4,z-2),(x+2,4,z+2),'stone_bricks','site.planter');box((x-1,5,z-1),(x+1,5,z+1),'azalea_leaves','site.plants')
 def construct(self,mode):
  b=self.b;p=self.p;self.site()
  for y in range(3,233):
   for x in range(16,57):
    for z in range(16,57):
     if self.inside(*self.world(x,y,z)):self.volume.add((x,y,z))
  face_neighbors=[(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)]
  shell={q for q in self.volume if any(tuple(q[i]+d[i] for i in range(3)) not in self.volume for d in face_neighbors)}
  for q in sorted(self.volume):
   x,y,z=q;xx,h,zz=self.world(*q);t=self.half_thickness(h)
   arc=(t-abs(zz))*self.s<1.2;at_opening=(p['aperture']['lower_m']-3<=h<=p['aperture']['upper_m']+3)
   if q in shell:
    edge=(self.D-abs(xx)-abs(zz))*self.s<.75 and arc
    if mode=='massing':mat='light_gray_concrete';owner='envelope.massing'
    elif mode=='glass_control':mat='cyan_stained_glass';owner='envelope.control_glass'
    else:
     if y%p['facade']['band_period_blocks']==0:mat='gray_concrete';owner='envelope.spandrel'
     else:
      # Coherent strips, not random per-block noise or copied sunset colours.
      k=(x//3 if arc else (x+z)//3)%7;mat='cyan_stained_glass' if k<4 else ('blue_stained_glass' if k<6 else 'black_stained_glass');owner='envelope.glass'
     if edge:mat='light_gray_concrete';owner='envelope.edge'
     if h>=p['bridge']['roof_m']:mat='gray_concrete';owner='crown.parapet'
    self.put(q,mat,owner)
   # Local window-back layer and sparse synthetic floors, below the protected portal.
   elif mode!='massing' and h<p['aperture']['lower_m']:
    if y%p['interior']['floor_spacing_blocks']==0:self.put(q,'gray_concrete','interior.floor')
    elif abs(xx)<8 and abs(zz)<min(8,t-3):self.put(q,'light_gray_concrete','interior.core')
    elif mode=='layered':
     depth=min(t-abs(zz),(self.D-abs(xx)-abs(zz))/math.sqrt(2))*self.s
     if p['facade']['backing_depth_blocks']-.3<depth<p['facade']['backing_depth_blocks']+.7:
      self.put(q,'gray_concrete','interior.backing')
      room=f'{x//3}:{y//5}:{z//3}';v=int(hashlib.sha256((str(p['lighting']['seed'])+room).encode()).hexdigest()[:8],16)/2**32
      if p['lighting']['enabled'] and y%5==2 and v<p['lighting']['window_probability']:
       self.put(q,'glowstone','lighting.windows');b.rooms.append({'id':room,'synthetic':True,'anchor':q,'light':'glowstone'})
   # Skywalk has a real separate bottom, walk deck and roof, no wall across void.
   if h>=p['aperture']['upper_m'] and abs(xx)<p['aperture']['width_upper_m']/2:
    by=self.q(0,p['bridge']['floor_m'],0)[1];cy=self.q(0,p['bridge']['ceiling_m'],0)[1]
    if y==by:self.put(q,'gray_stained_glass' if abs(xx)<24 else 'smooth_stone','bridge.floor')
    elif y==by-1:self.put(q,'polished_andesite' if x%3==0 else 'gray_stained_glass','bridge.soffit')
    elif y==cy:self.put(q,'gray_concrete','bridge.ceiling')
    if mode=='layered' and by<y<cy and arc:self.put(q,'gray_stained_glass','bridge.glass')
  if mode=='layered':
   # Exterior iron-bar seams on broad cut surfaces; portal remains empty.
   for x,y,z in sorted(shell):
    xx,h,zz=self.world(x,y,z);t=self.half_thickness(h)
    if h<25 or h>p['bridge']['roof_m'] or (t-abs(zz))*self.s>1.2:continue
    q=(x,y,z+(1 if zz>=0 else -1))
    if x%p['facade']['mullion_period_blocks']==0 and y%2==1 and q not in self.volume:self.put(q,'iron_bars','facade.mullion')
   # Fixed outline on one evidenced representative broad face; no mirror assumption.
   if p['lighting']['enabled']:
    for x,y,z in sorted(shell):
     xx,h,zz=self.world(x,y,z);t=self.half_thickness(h)
     if zz<=0 or (t-zz)*self.s>1.2:continue
     if (295<h<440 and y%8==1 and abs(xx)<28) or h>489:
      q=(x,y,z+1)
      if q not in self.volume:self.put(q,M('end_rod',facing='east'),'lighting.crown_slots')
  # Rooftop deck closes the narrow blade, and all stage additions obey the same void.
  for q in self.volume:
   if q[1]==232:self.put(q,'gray_concrete','crown.cap')
  for x in range(33,40):
   for y in range(4,7):
    for z in range(53,56):b.put(x,y,z,'minecraft:air','entry.opening')
  for q in list(b.s.blocks):
   if self.opening(*self.world(*q)):b.put(*q,'minecraft:air','aperture.protected_void')
  b.windows.append({'id':'envelope','fidelity':'coarse layer bands; not counted as 101 storeys','mode':mode})
  return b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--mode',choices=['massing','glass_control','layered'],default='layered');a=ap.parse_args()
 p=json.loads((CASE/'parameters.json').read_text());p['facade']['mode']=a.mode;t=SWFC(p);b=t.construct(a.mode)
 out=save_run(CASE,a.run,p,b,Path(__file__),{'route':'photos_plus_primary_sources','adapter_status':'case_specific','north_verified':False,'world_origin_y_max':320-p['size'][1],'sparse_air':True,'analytic_arc_radius_m_estimate':t.radius})
 dump(out/'form_sections.json',[{'height_m':h,'half_thickness_m':t.half_thickness(h),'base_half_diagonal_m':t.D} for h in (0,100,200,300,400,442,474,492)])
if __name__=='__main__':main()
