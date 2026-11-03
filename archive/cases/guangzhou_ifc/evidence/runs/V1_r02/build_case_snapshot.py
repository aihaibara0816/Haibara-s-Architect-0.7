"""Guangzhou IFC V1: evidence-led case adapter on unchanged HAF 0.3 primitives.

The outline is a manual trace of WE09, not recovered survey geometry. Height and
curvature use published design data. Room layouts and the cropped site are
explicit procedural approximations. No SU model is used.
"""
from pathlib import Path
import sys, json, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CASE=Path(__file__).resolve().parents[1]; ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder, M, erode
from hafusion.case_io import save_run, dump
from hafusion.lighting import room_lighting, unit
from detail_lab import states

NAMESPACE='ifc-v1-room-20261024'

def curve_trace():
    # Bottom plan in WE09 / old_01; image coordinates, manual uncertain trace.
    curves=[[(621,1032),(652,1035),(714,884),(719,790)],
            [(719,790),(723,750),(705,738),(673,743)],
            [(673,743),(573,749),(476,790),(442,827)],
            [(442,827),(426,846),(432,873),(451,897)],
            [(451,897),(510,969),(583,1021),(606,1029)],
            [(606,1029),(612,1031),(617,1032),(621,1032)]]
    pts=[]
    for c in curves:
        a,b,c,d=np.array(c,float)
        for t in np.linspace(0,1,80,endpoint=False):
            pts.append((1-t)**3*a+3*t*(1-t)**2*b+3*t*t*(1-t)*c+t**3*d)
    pts=np.array(pts);center=np.mean(pts,axis=0)
    # Use polygon area centroid, independent of segment sample density.
    nxt=np.roll(pts,-1,axis=0);cross=pts[:,0]*nxt[:,1]-nxt[:,0]*pts[:,1]
    center=np.sum((pts+nxt)*cross[:,None],axis=0)/(3*cross.sum())
    pts=(pts-center)/np.ptp(pts[:,0]);pts=np.vstack([pts,pts[0]])
    dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    samples=np.linspace(0,dist[-1],720,endpoint=False)
    return np.array([np.interp(samples,dist,pts[:,j]) for j in [0,1]]).T

