"""Memorial porch contracts; dimensions are case-specific, not public defaults."""
import json

def contract(run):
    p = json.loads((run/'params_used.json').read_text())
    cx, cz = p['center_xz']; fy = p['floor_y']
    return [
        {'id': 'column_full_bearing', 'kind': 'full_bearing',
         'samples': [[cx+u+dx,fy,cz+z] for u in p['entrance_columns_x'] for dx in range(-2,3) for z in range(62,67)]},
        {'id': 'portico_landing', 'kind': 'full_bearing',
         'samples': [[cx+x,fy,cz+z] for x in range(-40,41) for z in range(59,66)]},
    ]
