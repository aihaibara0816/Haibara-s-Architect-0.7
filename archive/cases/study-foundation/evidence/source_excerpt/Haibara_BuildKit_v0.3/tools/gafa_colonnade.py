"""Project adapter. These assumed dimensions belong to GAFA study only."""
import math
from voxel_core import Scene,state,repeated_axes,AIR

def build(p):
    if p['scale_blocks_per_metre']!=1:raise ValueError('This adapter requires 1 block/metre; no automatic rescaling')
    if p['size_xyz']!=[22,20,34] or p['ground_top_y']!=2 or p['stair_platform_top_y_assumed']!=6:
        raise ValueError('Current adapter supports this crop/floor/platform only; edit adapter deliberately to change them')
    g=Scene(tuple(p['size_xyz']));stages=[]
    quartz='minecraft:smooth_quartz';red='minecraft:red_terracotta'
    def roof(x):return math.floor((p['roof_high_y_assumed']-(x-2)*p['roof_slope_assumed'])*2)/2
    def half_surface(x,z,top,mat,owner):
        # Exact top plane on the half-block grid, occupying only its top half.
        if abs(top*2-round(top*2))>1e-6:raise ValueError('Surface requires half-grid Y')
        y=math.ceil(top)-1;ty='top' if top==int(top) else 'bottom'
        g.set((x,y,z),state(mat,type=ty,waterlogged='false'),owner)
    # 01: small standalone plinth, not an invented campus plan.
    g.fill((0,0,0),(22,1,34),'minecraft:stone_bricks','ground.foundation')
    g.fill((0,1,0),(22,2,34),'minecraft:smooth_stone','ground.paving')
    # A border defines the crop without claiming real paving module dimensions.
    for x in [0,21]:g.fill((x,1,0),(x+1,2,34),'minecraft:light_gray_concrete','ground.border')
    for z in [0,33]:g.fill((0,1,z),(22,2,z+1),'minecraft:light_gray_concrete','ground.border')
    stages.append(('01_foundation',g.snapshot()))
    # Two rows, four axes = three bays. Small cylinders resolve to square columns.
    axes=repeated_axes(p['first_column_z'],p['bay_pitch_metres_assumed'],p['bay_count']+1)
    for row,cx in enumerate(p['column_centres_x']):
        for i,cz in enumerate(axes):
            cid=f'columns.r{row}.c{i}'
            g.cylinder(cx,cz,p['column_radius_metres_assumed'],2,3,'minecraft:polished_blackstone',cid+'.base')
            g.cylinder(cx,cz,p['column_radius_metres_assumed'],3,int(roof(cx)), 'minecraft:gray_concrete',cid+'.shaft')
    # A cropped red core wall only; openings are study placements, not verified rooms.
    g.fill((2,2,2),(4,18,32),red,'wall.red_core')
    for z0,z1 in [(5,7),(25,27)]:
        g.fill((3,8,z0),(4,13,z1),'minecraft:black_concrete',f'window.{z0}.frame')
        g.fill((3,9,z0),(4,12,z1),'minecraft:black_stained_glass',f'window.{z0}.glass')
    g.fill((2,6,16),(4,9,18),AIR,'opening.landing')
    # Through-opening retained, not a fictitious office interior.
    g.fill((2,2,10),(4,5,12),AIR,'opening.ground')
    stages.append(('02_columns_wall',g.snapshot()))
    # 03: open underside stair, 8 half-height treads for a 4-block level change.
    g.fill((4,5,14),(8,6,20),red,'stair.landing')
    g.fill((4,2,14),(5,5,15),red,'stair.landing_support')
    g.fill((4,2,19),(5,5,20),red,'stair.landing_support')
    for x in range(4,8):
        for z in range(15,19):g.set((x,5,z),'minecraft:smooth_stone','stair.landing_finish')
    # Treads span z15..18, four blocks clear; red structure is a thin sloped soffit.
    for i in range(8):
        x=15-i;top=2+(i+1)*.5
        for z in range(15,19):
            lower=math.ceil(top)-2
            if lower>=2:g.set((x,lower,z),red,'stair.soffit')
            if top==int(top):g.set((x,int(top)-1,z),'minecraft:smooth_stone','stair.treads')
            else:half_surface(x,z,top,'minecraft:smooth_stone_slab','stair.treads')
        for z in (14,19):
            g.set((x,math.ceil(top)-1,z),red,'stair.stringer')
            g.set((x,math.ceil(top),z),state('minecraft:nether_brick_fence',east='true',west='true',north='false',south='false',waterlogged='false'),'stair.rail')
    for x in range(4,8):
        for z in (14,19):g.set((x,6,z),state('minecraft:nether_brick_fence',east='true',west='true',north='false',south='false',waterlogged='false'),'stair.landing_rail')
    stages.append(('03_stair',g.snapshot()))
    # 04: a stepped shallow roof, half-grid cap. Actual roof details unknown.
    for x in range(2,21):
        for z in range(1,33):
            top=roof(x)+.5
            half_surface(x,z,top,'minecraft:smooth_quartz_slab','roof.cap')
    # Primary frames follow column axes; secondary beams provide the ceiling grid.
    for zi,cz in enumerate(axes):
        for x in range(4,20):
            g.set((x,int(roof(x))-1,cz),quartz,f'roof.primary.{zi}')
    for zi,cz in enumerate([9,17,25]):
        for x in range(4,20):
            half_surface(x,cz,roof(x),'minecraft:smooth_quartz_slab',f'roof.secondary_cross.{zi}')
    for xi,x in enumerate([5,9,13,17]):
        for z in range(1,33):
            g.set((x,int(roof(x))-1,z),quartz,f'roof.longitudinal.{xi}')
    # Close joints between cap height steps, avoiding daylight slots.
    for x in range(3,21):
        prev=roof(x-1);cur=roof(x)
        if cur<prev:
            for z in range(1,33):half_surface(x,z,prev,'minecraft:smooth_quartz_slab','roof.step_joint')
    stages.append(('04_roof_detail',g.snapshot()))
    return g,stages,{'column_axes_z':axes,'ground_surface':2,'stair_platform_surface':6,
                      'stair_clear_width':4,'net_stair_rise':4,'bay_count':len(axes)-1,
                      'round_column_deviation':'2x2 square voxel proxy at radius 1m',
                      'scale_verification':'pending','interior':'not_reconstructed'}
