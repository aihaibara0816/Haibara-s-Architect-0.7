"""Small single-writer disk-cache experiment, not an installed engine scheduler.

Ideas studied: Arnis versioned wall caches and ObjToSchematic staged geometry /
material assignment. This implementation is new and independent of their code.
"""
from pathlib import Path
import hashlib, json, os, tempfile

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def digest(value): return hashlib.sha256(encode(value)).hexdigest()

def stage_key(stage, component_id, algorithm_version, parameters, dependencies, context):
    if not all((stage, component_id, algorithm_version)):
        raise ValueError('stage, component and algorithm version required')
    if not all(context.get(k) for k in ('frame_id', 'units', 'target_epoch', 'source_hash')):
        raise ValueError('explicit coordinate frame, units, epoch and source hash required')
    # Dependencies are ROLE -> hash: reversing input roles must change identity.
    return digest(dict(stage=stage, component_id=component_id, algorithm=algorithm_version,
                       params=parameters, dependencies=dependencies, context=context))

class DiskCache:
    def __init__(self, root):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True); self.events=[]
    def get_or_build(self, key, label, build):
        if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('expected SHA256 key')
        path = self.root/(key+'.json')
        if path.exists():
            obj = json.loads(path.read_text())
            if obj['key'] != key or digest(obj['payload']) != obj['payload_hash']:
                raise ValueError('cache content mismatch')
            self.events.append({'stage':label, 'hit':True, 'key':key})
            return obj['payload']
        payload = build()
        document = dict(key=key, payload=payload, payload_hash=digest(payload))
        fd, temp = tempfile.mkstemp(dir=self.root, prefix='entry-', suffix='.tmp')
        try:
            with os.fdopen(fd,'wb') as f: f.write(encode(document))
            os.replace(temp, path)
        finally:
            if os.path.exists(temp): os.unlink(temp)
        self.events.append({'stage':label, 'hit':False, 'key':key})
        return payload

def demonstration(cache, width=2, left_material='minecraft:stone', context=None):
    """Two piers plus a connector; synthetic geometry with declared dependencies."""
    context = context or dict(frame_id='synthetic-y-up', units='block', target_epoch='fixture', source_hash=digest('analytic-bridge-v1'))
    cache.events=[]
    def cached(stage, owner, params, deps, build):
        key=stage_key(stage, owner, 'lab-r03-v1', params, deps, context)
        value=cache.get_or_build(key,stage+':'+owner,build)
        return value,key
    def box(lo,hi):
        return {'lo':lo,'hi':hi,'cells':[[x,y,z] for x in range(lo[0],hi[0]) for y in range(lo[1],hi[1]) for z in range(lo[2],hi[2])]}
    left,lk=cached('geometry','pier.left',dict(width=width),{},lambda:box([0,0,0],[width,4,2]))
    right,rk=cached('geometry','pier.right',{}, {},lambda:box([9,0,0],[11,4,2]))
    connector,ck=cached('geometry','connector',{}, {'left':lk,'right':rk},lambda:box([left['hi'][0],3,0],[right['lo'][0],4,2]))
    geometry={'pier.left':left,'pier.right':right,'connector':connector}
    material={};material_keys={}
    for owner,g,key,state in [('pier.left',left,lk,left_material),('pier.right',right,rk,'minecraft:stone'),('connector',connector,ck,'minecraft:quartz_block')]:
        material[owner],material_keys[owner]=cached('material',owner,{'state':state},{'geometry':key},lambda g=g,state=state,owner=owner:[[ *p,state,owner] for p in g['cells']])
    def combine():
        cells={}
        for owner in sorted(material):
            for row in material[owner]:
                pos=tuple(row[:3])
                if pos in cells: raise ValueError('undeclared overlap')
                cells[pos]=row
        return [cells[p] for p in sorted(cells)]
    assembled,ak=cached('assembly','scene',{},material_keys,combine)
    return dict(geometry_hash=digest(geometry), output_hash=digest(assembled), output=assembled,
                rebuilt=[e['stage'] for e in cache.events if not e['hit']], hits=sum(e['hit'] for e in cache.events), key=ak)
