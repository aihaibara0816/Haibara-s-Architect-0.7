"""Seeded room lighting decisions, independent of iteration order or geometry.

This is procedural variation, not a prediction of the real building's occupancy.
Keyed hashes keep existing rooms stable when a new room is added.
"""
import hashlib

VERSION = 'room-lighting-0.2'
# A module release must not silently reseed existing rooms or furniture.
# New cases may explicitly opt into a different, persisted namespace.
RANDOM_NAMESPACE = 'room-lighting-0.1'

def first_clear_slot(candidates, occupied, reserved, connection_sensitive=()):
    """Pick an air cell that cannot add a horizontal pane/bar connection.

    Callers validate bounds and reserve slots for BOTH dark and lit rooms before
    applying occupancy randomness. This function never edits the geometry.
    """
    for p in candidates:
        p=tuple(p)
        if p in occupied or p in reserved:continue
        x,y,z=p
        if any((x+dx,y,z+dz) in connection_sensitive for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):continue
        return p
    return None

def unit(seed, *keys, namespace=RANDOM_NAMESPACE):
    payload = '\x1f'.join(map(str, (namespace, seed, *keys))).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big') / 2**64

def room_lighting(seed, floor_id, room_id, zone, activity=0.52, *, namespace=RANDOM_NAMESPACE):
    if not 0 <= activity <= 1:
        raise ValueError('activity must be in [0,1]')
    def draw(*keys):
        return unit(seed, *keys, namespace=namespace)
    floor_bias = (draw('floor', floor_id) - .5) * .52
    zone_bias = (draw('zone', floor_id, zone) - .5) * .30
    probability = max(.08, min(.88, activity + floor_bias + zone_bias))
    lit = draw('occupied', room_id) < probability
    material = 'glowstone' if draw('material', room_id) < .46 else 'sea_lantern'
    return {'lit': lit, 'material': material if lit else None,
            'fixture_count': (2 if draw('count', room_id) > .74 else 1) if lit else 0,
            'offset_x': int(draw('x', room_id) * 3) - 1,
            'depth': int(draw('z', room_id) * 3),
            'probability': round(probability, 4)}
