"""M07: authored shopfront and roof revision; preserve established indoor groups."""
import nbtlib as n

def refit_frontage(c):
 p,box,B,bes=c['p'],c['box'],c['B'],c['bes']
 def clear(x,y,z):
  p(x,y,z,'air','frontage.removed');bes.pop((x,y,z),None)
 def clean(lo,hi):
  for x in range(lo[0],hi[0]):
   for y in range(lo[1],hi[1]):
    for z in range(lo[2],hi[2]):clear(x,y,z)
 def panel(x,y,z,face,id):p(x,y,z,'dark_oak_trapdoor','frontage.'+id,facing=face,open=True)
 # Remove only exterior attachments and the old main roof, not any room ceiling.
 for q,owner in list(B.s.owners.items()):
  if owner.startswith(('roof.','gable.','eave.','shop.sign_back','shop.name','shop.noren','entry.light_support','entry.lantern.','front.menu','front.supply','front.bench','front.low_base','front.rain_chain')):
   clear(*q)
 for q in [(9,4,24),(10,4,25)]:clear(*q)
 c['plants'][:]=[r for r in c['plants'] if r['id'] not in ['front.high','front.low']]
 c['lights'][:]=[r for r in c['lights'] if not r['id'].startswith('entry.lantern.')]
 # Shop bay faces the street at counter height. The existing booth remains behind it.
 clean((9,4,22),(13,6,24))
 for x in range(9,13):
  p(x,3,22,'oak_stairs','frontage.counter',facing='north',half='top')
  p(x,3,23,'oak_trapdoor','frontage.counter_lip',half='top',facing='south',open=False)
 panel(8,4,23,'south','folded_shutter');panel(8,5,23,'south','folded_shutter')
 p(9,4,23,'flower_pot','frontage.counter_cup')
 p(12,4,23,'sea_pickle','frontage.counter_bottles',pickles=2,waterlogged=False)
 # A three-block entrance, recessed one block. The former single door is removed.
 clean((14,3,22),(19,6,24))
 for x in [14,18]:box((x,3,21),(x+1,6,22),'stripped_oak_log','frontage.entry_inner_post',axis='y')
 box((14,5,21),(19,6,22),'stripped_spruce_log','frontage.entry_inner_head',axis='x')
 for x in [15,17]:c['banner'](x,5,22,'south','blue','frontage.entry_noren')
 for x in [14,18]:panel(x,3,22,'south','folded_entry_panel');panel(x,4,22,'south','folded_entry_panel')
 for x in range(15,18):
  for z in [22,23,24]:p(x,2,z,'polished_andesite','frontage.entry_paving')
 c['doors'][:]=[d for d in c['doors'] if d['id']!='entry.main']
 # Open dining window at the corner, then a separate service opening along the side.
 clean((19,4,22),(22,6,24))
 for x in [19,20,21]:p(x,3,22,'spruce_planks','frontage.dining_sill')
 for z in [14,15,16,20,21]:
  for y in [4,5]:clear(23,y,z);clear(24,y,z)
 for z in [14,15,16]:
  p(23,3,z,'oak_stairs','frontage.side_counter',facing='west',half='top')
  p(24,3,z,'oak_trapdoor','frontage.side_counter_lip',facing='east',half='top',open=False)
 p(24,4,14,'flower_pot','frontage.side_cup')
 p(24,4,16,'white_carpet','frontage.side_towel')
 # Keep opaque WC rear windows and the existing side door/frame.
 c['banner'](24,5,17,'east','red','frontage.blade_banner')
 c['sign'](24,6,17,'east',['日和','小食','',''],'frontage.side_sign')
 # Distinct upper bays: narrow study window and a longer living-room group.
 for x in range(8,23):
  for y in [9,10]:
   if x not in [13,18]:p(x,y,22,'white_terracotta','frontage.upper_plaster')
  clear(x,9,23)
 for x in [9,10,15,16,17,19,20,21]:
  for y in [9,10]:p(x,y,22,'white_stained_glass_pane','frontage.upper_window')
 for x in [8,11,14,22]:box((x,8,22),(x+1,11,23),'stripped_oak_log','frontage.upper_jamb',axis='y')
 for x in [9,15,17,20]:panel(x,9,23,'south','upper_partial_lattice')
 for x in range(8,12):p(x,8,23,'oak_trapdoor','frontage.study_sill',half='top',facing='south',open=False)
 for x in range(15,23):p(x,8,23,'oak_slab','frontage.living_sill',type='top')
 # End planters are supported on the projecting ledge; it is not a walkable balcony.
 c['pot'](16,9,23,'front.upper_left');c['pot'](22,9,23,'front.upper_right')
 for z in [13,14,15,16]:
  for y in [9,10]:p(23,y,z,'white_stained_glass_pane','frontage.side_upper_window')
 for z in [13,16]:panel(24,9,z,'east','side_upper_lattice')
 for z in [14,15]:clear(24,9,z)
 # Lower roofs have different lengths/depths. Entry canopy projects farther than the window hoods.
 for x0,x1,zrows in [(6,14,[(23,7),(24,6)]),(14,19,[(23,7),(24,7),(25,6)]),(19,25,[(23,7),(24,6)])]:
  for z,y in zrows:
   for x in range(x0,x1):p(x,y,z,'deepslate_tile_stairs','frontage.shop_roof',facing='north')
 for x in [7,10,13,18,22,24]:
  p(x,6,23,'oak_slab','frontage.shop_rafter',type='top')
 for x in [14,18]:
  p(x,6,24,'stripped_oak_log','frontage.entry_bracket',axis='z')
 for z in range(13,23):p(24,7,z,'deepslate_tile_stairs','frontage.side_roof',facing='west')
 for z in range(13,18):p(25,6,z,'deepslate_tile_stairs','frontage.side_roof_edge',facing='west')
 for z in [14,17,21]:p(24,6,z,'oak_slab','frontage.side_rafter',type='top')
 # Rain chain is local to the western hood; support meets its top face.
 for y in range(3,6):p(6,y,24,'chain','frontage.rain_chain',axis='y')
 p(6,6,24,'deepslate_tile_slab','frontage.rain_chain_mount',type='bottom')
 p(6,2,25,'smooth_stone','frontage.old_basin_removed');p(6,2,24,'water_cauldron','frontage.rain_basin',level=3)
 # Main roof: asymmetric depth, one coherent ridge and contrasting thin verge bands.
 profile={}
 for z in range(5,25):
  inset=min(z-5,24-z);y=12+inset//2;profile[z]=y
  for x in range(5,26):
   edge=x in [5,25]
   material='polished_deepslate' if edge else 'deepslate_tile'
   if inset%2:p(x,y,z,material+'_stairs','frontage.roof.slope',facing='south'if z<=14 else'north')
   else:p(x,y,z,material+'_slab','frontage.roof.slope',type='bottom')
  for x in [7,23]:
   for yy in range(13,y+1):p(x,yy,z,'white_terracotta','frontage.roof.gable_infill')
 # Fill was placed after roof only on wall lines; restore tiles there at roof elevation.
 for z,y in profile.items():
  inset=min(z-5,24-z)
  for x in [7,23]:
   p(x,y,z,'deepslate_tile_stairs' if inset%2 else 'deepslate_tile_slab','frontage.roof.slope',**({'facing':'south'if z<=14 else'north'}if inset%2 else{'type':'bottom'}))
 for x in range(5,26):p(x,17,14,'deepslate_tile_slab','frontage.roof.ridge_cap',type='bottom')
 for x in [5,25]:p(x,17,14,'polished_deepslate_stairs','frontage.roof.ridge_end',facing='east'if x==5 else'west')
 # Visible timber gable and recessed attic vent on the east and west elevations.
 for x,face in [(7,'west'),(23,'east')]:
  for z in range(9,21):p(x,13,z,'stripped_spruce_log','frontage.roof.gable_tie',axis='z')
  for y in [14,15]:p(x,y,14,'stripped_oak_log','frontage.roof.king_post',axis='y')
  for z in [12,16]:
   p(x,14,z,'dark_oak_planks','frontage.roof.vent_back')
   panel(x+(-1 if x==7 else 1),14,z,face,'gable_louver')
 # One small transverse gable over the eastern living-room bay; not a repeated temple roof.
 for x in range(16,24):
  d=min(x-16,23-x);y=13+d
  for z in range(19,26):
   old=profile.get(z,11)
   if y>=old:
    if x in [19,20]:p(x,y,z,'deepslate_tile_slab','frontage.roof.front_gable',type='bottom')
    else:p(x,y,z,'deepslate_tile_stairs','frontage.roof.front_gable',facing='east'if x<20 else'west')
  # Front triangular closure at z24, above the preserved interior ceiling.
  for yy in range(13,y):p(x,yy,24,'white_terracotta','frontage.roof.front_pediment')
 for x in range(17,23):p(x,13,24,'stripped_spruce_log','frontage.roof.front_tie',axis='x')
 for y in [14,15]:p(20,y,24,'stripped_oak_log','frontage.roof.front_post',axis='y')
 for x in [18,19,21]:panel(x,14,25,'south','front_attic_louver')
 for x in range(5,26,3):
  for z in [5,6,23,24]:p(x,11,z,'oak_slab','frontage.roof.rafter_tip',type='top')
 for z in [6,23]:box((7,11,z),(24,12,z+1),'stripped_oak_log','frontage.roof.eave_tie',axis='x')
 # Shop name sits over the left serving bay. Fixtures are tied to distinct activity points.
 box((9,6,23),(13,7,24),'spruce_planks','frontage.sign_back')
 c['sign'](10,6,24,'south',['日和小食','酒とごはん','',''],'frontage.shop_name')
 for x,y,z,id in [(8,5,23,'display'),(18,5,24,'entrance'),(24,5,14,'side')]:
  p(x,y+1,z,'stripped_oak_log','frontage.light_bracket',axis='z'if x<24 else'x')
  c['lantern'](x,y,z,'frontage.light.'+id)
 # Low bench and pots are grouped in two places, with a clear central approach.
 for x in [10,11]:
  p(x,3,25,'oak_slab','frontage.waiting_bench',type='top');p(x,4,25,'red_carpet','frontage.bench_cushion')
 for x in [9,12]:panel(x,3,25,'west'if x==9 else'east','bench_end')
 p(7,3,24,'barrel','frontage.plant_base',facing='south',open=False)
 bes[7,3,24]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])})
 c['pot'](7,4,24,'front.high')
 p(8,3,25,'terracotta','frontage.low_pot_base');c['pot'](8,4,25,'front.low')
 p(22,3,24,'spruce_planks','frontage.menu_base');p(22,4,24,'spruce_planks','frontage.menu_back')
 c['sign'](22,4,25,'south',['本日の小鉢','焼き魚','お茶とお酒',''],'frontage.menu')
 c['pot'](23,3,25,'front.corner')
 for id,x,z in [('front_counter',11,24),('front_waiting',11,26),('side_counter',25,15),('entry_threshold',16,22)]:c['use']('G.'+id,x,2,z)
 c['frontage']={
  'revision':'M07','route':'original design informed by Freedom still and sampled #104 frames; not a replica',
  'front_counter_opening':{'x':[9,12],'y':[4,5],'z':22},
  'entry':{'clear_x':[15,17],'z':[21,24],'floor_y':2,'noren_top_y':5,'main_door':'removed; open trading frontage, no closing mechanism'},
  'side_counter_opening':{'x':23,'y':[4,5],'z':[14,16]},
  'upper_windows':'narrow study pair; longer living group with two planted ledge ends; private bedroom and WC remain screened',
  'roof':'main east-west gable with thin edge bands and ridge; one smaller south-facing transverse gable over eastern bay; differentiated shop canopies',
  'protected':'interior furniture, stairs, paintings and under-stair nook except entrance frame/threshold interface',
  'status':{'file_geometry':'pending','game':'pending','aesthetic':'pending'}}