class IFC(Builder):
    def __init__(self,p):
        super().__init__(p['frame']['size_xyz'],p['lighting']['seed'])
        self.p=p;self.cx,self.cz=p['frame']['center_xz'];self.grade=p['frame']['grade_y']
        self.trace=curve_trace();self.masks={};self.rings={};self.records={'entrances':[],'supports':[],'lights':[]}
        self.profile=[];self.diagrid_cells=set();self.room_slots=[]
        self.prepare_masks()

    def factor(self,h):
        t=self.p['tower'];offset=(h-t['widest_height_blocks'])**2/(2*t['vertical_radius_blocks'])
        return 1-offset/(t['maximum_width_blocks']/2)

    def point(self,u,h,inset=0):
        v=self.trace[int((u%1)*len(self.trace))]
        w=self.p['tower']['maximum_width_blocks']*self.factor(h)-2*inset
        return np.array([self.cx,self.cz])+v*w

    def mask(self,h,inset=0):
        w=self.p['tower']['maximum_width_blocks']*self.factor(h)-2*inset
        pts=self.trace*w+[self.cx-.5,self.cz-.5]
        im=Image.new('1',(self.s.size[0],self.s.size[2]));ImageDraw.Draw(im).polygon([tuple(v) for v in pts],fill=1)
        return np.asarray(im,dtype=bool)

    def prepare_masks(self):
        for h in range(self.p['tower']['glass_height_blocks']):
            y=self.grade+h;m=self.mask(h);e=erode(m)
            self.masks[y]=m;self.rings[y]=m&~e
            zz,xx=np.where(m)
            self.profile.append({'y':y,'width_x':int(np.ptp(xx)+1),'depth_z':int(np.ptp(zz)+1),'area':int(m.sum()),'factor':self.factor(h)})

    def surface_if(self,mask,y,mat,owner):self.surface(mask,y,mat,owner)

    def site(self):
        sx,sy,sz=self.s.size;g=self.grade
        # Deliberately cropped and estimated immediate setting, not full IFC parcel.
        for x in range(4,sx-4):
            for z in range(4,sz-4):
                road=x<12 or z>sz-15
                mat='gray_concrete' if road else 'polished_andesite' if x%9==0 or z%9==0 else 'smooth_stone'
                self.put(x,g-1,z,mat,'site.paving' if not road else 'site.dropoff')
                self.put(x,g-2,z,'stone_bricks','site.foundation')
        for z in range(15,sz-20,10):self.box((7,g-1,z),(8,g,z+4),'white_concrete','site.road_marks')
        for x in range(18,sx-15,4):self.box((x,g-1,sz-10),(x+2,g,sz-7),'white_concrete','site.crossing')
        for i,(x,z) in enumerate(self.p['site']['trees']):
            for xx in range(x-3,x+4):
                for zz in range(z-3,z+4):
                    edge=xx in [x-3,x+3] or zz in [z-3,z+3]
                    self.put(xx,g,zz,M('smooth_stone_slab') if edge else M('moss_block'),f'site.planter.{i}')
            self.tree(x,z,g+1,h=7,r=3)
            self.box((x-2,g+1,z+3),(x+2,g+2,z+4),M('dark_oak_slab'),f'site.bench.{i}')
        for i,(x,z) in enumerate([(17,83),(78,81),(79,29),(17,29)]):
            self.box((x,g,z),(x+1,g+4,z+1),'iron_bars',f'site.lamp.{i}.post')
            self.put(x,g+4,z,'glowstone',f'lighting.site.{i}')
            self.put(x,g+5,z,M('smooth_stone_slab'),f'site.lamp.{i}.cap')

    def podium(self):
        # Low entrance/retail interface only; the serviced-apartment tower omitted.
        g=self.grade;mask=Image.new('1',(self.s.size[0],self.s.size[2]));ImageDraw.Draw(mask).polygon(self.p['podium']['polygon'],fill=1)
        mask=np.asarray(mask,bool)&~self.mask(0,-1);edge=mask&~erode(mask)
        for y in [g,g+4,g+9]:self.surface(mask,y,M('smooth_stone_slab',type='top'),'podium.floor')
        for z,x in zip(*np.where(edge)):
            for y in range(g+1,g+9):
                mat='gray_stained_glass_pane' if (int(x)+int(z))%5 else 'polished_andesite'
                self.put(x,y,z,mat,'podium.glazing' if 'glass' in mat else 'podium.pier')
        self.surface(mask,g+10,M('smooth_stone_slab'),'podium.roof')
        # Setback green strips and roof equipment: bounded schematic completion.
        for x in range(27,64):
            for z in range(24,27):
                if mask[z,x]:self.put(x,g+11,z,'moss_block','podium.roof_garden')
        for x in [29,37,45,53]:
            for z in [20,29]:
                if mask[z,x]:self.put(x,g+8,z,'glowstone','lighting.podium')

    def floors_core_rooms(self):
        g=self.grade;hotel=g+self.p['tower']['hotel_lobby_blocks'];roof=g+self.p['tower']['glass_height_blocks']-1
        # Quantized floor elevations: not a claim of 103 playable Minecraft floors.
        floors=sorted(set([g,g+6]+[g+round(6+2.25*i) for i in range(1,66)]+[hotel+round(i*2.05) for i in range(31)]))
        floors=[y for y in floors if y<roof];self.floors=floors
        for y in range(g,roof):
            h=y-g;m=self.masks[y];inner=erode(m,2)
            atrium=self.mask(h, self.p['tower']['maximum_width_blocks']*self.factor(h)*.285) if y>=hotel else np.zeros_like(m)
            if y in floors:
                slab=M('polished_deepslate_slab',type='top') if y<hotel else M('smooth_quartz_slab',type='top')
                self.surface(inner&~atrium,y,slab,'interior.floor.office' if y<hotel else 'interior.floor.hotel')
                if y>=hotel:
                    rail=erode(atrium)&~erode(atrium,2)
                    self.surface(rail,y+1,'glass_pane','interior.atrium.balustrade')
            if y<hotel:
                core=self.mask(72,11.5);corewall=core&~erode(core)
                self.surface(corewall,y,'light_gray_concrete','interior.office_core')
                for xx in [self.cx-3,self.cx+2]:
                    self.put(xx,y,self.cz,'iron_bars','interior.lift_shaft')
                if y>g+6 and y not in floors:
                    back=erode(m,5)&~erode(m,6)
                    self.surface(back,y,'gray_concrete','interior.office_window_backs')
            else:
                # Hotel corridor screen sits outside the open central atrium.
                rim=erode(m,6)&~erode(m,7)&~atrium
                if y not in floors:self.surface(rim,y,'gray_concrete','interior.hotel_room_backs')
        # Stable synthetic bay identities; all furniture and light slots are behind glass.
        for fi,y in enumerate(floors[:-1]):
            ny=floors[fi+1]
            if y<g+6 or ny-y<2 or y>=roof-4:continue
            h=y-g;inner=erode(self.masks[y],3)
            for k in range(24):
                x,z=np.floor(self.point((k+.5)/24,h,3.4)).astype(int);rid=f'ifc.floor.{y:03d}.bay.{k:02d}'
                if not inner[z,x]:continue
                zone='hotel' if y>=hotel else 'office'
                # Avoid core and corridor boundaries; keep an actual empty viewing gap.
                yy=y+1;style=unit(self.seed,rid,'furniture',namespace=NAMESPACE)
                bx,bz=np.floor(self.point((k+.5)/24,h,5.2)).astype(int)
                if (bx,yy,bz) not in self.s.blocks:
                    mat=M('bookshelf') if style<.2 else M('oak_leaves') if style<.36 else M('anvil') if style<.48 else M('dark_oak_slab')
                    self.put(bx,yy,bz,mat,'interior.furniture.'+rid,empty=True)
                decision=room_lighting(self.seed,str(y),rid,zone,self.p['lighting']['room_activity'],namespace=NAMESPACE)
                self.room_slots.append({'q':[int(x),yy,int(z)],'id':rid,'decision':decision})
                self.rooms.append({'id':rid,'floor_y':y,'ceiling_y':ny,'zone':zone,'source':'synthetic, not surveyed rooms','furniture_sample':round(style,4),'light':decision})
                self.windows.append({'id':rid,'floor_y':y,'arc_fraction':(k+.5)/24,'depth_blocks':3.4})

    def structure(self):
        g=self.grade;top=self.p['tower']['glass_height_blocks'];families=self.p['diagrid']['lines_per_family'];period=self.p['diagrid']['diamond_height_blocks']
        for direction in [-1,1]:
            for k in range(families):
                previous=None
                for h in np.arange(0,top-.2,.25):
                    u=k/families+direction*h/(period*families)
                    x,z=self.point(u,h,2.25);q=(int(math.floor(x)),g+int(math.floor(h)),int(math.floor(z)))
                    if not self.masks[q[1]][q[2],q[0]] or self.rings[q[1]][q[2],q[0]]:continue
                    mat='smooth_quartz' if h<self.p['diagrid']['thin_above_blocks'] else 'diorite_wall'
                    self.put(*q,mat,f'structure.diagrid.{direction}.{k:02d}');self.diagrid_cells.add(q)
                    if h<.1:
                        self.put(q[0],g-1,q[2],'smooth_stone','structure.footing')
                        self.records['supports'].append({'id':f'diagrid.{direction}.{k}','x':q[0],'z':q[2],'foot_y':g})
        # Explicit wall arms only join the diagrid, not random nearby fixtures.
        for q in list(self.diagrid_cells):
            if 'diorite_wall' not in self.s.blocks[q]:continue
            props={}
            for name,(dx,dy,dz) in states.DIRS.items():
                props[name]='low' if (q[0]+dx,q[1],q[2]+dz) in self.diagrid_cells else 'none'
            self.put(*q,M('diorite_wall',**props),self.s.owners[q])

    def facade(self):
        g=self.grade;bands=self.p['lighting']['bands_local_y']
        for y,ring in self.rings.items():
            m=self.masks[y];h=y-g
            for z,x in zip(*np.where(ring)):
                x,z=int(x),int(z)
                # Straight runs use panes; raster turns use full glass to close diagonal cracks.
                neighbors=sum(bool(m[z+dz,x+dx]) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
                tangent=(ring[z,x-1] and ring[z,x+1]) or (ring[z-1,x] and ring[z+1,x])
                material=('glass_pane' if tangent else 'glass') if h<6 else ('gray_stained_glass_pane' if tangent else 'gray_stained_glass')
                if h>=209:material='gray_stained_glass_pane' if tangent else 'gray_stained_glass'
                self.put(x,y,z,material,'facade.glazing.lobby' if h<6 else 'facade.glazing.tower')
            # Recessed floor-edge bands; never add a protruding ring outside the silhouette.
            if y in self.floors and h>=6:
                inner=erode(m)&~erode(m,2)
                for z,x in zip(*np.where(inner)):
                    q=(int(x),y,int(z))
                    if q not in self.diagrid_cells:self.put(*q,M('polished_deepslate_slab',type='top'),'facade.recessed_spandrel')
        # Reserved, source-constrained illuminated mechanical bands. Interior only.
        for j,h0 in enumerate(bands):
            for h in [h0,h0+2]:
                y=g+h;m=erode(self.masks[y]);ring=m&~erode(m)
                for z,x in zip(*np.where(ring)):
                    q=(int(x),y,int(z))
                    if q in self.diagrid_cells:continue
                    mat='glowstone' if j in [0,2,4] else 'sea_lantern'
                    self.put(*q,mat,f'lighting.band.{j:02d}')
                    self.records['lights'].append({'xyz':list(q),'state':M(mat),'id':f'band.{j}'})

    def entrance(self):
        g=self.grade
        # Hotel entrance on the near side, canopy spans the actual facade at this cut.
        x0,x1=self.cx-5,self.cx+5;z0,z1=self.cz+12,self.cz+25
        for x in range(x0,x1+1):
            for z in range(z0,z1+1):
                self.put(x,g-1,z,'smooth_stone','entry.floor')
                for y in range(g,g+4):
                    self.put(x,y,z,'minecraft:air','entry.portal')
                self.put(x,g+5,z,M('smooth_stone_slab',type='top'),'entry.canopy.top')
                self.put(x,g+4,z,M('iron_trapdoor',half='top'),'entry.canopy.soffit')
                if x%3==0 and z<z1:self.put(x,g+4,z,'glowstone','lighting.entry.canopy')
        for x in [x0-1,x1+1]:
            self.put(x,g-1,z1-1,'smooth_stone','entry.column.footing')
            for y in range(g,g+5):self.put(x,y,z1-1,'diorite_wall','entry.column')
            self.records['supports'].append({'id':f'entry.{x}','x':x,'z':z1-1,'foot_y':g})
        for x in range(self.cx-2,self.cx+3):
            for z in range(z0,z1+1):
                self.records['entrances'].append({'x':x,'z':z,'floor_y':g-1,'clear_ys':[g,g+1,g+2]})
        # Small lobby reception and planted waiting edges, no oversized lettering.
        self.box((self.cx-9,g,self.cz+6),(self.cx-5,g+1,self.cz+8),'polished_andesite','entry.reception')
        for x in [self.cx-8,self.cx+8]:
            self.put(x,g,self.cz+11,'dark_oak_planks','entry.planter')
            self.put(x,g+1,self.cz+11,'oak_leaves','entry.plant')

    def crown(self):
        g=self.grade;h=self.p['tower']['glass_height_blocks'];y=g+h
        m=self.mask(h-1);inner=erode(m,2);atrium=self.mask(h-1,self.p['tower']['maximum_width_blocks']*self.factor(h-1)*.285)
        self.surface(m&~erode(m),y,M('polished_andesite_slab'),'crown.rim')
        self.surface(erode(m)&~atrium,y-1,M('smooth_stone_slab',type='top'),'crown.service_walk')
        self.surface(atrium,y-1,'glass','crown.atrium_skylight')
        for z,x in zip(*np.where(atrium)):
            if int(x)%4==0:self.put(x,y-1,z,'iron_bars','crown.skylight_frame')
        hx,hz=self.cx-2,self.cz-2;hy=g+218
        for dx,dz in [(-3,-2),(3,-2),(0,3)]:
            for yy in range(y,hy):self.put(hx+dx,yy,hz+dz,'iron_bars','crown.helipad_support')
            self.put(hx+dx,y-1,hz+dz,'smooth_stone','crown.support_bearing')
        self.disk(hx+.5,hz+.5,5.2,hy,M('smooth_stone_slab',type='top'),'crown.helipad')
        for dx in [-2,2]:
            for dz in range(-2,3):self.put(hx+dx,hy,hz+dz,M('quartz_slab',type='top'),'crown.pad_mark')
        for dx in range(-2,3):self.put(hx+dx,hy,hz,M('quartz_slab',type='top'),'crown.pad_mark')
        for dx,dz in [(5,0),(-5,0),(0,5),(0,-5)]:
            self.put(hx+dx,hy,hz+dz,'smooth_stone','crown.beacon_foot')
            self.put(hx+dx,hy+1,hz+dz,'redstone_torch','lighting.aviation')
        # Roof apparatus at two perimeter corners, leaving the skylight visible.
        for u in [.23,.57]:
            x,z=np.floor(self.point(u,h-1,2)).astype(int)
            self.put(x,y,z,'anvil','crown.bmu.base')
            self.line((x,y+1,z),(self.cx,y+1,self.cz),'iron_bars','crown.bmu.rail')

    def lights(self):
        # Applied last at reserved air cells; cannot replace glass, structure or doors.
        for row in self.room_slots:
            q=tuple(row['q']);dec=row['decision']
            if not dec['lit'] or q in self.s.blocks:continue
            if any(self.s.owners.get((q[0]+dx,q[1],q[2]+dz),'').startswith('facade.glazing') for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):continue
            self.put(*q,dec['material'],'lighting.room.'+row['id'])
            self.records['lights'].append({'xyz':list(q),'state':M(dec['material']),'id':row['id']})

    def build(self):
        for fn in [self.site,self.podium,self.floors_core_rooms,self.structure,self.facade,self.entrance,self.crown,self.lights]:
            print(fn.__name__,flush=True);fn()
        return self

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    p=json.loads((a.params or CASE/'params.json').read_text());b=IFC(p).build()
    out=save_run(CASE,a.run,p,b,Path(__file__),{'route':'unlimited_image_and_design_drawing_research','scale_blocks_per_m':.5,'tower_height_blocks':220,'bearing_status':'model frame only; geographic azimuth not calibrated','fidelity_status':'awaiting visual and user review','scope':'main tower, lobby and cropped immediate podium/site; no serviced-apartment tower or underground'})
    dump(out/'construction_records.json',b.records);dump(out/'profile.json',b.profile)
    dump(out/'floor_schedule.json',{'y_levels':b.floors,'status':'quantized illustrative floors, not 103 playable storeys'})
    dump(out/'geometry_controls.json',{'diagrid_family_count':2,'lines_per_family':p['diagrid']['lines_per_family'],'diamond_height_blocks':p['diagrid']['diamond_height_blocks'],'diagrid_cells_authored':len(b.diagrid_cells),'source_outline':'manual WE09 image-coordinate Bezier trace','perimeter_trace_normalized':b.trace[::12].tolist()})
if __name__=='__main__':main()
