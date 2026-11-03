"""Small explicit vanilla state vocabulary. Visual geometry != collision geometry.

Unsupported IDs/properties fail closed. Connection solver covers these samples'
panes/bars against each other and known full support cubes, not all vanilla tags.
"""
from functools import lru_cache
from vendor.voxel_core import state, parse_state, Scene

DIRS={'north':(0,0,-1),'east':(1,0,0),'south':(0,0,1),'west':(-1,0,0)}
TURN={'north':'east','east':'south','south':'west','west':'north'}
FULL={
 'smooth_quartz','quartz_block','smooth_stone','stone_bricks','white_concrete',
 'light_gray_concrete','gray_concrete','black_concrete','red_concrete','orange_concrete','iron_block','pink_concrete','magenta_terracotta',
 'glass','gray_stained_glass','light_blue_stained_glass','black_stained_glass','blue_stained_glass','cyan_stained_glass',
 'white_stained_glass','red_stained_glass','green_stained_glass','water','bricks','polished_andesite',
 'dark_oak_planks','oak_planks','dirt','moss_block','sea_lantern','glowstone',
 'polished_deepslate','red_terracotta','yellow_terracotta','blue_concrete','bookshelf',
 'sandstone','smooth_sandstone','cut_sandstone','gold_block','lapis_block','oxidized_copper'}
SLABS={'smooth_sandstone_slab','sandstone_slab','cut_sandstone_slab','smooth_quartz_slab','quartz_slab','smooth_stone_slab','stone_brick_slab','oak_slab','dark_oak_slab','polished_deepslate_slab','polished_andesite_slab'}
STAIRS={'sandstone_stairs','smooth_sandstone_stairs','quartz_stairs','smooth_quartz_stairs','stone_brick_stairs','polished_andesite_stairs','polished_deepslate_stairs','oak_stairs','dark_oak_stairs'}
PANES={'glass_pane','gray_stained_glass_pane','light_blue_stained_glass_pane','green_stained_glass_pane','white_stained_glass_pane','red_stained_glass_pane','black_stained_glass_pane','blue_stained_glass_pane','cyan_stained_glass_pane','iron_bars'}
TRAPS={'iron_trapdoor','dark_oak_trapdoor','oak_trapdoor'}
WALLS={'diorite_wall'}
BOOL={'true','false'}

def make(name,**p):
    if ':' not in name:name='minecraft:'+name
    base=name.split(':',1)[1]
    defaults={}
    if base in SLABS:defaults={'type':'bottom','waterlogged':'false'}
    elif base in STAIRS:defaults={'facing':'north','half':'bottom','shape':'straight','waterlogged':'false'}
    elif base in PANES:defaults={**{d:'false' for d in DIRS},'waterlogged':'false'}
    elif base in TRAPS:defaults={'facing':'north','half':'bottom','open':'false','powered':'false','waterlogged':'false'}
    elif base in WALLS:defaults={**{d:'none' for d in DIRS},'up':'true','waterlogged':'false'}
    elif base=='chain':defaults={'axis':'y','waterlogged':'false'}
    elif base=='end_rod':defaults={'facing':'up'}
    elif base=='anvil':defaults={'facing':'north'}
    elif base=='redstone_torch':defaults={'lit':'true'}
    elif base=='oak_log':defaults={'axis':'y'}
    elif base in {'oak_leaves','azalea_leaves'}:defaults={'distance':'7','persistent':'true','waterlogged':'false'}
    elif base=='grass_block':defaults={'snowy':'false'}
    elif base=='bamboo':defaults={'age':'1','leaves':'none','stage':'1'}
    elif base=='water':defaults={'level':'0'}
    defaults.update({k:str(v).lower() for k,v in p.items()})
    s=state(name,**defaults);validate(s);return s

