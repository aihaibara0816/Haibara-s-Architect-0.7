"""V3: centered inverted-T podium; preserve HAF and immutable V1/V2 adapters."""
from build_v2 import CustomsV2
from build_case import CASE, M, save_run, dump
from pathlib import Path
import argparse, collections, json

class CustomsV3(CustomsV2):
    def masks(self):
        # One explicit topology for both the mask and its outline-derived shell.
        rects=[c['rect'] for c in self.p['v3']['podium_components']]
        assert rects==self.p['v2']['podium_masses']
        super().masks()

    def window(self,x,z,normal,y,width,height,own,room=True):
        # Old case windows must not survive as floating panes after a setback.
        dx,dz=normal;tx,tz=dz,-dx
        for u in range(-(width//2),-(width//2)+width):
            xx,zz=x+tx*u,z+tz*u
            if not self.mass[y,zz,xx] or self.mass[y,zz+dz,xx+dx]:
                if not hasattr(self,'skipped_windows'):self.skipped_windows=[]
                self.skipped_windows.append(own)
                return
        super().window(x,z,normal,y,width,height,own,room)

    def podium(self):
        g=self.g
        for seg in self.p['v3']['podium_window_segments']:
            for fy in (0,5,10,15):
                for u in seg['centres']:
                    x,z=(u,seg['wall']) if seg['normal'][1] else (seg['wall'],u)
                    self.window(x,z,tuple(seg['normal']),g+fy+1,2,3,f"podium.{seg['id']}.{fy}.{u}",room=False)
        for x0,z0,x1,z1 in self.p['podium']['roof_tinted_regions']:
            for x in range(x0,x1):
                for z in range(z0,z1):
                    if self.mass[g+21,z,x] and not self.mass[g+22,z,x]:
                        self.put(x,g+21,z,'oxidized_copper','podium.roof.green_gray_proxy')
        for i,(x0,z0,x1,z1) in enumerate(self.p['podium']['glass_pavilions']):
            y0=g+22;y1=y0+self.p['podium']['pavilion_height']
            for y in range(y0,y1):
                for x in range(x0,x1):
                    for z in (z0,z1-1):
                        self.put(x,y,z,'smooth_quartz' if (x-x0)%5==0 or y in (y0+3,y1-1) else 'black_stained_glass_pane',f'podium.pavilion{i}.skin')
                for z in range(z0,z1):
                    for x in (x0,x1-1):
                        self.put(x,y,z,'smooth_quartz' if (z-z0)%4==0 or y in (y0+3,y1-1) else 'black_stained_glass_pane',f'podium.pavilion{i}.skin')
            self.box((x0,y1,z0),(x1,y1+1,z1),M('smooth_stone_slab'),f'podium.pavilion{i}.roof')
            for x in range(x0,x1,5):self.box((x,y1+1,z0),(x+1,y1+2,z1),M('smooth_quartz_slab'),f'podium.pavilion{i}.roof_rib')
        # A provisional three-arched rear portal centered on the longitudinal axis.
        ar=self.p['v3']['rear_portal'];z=ar['wall_z'];x0,x1=ar['span_x']
        self.box((x0,g+3,z),(x1,g+18,z+6),'air','podium.rear_portal.double_height_void')
        self.box((x0,g+2,z-2),(x1,g+3,z+7),'smooth_stone','podium.rear_portal.landing')
        for i,x in enumerate(ar['centres_x']):self.arch(x,z,(0,-1),7,3,12,f'podium.rear_portal.arch{i}')
        for x in (x0,x0+2,x1-3,x1-1):
            self.box((x,g+2,z-1),(x+1,g+18,z),'smooth_quartz','podium.rear_portal.pilaster')
        self.box((x0-1,g+18,z-2),(x1+1,g+20,z+1),'smooth_quartz','podium.rear_portal.entablature')
        for k in range(6):
            zz=z-8+k;yy=g+k//2
            self.box((x0,g-1,zz),(x1,yy,zz+1),'smooth_stone','podium.rear_portal.stair.support')
            self.box((x0,yy,zz),(x1,yy+1,zz+1),M('smooth_quartz_slab',type='top' if k%2 else 'bottom'),'podium.rear_portal.stair')
        self.box((61,g+3,z-1),(66,g+7,z+4),'air','podium.rear_portal.door')
        # Remove landscape left under the inherited front colonnade, retaining
        # front planting beyond its balustrade. This is site cleanup, not a new wing.
        for a,b in ((14,46),(81,113)):
            self.box((a,g,88),(b,g+13,97),'air','site.clear_front_colonnade')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name!=a.run or a.run in ('.','..'):ap.error('simple new run required')
    p=json.loads((a.params or CASE/'params_v3.json').read_text());b=CustomsV3(p).build()
    counts=collections.Counter(r['actual_lamp'] or 'off' for r in b.rooms)
    out=save_run(CASE,a.run,p,b,__file__,{'route':'image_only','three_dimensional_model_used':False,'building_height_envelope':137,'nominal_blocks_per_metre':1,'height_status':'study envelope, not surveyed','room_lighting_counts':dict(counts),'floor_schedule':b.floor_ys,'clock_face_count':4,'geographic_bearing':'unverified model axes','estimate_notice':p['estimates']})
    dump(out/'build_decisions.json',{'version':'V3','research':'research/v3/feedback_and_decisions.json','image_limit':None,'room_lights':dict(counts),'skipped_old_windows':getattr(b,'skipped_windows',[]),'previous_status':'V2 footprint rejected','visual_status':'pending user review','game_status':'pending'})
    for name in ('build_case.py','build_v2.py'):(out/('dependency_'+name)).write_bytes((CASE/'src'/name).read_bytes())

if __name__=='__main__':main()
