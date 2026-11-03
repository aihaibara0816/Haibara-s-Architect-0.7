"""R13: connected podium, aligned utility forecourts, clearance-led footbridges."""
group('podium','22 · 研发塔楼与实验培训翼共享裙楼')
# Connect the existing tower (X64..104) and laboratory/training wing (X120..178).
# All three lower floor datums stay at Y7/13/19; the tower above remains intact.
box(104,4,176,120,7,216,'light_gray_concrete')
box(104,7,176,120,25,216,'white_concrete');air(104,7,177,120,24,215)
podium_routes=[]
for fy in [7,13,19]:
 box(104,fy-1,177,120,fy,215,'smooth_stone')
 for z in [176,215]:
  box(105,fy+1,z,119,fy+4,z+1,'light_blue_stained_glass_pane')
  box(104,fy+4,z,120,fy+5,z+1,'light_gray_concrete')
 for z in [181,190,208]:box(108,fy+4,z,116,fy+5,z+1,'sea_lantern')
 # A full-width route crosses both former exterior walls, clear of existing stairs.
 box(94,fy-1,198,133,fy,202,'smooth_stone')
 air(94,fy,198,133,fy+4,202)
 for x in range(94,133):
  for z in range(198,202):podium_routes.append([x,fy,z])
 # Small shared break-out zones, away from the circulation strip.
 bench(108,fy,184,7);box(117,fy,180,119,fy+2,183,'bookshelf')
 rooms.append({'id':'podium_F'+str((fy-7)//6+1),'floor_y':fy,'bounds':[104,fy,177,120,fy+5,215],'use':'共享大厅 / 实验培训交流与通廊','clear_corridor':[94,198,133,202]})
box(104,24,175,120,26,217,'white_concrete')
# Continuous three-storey cornice and ground-floor entrance canopy unify the base.
for z in [173,217]:
 box(63,24,z,179,26,z+1,'white_concrete')
 box(64,23,z,178,24,z+1,'gray_concrete')
box(104,26,176,120,27,177,'gray_concrete');box(104,26,215,120,27,216,'gray_concrete')
box(74,11,216,178,12,220,'gray_concrete')
for x in [96,107,118,153,176]:box(x,7,218,x+1,11,219,'light_gray_concrete')
for x in range(77,176,8):box(x,11,218,x+3,12,219,'sea_lantern')
air(109,7,215,116,11,216)
# Remove only the two small entry trees that occupied the new shared entrance seam.
for p,st in list(sc.blocks.items()):
 x,y,z=p
 if sc.owners.get(p)=='entry' and 108<=x<=116 and ((168<=z<=175) or (218<=z<=224)):
  sc.set(p,'minecraft:air','entry')
group('site',components['site']['name'])
box(104,6,168,120,7,176,'light_gray_concrete');box(104,6,216,120,7,226,'smooth_stone')
# Northern utilities share one pad frontage Z8, with a single pedestrian service walk.
# Old access spurs are replaced by short, consistently oriented entrances.
for cid,a,b in [('substation',51,60),('waterworks',182,190),('airplant',268,277)]:
 group(cid,components[cid]['name'])
 air(a,7,8,b,10,9);box(a,4,6,b,7,8,'smooth_stone')
group('site',components['site']['name'])
box(24,4,6,282,7,8,'smooth_stone')

# Three protected pedestrian crossings. Deck underside Y18, rail base Y7.
# Stairs are outside the outer running envelopes, never between two close tracks.
group('bridges','14 · 三处跨线廊桥与员工连廊')
bridge_records=[]
for ident,bx,z0,z1,supports in [
 ('west',110,60,148,[62,118,146]),
 ('central',198,38,148,[40,88,146]),
 ('east',288,8,148,[10,62,88,146])]:
 box(bx,18,z0,bx+6,19,z1,'smooth_stone')
 box(bx,23,z0,bx+6,24,z1,'white_concrete')
 for xx in [bx,bx+5]:
  box(xx,19,z0,xx+1,20,z1,'gray_concrete')
  box(xx,20,z0,xx+1,23,z1,'light_blue_stained_glass_pane')
  for zz in range(z0+5,z1-3,10):box(xx,19,zz,xx+1,23,zz+1,'white_concrete')
 for zz in range(z0+5,z1-3,10):box(bx+2,23,zz,bx+4,24,zz+2,'sea_lantern')
 for zz in supports:
  for xx in [bx,bx+5]:box(xx,4,zz,xx+1,18,zz+1,'gray_concrete')
 steps=[]
 for zz in [z0,z1-4]:
  east=ident=='east' and zz==z0
  xa,xb=(bx+6,bx+20) if east else (bx-14,bx)
  box(xa,4,zz,xb,7,zz+4,'smooth_stone')
  for i in range(12):
   xx=bx+17-i if east else bx-12+i
   for z in range(zz,zz+4):
    if i:box(xx,7,z,xx+1,7+i,z+1,'light_gray_concrete')
    put(xx,7+i,z,'smooth_quartz_stairs',facing='west' if east else 'east')
    steps.append([xx,7+i,z])
   for z in [zz-1,zz+4]:put(xx,8+i,z,'iron_bars')
  # Full 4-wide portal: remove side enclosure at both stair-to-deck landings.
  xx=bx+5 if east else bx
  air(xx,19,zz,xx+1,23,zz+4)
  # Northern landings descend to the sunken service ground in two extra steps.
  if zz==z0:
   for k in range(2):
    xx=bx+21-k if east else bx-16+k
    for z in range(zz,zz+4):
     box(xx,4,z,xx+1,5+k,z+1,'smooth_stone')
     put(xx,5+k,z,'smooth_quartz_stairs',facing='west' if east else 'east')
     steps.append([xx,5+k,z])
 bridge_records.append({'id':ident,'x':bx,'z_span':[z0,z1],'deck_bottom_y':18,'foot_y':19,'rail_base_y':7,'clearance_above_base':11,'stairs':steps,'supports_z':supports})
 for x in range(bx+1,bx+5):
  for z in range(z0,z1):walks.append((x,19,z))
# Access from the south service road to all three bridges, through existing hardscape.
group('site',components['site']['name'])
for bx in [110,198,288]:box(bx-14,4,148,bx+6,7,149,'smooth_stone')
(R/'campus_revision.json').write_text(json.dumps({'baseline':'R12','podium_floors_y':[7,13,19],'podium_connection_bounds':[104,176,120,216],'podium_routes':podium_routes,'utility_north_pad_z':8,'utility_pads':{'substation':[36,8,110,38],'waterworks':[137,8,194,35],'airplant':[207,8,281,29]},'bridges':bridge_records,'conservative_vehicle_height_blocks':7,'conservative_vehicle_top_exclusive_y':15,'bridge_bottom_y':18,'lighting':'flush aisle strips and formation markers; no yard poles or overhead arms','game':'not_run'},ensure_ascii=False,indent=2))
# Refresh exposed rims and light inventories after bridge foundations and shared paths.
group('site',components['site']['name'])
surf={}
for x in range(6,459):
 for z in range(8,149):
  if x>=301 and z>=35:continue
  ys=[y for y in [4,5,6] if (x,y,z) in sc.blocks]
  if ys:surf[x,z]=max(ys)
edges=[]
for (x,z),y in surf.items():
 if any(surf.get((x+dx,z+dz),y)<y for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):
  st=sc.blocks[x,y,z]
  if 'stairs' not in st and 'slab' not in st and sc.owners.get((x,y,z)) in ['site','railway']:
   put(x,y,z,'gray_concrete');edges.append([x,y,z])
yd=json.loads((R/'yard_revision.json').read_text());yd['step_borders']=edges;yd['step_border_cells']=len(edges)
yd['flush_guide_lights']=[q for q in yd['flush_guide_lights'] if sc.blocks.get(tuple(q))=='minecraft:sea_lantern']
for g in yd['lamp_groups']:g['cells']=[q for q in g['cells'] if sc.blocks.get(tuple(q))=='minecraft:sea_lantern']
yd['lamp_groups']=[g for g in yd['lamp_groups'] if g['cells']]
(R/'yard_revision.json').write_text(json.dumps(yd,ensure_ascii=False,indent=2))
