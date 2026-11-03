"""Bounded scene recipes learned from case studies; no world mutation or model code.

The height grid is supplied data, not automatic terrain extraction. Geometry,
readback, aesthetics and client behavior have deliberately separate states.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import sys

from .workflow06 import require, run_path, reject_links, load_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'support'))
from vendor.voxel_core import Scene, state, export_structure, parse_state
from vendor.inspect_build import load_build, Limits

VERSION = '0.7.0'
ALGORITHM = 'ha-habitat-0.7.0'
RECIPES = {
    'tree': {'size': [9, 13, 9], 'category': 'vegetation', 'support': 'trunk',
             'lesson': '层次化树冠、独立种子、保护通路；不是自动植被生态模拟'},
    'planter': {'size': [3, 5, 3], 'category': 'decoration', 'support': 'footprint',
                'lesson': '盆口、盆身、植株分开；不靠盆栽填满留白'},
    'reading-room': {'size': [19, 8, 17], 'category': 'interior', 'support': 'footprint',
                    'lesson': '先用途与活动组，再墙地顶、家具、齐平灯和使用面'},
    'workshop-bay': {'size': [27, 14, 23], 'category': 'industrial', 'support': 'footprint',
                     'lesson': '厂房柱网、屋面采光、大门、生产与通行分层；原创类型试样'},
    'pipe-rack': {'size': [7, 10, 17], 'category': 'industrial', 'support': 'footprint',
                  'lesson': '连续管线必须有承托、接口和跨越净空；不模拟真实工艺'},
    'fixed-roof-tank': {'size': [17, 15, 17], 'category': 'industrial', 'support': 'footprint',
                        'lesson': '矮宽圆筒、低坡固定顶、附属梯道；不是浮顶罐'},
}


def _int(value, label, low, high):
    require(type(value) is int and low <= value <= high, f'{label}: integer {low}..{high} required')
    return value


def _box(v, size, label):
    require(isinstance(v, list) and len(v) == 6, label + ': six integers required')
    for i, x in enumerate(v): _int(x, label, 0, size[i % 3])
    require(all(v[i] < v[i + 3] for i in range(3)), label + ': empty box')
    return v


def _inside(p, b):
    return all(b[i] <= p[i] < b[i + 3] for i in range(3))


def _pick(seed, component, channel, values):
    h = hashlib.sha256(json.dumps([ALGORITHM, seed, component, channel], separators=(',', ':')).encode()).digest()
    return values[int.from_bytes(h[:8], 'big') % len(values)]


def _recipe(recipe, seed, identity):
    """Return relative blocks, support cells and explicit acceptance probes."""
    cells, probes, metadata = {}, [], {}
    def put(x, y, z, name, **props):
        cells[x, y, z] = state('minecraft:' + name, **{k: str(v).lower() for k, v in props.items()})
    def fill(lo, hi, name, **props):
        for y in range(lo[1], hi[1]):
            for z in range(lo[2], hi[2]):
                for x in range(lo[0], hi[0]): put(x, y, z, name, **props)
    if recipe == 'tree':
        trunk = _pick(seed, identity, 'height', [5, 6, 7])
        radius = _pick(seed, identity, 'crown', [2, 3])
        species = _pick(seed, identity, 'species', ['oak', 'birch'])
        lean = _pick(seed, identity, 'crown-offset', [-1, 0, 1])
        for y in range(trunk + 1): put(4, y, 4, species + '_log', axis='y')
        for dy, r in [(-2, radius - 1), (-1, radius), (0, radius), (1, radius - 1), (2, 1)]:
            for x in range(4 + lean - r, 5 + lean + r):
                for z in range(4 - r, 5 + r):
                    if (x - 4 - lean)**2 + (z - 4)**2 <= r*r + 1 and (x, trunk + dy, z) not in cells:
                        put(x, trunk + dy, z, species + '_leaves', distance=1, persistent=True, waterlogged=False)
        support = [(4, 0, 4)]
        metadata.update(trunk_height=trunk + 1, crown_radius=radius, species=species, crown_offset=lean)
    elif recipe == 'planter':
        material = _pick(seed, identity, 'container', ['terracotta', 'light_gray_concrete', 'bricks'])
        fill((0, 0, 0), (3, 1, 3), material)
        put(1, 0, 1, 'dirt')
        put(1, 1, 1, 'oak_fence', north=False, south=False, east=False, west=False, waterlogged=False)
        for x, z in [(1, 1), (0, 1), (2, 1), (1, 0), (1, 2)]:
            put(x, 2, z, 'azalea_leaves', distance=1, persistent=True, waterlogged=False)
        put(1, 3, 1, 'azalea_leaves', distance=1, persistent=True, waterlogged=False)
        support = [(x, 0, z) for x in range(3) for z in range(3)]
        metadata['container'] = material
    elif recipe == 'reading-room':
        fill((0, 0, 0), (19, 1, 17), 'oak_planks')
        fill((0, 1, 0), (19, 6, 1), 'white_concrete')
        fill((0, 1, 16), (19, 6, 17), 'white_concrete')
        for x in [0, 18]: fill((x, 1, 1), (x + 1, 6, 16), 'white_concrete')
        # Two physical layers: ceiling then upper-floor slab. No hanging full cube.
        fill((0, 6, 0), (19, 7, 17), 'white_concrete')
        fill((0, 7, 0), (19, 8, 17), 'smooth_stone')
        for x in [4, 9, 14]:
            for z in [4, 9, 13]: put(x, 6, z, 'sea_lantern')
        for x in range(5, 14):
            for y in [2, 3, 4]: put(x, y, 0, 'glass')
        for x in [8, 9]:
            for y, half in [(1, 'lower'), (2, 'upper')]:
                put(x, y, 16, 'oak_door', facing='north', half=half, hinge='left' if x == 8 else 'right', open=False, powered=False)
            probes.append({'kind': 'door_pair', 'pos': [x, 1, 16]})
        # Core purpose: perimeter book walls, two table groups, separate lending desk.
        fill((1, 1, 2), (2, 4, 14), 'bookshelf')
        fill((17, 1, 2), (18, 4, 14), 'bookshelf')
        for x0 in [4, 11]:
            fill((x0, 1, 5), (x0 + 3, 2, 8), 'oak_slab', type='top', waterlogged=False)
            for x in [x0, x0 + 2]:
                put(x, 1, 4, 'oak_stairs', facing='north', half='bottom', shape='straight', waterlogged=False)
                put(x, 1, 8, 'oak_stairs', facing='south', half='bottom', shape='straight', waterlogged=False)
        fill((3, 1, 12), (6, 2, 13), 'spruce_planks')
        fill((3, 2, 12), (6, 3, 13), 'spruce_slab', type='bottom', waterlogged=False)
        # Low framed seating: broad cushion plus thin arms, not a line of identical stairs.
        fill((12, 1, 12), (15, 2, 13), 'quartz_slab', type='bottom', waterlogged=False)
        fill((12, 1, 13), (15, 2, 14), 'white_wool')
        for x, face in [(11, 'west'), (15, 'east')]:
            put(x, 1, 12, 'oak_trapdoor', facing=face, half='bottom', open=True, powered=False, waterlogged=False)
        put(16, 1, 3, 'oak_planks'); put(16, 2, 3, _pick(seed, identity, 'plant', ['potted_fern', 'potted_bamboo']))
        for x, z in [(8, 15), (9, 15), (8, 10), (9, 10), (3, 6), (16, 6), (6, 12), (13, 11)]:
            probes.append({'kind': 'air', 'pos': [x, 1, z]}); probes.append({'kind': 'air', 'pos': [x, 2, z]})
        support = [(x, 0, z) for x in range(19) for z in range(17)]
        metadata.update(purpose='reading-and-lending', full_ceiling=True, lighting='all-functional-zones', interaction='chairs and sofa decorative; doors pending client test')
    elif recipe == 'workshop-bay':
        fill((0, 0, 0), (27, 1, 23), 'smooth_stone')
        fill((0, 1, 0), (27, 9, 1), 'light_gray_concrete')
        fill((0, 1, 22), (27, 9, 23), 'light_gray_concrete')
        for x in [0, 26]: fill((x, 1, 1), (x + 1, 9, 22), 'light_gray_concrete')
        # A genuine open loading portal through the final envelope.
        for x in range(10, 17):
            for y in range(1, 7): cells.pop((x, y, 22), None)
        for x in [1, 9, 17, 25]:
            for z in [1, 11, 21]: fill((x, 1, z), (x + 1, 10, z + 1), 'gray_concrete')
        for x in range(27):
            y = 10 + (3 - abs((x % 9) - 4)) // 2
            fill((x, y, 0), (x + 1, y + 1, 23), 'smooth_stone')
        for x in [4, 13, 22]:
            for z in range(3, 20): put(x, 11, z, 'glass')
        for x in [4, 22]:
            for z in [5, 11, 17]:
                put(x, 8, z, 'sea_lantern'); fill((x,9,z),(x+1,12,z+1),'iron_block')
        for x0 in [3, 19]:
            for z0 in [4, 10, 16]:
                fill((x0, 1, z0), (x0 + 4, 3, z0 + 2), 'polished_andesite')
                fill((x0, 3, z0), (x0 + 4, 4, z0 + 1), 'yellow_concrete')
        for z in range(2, 23):
            probes.append({'kind': 'air', 'pos': [13, 1, z]}); probes.append({'kind': 'air', 'pos': [13, 2, z]})
        support = [(x, 0, z) for x in range(27) for z in range(23)]
        metadata.update(function='authored workshop sample', machines='decorative', entrance_clear_width=7)
    elif recipe == 'pipe-rack':
        for z in [0, 4, 8, 12, 16]:
            for x in [0, 6]: fill((x, 0, z), (x + 1, 7, z + 1), 'gray_concrete')
            fill((0, 6, z), (7, 7, z + 1), 'iron_block')
        for x in [2, 3, 4]: fill((x, 7, 0), (x + 1, 8, 17), 'light_gray_concrete')
        support = [(x, 0, z) for z in [0, 4, 8, 12, 16] for x in [0, 6]]
        metadata['ports'] = [{'id': side, 'cells': [[x, 7, z] for x in [2, 3, 4]]} for side, z in [('start', 0), ('end', 16)]]
        probes = [{'kind': 'air', 'pos': [3, 1, z]} for z in range(17)]
    else:
        for x in range(17):
            for z in range(17):
                d = math.hypot(x - 8, z - 8)
                if d <= 7:
                    put(x, 0, z, 'smooth_stone')
                    if d >= 6:
                        for y in range(1, 10): put(x, y, z, 'white_concrete')
                    put(x, 10 + max(0, int((7 - d) / 3)), z, 'white_concrete')
        for y in range(0, 11): put(8, y, 16, 'iron_bars', north=True, south=False, east=False, west=False, waterlogged=False)
        support = [(x, 0, z) for x in range(17) for z in range(17) if math.hypot(x-8,z-8) <= 7] + [(8,0,16)]
        metadata.update(type='fixed-roof atmospheric tank sample', contents='empty/decorative; no simulated fluid')
    return cells, support, probes, metadata


def compile_scene(request):
    require(isinstance(request, dict) and set(request) == {'schema_version','scene_id','seed','terrain','keepouts','modules'}, 'unexpected or missing scene request fields')
    require(request['schema_version'] == '0.7', 'scene schema must be 0.7')
    seed = _int(request['seed'], 'seed', 0, 2**63-1)
    require(isinstance(request['scene_id'], str) and 0 < len(request['scene_id']) <= 80, 'scene_id required')
    t = request['terrain']
    require(isinstance(t, dict) and set(t) == {'size_xyz','height_rows','water_cells','source'}, 'terrain fields invalid')
    size = t['size_xyz']
    require(isinstance(size, list) and len(size) == 3, 'size_xyz required')
    for x in size: _int(x, 'dimension', 1, 160)
    require(math.prod(size) <= 1_000_000, 'scene volume exceeds one million cells')
    require(isinstance(t['source'], str) and t['source'].strip(), 'terrain source required')
    heights = t['height_rows']
    require(isinstance(heights, list) and len(heights) == size[2], 'height row count')
    for row in heights:
        require(isinstance(row, list) and len(row) == size[0], 'height row width')
        for y in row: _int(y, 'ground height', 0, size[1] - 2)
    require(isinstance(t['water_cells'], list), 'water_cells list required')
    water = set()
    for c in t['water_cells']:
        require(isinstance(c, list) and len(c) == 2, 'water cell [x,z] required')
        _int(c[0], 'water x', 0, size[0]-1); _int(c[1], 'water z', 0, size[2]-1)
        require(tuple(c) not in water, 'duplicate water cell'); water.add(tuple(c))
    require(isinstance(request['keepouts'], list) and len(request['keepouts']) <= 500, 'keepout limit')
    keepouts = [_box(v, size, 'keepout') for v in request['keepouts']]
    require(isinstance(request['modules'], list) and 1 <= len(request['modules']) <= 200, '1..200 modules required')
    scene = Scene(tuple(size)); occupied = {}; modules = []; probes = []; ids = set()
    for z, row in enumerate(heights):
        for x, y in enumerate(row):
            scene.fill((x, 0, z), (x+1, y+1, z+1), state('minecraft:dirt'), 'terrain')
            scene.set((x,y,z), state('minecraft:water',level='0') if (x,z) in water else state('minecraft:grass_block',snowy='false'), 'terrain')
    terrain_hash = scene.fingerprint()
    # Sorting makes input reordering irrelevant; no candidate placement moves approved anchors.
    for m in request['modules']:
        require(isinstance(m, dict) and set(m) == {'id','recipe','origin'}, 'module fields invalid')
        require(isinstance(m['id'],str) and 0 < len(m['id']) <= 80 and m['id'] not in ids, 'unique module ID required')
        ids.add(m['id']); require(isinstance(m['recipe'],str) and m['recipe'] in RECIPES, 'unknown recipe')
        require(isinstance(m['origin'],list) and len(m['origin']) == 3, 'origin must have 3 integers')
        for i,v in enumerate(m['origin']): _int(v, 'origin', 0, size[i]-1)
    for m in sorted(request['modules'], key=lambda x:x['id']):
        origin = m['origin']; rel, supports, checks, meta = _recipe(m['recipe'], seed, m['id'])
        world = {tuple(p[i]+origin[i] for i in range(3)):v for p,v in rel.items()}
        require(all(all(0 <= p[i] < size[i] for i in range(3)) for p in world), 'module outside scene: '+m['id'])
        require(all(p[1] > heights[p[2]][p[0]] for p in world), 'module intersects terrain: '+m['id'])
        require(all((p[0],p[2]) not in water for p in world), 'module over protected water: '+m['id'])
        require(not any(any(_inside(p,b) for b in keepouts) for p in world), 'module violates keepout: '+m['id'])
        require(not set(world).intersection(occupied), 'module collision: '+m['id'])
        for p in supports:
            q = tuple(p[i]+origin[i] for i in range(3))
            require(q[1]-1 == heights[q[2]][q[0]] and (q[0],q[2]) not in water, 'unsupported module: '+m['id'])
        for p,v in world.items():scene.set(p,v,m['id']);occupied[p]=m['id']
        probes.extend({**c,'component_id':m['id'],'pos':[c['pos'][i]+origin[i] for i in range(3)]} for c in checks)
        lo=[min(p[i] for p in world) for i in range(3)];hi=[max(p[i] for p in world)+1 for i in range(3)]
        modules.append({**m,'bounds_xyz':lo+hi,'block_count':len(world),'recipe_version':ALGORITHM,'choices':meta})
    # Probes run after every module has been assembled, including later decorations.
    for c in probes:
        if c['kind']=='air': require(tuple(c['pos']) not in scene.blocks,'blocked use/route point: '+c['component_id'])
        elif c['kind']=='door_pair':
            q=tuple(c['pos']);above=(q[0],q[1]+1,q[2]);a,ap=parse_state(scene.blocks.get(q,'minecraft:air'));b,bp=parse_state(scene.blocks.get(above,'minecraft:air'))
            require(a==b and a.endswith('_door') and ap.get('half')=='lower' and bp.get('half')=='upper' and all(ap.get(k)==bp.get(k) for k in ['facing','hinge','open']),'invalid final door pair: '+c['component_id'])
    plan={'schema_version':'0.7','scene_id':request['scene_id'],'algorithm':ALGORITHM,'seed':seed,'terrain_source':t['source'],
          'terrain_sha256':terrain_hash,'terrain_changes':0,'modules':modules,'probes':probes,'geometry_sha256':scene.fingerprint(),
          'non_air_blocks':len(scene.blocks),'status':{'geometry':'compiled','nbt':'not_written','visual':'pending','game':'pending','user_aesthetic':'pending'},
          'limits':['Fixed authored recipes, no arbitrary building synthesis','Height grid supplied by caller; no automatic world extraction','Block envelopes are not client collision models','No existing world is opened or changed','No trained weights or self-improving model']}
    return scene, plan


def _write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n',encoding='utf8')


def _readback(scene, path):
    rb=load_build(path,Limits(cells=1_000_000,nodes=12_000_000,decoded_bytes=128*1024*1024))
    require(rb.size==scene.size,'NBT size mismatch')
    require(rb.info['format']=='java_structure' and rb.info['data_version']==3955,'NBT format/version mismatch')
    require(rb.info['entities_count']==0 and rb.info['block_entities_count']==0,'unexpected NBT entities')
    require(len(rb.blocks)==math.prod(scene.size),'NBT explicit-air coverage mismatch')
    require({p:s for p,s in rb.blocks.items() if s!='minecraft:air'}==scene.blocks,'NBT block replay mismatch')
    return {'file':path.name,'bytes':rb.info['file_bytes'],'sha256':rb.info['file_sha256'],
            'listed_blocks':len(rb.blocks),'non_air_blocks':len(scene.blocks),'size_xyz':list(rb.size),
            'contains_explicit_air':True,'geometry_sha256':scene.fingerprint(),'data_version':3955}


def build_scene(request, runs_root, run_id):
    scene, plan = compile_scene(request)
    out=run_path(runs_root,run_id); out.parent.mkdir(parents=True,exist_ok=True);reject_links(out.parent);out.mkdir(exist_ok=False)
    _write_json(out/'request.json',request)
    nb=export_structure(scene,out/'scene.nbt',include_air=True)
    require(nb==_readback(scene,out/'scene.nbt'),'NBT export summary mismatch')
    plan['status']['nbt']='exact_readback';_write_json(out/'scene_plan.json',plan)
    _write_json(out/'owners.json',{','.join(map(str,p)):v for p,v in sorted(scene.owners.items())})
    manifest={'release':VERSION,'run_id':run_id,'kind':'habitat07','status':plan['status'],'geometry_sha256':scene.fingerprint(),'nbt':nb,'artifacts':{}}
    for name in ['request.json','scene.nbt','scene_plan.json','owners.json']:
        b=(out/name).read_bytes();manifest['artifacts'][name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    _write_json(out/'manifest.json',manifest)
    return {'run':str(out),'state':'generated','non_air_blocks':len(scene.blocks),'status':plan['status']}


def verify_scene(runs_root,run_id):
    p=run_path(runs_root,run_id);reject_links(p);m=load_json(p/'manifest.json')
    require(isinstance(m,dict),'manifest must be an object')
    require(m.get('kind')=='habitat07','not a habitat07 run')
    require(m.get('release')==VERSION and m.get('run_id')==run_id,'manifest release/run mismatch')
    expected={'request.json','scene.nbt','scene_plan.json','owners.json'}
    require(isinstance(m.get('artifacts'),dict),'artifact manifest must be an object')
    require(set(m.get('artifacts',{}))==expected,'unexpected artifact manifest')
    require({x.name for x in p.iterdir()}==expected|{'manifest.json'},'unexpected run files')
    for name in expected:
        f=p/name;reject_links(f);b=f.read_bytes();a=m['artifacts'][name]
        require(isinstance(a,dict) and set(a)=={'bytes','sha256'},'invalid artifact entry: '+name)
        require(len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256'],'artifact checksum mismatch: '+name)
    scene,plan=compile_scene(load_json(p/'request.json'));plan['status']['nbt']='exact_readback'
    require(load_json(p/'scene_plan.json')==plan,'scene plan replay mismatch')
    owners={','.join(map(str,q)):v for q,v in sorted(scene.owners.items())}
    require(load_json(p/'owners.json')==owners,'owners replay mismatch')
    require(m['geometry_sha256']==scene.fingerprint() and m['status']==plan['status'],'manifest replay mismatch')
    require(m.get('nbt')==_readback(scene,p/'scene.nbt'),'manifest NBT summary mismatch')
    return {'status':'pass','scope':'file hashes, recipe replay, NBT size/version/entities/explicit-air and final block states','game':'pending','visual':'pending','user_aesthetic':'pending','source_authenticity':'not_verified'}


def dispatch_scene(call,base_request,runs_root,run_id,execute=False):
    """Model may add bounded modules; host owns terrain, seed, base and execution."""
    require(isinstance(call,dict) and set(call)=={'name','arguments'},'scene tool call fields invalid')
    require(call['name']=='ha_scene_add_modules','unknown scene tool')
    args=call['arguments'];require(isinstance(args,dict) and set(args)=={'modules'},'scene arguments must contain only modules')
    require(isinstance(args['modules'],list) and args['modules'],'new modules required')
    compile_scene(base_request)
    request=json.loads(json.dumps(base_request));request['modules'].extend(args['modules'])
    plan=compile_scene(request)[1]
    if execute:return build_scene(request,runs_root,run_id)
    return {'state':'proposed','generated_geometry':False,'plan':plan,'execution':'host must explicitly enable execution'}
