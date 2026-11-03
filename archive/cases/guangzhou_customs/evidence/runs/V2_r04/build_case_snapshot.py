"""Customs V2: component-resolved photo interpretation, reusing HAF 0.2.

V1 adapter remains unchanged. Dimensions are declared block hypotheses, not a
photogrammetric reconstruction. See research/v2/component_decisions.json.
"""
from build_case import Customs, CASE, M, save_run, dump, room_style, furnishing_cells, unit, first_clear_slot
from pathlib import Path
import argparse, collections, json, math
import numpy as np


class CustomsV2(Customs):
    def masks(self):
        p = self.p
        for r in p['v2']['podium_masses']:
            self.mark(r, 0, p['podium']['top'])
        for r in p['v2']['tower_masses']:
            self.mark(r, 22, p['tower']['wing_top'])
        self.mark(p['tower']['central_rect'], 22, p['tower']['wing_top'])
        self.mark(p['v2']['upper_center_rect'], p['tower']['wing_top'], p['tower']['center_top'])
        self.mass[self.g+22:self.g+96, 73:76, 57:70] = False
        self.mass[self.g+96:self.g+112, 74:76, 57:70] = False

    def shell_and_floors(self):
        g = self.g
        for y in range(g, g+self.p['tower']['center_top']):
            active = self.mass[y]
            interior = active.copy()
            for shift in (1, 2):
                for axis in (0, 1):
                    interior &= np.roll(active, shift, axis=axis)
                    interior &= np.roll(active, -shift, axis=axis)
            boundary = active & ~interior
            roof = active & ~self.mass[y+1]
            base = active & ~self.mass[y-1]
            for z, x in zip(*np.where(boundary | roof | base | (active if y in self.floor_ys else False))):
                body = 'podium' if y < g+22 else 'tower'
                material = (self.p['materials']['panel_stone'] if (int(x)+int(z))%5 == 0 else self.p['materials']['main_stone']) if boundary[z,x] else 'smooth_stone' if roof[z,x] else M('smooth_stone_slab',type='top')
                self.put(int(x),y,int(z),material,body+('.masonry' if boundary[z,x] else '.roof' if roof[z,x] else '.floor'))
        # Derive the podium cornice from its actual outline, including the notch.
        a=self.mass[g+20]
        for z,x in zip(*np.where(a)):
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                if not a[z+dz,x+dx]:
                    for dy,dist,mat in [(0,1,'smooth_quartz'),(1,1,M('smooth_quartz_slab',type='top')),(2,2,M('smooth_stone_slab'))]:
                        self.put(int(x+dx*dist),g+20+dy,int(z+dz*dist),mat,'podium.outline.cornice')
                    self.put(int(x),g+23,int(z),M('smooth_quartz_slab'),'podium.outline.parapet')
        for rect in self.p['v2']['tower_masses']:
            self.cornice(rect,g+103,'tower.shoulder.cornice')
            # Wrap the lower shoulder band around each volume, including sides/rear.
            x0,z0,x1,z1=rect
            for x in range(x0,x1):
                for z in (z0-1,z1):
                    self.put(x,g+94,z,M('smooth_quartz_slab',type='top'),'tower.shoulder.wrap_band')
            for z in range(z0,z1):
                for x in (x0-1,x1):
                    self.put(x,g+94,z,M('smooth_quartz_slab',type='top'),'tower.shoulder.wrap_band')
        self.cornice(self.p['v2']['upper_center_rect'],g+112,'tower.center.cornice')

    def tower_facades(self):
        t,g=self.p['tower'],self.g
        for fi,fy in enumerate(t['floor_levels']):
            if fy+3 >= t['wing_top']: continue
            y=g+fy+1
            for key,z,width in [('outer_pair_windows',t['outer_front_z'],3),('inner_windows',t['inner_front_z'],2),('center_edge_windows',t['center_front_z'],2),('center_windows',t['middle_front_z'],2)]:
                if key=='center_windows' and fy>=94:continue
                if key=='center_edge_windows' and fy==94:continue # solid crown balcony band
                for x in t[key]: self.window(x,z,(0,1),y,width,2,f'tower.front.{key}.f{fi}.x{x}')
            for band in self.p['v2']['rear_window_bands']:
                for x in band['xs']:
                    self.window(x,band['z'],(0,-1),y,2,2,f'tower.rear.f{fi}.x{x}')
            for x,n,side in [(25,(-1,0),'left'),(101,(1,0),'right')]:
                for z in self.p['v2']['side_window_zs']:
                    self.window(x,z,n,y,2,2,f'tower.{side}.f{fi}.z{z}')
            for x,n in [(50,(-1,0)),(76,(1,0))]:
                for z in (47,51):self.window(x,z,n,y,2,2,f'tower.reentrant.f{fi}.{x}.{z}',room=False)
        r=self.p['v2']['upper_center_rect'];x0,z0,x1,z1=r
        for fy in t['upper_floor_levels']:
            if fy!=110:
                for x in t['center_edge_windows']:self.window(x,75,(0,1),g+fy+1,2,2,f'tower.front.upper.{fy}.{x}',room=False)
            for x in (53,58,63,68,73):self.window(x,z0,(0,-1),g+fy+1,2,2,f'tower.rear.upper.{fy}.{x}',room=False)
            for x,n in [(x0,(-1,0)),(x1-1,(1,0))]:
                for z in (56,61,66,71):self.window(x,z,n,g+fy+1,2,2,f'tower.side.upper.{fy}.{x}.{z}',room=False)
        # Shallow panels are subordinate to real front/back mass setbacks.
        for a,b,z in [(38,50,70),(57,70,72),(77,89,70)]:
            for x in range(a+1,b,4 if a!=57 else 3):
                for y in range(g+23,g+94):
                    if (x,y,z) in self.s.blocks and 'glass' not in self.s.blocks[(x,y,z)]:self.put(x,y,z,'quartz_block','tower.front.recessed_panel')
        for x in (41,46,80,85):
            f=self.frame(x,70,(0,1))
            f.rect(-1,2,g+101,g+103,-2,1,'air','tower.attic.opening')
            f.rect(-1,2,g+101,g+102,-1,0,'black_stained_glass_pane','tower.attic.glass')
            f.put(0,g+102,-1,'black_stained_glass_pane','tower.attic.glass')

    def arch(self,x,z,n,width,bottom,spring,own):
        f=self.frame(x,z,n);r=width/2
        for u in range(-math.ceil(r)-1,math.ceil(r)+2):
            for yy in range(bottom,math.ceil(spring+r)+2):
                inside=abs(u)<=r and (yy<=spring or u*u+(yy-spring)**2<=r*r)
                ring=(abs(u)<=r+1 and yy<=spring) or (r*r<u*u+(yy-spring)**2<=(r+1)**2 and yy>=spring)
                if inside:
                    f.rect(u,u+1,self.g+yy,self.g+yy+1,-2,1,'air',own+'.opening')
                    f.put(u,self.g+yy,-1,'gray_stained_glass_pane',own+'.glass')
                    if yy==bottom+5 or u==0:f.put(u,self.g+yy,-1,'black_stained_glass_pane',own+'.transom')
                elif ring:f.put(u,self.g+yy,0,'smooth_quartz',own+'.ring')

    def podium(self):
        g=self.g
        # Different wall segments belong to different masses, not a single box.
        for seg in self.p['v2']['podium_window_segments']:
            for fy in (0,5,10,15):
                for u in seg['centres']:
                    x,z=(u,seg['wall']) if seg['normal'][1] else (seg['wall'],u)
                    self.window(x,z,tuple(seg['normal']),g+fy+1,2,3,f"podium.{seg['id']}.{fy}.{u}",room=False)
        for rect in self.p['podium']['roof_tinted_regions']:
            x0,z0,x1,z1=rect
            for x in range(x0,x1):
                for z in range(z0,z1):
                    if self.mass[g+21,z,x] and not self.mass[g+22,z,x]:self.put(x,g+21,z,'oxidized_copper','podium.roof.green_finish_proxy')
        for i,rect in enumerate(self.p['podium']['glass_pavilions']):
            x0,z0,x1,z1=rect;y0=g+22;y1=y0+self.p['podium']['pavilion_height']
            for y in range(y0,y1):
                for x in range(x0,x1):
                    for z in (z0,z1-1):self.put(x,y,z,'smooth_quartz' if (x-x0)%5==0 or y==y1-1 else 'black_stained_glass_pane',f'podium.pavilion{i}.skin')
                for z in range(z0,z1):
                    for x in (x0,x1-1):self.put(x,y,z,'smooth_quartz' if (z-z0)%5==0 or y==y1-1 else 'black_stained_glass_pane',f'podium.pavilion{i}.skin')
            self.box((x0,y1,z0),(x1,y1+1,z1),M('smooth_stone_slab'),f'podium.pavilion{i}.roof')
            for x in range(x0,x1,5):self.box((x,y1+1,z0),(x+1,y1+2,z1),M('smooth_quartz_slab'),f'podium.pavilion{i}.roof_rib')
        # Opposite side from the ordinary-window elevation in img-nc-13.
        ar=self.p['v2']['side_portal']
        for i,z in enumerate(ar['centres_z']):self.arch(ar['wall_x'],z,(-1,0),7,3,12,f'podium.side_portal.arch{i}')
        z0,z1=ar['span_z'];x=ar['wall_x']
        for z in (z0,z0+2,z1-3,z1-1):
            self.box((x-1,g+2,z),(x,g+18,z+1),'smooth_quartz','podium.side_portal.pilaster')
        self.box((x-2,g+18,z0-1),(x+1,g+20,z1+1),'smooth_quartz','podium.side_portal.entablature')
        for k in range(6):
            xx=x-8+k;yy=g+k//2
            self.box((xx,g-1,z0),(xx+1,yy,z1),'smooth_stone','podium.side_portal.stair.support')
            self.box((xx,yy,z0),(xx+1,yy+1,z1),M('smooth_quartz_slab',type='top' if k%2 else 'bottom'),'podium.side_portal.stair')
        self.box((x-1,g+3,61),(x+4,g+7,64),'air','podium.side_portal.door')
        # Remove the V1 landscape strip where it would obstruct the new stair.
        self.box((7,g,44),(10,g+11,83),'air','site.clear_side_portal')
        # Small entry in the recessed rear court, visible next to the projecting wing.
        self.box((44,g,26),(49,g+5,29),'air','podium.rear_court.door')
        self.box((42,g+6,23),(51,g+7,29),M('smooth_stone_slab'),'podium.rear_court.canopy')

    def entrance(self):
        super().entrance()
        g=self.g
        # Full colonnade flanks the central paired-column portal.
        for x0,x1 in ((14,46),(81,113)):
            self.box((x0,g+3,78),(x1,g+16,96),'air','entrance.side_colonnade.void')
            self.box((x0,g+2,78),(x1,g+3,96),'smooth_stone','entrance.side_colonnade.landing')
            self.box((x0,g+16,82),(x1,g+20,97),'smooth_quartz','entrance.side_colonnade.entablature')
            self.box((x0-1,g+20,81),(x1+1,g+21,98),M('smooth_quartz_slab'),'entrance.side_colonnade.cornice')
            for x in range(x0+3,x1,7):
                self.round_column(x,93,g+3,g+16,f'entrance.side_column.{x}',radius=1.1)
                self.arch(x,96,(0,1),3,17,18,f'entrance.attic_window.{x}')
            # Continuous set-back glazing behind the columns, with a horizontal transom.
            for x in range(x0+1,x1-1):
                for y in range(g+3,g+16):
                    mat='smooth_quartz' if (x-x0)%7==0 else 'black_stained_glass_pane' if y==g+9 else 'gray_stained_glass_pane'
                    self.put(x,y,80,mat,'entrance.side_colonnade.recessed_glazing')
            for x in range(x0,x1):
                for z in range(82,96):
                    if (x-x0)%4==0 or z%4==0:self.put(x,g+15,z,M('smooth_sandstone_slab',type='top'),'entrance.side_colonnade.coffered_soffit')
            for x in range(x0+3,x1,14):self.put(x,g+14,87,'glowstone','lighting.colonnade.warm')
            # Low balustrade; main stair remains unobstructed.
            f=self.frame(x0,96,(0,1))
            for u in range(x1-x0):
                f.put(u,g+3,1,M('smooth_quartz_slab'),'entrance.side_colonnade.balustrade.base')
                f.put(u,g+5,1,M('smooth_quartz_slab'),'entrance.side_colonnade.balustrade.rail')
                if u%3==0:f.put(u,g+4,1,'diorite_wall','entrance.side_colonnade.balustrade.baluster')
        # Metal-framed door panels and a coarse circular motif from the close photo.
        for x in (57,63,69):
            f=self.frame(x,84,(0,1))
            for u,v in [(-1,0),(0,-1),(1,0),(0,1)]:f.put(u,g+9+v,0,'iron_bars','entrance.door.ring_proxy')
        self.box((61,g+3,83),(66,g+7,86),'air','entrance.clear_entry')

    def crown(self):
        super().crown()
        g=self.g;x,z=self.p['crown']['clock_center_xz']
        # The clock has a tapered, stepped plinth; V1 placed it on a long empty roof.
        for y,r in [(113,10),(114,9),(115,8)]:
            for xx in range(x-r,x+r+1):
                for zz in range(z-r,z+r+1):
                    if abs(xx-x)>6 or abs(zz-z)>6:self.put(xx,g+y,zz,M('smooth_quartz_slab',type='top'),'clock.stepped_plinth')

    def interiors(self):
        # Reposition the synthetic stair before allocating furniture/lights.
        # The V1 stair at z=44 cut through the new rear wall: never reuse blindly.
        g=self.g
        for fy in self.p['tower']['floor_levels'][:-1]:
            yy=g+fy
            self.box((60,yy,55),(64,yy+1,64),'air','interior.service_stair.floor_void')
            for k in range(8):
                self.box((60,yy+1+k//2,56+k),(64,yy+2+k//2,57+k),M('smooth_stone_slab',type='top' if k%2 else 'bottom'),'interior.service_stair.tread')
            for k in range(9):self.put(64,yy+2+k//2,55+k,'iron_bars','interior.service_stair.rail')
        groups={};reserved=set()
        sensitive={q for q,s in self.s.blocks.items() if 'glass_pane' in s or 'iron_bars' in s}
        for w in self.windows:
            if not w['room_candidate'] or not w['id'].startswith('tower.'):continue
            x,wy,z=w['anchor'];dx,dz=w['normal_xz'];fy=wy-1;u=x if dz else z
            groups.setdefault((dx,dz,z if dz else x,fy,u//6),[]).append(w)
        for key,windows in sorted(groups.items()):
            w=windows[len(windows)//2];x,wy,z=w['anchor'];dx,dz=w['normal_xz'];fy=wy-1;tx,tz=dz,-dx
            rid='office.'+'.'.join(map(str,key))
            coords=[(x+tx*u-dx*d,fy+2,z+tz*u-dz*d) for u in (-2,2) for d in (2,7)]
            if not all(self.mass[yy,zz,xx] for xx,yy,zz in coords):continue
            if fy>=g+94 and 55<=x<=71 and dz==1:continue
            style=room_style(self.seed,rid,3,'office')
            for u in range(-2,3):
                for yy in range(fy+1,fy+4):self.put(x+tx*u-dx*7,yy,z+tz*u-dz*7,'light_gray_concrete','interior.'+rid+'.back',empty=True)
            for u,yy,d,m in furnishing_cells(style['style'],3):
                q=(x+tx*(u-2)-dx*(d+2),fy+1+yy,z+tz*(u-2)-dz*(d+2))
                if self.mass[q[1],q[2],q[0]]:self.put(*q,m,'interior.'+rid+'.furniture',empty=True)
            draw=unit(self.seed,rid,'occupancy',namespace=self.p['lighting']['namespace'])
            material=None if draw<.5 else 'glowstone' if draw<.75 else 'sea_lantern'
            candidates=[(x+tx*u-dx*d,fy+3,z+tz*u-dz*d) for d in (4,5,6) for u in (0,-1,1)]
            candidates=[q for q in candidates if self.mass[q[1],q[2],q[0]]]
            q=first_clear_slot(candidates,self.s.blocks,reserved,sensitive)
            if q is not None:reserved.add(q)
            placed=bool(material and q is not None and self.put(*q,material,'lighting.room.'+rid,empty=True))
            self.rooms.append({'id':rid,'floor_y':fy,'windows':[a['id'] for a in windows],'style':style['style'],'expected_material':material,'lamp_candidate':list(q) if q is not None else None,'lamp_position':list(q) if placed else None,'actual_lamp':material if placed else None,'fidelity':'synthetic office window-back; unknown real plan'})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name!=a.run or a.run in ('.','..'):ap.error('simple new run required')
    p=json.loads((a.params or CASE/'params_v2.json').read_text());b=CustomsV2(p).build()
    counts=collections.Counter(r['actual_lamp'] or 'off' for r in b.rooms)
    out=save_run(CASE,a.run,p,b,__file__,{'route':'image_only','three_dimensional_model_used':False,'building_height_envelope':137,'nominal_blocks_per_metre':1,'height_status':'study envelope, not surveyed','room_lighting_counts':dict(counts),'floor_schedule':b.floor_ys,'clock_face_count':4,'geographic_bearing':'model axes; unverified','estimate_notice':p['estimates']})
    dump(out/'build_decisions.json',{'version':'V2','source_module':'build_v2.py','v1_adapter_reused':'build_case.py','research':'research/v2/component_decisions.json','references_reviewed':11,'image_limit':None,'independent_view_count_claimed':False,'top_evidence':'satellite/OSM context inspected; no reliable measured roof plan','room_lights':dict(counts),'no_night_photo_claim':True,'fidelity_status':'awaiting user visual review and game import'})
    (out/'v1_dependency_snapshot.py').write_bytes((CASE/'src/build_case.py').read_bytes())

if __name__=='__main__':main()
