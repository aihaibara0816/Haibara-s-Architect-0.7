"""Consume design intent into an auditable plan; never places blocks or edits a run.

Coordinates are integer block coordinates, half-open bounds [x0,y0,z0,x1,y1,z1].
floor_y is the first standing-air cell above the finished floor; upper_floor_y
is the corresponding level above. Rules are planning checks, not game collision.
"""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


class HandoffError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise HandoffError(message)


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def bounds(value):
    require(isinstance(value, list) and len(value) == 6 and all(integer(x) for x in value),
            'bounds_xyz must contain six integer block coordinates')
    require(all(value[i] < value[i + 3] for i in range(3)), 'bounds must have positive volume')
    return value


def inside(a, b):
    return all(b[i] <= a[i] and a[i + 3] <= b[i + 3] for i in range(3))


def overlaps(a, b):
    return all(a[i] < b[i + 3] and b[i] < a[i + 3] for i in range(3))


def compile_handoff(spec):
    require(isinstance(spec, dict), 'handoff must be an object')
    require(spec.get('schema_version') == '0.4', 'explicit schema_version 0.4 required; do not relabel older study templates')
    catalog = json.loads((ROOT / 'docs/design_catalog.json').read_text(encoding="utf-8"))
    identities = {r['id']: r for r in catalog['rooms']}
    gardens = {g['id']: g for g in catalog['gardens']}
    require(spec.get('project_id'), 'project_id required')
    require(spec.get('route') in ('original', 'constrained_completion', 'real_reconstruction'), 'explicit design route required')
    require(spec.get('primary_use') in identities, 'unknown primary_use; extend the catalog deliberately')
    require(spec.get('interior_level') in ('L0', 'L1', 'L2', 'L3'), 'interior_level L0..L3 required')
    features = spec.get('identity_features', [])
    require(isinstance(features, list) and all(isinstance(x, str) and x.strip() for x in features)
            and len(set(features)) >= 3, 'record at least three distinct primary-use identity features')
    require(spec.get('style') in ('modern', 'medieval'), 'style must be modern or medieval; other styles need an explicit rule')
    coord = spec.get('coordinates', {})
    require(coord.get('unit') == 'block' and coord.get('up') == 'Y'
            and coord.get('north') in ('+Z', '-Z', 'unknown'), 'explicit block/Y-up coordinates and north required')
    count = spec.get('storeys_total')
    require(count is None or (integer(count) and count > 0), 'storeys_total must be a positive integer or null')
    scope = spec.get('authorized_scope', {})
    editable = [bounds(b) for b in scope.get('editable_regions', [])]
    require(editable, 'authorized editable regions required even for a plan')
    locked = scope.get('locked_component_ids', [])
    require(isinstance(locked, list) and all(isinstance(x, str) and x for x in locked), 'locked_component_ids must be explicit IDs')
    keepouts = [bounds(b) for b in spec.get('circulation_keepouts', [])]
    pending = []
    if count is None:
        pending.append('storeys_total unknown: low-rise coverage cannot be asserted; record or resolve the assumption')
    if spec.get('storeys_assumption'):
        pending.append('storey count uses a design assumption, not measured evidence')
    if spec['route'] != 'original' and not spec.get('evidence_refs'):
        pending.append('source evidence missing: constrained/real geometry remains unverified')
    floors = {}
    preferred_layers = 2 if spec['style'] == 'modern' else 1
    ceiling_plans = []
    for floor in spec.get('floor_levels', []):
        fid = floor.get('id')
        require(isinstance(fid, str) and fid and fid not in floors, 'unique floor IDs required')
        low, high, minimum = (floor.get(k) for k in ('floor_y', 'upper_floor_y', 'min_clear_height'))
        require(all(integer(v) for v in (low, high, minimum)) and high > low and minimum >= 2,
                'floor_y, upper_floor_y and min_clear_height must be valid integer block levels')
        target = high - preferred_layers
        exception = None
        if target - low < minimum:
            reason = floor.get('existing_slab_recess_reason')
            if spec['route'] == 'constrained_completion' and reason and high - 1 - low >= minimum:
                target = high - 1
                exception = 'existing_slab_recess: ' + str(reason)
            else:
                target = None
                pending.append(fid + ': insufficient headroom; do not move floors or hang a cubic lamp below the ceiling')
        ceiling_plans.append({'floor_id': fid, 'preferred_separator_layers': preferred_layers,
                              'ceiling_y': target, 'clear_height_blocks': None if target is None else target - low,
                              'exception': exception, 'floor_levels_changed': False,
                              'fixture_rule': 'flush_or_supported_thin_rod' if spec['style'] == 'modern' else 'supported_lantern',
                              'fixture_collision': 'pending', 'geometry_status': 'pending_adapter'})
        floors[fid] = floor
    require(floors, 'explicit floor_levels required')
    require(count is None or len(floors) <= count, 'declared floors exceed total storeys')
    if count is not None and len(floors) < count:
        pending.append('some storeys are not represented in this scope; building-wide lighting is not verified')
    coverage = 'all_occupied_spaces' if count is not None and count < 10 else ('evidence_based' if count else 'pending_storey_count')
    lighting = spec.get('lighting', {})
    override = lighting.get('coverage_override')
    if override:
        require(override in ('all_occupied_spaces', 'evidence_based', 'selected_spaces'), 'unknown coverage override')
        require(bool(lighting.get('override_reason')), 'lighting override requires user/evidence reason')
        coverage = override
    rooms = {}
    light_tasks = []
    for room in spec.get('rooms', []):
        rid = room.get('id')
        require(isinstance(rid, str) and rid and rid not in rooms, 'unique room IDs required')
        require(room.get('floor_id') in floors and room.get('function'), 'room floor_id and function required')
        rb = bounds(room.get('bounds_xyz'))
        require(any(inside(rb, b) for b in editable), 'room outside authorized scope: ' + rid)
        entrances = room.get('entrances', [])
        require(isinstance(entrances, list), 'entrances must be a list')
        for p in entrances:
            require(isinstance(p, list) and len(p) == 3 and all(integer(v) for v in p)
                    and all(rb[i] <= p[i] < rb[i + 3] for i in range(3)), 'entrance point must lie inside its room bounds')
        if not entrances:
            pending.append(rid + ': no entry/approach point recorded')
        rooms[rid] = room
        light_tasks.append({'room_id': rid, 'function': room['function'],
                            'required': coverage == 'all_occupied_spaces',
                            'status': 'planned_not_generated', 'color_intent': room.get('color_intent', 'unspecified')})
    require(rooms, 'explicit occupied rooms required; no inferred complete interiors')
    modules = []
    ids = set()
    for module in spec.get('proposed_modules', []):
        mid, rid = module.get('component_id'), module.get('room_id')
        require(isinstance(mid, str) and mid and mid not in ids, 'unique module component_id required')
        require(mid not in locked and not any(mid.startswith(x + '.') for x in locked), 'module changes a locked component: ' + mid)
        require(rid in rooms, 'module room_id must reference an occupied room')
        mb = bounds(module.get('bounds_xyz'))
        require(inside(mb, rooms[rid]['bounds_xyz']), 'module outside its room: ' + mid)
        require(not any(overlaps(mb, b) for b in keepouts), 'module intersects circulation keepout: ' + mid)
        require(not any(overlaps(mb, b['bounds_xyz']) for b in modules), 'module footprints overlap: ' + mid)
        ids.add(mid)
        modules.append(copy.deepcopy(module))
        if not module.get('use_faces'):
            pending.append(mid + ': use face/approach not recorded')
    landscape = spec.get('landscape')
    landscape_plan = None
    if landscape:
        require(landscape.get('archetype') in gardens, 'unknown landscape archetype')
        lb = bounds(landscape.get('bounds_xyz'))
        require(any(inside(lb, b) for b in editable), 'landscape outside authorized scope')
        water = landscape.get('water_requested', False)
        require(isinstance(water, bool), 'water_requested must be boolean')
        require(not water or bool(landscape.get('water_reason')), 'pond needs explicit design/user reason; never infer from civic label')
        landscape_plan = copy.deepcopy(landscape)
        landscape_plan['geometry_status'] = 'pending_adapter'
        landscape_plan['required_checks'] = ['whole_path_width', 'entry_view_corridors', 'stay_nodes', 'plant_support', 'maintenance_access']
        if water:
            landscape_plan['required_checks'] += ['water_containment', 'safe_edge_design']
        pending.append('landscape route, plants, edge and levels need geometric/readback checks')
    canonical = json.dumps(spec, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return {'schema_version': '0.4', 'engine': 'HAF 0.4.0', 'consumer': 'hafusion.design_handoff.compile_handoff',
            'project_id': spec['project_id'], 'source_sha256': hashlib.sha256(canonical).hexdigest(),
            'status': 'plan_with_pending_items' if pending else 'plan_ready_for_adapter',
            'primary_use': spec['primary_use'], 'identity_reference': identities[spec['primary_use']],
            'identity_features': features, 'secondary_uses': spec.get('secondary_uses', []),
            'interior_level': spec['interior_level'], 'authorized_scope': copy.deepcopy(scope),
            'lighting_coverage_policy': coverage, 'ceiling_plans': ceiling_plans,
            'lighting_tasks': light_tasks, 'modules': modules, 'landscape_plan': landscape_plan,
            'pending': pending, 'input_snapshot': copy.deepcopy(spec),
            'generated_geometry': False, 'game_status': 'pending',
            'limits': ['Planning checks only; no automatic furniture placement or arbitrary building generator',
                       'Bounding boxes do not establish game collision, structural safety or actual light coverage',
                       'Cold/warm materials do not imply vanilla colored-light propagation',
                       'Input snapshot preserves unconsumed fields; retention does not mean execution']}
