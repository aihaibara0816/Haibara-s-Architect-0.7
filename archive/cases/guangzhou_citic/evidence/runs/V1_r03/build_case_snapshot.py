"""CITIC Plaza: evidence-constrained case adapter, HAF 0.4.
OSM plan geometry + reviewed photos; elevations below tip remain estimates.
The authored module consumer is local to this case, not a universal interior AI.
"""
from pathlib import Path
import sys,json,math,argparse,hashlib
from collections import Counter
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump
from hafusion.design_handoff import compile_handoff
from detail_lab import states
M=states.make
D=[(1,0),(-1,0),(0,1),(0,-1)]
def inside(x,z,poly):
 c=False;j=len(poly)-1
 for i,(ax,az) in enumerate(poly):
  bx,bz=poly[j]
  if (az>z)!=(bz>z) and x<(bx-ax)*(z-az)/(bz-az)+ax:c=not c
  j=i
 return c
def raster(poly):return {(x,z) for x in range(92) for z in range(98) if inside(x+.5,z+.5,poly)}
def edge(mask):return {q for q in mask if any((q[0]+dx,q[1]+dz) not in mask for dx,dz in D)}
def erode(mask,n=1):
 for _ in range(n):mask=mask-edge(mask)
 return mask
def rand(key):return int(hashlib.sha256(key.encode()).hexdigest()[:12],16)/16**12

