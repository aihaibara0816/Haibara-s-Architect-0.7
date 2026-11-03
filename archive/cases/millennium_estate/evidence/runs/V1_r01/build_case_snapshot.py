"""Six original millennium-era apartment towers. Explicit case adapter, not image reconstruction."""
from pathlib import Path
import sys,json,argparse,hashlib,math
from collections import Counter
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump,sha
from hafusion.design_handoff import compile_handoff
from detail_lab import states
M=states.make
def rnd(key):return int(hashlib.sha256(key.encode()).hexdigest()[:12],16)/16**12

def build(p,run):
 b=Builder(p['size_xyz'],p['seed']);g=p['grade_y'];pitch=p['floor_pitch']
 lamps=[];trees=[];stairs=[];entries=[];units=[];modules=[];plans=[];specs=[];paths=set();facades=[];floor_records=[]
 def box(x0,z0,x1,z1,y0,y1,mat,own):b.box((x0,y0,z0),(x1,y1,z1),mat,own)
 def light(x,y,z,mat,own):b.put(x,y,z,mat,own);lamps.append({'xyz':[x,y,z],'material':mat,'owner':own})
 def path(rect):
  x0,z0,x1,z1=rect
  for x in range(x0,x1):
   for z in range(z0,z1):paths.add((x,z))
 box(0,0,160,148,0,2,'dirt','site.foundation');box(0,0,160,148,2,3,'grass_block','site.lawn')
 # Road and pavement frame, not an infinite ground plane.
 for x in range(160):
  for z in range(148):
   if x<5 or x>=155 or z<5 or z>=140:b.put(x,2,z,'gray_concrete','site.road')
   elif x<9 or x>=151 or z<8 or z>=136:b.put(x,2,z,'smooth_stone','site.pavement')
 for x in range(10,150,7):box(x,143,x+3,144,2,3,'white_concrete','site.marking')
 path((50,88,55,141));path((9,46,151,50));path((9,90,151,94));path((7,8,10,136));path((150,8,153,136))
 for x in range(22,139):
  for z in range(48,91):
   r=((x+.5-80)/55)**2+((z+.5-70)/19)**2
   if .78<r<1.12:paths.add((x,z))
 path((25,68,136,72));path((101,48,105,92))
 for t in p['towers']:
  ex=t['x']+(11 if t['type']=='A' else 20);ez=t['z'] if t['type']=='A' else t['z']+24
  if t['type']=='A':path((ex-1,90,ex+3,ez+1))
  else:path((ex-1,ez,ex+3,50))
 for x,z in paths:b.put(x,2,z,'smooth_sandstone' if (x+z)%17 else 'cut_sandstone','site.path')

 for t in p['towers']:
  tid=t['id'];x,z,w,d,n=t['x'],t['z'],t['w'],t['d'],t['storeys'];roof=g+n*pitch
  own=tid+'.shell'
  box(x,z,x+w,z+d,2,3,'stone_bricks',own+'.foundation')
  for f in range(n+1):
   fy=g+f*pitch
   box(x,z,x+w,z+d,fy-1,fy,'oak_planks' if f<n else 'smooth_stone',own+'.floor')
   if f:box(x,z,x+w,z+d,fy-2,fy-1,'white_concrete',own+'.ceiling')
  for xx in range(w):
   for zz in range(d):
    if xx in [0,w-1] or zz in [0,d-1]:
     for yy in range(g,roof):
      belt=(yy-g)%pitch==4
      panel=xx<2 or xx>w-3 or (t['type']=='B' and 13<=xx<=23)
      mat='smooth_sandstone' if panel or belt else 'yellow_terracotta'
      b.put(x+xx,yy,z+zz,mat,own+'.facade')
  # Two related roof crowns; wide B has low tiled hips with a central service cap.
  for xx in range(-1,w+1):
   for zz in range(-1,d+1):
    inset=min(xx+1,w-xx,zz+1,d-zz);yy=roof+min(4,inset//2)
    b.put(x+xx,roof-1,z+zz,M('smooth_sandstone_slab',type='top'),own+'.cornice')
    b.put(x+xx,yy,z+zz,'red_terracotta' if inset%2 else 'bricks',own+'.roof')
  capx=x+(13 if t['type']=='A' else 17)
  box(capx,z+5,capx+4,z+9,roof+2,roof+6,'smooth_sandstone',own+'.lift_overrun')
  box(capx-1,z+4,capx+5,z+10,roof+6,roof+7,'red_terracotta',own+'.overrun_cap')
  # Stair core is hollow through slabs. Clear before constructing flights.
  cx=x+(1 if t['type']=='A' else 14);cz=z+(0 if t['type']=='A' else 1)
  box(cx+1,cz+1,cx+8,cz+6,g-1,roof-1,'air',tid+'.stairs.void')
  for xx in range(9):
   for zz in range(9):
    if xx in [0,8] or zz in [0,8]:box(cx+xx,cz+zz,cx+xx+1,cz+zz+1,g,roof-1,'smooth_sandstone',tid+'.stairs.wall')
  box(cx+4,cz+3,cx+5,cz+6,g-1,roof-1,'smooth_sandstone',tid+'.stairs.spine')
  for f in range(n):
   fy=g+f*pitch;fid=f'{tid}.F{f+1:02d}'
   box(cx+6,cz+8,cx+8,cz+9,fy,fy+3,'air',tid+'.stairs.entry')
   # Each flight rises 5 blocks: 3 northbound, 2 southbound, generous intermediate landing.
   if f<n-1:
    for v,h in [(5,0),(4,1),(3,2)]:
     for u in [1,2]:b.put(cx+u,fy+h,cz+v,M('smooth_quartz_stairs',facing='north'),tid+'.stairs.tread')
    box(cx+1,cz+1,cx+8,cz+3,fy+2,fy+3,'smooth_quartz',tid+'.stairs.landing')
    for v,h in [(3,3),(4,4)]:
     for u in [6,7]:b.put(cx+u,fy+h,cz+v,M('smooth_quartz_stairs',facing='south'),tid+'.stairs.tread')
    box(cx+6,cz+5,cx+8,cz+6,fy+4,fy+5,'smooth_quartz',tid+'.stairs.top_landing')
    trace=[[cx+1,fy,cz+6],[cx+1,fy+1,cz+5],[cx+1,fy+2,cz+4],[cx+1,fy+3,cz+3],[cx+1,fy+3,cz+2],[cx+2,fy+3,cz+2],[cx+3,fy+3,cz+2],[cx+4,fy+3,cz+2],[cx+5,fy+3,cz+2],[cx+6,fy+3,cz+2],[cx+6,fy+4,cz+3],[cx+6,fy+5,cz+4],[cx+6,fy+5,cz+5],[cx+6,fy+5,cz+6]]
    stairs.append({'id':fid+'.stair_to_next','from_floor':fy,'to_floor':fy+5,'trace':trace,'width':2})
   # Guard the open central edge; lower flight access at u1/2 remains open.
   for u in [3,4,5]:b.put(cx+u,fy,cz+6,'iron_bars',tid+'.stairs.guard')
   light(cx+6,fy+3,cz+7,'glowstone',fid+'.common.light')
  # Dedicated lift shaft, represented as a static enclosed cabin stack, never claimed functional.
  lx=x+(16 if t['type']=='A' else 15);lz=z+(2 if t['type']=='A' else 12)
  box(lx,lz,lx+4,lz+4,g,roof,'light_gray_concrete',tid+'.lift.shell')
  box(lx+1,lz+1,lx+3,lz+3,g,roof-2,'air',tid+'.lift.shaft')
  for f in range(n):
   fy=g+f*pitch
   for xx in [lx+1,lx+2]:
    for yy in [fy,fy+1]:b.put(xx,yy,lz+3,M('iron_trapdoor',open=True,facing='north'),tid+'.lift.static_door')
   # Common area floor material reads separately from apartments.
   if t['type']=='A':box(x+10,z+1,x+15,z+10,fy-1,fy,'smooth_stone',tid+'.lobby.floor')
   else:box(x+14,z+17,x+23,z+24,fy-1,fy,'smooth_stone',tid+'.lobby.floor')
  spec={'schema_version':'0.4','project_id':'millennium-'+tid,'route':'original','primary_use':'home','style':'modern','interior_level':'L2','identity_features':['起居与家庭用餐','两间卧室与收纳','厨房卫生间与独立入户'],'coordinates':{'unit':'block','up':'Y','north':'-Z'},'storeys_total':n,'authorized_scope':{'editable_regions':[[x-2,0,z-2,x+w+2,86,z+d+3]],'locked_component_ids':[]},'floor_levels':[],'rooms':[],'proposed_modules':[],'circulation_keepouts':[],'lighting':{'coverage_override':'selected_spaces','override_reason':'10/15层住宅；接续用户太亮反馈，按住户亮灯，公共交通有灯。'}}
  # Room layouts use the same data for partitions, doors, compiler modules and validation.
  def unit_template(uid,fy,typ,mirror=False):
   def q(u,v):return (x+(w-1-u if mirror else u),z+v)
   def rect(a):
    u,v,U,V=a
    return [x+(w-U if mirror else u),fy,z+v,x+(w-u if mirror else U),fy+3,z+V]
   def wall(a,door=None):
    bb=rect(a);b.box(bb[:3],bb[3:],'smooth_sandstone',uid+'.partition')
    if door:
     for u,v in door:
      xx,zz=q(u,v);box(xx,zz,xx+1,zz+1,fy,fy+2,'air',uid+'.doorway')
   if typ=='A':
    wall((1,10,22,11),[(11,10),(12,10)]);wall((10,11,11,24),[(10,13),(10,20),(10,21)]);wall((13,11,14,24),[(13,13),(13,21),(13,22)])
    wall((1,17,10,18));wall((14,17,22,18));wall((18,18,19,21),[(18,19)]);wall((19,20,22,21))
    rr=[('bed1','bedroom',(1,11,10,17),(9,13)),('bed2','bedroom',(14,11,22,17),(14,13)),('living','living',(1,18,10,24),(9,20)),('dining','dining',(14,18,18,24),(14,21)),('kitchen','kitchen',(19,21,22,24),(19,22)),('bath','bathroom',(19,18,22,20),(19,19))]
    layouts={'bed1':[('bed',(2,12,5,15)),('wardrobe',(2,15,5,16))],'bed2':[('bed',(16,12,19,15)),('wardrobe',(19,15,21,16))],'living':[('sofa',(2,19,6,20)),('coffee',(3,21,5,22)),('television',(7,21,8,23))],'dining':[('dining',(14,18,17,21))],'kitchen':[('kitchen',(20,21,22,24))],'bath':[('bath',(20,18,22,20))]}
    e=q(11,10);keep=[(11,11,13,24)]
   else:
    wall((13,1,14,24),[(13,20),(13,21)]);wall((10,1,11,24),[(10,4),(10,11),(10,16),(10,20),(10,21)]);wall((1,7,10,8));wall((1,14,10,15));wall((1,18,10,19));wall((6,15,7,18),[(6,16)])
    rr=[('bed1','bedroom',(1,1,10,7),(9,4)),('bed2','bedroom',(1,8,10,14),(9,11)),('kitchen','kitchen',(1,15,6,18),(5,16)),('bath','bathroom',(7,15,10,18),(9,16)),('living','living_dining',(1,19,10,24),(9,20))]
    layouts={'bed1':[('bed',(2,2,5,5)),('wardrobe',(6,2,9,3))],'bed2':[('bed',(2,9,5,12)),('wardrobe',(6,9,9,10))],'kitchen':[('kitchen',(1,15,3,18))],'bath':[('bath',(7,15,9,18))],'living':[('sofa',(2,20,6,21)),('coffee',(3,22,5,23)),('dining',(6,22,9,24))]}
    e=q(13,20);keep=[(11,1,13,24)]
   rec={'id':uid,'tower':tid,'floor':int((fy-g)/pitch)+1,'floor_y':fy,'entry':[e[0],fy,e[1]],'rooms':[],'lit':rnd(uid+'.occupancy')<.34}
   for a in keep:spec['circulation_keepouts'].append(rect(a))
   for name,fun,a,door in rr:
    rid=uid+'.'+name;bb=rect(a);dq=q(*door);r={'id':rid,'floor_id':f'{tid}.F{int((fy-g)/pitch)+1:02d}','function':fun,'bounds_xyz':bb,'entrances':[[dq[0],fy,dq[1]]],'color_intent':'warm' if fun not in ['kitchen','bathroom'] else 'neutral'}
    spec['rooms'].append(r);b.rooms.append(r);rec['rooms'].append(rid)
    # Finish floors per use, without altering floor height.
    box(bb[0],bb[2],bb[3],bb[5],fy-1,fy,'smooth_quartz' if fun in ['kitchen','bathroom'] else 'oak_planks',rid+'.floor')
    for index,(kind,a2) in enumerate(layouts[name]):
     mb=rect(a2);mb[4]=fy+(2 if kind in ['wardrobe','television','kitchen','bath'] else 1)
     spec['proposed_modules'].append({'component_id':rid+'.'+kind+str(index),'room_id':rid,'kind':kind,'bounds_xyz':mb,'use_faces':['east' if not mirror else 'west'],'variant':int(rnd(uid+'.fabric')*3)})
    if rec['lit'] and (fun in ['living','living_dining','kitchen','dining'] or rnd(rid+'.light')<.55):
     xx=(bb[0]+bb[3])//2;zz=(bb[2]+bb[5])//2;light(xx,fy+3,zz,'sea_lantern' if fun=='kitchen' else 'glowstone',rid+'.flush_light')
   units.append(rec)
  for f in range(n):
   fy=g+f*pitch;fid=f'{tid}.F{f+1:02d}';spec['floor_levels'].append({'id':fid,'floor_y':fy,'upper_floor_y':fy+5,'min_clear_height':3})
   floor_records.append({'tower':tid,'floor':f+1,'floor_y':fy,'ceiling_y':fy+3,'upper_floor_y':fy+5})
   if t['type']=='A':unit_template(fid+'.U1',fy,'A')
   else:
    unit_template(fid+'.U1',fy,'B');unit_template(fid+'.U2',fy,'B',True)
  plan=compile_handoff(spec);specs.append(spec);plans.append(plan)
  # Explicitly consume compiled modules into decorative furniture geometry.
  for mod in plan['modules']:
   a=mod['bounds_xyz'];xx,yy,zz,X,Y,Z=a;kind=mod['kind'];o=mod['component_id'];mat=['white_concrete','light_gray_concrete','cyan_stained_glass'][mod['variant']]
   if kind=='bed':
    box(xx,zz,X,Z,yy,yy+1,'white_concrete',o);box(xx,zz,X,zz+1,yy,yy+1,'smooth_quartz',o+'.pillow')
    box(xx,zz+1,X,Z,yy,yy+1,['blue_concrete','yellow_terracotta','pink_concrete'][mod['variant']],o+'.cover')
   elif kind=='wardrobe':box(xx,zz,X,Z,yy,Y,'dark_oak_planks',o)
   elif kind=='sofa':
    for u in range(xx,X):b.put(u,yy,zz,M('smooth_quartz_stairs',facing='north'),o)
   elif kind=='coffee':box(xx,zz,X,Z,yy,yy+1,M('dark_oak_slab',type='top'),o)
   elif kind=='television':
    box(xx,zz,X,Z,yy,yy+1,'dark_oak_planks',o+'.stand');box(xx,zz,X,Z,yy+1,yy+2,'black_concrete',o+'.screen')
   elif kind=='dining':
    box(xx+1,zz,min(X,xx+2),Z,yy,yy+1,M('oak_slab',type='top'),o+'.table')
    b.put(xx,yy,zz,M('oak_stairs',facing='west'),o+'.chair')
    if X-xx>2:b.put(X-1,yy,Z-1,M('oak_stairs',facing='east'),o+'.chair')
   elif kind=='kitchen':
    box(xx,zz,X,Z,yy,yy+1,'smooth_quartz',o+'.counter');b.put(xx,yy,zz,'gray_concrete',o+'.hob');b.put(X-1,yy,Z-1,M('iron_trapdoor',half='top'),o+'.sink')
    b.put(xx,yy+1,Z-1,'iron_block',o+'.appliance')
   elif kind=='bath':
    b.put(xx,yy,zz,M('smooth_quartz_stairs',facing='north'),o+'.toilet');b.put(X-1,yy,Z-1,'smooth_quartz',o+'.basin');b.put(xx,yy+1,Z-1,'glass_pane',o+'.screen')
   cells=[(a,b0,c) for a in range(xx,X) for b0 in range(yy,Y) for c in range(zz,Z) if b.s.owners.get((a,b0,c),'').startswith(o)]
   modules.append({**mod,'placed_cells':len(cells),'status':'consumed_case_geometry','functional_game_furniture':False})
  # Windows always cut actual wall openings. Grilles vary per household and window group.
  def window(fid,uid,normal,u0,y0,width,stylekey):
   frame=b.frame(x+u0 if normal in [(0,-1),(0,1)] else (x if normal==(-1,0) else x+w-1), z if normal==(0,-1) else z+d-1 if normal==(0,1) else z+u0, normal)
   # tangent-dependent positioning: all windows use centered local u coordinates.
   lo=-(width//2);hi=lo+width;v=rnd(uid+'.security');style='cage' if v<.29 else 'flush' if v<.48 else 'none'
   if rnd(stylekey+'.exception')<.18:style='none'
   pane=['glass_pane','light_blue_stained_glass_pane','gray_stained_glass_pane'][int(rnd(uid+'.glazing')*3)]
   frame.rect(lo,hi,y0+1,y0+3,0,1,pane,fid+'.window.glass')
   frame.rect(lo,hi,y0,y0+1,0,1,'smooth_sandstone',fid+'.window.sill')
   if style!='none':
    dep=1
    frame.rect(lo,hi,y0+1,y0+3,dep,dep+1,'iron_bars',fid+'.window.'+style)
    if style=='cage':
     for u in [lo,hi-1]:frame.rect(u,u+1,y0+1,y0+3,0,2,'iron_bars',fid+'.window.cage_side')
     frame.rect(lo,hi,y0,y0+1,1,2,M('iron_trapdoor',half='top'),fid+'.window.cage_base')
   if rnd(stylekey+'.ac')<.58:
    frame.put(lo-1,y0+1,1,'iron_block',fid+'.ac');frame.put(lo-1,y0+1,2,M('iron_trapdoor',open=True,facing='north'),'facade.ac_grille')
   b.windows.append({'id':stylekey,'unit_id':uid,'floor_y':y0,'normal':normal,'center':list(frame.xyz(0,y0+1,0)),'width':width,'security':style,'glass':pane})
  for f in range(n):
   fy=g+f*pitch;fid=f'{tid}.F{f+1:02d}'
   if t['type']=='A':
    for side in [(-1,0),(1,0)]:
     for u in [13,21]:window(fid,fid+'.U1',side,u,fy,3,fid+str(side)+str(u))
    for u in [5,18]:window(fid,fid+'.U1',(0,1),u,fy,4,fid+'.south'+str(u))
    window(fid,fid+'.U1',(0,-1),21,fy,2,fid+'.north')
    balconies=[(2,8,fid+'.U1')]
   else:
    for side,uid in [((-1,0),fid+'.U1'),((1,0),fid+'.U2')]:
     for u in [4,11,21]:window(fid,uid,side,u,fy,3,fid+str(side)+str(u))
    for u,uid in [(5,fid+'.U1'),(31,fid+'.U2')]:
     window(fid,uid,(0,-1),u,fy,4,fid+'.north'+str(u));window(fid,uid,(0,1),u,fy,4,fid+'.south'+str(u))
    balconies=[(2,8,fid+'.U1'),(28,34,fid+'.U2')]
   for a,A,uid in balconies:
    enclosed=rnd(uid+'.balcony')<.4
    box(x+a,z+d,x+A,z+d+2,fy-1,fy,'smooth_sandstone',uid+'.balcony.floor')
    for xx in range(x+a,x+A):
     b.put(xx,fy,z+d+1,'iron_bars' if not enclosed else 'smooth_sandstone',uid+'.balcony.rail')
     if enclosed:
      for yy in [fy+1,fy+2]:b.put(xx,yy,z+d+1,'glass_pane',uid+'.balcony.enclosed')
    for xx in [x+a,x+A-1]:
     b.put(xx,fy,z+d,'iron_bars',uid+'.balcony.side')
     if enclosed:
      for yy in [fy+1,fy+2]:b.put(xx,yy,z+d,'glass_pane',uid+'.balcony.enclosed')
    # One open access beside living furniture, with complete floor underneath.
    box(x+a+2,z+d-1,x+a+4,z+d,fy,fy+2,'air',uid+'.balcony.door')
    if enclosed:box(x+a,z+d,x+A,z+d+2,fy+3,fy+4,M('smooth_sandstone_slab',type='top'),uid+'.balcony.canopy')
    if rnd(uid+'.pots')<.55:
     b.put(x+a,fy,z+d,'red_terracotta',uid+'.pot');b.put(x+a,fy+1,z+d,'azalea_leaves',uid+'.pot.plant')
  # Ground entry faces the shared garden; a separate common lobby serves the ground-floor homes.
  ex=x+(11 if t['type']=='A' else 20);ez=z if t['type']=='A' else z+d-1;sgn=-1 if t['type']=='A' else 1
  box(ex,ez,ex+2,ez+1,g,g+3,'air',tid+'.entry')
  for xx in range(ex-2,ex+4):
   for dd in range(1,4):b.put(xx,g+4,ez+sgn*dd,'gray_stained_glass',tid+'.entry.canopy')
  for xx in [ex-2,ex+3]:
   for yy in range(g,g+4):b.put(xx,yy,ez+sgn*2,'iron_bars',tid+'.entry.post')
  # Lobby/mail/rest stays away from two-wide access routes.
  if t['type']=='A':
   box(x+20,z+7,x+22,z+8,g,g+1,'oak_planks',tid+'.mail');b.put(x+20,g,z+9,M('oak_stairs',facing='south'),tid+'.common.seat')
  else:box(x+15,z+21,x+18,z+22,g,g+1,'oak_planks',tid+'.mail')
  entries.append({'id':tid,'entry':[ex,g,ez],'width':2,'direction':sgn,'core_landing':[cx+6,g,cz+7]})
  facades.append({'tower':tid,'main_material':'yellow_terracotta','trim':'smooth_sandstone','roof':'red_terracotta / bricks','grille_assignment':'stable per household plus occasional open window exception'})

 # Garden: one connected pedestrian network, distinct stays, planted margins and one modest pond.
 def safe(x,z,r=1):return all((xx,zz) not in paths for xx in range(x-r,x+r+1) for zz in range(z-r,z+r+1)) and not any(t['x']-3<=x<=t['x']+t['w']+3 and t['z']-3<=z<=t['z']+t['d']+3 for t in p['towers'])
 def tree(x,z,h,r):
  if not safe(x,z,1):return
  b.put(x,2,z,'dirt','garden.root');box(x,z,x+1,z+1,3,3+h,'oak_log','garden.trunk')
  for xx in range(x-r,x+r+1):
   for zz in range(z-r,z+r+1):
    for yy in range(3+h-3,3+h+3):
     if ((xx-x)/r)**2+((zz-z)/r)**2+((yy-3-h)/2.6)**2<1.12:b.put(xx,yy,zz,'oak_leaves' if (x+z)%2 else 'azalea_leaves','garden.canopy',empty=True)
  trees.append({'root':[x,2,z],'height':h,'radius':r})
 for xx,zz,h,r in [(18,58,9,5),(20,82,10,5),(41,56,9,4),(66,56,11,5),(92,55,9,4),(120,55,10,5),(142,61,10,5),(143,83,8,4),(40,83,10,4),(66,83,9,4),(89,83,11,5),(121,84,9,4),(14,132,10,4),(43,128,9,4),(89,134,9,4),(145,132,10,4)]:tree(xx,zz,h,r)
 # Continuous low planting outside path envelope; never random isolated cubes in circulation.
 for xx in range(15,147):
  for zz in range(51,89):
   ellipse=((xx-80)/58)**2+((zz-70)/22)**2
   if .93<ellipse<1.08 and safe(xx,zz,1):
    b.put(xx,2,zz,'moss_block','garden.bed');b.put(xx,3,zz,'azalea_leaves','garden.shrub')
    if (xx+zz)%13==0:b.put(xx,4,zz,'poppy','garden.flowers')
 pond={(xx,zz) for xx in range(43,61) for zz in range(58,68) if ((xx-52)/8)**2+((zz-63)/4)**2<1}
 for xx,zz in sorted(pond):
  b.put(xx,1,zz,'stone_bricks','garden.pond.basin');b.put(xx,2,zz,'water','garden.pond.water')
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   if (xx+dx,zz+dz) not in pond:b.put(xx+dx,2,zz+dz,'stone_bricks','garden.pond.bank')
 # Pergola in east garden, attached to the central route; supported beams, benches inside.
 box(110,73,128,81,2,3,'smooth_stone','garden.pergola.paving')
 for xx in [111,126]:
  for zz in [74,79]:box(xx,zz,xx+1,zz+1,3,7,'dark_oak_planks','garden.pergola.post')
 for zz in [74,79]:box(110,zz,128,zz+1,7,8,'dark_oak_planks','garden.pergola.beam')
 for xx in range(110,128,2):box(xx,73,xx+1,81,8,9,M('oak_slab'),'garden.pergola.rafter')
 for xx in range(113,125):b.put(xx,3,78,M('oak_stairs',facing='south'),'garden.pergola.bench')
 path((115,70,120,74))
 # Small exercise/play court at west edge, lawn remains dominant.
 box(29,74,39,81,2,3,'yellow_terracotta','garden.play.surface')
 for xx in [30,36]:
  box(xx,75,xx+1,76,3,7,'iron_bars','garden.play.frame')
 box(30,75,37,76,7,8,'iron_bars','garden.play.beam')
 for xx in [32,34]:
  box(xx,75,xx+1,76,4,7,'chain','garden.play.chain');b.put(xx,3,75,M('oak_slab'),'garden.play.seat')
 for xx,zz in [(66,65),(85,74),(92,64),(41,77)]:
  if safe(xx,zz):
   for u in range(4):b.put(xx+u,3,zz,M('oak_stairs',facing='north'),'garden.bench')
 for xx,zz in [(26,52),(52,52),(78,52),(106,52),(133,52),(25,87),(52,87),(79,87),(107,87),(134,87),(48,134),(56,134)]:
  if (xx,zz) not in paths:
   b.put(xx,3,zz,'stone_bricks','garden.lamp.base');light(xx,4,zz,'end_rod','garden.lamp.rod')
 # Perimeter fence, with the south gate open and canopy supported.
 for xx in range(9,151):
  for zz in [8,136]:
   if (zz==136 and 48<=xx<=57) or (xx,zz) in paths:continue
   b.put(xx,3,zz,'iron_bars','site.fence')
 for zz in range(9,136):
  for xx in [9,150]:
   if 45<=zz<=50 or 89<=zz<=94:continue
   if (xx,zz) not in paths:b.put(xx,3,zz,'iron_bars','site.fence')
 for xx in [48,57]:box(xx,135,xx+1,138,3,8,'smooth_sandstone','site.gate.pier')
 box(47,134,59,139,8,9,'red_terracotta','site.gate.roof')
 for xx,zz in paths:b.put(xx,2,zz,'smooth_sandstone','site.path')
 out=save_run(CASE,run,p,b,Path(__file__),{'design_route':'original','units':len(units),'towers':6,'residential_floor_counts':[10,10,10,15,15,15],'module_count':len(modules),'lamp_count':len(lamps),'source_references_sha256':sha(CASE/'input/provenance.json')})
 for file,obj in [('design_handoffs.json',specs),('resolved_plans.json',plans),('units.json',units),('floor_levels.json',floor_records),('stairs.json',stairs),('entries.json',entries),('module_consumption.json',modules),('lamps.json',lamps),('trees.json',trees),('paths.json',{'floor_y':3,'cells_xz':sorted(paths)}),('facade_rules.json',facades)]:dump(out/file,obj)
 dump(out/'source_bundle.json',{'files':{str(v.relative_to(CASE)):sha(v) for v in sorted((CASE/'input').glob('*')) if v.is_file()},'engine_core_changed':False})

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'input/params.json');a=ap.parse_args();build(json.loads(a.params.read_text()),a.run)
