"""Authored CITIC interior revision; bounded furniture, real block consumers.
No actual tenant fitout or working container/elevator claim.
"""
from detail_lab import states
M=states.make

def furnish(b,spec,plan,p,mainmask,lobby):
 records=[]
 for m in plan['modules']:
  x,y,z,X,Y,Z=m['bounds_xyz'];own='module.'+m['component_id'];kind=m['kind'];before=len(b.s.blocks)
  def put(a,h,c,mat,part):
   assert x<=a<X and y<=h<Y and z<=c<Z,(m['component_id'],a,h,c)
   b.put(a,h,c,mat,own+'.'+part)
  if kind=='desk_group':
   for zz in [z,z+2]:
    for xx in range(x,X):
     put(xx,y,zz,M('oak_slab',type='top'),'desk')
     if xx in [x,X-1]:put(xx,y+1,zz,'black_stained_glass_pane','monitor')
    for xx in [x,X-1]:put(xx,y,zz+1,M('dark_oak_stairs',facing='north'),'chair')
   for zz in [z,z+2]:put(x+1,y+1,zz,'gray_stained_glass_pane','desk_screen')
  elif kind=='meeting':
   for xx in range(x,X):
    for zz in [z+1,z+2]:put(xx,y,zz,M('dark_oak_slab',type='top'),'table')
    for zz,face in [(z,'south'),(z+3,'north')]:put(xx,y,zz,M('oak_stairs',facing=face),'chair')
   for zz in range(z,Z):
    for yy in range(y+1,Y):put(X-1,yy,zz,'glass_pane','partition')
   put(X-1,y+1,z+1,'black_concrete','presentation_screen')
  elif kind=='lounge':
   for xx in range(x,X):put(xx,y,z,M('quartz_stairs',facing='south'),'sofa')
   put(x,y,z+2,M('dark_oak_slab'),'coffee_table')
   put(X-1,y,Z-1,'oak_planks','plant_base');put(X-1,y+1,Z-1,'azalea_leaves','plant')
   if X-x>=3:put(x,y+1,z,'gray_stained_glass_pane','sofa_screen')
  elif kind in ['pantry','pantry_compact']:
   for xx in range(x,X):
    put(xx,y,z,'smooth_quartz','counter');put(xx,y+2,z,M('oak_trapdoor',half='top'),'upper_cabinet')
   put(x,y+1,z,'black_concrete','coffee_machine')
   put(X-1,y+1,z,'iron_block','sink')
   if kind=='pantry':
    for xx in range(x,X):put(xx,y,z+3,M('oak_stairs',facing='north'),'seat')
  elif kind=='reception':
   for xx in range(x,X):put(xx,y,z,'dark_oak_planks','counter')
   put(x,y+1,z,'black_stained_glass_pane','screen')
   put(X-1,y,z+1,M('dark_oak_stairs',facing='north'),'chair')
  elif kind=='storage':
   for xx in range(x,X):
    put(xx,y,z,'oak_planks','cabinet')
    put(xx,y+1,z,'bookshelf','archive')
    put(xx,y+2,z,M('dark_oak_slab'),'shelf_top')
   if m.get('printing'):
    put(X-1,y+1,z,'iron_block','printer');put(X-1,y+2,z,M('black_stained_glass_pane'),'printer_panel')
  elif kind=='window_bench':
   for xx in range(x,X):
    put(xx,y,Z-1,M('oak_stairs',facing='north'),'seat')
   for xx in [x+2,X-3]:put(xx,y,z,M('dark_oak_slab'),'table')
   for xx in [x,X-1]:
    put(xx,y,z,'oak_planks','planter');put(xx,y+1,z,'azalea_leaves','plant')
  else:raise ValueError('No module consumer: '+kind)
  records.append({**m,'consumer':'guangzhou_citic.interior_v2:furnish','geometry_status':'generated','net_blocks_added':len(b.s.blocks)-before})
 # Spatial boundaries are not random props. Keep the entire reserved walkway clear.
 for f in p['synthetic_levels']:
  fid=f['id'];y=f['floor_y'];cy=f['upper_floor_y']-2
  mask=lobby if fid=='lobby' else mainmask
  keeps=[k for k in spec['circulation_keepouts'] if k[1]==y]
  def roomput(x,yy,z,mat,tag):
   if (x,z) not in mask:return
   if any(k[0]<=x<k[3] and k[1]<=yy<k[4] and k[2]<=z<k[5] for k in keeps):return
   old=b.s.owners.get((x,yy,z),'')
   if old.startswith(('module.','tower.facade','tower.lobby.glazing','tower.portal')) or old.endswith('visual_column'):return
   b.put(x,yy,z,mat,'interior.'+fid+'.'+tag)
  # Column-to-ceiling shallow visual lintels, above the 4-block minimum clear zone.
  if fid!='lobby':
   for z in [56,72]:
    for x in range(36,54):roomput(x,cy-1,z,M('smooth_quartz_slab',type='top'),'ceiling_rib')
   # A full-height glazed meeting edge with an explicit two-cell opening.
   for z in range(56,64):
    if z in [59,60]:continue
    for yy in range(y,cy):roomput(51,yy,z,'gray_stained_glass_pane','meeting_boundary')
   # Short wall and timber slats separate tea and sofas, without closing sight lines.
   for x in range(51,54):
    roomput(x,y,68,'oak_planks','tea_boundary')
    for yy in range(y+1,y+3):roomput(x,yy,68,'iron_bars','tea_screen')
   # Core skirting and lift headers add a readable arrival zone.
   for z in [58,69]:
    for x in [42,45,47]:roomput(x,y,z,M('polished_deepslate_slab'),'lift_base')
  else:
   for x in [37,52]:
    for yy in range(y+3,cy):roomput(x,yy,67,'oak_planks','lobby_feature_slats')
   for x,z in [(38,60),(51,67)]:
    roomput(x,y,z,'smooth_quartz','planter');roomput(x,y+1,z,'azalea_leaves','plant')
 return records
