"""Shared, immutable-run export for explicit building adapters."""
from pathlib import Path
from hafusion import __version__
import collections,gzip,hashlib,json
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build,Limits

def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_run(case,run,p,b,source,extra=None):
    out=case/'runs'/run
    if out.exists():raise ValueError('Existing run is immutable: '+str(out))
    out.mkdir(parents=True);dump(out/'params_used.json',p)
    updates=b.finish();s=b.s;meta=export_structure(s,out/'building.nbt',include_air=False)
    rb=load_build(out/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
    assert rb.blocks==s.blocks and rb.size==s.size
    counts=collections.Counter(v.split('[')[0] for v in rb.blocks.values());states=collections.Counter(rb.blocks.values())
    (out/'materials.csv').write_text('block_id,count,stacks,remainder\n'+''.join(f'{k},{v},{v//64},{v%64}\n' for k,v in sorted(counts.items())),encoding='utf-8-sig')
    (out/'blockstates.csv').write_text('blockstate,count\n'+''.join('"'+k+'",'+str(v)+'\n' for k,v in sorted(states.items())),encoding='utf-8-sig')
    owners=sorted(set(s.owners.values()));ids={s:i for i,s in enumerate(owners)}
    data=json.dumps({'owner_names':owners,'xyz_owner':[[*q,ids[o]] for q,o in sorted(s.owners.items())]},separators=(',',':')).encode()
    (out/'component_ownership.json.gz').write_bytes(gzip.compress(data,mtime=0))
    dump(out/'interiors.json',b.rooms);dump(out/'windows.json',b.windows)
    dump(out/'manifest.json',{**meta,'case':case.name,'engine':'HAF '+__version__,'run':run,'readback_exact':True,'connection_updates':updates,
        'components':dict(collections.Counter(o.split('.')[0] for o in s.owners.values())),'component_count':len(owners),
        'material_types':len(counts),'state_types':len(states),'window_count':len(b.windows),'synthetic_room_count':len(b.rooms),
        'source_code_sha256':sha(source),'params_sha256':sha(out/'params_used.json'),'game_status':'pending',**(extra or {})})
    (out/'build_case_snapshot.py').write_bytes(Path(source).read_bytes())
    print(json.dumps({**meta,'windows':len(b.windows),'readback_exact':True}),flush=True)
    return out
