"""CPU anchor alignment; requires explicit 3D correspondences, not photo inference."""
import numpy as np

def fit_similarity(source, target, *, target_unit, tolerance):
    a,b=np.asarray(source,dtype=float),np.asarray(target,dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1]!=3 or len(a)<3:
        raise ValueError('at least 3 corresponding 3D points required')
    if target_unit not in ('m','block') or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('explicit target units and finite coordinates required')
    if tolerance < 0 or not np.isfinite(tolerance): raise ValueError('invalid tolerance')
    ac,bc=a-a.mean(0),b-b.mean(0)
    if np.linalg.matrix_rank(ac)<2 or np.linalg.matrix_rank(bc)<2:
        raise ValueError('collinear anchors do not constrain a 3D orientation')
    u,s,vt=np.linalg.svd(ac.T@bc)
    sign=np.ones(3);sign[-1]=1 if np.linalg.det(u@vt)>0 else -1
    rotation=u@np.diag(sign)@vt
    scale=float((s*sign).sum()/(ac*ac).sum())
    if scale<=0: raise ValueError('positive uniform scale required')
    translation=b.mean(0)-scale*a.mean(0)@rotation
    predicted=scale*a@rotation+translation
    errors=np.linalg.norm(predicted-b,axis=1)
    matrix=np.eye(4);matrix[:3,:3]=scale*rotation.T;matrix[:3,3]=translation
    return {'matrix':matrix.tolist(),'scale':scale,'det_rotation':float(np.linalg.det(rotation)),
            'rmse':float(np.sqrt(np.mean(errors**2))),'max_error':float(errors.max()),
            'unit':target_unit,'status':'candidate' if errors.max()<=tolerance else 'needs_review',
            'automatic_write':False,'scope':'fit anchors only; holdout and real camera validation still required'}

def transform(points, matrix):
    p=np.asarray(points,dtype=float);m=np.asarray(matrix,dtype=float)
    return p@m[:3,:3].T+m[:3,3]
