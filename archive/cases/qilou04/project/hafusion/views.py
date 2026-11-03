"""Four comparable diagonal review views, in model coordinates.

X+ is east and Z- is north for these labels. This does not infer a building's
surveyed bearing. The input list is copied, and detail views are preserved.
"""
from copy import deepcopy
import math

QUADRANTS = {'se': (1, 1), 'sw': (-1, 1), 'ne': (1, -1), 'nw': (-1, -1)}


def ensure_diagonal_views(views, size_xyz, *, night=True):
    """Ensure 45-degree, equally framed SE/SW/NE/NW day and optional night views.

    Fit the full volume in every view, rather than inheriting a detail crop.
    Existing diagonal IDs are refreshed from the same overview, making repeated
    calls idempotent and preventing different scales between the four sides.
    """
    if len(size_xyz) != 3 or any(not math.isfinite(v) or v <= 0 for v in size_xyz):
        raise ValueError('positive finite size_xyz required')
    ids = [v['id'] for v in views]
    if len(set(ids)) != len(ids):
        raise ValueError('camera IDs must be unique')
    reserved = {f'{q}_{mode}' for q in QUADRANTS for mode in ('day', 'night')}
    kept = [deepcopy(v) for v in views if v['id'] not in reserved]
    candidates = [v for v in kept if not v.get('night') and not any(k in v for k in ('cutX', 'cutY', 'minY'))]
    base = next((v for v in candidates if v['id'] == 'overview'), candidates[0] if candidates else {})
    target = list(base.get('target', [s / 2 for s in size_xyz]))
    width, height = base.get('width', 1800), base.get('height', 2400)
    aspect = width / height
    eye = base.get('eye', [target[0] + 300, target[1] + 80, target[2] + 300])
    distance = max(math.hypot(eye[0] - target[0], eye[2] - target[2]), max(size_xyz))
    rise = max(0.0, min(eye[1] - target[1], distance * .6))
    norm = math.hypot(distance, rise)
    sin_e, cos_e = rise / norm, distance / norm
    diag = distance / math.sqrt(2)
    half_x = half_y = 0.0
    for sx, sz in QUADRANTS.values():
        for x in (0, size_xyz[0]):
            for y in (0, size_xyz[1]):
                for z in (0, size_xyz[2]):
                    dx, dy, dz = x-target[0], y-target[1], z-target[2]
                    half_x = max(half_x, abs((sz*dx - sx*dz) / math.sqrt(2)))
                    half_y = max(half_y, abs(dy*cos_e - (sx*dx + sz*dz)*sin_e / math.sqrt(2)))
    span_x = max(float(base.get('spanX', 0)), 2*half_x*1.04, 2*half_y*1.04*aspect)
    shared = dict(target=target, width=width, height=height, spanX=span_x,
                  spanZ=span_x/aspect, ortho=True, fov=36, concept=False,
                  coordinate_frame='model: east=+X, north=-Z; geographic bearing unverified')
    for key in ('sun_day', 'sun_night'):
        if key in base:
            shared[key] = deepcopy(base[key])
    for q, (sx, sz) in QUADRANTS.items():
        for mode in (('day', 'night') if night else ('day',)):
            kept.append(dict(deepcopy(shared), id=f'{q}_{mode}',
                             eye=[target[0]+sx*diag, target[1]+rise, target[2]+sz*diag],
                             night=mode == 'night'))
    return kept


def ensure_review_views(views, size_xyz, *, night=True):
    """Four matched diagonals plus a genuinely vertical orthographic top view.

    Retain existing detail cameras and old top aliases. Refresh only top_day;
    plan footprint must not inherit a tilted satellite camera or a detail crop.
    """
    result = ensure_diagonal_views([v for v in views if v['id'] != 'top_day'], size_xyz, night=night)
    x, y, z = size_xyz
    span_x, span_z = x*1.06, z*1.06
    width = 1800
    height = max(1, round(width*span_z/span_x))
    result.append(dict(id='top_day', eye=[x/2, y+max(size_xyz), z/2],
                       target=[x/2, y/2, z/2], spanX=span_x,
                       spanZ=span_x*height/width, width=width, height=height,
                       ortho=True, night=False, fov=36, concept=False,
                       coordinate_frame='model: east=+X, north=-Z; geographic bearing unverified'))
    return result
