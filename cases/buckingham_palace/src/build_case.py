"""Buckingham Palace V1: mapped quadrangle, differentiated faces and real voids."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
from PIL import Image,ImageFilter
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.classical import Builder,M,mask_polygon,erode
from hafusion.case_io import save_run,sha
from hafusion.lighting import unit

class Palace(Builder):
    def __init__(self,p):
        super().__init__(p['frame']['size_xyz'],p['seed']);self.p=p;self.g=p['frame']['ground_y']
        self.w,self.h,self.d=self.s.size;self.offset=p['frame']['plan_offset_xz']
        plan=json.loads((CASE/p['plan']).read_text());self.ways={a['id']:a for a in plan['ways']};self.parts=[]
        self.height=np.zeros((self.d,self.w),np.int16)
        omit={'1037796041','1226905189'} # explicit courtyard portico / garden bow below
        for row in plan['ways']:
            if 'building:part' not in row['tags'] or row['id'] in omit:continue
            pts=[(round(x*2+self.offset[0]),round(z*2+self.offset[1])) for x,z in row['points_m']]
            mask=mask_polygon((self.w,self.d),pts);h=round(float(row['tags'].get('height',14))*2)
            # OSM's tags are candidate heights; east facade crown includes pediment.
            h=40 if row['id']=='1226754902' else h
            h=min(h,48);self.height[mask]=np.maximum(self.height[mask],h)
            self.parts.append({'id':row['id'],'mask':mask,'height':h,'points':pts})
        self.union=self.height>0
    def site(self):
        # Closed thin platform, without a hidden full-volume cube fill.
        self.box((0,0,0),(self.w,1,self.d),'stone_bricks','site.foundation')
        self.box((0,3,0),(self.w,4,self.d),'grass_block','site.lawn')
        for lo,hi in [((0,1,0),(1,3,self.d)),((self.w-1,1,0),(self.w,3,self.d)),((0,1,0),(self.w,3,1)),((0,1,self.d-1),(self.w,3,self.d))]:self.box(lo,hi,'stone_bricks','site.cut_edge')
        for z in range(10,274):
            for x in range(18,404):
                # Paved forecourt/approach and retained broad green flanks.
                paved=(z>=142 and 38<=x<=375) or (40<=z<142 and 66<=x<=350) or abs(x-208)<26
                if paved:self.put(x,3,z,'red_terracotta' if (x//22+z//22)%3 else 'bricks','site.red_approach')
        # Central open quadrangle stays open all the way to the sky.
        row=self.ways['349637488'];mask=mask_polygon((self.w,self.d),[(round(x*2+self.offset[0]),round(z*2+self.offset[1])) for x,z in row['points_m']])
        self.surface(mask,3,'red_terracotta','site.quadrangle')
        self.court_mask=mask
        for x0,x1 in [(16,82),(336,456)]:
            self.box((x0,3,145),(x1,4,160),'smooth_stone','site.side_path')
        # Cropped western lawn walk and front flower beds; not a complete garden.
        self.box((18,3,540),(455,4,549),'smooth_stone','site.garden_walk')
        for cx,cz,rx,rz in [(72,54,25,13),(344,54,25,13),(74,119,23,10),(342,119,23,10)]:
            for z in range(cz-rz-2,cz+rz+3):
                for x in range(cx-rx-2,cx+rx+3):
                    q=((x-cx)/rx)**2+((z-cz)/rz)**2
                    if .8<=q<=1.12:self.put(x,4,z,M('smooth_quartz_slab'),'site.flowerbed.edge')
                    elif q<.8:
                        self.put(x,3,z,'dirt','site.flowerbed.soil')
                        if (x+2*z)%3==0:self.put(x,4,z,'poppy' if ((x//6)+(z//4))%3 else 'oxeye_daisy','site.flowerbed.flowers')
        for x,z in [(45,165),(115,165),(299,165),(368,165),(132,82),(284,82),(145,235),(268,235)]:self.lamp(x,z,4)
    def mass(self):
        h=self.height;g=self.g
        # Union heights avoid extruding shared partition faces as exterior walls.
        for z,x in zip(*np.where(self.union)):
            hh=int(h[z,x]);front=(100<=x<=316 and 242<=z<=294);mat='smooth_quartz' if front else 'smooth_sandstone'
            for yy in range(0,hh+1,12):self.put(int(x),g+yy,int(z),'oak_planks' if yy else 'smooth_stone',f'palace.floors.{yy}')
            neighbour=min(int(h[z+dz,x+dx]) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
            # Two-cell walls at exposed edges, not a fully solid shell.
            near=min(int(h[z+dz,x+dx]) for dx,dz in [(2,0),(-2,0),(0,2),(0,-2)])
            y0=min(neighbour,near)
            if y0<hh:
                for yy in range(y0,hh):self.put(int(x),g+yy,int(z),mat,f'palace.masonry.{"east" if front else "warm"}')
        # Lead/slate roofs with a shallow ridge, joined at real plan offsets.
        for part in sorted(self.parts,key=lambda r:r['height']):
            mask=part['mask'];hh=part['height'];active=mask&(self.height<=hh)
            depth=np.zeros_like(h);work=mask.copy()
            for i in range(1,9):work=erode(work);depth[work]=i
            for z,x in zip(*np.where(active)):
                rise=min(5,int(depth[z,x])//2);yy=g+hh+rise
                self.put(int(x),yy,int(z),'polished_deepslate',f'roof.{part["id"]}.slate')
                if (int(depth[z,x])%2)==0:self.put(int(x),yy+1,int(z),M('polished_deepslate_slab'),f'roof.{part["id"]}.tile_edge')
            edge=mask&~erode(mask)
            for z,x in zip(*np.where(edge&(h<=hh))):
                self.put(int(x),g+hh,int(z),M('smooth_quartz_slab' if part['id']=='1226754902' else 'smooth_sandstone_slab'),f'roof.{part["id"]}.cornice')
        # Roof stacks are explicitly an approximation to visible clusters.
        for x,z in [(113,279),(145,279),(272,279),(304,279),(105,332),(105,375),(105,425),(271,365),(271,412),(164,477),(242,477),(344,437),(343,471)]:
            hh=int(h[z,x])
            if not hh:continue
            yy=g+hh+3;self.box((x-2,yy,z-1),(x+3,yy+8,z+2),'cut_sandstone','roof.chimney.stack')
            for xx in [x-1,x+1]:self.put(xx,yy+8,z,'diorite_wall','roof.chimney.pot')
    def generic_facades(self):
        h=self.height;g=self.g;serial=0
        # Collect long straight exposed runs. Short steps retain closed masonry.
        for dx,dz in [(0,-1),(0,1),(-1,0),(1,0)]:
            if dz:
                for z in range(2,self.d-2):
                    candidates=[x for x in range(2,self.w-2) if h[z,x]>h[z+dz,x]+9]
                    groups=[]
                    for x in candidates:
                        if not groups or x>groups[-1][-1]+1 or h[z+dz,x]!=h[z+dz,groups[-1][-1]]:groups.append([x])
                        else:groups[-1].append(x)
                    for xs in groups:
                        if len(xs)<12 or (dz==-1 and z<253 and 99<=xs[0]<=316):continue
                        serial=self.facade_run(xs[0],z,xs[-1]-xs[0]+1,(dx,dz),serial,int(h[z+dz,xs[0]]))
            else:
                for x in range(2,self.w-2):
                    candidates=[z for z in range(2,self.d-2) if h[z,x]>h[z,x+dx]+9]
                    groups=[]
                    for z in candidates:
                        if not groups or z>groups[-1][-1]+1 or h[z,x+dx]!=h[groups[-1][-1],x+dx]:groups.append([z])
                        else:groups[-1].append(z)
                    for zs in groups:
                        if len(zs)<12:continue
                        serial=self.facade_run(x,zs[0],zs[-1]-zs[0]+1,(dx,dz),serial,int(h[zs[0],x+dx]))
    def facade_run(self,x,z,length,n,serial,lower=0):
        # Frame u may run backwards, so choose the actual low endpoint.
        f=self.frame(x,z,n)
        if f.t[0]+f.t[1]<0:f=self.frame(x+(length-1 if n[1] else 0),z+(length-1 if n[0] else 0),n)
        serial+=1;hh=int(self.height[z,x]);stone='smooth_sandstone'
        if 100<=x<=316 and z<295:stone='smooth_quartz'
        for yy in [12,24,hh-1]:
            if yy>hh or yy<=lower:continue
            for u in range(length):f.put(u,self.g+yy,1,M('smooth_quartz_slab' if stone=='smooth_quartz' else 'smooth_sandstone_slab'),f'facade.run{serial}.band')
        for u in range(5,length-4,9):
            px,_,pz=f.xyz(u,self.g,0);hh=int(self.height[int(pz),int(px)])
            for level,yy in enumerate(range(3,hh-5,12)):
                if yy<lower+3:continue
                height=min(8,hh-yy-3);owner=f'facade.run{serial}.window.{u}.{level}'
                room=True
                for du in [-3,3]:
                    q=f.xyz(u+du,self.g,-10)
                    if self.height[int(q[2]),int(q[0])]<yy+height:room=False
                f.window(u,self.g+yy,4,height,owner,stone=stone,room=room,floor_y=self.g+level*12)
        # Open balustrade on major roof lines only, leaving a shadow gap.
        if length>=30 and hh>=36:f.balustrade(0,length,self.g+hh+1,stone,f'facade.run{serial}.parapet')
        return serial
    def east_front(self):
        p=self.p['front'];g=self.g;z=p['z'];lo=p['x0'];hi=lo+p['width_blocks'];centres=p['pavilion_centres_x']
        # Remove generic rows in the refined 23-bay face, keep shared floor behind.
        self.box((lo,g,z-4),(hi,g+41,z+3),'smooth_quartz','east_front.masonry')
        for c in centres:self.box((c-17,g,z-7),(c+18,g+42,z),'smooth_quartz','east_front.pavilion')
        for i in range(sum(p['bay_groups'])):
            x=p['first_bay_x']+i*p['bay_pitch'];pavilion=min(abs(x-c) for c in centres)<14;zz=z-7 if pavilion else z-4
            f=self.frame(x,zz,(0,-1));owner=f'east_front.bay.{i:02}'
            for level,yy,hh in [(0,3,7),(1,16,9),(2,29,8)]:
                f.window(0,g+yy,4,hh,owner+f'.level{level}',pediment=(level==1),floor_y=g+[0,13,27][level])
            f.window(0,g+39,3,2,owner+'.attic',room=False)
            if not pavilion:
                f.rect(4,5,g+15,g+40,1,2,'quartz_block','east_front.pilaster')
                for yy in [g+15,g+39]:f.rect(3,6,yy,yy+1,1,3,'smooth_quartz','east_front.pilaster.capital')
            # Deep horizontal ground-floor rustication, separated from tall pilasters.
            for yy in [g+1,g+11,g+13]:f.rect(-4,5,yy,yy+1,1,2,M('smooth_quartz_slab'),'east_front.rustication')
        for a,b,zz in [(lo,hi,z-4)]:
            f=self.frame((a+b)//2,zz,(0,-1))
            for yy in [g+13,g+40,g+42]:f.rect(-108,108,yy,yy+1,1,3,M('smooth_quartz_slab',type='top'),'east_front.cornice')
            f.balustrade(-108,108,g+43,'smooth_quartz','east_front.roof_balustrade')
        for c in centres:
            f=self.frame(c,z-7,(0,-1))
            for u in [-14,-5,5,14]:f.column(u,g+15,26,2,'smooth_quartz','east_front.giant_columns')
            f.pediment(0,g+42,36,6,'smooth_quartz','east_front.pediment')
            # Blind attic/relief is stone, not a giant new dark window.
            f.rect(-8,9,g+43,g+46,-1,0,'quartz_block','east_front.pediment.relief')
        # Main and side gateways clear through the range into the quadrangle.
        for c,w in [(207,9),(162,7),(252,7)]:
            for x in range(c-w//2,c+w//2+1):
                roof=g+9+round(3*math.sqrt(max(0,1-((x-c)/(w/2+1))**2)))
                self.box((x,g,z-8),(x+1,roof,294),'minecraft:air','east_front.gateway.void')
                self.box((x,roof,z-8),(x+1,roof+1,294),'smooth_quartz','east_front.gateway.vault')
            for x in [c-w//2-1,c+w//2+1]:self.box((x,g,z-8),(x+1,g+10,z-6),'quartz_block','east_front.gateway.jamb')
            self.box((c-w//2,g,243),(c+w//2+1,g+1,294),'smooth_stone','east_front.gateway.floor')
        # Famous balcony; no red ceremonial drape from a single event photograph.
        self.box((190,g+13,z-13),(225,g+15,z-5),'smooth_quartz','east_front.balcony.floor')
        f=self.frame(207,z-13,(0,-1));f.balustrade(-17,18,g+15,'smooth_quartz','east_front.balcony.rail')
        for x in [193,200,214,221]:
            self.box((x,g+10,z-10),(x+2,g+13,z-6),'quartz_block','east_front.balcony.corbel')
        # Small fixed concealed fixtures approximate the observed lit bays/cornice.
        for x in range(108,307,9):
            zz=z-9 if min(abs(x-c) for c in centres)<14 else z-6
            for yy in [g+14,g+39]:
                self.put(x,yy,zz,'glowstone' if yy==g+39 else 'sea_lantern','lighting.east_front.fixed')
        # Flagpole and a voxel Union Flag; actual occupancy flag is not inferred.
        self.line((207,g+48,266),(207,g+78,266),'iron_bars','roof.flagpole')
        for dx in range(1,14):
            for dy in range(8):
                mat='lapis_block'
                if abs(dy-3.5)<1 or abs(dx-7)<1 or abs(dy-(dx-1)*7/12)<.7 or abs(dy-(13-dx)*7/12)<.7:mat='white_concrete'
                if dy in [3,4] or dx==7:mat='red_concrete'
                self.put(207+dx,g+70+dy,266,mat,'roof.flag')
    def west_front(self):
        # The garden elevation is a distinct composition, not the east face copied.
        # Large principal-floor windows, small upper lights, paired columns and bow.
        g=self.g;cx=205;cz=482;r=15
        self.box((97,g+1,480),(314,g+40,494),'minecraft:air','west_front.refinement_clear')
        self.box((98,g,482),(313,g+38,485),'smooth_sandstone','west_front.masonry')
        f=self.frame(cx,485,(0,1))
        for u in [-96,-84,-72,-60,-48,-36,-24,24,36,48,60,72,84,96]:
            f.window(u,g+3,4,7,f'west_front.bay.{u}.ground',stone='smooth_sandstone',floor_y=g)
            f.window(u,g+16,5,13,f'west_front.bay.{u}.principal',stone='smooth_sandstone',pediment=True,floor_y=g+13)
            f.window(u,g+32,4,4,f'west_front.bay.{u}.upper',stone='smooth_sandstone',room=False)
        for yy in [g+12,g+14,g+37,g+39]:
            f.rect(-107,108,yy,yy+1,0,3,M('smooth_sandstone_slab'),'west_front.entablature')
        for u in [-103,-98,-68,-63,-23,-18,18,23,63,68,98,103]:
            f.column(u,g+14,23,1,'smooth_sandstone','west_front.paired_columns')
        # Relief panels are shallow stone; figurative carving remains simplified.
        for a,b in [(-58,-28),(28,58)]:
            f.rect(a,b,g+31,g+35,1,2,'cut_sandstone','west_front.relief.panel')
            for u in range(a+2,b-1,3):f.put(u,g+33,2,M('smooth_sandstone_slab'),'west_front.relief.voxel')
        f.balustrade(-107,108,g+39,'smooth_sandstone','west_front.parapet')
        self.box((150,g+39,479),(260,g+48,485),'smooth_sandstone','west_front.attic')
        for u in [-48,-36,-24,24,36,48]:f.window(u,g+40,5,4,'west_front.attic.'+str(u),stone='smooth_sandstone',room=False)
        f.rect(-12,13,g+47,g+52,0,3,'cut_sandstone','west_front.frieze_panel')
        f.rect(-54,55,g+48,g+49,0,2,M('smooth_sandstone_slab'),'west_front.attic_cornice')
        # Remove the flat facade through the bow; preserve real interior depth.
        self.box((cx-r+2,g+1,480),(cx+r-1,g+37,486),'minecraft:air','west_front.bow.join_void')
        for yy in range(g,g+38):
            for a in np.linspace(0,math.pi,100):self.put(cx+r*math.cos(a),yy,cz+r*math.sin(a),'smooth_sandstone','west_front.bow.wall')
        for yy in [g,g+13,g+37]:
            for zz in range(cz,cz+r+1):
                for xx in range(cx-r,cx+r+1):
                    if (xx-cx)**2+(zz-cz)**2<=r*r:self.put(xx,yy,zz,'smooth_sandstone','west_front.bow.floor')
        for a in np.linspace(.15,math.pi-.15,6):
            xx=round(cx+(r+1)*math.cos(a));zz=round(cz+(r+1)*math.sin(a))
            self.box((xx,g+14,zz),(xx+2,g+37,zz+2),'cut_sandstone','west_front.bow.column')
            self.box((xx-1,g+35,zz-1),(xx+3,g+38,zz+3),'smooth_sandstone','west_front.bow.capital')
        for a in np.linspace(.34,math.pi-.34,5):
            # Radial window aperture avoids a pane pasted over a curved solid wall.
            for da in np.linspace(-.1,.1,9):
                for yy in list(range(g+3,g+10))+list(range(g+16,g+29)):
                    for rr in np.linspace(r-3,r+1,9):
                        self.put(cx+rr*math.cos(a+da),yy,cz+rr*math.sin(a+da),'minecraft:air','west_front.bow.opening')
                    self.put(cx+(r-.5)*math.cos(a+da),yy,cz+(r-.5)*math.sin(a+da),'gray_stained_glass_pane','west_front.bow.window')
            for yy in range(g+16,g+29):
                self.put(cx+(r-.5)*math.cos(a),yy,cz+(r-.5)*math.sin(a),'white_stained_glass_pane','west_front.bow.sash')
            self.put(cx+(r-5)*math.cos(a),g+30,cz+(r-5)*math.sin(a),'glowstone','lighting.west_front.bow')
        for xx in range(cx-r,cx+r+1):
            for zz in range(cz,cz+r+1):
                d=((xx-cx)/r)**2+((zz-cz)/r)**2
                if d<=1:
                    yy=g+38+round(7*math.sqrt(1-d));self.put(xx,yy,zz,'oxidized_copper','west_front.bow.half_dome')
        # Broad western terrace, terminating in the cropped lawn.
        self.box((94,g,490),(309,g+2,528),'smooth_sandstone','west_front.terrace')
        for x in range(94,309):
            if 193<=x<=217:continue
            self.put(x,g+2,527,M('smooth_sandstone_slab'),'west_front.terrace.rail')
            if x%2==0:self.put(x,g+3,527,'diorite_wall','west_front.terrace.baluster')
            self.put(x,g+4,527,M('smooth_sandstone_slab'),'west_front.terrace.toprail')
        for step in range(4):self.box((193,3,528+step*2),(218,6-step//2,530+step*2),'smooth_sandstone','west_front.terrace.steps')
    def courtyard_portico(self):
        g=self.g;f=self.frame(206,415,(0,-1))
        # Four paired columns, open lower arcade and a copper pediment roof.
        for u in [-15,-10,10,15]:f.column(u,g+13,25,2,'smooth_sandstone','quadrangle.portico.column')
        f.rect(-20,21,g+12,g+14,-9,8,'smooth_sandstone','quadrangle.portico.floor')
        f.pediment(0,g+38,44,7,'smooth_sandstone','quadrangle.portico.pediment')
        for u in range(-20,21):
            yy=g+46-round(abs(u)*7/20)
            for d in range(-11,2):f.put(u,yy,d,'oxidized_copper','quadrangle.portico.copper_roof')
        for u in [-16,-8,8,16]:
            f.rect(u,u+1,g+1,g+12,3,4,'polished_deepslate','quadrangle.portico.lower_column')
        # Glass entrance canopy + visible black ribs/soffit, from visitor guide.
        for x in range(183,230):
            for z in range(393,415):self.put(x,g+9,z,'white_stained_glass' if (x-183)%6 else 'polished_deepslate','quadrangle.entrance_canopy')
        for x in range(183,230,6):
            self.line((x,g+8,394),(x,g+1,394),'iron_bars','quadrangle.canopy.post')
            self.put(x,g+8,405,'glowstone','lighting.quadrangle.canopy')
        self.box((198,g,412),(215,g+12,432),'minecraft:air','quadrangle.main_entry.void')
        self.box((198,g,412),(215,g+1,432),'smooth_stone','quadrangle.main_entry.floor')
    def gates_and_memorial(self):
        g=self.g;fz=self.p['site']['forecourt_fence_z']
        for x in range(42,374):
            if 196<x<220:continue
            for y in range(g,g+7):self.put(x,y,fz,'iron_bars','forecourt.railings')
            if x%3==0:self.put(x,g+7,fz,'gold_block','forecourt.railings.tips')
        for x in [42,86,130,174,195,221,242,286,330,373]:
            self.box((x-2,g,fz-2),(x+3,g+13,fz+3),'smooth_quartz','forecourt.gate_pier')
            self.box((x-3,g+12,fz-3),(x+4,g+14,fz+4),'quartz_block','forecourt.gate_cap')
            self.put(x,g+14,fz,'diorite_wall','forecourt.gate_urn');self.put(x,g+15,fz,'gold_block','forecourt.gate_urn.tip')
        # Main decorative gates remain closed; lateral pedestrian opening retained.
        for x in range(198,219):
            top=g+8+round(4*(1-abs(x-208)/11))
            for yy in range(g,top):self.put(x,yy,fz,'iron_bars','forecourt.central_gate')
            self.put(x,top,fz,'gold_block','forecourt.central_gate.crest')
        # Victoria Memorial: geographic anchor from OSM, sculpture is abbreviated.
        cx,cz=self.p['site']['memorial_xz']
        for y,r in [(g,47),(g+1,44),(g+2,41)]:self.disk(cx,cz,r,y,'smooth_quartz','memorial.circular_steps')
        for y in [g+3,g+4]:self.disk(cx,cz,37,y,'light_blue_stained_glass','memorial.basin_water_proxy',inner=23)
        self.disk(cx,cz,38,g+4,'smooth_quartz','memorial.basin_rim',inner=37)
        for y,r in [(g+3,24),(g+4,20),(g+5,17),(g+6,14),(g+7,12)]:self.disk(cx,cz,r,y,'smooth_quartz','memorial.pedestal_steps')
        self.box((cx-7,g+8,cz-7),(cx+8,g+28,cz+8),'smooth_quartz','memorial.pylon')
        for y in [g+8,g+17,g+27]:self.box((cx-8,y,cz-8),(cx+9,y+1,cz+9),'quartz_block','memorial.pylon.band')
        for dx,dz in [(0,-1),(0,1),(-1,0),(1,0)]:
            xx=cx+dx*9;zz=cz+dz*9
            self.box((xx-2,g+8,zz-2),(xx+3,g+14,zz+3),'smooth_quartz','memorial.figure.lower')
            self.box((xx-1,g+14,zz-1),(xx+2,g+18,zz+2),'quartz_block','memorial.figure.head')
        for y,r in [(g+28,7),(g+29,6),(g+30,5)]:self.disk(cx,cz,r,y,'smooth_quartz','memorial.top_plinth')
        self.box((cx-2,g+31,cz-2),(cx+3,g+40,cz+3),'gold_block','memorial.victory.body')
        self.box((cx-1,g+40,cz-1),(cx+2,g+43,cz+2),'gold_block','memorial.victory.head')
        for sign in [-1,1]:
            for i in range(1,9):
                yy=g+36+i//2;xx=cx+sign*i
                self.box((xx,yy,cz-1),(xx+1,yy+3,cz+2),'gold_block','memorial.victory.wing')
        self.line((cx+2,g+37,cz),(cx+6,g+44,cz),'gold_block','memorial.victory.arm')
        for dx,dz in [(-30,0),(30,0),(0,-30),(0,30)]:self.put(cx+dx,g+5,cz+dz,'sea_lantern','lighting.memorial')
    def landscape(self):
        reserved=np.asarray(Image.fromarray(self.union.astype('uint8')*255).filter(ImageFilter.MaxFilter(23)))>0
        for x in range(18,self.w-16,25):
            for z in range(280,self.d-14,27):
                if reserved[z,x] or self.court_mask[z,x] or 92<x<315 and z<550:continue
                if unit(self.seed,'tree',x,z,namespace='london-site')<.35:continue
                self.tree(x,z,4,14+int(unit(self.seed,x,z)*5),5)
        # Benches and clipped planters by the forecourt are sparse, not all lit.
        for x in [62,92,324,354]:
            for dx in range(7):self.put(x+dx,4,220,M('dark_oak_stairs',facing='north'),'site.bench')
            self.box((x-2,4,225),(x+9,6,229),'smooth_quartz','site.planter')
            self.box((x-1,6,226),(x+8,8,228),'azalea_leaves','site.planter.hedge')
    def build(self):
        for name,fn in [('site',self.site),('mass',self.mass),('facades',self.generic_facades),('east',self.east_front),('west',self.west_front),('court',self.courtyard_portico),('gates',self.gates_and_memorial),('landscape',self.landscape)]:
            fn();print(name,len(self.s.blocks),flush=True)
        return self

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name!=a.run:ap.error('simple run name required')
    p=json.loads((a.params or CASE/'params.json').read_text());b=Palace(p).build()
    save_run(CASE,a.run,p,b,__file__,{'scale_blocks_per_metre':2,'east_front_width_blocks':216,'east_front_bay_groups':[3,7,3,7,3],'plan_sha256':sha(CASE/p['plan']),'scope':p['scope'],'limitations':['Mapped plan is not a survey; roof and side-wing details approximated','Synthetic window-back rooms, not all 775 real rooms','Victoria Memorial sculpture simplified; basin uses coloured glass as static water proxy','No game import, collision or light-engine verification']})
if __name__=='__main__':main()