def build(p,run):
 b=Builder(p['size_xyz'],p['seed']);grade=p['grade_y'];s=p['scale_blocks_per_m'];ms={k:raster(v['polygon']) for k,v in p['map_polygons'].items()}
 spec=json.loads((CASE/'input/handoff.json').read_text());plan=compile_handoff(spec)
 lamp_records=[];plant_records=[];module_records=[];path_rects=[];deferred_room_lamps=[]
 def surf(mask,y,mat,own):
  for x,z in sorted(mask):b.put(x,y,z,mat,own)
 def box(rect,y0,y1,mat,own):b.box((rect[0],y0,rect[1]),(rect[2],y1,rect[3]),mat,own)
 def cube(q,mat,own):b.put(*q,mat,own)
 def light(x,y,z,kind,own):
  b.put(x,y,z,kind,own);lamp_records.append({'xyz':[x,y,z],'material':kind,'owner':own})
 def tree(x,z,h=7,r=3,palm=False):
  b.put(x,2,z,'dirt','site.tree.soil');b.put(x,3,z,'moss_block','site.tree.root')
  for y in range(4,4+h):b.put(x,y,z,'oak_log','site.tree.trunk')
  if palm:
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
    for k in range(1,4):b.put(x+dx*k,3+h-(k//3),z+dz*k,'oak_leaves','site.tree.palm_frond')
  else:
   for dx in range(-r,r+1):
    for dz in range(-r,r+1):
     for dy in range(-2,3):
      if (dx/r)**2+(dz/r)**2+(dy/2.3)**2<1.2:b.put(x+dx,3+h+dy,z+dz,'oak_leaves','site.tree.canopy')
  plant_records.append({'root':[x,3,z],'type':'palm silhouette' if palm else 'shade tree','source':'photo motif; exact location designed'})
 # A bounded, almost flat immediate site. Road strips are context, not full city.
 box((2,2,90,96),0,3,'stone_bricks','site.base')
 for x in range(2,90):
  for z in range(2,96):
   road=x<8 or x>=84 or z<6 or z>=90
   mat='gray_concrete' if road else ('polished_andesite' if x%9==0 or z%9==0 else 'smooth_stone')
   b.put(x,2,z,mat,'site.road' if road else 'site.plaza.paving')
 for x in range(12,83,5):
  b.put(x,2,93,'white_concrete','site.road.marking')
 for x in range(41,49):
  for z in [90,92,94]:b.put(x,2,z,'white_concrete','site.road.crossing')
 # Protected 4-block routes and generous front apron.
 path_rects=[{'id':'front_axis','bounds':[42,77,48,90],'floor_y':3},
             {'id':'west_route','bounds':[9,7,12,90],'floor_y':3},
             {'id':'east_route','bounds':[80,7,84,90],'floor_y':3},
             {'id':'north_approach','bounds':[42,6,48,13],'floor_y':3}]
 for pr in path_rects:box(pr['bounds'],2,3,'smooth_quartz','site.path.'+pr['id'])
 # Front fountains: water motif is observed; exact outline is a designed completion.
 for x0 in [27,55]:
  z0=80;box((x0,z0,x0+9,z0+6),2,3,'polished_andesite','site.pool.basin')
  for x in range(x0,x0+9):
   for z in range(z0,z0+6):
    if x in [x0,x0+8] or z in [z0,z0+5]:b.put(x,3,z,M('smooth_quartz_slab'),'site.pool.edge')
    else:b.put(x,2,z,'water','site.pool.water')
  for x in [x0+2,x0+6]:light(x,1,z0+2,'sea_lantern','site.pool.light')
 # Lateral shaded stays, palms and planted edges; centre axis remains open.
 for x0 in [16,68]:
  # Continuous planted margin joins the two stays, with irregular inner edge.
  for x in range(x0,x0+7):
   for z in range(58,82):
    if x<x0+5 or (z-58)%9<5:b.put(x,2,z,'moss_block','site.garden.continuous_bed')
  for z in [61,65,70,79]:
   for x in [x0+1,x0+2]:b.put(x,3,z,'azalea_leaves','site.garden.shrub_layer')
  for z0 in [58,74]:
   box((x0,z0,x0+7,z0+8),2,3,'moss_block','site.garden.bed')
   for x in range(x0,x0+7):b.put(x,3,z0,M('smooth_quartz_slab'),'site.garden.edge')
   tree(x0+3,z0+4,h=8 if z0==74 else 7,r=3,palm=z0==58)
   for x in range(x0,x0+6):b.put(x,3,z0+9,M('dark_oak_stairs',facing='north'),'site.garden.bench')
 for x,z in [(18,86),(72,86),(22,8),(69,8),(8,43),(85,43)]:tree(x,z,7,3)
 for x,z in [(30,70),(60,70),(26,57),(65,57)]:tree(x,z,8,3,True)
 for x,z in [(15,88),(32,88),(57,88),(76,88),(13,50),(78,50),(30,9),(59,9)]:
  b.put(x,3,z,M('polished_andesite_slab'),'site.light.base');light(x,4,z,'end_rod','site.light.bollard')
 # Commercial podium derived from map outline. Roof cuts do not use tower shadows.
 pod=ms['157418073'];pe=edge(pod);annex=ms['157418082']|ms['157418084'];pod_top=14
 for fy in [3,8,14]:surf(pod,fy,'smooth_stone','podium.floor')
 for x,z in pe:
  for y in range(4,pod_top):
   mat='light_blue_stained_glass' if y not in [8,12,13] and (x+z)%7>0 else 'light_gray_concrete'
   b.put(x,y,z,mat,'podium.facade')
  b.put(x,pod_top,z,M('smooth_quartz_slab',type='top'),'podium.coping')
  # Thin projecting glass canopy and metal supports on observed curved facade.
  if z<42:
   for dx,dz in D:
    if (x+dx,z+dz) not in pod:
     b.put(x+dx,6,z+dz,'light_blue_stained_glass','podium.canopy')
     if (x+z)%4==0:b.put(x+dx,5,z+dz,M('iron_trapdoor',half='top'),'podium.canopy.rib')
 # North doorway and internal shop-front corridor (not a real tenant map).
 b.box((42,4,12),(48,7,18),'minecraft:air','podium.entry.clear')
 for x,z in sorted(erode(pod,3)):
  if x%6==0 and z%6==0 and (x,z) not in annex:light(x,7,z,'sea_lantern','podium.flush_light')
 for x,z in [(35,32),(53,32),(35,41),(53,41)]:
  b.box((x,4,z),(x+1,13,z+1),'light_gray_concrete','podium.visual_column')
 # Stepped L-shaped apartment wings, approximate height; no invented inhabited layout.
 for wid,ident in [('157418082','west'),('157418084','east')]:
  mask=ms[wid];ee=edge(mask);top=66
  for yy in [3,14,top]:surf(mask,yy,'light_gray_concrete','annex.'+ident+'.floor')
  for x,z in ee:
   for y in range(4,top):
    # Outer projecting blade is held on piers, exposing the photographed undercroft.
    opening=y<19 and ((ident=='west' and x<22 and z<24) or (ident=='east' and x>69 and z<24)) and z>15
    if opening:continue
    mat='light_gray_concrete' if y%2==0 or z<15 else 'cyan_stained_glass'
    b.put(x,y,z,mat,'annex.'+ident+'.facade')
   for dx,dz in D:
    if (x+dx,z+dz) not in mask:
     for y in range(20,top,2):b.put(x+dx,y,z+dz,M('smooth_stone_slab',type='top'),'annex.'+ident+'.ledge')
  for x,z in erode(mask,2):
   if any((x+dx*2,z+dz*2) not in mask for dx,dz in D):
    for y in range(15,top):b.put(x,y,z,'gray_concrete','annex.'+ident+'.backing')
   if x%3==0 and z%3==0:
    for y in range(17,top,4):
     if rand(f'annex:{wid}:{x}:{z}:{y}')<.35:light(x,y,z,'glowstone','annex.'+ident+'.light')
  surf(mask,top+1,M('smooth_quartz_slab'),'annex.'+ident+'.cap')
 # Main tower from OSM circle-on-square plan, cross-checked against DLN photos.
 footprint=ms['926228208'];wings=ms['1548063152']|ms['1548063153'];octagon=ms['1548063158'];cylinder=ms['1548063159']
 mainmask=wings|octagon;demo=p['synthetic_levels'];intervals=[(f['floor_y']-1,f['upper_floor_y']) for f in demo]
 def isdemo(y):return any(a<=y<c for a,c in intervals)
 # Plinth and high portal, four piers with shallow silver flutes.
 surf(footprint,3,'smooth_quartz','tower.lobby.floor')
 for x,z in footprint:
  if (x+z)%7==0:b.put(x,3,z,'polished_deepslate','tower.lobby.floor_inlay')
 for rect in [(33,53,37,57),(52,53,56,57),(33,71,37,76),(52,71,56,76)]:
  box(rect,4,12,'black_concrete','tower.portal.pier')
  for x in range(rect[0],rect[2],2):
   for y in range(4,12):b.put(x,y,rect[3]-1,M('iron_trapdoor',open=True,facing='south'),'tower.portal.flute')
 for yy in range(12,16):surf(footprint if yy>=14 else edge(footprint),yy,'black_concrete','tower.portal.head')
 # Round entrance hall with recessed door openings and an elliptical canopy.
 lobby={(x,z) for x in range(34,56) for z in range(54,75) if (x+.5-44.6)**2+(z+.5-64.2)**2<10.0**2}
 le=edge(lobby)
 for x,z in le:
  for y in range(4,12):
   doorway=42<=x<47 and (z>=73 or z<=55) and y<8
   if not doorway:b.put(x,y,z,'cyan_stained_glass' if y not in [7,10] else 'light_blue_stained_glass','tower.lobby.glazing')
 for x in range(38,52):
  for z in range(72,79):
   if ((x+.5-45)/7)**2+((z+.5-74)/5)**2<=1:
    b.put(x,8,z,M('smooth_quartz_slab',type='top'),'tower.entry.canopy')
    if x%2==0:b.put(x,7,z,M('iron_trapdoor',half='top'),'tower.entry.canopy.rib')
 for x in range(42,48):b.put(x,3,76,M('smooth_quartz_stairs',facing='north'),'tower.entry.step')
 # Connected glass link to podium, with doors left open at both ends.
 box((41,47,49,54),3,4,'smooth_stone','tower.podium_link.floor')
 for x in [41,48]:box((x,47,x+1,54),4,8,'glass_pane','tower.podium_link.side')
 box((41,47,49,54),8,9,M('smooth_stone_slab'),'tower.podium_link.roof')
 # Slender straight body, no unjustified taper. Skin groups are stable by elevation/bay.
 masks={y:(mainmask if y<142 else wings|cylinder if y<148 else wings) for y in range(16,154)}
 for y,mask in masks.items():
  for x,z in edge(mask):
   middle=(41<=x<=48 and (z<57 or z>71)) or (60<=z<=68 and (x<38 or x>51))
   mat='cyan_stained_glass' if middle else 'light_blue_stained_glass'
   if middle and (y//7)%5==2:mat='blue_stained_glass'
   if y in [54,55,89,90,123,124] and middle:mat='gray_stained_glass'
   b.put(x,y,z,mat,'tower.facade.glass.middle' if middle else 'tower.facade.glass.wings')
   for dx,dz in D:
    if (x+dx,z+dz) not in mask:
     u=x if dz else z
     # Thin bars only at zone boundaries; shallow rail avoids full-cube fins.
     if u%3==0 or u in [33,55,53,75]:b.put(x+dx,y,z+dz,'iron_bars','tower.facade.vertical_rail')
     if y%2==0:b.put(x+dx,y,z+dz,M('iron_trapdoor',half='top'),'tower.facade.horizontal_rail')
  # Two-cell-tall facade rhythm is a compressed visual abstraction, not 80 usable floors.
  if not isdemo(y) and y<142:
   inn=erode(mask)
   if y%2==0:surf(inn,y,'gray_concrete','tower.L1.slab')
   else:
    back=edge(erode(mask,4));surf(back,y,'gray_concrete','tower.L1.backing')
    for x,z in edge(erode(mask,2)):
     if (x+z)%4==0:
      rid=f'L1.y{y}.x{x}.z{z}';u=rand(str(p['seed'])+rid);kind='dark' if u<.5 else 'glowstone' if u<.75 else 'sea_lantern'
      if y in [53,55,89,91,123,125]:kind='dark'
      if kind!='dark':deferred_room_lamps.append((x,y+1,z,kind,'tower.L1.room_light.'+rid))
      b.rooms.append({'id':rid,'kind':'L1_window_back','lighting':kind,'walkable':False,'evidence':'synthetic visual occupancy; no real tenant assignment'})
 # Close each real stepped roof; leave top notch as air above the lower circular drum.
 for y in [141,147,153]:
  nextmask=masks.get(y+1,set());surf(masks[y]-nextmask,y,'light_gray_concrete','tower.crown.roof')
 for y in [149,151]:
  for x in range(42,47):b.put(x,y,64,'iron_bars','tower.crown.cross_rods')
 # 182-block tip height above grade, both spires included. Small bases; thin upper rods.
 for x in [36,52]:
  b.box((x,148,64),(x+1,164,65),'white_concrete','tower.spires.base')
  for y in range(164,182):b.put(x,y,64,'iron_bars','tower.spires.shaft')
  for y in range(182,185):light(x,y,64,'end_rod','tower.spires.tip')
 # Legible 5x7 / 7x7 block-sign, separate from the tower body. No oversized parapet text.
 box((37,63,52,65),157,166,'black_concrete','tower.crown.sign.panel')
 glyphs=[['00100','11111','10101','10101','11111','00100','00100','00100'],['0100100','1001111','1000110','1001111','1000000','1001111','1001001','1001111']]
 for gx,g in zip([38,44],glyphs):
  for row,line in enumerate(g):
   for col,c in enumerate(line):
    if c=='1':
     for z in [62,65]:light(gx+col,164-row,z,'glowstone','tower.crown.sign.glyph')
 for x in range(37,53):
  for y in [156,166]:b.put(x,y,64,'iron_bars','tower.crown.sign.frame')
 # Core and authored demonstration floors. Exact tenant partitions are unavailable.
 for f in demo:
  fid=f['id'];y=f['floor_y'];up=f['upper_floor_y'];mask=footprint if fid=='lobby' else erode(mainmask)
  # Clear only interiors; approved external skin remains outside this region.
  clear=erode(lobby) if fid=='lobby' else erode(mainmask)
  for xx,zz in clear:
   for yy in range(y,up-2):b.put(xx,yy,zz,'minecraft:air','interior.'+fid+'.clear')
  surf(mask,y-1,'smooth_quartz' if fid=='lobby' else 'light_gray_concrete','interior.'+fid+'.floor')
  surf(mask,up-2,'white_concrete','interior.'+fid+'.ceiling')
  surf(mask,up-1,'smooth_stone','interior.'+fid+'.upper_floor')
  # Static core: lift lobby is represented, shafts do not claim working transport.
  for xx in range(41,49):
   for zz in range(59,69):
    if xx in [41,48] or zz in [59,68]:
     for yy in range(y,up-2):b.put(xx,yy,zz,'light_gray_concrete','interior.'+fid+'.core')
  for zz in [59,68]:
   for xx in [43,44,46]:
    for yy in range(y,y+3):b.put(xx,yy,zz,'iron_block' if yy<y+2 else 'black_concrete','interior.'+fid+'.lift_panel')
  # Four visual columns organize work/meeting/rest; they meet floor and ceiling.
  for xx,zz in [(36,56),(36,72),(53,56),(53,72)]:
   if (xx,zz) in mask:
    for yy in range(y,up-2):b.put(xx,yy,zz,'polished_andesite','interior.'+fid+'.visual_column')
  # Fixed, fully flush ceiling fixtures. Every demo zone gets lighting; highrise L1 differs.
  for xx in range(36,55,4):
   for zz in range(56,75,4):
    if (xx,zz) in mask and not(41<=xx<49 and 59<=zz<69):light(xx,up-2,zz,'glowstone' if fid in ['lobby','lounge'] or xx>49 and zz>64 else 'sea_lantern','interior.'+fid+'.flush_light')
 # Consume actual resolved module table, not an unconsumed JSON attachment.
 for m in plan['modules']:
  x0,y,z0,x1,_,z1=m['bounds_xyz'];own='module.'+m['component_id'];kind=m['kind'];before=len(b.s.blocks)
  if kind=='desk_group':
   for zz in [z0,z0+2]:
    for xx in range(x0,x1):
     b.put(xx,y,zz,M('oak_slab',type='top'),own+'.desk')
     if xx==x0+1:b.put(xx,y+1,zz,M('black_stained_glass_pane'),own+'.monitor')
    b.put(x0+1,y,zz+1,M('dark_oak_stairs',facing='north'),own+'.chair')
  elif kind=='meeting':
   box((x0,z0+1,x1,z0+3),y,y+1,M('dark_oak_slab',type='top'),own+'.table')
   for zz,facing in [(z0,'south'),(z0+3,'north')]:
    for xx in range(x0,x1):b.put(xx,y,zz,M('oak_stairs',facing=facing),own+'.chair')
   for zz in range(z0,z1):b.put(x1-1,y+2,zz,'glass_pane',own+'.partition')
  elif kind=='lounge':
   for xx in range(x0,x1):b.put(xx,y,z0,M('quartz_stairs',facing='south'),own+'.sofa')
   b.put(x0+1,y,z0+2,M('dark_oak_slab'),own+'.coffee_table')
   b.put(x0,y,z1-1,'moss_block',own+'.plant_base');b.put(x0,y+1,z1-1,'azalea_leaves',own+'.plant')
  elif kind=='pantry':
   box((x0,z0,x1,z0+1),y,y+1,'smooth_quartz',own+'.counter')
   b.put(x0,y+1,z0,'black_concrete',own+'.coffee_machine')
   for xx in range(x0,x1):b.put(xx,y,z0+3,M('oak_stairs',facing='north'),own+'.seat')
  elif kind=='reception':
   box((x0,z0,x1,z1),y,y+1,'dark_oak_planks',own+'.counter')
   b.put(x0+1,y+1,z0,'black_stained_glass_pane',own+'.screen')
  else:raise ValueError('No geometry consumer for '+kind)
  module_records.append({**m,'consumer':'guangzhou_citic.build_case:authored_module','geometry_status':'generated','net_blocks_added':len(b.s.blocks)-before})
 # Apply window-back lamps after slab construction; otherwise a later slab erases them.
 for x,y,z,kind,own in deferred_room_lamps:
  if not isdemo(y) and y<142:light(x,y,z,kind,own)
 # Door/approach cleanup comes last and is limited to the explicit portal contract.
 b.box((42,4,73),(48,7,77),'minecraft:air','tower.entry.clear')
 b.box((42,4,52),(48,7,57),'minecraft:air','tower.rear_entry.clear')
 b.box((42,4,12),(48,7,18),'minecraft:air','podium.entry.clear')
 out=save_run(CASE,run,p,b,Path(__file__),{'height_blocks_above_grade':182,'fidelity':'evidence-constrained exterior, designed interiors/site','demo_levels':len(demo),'resolved_plan_sha256':plan['source_sha256'],'source_reference':'input/evidence.json'})
 dump(out/'resolved_plan.json',plan);dump(out/'module_consumption.json',module_records);dump(out/'lamps.json',lamp_records);dump(out/'plants.json',plant_records);dump(out/'paths.json',path_rects)
 dump(out/'component_stats.json',dict(Counter(o.split('.')[0] for o in b.s.owners.values())))
 return out

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'params.json');a=ap.parse_args()
 if Path(a.run).name!=a.run:ap.error('simple immutable run name required')
 build(json.loads(a.params.read_text()),a.run)
