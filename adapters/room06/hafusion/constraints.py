"""Explicit block-space feasibility, not real-world measurement or photo fitting."""
import math
import numpy as np
from .bootstrap import CASE
from common import ellipse_cells
from hybrid_geometry import face_path
from v4_geometry import poly_margin

def make_rings(g,inset):
    result=[]
    for k,y in enumerate(np.linspace(2,204,46)):
        outer=np.asarray([g.at(j,float(y)) for j in range(24)])
        center=outer.mean(0); v=outer-center;v[:,1]=0
        inner=outer-v/np.linalg.norm(v,axis=1)[:,None]*inset
        path=[]
        for a,b in zip(inner,np.roll(inner,-1,axis=0)):
            seg=face_path(a,b);path.extend(seg if not path else seg[1:])
        if path[-1]!=path[0]:raise ValueError('Ring traversal is not closed')
        cells=set(path)
        margin=min(poly_margin(outer,x+dx,z+dz) for x,_,z in cells for dx,dz in [(0,0),(1,0),(0,1),(1,1)])
        result.append({'id':f'frame.ring.{k:02}','y':float(y),'outer':outer.tolist(),
                       'inner':inner.tolist(),'path':[list(q) for q in path],
                       'minimum_outer_margin':margin})
    return result

def choose_axis(g, rings, original=(28.5,28.5), max_shift=3):
    # Search translations only: retain verticality, radii, 3x3 shaft and scale.
    from open_lattice import OpenLatticeGeometry
    from common import Scene
    frame=Scene((56,282,56));OpenLatticeGeometry.frame(g,frame)
    protected=[q for q,o in frame.owners.items() if not o.startswith('frame.ring.') and q[1]<211]
    candidates=[]
    for dx in range(-max_shift,max_shift+1):
      for dz in range(-max_shift,max_shift+1):
        cx,cz=original[0]+dx,original[1]+dz
        shell=set(ellipse_cells(cx,cz,3.3,2.8,hollow=True))
        shaft={(x,z) for x in range(math.floor(cx)-1,math.floor(cx)+2) for z in range(math.floor(cz)-1,math.floor(cz)+2)}
        hits=sum((x,z) in shell|shaft for r in rings for x,y,z in r['path'])
        framehits=sum((x,z) in shell|shaft for x,y,z in protected)
        candidates.append({'center_xz':[cx,cz],'shift_xz':[dx,dz], 'ring_conflicts':hits,
                           'frame_conflicts':framehits,'distance2':dx*dx+dz*dz})
    ranked=sorted(candidates,key=lambda c:(c['ring_conflicts']+c['frame_conflicts'],c['distance2'],c['center_xz']))
    if ranked[0]['ring_conflicts'] or ranked[0]['frame_conflicts']:
        raise ValueError('No feasible core axis within allowed shift; do not alter outer silhouette')
    return {'selected':ranked[0],'baseline':next(c for c in candidates if c['distance2']==0),
            'candidates':ranked,'status':'estimated',
            'meaning':'Block-space feasibility proposal; not surveyed core position, not source-model core extraction.'}
