"""Single-writer content-addressed stages; no world-edit or distributed claims.

Independent implementation expanded from the R0.3 lab. Arnis inspired explicit
source/version invalidation; ObjToSchematic inspired separate geometry/material.
"""
from pathlib import Path
from research_lab.stage_cache import DiskCache, stage_key, digest

class Stages:
    def __init__(self, root, context, code_hash):
        self.disk=DiskCache(root);self.context=context;self.code_hash=code_hash
        self.keys={};self.values={}
    def run(self, name, params, dependencies, builder):
        if name in self.keys: raise ValueError('Duplicate stage')
        deps={role:self.keys[node] for role,node in dependencies.items()}
        key=stage_key(name,name,self.code_hash,params,deps,self.context)
        value=self.disk.get_or_build(key,name,builder)
        self.keys[name]=key;self.values[name]=value
        return value
    def summary(self):
        return {'events':self.disk.events,'hits':sum(e['hit'] for e in self.disk.events),
                'rebuilt':[e['stage'] for e in self.disk.events if not e['hit']],
                'scope':'Local single-writer artifact cache; NBT export and independent QA run every time.'}
