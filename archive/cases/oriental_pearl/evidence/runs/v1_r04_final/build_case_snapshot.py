"""Oriental Pearl V1 explicit image/primary-paper adapter; HAF remains 0.3.

All measured/estimated dimensions use a single metres-to-blocks conversion.
No mesh reconstruction, learned geometry, survey alignment or automatic fusion.
"""
from pathlib import Path
import argparse, math, json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder, M
from hafusion.case_io import save_run, dump
CASE=Path(__file__).resolve().parent

class Pearl:
    def __init__(self,p):
        self.p=p;self.s=p['scale'];self.o=p['origin'];self.b=Builder(p['size'],20261026)
        self.component_specs=[]
    def q(self,v):return np.array([self.o[0]+v[0]*self.s,self.o[1]+v[1]*self.s,self.o[2]+v[2]*self.s])
    def record(self,id,kind,**kw):self.component_specs.append(dict(id=id,kind=kind,**kw))
    def tube(self,a,b,r,mat,owner,hollow=False):
        a=self.q(a);b=self.q(b);r*=self.s;d=b-a;l=float(d@d)
        if r<.75:
            # Sub-voxel axial members otherwise disappear between cell centres.
            # Explicit minimum-feature adaptation: one-cell bar centreline.
            self.b.line(a-.5,b-.5,'iron_bars',owner+'.thin_adaptation')
            return
        lo=np.floor(np.minimum(a,b)-r).astype(int);hi=np.ceil(np.maximum(a,b)+r).astype(int)
        for y in range(max(0,lo[1]),min(self.p['size'][1],hi[1]+1)):
            for x in range(max(0,lo[0]),min(self.p['size'][0],hi[0]+1)):
                for z in range(max(0,lo[2]),min(self.p['size'][2],hi[2]+1)):
                    v=np.array([x+.5,y+.5,z+.5]);t=(v-a)@d/l if l else 0
                    if not 0<=t<=1:continue
                    dist=np.linalg.norm(v-a-d*t)
                    if dist<=r and (not hollow or dist>=max(0,r-1.05)):self.b.put(x,y,z,mat,owner)
    def ring(self,center,r,mat,owner,step=.28):
        c=self.q(center);r*=self.s
        for t in np.arange(0,2*math.pi,step/max(1,r)):
            self.b.put(c[0]+r*math.cos(t)-.5,c[1]-.5,c[2]+r*math.sin(t)-.5,mat,owner)
    def disk(self,center,r,mat,owner,inner=0):
        c=self.q(center);self.b.disk(c[0],c[2],r*self.s,math.floor(c[1]),mat,owner,inner*self.s)
    def sphere(self,id,center,r,style):
        c=self.q(center);R=r*self.s;mode=self.p['shell_mode'];thick=self.p['shell_thickness_blocks']
        self.record(id,'sphere',center_m=center,radius_m=r,center_voxel=c.tolist(),radius_voxel=R,style=style)
        for y in range(math.floor(c[1]-R),math.ceil(c[1]+R)):
            for x in range(math.floor(c[0]-R),math.ceil(c[0]+R)):
                for z in range(math.floor(c[2]-R),math.ceil(c[2]+R)):
                    dx,dy,dz=x+.5-c[0],y+.5-c[1],z+.5-c[2];d=math.sqrt(dx*dx+dy*dy+dz*dz)
                    if not R-thick<d<=R:continue
                    t=dy/R;angle=math.atan2(dz,dx);sector=int((angle+math.pi)/(2*math.pi)*24)
                    mat='light_gray_concrete';suffix='silver_shell'
                    band=False
                    if style=='lower':
                        pink=(-.40<t<.56);band=(-.025<t<.12)
                    elif style=='upper':
                        pink=t>-.35;band=(-.49<t<-.29)
                    elif style=='capsule':
                        pink=(-.20<t<.5);band=(.0<t<.28)
                    else:pink=False;band=abs(t)<.15
                    if pink:
                        mat='pink_concrete' if (sector+int((t+1)*7))%4 else 'magenta_terracotta';suffix='rose_panel'
                    if band:mat='black_stained_glass' if sector%3 else 'gray_stained_glass';suffix='viewing_band'
                    if mode=='glass_control' and style in ('lower','upper','capsule'):
                        mat='red_stained_glass' if pink else 'gray_stained_glass';suffix='control_glass'
                    self.b.put(x,y,z,mat,id+'.'+suffix)
        # Backing and floors are deliberately synthetic; never claim real room plans.
        if style in ('lower','upper','capsule'):
            h=center[1]+(-r*.4 if style=='upper' else 0)
            self.disk((center[0],h-3.0,center[2]),r*.90,'smooth_stone',id+'.interior.floor')
            self.tube((center[0],h-2,center[2]),(center[0],h+3,center[2]),max(2,r*.55),'gray_concrete',id+'.interior.backing',hollow=True)
            self.b.rooms.append({'id':id+'.interior','fidelity':'synthetic gallery floor and opaque window-back, no real plan','height_m':h})
            self.b.windows.append({'id':id+'.viewing_band','type':'spherical belt','fidelity':'photo-derived zone; simplified block joints'})
        if mode!='glass_control' and style in ('lower','upper'):
            # Coarse seams placed only in exterior empty cells; fine triangle grid omitted.
            for t in ([-.40,.56] if style=='lower' else [-.28]):
                rr=r*math.sqrt(1-t*t)+.45
                self.ring((center[0],center[1]+r*t,center[2]),rr,'iron_bars',id+'.seam')
    def construct(self,stage):
        p=self.p;b=self.b
        # Compact editable study plaza, not an as-built site plan.
        for y in range(3):b.disk(self.o[0],self.o[2],p['site']['radius_m']*self.s,y,'stone_bricks','site.foundation')
        self.disk((0,0,0),p['site']['radius_m'],'smooth_stone','site.paving')
        a0=math.radians(p['structure']['rotation_degrees'])
        axes=[np.array([math.cos(a0+i*2*math.pi/3),math.sin(a0+i*2*math.pi/3)]) for i in range(3)]
        R=p['structure']['tube_axis_radius_m'];foot=R+93/math.tan(math.pi/3)
        for i,v in enumerate(axes):
            x,z=v*R;fx,fz=v*foot
            self.tube((x,0,z),(x,284,z),4.5,'smooth_sandstone',f'structure.main_{i}',hollow=True)
            self.tube((fx,0,fz),(x,93,z),3.5,'smooth_sandstone',f'structure.slant_{i}')
            mid=v*(R+(93-45)/math.tan(math.pi/3))
            self.tube((x,0,z),(mid[0],45,mid[1]),2.5,'light_gray_concrete',f'structure.brace_{i}')
            self.record(f'structure.main_{i}','tube',axis_m=[x,z],diameter_m=9,height_m=284)
            self.record(f'structure.slant_{i}','tube',a_m=[fx,0,fz],b_m=[x,93,z],diameter_m=7)
        self.tube((0,118,0),(0,297,0),2.0,'light_gray_concrete','structure.middle')
        self.tube((0,290,0),(0,350,0),3.5,'smooth_sandstone','structure.upper_core')
        for h in p['structure']['beam_levels_m']:
            for i,v in enumerate(axes):
                self.tube((0,h,0),(v[0]*R,h,v[1]*R),2.3,'light_gray_concrete',f'structure.y_beam_{h}_{i}')
                # Narrow magenta band + slab floor on the visible connecting arms.
                self.tube((0,h+.8,0),(v[0]*R,h+.8,v[1]*R),1.0,'magenta_terracotta',f'structure.y_beam_trim_{h}_{i}')
        for h0,h1,r in [(350,382,2.0),(382,414,1.25),(414,444,.7)]:
            self.tube((0,h0,0),(0,h1,0),r,'iron_block','mast.segment')
        a=self.q((0,444,0));c=self.q((0,468,0));b.line(a-.5,c-.5,'iron_bars','mast.tip')
        for h,r in [(350,5),(382,3),(414,2)]:
            self.ring((0,h,0),r,'iron_bars','mast.ring')
            for dx,dz in [(r,0),(-r,0),(0,r),(0,-r)]:
                b.line(self.q((0,h,0))-.5,self.q((dx,h,dz))-.5,'iron_bars','mast.ring_spoke')
        if stage=='structure':return b
        for s in p['spheres']:self.sphere(s['id'],s['center_m'],s['diameter_m']/2,s['style'])
        for i,h in enumerate(p['small_spheres']['centers_m']):self.sphere(f'sphere.small_{i}',[0,h,0],6,'small')
        for i,v in enumerate(axes):
            mid=v*(R+(93-45)/math.tan(math.pi/3));self.sphere(f'sphere.base_{i}',[mid[0],45,mid[1]],5,'small')
        # 60m hall: simplified low radial canopy, stepped roof with a dark glazed edge.
        self.tube((0,1,0),(0,9,0),30,'gray_stained_glass','podium.wall',hollow=True)
        for h in np.arange(9,18,2.0):self.disk((0,h,0),30-(h-9)*1.8,'smooth_quartz','podium.canopy')
        # Open three short routes through the low hall shell. These are study entry interfaces.
        for i,v in enumerate(axes):
            for d in np.arange(0,75,.5):
                q=self.q((v[0]*d,0,v[1]*d));b.disk(q[0],q[2],1.6,int(self.o[1]),'polished_andesite',f'site.path_{i}')
            for d in np.arange(26,33,.5):
                q=self.q((v[0]*d,0,v[1]*d))
                for x in range(round(q[0])-1,round(q[0])+2):
                    for z in range(round(q[2])-1,round(q[2])+2):
                        for y in range(self.o[1]+1,self.o[1]+4):b.put(x,y,z,'minecraft:air',f'podium.entry_{i}')
        for j in range(12):
            t=j*math.pi/6+.18;r=66
            x,z=r*math.cos(t),r*math.sin(t)
            # Avoid support feet and paths.
            if any(abs(math.sin(t-(a0+i*2*math.pi/3)))<.17 for i in range(3)):continue
            self.disk((x,0,z),4.5,'moss_block','site.planting')
            self.disk((x,2,z),3,'azalea_leaves','site.shrub')
        # Embedded light slots. They emit vanilla white/warm light, not coloured floodlights.
        if p['lighting']['enabled']:
            for s in p['spheres'][:2]:
                cy=s['center_m'][1];rad=s['diameter_m']/2
                for j in range(12):
                    t=2*math.pi*j/12;r=rad*.88
                    q=self.q((r*math.cos(t),cy-rad*.45,r*math.sin(t)))
                    b.put(*q-.5,'sea_lantern',s['id']+'.lighting.slot')
            for i,v in enumerate(axes):
                for h in range(125,248,13):
                    q=self.q((v[0]*(R+4.1),h,v[1]*(R+4.1)))
                    b.put(*q-.5,'end_rod',f'lighting.tube_{i}')
        return b

def main():
    a=argparse.ArgumentParser();a.add_argument('--run',required=True);a.add_argument('--mode',choices=['layered','glass_control'],default='layered');a.add_argument('--stage',choices=['structure','complete'],default='complete');args=a.parse_args()
    p=json.loads((CASE/'parameters.json').read_text());p['shell_mode']=args.mode;p['stage']=args.stage
    tower=Pearl(p);b=tower.construct(args.stage)
    out=save_run(CASE,args.run,p,b,Path(__file__),{'route':'image_only_with_primary_paper','adapter_status':'case_specific','north_verified':False,'sphere_count':sum(x['kind']=='sphere' for x in tower.component_specs),'world_origin_y_max':320-p['size'][1],'sparse_air':True})
    dump(out/'components.json',tower.component_specs)
if __name__=='__main__':main()
