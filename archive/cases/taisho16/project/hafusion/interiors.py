"""Stable, clearance-aware window-back furnishing proposals, not real interiors."""
from .lighting import unit

VERSION='window-room-0.1'
NAMESPACE='window-room-style-0.1'

def room_style(seed, room_id, clear_height, zone='office'):
    if clear_height<1:raise ValueError('at least one clear block is required')
    styles=['work','library','lounge','green'] if clear_height>=2 else ['work','library','lounge']
    pick=unit(seed,room_id,'style',namespace=NAMESPACE)
    style=styles[min(len(styles)-1,int(pick*len(styles)))]
    warm_share={'office':.55,'residential':.75,'hotel':.80}.get(zone,.60)
    warm=unit(seed,room_id,'temperature',namespace=NAMESPACE)<warm_share
    return {'style':style,'light':'glowstone' if warm else 'sea_lantern',
            'warm_share':warm_share,'clear_height':clear_height,
            'fidelity':'synthetic window-back variation; not surveyed room use'}

def furnishing_cells(style, clear_height):
    """Local x/y/z in a 4-wide, 4-deep bay; floor top at y=0, glazing at z=0.

    Furniture is deliberately set back to z=2..3. Caller checks supports,
    collisions, envelope, and any shared fixture reservations before placement.
    """
    if clear_height<1:raise ValueError('no furnishing clearance')
    if style=='work':return [(1,0,2,'anvil'),(3,0,3,'bookshelf')]
    if style=='library':return [(0,0,3,'bookshelf'),(1,0,3,'bookshelf'),(3,0,2,'dark_oak_slab')]
    if style=='lounge':return [(0,0,3,'dark_oak_stairs'),(1,0,3,'dark_oak_stairs'),(3,0,2,'dark_oak_slab')]
    if style=='green':
        if clear_height<2:raise ValueError('leaf-block planter needs two clear blocks')
        return [(1,0,3,'dark_oak_planks'),(1,1,3,'oak_leaves'),(3,0,2,'anvil')]
    raise ValueError('unknown room style')
