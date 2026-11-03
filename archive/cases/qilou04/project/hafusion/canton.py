"""Canton V6 adapter: reviewed V5 grammar plus an explicit feasibility revision.

This is a case adapter, not a generic automatic architectural reconstruction.
"""
import json,math
import numpy as np
from .bootstrap import CASE
from common import Scene,PALETTE,AIR,ellipse_cells
from v4_geometry import V4Geometry,SiteScene,LIGHT
from v5_geometry import Podium
from open_lattice import OpenLatticeGeometry,BARS,member_state,register_state,connect_thin_members
from hybrid_geometry import face_path

def load(name):return json.loads((CASE/'inputs'/name).read_text())
def rows(s):return [[*q,st,s.owners[q]] for q,st in sorted(s.blocks.items())]
def scene(data,size=(56,282,56)):
    s=SiteScene(tuple(size))
    for x,y,z,st,o in data:s.set((x,y,z),st,o)
    return s

class CantonGeometry(V4Geometry):
    def __init__(self,center):
        super().__init__(load('common.json'),load('v3a_parameters.json'),load('v4_parameters.json'))
        self.center=center
        self.shaft_min=[math.floor(v)-1 for v in center]
    def shaft(self,q):
        x,y,z=q;a,b=self.shaft_min
        return a<=x<a+3 and b<=z<b+3 and 2<=y<211
    def inner(self,s):
        for y in range(2,211):
            for x,z in ellipse_cells(*self.center,*self.c['core_radii_blocks'],hollow=True):
                s.set((x,y,z),PALETTE['core'][0],'core')
        for zone in self.zones:
            lo,hi=zone['height_blocks_half_open']
            for h in range(lo,hi):
                cx,cz,a,b,phi=self.route.profile(h)
                floor=h in [lo,hi-1] or (h-lo)%5==0
                for x,z in ellipse_cells(cx,cz,max(3.7,a-3),max(3.2,b-3),phi,hollow=not floor):
                    q=(x,h+2,z)
                    if not self.shaft(q) and q[1]<self.deck_y(x,z):
                        s.set(q,PALETTE['floor' if floor else 'glass'][0],'program.'+zone['id'])
        a,b=self.shaft_min
        for x in range(a,a+3):
          for z in range(b-3,b+2):
            for y in range(2,5):s.set((x,y,z),AIR,'entry')
    def outer(self,s):
        tmp=Scene(s.size);OpenLatticeGeometry.frame(self,tmp)
        for q,st in tmp.blocks.items():
            if not tmp.owners[q].startswith('frame.ring.'):
                if self.shaft(q):raise ValueError('Outer frame intersects reserved shaft')
                s.set(q,st,tmp.owners[q])
    def rings(self,s,ring_data):
        for r in ring_data:
            for q in r['path']:
                q=tuple(q)
                if self.shaft(q):raise ValueError('Ring path intersects reserved shaft')
                s.set(q,PALETTE['ring'][0],r['id'])
            for j,(a,b) in enumerate(zip(r['inner'],r['outer'])):
                for q in face_path(a,b):
                    if q not in s.blocks:
                        if self.shaft(q):raise ValueError('Ring joint intersects reserved shaft')
                        s.set(q,register_state(member_state(BARS)),f'frame.ring_joint.{r["id"].split(".")[-1]}.{j:02}')
    def lighting(self,s):
        # Light fixtures are children of the relocated core; legacy literal
        # coordinates must not be left behind after the parent moves.
        counts={}
        for zone in self.zones:
            owner='program.'+zone['id'];n=0
            for q,state in list(s.blocks.items()):
                x,y,z=q
                if s.owners[q]==owner and state==PALETTE['floor'][0] and x%5==2 and z%5==2 and not self.shaft((x,y-1,z)) and y>zone['local_y_half_open'][0]:
                    s.set(q,LIGHT,'lighting.interior.'+zone['id']);n+=1
            counts[zone['id']]=n
        dx,dz=[int(v-28.5) for v in self.center]
        anchors={(x+dx,z+dz) for x,z in [(25,28),(31,28),(28,25),(28,31)]}
        for q,st in list(s.blocks.items()):
            if s.owners[q]=='core' and q[1]%12==7 and (q[0],q[2]) in anchors:
                s.set(q,LIGHT,'lighting.core')
        return counts

class CantonPodium(Podium):
    def __init__(self,s,c,g):super().__init__(s,c);self.g=g
    def base_interface(self,tower):
        super().base_interface(tower)
        a,b=self.g.shaft_min
        for x in range(a,a+3):
          for z in range(b,45):
            for y in range(2,6):
                q=(x,y,z)
                if tower.owners.get(q,'').startswith(('program.','core')):
                    tower.set(q,AIR,'entry.clear')

def compose_tower(artifacts):
    s=Scene((56,282,56))
    for key in ['inner','rings','outer','crown','mast']:
        for x,y,z,st,o in artifacts[key]:s.set((x,y,z),st,o)
    return s

def make_site(g,artifacts):
    t=compose_tower(artifacts);lights=g.lighting(t)
    cfg=load('v5_parameters.json');s=SiteScene(tuple(cfg['size_xyz']))
    site=CantonPodium(s,cfg,g).build(t);offset=cfg['tower_offset_xyz']
    for q,st in t.blocks.items():s.set(tuple(q[i]+offset[i] for i in range(3)),st,t.owners[q])
    for q in list(s.blocks):
        local=tuple(q[i]-offset[i] for i in range(3))
        if g.shaft(local):s.set(q,AIR,'shaft.clear')
    connect_thin_members(s)
    return {'rows':rows(s),'size':list(s.size),'stairs':site.stairs,'lights_by_band':lights,
            'zones':g.zones,'site_records':site.records,'shaft_min':g.shaft_min,
            'core_center':g.center,'offset':offset,'levels':cfg['levels']}
