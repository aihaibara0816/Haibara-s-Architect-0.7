"""N Seoul Tower V1: measured map/DEM + reviewed photographs, HAF 0.2.

This explicit case adapter is not automatic image reconstruction. Site x=east,
z=south, 1 block/metre. Fine terrace elevations, vegetation and hidden rooms are
authored approximations; the saved DEM is an approximately 30m surface model.
"""
from pathlib import Path
import argparse, collections, gzip, hashlib, json, math, random, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CASE=Path(__file__).resolve().parents[1]; HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.site_scene import SiteScene
from hafusion.lighting import unit, room_lighting
from hafusion.interiors import room_style, furnishing_cells
from vendor.voxel_core import export_structure
from vendor.inspect_build import load_build, Limits
from detail_lab import states
M=states.make
DIRS=[(1,0),(-1,0),(0,1),(0,-1)]

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def expanded(mask,r):
    return np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(2*r+1)))>0

def eroded(mask,r=1):
    return np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MinFilter(2*r+1)))>0

def edge(mask):return mask & ~eroded(mask)

class Builder:
    def __init__(self,p):
        self.p=p;self.f=p['frame'];self.s=SiteScene(tuple(self.f['size_xyz']))
        self.w,self.h,self.d=self.s.size; self.cx,self.cz=self.f['tower_xz'];self.g=self.f['tower_grade_y']
        self.seed=p['seed'];self.rooms=[];self.trees=[];self.route_records=[];self.beacons=[]
        self.nodes={};self.ways={};self.tags={}
        root=ET.parse(CASE/p['site']['osm_source']).getroot()
        for q in root.findall('node'):
            self.nodes[q.attrib['id']]=self.project(float(q.attrib['lon']),float(q.attrib['lat']))
        for q in root.findall('way'):
            key=int(q.attrib['id']);self.ways[key]=[self.nodes[n.attrib['ref']] for n in q.findall('nd')]
            self.tags[key]={v.attrib['k']:v.attrib['v'] for v in q.findall('tag')}

    def project(self,lon,lat):
        return (self.cx+(lon-self.f['longitude'])*111320*math.cos(math.radians(self.f['latitude'])),
                self.cz-(lat-self.f['latitude'])*111132)

    def polygon(self,points):
        im=Image.new('1',(self.w,self.d));ImageDraw.Draw(im).polygon(points,fill=1)
        return np.asarray(im,dtype=bool)

    def mask(self,key):return self.polygon(self.ways[key])

    def put(self,x,y,z,mat,owner,empty=False):
        q=(int(round(x)),int(round(y)),int(round(z)))
        if not(0<=q[0]<self.w and 0<=q[1]<self.h and 0<=q[2]<self.d):return
        if empty and q in self.s.blocks:return
        self.s.set(q,M(mat) if not mat.startswith('minecraft:') else mat,owner)

    def line(self,a,b,mat,owner):
        # Face-connected raster line; no unsupported diagonal-only bar islands.
        a=np.array(a,float);b=np.array(b,float);steps=max(1,int(np.max(np.abs(a-b))*3))
        prev=None
        for t in np.linspace(0,1,steps+1):
            q=tuple(int(round(v)) for v in a+(b-a)*t)
            if prev is not None:
                cur=list(prev)
                for axis in [1,0,2]:
                    while cur[axis]!=q[axis]:
                        cur[axis]+=1 if q[axis]>cur[axis] else -1
                        self.put(*cur,mat,owner)
            self.put(*q,mat,owner);prev=q

    def disk(self,cx,cz,r,y,mat,owner,inner=0):
        for z in range(math.floor(cz-r),math.ceil(cz+r)+1):
            for x in range(math.floor(cx-r),math.ceil(cx+r)+1):
                d=math.hypot(x+.5-cx,z+.5-cz)
                if inner<=d<=r:self.put(x,y,z,mat,owner)

    def ring_line(self,cx,cz,r,y,mat,owner,n=64):
        ps=[(cx+r*math.cos(i*math.tau/n),y,cz+r*math.sin(i*math.tau/n)) for i in range(n+1)]
        for a,b in zip(ps,ps[1:]):self.line(a,b,mat,owner)

    def surface(self,mask,y,mat,owner):
        for z,x in zip(*np.where(mask)):self.put(int(x),y,int(z),mat,owner)

    def prepare_site(self):
        data=json.loads((CASE/self.p['site']['terrain_source']).read_text());n=11
        grid=np.array([v['elevation'] for v in data['points']]).reshape(n,n)
        axis=np.arange(0,321,32);arr=np.array([np.interp(np.arange(self.w),axis,row) for row in grid])
        dem=np.array([np.interp(np.arange(self.d),axis,arr[:,x]) for x in range(self.w)]).T
        self.raw_dem=dem; self.grade=np.rint(dem-self.f['vertical_reference_m']).astype('int16')
        self.podium=self.mask(1214950317)
        self.upper=self.mask(1214950319)
        self.wood=self.mask(1214950314)
        self.lower=self.mask(1214950315)|self.mask(1214950320)
        self.path=np.zeros_like(self.grade,dtype=bool);self.path_wood=self.path.copy()
        # Authored terraces supersede coarse SRTM surface elevations only locally.
        for mask,y in [(self.upper,91),(self.wood,67),(self.lower,67)]:
            for r in range(6,0,-1):
                blend=expanded(mask,r)&~mask
                self.grade[blend]=np.rint(self.grade[blend]*(r/7)+y*(1-r/7))
            self.grade[mask]=y
        self.grade[self.podium]=self.g-1
        for key,pts in sorted(self.ways.items()):
            tags=self.tags[key];kind=tags.get('highway')
            if not kind or tags.get('area')=='yes':continue
            if kind not in {'service','footway','path','steps','pedestrian'}:continue
            radius=3 if kind=='service' else 1
            records=[]
            for a,b in zip(pts,pts[1:]):
                dist=math.hypot(b[0]-a[0],b[1]-a[1]);steps=max(1,int(dist*1.5))
                for t in np.linspace(0,1,steps+1):
                    x,z=(int(round(a[i]+(b[i]-a[i])*t)) for i in [0,1])
                    if not(0<=x<self.w and 0<=z<self.d) or self.podium[z,x]:continue
                    if records and records[-1][:2]==[x,z]:continue
                    records.append([x,z,int(self.grade[z,x])])
            # Smooth the sampled walk profile without assuming survey-grade stairs.
            for run in [records,list(reversed(records))]:
                for a,b in zip(run,run[1:]):
                    if abs(a[0]-b[0])+abs(a[1]-b[1])<=3:b[2]=max(a[2]-1,min(a[2]+1,b[2]))
            for x,z,y in records:
                for zz in range(max(0,z-radius),min(self.d,z+radius+1)):
                    for xx in range(max(0,x-radius),min(self.w,x+radius+1)):
                        if self.podium[zz,xx]:continue
                        if self.upper[zz,xx]:y=91
                        if self.lower[zz,xx] or self.wood[zz,xx]:y=67
                        self.grade[zz,xx]=y;self.path[zz,xx]=True
                        if tags.get('surface')=='wood':self.path_wood[zz,xx]=True
            if records:self.route_records.append({'osm_way':key,'kind':kind,'surface':tags.get('surface','unknown'),'profile_xzy':records})
        # Lower podium access is cleared, not left behind the DEM's building lump.
        self.grade[self.podium]=self.g-1
        self.reserved=expanded(self.podium|self.upper|self.lower|self.wood|self.path,4)
        for key,t in self.tags.items():
            if t.get('building') and key in self.ways and len(self.ways[key])>=3:
                self.reserved|=expanded(self.mask(key),4)
        self.terrain_meta={'raw_min_m':float(dem.min()),'raw_max_m':float(dem.max()),'resolution_m_approx':30,
            'sample_grid':[11,11],'sample_spacing_m':32,'block_surface_range_y':[int(self.grade.min()),int(self.grade.max())],
            'authored_terraces':[{'component':'site.upper_plaza','surface_y':91},{'component':'site.lower_plaza','surface_y':67},{'component':'podium.roof','surface_y':87}],
            'method':'Bilinear interpolation of saved SRTM samples; mapped plaza footprints with manually interpreted level corrections',
            'caveat':'SRTM includes canopy/building biases; no centimeter-grade survey or whole-park recreation'}

    def terrain(self):
        h=self.grade
        # A closed visual shell with a bottom and cut-edge walls, not solid geology.
        for z in range(self.d):
            for x in range(self.w):
                top=int(h[z,x]);bottom=max(1,top-2)
                if x in [0,self.w-1] or z in [0,self.d-1]:bottom=1
                else:bottom=max(1,min(bottom,int(min(h[z,x-1],h[z,x+1],h[z-1,x],h[z+1,x]))-1))
                self.put(x,0,z,'stone_bricks','terrain.bottom')
                for y in range(bottom,top):self.put(x,y,z,'dirt' if y>=top-1 else 'polished_andesite','terrain.shell')
                paved=self.path[z,x] or self.upper[z,x] or self.lower[z,x]
                wood=(self.path_wood[z,x] and not self.upper[z,x]) or self.wood[z,x]
                mat='dark_oak_planks' if wood else ('polished_andesite' if (x+z)%13==0 else 'smooth_stone') if paved else 'grass_block'
                if self.path[z,x] and not wood and not(self.upper[z,x] or self.lower[z,x]) and 0<x<self.w-1 and 0<z<self.d-1:
                    lower=[(dx,dz) for dx,dz in DIRS if int(h[z+dz,x+dx])==top-1]
                    if lower:
                        dx,dz=lower[0];facing='west' if dx==1 else 'east' if dx==-1 else 'north' if dz==1 else 'south'
                        mat=M('polished_andesite_stairs',facing=facing)
                self.put(x,top,z,mat,'site.wood_walk' if wood else 'site.paving' if paved else 'terrain.grass')
        # Sparse warm park fixtures, deliberately separate from interior activity.
        occupied=[]
        for route in self.route_records:
            for x,z,y in route['profile_xzy'][::22]:
                if not(7<x<self.w-7 and 7<z<self.d-7) or self.podium[z,x] or self.upper[z,x]:continue
                if any((x-a)**2+(z-b)**2<15**2 for a,b in occupied):continue
                xx=x+3
                if self.reserved[z,xx] and not self.path[z,xx]:continue
                y=int(self.grade[z,xx]);occupied.append((xx,z))
                self.line((xx,y+1,z),(xx,y+3,z),'iron_bars','site.path_lights.pole')
                self.put(xx,y+4,z,'glowstone','site.path_lights.lamp')
                self.put(xx,y+5,z,M('dark_oak_slab'),'site.path_lights.cap')
        self.path_lamp_count=len(occupied)

    def furniture(self,mask,y,zone,prefix,step=9):
        for z in range(5,self.d-5,step):
            for x in range(5,self.w-5,step):
                if not mask[z:z+5,x:x+5].all():continue
                rid=f'{prefix}.{x}.{z}';style=room_style(self.seed,rid,3,zone)
                decision=room_lighting(self.seed,prefix,rid,zone,self.p['lighting']['activity'],namespace='namsan-light-0.1')
                installed=[]
                for xx,yy,zz,mat in furnishing_cells(style['style'],3):
                    q=(x+xx,y+1+yy,z+zz)
                    if q not in self.s.blocks and (q[0],q[1]-1,q[2]) in self.s.blocks:
                        self.put(*q,mat,prefix+'.furniture');installed.append([*q,mat])
                if decision['lit']:
                    q=(x+2,y+4,z+2)
                    if q not in self.s.blocks:self.put(*q,decision['material'],prefix+'.light')
                self.rooms.append({'id':rid,'style':style['style'],'furniture':installed,'lighting':decision,'fidelity':'synthetic visitor/cafe fitout; not real room survey'})

    def podium_build(self):
        mask=self.podium;outer=edge(mask);inner=eroded(mask,3);skin=edge(inner)
        for floor in range(5):
            y=self.g+floor*5
            self.surface(mask,y,M('smooth_quartz_slab',type='top'),'podium.floor.'+str(floor))
            if floor==4:break
            for z,x in zip(*np.where(skin)):
                multi=sum(not inner[z+dz,x+dx] for dx,dz in DIRS)>1
                for yy in range(y+1,y+5):
                    self.put(int(x),yy,int(z),'gray_stained_glass' if multi else 'gray_stained_glass_pane','podium.glazing')
            for z,x in zip(*np.where(outer)):
                for yy in range(y+1,y+5):
                    if (int(x)+2*int(z))%7==0:self.put(int(x),yy,int(z),'dark_oak_planks','podium.bronze_fins')
                if floor>0:self.put(int(x),y+1,int(z),'glass_pane','podium.terrace_guardrail')
            # A fine soffit grid is visible beneath the projecting terraces.
            for z,x in zip(*np.where(mask&~inner)):
                if (int(x)+int(z))%4==0:self.put(int(x),y+4,int(z),M('iron_trapdoor',half='top'),'podium.soffit')
                if (int(x)+int(z)*2)%23==0:self.put(int(x),y+4,int(z),'glowstone' if floor%2==0 else 'sea_lantern','podium.fixed_terrace_light')
            self.furniture(eroded(inner,2),y,'hotel','podium.interior.'+str(floor))
            for z in range(135,201,8):
                for x in range(130,193,8):
                    if inner[z,x]:
                        for yy in range(y+1,y+5):self.put(x,yy,z,'smooth_quartz','podium.support_column')
        # North roof connects to the higher pavilion square, in short terraces.
        for z,x in zip(*np.where(mask)):
            if z>=158:continue
            top=min(91,87+(158-int(z))//4)
            for y in range(88,top+1):self.put(int(x),y,int(z),'smooth_stone','podium.upper_roof_steps')
        for z,x in zip(*np.where(outer)):
            if z>158:self.put(int(x),88,int(z),'glass_pane','podium.roof_guardrail')
        # Switchback exterior stair, observed as a separate layer outside glazing.
        for level in range(4):
            y0=self.g+level*5
            for step in range(15):
                z=193-step if level%2==0 else 179+step
                y=y0+step//3+1
                for x in range(197,201):self.put(x,y,z,M('smooth_quartz_stairs',facing='north' if level%2==0 else 'south'),'podium.external_stair')
                self.put(201,y+1,z,'iron_bars','podium.external_stair.railing')
            z=178 if level%2==0 else 194
            for xx in range(196,202):
                for zz in range(z,z+2):self.put(xx,y0+5,zz,M('smooth_quartz_slab',type='top'),'podium.stair_landing')
        # Glazed external lift shaft on the east corner, geometry only (no mechanism).
        for y in range(self.g,88):
            for x in range(192,197):
                for z in range(163,168):
                    if x in [192,196] or z in [163,167]:self.put(x,y,z,'smooth_quartz' if x in [192,196] and z in [163,167] else 'light_blue_stained_glass','podium.lift')
        # T1/T2 round glazed visitor building sitting above the commercial terraces.
        for y in [87,92,97]:self.disk(self.cx,self.cz,12,y,M('smooth_quartz_slab',type='top'),'podium.round_visitor.floor',inner=4.5)
        for y in list(range(88,92))+list(range(93,97)):
            self.disk(self.cx,self.cz,11.4,y,'gray_stained_glass','podium.round_visitor.glass',inner=10.5)
        for deg in range(0,360,30):
            a=math.radians(deg);x=self.cx+11*math.cos(a);z=self.cz+11*math.sin(a)
            self.line((x,88,z),(x,96,z),'iron_bars','podium.round_visitor.mullion')
            self.put(self.cx+8*math.cos(a),91,self.cz+8*math.sin(a),'glowstone' if deg%60==0 else 'sea_lantern','podium.round_visitor.light')
        for a in np.linspace(0,math.tau,12,endpoint=False):
            x=int(self.cx+8*math.cos(a));z=int(self.cz+8*math.sin(a));self.put(x,88,z,'dark_oak_slab','podium.round_visitor.table')
        # A small roof deck with locks represented as sparse coloured tokens.
        for x in range(141,181):
            for z in range(198,202):
                if mask[z,x]:self.put(x,88,z,'dark_oak_slab','podium.lock_terrace.deck')
        for x in range(145,181):
            if mask[199,x]:
                self.put(x,89,199,'iron_bars','podium.lock_terrace.railing')
                if x%4==0:self.put(x,90,199,'red_stained_glass_pane' if x%8 else 'yellow_terracotta','podium.lock_terrace.tokens')
        # Ground visitor entrance: remove three glass rows, keep its slab and header.
        for x in range(164,170):
            zs=np.where(skin[:,x])[0]
            if not len(zs):continue
            z=int(zs.max())
            for yy in range(self.g+1,self.g+4):
                self.s.set((x,yy,z),'minecraft:air','podium.visitor_entry')

    def tower(self):
        t=self.p['tower'];g=self.g;cx,cz=self.cx,self.cz
        # Hollow concrete core, full floors only at defined inhabited levels.
        for v in range(0,t['pod_lower']+2):
            r=t['shaft_radius_base']+(t['shaft_radius_top']-t['shaft_radius_base'])*v/t['pod_lower']
            self.disk(cx,cz,r,g+v,'white_concrete','tower.shaft',inner=max(0,r-1.3))
        # Core floors stop inside the wall. A larger disk would overwrite the
        # white envelope and produce false horizontal marks on the real shaft.
        for v in range(0,111,8):self.disk(cx,cz,2.5,g+v,'smooth_stone','tower.core_service_floor')
        for h in t['equipment_rings']:
            y=g+h
            self.ring_line(cx,cz,8.5,y,M('iron_trapdoor',half='top'),'tower.radio_ring.open_edge')
            self.ring_line(cx,cz,8.5,y+1,'iron_bars','tower.radio_ring.guardrail')
            for a in np.linspace(0,math.tau,16,endpoint=False):
                self.line((cx+4*math.cos(a),y,cz+4*math.sin(a)),(cx+8.5*math.cos(a),y,cz+8.5*math.sin(a)),M('iron_trapdoor',half='top'),'tower.radio_ring.radial_spoke')
        for a in np.linspace(0,math.tau,8,endpoint=False):
            x=cx+6*math.cos(a);z=cz+6*math.sin(a)
            self.line((x,g+49,z),(x,g+60,z),'iron_bars','tower.radio_ring.vertical')
            self.put(x,g+53,z,'smooth_quartz','tower.radio_equipment.dish_approx')
            self.put(x,g+54,z,'white_stained_glass','tower.radio_equipment.dish_approx')
        # Inverted bowl with radial beams, not a cylindrical cap on a stick.
        for v in range(105,111):
            r=5+(v-105)*(t['pod_radius']-5)/5
            self.disk(cx,cz,r,g+v,'gray_concrete','tower.pod.bowl',inner=max(4,r-1.3))
        for a in np.linspace(0,math.tau,24,endpoint=False):
            self.line((cx+4*math.cos(a),g+105,cz+4*math.sin(a)),(cx+12.6*math.cos(a),g+110,cz+12.6*math.sin(a)),'iron_bars','tower.pod.soffit_rib')
        for y in [110,115,120,124]:self.disk(cx,cz,t['pod_radius'],g+y,M('smooth_stone_slab',type='top'),'tower.pod.floor',inner=4)
        for v in range(111,124):
            material='light_gray_concrete' if v in [114,119,123] else 'light_blue_stained_glass'
            self.disk(cx,cz,t['pod_radius'],g+v,material,'tower.pod.envelope',inner=t['pod_radius']-1)
        for a in np.linspace(0,math.tau,32,endpoint=False):
            x=cx+12.9*math.cos(a);z=cz+12.9*math.sin(a)
            self.line((x,g+110,z),(x,g+124,z),'iron_bars','tower.pod.mullion')
        for v in range(125,132):
            self.disk(cx,cz,9.2,g+v,'light_gray_concrete' if v in [128,131] else 'gray_stained_glass','tower.restaurant.envelope',inner=8.2)
        for y,r in [(124,9.4),(128,9.4),(132,10.0),(134,6.4),(135,5.0)]:self.disk(cx,cz,r,g+y,M('smooth_quartz_slab',type='top'),'tower.restaurant.floor',inner=2)
        for v in [133,134]:self.disk(cx,cz,8-(v-133)*2,g+v,'gray_concrete','tower.restaurant.roof',inner=4)
        for fy,radius in [(110,10),(115,10),(120,10),(124,7),(128,7)]:
            for i,a in enumerate(np.linspace(0,math.tau,16,endpoint=False)):
                rid=f'tower.pod.{fy}.bay.{i}';decision=room_lighting(self.seed,fy,rid,'hotel',.82,namespace='namsan-light-0.1')
                if decision['lit']:self.put(cx+radius*math.cos(a),g+fy+3,cz+radius*math.sin(a),decision['material'],'tower.pod.interior_light')
                self.put(cx+(radius-1)*math.cos(a),g+fy+1,cz+(radius-1)*math.sin(a),'dark_oak_slab' if i%4 else 'bookshelf','tower.pod.furniture')
                self.rooms.append({'id':rid,'lighting':decision,'fidelity':'synthetic visitor fitout'})
        self.mast(cx,cz,g+136,100,3.5,'tower.antenna',primary=True)

    def beacon(self,x,y,z,owner):
        self.put(x,y,z,'glowstone',owner+'.emitter')
        for dx,dz in DIRS:self.put(x+dx,y,z+dz,'red_stained_glass_pane',owner+'.red_housing')
        self.put(x,y+1,z,M('iron_trapdoor'),'antenna.beacon.cap')
        self.beacons.append({'xyz':[int(round(x)),int(round(y)),int(round(z))],'owner':owner,'mode':'static decorative light; no regulatory or flashing simulation'})

    def mast(self,cx,cz,y0,height,radius,prefix,primary=False):
        # Each stage is open: four tapering legs, cross-bracing and small platforms.
        for v in range(height):
            r=max(.45,radius*(1-v/height)**.85)
            red=(v//13)%2==0
            mat='red_concrete' if red and r>1.1 else 'diorite_wall' if r>1.1 else 'iron_bars'
            for sx,sz in [(1,1),(1,-1),(-1,1),(-1,-1)]:self.put(cx+sx*r,y0+v,cz+sz*r,mat,prefix+'.leg')
            if v%7==0 and r>1:
                for a,b in [((-1,-1),(1,-1)),((1,-1),(1,1)),((1,1),(-1,1)),((-1,1),(-1,-1))]:
                    self.line((cx+a[0]*r,y0+v,cz+a[1]*r),(cx+b[0]*r,y0+v,cz+b[1]*r),'iron_bars',prefix+'.horizontal')
                r2=max(.45,radius*(1-min(height-1,v+7)/height)**.85)
                for a,b in [((-1,-1),(1,-1)),((1,1),(-1,1)),((-1,1),(-1,-1)),((1,-1),(1,1))]:
                    self.line((cx+a[0]*r,y0+v,cz+a[1]*r),(cx+b[0]*r2,y0+min(height-1,v+7),cz+b[1]*r2),'iron_bars',prefix+'.brace')
            if v in [4,30,57,78]:
                self.ring_line(cx,cz,r+1,y0+v,M('iron_trapdoor'),prefix+'.maintenance_platform',n=24)
                if primary:self.beacon(cx+r+1,y0+v+1,cz,prefix+'.beacon.'+str(v))
        # Last occupied block stays within the declared 237m tower envelope.
        self.put(cx,y0+height,cz,'redstone_torch',prefix+'.tip_light')
        for v in [10,17,25]:
            for side in [-1,1]:
                self.line((cx+side*(radius+1),y0+v,cz-2),(cx+side*(radius+1),y0+v,cz+2),'iron_bars',prefix+'.aerial_array')

    def pavilion_and_landmarks(self):
        pts=self.ways[1555991263];cx=sum(x for x,z in pts[:-1])/len(pts[:-1]);cz=sum(z for x,z in pts[:-1])/len(pts[:-1])
        # Survey footprint is ~6m; 2m eaves and stepped stone plinth are photo-derived.
        y=91
        for lev,r in [(0,8),(1,7),(2,6),(3,5)]:self.disk(cx,cz,r,y+lev,'stone_bricks','park.pavilion.plinth')
        self.disk(cx,cz,4.5,y+4,'dark_oak_planks','park.pavilion.floor')
        for a in np.linspace(math.pi/8,math.tau+math.pi/8,8,endpoint=False):
            x=cx+3.3*math.cos(a);z=cz+3.3*math.sin(a)
            self.line((x,y+4,z),(x,y+8,z),'red_terracotta','park.pavilion.column')
        self.ring_line(cx,cz,4,y+8,'moss_block','park.pavilion.painted_beam',n=8)
        for lev,r in [(9,6.2),(10,5.4),(11,4.0),(12,2.7),(13,1.5)]:
            poly=[(cx+r*math.cos(a),cz+r*math.sin(a)) for a in np.linspace(math.pi/8,math.tau+math.pi/8,8,endpoint=False)]
            self.surface(self.polygon(poly),y+lev,M('polished_deepslate_slab'),'park.pavilion.roof')
        for a in np.linspace(math.pi/8,math.tau+math.pi/8,8,endpoint=False):
            self.put(cx+6.2*math.cos(a),y+10,cz+6.2*math.sin(a),M('polished_deepslate_stairs',half='top'),'park.pavilion.raised_eave')
        self.put(cx,y+14,cz,'diorite_wall','park.pavilion.finial');self.put(cx,y+8,cz,'glowstone','park.pavilion.light')
        # Historic stone beacon: footprint from OSM, five cylindrical mouths from photo.
        mask=self.mask(378371654);zs,xs=np.where(mask);by=int(np.median(self.grade[mask]))
        for yy in range(by,by+4):self.surface(mask,yy,'stone_bricks','park.historic_beacon.base')
        for i in range(5):
            xx=int(xs.min()+2+i*(xs.max()-xs.min()-4)/4);zz=int(np.median(zs))
            for lev,r in [(0,1.8),(1,1.8),(2,1.5),(3,1.2)]:self.disk(xx,zz,r,by+4+lev,'polished_deepslate','park.historic_beacon.chimney',inner=.5 if lev==3 else 0)
        # Existing secondary communications mast, community-map height 60m.
        mask=self.mask(238866254);zs,xs=np.where(mask);mx=int(np.mean(xs));mz=int(np.mean(zs));my=int(np.median(self.grade[mask]))
        self.surface(mask,my,'smooth_stone','park.secondary_mast.pad')
        self.mast(mx,mz,my+1,59,7.8,'park.secondary_mast')
        self.beacon(mx,my+49,mz,'park.secondary_mast.beacon')
        # Cablecar upper station and small service buildings; no lower station.
        for key in [304260844,468254355,1214950318,1214950311,1214950312,1554014025,1554015589,1554015590]:
            mask=self.mask(key);base=int(np.median(self.grade[mask]));rim=edge(mask);height=7 if key==304260844 else 4
            self.surface(mask,base,'smooth_stone',f'park.building.{key}.floor')
            for yy in range(base+1,base+height):
                for z,x in zip(*np.where(rim)):
                    self.put(int(x),yy,int(z),'gray_stained_glass_pane' if yy<base+4 and (int(x)+int(z))%5 else 'light_gray_concrete',f'park.building.{key}.wall')
            self.surface(mask,base+height,M('smooth_stone_slab'),f'park.building.{key}.roof')
            zs,xs=np.where(mask);self.put(int(np.median(xs)),base+height-1,int(np.median(zs)),'glowstone',f'park.building.{key}.light')
        # Short visible cable continuation, anchored at the mapped station and site edge.
        for a,b in zip(self.ways[61855801],self.ways[61855801][1:]):
            if not(0<=a[0]<self.w and 0<=a[1]<self.d):continue
            x,z=map(lambda v:int(round(v)),a);y=int(self.grade[z,x])+10
            if b[1]<0:
                t=(a[1]-2)/(a[1]-b[1]);ex=a[0]+(b[0]-a[0])*t;ez=2;ey=max(4,y-int(math.hypot(ex-a[0],ez-a[1])*.32))
                for dx in [-1,1]:self.line((a[0]+dx,y,a[1]),(ex+dx,ey,ez),'chain','park.cablecar.cable_segment')
        # Benches and planters at the square, positioned away from pavilion stairs.
        for x,z in [(132,113),(147,102),(187,106),(198,119),(155,134),(209,168),(219,184)]:
            y=int(self.grade[z,x]);self.line((x,y+1,z),(x+4,y+1,z),M('dark_oak_stairs',facing='north'),'park.bench')
            for xx in [x-2,x+6]:
                self.put(xx,y+1,z,'dark_oak_planks','park.planter');self.put(xx,y+2,z,'azalea_leaves','park.planter')

    def forest(self):
        rng=random.Random(self.seed);centres=[];target=self.p['site']['tree_count_target']
        for _ in range(22000):
            if len(centres)>=target:break
            x=rng.randrange(7,self.w-7);z=rng.randrange(7,self.d-7)
            if self.reserved[z,x] or any((x-a)**2+(z-b)**2<8.0**2 for a,b in centres):continue
            r=rng.choice([3.3,3.8,4.4,4.9]);height=rng.randrange(8,15);y=int(self.grade[z,x])
            if self.reserved[max(0,z-3):min(self.d,z+4),max(0,x-3):min(self.w,x+4)].any():continue
            centres.append((x,z));tid=f'park.tree.{x}.{z}';self.line((x,y+1,z),(x,y+height-2,z),'oak_log',tid+'.trunk')
            for branch in range(3):
                a=rng.random()*math.tau;self.line((x,y+height-5,z),(x+2*math.cos(a),y+height-2,z+2*math.sin(a)),'oak_log',tid+'.branch')
            for yy in range(y+height-5,y+height+3):
                for zz in range(z-math.ceil(r),z+math.ceil(r)+1):
                    for xx in range(x-math.ceil(r),x+math.ceil(r)+1):
                        ell=((xx-x)/r)**2+((zz-z)/r)**2+((yy-(y+height-1))/4.5)**2
                        if ell<1 and not self.reserved[zz,xx]:self.put(xx,yy,zz,'azalea_leaves' if len(centres)%7==0 else 'oak_leaves',tid+'.crown',empty=True)
            self.trees.append({'id':tid,'base_xyz':[x,y+1,z],'height':height,'crown_radius':r,'source':'procedural forest distribution, not surveyed individual trees'})

    def build(self):
        self.prepare_site()
        for name,fn in [('terrain',self.terrain),('podium',self.podium_build),('tower',self.tower),('landmarks',self.pavilion_and_landmarks),('forest',self.forest)]:
            fn();print(name,len(self.s.blocks),flush=True)
        self.connection_updates=states.connect(self.s)
        for s in set(self.s.blocks.values()):states.validate(s)
        return self.s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name!=a.run or a.run in ['.','..']:ap.error('new run name required')
    out=CASE/'runs'/a.run
    if out.exists():raise SystemExit('Refusing to overwrite an existing run: '+str(out))
    out.mkdir(parents=True);p=json.loads((a.params or CASE/'params.json').read_text());dump(out/'params_used.json',p)
    b=Builder(p);scene=b.build();print('exporting',flush=True)
    meta=export_structure(scene,out/'building.nbt',include_air=False)
    print('reading exported NBT',flush=True)
    rb=load_build(out/'building.nbt',Limits(cells=40_000_000,nodes=12_000_000))
    assert rb.blocks==scene.blocks and rb.size==scene.size
    tower_points=[q for q,o in scene.owners.items() if o.startswith('tower.')]
    top=max(q[1] for q in tower_points);assert top==p['frame']['tower_grade_y']+p['tower']['height_blocks']-1,(top,p['frame']['tower_grade_y'])
    materials=collections.Counter(s.split('[')[0] for s in rb.blocks.values())
    components=collections.Counter(o.split('.')[0] for o in scene.owners.values())
    (out/'materials.csv').write_text('block_id,count,stacks,remainder\n'+''.join(f'{k},{v},{v//64},{v%64}\n' for k,v in sorted(materials.items())),encoding='utf-8-sig')
    # Ownership is separate provenance, never silently encoded as game entities.
    owner_names=sorted(set(scene.owners.values()));owner_ids={s:i for i,s in enumerate(owner_names)}
    with gzip.open(out/'component_ownership.json.gz','wt',encoding='utf8') as f:json.dump({'owner_names':owner_names,'xyz_owner':[[*q,owner_ids[o]] for q,o in sorted(scene.owners.items())]},f,separators=(',',':'))
    np.save(out/'terrain_height_y.npy',b.grade);np.save(out/'dem_interpolated_m.npy',b.raw_dem)
    dump(out/'site_profile.json',{'terrain':b.terrain_meta,'routes':b.route_records,'trees':b.trees,'path_lamps':b.path_lamp_count})
    dump(out/'interior_lighting.json',{'seed':p['seed'],'rooms':b.rooms,'beacons':b.beacons})
    dump(out/'manifest.json',{**meta,'case':'namsan_tower','engine':'HAF 0.2.0','run':a.run,'components':dict(components),'material_types':len(materials),'state_count':len(set(rb.blocks.values())),
        'tree_count':len(b.trees),'tower_height_blocks':top-p['frame']['tower_grade_y']+1,'readback_exact':True,'connection_updates':b.connection_updates,
        'source_code_sha256':sha(__file__),'params_sha256':sha(out/'params_used.json'),'terrain_sha256':sha(CASE/p['site']['terrain_source']),
        'osm_sha256':sha(CASE/p['site']['osm_source']),'notes':['Sparse NBT omits air: paste into cleared area','Terrain is a closed surface shell with hollow interior','No game import, collision, lighting engine or walkability validation','Photograph-based component dimensions are estimates except documented total height','Tree distribution and room furnishing are authored approximations']})
    (out/'build_case_snapshot.py').write_text(Path(__file__).read_text())
    print(json.dumps({**meta,'trees':len(b.trees),'readback_exact':True},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
