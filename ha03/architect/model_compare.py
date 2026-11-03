"""Compare placed triangle geometry across file formats, independent of face order."""
from collections import defaultdict
from itertools import product, permutations
import numpy as np
from .model_io import world_meshes

def triangles(asset):
    return np.concatenate([v[f] for _,_,v,f in world_meshes(asset)])

def compare(a,b,tolerance_m=.001):
    if not np.isfinite(tolerance_m) or tolerance_m<=0:raise ValueError('Positive tolerance required')
    ta,tb=triangles(a),triangles(b);buckets=defaultdict(list)
    centers=tb.mean(1)
    for i,c in enumerate(centers):buckets[tuple(np.floor(c/tolerance_m).astype(np.int64))].append(i)
    perms=np.array(list(permutations(range(3))));offsets=list(product((-1,0,1),repeat=3));used=set();maxerr=0.;missing=0
    for t in ta:
        cell=np.floor(t.mean(0)/tolerance_m).astype(np.int64);best=None
        for off in offsets:
            for j in buckets.get(tuple(cell+off),[]):
                if j in used:continue
                err=float(np.abs(tb[j][perms]-t).max(axis=(1,2)).min())
                if err<=tolerance_m and (best is None or err<best[0]):best=(err,j)
        if best is None:missing+=1
        else:maxerr=max(maxerr,best[0]);used.add(best[1])
    return {'status':'pass' if missing==0 and len(used)==len(tb) else 'fail','source_triangles':len(ta),'target_triangles':len(tb),'unmatched_source_triangles':missing,'unmatched_target_triangles':len(tb)-len(used),'maximum_matched_vertex_axis_error_m':maxerr,'tolerance_m':tolerance_m,'scope':'Placed triangle corner multiset; ignores winding, materials, textures, loose curves and hierarchy.'}
