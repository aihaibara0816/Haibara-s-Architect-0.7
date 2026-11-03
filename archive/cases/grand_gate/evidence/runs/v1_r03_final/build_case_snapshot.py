"""Whole Hiroshima JP Building, case-specific manually interpreted image adapter.
No automated camera recovery, measurement or photogrammetry. +Z is the selected
long public frontage in working coordinates; no asserted geographic north.
"""
from pathlib import Path
import argparse,json,sys,hashlib
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from hafusion.classical import Builder,M
from hafusion.case_io import save_run
C=Path(__file__).parent
class Hiroshima:
 def __init__(self,p,mode):self.p=p;self.mode=mode;self.b=Builder(p['size'],p['lighting']['seed'])
 def box(self,a,b,m,o):self.b.box(a,tuple(v+1 for v in b),m,o)
 def put(self,x,y,z,m,o):self.b.put(x,y,z,m,o)
 def shell(self,a,b,m,o):
  x0,y0,z0=a;x1,y1,z1=b
  for z in [z0,z1]:self.box((x0,y0,z),(x1,y1,z),m,o)
  for x in [x0,x1]:self.box((x,y0,z0),(x,y1,z1),m,o)
  for y in [y0,y1]:self.box((x0,y,z0),(x1,y,z1),m,o)
 def site(self):
  self.box((3,0,8),(95,1,79),'stone_bricks','site.foundation')
  self.box((3,2,8),(95,2,79),'smooth_stone','site.ground')
  for x in [20,38,57,75]:
   self.box((x-3,3,65),(x+3,3,68),'polished_andesite','site.planter')
   self.box((x-2,4,66),(x+2,4,67),'azalea_leaves','site.planting')
   self.box((x,4,66),(x,7,66),'oak_log','site.tree')
   self.box((x-1,8,65),(x+1,10,67),'azalea_leaves','site.tree')
  for x in [18,36,55,73]:self.box((x,3,71),(x+3,3,71),M('dark_oak_slab',type='bottom'),'site.bench')
 def podium(self):
  p=self.p['podium'];x0,x1=p['x'];z0,z1=p['z']
  # Main enclosing lobby is inset; the public frontage is open underneath.
  self.shell((12,3,17),(81,14,p['front_lobby_z']),'gray_stained_glass','podium.lobby_glass')
  for y in [3,9]:self.box((12,y,17),(81,y,49),'smooth_stone','podium.floor')
  # Lower two-storey glazing and dark structural piers, kept independent.
  for x in range(14,82,7):
   self.box((x,4,49),(x,13,49),'iron_bars','podium.lobby_mullion')
  for x in [17,38,59,80]:self.box((x,3,54),(x+1,14,55),'gray_concrete','podium.pier')
  self.box((10,14,14),(83,14,60),'smooth_quartz','podium.soffit')
  for x in range(12,83,4):self.box((x,13,50),(x,13,59),M('iron_trapdoor',half='top'),'podium.soffit_seam')
  # Second-floor deck and stair/escalator representation at the open frontage.
  self.box((11,9,50),(83,9,57),'smooth_stone','deck.landing')
  for x in range(12,84):self.put(x,10,58,'gray_stained_glass_pane','deck.rail')
  # Stair opening, filled later by the rising flight only.
  self.box((45,9,55),(51,10,61),'minecraft:air','deck.stair_opening')
  for n in range(7):
   y=3+n;z=61-n
   self.box((46,3,z),(50,y-1 if y>3 else 3,z),'gray_concrete','deck.stair_support')
   for x in range(46,51):self.put(x,y,z,M('smooth_quartz_stairs',facing='north'),'deck.stair')
   for x in [45,51]:self.put(x,y+1,z,'iron_bars','deck.stair_rail')
  # The connector is intentionally cropped at the site boundary.
  self.box((82,9,49),(95,9,55),'smooth_stone','deck.connector')
  for z in [49,55]:self.box((84,10,z),(95,10,z),'gray_stained_glass_pane','deck.connector_rail')
  for x in [86,94]:
   self.box((x,3,50),(x,8,50),'gray_concrete','deck.support')
   self.box((x,10,50),(x,13,50),'iron_bars','deck.canopy_post')
  self.box((82,14,48),(95,14,56),M('smooth_quartz_slab',type='top'),'deck.canopy')
  # Three parking floors: dark louvres, offset planters, thin white eaves.
  for y in [15,19,23,27]:self.box((10,y,14),(83,y,60),M('smooth_quartz_slab',type='bottom'),'podium.eave')
  for y0 in [16,20,24]:
   self.box((12,y0-1,16),(81,y0-1,58),'gray_concrete','podium.parking_floor')
   for z in [16,58]:
    self.box((12,y0,z),(81,y0+2,z),'black_concrete','podium.parking_shadow')
    for x in range(13,81):
     self.put(x,y0,z+(-1 if z==16 else 1),'iron_bars','podium.louvre')
     if (x+(y0//4)%2*3)%8<5:
      self.put(x,y0+1,z+(-1 if z==16 else 1),M('smooth_stone_slab',type='top'),'podium.planter')
      self.put(x,y0+2,z+(-1 if z==16 else 1),'azalea_leaves','podium.green_wall')
   for x in [12,81]:
    self.box((x,y0,17),(x,y0+2,57),'black_concrete','podium.parking_shadow')
    for z in range(17,58):
     self.put(x+(-1 if x==12 else 1),y0,z,'iron_bars','podium.louvre')
     if z%8<5:
      self.put(x+(-1 if x==12 else 1),y0+1,z,M('smooth_stone_slab',type='top'),'podium.planter')
      self.put(x+(-1 if x==12 else 1),y0+2,z,'azalea_leaves','podium.green_wall')
  # Roof garden on the remaining rear podium strip, schematic vegetation.
  self.box((16,27,15),(27,27,20),'dark_oak_planks','podium.roof_garden')
  self.box((17,28,16),(26,28,17),'azalea_leaves','podium.garden_edge')
  # Public entrances and through-route use two-block-high explicit clearances.
  self.box((69,4,17),(73,7,49),'minecraft:air','entry.passage')
  self.box((23,10,49),(27,12,50),'minecraft:air','entry.level2')
  if self.mode=='layered':
   for y in [18,22,26]:
    # Put emitters behind actual planted cells, not visible gaps between boxes.
    offset=((y-2)//4)%2*3
    for x in range(13,82):
     if (x+offset)%8==2:self.put(x,y,58,'glowstone','lighting.eave')
    for z in range(18,59,8):self.put(12,y,z,'glowstone','lighting.eave')
   for x in [25,45,65,78]:self.put(x,13,53,'sea_lantern','lighting.soffit')
 def floor_at(self,y):
  levels=self.p['tower']['floor_y'];i=max(j for j,v in enumerate(levels) if y>=v);return i,levels[i]
 def facade(self,axis,plane,inside,start,end,fin_positions):
  p=self.p;f=p['facade'];levels=p['tower']['floor_y']
  def put(u,y,d,m,o):
   q=[u,y,plane+inside*d] if axis=='x' else [plane+inside*d,y,u]
   self.put(*q,m,o)
  for y in range(27,90):
   row,fy=self.floor_at(min(y,88));dy=y-fy
   for u in range(start,end+1):
    if self.mode=='massing':put(u,y,0,'white_concrete','facade.massing');continue
    if self.mode=='glass_control':put(u,y,0,'cyan_stained_glass','facade.control');continue
    fin=u in fin_positions
    if fin:
     put(u,y,0,'smooth_quartz','facade.main_fin');put(u,y,1,'light_gray_concrete','facade.fin_return')
    else:
     mat='gray_concrete' if y in levels else f['glass_palette'][(u//7)%len(f['glass_palette'])]
     put(u,y,1,mat,'facade.spandrel' if y in levels else 'facade.glass')
     if u%7==2:put(u,y,0,'iron_bars','facade.secondary_mullion')
    if y<88:
     put(u,y,4,'gray_concrete','interior.backing')
     if y in levels:put(u,y,2,'gray_concrete','interior.reveal_support');put(u,y,3,'gray_concrete','interior.reveal_support')
     room=f'{axis}:{plane}:{row}:{u//4}';lit=int(hashlib.sha256((str(p['lighting']['seed'])+room).encode()).hexdigest()[:8],16)/2**32<p['lighting']['window_probability']
     if dy==2 and u%4==1 and lit and self.mode=='layered':
      put(u,y,3,'glowstone','lighting.window');self.b.rooms.append({'id':room,'synthetic':True})
     if dy==1 and u%8==4 and self.mode=='layered':put(u,y,3,'bookshelf','interior.synthetic_desk')
     if dy==1 and not fin:self.b.windows.append({'id':room,'axis':axis,'plane':plane,'u':u,'y':y,'synthetic_module':True})
  if self.mode=='layered':
   for u in fin_positions:put(u,90,0,M('smooth_quartz_slab',type='bottom'),'roof.fin_tip')
 def tower(self):
  p=self.p['tower'];x0,x1=p['x'];z0,z1=p['z']
  for y in p['floor_y']:
   self.box((x0+1,y,z0+1),(x1-1,y,z1-1),'gray_concrete','interior.floor')
  self.facade('x',z1,-1,x0+2,x1-2,self.p['facade']['fin_x'])
  self.facade('x',z0,1,x0+2,x1-2,self.p['facade']['fin_x'])
  self.facade('z',x0,1,z0+2,z1-2,self.p['facade']['fin_z'])
  self.facade('z',x1,-1,z0+2,z1-2,self.p['facade']['fin_z'])
  if self.mode=='layered':
   for x in self.p['facade']['fin_x']:
    self.put(x,28,z1+1,'end_rod','lighting.fin_base')
    self.put(x,27,z1+1,'smooth_quartz','lighting.fin_base_support')
  # Glazed stepped corners separate the white fins on adjacent faces.
  for x,z,dx,dz in [(x0,z0,1,1),(x0,z1,1,-1),(x1,z0,-1,1),(x1,z1,-1,-1)]:
   for y in range(27,90):
    for a,b in [(0,2),(1,1),(2,0)]:
     xx=x+a*dx;zz=z+b*dz
     self.put(xx,y,zz,'gray_concrete' if y in p['floor_y'] else 'gray_stained_glass','tower.corner_glass')
    if self.mode=='layered':self.put(x+dx,y,z+dz,'end_rod','lighting.corner')
   # Each corner light is supported at the same base level as the facade.
   self.put(x+dx,26,z+dz,'smooth_quartz','tower.corner_support')
  # Rear service volume from the published typical plan, not a mirrored front.
  self.shell((31,27,18),(62,89,27),'light_gray_concrete','tower.core')
  for y in range(29,88,4):
   for x in [34,59]:self.box((x,y,18),(x+1,y+1,18),'black_stained_glass','tower.core_slit')
  # Roof plant is approximate; original aerial supports the presence, not locations.
  self.box((17,88,25),(76,88,50),'gray_concrete','roof.deck')
  for x in [23,36,49,62]:
   self.shell((x,89,31),(x+7,90,39),'polished_andesite','roof.plant_schematic')
   self.box((x+1,90,32),(x+6,90,38),'iron_trapdoor','roof.plant_grille')
 def build(self):self.site();self.podium();self.tower();return self.b
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--mode',choices=['massing','glass_control','layered'],default='layered');a=ap.parse_args()
 p=json.loads((C/'parameters.json').read_text());p['facade']['mode']=a.mode;b=Hiroshima(p,a.mode).build()
 save_run(C,a.run,p,b,Path(__file__),{'route':p['route'],'adapter_status':'case_specific','north_verified':False,'world_origin_y_max':320-p['size'][1],'sparse_air':True})
if __name__=='__main__':main()
