"""Explicit final-output samples for this IFC case; no inferred building semantics."""
import json

def contract(run):
    r=json.loads((run/'construction_records.json').read_text());p=json.loads((run/'params_used.json').read_text())
    g=p['frame']['grade_y'];cx,cz=p['frame']['center_xz']
    return [
      {'id':'entry_floor','kind':'full_bearing','samples':[[e['x'],e['floor_y'],e['z']] for e in r['entrances']]},
      {'id':'entry_clearance','kind':'air','samples':[[e['x'],y,e['z']] for e in r['entrances'] for y in e['clear_ys']]},
      {'id':'declared_column_bearing','kind':'full_bearing','samples':[[c['x'],c['foot_y']-1,c['z']] for c in r['supports']]},
      {'id':'recorded_lamp_survival','kind':'material','samples':[{'xyz':l['xyz'],'material':l['state'].split('[')[0]} for l in r['lights']]},
      {'id':'hotel_central_void','kind':'air','samples':[[cx+dx,y,cz+dz] for y in range(g+p['tower']['hotel_lobby_blocks']+2,g+p['tower']['glass_height_blocks']-2) for dx,dz in [(0,0),(1,0),(0,1),(-1,0),(0,-1)]]}
    ]
