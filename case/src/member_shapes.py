"""Case preview models for explicit vanilla wall/bar states.

These are untextured visual boxes, not a Minecraft collision or lighting engine.
No preview-only thinning is applied to full-cube NBT blocks.
"""
from voxel_core import parse_state,block_parts as legacy_parts

def block_parts(state):
    name,p=parse_state(state)
    if name=='minecraft:diorite_wall':
        result=[(.25,0,.25,.75,1,.75)] if p.get('up')=='true' else []
        for d,box in [('north',(.3125,0,0,.6875,.875,.5)),('south',(.3125,0,.5,.6875,.875,1)),
                      ('east',(.5,0,.3125,1,.875,.6875)),('west',(0,0,.3125,.5,.875,.6875))]:
            side=p.get(d,'none')
            if side not in ['none','low','tall']:raise ValueError('Unknown wall side state')
            if side!='none':
                b=list(box)
                if side=='tall':b[4]=1
                result.append(tuple(b))
        return result
    if name=='minecraft:iron_bars':
        result=[(.4375,0,.4375,.5625,1,.5625)]
        for d,box in [('north',(.4375,0,0,.5625,1,.5)),('south',(.4375,0,.5,.5625,1,1)),
                      ('east',(.5,0,.4375,1,1,.5625)),('west',(0,0,.4375,.5,1,.5625))]:
            if p.get(d)=='true':result.append(box)
        return result
    return legacy_parts(state)

def union_volume(parts):
    # Exact union volume for these axis-aligned preview parts, for diagnostics only.
    axes=[sorted({p[i] for p in parts}|{p[i+3] for p in parts}) for i in range(3)]
    total=0.
    for a,b in zip(axes[0],axes[0][1:]):
      for c,d in zip(axes[1],axes[1][1:]):
       for e,f in zip(axes[2],axes[2][1:]):
        mid=((a+b)/2,(c+d)/2,(e+f)/2)
        if any(all(p[i]<=mid[i]<=p[i+3] for i in range(3)) for p in parts):total+=(b-a)*(d-c)*(f-e)
    return total