def family(s):
    n,p=parse_state(s);b=n.split(':',1)[1]
    if n=='minecraft:air':return 'air'
    if b in FULL or b in {'grass_block','oak_log'}:return 'cube'
    if b in SLABS:return 'slab'
    if b in STAIRS:return 'stairs'
    if b in PANES:return 'pane'
    if b in TRAPS:return 'trapdoor'
    if b in WALLS:return 'wall'
    if b=='chain':return 'chain'
    if b=='end_rod':return 'rod'
    if b=='anvil':return 'anvil'
    if b=='redstone_torch':return 'torch'
    if b in {'oak_leaves','azalea_leaves'}:return 'leaves'
    if b in {'poppy','oxeye_daisy'}:return 'flower'
    if b=='bamboo':return 'bamboo'
    raise ValueError('Unsupported block family: '+s)

@lru_cache(maxsize=4096)
def validate(s):
    n,p=parse_state(s)
    if not n.startswith('minecraft:'):raise ValueError('Only registered vanilla subset supported')
    b=n.split(':',1)[1];f=family(s);allowed={}
    if f=='slab':allowed={'type':{'top','bottom','double'},'waterlogged':BOOL}
    elif f=='stairs':allowed={'facing':set(DIRS),'half':{'top','bottom'},'shape':{'straight','inner_left','inner_right','outer_left','outer_right'},'waterlogged':BOOL}
    elif f=='pane':allowed={**{d:BOOL for d in DIRS},'waterlogged':BOOL}
    elif f=='trapdoor':allowed={'facing':set(DIRS),'half':{'top','bottom'},'open':BOOL,'powered':BOOL,'waterlogged':BOOL}
    elif f=='wall':allowed={**{d:{'none','low','tall'} for d in DIRS},'up':BOOL,'waterlogged':BOOL}
    elif f=='chain':allowed={'axis':{'x','y','z'},'waterlogged':BOOL}
    elif f=='rod':allowed={'facing':set(DIRS)|{'up','down'}}
    elif f=='anvil':allowed={'facing':set(DIRS)}
    elif f=='torch':allowed={'lit':BOOL}
    elif f=='leaves':allowed={'distance':set(map(str,range(1,8))),'persistent':BOOL,'waterlogged':BOOL}
    elif b=='grass_block':allowed={'snowy':BOOL}
    elif b=='oak_log':allowed={'axis':{'x','y','z'}}
    elif b=='water':allowed={'level':set(map(str,range(16)))}
    elif f=='bamboo':allowed={'age':{'0','1'},'leaves':{'none','small','large'},'stage':{'0','1'}}
    if set(p)!=set(allowed) or any(v not in allowed[k] for k,v in p.items()):raise ValueError('Invalid or incomplete registered state: '+s)
    return True

def transparent(s):return 'glass' in parse_state(s)[0] or parse_state(s)[0]=='minecraft:water'
def support_cube(s):return family(s)=='cube' and parse_state(s)[0]!='minecraft:water'
def connect(scene):
    """Final assembly pass. Every horizontal pane/bar edge is symmetric."""
    updates=0
    for xyz,s in list(scene.blocks.items()):
        if family(s)!='pane':continue
        n,p=parse_state(s)
        for d,off in DIRS.items():
            q=tuple(x+y for x,y in zip(xyz,off));other=scene.blocks.get(q)
            p[d]='true' if other and (family(other)=='pane' or support_cube(other)) else 'false'
        new=state(n,**p)
        updates+=s!=new;scene.blocks[xyz]=new
    return updates

def rotate_state(s):
    n,p=parse_state(s);p=dict(p)
    if p.get('facing') in TURN:p['facing']=TURN[p['facing']]
    if p.get('axis') in {'x','z'}:p['axis']={'x':'z','z':'x'}[p['axis']]
    old={d:p.pop(d) for d in DIRS if d in p}
    p.update({TURN[d]:v for d,v in old.items()})
    out=state(n,**p);validate(out);return out

def rotate_scene(scene):
    sx,sy,sz=scene.size;out=Scene((sz,sy,sx),max_cells=scene.max_cells)
    for (x,y,z),s in scene.blocks.items():out.set((sz-1-z,y,x),rotate_state(s),scene.owners[(x,y,z)])
    return out

