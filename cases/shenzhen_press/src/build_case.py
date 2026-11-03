"""HAF mainline Shenzhen case V2. Baseline V1 and HA03 remain archived.
Case geometry consumes shared HAF stages, room lighting and thin-state support.
"""
import sys,json,math,hashlib,argparse,os,copy
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
HAF=ROOT.parents[1]
sys.path.insert(0,str(HAF));sys.path.insert(0,str(HAF/'support'))
from hafusion.cache import Stages
from hafusion.lighting import room_lighting, unit
from research_lab.stage_cache import digest
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build,inspect,bbox
from detail_lab import states
states.FULL.add('cyan_stained_glass');states.PANES.add('cyan_stained_glass_pane')
M=states.make
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Geometry:
 def __init__(self,prefix):self.cells={};self.prefix=prefix;self.cuts=[]
 def put(self,x,y,z,mat,sub):
  p=(int(x),int(y),int(z));assert all(0<=p[i]<[68,214,68][i] for i in range(3)),p
  self.cells[p]=[mat,self.prefix+'.'+sub]
 def box(self,lo,hi,mat,sub):
  for y in range(lo[1],hi[1]):
   for z in range(lo[2],hi[2]):
    for x in range(lo[0],hi[0]):self.put(x,y,z,mat,sub)
 def line(self,a,b,mat,sub):
  n=max(abs(b[i]-a[i]) for i in range(3))*3
  for j in range(int(n)+1):
   v=[round(a[i]+(b[i]-a[i])*j/max(1,n)) for i in range(3)];self.put(*v,mat,sub)
 def out(self):return {'cells':[[*p,*v] for p,v in sorted(self.cells.items())],'cuts':self.cuts}
def frontage(p,x):return int(round(p['front_center_z']+p['bow']*((x+.5-p['center_x'])/((p['xmax']-p['xmin'])/2))**2))
def route(p):
 # 4-connected facade edge; panes cannot bridge diagonal-only neighbours.
 path=[];last=None
 for x in range(p['xmin'],p['xmax']):
  z=frontage(p,x)
  if last is not None:
   for zz in range(min(last,z),max(last,z)+1):path.append((x,zz))
  path.append((x,z));last=z
 return sorted(set(path))
def site(p):
 g=Geometry('site');g.box(p['bounds'][:3],p['bounds'][3:],'paving','base')
 for z in range(4,16,3):g.box((25,1,z),(43,2,z+1),'white','paving_inlay')
 for i,(x,z) in enumerate(p['planters']):
  g.box((x-2,2,z-2),(x+3,3,z+3),'slab','planter_rim')
  g.box((x-1,2,z-1),(x+2,3,z+2),'soil','planter_soil')
  g.box((x-1,3,z-1),(x+2,4,z+2),'green','planting')
  g.box((x,3,z),(x+1,9,z+1),'trunk','palm'+str(i))
  for dx,dz in [(3,0),(-3,0),(0,3),(0,-3),(2,2),(-2,-2)]:
   g.line((x,9,z),(x+dx,8,z+dz),'leaves','palm'+str(i))
  g.put(x,4,z-2,'flower','accent')
 for x in range(16,55,5):g.put(x,2,5,'bollard','approach_bollards')
 return g.out()
