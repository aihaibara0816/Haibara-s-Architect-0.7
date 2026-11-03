"""Read and export the curated case archive without fetching private sources."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from .workflow06 import require, reject_links, run_path

ROOT=Path(__file__).resolve().parents[1]

def catalog():
    return json.loads((ROOT/'archive/catalog.json').read_text('utf8'))

def find_case(identity):
    for c in catalog()['entries']:
        if c['id']==identity:return c
    raise ValueError('unknown archive case: '+identity)

def local_asset(relative):
    require(isinstance(relative,str), 'asset path must be a string')
    p=Path(relative)
    require(not p.is_absolute() and '..' not in p.parts and p.parts and p.parts[0] in ['archive','downloads'], 'invalid archive path')
    resolved=(ROOT/p).resolve();require(resolved.is_relative_to(ROOT.resolve()),'asset leaves repository');reject_links(ROOT/p)
    require(resolved.is_file(),'archive asset missing: '+relative)
    return resolved

def verify_case(identity):
    c=find_case(identity);d=c['download'];b=local_asset(d['path']).read_bytes()
    require(len(b)==d['bytes'] and hashlib.sha256(b).hexdigest()==d['sha256'],'download checksum mismatch: '+identity)
    for p in c['artifact_paths']:local_asset(p)
    for p in c['images']:local_asset(p['path'])
    return {'id':identity,'status':'pass','scope':'curated archive pack SHA-256 and linked asset existence','buildability':c['buildability'],'game':c['game'],'aesthetic':c['acceptance']}

def export_case(identity,destination):
    verify_case(identity);c=find_case(identity);src=local_asset(c['download']['path'])
    directory=Path(destination).absolute();reject_links(directory);directory.mkdir(parents=True,exist_ok=True);reject_links(directory)
    target=directory/src.name
    with target.open('xb') as f:f.write(src.read_bytes())
    return {'id':identity,'output':str(target),'sha256':c['download']['sha256'],'mode':'export_existing_artifacts','generated':False}

def isolated_room(runs_root,run_id,seed=1145):
    require(type(seed)is int and 0<=seed<2**63,'seed must be a nonnegative integer')
    require(importlib.util.find_spec('nbtlib') is not None,'Room06 requires nbtlib; install requirements.txt first')
    out=run_path(runs_root,run_id);out.parent.mkdir(parents=True,exist_ok=True);reject_links(out.parent);out.mkdir(exist_ok=False)
    project=out/'project';shutil.copytree(ROOT/'adapters/room06',project)
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    for command in [[sys.executable,str(project/'src/build_room.py'),'result','--seed',str(seed)],
                    [sys.executable,str(project/'src/audit_room.py'),'result']]:
        result=subprocess.run(command,cwd=project,env=env,capture_output=True,text=True,encoding='utf8',shell=False)
        with (out/'build.log').open('a',encoding='utf8') as f:f.write(result.stdout+'\n'+result.stderr+'\n')
        require(result.returncode==0,'Room06 build/audit failed; see isolated build.log')
    evidence=project/'runs/result';audit=json.loads((evidence/'audit.json').read_text('utf8'))
    require(not audit['errors'],'Room06 audit has errors')
    manifest={'release':'0.7.0','kind':'isolated_room06','run_id':run_id,'seed':seed,'source':'adapters/room06',
              'artifact':str((evidence/'Room06.nbt').relative_to(out)).replace('\\','/'),
              'sha256':hashlib.sha256((evidence/'Room06.nbt').read_bytes()).hexdigest(),
              'status':{'geometry':'legacy_build_and_audit_pass','game':'pending','aesthetic':'pending','Corner01':'needs_revision'}}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
    return {'run':str(out),**manifest}

def knowledge(topic=None):
    data=json.loads((ROOT/'knowledge/workflow07.json').read_text('utf8'))
    if topic is None:return data
    for d in data['domains']:
        if d['id']==topic:return d
    raise ValueError('unknown knowledge domain: '+topic)