@lru_cache(maxsize=4096)
def boxes(s):
    validate(s);n,p=parse_state(s);f=family(s)
    if f=='air':return ()
    if f in {'cube','leaves'}:return ((0,0,0,1,1,1),)
    if f=='slab':
        t=p['type'];return ((0,.5 if t=='top' else 0,0,1,.5 if t=='bottom' else 1,1),)
    if f=='stairs':
        d=p['facing'];sets={'north':{(0,0),(1,0)},'south':{(0,1),(1,1)},'west':{(0,0),(0,1)},'east':{(1,0),(1,1)}}
        high=sets[d];left={'north':'west','west':'south','south':'east','east':'north'}[d];right=TURN[d];shape=p['shape']
        if shape.startswith('inner'):high=high|sets[left if shape.endswith('left') else right]
        if shape.startswith('outer'):high=high&sets[left if shape.endswith('left') else right]
        bottom=p['half']=='bottom';out=[(0,0 if bottom else .5,0,1,.5 if bottom else 1,1)]
        out.extend((x*.5,.5 if bottom else 0,z*.5,(x+1)*.5,1 if bottom else .5,(z+1)*.5) for x,z in sorted(high))
        return tuple(out)
    if f=='pane':
        out=[(.4375,0,.4375,.5625,1,.5625)]
        for d,b in [('north',(.4375,0,0,.5625,1,.4375)),('south',(.4375,0,.5625,.5625,1,1)),('east',(.5625,0,.4375,1,1,.5625)),('west',(0,0,.4375,.4375,1,.5625))]:
            if p[d]=='true':out.append(b)
        return tuple(out)
    if f=='trapdoor':
        if p['open']=='false':return ((0,.8125 if p['half']=='top' else 0,0,1,1 if p['half']=='top' else .1875,1),)
        return ({'north':(0,0,.8125,1,1,1),'south':(0,0,0,1,1,.1875),'west':(.8125,0,0,1,1,1),'east':(0,0,0,.1875,1,1)}[p['facing']],)
    if f=='wall':
        # Official Java 1.21.1 template_wall_{post,side,side_tall} visual boxes.
        # This is NOT the 1.5-block-high wall collision shape or a world solver.
        out=[(.25,0,.25,.75,1,.75)] if p['up']=='true' else []
        for d in DIRS:
            if p[d]=='none':continue
            h=.875 if p[d]=='low' else 1
            out.append({'north':(.3125,0,0,.6875,h,.5),
                        'south':(.3125,0,.5,.6875,h,1),
                        'west':(0,0,.3125,.5,h,.6875),
                        'east':(.5,0,.3125,1,h,.6875)}[d])
        return tuple(out)
    if f=='anvil':
        # Java 1.21.1 template_anvil.json, in block units; textures omitted.
        out=[(2,0,2,14,4,14),(4,4,3,12,5,13),(6,5,4,10,10,12),(3,10,0,13,16,16)]
        if p['facing'] in {'east','west'}:out=[(z,y,x,Z,Y,X) for x,y,z,X,Y,Z in out]
        return tuple(tuple(v/16 for v in b) for b in out)
    if f=='torch':
        # Visible shaft/head envelope; alpha-textured torch planes are omitted.
        return ((7/16,0,7/16,9/16,10/16,9/16),)
    if f in {'chain','rod'}:
        # Thin solid boxes are an explicitly approximate substitute for textured models.
        axis=p.get('axis') or {'up':'y','down':'y','east':'x','west':'x','north':'z','south':'z'}[p['facing']]
        lo=[.4375]*3;hi=[.5625]*3;i='xyz'.index(axis);lo[i]=0;hi[i]=1
        return (tuple(lo+hi),)
    if f=='flower':return ((.4375,0,.4375,.5625,.625,.5625),(.25,.5,.25,.75,.6875,.75))
    if f=='bamboo':
        # Mojang 1.21.1 bamboo1_age{0,1} stem dimensions. Leaf clusters below
        # approximate alpha-textured planes; random model offsets are omitted.
        width=3/16 if p['age']=='1' else 2/16
        out=[(.5-width/2,0,.5-width/2,.5+width/2,1,.5+width/2)]
        if p['leaves']!='none':
            reach=.43 if p['leaves']=='large' else .30
            out += [(.5-reach,.55,.46,.5+reach,.64,.54),(.46,.74,.5-reach,.54,.83,.5+reach)]
        return tuple(out)
    raise ValueError(s)

