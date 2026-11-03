"""M05: case-specific open supply nook below the existing return stair."""
import nbtlib as n

def refit_under_stair(c):
 p,bes=c['p'],c['bes']
 def barrel(x,y,z,face,id):
  p(x,y,z,'barrel','understair.'+id,facing=face,open=False)
  bes[x,y,z]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])})
 # Deep low cupboard under the midlanding. Its usable door faces the short approach.
 barrel(11,3,12,'south','rear_stock')
 p(12,3,12,'spruce_planks','understair.closed_corner')
 for x in [11,12]:p(x,4,12,'white_carpet','understair.folded_linen')
 # Shallow side cabinet follows the taller return stair; low working surface, upper open shelf.
 barrel(12,3,13,'west','side_stock')
 p(12,4,13,'sea_pickle','understair.bottle_group',pickles=2,waterlogged=False)
 p(12,3,14,'spruce_planks','understair.side_cabinet')
 p(12,4,14,'oak_trapdoor','understair.open_shelf',facing='east',half='top',open=False)
 p(12,5,14,'flower_pot','understair.crock')
 # Replace the former upper barrel with a cloth-topped low counter, preserving its lower barrel.
 bes.pop((12,4,15),None)
 p(12,4,15,'white_carpet','understair.folded_service_cloth')
 # The fixture is fixed to the underside of the unchanged upper landing by a chain.
 p(12,6,15,'chain','understair.light_chain',axis='y')
 c['lantern'](12,5,15,'understair.task_lamp')
 # A thin stepped side screen; the front remains open, with no added door.
 for y,z in [(3,13),(4,13),(3,14)]:
  p(10,y,z,'dark_oak_trapdoor','understair.short_screen',facing='west',open=True)
 c['sign'](12,5,13,'west',['備品','予備の器','',''],'understair.stock_label')
 c['use']('G.understair_rear',11,2,13)
 c['use']('G.understair_shelf',11,2,14)
 c['use']('G.understair_counter',11,2,15)
 c['under_stair']={
  'program':'semi-open izakaya supply nook; concealed low storage at rear, open retrieval shelf toward hall',
  'changed_bounds_xyz':[10,3,12,13,7,16],
  'floor_block_y':2,'entry_cell':[11,3,16],
  'protected_upper_stair':'existing return stairs and landing unchanged',
  'approach_cells':[[11,3,13],[11,3,14],[11,3,15],[11,3,16]],
  'functional_containers':[[11,3,12],[12,3,13],[12,3,15]],
  'decorative_contents':'empty containers; sea-pickle bottle group, flower-pot crock, carpet folded cloth',
  'lighting':'supported hanging lantern below landing, above the side cabinet',
  'scope':'case_specific; not an arbitrary stair-storage generator',
  'game':'pending','aesthetic':'pending'}
 c['refit_groups'].append({'id':'under_stair_nook','name':'楼梯下半开放备货凹间','purpose':'备用器皿、布巾、库存和就近取物','approaches':['G.understair_rear','G.understair_shelf','G.understair_counter']})
