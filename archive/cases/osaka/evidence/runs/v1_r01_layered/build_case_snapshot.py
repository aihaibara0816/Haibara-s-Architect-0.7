"""Explicit Osaka case adapter. Geometry from manually interpreted image evidence.
No calibrated camera, photogrammetry or general image-to-building inference.
Coordinates are working axes; +Z is the researched river-facing side.
"""
from pathlib import Path
import argparse,json,sys,hashlib,math
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from hafusion.classical import Builder,M
from hafusion.case_io import save_run,dump
C=Path(__file__).parent
class Osaka:
 def __init__(self,p,mode):self.p=p;self.mode=mode;self.b=Builder(p['size'],p['lighting']['seed'])
 def box(self,a,b,mat,owner):self.b.box(a,tuple(v+1 for v in b),mat,owner)
 def put(self,x,y,z,mat,owner):self.b.put(x,y,z,mat,owner)
 def shell(self,lo,hi,mat,owner):
  x0,y0,z0=lo;x1,y1,z1=hi
  self.box((x0,y0,z0),(x1,y1,z0),mat,owner);self.box((x0,y0,z1),(x1,y1,z1),mat,owner)
  self.box((x0,y0,z0),(x0,y1,z1),mat,owner);self.box((x1,y0,z0),(x1,y1,z1),mat,owner)
  self.box((x0,y0,z0),(x1,y0,z1),mat,owner);self.box((x0,y1,z0),(x1,y1,z1),mat,owner)
 def site(self):
  self.box((4,0,10),(91,2,78),'stone_bricks','site.foundation')
  self.box((4,3,10),(91,3,69),'smooth_stone','site.ground')
  self.box((4,1,70),(91,1,83),'cyan_stained_glass','site.river_symbol')
  self.box((4,0,70),(91,0,83),'gray_concrete','site.river_bed')
  self.box((8,4,64),(86,4,68),'dark_oak_planks','site.deck')
  for x in range(8,87):self.put(x,5,68,'iron_bars','site.railing')
  for x in [17,35,52,75]:
   self.box((x-2,5,65),(x+2,5,67),'smooth_quartz','site.planter')
   self.put(x,6,66,'oak_log','site.tree');self.put(x,7,66,'oak_log','site.tree')
   self.box((x-1,8,65),(x+1,9,67),'azalea_leaves','site.tree')
  # Access from the lower approach to the raised river deck.
  for x in range(81,86):self.put(x,4,63,M('dark_oak_stairs',facing='south'),'site.step')
 def podium(self):
  self.shell((12,4,24),(82,26,63),'polished_andesite','podium.wall')
  for y in [4,10,16,22,26]:self.box((13,y,25),(81,y,62),'gray_concrete','podium.floor')
  # Horizontal ribbon windows, dark reveals, and a recessed ground interface.
  for z,inside in [(24,1),(63,-1)]:
   for y in range(5,26):
    for x in range(13,82):
     ribbon=(y in [12,18,24] and 25<=x<=77) or (5<=y<=9 and x%8>1)
     if ribbon:
      self.put(x,y,z,'gray_stained_glass','podium.ribbon')
      self.put(x,y,z+3*inside,'gray_concrete','podium.backing')
     if y in [11,17,23]:self.put(x,y,z,'gray_concrete','podium.band')
  # River-facing projecting public box, independent underside and glazing bay.
  self.shell((20,27,49),(80,38,62),'white_concrete','public.white_box')
  for y in [28,31,34,37]:
   for x in range(21,80):
    if ((x//13)+(y//3))%3==0:self.put(x,y,63,M('smooth_quartz_slab',type='top'),'public.thin_bands')
  self.box((22,26,50),(80,26,62),'gray_concrete','public.soffit')
  self.box((27,30,63),(48,33,65),'gray_stained_glass','public.projecting_window')
  self.box((27,29,63),(48,29,65),'gray_concrete','public.window_soffit')
  for x in range(27,49,3):self.box((x,30,66),(x,33,66),'iron_bars','public.window_mullion')
  self.box((48,35,62),(78,35,62),'gray_stained_glass','public.upper_strip')
  # Ground floor remains inset beneath a supported cantilevered TV corner.
  for y in range(10,28):
   for z in range(47,63):
    xx=83+(27-y)//6
    self.put(xx,y,z,'gray_stained_glass','tv.slope_glass')
    if z%4==0:self.put(xx+1,y,z,'iron_bars','tv.fine_mullion')
    if (z+y//5)%11==0:self.put(xx+1,y,z,'white_concrete','tv.offset_frames')
  self.box((81,9,47),(86,9,63),'gray_concrete','tv.soffit')
  for z in [47,62]:self.box((85,4,z),(86,8,z),'polished_andesite','tv.pier')
  self.box((81,4,48),(81,8,61),'black_stained_glass','tv.inset_lobby')
  if self.mode=='layered':
   for z in [50,57]:self.put(84,9,z,'sea_lantern','lighting.soffit')
  # River left terraces with railings supported by a solid side return.
  self.box((12,4,54),(15,26,59),'gray_concrete','podium.terrace_support')
  for y in [10,16,22]:
   self.box((10,y,56),(21,y,64),'gray_concrete','podium.terrace')
   self.box((10,y+1,64),(21,y+1,64),'iron_bars','podium.terrace_rail')
  # Hotel entrance on the opposite side, with explicit two-block clear opening.
  self.box((56,4,24),(60,7,27),'minecraft:air','entry.clearance')
  self.box((54,8,20),(62,8,26),M('smooth_quartz_slab',type='top'),'entry.canopy')
  self.box((54,4,20),(54,7,20),'iron_bars','entry.post')
  self.box((62,4,20),(62,7,20),'iron_bars','entry.post')
  # Coarse TVO lettering on the slope: actual brand, pixel interpretation.
  glyphs={'T':['111','010','010','010','010'],'V':['101','101','101','101','010'],'O':['111','101','101','101','111']}
  for k,ch in enumerate('TVO'):
   for j,row in enumerate(glyphs[ch]):
    for i,v in enumerate(row):
     if v=='1':self.put(85,31-j,48+k*4+i,'white_concrete','tv.wordmark_pixel')
 def facade(self,z,step,x0,x1,y0=30,y1=95):
  p=self.p;f=p['facade'];mode=self.mode
  for y in range(y0,y1+1):
   row=(y-y0)//f['row_height'];dy=(y-y0)%f['row_height'];offset=row%2
   for x in range(x0,x1+1):
    window=(x-x0-offset)%f['pitch']==0 and x>x0 and x<x1
    if mode=='glass_control':self.put(x,y,z,'cyan_stained_glass','facade.control');continue
    if mode=='massing':self.put(x,y,z,'white_concrete','facade.massing');continue
    if not window:self.put(x,y,z,'white_concrete','facade.solid');continue
    self.put(x,y,z,'minecraft:air','facade.opening')
    if dy==3 or y>88:mat='gray_concrete';owner='facade.dark_spandrel'
    else:mat=f['glass_palette'][(x//3+row//4)%len(f['glass_palette'])];owner='facade.glass'
    self.put(x,y,z+step*f['recess_blocks'],mat,owner)
    self.put(x,y,z+step*f['backing_depth_blocks'],'gray_concrete','interior.room_back')
    # Per-window room identity; no random per-block noisy rainbow facade.
    wid=f'{z}:{x}:{row}';lit=int(hashlib.sha256((str(p['lighting']['seed'])+wid).encode()).hexdigest()[:8],16)/2**32<p['lighting']['window_probability']
    if dy==1 and y<89 and lit and p['lighting']['enabled']:
     self.put(x,y,z+step*(f['backing_depth_blocks']-1),'glowstone','lighting.room')
     self.b.rooms.append({'id':wid,'synthetic':True,'anchor':[x,y,z+step*3]})
    if dy==0:self.b.windows.append({'id':wid,'front':[x,y,z],'glass':[x,y,z+step],'synthetic_module':True})
 def tower(self):
  self.shell((14,27,26),(80,96,48),'white_concrete','tower.enclosure')
  for y in range(29,96,4):self.box((15,y,27),(79,y,47),'gray_concrete','interior.floor')
  self.facade(26,1,14,80)
  self.facade(48,-1,21,80,39,94)
  # Front continuous lounge strip immediately above the dark transfer zone.
  self.box((15,27,26),(79,28,26),'black_concrete','tower.transfer')
  self.box((25,29,26),(78,30,26),'gray_stained_glass','tower.lounge_strip')
  # Two unequal deep vertical volumes; river elevation is not a mirrored facade.
  self.shell((14,27,48),(20,96,54),'white_concrete','tower.left_blade')
  self.shell((61,27,48),(73,99,57),'white_concrete','tower.service_blade')
  self.box((59,39,49),(60,94,52),'black_stained_glass','tower.recessed_joint')
  for y in range(40,94,4):
   self.put(67+(y//4)%2,y,57,'gray_stained_glass','tower.service_slit')
   self.put(67+(y//4)%2,y+1,57,'gray_stained_glass','tower.service_slit')
   self.put(14,y,34,'gray_stained_glass','tower.side_slit')
  self.box((14,90,29),(14,94,37),'black_concrete','roof.antenna_recess')
  # Roof enclosure and thin antenna; exact equipment layout not measured.
  self.shell((37,97,32),(54,100,43),'white_concrete','roof.plant')
  self.box((38,101,33),(53,101,42),'iron_bars','roof.railing')
  self.box((48,100,37),(48,101,37),'iron_bars','roof.antenna')
  # Dish silhouette inside an observed top recess, not a full antenna engineering model.
  for y in range(90,95):
   for z in range(30,36):
    if (y-92)**2+(z-32.5)**2<6:self.put(13,y,z,'white_concrete','roof.dish')
  if self.mode=='layered':
   for x in [26,45,65]:self.put(x,8,62,M('end_rod',facing='east'),'lighting.entry')
 def build(self):self.site();self.podium();self.tower();return self.b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--mode',choices=['massing','layered','glass_control'],default='layered');a=ap.parse_args()
 p=json.loads((C/'parameters.json').read_text());p['facade']['mode']=a.mode;t=Osaka(p,a.mode);b=t.build()
 save_run(C,a.run,p,b,Path(__file__),{'route':'image_only_plus_documents','adapter_status':'case_specific','north_verified':False,'world_origin_y_max':320-p['size'][1],'sparse_air':True})
if __name__=='__main__':main()