def cube_control(s):
    n,p=parse_state(s);b=n.split(':',1)[1];f=family(s)
    if f in {'cube','air','leaves','flower'}:return s
    if f=='pane':return make('iron_block' if b=='iron_bars' else b.removesuffix('_pane'))
    if f=='rod':return make('sea_lantern')
    if f=='chain' or b=='iron_trapdoor':return make('iron_block')
    if f=='wall':return make('smooth_quartz')
    if f=='anvil':return make('iron_block')
    if f=='torch':return make('red_concrete')
    if f=='bamboo':return make('moss_block')
    if 'sandstone' in b:return make('smooth_sandstone')
    if 'quartz' in b:return make('smooth_quartz')
    if 'deepslate' in b:return make('polished_deepslate')
    if 'dark_oak' in b:return make('dark_oak_planks')
    if 'oak' in b:return make('oak_planks')
    if 'andesite' in b:return make('polished_andesite')
    if 'stone_brick' in b:return make('stone_bricks')
    return make('smooth_stone')

def color(s):
    n,p=parse_state(s)
    if n=='minecraft:bamboo':return (105,147,59)
    if 'orange_concrete' in n:return (224,111,36)
    if 'pink_concrete' in n:return (214,112,147)
    if 'magenta_terracotta' in n:return (153,88,111)
    if 'sandstone' in n:return (215,199,159) if 'cut_' in n else (225,211,175)
    if 'gold_block' in n:return (236,194,64)
    if 'lapis_block' in n:return (39,64,115)
    if 'oxidized_copper' in n:return (92,159,134)
    if n=='minecraft:water':return (75,132,143)
    if 'green_stained_glass' in n:return (119,165,139)
    if 'sea_lantern' in n or 'end_rod' in n:return (218,245,220)
    if 'glowstone' in n:return (247,206,135)
    if 'redstone_torch' in n:return (240,58,39) if p['lit']=='true' else (104,54,41)
    if 'bookshelf' in n:return (155,113,69)
    if 'anvil' in n:return (68,69,73)
    if 'poppy' in n:return (194,67,68)
    if 'daisy' in n:return (243,225,162)
    if 'red_stained' in n or 'red_concrete' in n:return (183,68,51)
    if 'white_stained' in n:return (212,224,223)
    if 'bricks' in n and 'stone' not in n or 'red_terracotta' in n:return (155,82,64)
    if 'yellow_terracotta' in n:return (183,141,91)
    if 'deepslate' in n or 'black_concrete' in n:return (65,72,76)
    if 'dark_oak' in n:return (100,70,45)
    if 'oak_log' in n:return (112,83,51)
    if 'leaves' in n:return (69,111,60) if 'oak' in n else (80,128,65)
    if 'moss' in n or 'grass' in n:return (110,148,77)
    if 'dirt' in n:return (128,94,62)
    if 'light_blue' in n:return (105,167,190)
    # Explicit untextured preview colours, not sampled vanilla textures.
    if 'blue_stained_glass' in n:return (48,63,126)
    if 'cyan_stained_glass' in n:return (49,116,125)
    if 'black_stained' in n:return (55,76,89)
    if 'gray_stained' in n:return (100,132,141)
    if 'glass' in n:return (163,201,206)
    if 'quartz' in n or 'white_concrete' in n:return (230,225,211)
    if 'diorite_wall' in n:return (218,219,210)
    if 'iron_block' in n:return (194,206,211)
    if 'iron_' in n or 'chain' in n:return (130,145,154)
    if 'oak' in n:return (163,124,77)
    if 'light_gray' in n:return (183,184,176)
    if 'gray_concrete' in n:return (91,101,104)
    return (156,164,163)