def podium(p):
 g=Geometry('podium');path=route(p)
 # Interior occupied depth and the front 5–7 cells of clear portico remain separate.
 for x in range(9,61):
  z0=frontage(p,x)
  g.box((x,2,z0),(x+1,4,p['back_z']),'paving','floor')
  g.box((x,4,z0+6),(x+1,5,p['back_z']),'floor','lobby_floor')
  g.box((x,20,z0+3),(x+1,21,p['back_z']),'slab','roof')
  for y in range(5,20):
   if not(p['entry_x'][0]<=x<p['entry_x'][1] and y<13):g.put(x,y,z0+7,'pane','recessed_glazing')
  for y in [10,15]:
   if not 26<=x<42:g.box((x,y,z0+7),(x+1,y+1,48),'floor_slab','mezzanine')
 for x,z in path:
  for y in p['ribbon_ys']:
   if 26<=x<42 and 5<y<17:continue
   g.put(x,y,z,'slab_top' if y<21 else 'white','outer_ribbon')
   if y==21:g.put(x,y,z+1,'white','roof_edge')
 for i,x in enumerate([8,18,25,42,52,60]):
  z=frontage(p,x);g.box((x,4,z),(x+1,21,z+1),'white','portico_post'+str(i))
 # Entrance stair = actual stair state, direction ascends towards +Z.
 for i in range(3):g.box((26,2+i,12+i*2),(42,3+i,14+i*2),'stair_s','entry_stair')
 g.box((26,4,18),(42,5,30),'paving','entry_landing')
 g.box((26,13,13),(42,14,28),'glass','canopy_glazing')
 for x in [26,31,36,41]:
  g.box((x,12,13),(x+1,13,29),'slab_top','canopy_beam')
  g.line((x,15,27),(x,14,14),'bar','canopy_tie')
 for z in [13,18,23,27]:g.box((26,12,z),(42,13,z+1),'trap','canopy_purlin')
 for x in [26,41]:g.box((x,5,14),(x+1,13,15),'white','canopy_post')
 # Lobby closure/doors is set back beyond the open portico.
 for x in range(22,47):
  for y in range(5,17):
   if not (31<=x<37 and y<10):g.put(x,y,31,'pane' if x%4 else 'bar','lobby_curtain')
 g.box((20,17,32),(48,18,45),'slab','lobby_ceiling')
 for x in [22,46]:g.box((x,5,35),(x+2,17,37),'paving','lobby_column')
 for x in [24,34,44]:g.put(x,16,33,'light','lobby_lamp')
 # Thin internal stair with open side railing, low-confidence interpretation of lobby photo.
 for i in range(7):g.box((44,5+i,36+i),(47,6+i,37+i),'stair_s','lobby_stair')
 for i in range(7):g.put(43,7+i,36+i,'bar','lobby_stair_rail')
 g.box((9,21,37),(18,22,44),'green','roof_garden')
 # Text is not rendered as arbitrary glyph blocks. The physical sign strip is retained.
 for x in [21,24,27,30,33,36,39,42,45,48]:g.put(x,21,frontage(p,x)-1,'red','sign_markers')
 # Enclose occupied rear/ends; keep the observed FRONT loggia and entrance open.
 for y in range(5,21):
  for x in range(9,61):
   if 33<=x<37 and y<9:continue  # documented service opening, not accidental air
   role='pane_gray' if y in [6,7,8,11,12,13,16,17,18] and x%6 else 'white'
   g.put(x,y,48,role,'rear_enclosure')
  for x in [9,60]:
   for z in range(frontage(p,x)+7,48):
    g.put(x,y,z,'pane_gray' if y%5 in [1,2,3] else 'white','end_enclosure')
 # Rear occupied bays have window-back partitions and floors.
 for x in range(10,60):
  for y in [5,10,15,20]:g.box((x,y,40),(x+1,y+1,48),'floor_slab','rear_floors')
  for y in range(6,20):g.put(x,y,40,'floor','rear_room_back')
 for x in [14,23,31,43,53]:
  lp=room_lighting(p['lighting_seed'],'podium',f'podium.rear.{x}',x//14,.55)
  if lp['lit']:g.put(x,18,44,'warm' if lp['material']=='glowstone' else 'light','rear_room_lamp')
 # Front has a substantial top fascia, thinner lower ribbons, a diagonal prow.
 for (x,y,z),v in list(g.cells.items()):
  if v[1]=='podium.outer_ribbon' and (x<19 and y<20 or x>round(55+(y-5)*.42)):
   del g.cells[(x,y,z)]
 for x,z in path:
  g.box((x,20,z),(x+1,22,z+3),'white','thick_top_fascia')
  if x>=54:
   for y in [5,9,13,17]:
    tip=round(55+(y-5)*.42)
    if x<=tip:g.put(x,y,z,'slab_top','graduated_right_ribbon')
 for y in range(5,22):
  x=round(55+(y-5)*.42); z=frontage(p,x)
  g.put(x,y,z,'white','diagonal_prow')
  g.put(x,y,z+1,'white','diagonal_prow')
 # Low, solid left wing supports planting above, rather than another equal ribbon.
 for x in range(8,20):
  z0=max(29,frontage(p,x)+2)
  for y in range(4,16):
   g.put(x,y,z0,'white','left_solid_wing')
   g.put(x,y,44,'white','left_wing_back')
  g.box((x,15,z0),(x+1,16,45),'slab','left_terrace')
 for z in range(30,45):g.box((8,4,z),(9,16,z+1),'white','left_wing_end')
 g.box((10,16,33),(17,17,43),'green','left_terrace_planting')
 for x in range(10,18):g.put(x,17,32,'bar','terrace_rail')
 for y in range(4,19):
  for x in range(17,22):
   for z in range(27,32):
    d=(x-19)**2+(z-29)**2
    if 2<=d<=6:g.put(x,y,z,'white','round_corner_core')
 # Fill soffit grids only where floors actually exist, not across the open entrance.
 for x in list(range(20,26))+list(range(43,56)):
  for y in [9,14,19]:
   z0=frontage(p,x)+2
   g.box((x,y,z0),(x+1,y+1,z0+4),'trap','loggia_soffit')
 return g.out()
def core(p):
 g=Geometry('core')
 for side,b in [(s,p[s]) for s in ['left','right']]:
  g.box(b[:3],b[3:],'white',side)
  # Hollow vertical service volume: core occupies real walls, not a full solid bar.
  for x in range(b[0]+1,b[3]-1):
   for z in range(b[2]+1,b[5]-1):
    for y in range(b[1]+1,b[4]-1):g.cells.pop((x,y,z),None)
  if side=='left':
   for y in range(31,144,6):g.box((12,y,33),(13,y+2,34),'darkglass','left_windows')
  else:
   for y in range(32,150,6):g.box((58,y,38),(59,y+2,40),'darkglass','right_windows')
   for y in [151,154]:g.box((53,y,31),(60,y+1,33),'darkglass','upper_slots')
 g.box((7,22,38),(13,23,50),'floor_slab','left_wing_base')
 for x in [49,57]:g.box((x,22,49),(x+2,29,51),'white','rear_wing_pilotis')
 for y in range(22,29):
  for x in range(17,53):g.put(x,y,46,'pane_gray','rear_base_enclosure')
 # Wider left window wing and a rounded glass connector, visible in two photos.
 for y in range(23,140):
  for x in range(7,12):
   g.put(x,y,38,'darkglass' if (y-29)%6 in [1,2,3] else 'white','left_window_wing')
   g.put(x,y,49,'darkglass' if (y-29)%6 in [1,2,3] else 'white','left_wing_rear')
  for z in range(39,49):g.put(7,y,z,'darkglass' if (y-29)%6 in [1,2,3] else 'white','left_wing_return')
  for x,z in [(9,36),(10,35),(11,35),(12,36),(12,37),(9,37)]:
   g.put(x,y,z,'glass','round_green_connector')
  if (y-29)%6==0:
   g.box((8,y,39),(12,y+1,49),'floor_slab','wing_floors')
   for x,z in [(9,35),(10,34),(11,34),(12,35)]:g.put(x,y,z,'trap','connector_transom')
 # Side/rear depth behind the high core is visible; full rear pattern is estimated.
 for y in range(29,140):
  for x in range(48,59):g.put(x,y,51,'darkglass','rear_wing_back')
  for z in range(46,52):g.put(58,y,z,'darkglass','rear_wing_side')
  for z in range(47,51):g.put(60,y,z,'glass','rear_green_seam')
  if (y-29)%12==0:
   g.box((48,y,47),(60,y+1,53),'slab_top','rear_wing_ledges')
 g.box((7,140,38),(13,142,50),'white','left_wing_cap')
 # Roof cores have actual depth and a restrained cap, not two thin sticks.
 for x in range(11,23):
  top=147-max(0,(x-16)//3)
  for y in range(140,top):
   for z in range(32,47):
    if x in [11,22] or y in [140,top-1] or z in [32,46]:g.put(x,y,z,'white','left_roof_mass')
 g.box((51,140,34),(59,157,48),'white','right_roof_mass')
 for y in [151,154]:
  g.box((52,y,31),(60,y+1,34),'darkglass','roof_recess_slots')
  g.box((52,y+1,30),(60,y+2,34),'slab','roof_slot_lips')
 for x in range(23,51):
  crest=141+round(2*math.sin(math.pi*(x-23)/28))
  g.box((x,140,37),(x+1,crest,44),'floor','recessed_roof_link')
  g.box((x,crest,37),(x+1,crest+1,44),'slab','roof_link_cover')
 return g.out()
def tower(p):
 g=Geometry('tower');edge=route(p)
 for y in range(p['y0'],p['y1']):
  cutoff=round(p['right_bottom_x']+(y-p['y0'])*p['right_slope'])
  for x,z in edge:
   if x>cutoff:continue
   g.put(x,y,z,p['curved_glass_role'],'curved_skin')
   if (y-p['y0'])%p['band_pitch']==0:g.put(x,y,z-1,'trap','fine_horizontal')
   if p['external_vertical_grid'] and (x-15)%5==0 and (y-p['y0'])%p['band_pitch']!=0:g.put(x,y,z-1,'bar','fine_vertical')
  # Recessed trapezoid grid is a separate planar band behind the curved skin.
  for x in range(cutoff+1,56):
   g.put(x,y,32,'bar' if x%3==0 else 'pane_gray','side_grid')
   if (y-p['y0'])%6==0:g.put(x,y,31,'slab_top','side_transom')
  for x in range(16,54):g.put(x,y,p['back_z'],'pane_gray','back_completion')
  for x in [16,53]:
   for z in range(34,p['back_z']):g.put(x,y,z,'pane_gray','side_return')
  if (y-p['y0'])%p['floor_pitch']==0:
   for x in range(16,54):
    z0=frontage(p,x)+1;g.box((x,y,z0),(x+1,y+1,p['back_z']),'floor_slab','interior_floor')
 for y in [59,96]:
  for x,z in edge:
   if 19<=x<=47:
    g.put(x,y,z-1,'white','wide_pale_band');g.put(x,y+1,z-1,'slab','wide_pale_band')
 # Base is open in front of inner glazing, with substantial round-column approximation.
 for x in [18,27,36,45,52]:
  for xx in range(x-1,x+2):
   for zz in range(28,31):
    if (xx-x)**2+(zz-29)**2<=1:g.box((xx,22,zz),(xx+1,29,zz+1),'white','pilotis')
 for x in range(17,53):
  for y in range(22,29):g.put(x,y,34,'pane','setback_lobby')
 g.box((17,29,37),(53,140,38),'floor','inner_back')
 # Perimeter roof / recessed equipment, no unobserved dramatic roof inventions.
 for x in range(16,54):g.box((x,139,frontage(p,x)+1),(x+1,140,46),'floor','roof')
 return g.out()
def eye(p):
 g=Geometry('eye');g.cuts=[{'lo':p['cavity_min'],'hi':[p['cavity_max'][0],p['cavity_max'][1],38],'owner_prefixes':['tower.'],'reason':'Observed real void in facade; cut before news-eye assembly'}]
 cx,cy,cz=p['center'];r=p['radius']
 for x in range(math.floor(cx-r),math.ceil(cx+r)):
  for y in range(math.floor(cy-r),math.ceil(cy+r)):
   for z in range(math.floor(cz-r),math.ceil(cz+r)):
    dx,dy,dz=x+.5-cx,y+.5-cy,z+.5-cz;dist=math.sqrt(dx*dx+dy*dy+dz*dz)
    if r-p['skin']<dist<=r:g.put(x,y,z,'glass','globe_skin')
 # Restrained meridians and latitudes, no thick polygonal cage replacing glass.
 for y in [122,125,129]:
  rr=math.sqrt(max(0,r*r-(y+.5-cy)**2))
  for a in range(0,360,3):g.put(round(cx-.5+rr*math.cos(math.radians(a))),y,round(cz-.5+rr*math.sin(math.radians(a))),'bar','globe_grid')
 y=p['platform_y'];g.box((24,y,17),(34,y+1,21),'slab_top','platform_frame')
 for x in range(26,32):
  for z in range(18,20):g.cells.pop((x,y,z),None)
 g.box((29,y,20),(31,y+1,37),'floor_slab','bridge')
 g.box((22,117,36),(39,137,37),'floor','cavity_back')
 for y in [133,136]:g.box((21,y,24),(39,y+1,25),'trap','header_louver')
 for x in [22,37]:g.box((x,118,34),(x+1,137,35),'chain','rear_tie')
 # Dark globe lounge, a tiny warm light, not a solid luminous sphere.
 g.box((27,124,24),(33,125,28),'floor_slab','lounge_floor');g.put(29,127,28,'warm','lounge_light')
 return g.out()
def crown(p):
 g=Geometry('crown');mx,mz=p['mast_center']
 g.box((44,p['core_top'],37),(45,p['rack_y1']+1,38),'white','rack_upright')
 for y in range(p['rack_y0'],p['rack_y1']+1,p['hoop_pitch']):
  # Shallow bowed sail ribs fixed between upright and mast; not full circular rings.
  pts=[]
  for x in range(44,mx+1):
   t=(x-44)/(mx-44);z=round(mz-4*math.sin(math.pi*t));pts.append((x,y,z))
  for a,b in zip(pts,pts[1:]):g.line(a,b,'slab_top','open_ribs')
  for x,z in [(48,35),(52,36)]:g.line((x,y,z),(mx,y+2,mz),'chain','rib_brace')
 g.box((mx-1,p['core_top'],mz-1),(mx+1,p['mast_base_top'],mz+1),'white','mast_root')
 g.box((mx,p['mast_base_top'],mz),(mx+1,p['tip_top_exclusive'],mz+1),'bar','mast_tip')
 # A short dark transition avoids treating the entire roof as a glowing tower.
 for y in [153,156]:g.box((52,y,31),(60,y+1,33),'slab_top','core_cap')
 return g.out()
def interior(p):
 g=Geometry('interior');rooms=[]
 tower_front={'xmin':14,'xmax':54,'front_center_z':23,'center_x':34,'bow':9}
 for y in p['floor_ys']:
  for x in p['room_centers_x']:
   if y>=113 and x<41:continue  # preserve news-eye void, not just the facade hole
   rid=f'office.front.y{y}.x{x}';z0=max(frontage(tower_front,xx) for xx in range(x-2,x+3))+2
   lp=room_lighting(p['seed'],f'floor{y}',rid,'left' if x<32 else 'right',p['activity'])
   g.box((x-2,y,z0),(x+3,y+1,36),'floor_slab',rid+'.floor')
   g.box((x-2,y+5,z0),(x+3,y+6,36),'floor_slab',rid+'.ceiling')
   g.box((x-2,y+1,35),(x+3,y+5,36),'floor',rid+'.back')
   # Partition stays behind glazing; avoid opaque stripes occupying the curtain.
   for xx in [x-2,x+2]:g.box((xx,y+1,z0+1),(xx+1,y+5,36),'floor',rid+'.partition')
   style=int(unit(0,'furniture',rid)*3)
   if style==0:
    g.box((x-1,y+2,z0+3),(x+2,y+3,z0+5),'desk',rid+'.desk')
    g.put(x,y+1,min(34,z0+5),'chair',rid+'.chair');g.put(x,y+3,z0+4,'dark',rid+'.screen')
   elif style==1:
    g.box((x-1,y+1,33),(x+2,y+2,34),'chair',rid+'.seating')
    g.box((x-1,y+1,31),(x+2,y+2,32),'desk',rid+'.low_table')
   else:
    g.box((x-1,y+1,34),(x+2,y+4,35),'desk',rid+'.storage')
    g.put(x,y+1,z0+3,'green',rid+'.indoor_green')
   lamps=[]
   for j in range(lp['fixture_count']):
    lx=x+lp['offset_x'] if j==0 else x-lp['offset_x']
    lz=min(33,z0+1+lp['depth']+j)
    pos=(lx,y+4,lz);g.put(*pos,'warm' if lp['material']=='glowstone' else 'light',rid+'.lamp');lamps.append(pos)
   rooms.append({'id':rid,'box':[x-2,y,z0,x+3,y+6,36],'lighting':lp,'lamp_positions_work':lamps,'fidelity':'synthetic office depth, not surveyed interior'})
  for x in [21,29,37,45]:
   rid=f'office.rear.y{y}.x{x}'
   lp=room_lighting(p['seed'],f'floor{y}',rid,'rear',p['activity']*.85)
   g.box((x-3,y,38),(x+4,y+1,46),'floor_slab',rid+'.floor')
   g.box((x-3,y+5,38),(x+4,y+6,46),'floor_slab',rid+'.ceiling')
   g.box((x-3,y+1,38),(x+4,y+5,39),'floor',rid+'.back')
   g.box((x-3,y+1,39),(x-2,y+5,45),'floor',rid+'.partition')
   g.box((x-1,y+2,40),(x+2,y+3,42),'desk',rid+'.desk')
   lamps=[]
   if lp['lit']:
    pos=(x+lp['offset_x'],y+4,42+lp['depth']);g.put(*pos,'warm' if lp['material']=='glowstone' else 'light',rid+'.lamp');lamps.append(pos)
   rooms.append({'id':rid,'box':[x-3,y,38,x+4,y+6,46],'lighting':lp,'lamp_positions_work':lamps,'fidelity':'estimated rear office'})
 out=g.out();out['rooms']=rooms;return out

BUILDERS={'site':site,'podium':podium,'core':core,'tower':tower,'eye':eye,'crown':crown,'interior':interior}
PALETTE={'white':M('smooth_quartz'),'glass':M('cyan_stained_glass'),'darkglass':M('gray_stained_glass'),'pane':M('cyan_stained_glass_pane'),'pane_gray':M('gray_stained_glass_pane'),'bar':M('iron_bars'),'chain':M('chain'),'rod':M('end_rod'),'slab':M('smooth_quartz_slab'),'slab_top':M('smooth_quartz_slab',type='top'),'floor_slab':M('smooth_stone_slab'),'trap':M('iron_trapdoor',half='top'),'stair_s':M('smooth_quartz_stairs',facing='south'),'floor':M('gray_concrete'),'paving':M('smooth_stone'),'green':M('moss_block'),'soil':M('dirt'),'trunk':M('oak_log'),'leaves':M('oak_leaves'),'flower':M('poppy'),'bollard':M('end_rod'),'red':M('red_concrete'),'light':M('sea_lantern'),'warm':M('glowstone'),'desk':M('dark_oak_slab',type='top'),'chair':M('dark_oak_stairs',facing='south'),'dark':M('black_concrete')}
REGIONS={
 'site':[('broker_3',[0,.44,1,1],'路缘/棕榈/入口周边，小场地补全')],
 'podium':[('prior_04',[0,.25,1,.85],'船形薄层带与敞廊'),('broker_1',[0,0,1,.86],'雨棚梁/下表面/退后门厅'),('broker_4',[.45,.3,.9,.85],'大厅夹层楼梯，仅低置信度参考')],
 'core':[('N13',[.28,.15,.7,.8],'左侧横窗翼与圆玻璃接缝，尺度估算'),('N14',[.49,.3,.6,.88],'高核心背后绿色玻璃和挑边，不能外推完整背面'),('prior_00',[.31,.29,.41,.86],'低侧实体翼'),('prior_01',[.62,.24,.71,.78],'偏置高核心')],
 'tower':[('prior_02',[.08,.1,.65,.85],'弧形玻璃与细水平线'),('prior_02',[.66,.12,.88,.88],'斜边局部网格'),('prior_00',[.37,.75,.65,.88],'塔脚柱与内退门厅')],
 'eye':[('prior_03',[.32,.08,.82,.86],'洞口/球/方框平台/后部细构件')],
 'crown':[('prior_00',[.53,.02,.66,.28],'开放格架接细桅杆'),('prior_05',[.61,.18,.76,.42],'格架实际进深')],
 'interior':[('broker_2',[0,.03,1,.95],'大厅材料层次低置信度'),('prior_02',[.1,.25,.61,.8],'窗后进深需要；办公布置为游戏补全')]
}
def run(runid,params):
 out=ROOT/'runs'/runid
 if out.exists():raise ValueError('Select a fresh run directory')
 out.mkdir(parents=True)
 source_hash=sha(ROOT/'input/manifest.json')
 st=Stages(ROOT/'cache',{'frame_id':'szpress-xright-yup-zback-0p8','units':'block','target_epoch':'2026-study','source_hash':source_hash},digest({'adapter':sha(Path(__file__)),'parameters_version':params['adapter_version'],'lighting_module':sha(HAF/'hafusion/lighting.py'),'stages':sha(HAF/'hafusion/cache.py'),'state_module':sha(HAF/'support/detail_lab/states.py')}))
 scene=Scene((68,214,68));overlaps=Counter();cut_counts=[];components={}
 for group,builder in BUILDERS.items():
  geo=st.run(group+'.geometry',params[group],{},lambda b=builder,p=params[group]:b(p))
  mat=st.run(group+'.materials',PALETTE,{'geometry':group+'.geometry'},lambda g=geo:{'cells':[[*r[:3],PALETTE[r[3]],r[4]] for r in g['cells']],'cuts':g['cuts']})
  for c in mat['cuts']:
   n=0
   for p in list(scene.blocks):
    if all(c['lo'][i]<=p[i]<c['hi'][i] for i in range(3)) and any(scene.owners[p].startswith(prefix) for prefix in c['owner_prefixes']):scene.set(p,'minecraft:air','void');n+=1
   cut_counts.append({**c,'removed':n})
  for r in mat['cells']:
   p=tuple(r[:3]);s,owner=r[3:];old=scene.owners.get(p)
   if old and old!=owner:overlaps[(old,owner)]+=1
   scene.set(p,s,owner)
  if group=='interior':dump(out/'rooms.json',geo['rooms'])
 # Same published paper->Minecraft basis correction, not shared shape interpretation.
 reflected=Scene(scene.size)
 from vendor.voxel_core import parse_state,state
 for (x,y,z),s in scene.blocks.items():
  n,p=parse_state(s);p=dict(p)
  if p.get('facing') in ['east','west']:p['facing']={'east':'west','west':'east'}[p['facing']]
  if 'east' in p:p['east'],p['west']=p['west'],p['east']
  reflected.set((67-x,y,z),state(n,**p),scene.owners[(x,y,z)])
 scene=reflected
 connected=states.connect(scene)
 for s in set(scene.blocks.values()):states.validate(s)
 meta=export_structure(scene,out/'building.nbt',3955,False);read=load_build(out/'building.nbt')
 assert read.size==scene.size and read.blocks==scene.blocks,'Independent NBT roundtrip mismatch'
 for pos,owner in scene.owners.items():components.setdefault(owner,[]).append(pos)
 comp={k:{'blocks':len(v),'bbox':bbox(v),'evidence_group':k.split('.')[0]} for k,v in components.items()}
 dump(out/'components.json',comp);dump(out/'blocks.json',{'size_xyz':list(scene.size),'blocks':[[*p,s,scene.owners[p]] for p,s in sorted(scene.blocks.items())]})
 dump(out/'inspection.json',inspect(read));dump(out/'cache_report.json',st.summary());dump(out/'params_used.json',params)
 dump(out/'assembly_report.json',{'void_operations':cut_counts,'overlaps':[{'earlier':a,'later':b,'cells':n,'review':'layer precedence; inspect component bounds and focused QA'} for (a,b),n in overlaps.items()],'pane_connections_updated':connected})
 dump(out/'build_report.json',{'route':'HAF','engine':'HAF mainline + SZ case adapter 0.2.0 + shared seeded lighting + Detail Lab','nbt':meta,'components':len(comp),'nbt_readback_exact_match':True,'state_validation':'explicit local vanilla subset; not authoritative game registry','runtime_game_test':'pending','native_canton_pipeline_used':False,'automatic_model_or_image_fusion':False,'geometry_case_specific':True,'limitations':['Rear facade and offices are estimated','No calibrated camera/survey data','State preview shapes approximate; no Minecraft runtime','Paper work-frame X reflected on export to respect right-handed Minecraft front orientation']})
 print(json.dumps({'nbt':meta,'components':len(comp),'cache':{'hits':st.summary()['hits'],'rebuilt':len(st.summary()['rebuilt'])}},ensure_ascii=False),flush=True)
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',default='r01');ap.add_argument('--spec-only',action='store_true');ap.add_argument('--params',type=Path,default=ROOT/'research/parameters.json');a=ap.parse_args()
 reads=set();forbidden=(ROOT.parent/'HA03').resolve()
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes)):
   p=Path(os.fsdecode(args[0])).absolute()
   if p.is_relative_to(forbidden):raise PermissionError('Other route is forbidden: '+str(p))
   if p.is_relative_to(ROOT):reads.add(str(p.relative_to(ROOT)))
 sys.addaudithook(audit)
 params=json.loads(a.params.read_text())
 dump(ROOT/'research/decision_log.json',{'status':'v2_haf_mainline_revision','route':'HAF','source_code_sha256':sha(Path(__file__)),'parameters_sha256':sha(ROOT/'research/parameters.json'),'same_operator_nonblind':True,'key_decisions':['浅弧连续玻璃线/后退侧网格/半砖与活板门薄边分层','眼球真实球壳，先切洞，悬挂线不加粗','船形敞廊、后排玻璃、雨棚底梁分层','楼层内饰是可见深度补全，不宣称实测办公室'],'case_adapter_scope':'Only this building; unchanged HAF stage cache; no universal automatic architectural inference'})
 dump(ROOT/'research/evidence_regions.json',{'method':'manual reviewed rectangles, not automatic segmentation','groups':{k:[{'image_id':i,'bbox_normalized':b,'observation':t,'consumer':'BUILDERS.'+k,'parameter_group':k,'status':'estimated'} for i,b,t in v] for k,v in REGIONS.items()}})
 if not a.spec_only:run(a.run,params)
 dump(ROOT/'research/runtime_reads.json',{'forbidden_route':'HA03','rejected_access':0,'recorded_paths':sorted(reads),'scope':'Python route-tree open events, not cognitive blindness'})
