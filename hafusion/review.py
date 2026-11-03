"""Explicit final-output review contracts; not automatic architectural judgement.

Sample coordinates are supplied by a case or researcher. Empty/unknown evidence
is pending, never a pass. Full-cube bearing is deliberately narrower than game
collision. No geometry, historical run, or acceptance record is mutated here.
"""
import math
from detail_lab.states import support_cube

AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}


def review_samples(blocks, size_xyz, checks):
    results = []
    seen = set()
    for check in checks:
        key, kind = check['id'], check['kind']
        if key in seen:
            raise ValueError('Duplicate check ID: ' + key)
        seen.add(key)
        if kind not in {'air', 'full_bearing', 'material'}:
            raise ValueError('Unknown check kind: ' + kind)
        samples = check.get('samples', [])
        failures, unknown = [], []
        for sample in samples:
            xyz = sample['xyz'] if isinstance(sample, dict) else sample
            if len(xyz) != 3 or any(type(v) is not int for v in xyz):
                raise ValueError('Integer XYZ required')
            q = tuple(xyz)
            if any(not 0 <= q[i] < size_xyz[i] for i in range(3)):
                failures.append({'xyz': xyz, 'reason': 'outside NBT bounds'})
                continue
            state = blocks.get(q, 'minecraft:air')
            if kind == 'air':
                ok = state.split('[')[0] in AIR
            elif kind == 'full_bearing':
                try:
                    ok = support_cube(state)
                except ValueError:
                    unknown.append({'xyz': xyz, 'state': state})
                    continue
            else:
                expected = sample.get('material', check.get('material')) if isinstance(sample, dict) else check.get('material')
                if not expected:
                    raise ValueError('Material expectation missing')
                expected = expected if ':' in expected else 'minecraft:' + expected
                ok = state.split('[')[0] == expected
            if not ok:
                failures.append({'xyz': xyz, 'state': state})
        results.append({'id': key, 'kind': kind, 'samples': len(samples),
                        'status': 'fail' if failures else ('pending' if unknown or not samples else 'pass'),
                        'failures': len(failures), 'unknown': len(unknown),
                        'examples': failures[:12] + unknown[:3]})
    return results


def construction_checks(records):
    """Guangzhou South's declared records, adapted to shared sample contracts.

    This schema is case-specific. Do not infer that all cases produce it.
    """
    columns, floors, headroom = [], [], []
    for c in records.get('columns', []):
        x, y, z = c['xyz']
        columns.extend([[x+dx, y-1, z+dz] for dx in range(c['width']) for dz in range(c['width'])])
    for e in records.get('entries', []):
        for x in range(e['x']-3, e['x']+4):
            floors.append([x, e['floor_y'], e['z']])
            headroom.extend([[x, e['floor_y']+dy, e['z']] for dy in (1, 2)])
    return [
        {'id': 'declared_voids', 'kind': 'air', 'samples': records.get('clearance', [])},
        {'id': 'column_full_bearing', 'kind': 'full_bearing', 'samples': columns},
        {'id': 'entry_floor', 'kind': 'full_bearing', 'samples': floors},
        {'id': 'entry_headroom', 'kind': 'air', 'samples': headroom},
        {'id': 'lamp_survival', 'kind': 'material', 'samples': records.get('lamps', [])},
    ]


def review_views(records, source_nbt_sha256, *, night=True):
    """Check camera metadata and source binding, not image quality or fidelity."""
    wanted = [q+'_'+m for q in ('se','sw','ne','nw') for m in (('day','night') if night else ('day',))] + ['top_day']
    by_id = {}
    for record in records:
        key = record['camera']['id']
        if key in by_id:
            raise ValueError('Duplicate rendered camera ID: ' + key)
        by_id[key] = record
    # Older valid top views may be named top/plan. Judge geometry, not spelling;
    # keep the original ID in the report and never rewrite historical metadata.
    if 'top_day' not in by_id:
        for record in records:
            v = record['camera']
            try:
                vertical = (v['eye'][0] == v['target'][0] and v['eye'][2] == v['target'][2]
                            and v['eye'][1] > v['target'][1])
            except (KeyError,TypeError,IndexError):
                vertical = False
            if vertical and v.get('ortho') and not v.get('night') and not any(k in v for k in ('cutX','cutY','minY')):
                by_id['top_day'] = record
                break
    result, frames = [], []
    for key in wanted:
        r = by_id.get(key)
        if r is None:
            result.append({'id': key, 'status': 'pending', 'reason': 'missing rendered view'})
            continue
        v = r['camera']
        errors = []
        if not source_nbt_sha256 or r.get('source_nbt_sha256') != source_nbt_sha256:
            errors.append('source NBT mismatch')
        if not v.get('ortho') or any(k in v for k in ('cutX','cutY','minY')):
            errors.append('full orthographic view required')
        try:
            dx, dy, dz = [float(v['eye'][i])-float(v['target'][i]) for i in range(3)]
            if not all(math.isfinite(n) for n in (dx,dy,dz)):
                errors.append('nonfinite camera')
            if key == 'top_day':
                if abs(dx)>1e-7 or abs(dz)>1e-7 or dy<=0 or v.get('night', False):
                    errors.append('top must be vertical, not oblique')
            else:
                q, mode = key.split('_')
                if dx==0 or dz==0 or not math.isclose(abs(dx),abs(dz),rel_tol=1e-7):
                    errors.append('not 45 degrees')
                if (dx>0)!=(q in ('se','ne')) or (dz>0)!=(q in ('se','sw')):
                    errors.append('quadrant mismatch')
                if bool(v.get('night',False))!=(mode=='night'):
                    errors.append('day/night mismatch')
                frames.append((tuple(v['target']),v['width'],v['height'],v['spanX'],v['spanZ'],round(dy,7),round(math.hypot(dx,dz),7)))
        except (KeyError,TypeError,ValueError):
            errors.append('invalid camera metadata')
        result.append({'id': key, 'source_camera_id': v['id'], 'status': 'fail' if errors else 'pass', 'errors': errors})
    result.append({'id': 'shared_diagonal_framing', 'status': 'fail' if len(set(frames))>1 else ('pass' if len(frames)==len(wanted)-1 else 'pending')})
    return result


def status(checks):
    if any(c['status']=='fail' for c in checks):
        return 'fail'
    return 'pass' if checks and all(c['status']=='pass' for c in checks) else 'pending'
