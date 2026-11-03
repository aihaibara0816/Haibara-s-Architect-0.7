"""Explicit facade layers for cardinal surfaces; no photo interpretation.

Stable fin phase is independent of crop origin. The caller supplies a reviewed
boundary, material choice and openings. Offsets are Minecraft cells.
"""
from detail_lab.states import make

VERSION='vertical-facade-0.1'
NORMALS={'north':(0,-1),'south':(0,1),'west':(-1,0),'east':(1,0)}

def skin_cell(x,y,z,side,*,pitch=2,phase=0,glass='gray_stained_glass_pane',
              fin='diorite_wall',fin_enabled=True,component='facade'):
    if side not in NORMALS:raise ValueError('Expected cardinal face')
    if not isinstance(pitch,int) or pitch<1:raise ValueError('pitch must be positive integer')
    dx,dz=NORMALS[side];u=x if dz else z
    cells=[(x,y,z,make(glass),component+'.glass')]
    if fin_enabled and (u-phase)%pitch==0:
        cells.append((x+dx,y,z+dz,make(fin),component+'.fins'))
    return cells

def add_skin(scene,*args,**kwargs):
    for x,y,z,s,owner in skin_cell(*args,**kwargs):scene.set((x,y,z),s,owner)
