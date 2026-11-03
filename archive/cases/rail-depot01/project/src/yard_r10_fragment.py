"""North yard extension, independent lane context, surface edges and aisle lighting."""
group('outdoor','20 · 北侧新增两条露天整备线')
for z,start in [(32,354),(20,354)]:
 for x in range(start,454):
  box(x,7,z-4,x+1,9,z-2,'smooth_stone');put(x,8,z-3,'yellow_concrete')
 for k in range(2):
  for zz in range(z-4,z-2):put(start-2+k,7+k,zz,'smooth_quartz_stairs',facing='east')
 box(457,7,z-1,459,9,z+2,'gray_concrete');box(457,9,z-2,458,10,z+3,'red_concrete')
# The northern road is gone; the new sidings occupy its former strip.
# Draw a border on every exposed height step, including the inner shoulders.
group('site',components['site']['name'])
surface={}
for x in range(6,459):
 for z in range(8,149):
  if x>=301 and z>=35:continue
  ys=[y for y in [4,5,6] if (x,y,z) in sc.blocks]
  if ys:surface[x,z]=max(ys)
edges=[]
for (x,z),y in surface.items():
 if any(surface.get((x+dx,z+dz),y)<y for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):
  st=sc.blocks[x,y,z]
  if 'stairs' not in st and 'slab' not in st and sc.owners.get((x,y,z)) in ['site','railway']:
   put(x,y,z,'gray_concrete');edges.append([x,y,z])
# Broad deterministic patches, tied to paving panels rather than per-cell noise.
patches=0
for (x,y,z),st in list(sc.blocks.items()):
 if sc.owners.get((x,y,z))!='site' or y not in [4,6]:continue
 name=parse_state(st)[0]
 if name not in ['minecraft:stone','minecraft:andesite','minecraft:light_gray_concrete']:continue
 k=((x//13)*17+(z//9)*29+((x//31)^(z//19))*11)%31
 mat=('smooth_stone' if k<5 else 'andesite' if k<8 else 'stone') if y==4 else ('smooth_stone' if k<5 else 'stone' if k<7 else 'light_gray_concrete')
 put(x,y,z,mat);patches+=1
for x,z in [(46,111),(102,118),(158,89),(220,89),(282,89)]:
 for xx in range(x,x+4):
  for zz in range(z,z+2):
   if surface.get((xx,zz))==4:put(xx,4,zz,'iron_trapdoor',half='top',facing='north',open='false',powered='false')

# Swept horizontal vehicle footprint protects trackside poles. Light heads stay above it.
guard=set()
for x,y,z in trackcells:
 for xx in range(x-2,x+3):
  for zz in range(z-2,z+3):guard.add((xx,zz))
for p,q in curve_pairs:
 for x,y,z in curve_points(p,q):
  for xx in range(math.floor(x-2.5),math.ceil(x+2.5)):
   for zz in range(math.floor(z-2.5),math.ceil(z+2.5)):guard.add((xx,zz))
group('yardlights','21 · 股道之间的嵌地灯组')
light_groups=[];guide_lights=[]
# Pairs of flush light strips in the service aisles. No poles or overhead arms.
for x in range(36,450,20):
 axes=[]
 for z in sorted(corridor.get(x,[])):
  if not axes or z-axes[-1]>1:axes.append(z)
 for a,b in zip(axes,axes[1:]):
  if b-a<10:continue
  z=math.floor((a+b)/2)
  for dz in [-1,1]:
   cells=[]
   for xx in range(x-1,x+2):
    zz=z+dz
    if (xx,zz) in guard:continue
    ys=[y for y in range(4,7) if (xx,y,zz) in sc.blocks]
    if not ys:continue
    y=max(ys)
    if sc.owners.get((xx,y,zz)) not in ['site','railway','yardlights'] or any((xx,yy,zz) in sc.blocks for yy in range(y+1,16)):continue
    if [xx,y,zz] in edges:continue
    put(xx,y,zz,'sea_lantern');cells.append([xx,y,zz])
   if cells:light_groups.append({'cells':cells,'clear_axis_gap':round(b-a,2),'type':'flush_strip'})
# Compact entrance markers also remain flush to the existing surface.
for x in [10,26,42,58]:
 for z in [83,90,97]:
  ys=[y for y in range(4,7) if (x,y,z) in sc.blocks]
  if not ys:continue
  y=max(ys)
  if [x,y,z] not in edges and not any((x,yy,z) in sc.blocks for yy in range(y+1,16)):
   put(x,y,z,'sea_lantern');light_groups.append({'cells':[[x,y,z]],'entrance':True,'type':'flush'})
edge_keys={tuple(e) for e in edges}
# Low, flush lights supplement the aisle groups along the exposed formation, without breaking its rim.
for x in range(12,450,16):
 for z in sorted(set(round(v) for v in corridor.get(x,[]))):
  for dz in [-2,2]:
   zz=z+dz
   if (x,6,zz) in sc.blocks and sc.owners.get((x,6,zz)) in ['site','railway']:
    if (x,7,zz) not in sc.blocks and (x,6,zz) not in edge_keys:
     put(x,6,zz,'sea_lantern');guide_lights.append([x,6,zz])
# Independent inspection-lane canopy lighting is a continuous sequence of embedded strips.
group('testline',components['testline']['name'])
for x in range(62,160,8):box(x,15,138,x+3,16,139,'sea_lantern')
(R/'yard_revision.json').write_text(json.dumps({'baseline':'R09','main_track_count':10,'group_counts':[6,4],'independent_lane_z':135,'independent_lane_length_cells':141,'external_track_axes_z':[87,93],'external_axis_spacing':6,'external_sleeper_gap':3.25625,'north_perimeter_road_removed':True,'airplant_bounds':[207,8,281,29],'waterworks_offset':[0,-23],'utility_north_alignment_z':8,'step_border_cells':len(edges),'step_borders':edges,'paving_cells_processed':patches,'lamp_groups':light_groups,'flush_guide_lights':guide_lights,'test_canopy_light_strips':13,'tree_count':4,'game':'not_run'},ensure_ascii=False,indent=2))
