"""Nanshan Cloud V1: explicit photo interpretation; not automatic reconstruction.

Three offset tower prisms, four stacked stepped-glass clusters, open ground
and deep inter-tower reveals. All coordinates and estimates live in params.json.
"""
from pathlib import Path
import argparse, json, math, sys
import numpy as np
CASE=Path(__file__).resolve().parents[1]; HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.classical import Builder, M
from hafusion.case_io import save_run, dump
from hafusion.lighting import room_lighting, unit
from hafusion.interiors import room_style, furnishing_cells

DIRS=[('north',0,-1),('south',0,1),('west',-1,0),('east',1,0)]
OPP={'north':'south','south':'north','west':'east','east':'west'}

class Cloud(Builder):
    def __init__(self,p):
        super().__init__(p['frame']['size_xyz'],p['seed']);self.p=p
        self.g=p['frame']['ground_y'];self.w,self.h,self.d=self.s.size
        self.solid=np.zeros((self.h,self.d,self.w),bool)
        self.tower=np.zeros_like(self.solid,dtype=np.uint8)
        self.hill=np.zeros_like(self.solid,dtype=np.uint8)
        self.hill_bounds=[];self.room_anchors=[]
    def mass_masks(self):
        g=self.g;start=g+self.p['tower_base']
        for i,t in enumerate(self.p['towers'],1):
            x0,z0,x1,z1=t['rect'];top=g+t['height']
            self.solid[start:top,z0:z1,x0:x1]=True
            self.tower[start:top,z0:z1,x0:x1]=i
        c=self.p['core'];x0,z0,x1,z1=c['rect'];top=g+c['height']
        self.solid[g:top,z0:z1,x0:x1]=True
        self.tower[g:top,z0:z1,x0:x1]=4
        cp=self.p['cascades']
        for band,base in enumerate(cp['bands']):
            for step in range(cp['step_count']):
                y0=g+base+step*cp['step_heights'];y1=y0+cp['step_heights']
                inset=step*cp['width_loss_per_step']
                # Front and right "hills" project from the recessed junction.
                # Third inner/rear cluster is explicitly an estimated interface.
                rects=[('front',(34+inset,86,98-inset,106)),
                       ('right',(90,26+inset,110,94-inset)),
                       ('inner',(44,46+inset//2,70,80-inset//2))]
                for side,(x0,z0,x1,z1) in rects:
                    self.solid[y0:y1,z0:z1,x0:x1]=True
                    self.hill[y0:y1,z0:z1,x0:x1]=band+1
                    self.hill_bounds.append({'id':f'hills.{side}.{band}.step{step}',
                        'side':side,'band':band,'step':step,'box':[x0,y0,z0,x1,y1,z1],
                        'confidence':'estimated rear interface' if side=='inner' else 'photo-constrained approximation'})
    def site(self):
        g=self.g
        self.box((7,g-2,8),(132,g-1,131),'stone_bricks','site.base')
        for x in range(7,132):
            for z in range(8,131):
                mat='polished_andesite' if x%9==0 or z%9==0 else 'smooth_stone'
                self.put(x,g-1,z,mat,'site.paving')
        # Tree belts and low clipped planters from the approach/aerial views.
        for rect in [(13,20,20,105),(20,113,58,120),(82,113,121,120),(119,26,126,99),(32,12,105,18)]:
            x0,z0,x1,z1=rect
            self.box((x0,g-1,z0),(x1,g,z1),'dirt','site.planter.soil')
            for x in range(x0,x1):
                for z in range(z0,z1):
                    edge=x in (x0,x1-1) or z in (z0,z1-1)
                    self.put(x,g,z,M('smooth_stone_slab') if edge else M('moss_block'),'site.planter.edge' if edge else 'site.planter.green')
        for x,z in [(16,31),(16,64),(16,95),(35,116),(96,116),(123,38),(123,85),(48,14),(91,14)]:self.tree(x,z,g+1,h=10,r=3)
        # Smaller street furniture than the 2-block/metre London examples.
        for x,z in [(24,103),(113,102),(113,24),(25,25)]:
            self.line((x,g,z),(x,g+5,z),'iron_bars','lighting.site.pole')
            self.put(x,g+6,z,'sea_lantern','lighting.site.head')
            self.put(x,g+7,z,M('smooth_stone_slab'),'lighting.site.cap')
        for x,z in [(35,111),(91,111),(117,66)]:
            self.box((x-3,g,z),(x+4,g+1,z+1),M('dark_oak_slab'),'site.bench')
    def support_and_lobby(self):
        g=self.g;base=g+self.p['tower_base']
        # Stone piers expose the full-height passage, rather than solid podium.
        for t in self.p['towers']:
            x0,z0,x1,z1=t['rect']
            for x in range(x0+2,x1,8):
                for z in [z0+2,z1-3]:
                    self.box((x-1,g,z-1),(x+1,base,z+1),'polished_andesite',f'base.{t["id"]}.pier')
                    self.box((x-1,g,z-1),(x+1,g+1,z+1),'polished_deepslate',f'base.{t["id"]}.plinth')
        # The second-level gallery is cropped at the site, not an invented bridge.
        fy=g+6
        self.box((30,fy,87),(104,fy+1,93),M('smooth_stone_slab',type='top'),'base.gallery.floor')
        for x in range(30,104):
            if x not in range(87,92):self.put(x,fy+1,93,'glass_pane','base.gallery.rail')
        self.box((87,fy,92),(92,fy+1,96),M('smooth_stone_slab',type='top'),'base.stair.landing')
        for k in range(14):
            yy=g+k//2;z=107-k
            self.box((87,yy,z),(92,yy+1,z+1),M('polished_andesite_stairs',facing='north'),'base.stair')
            for x in [86,92]:self.put(x,yy+1,z,'iron_bars','base.stair.rail')
        # Local entrance lobby: stone piers, reflective dark ceiling and gates.
        for x in range(56,85):
            for z in range(79,87):
                self.put(x,g-1,z,'polished_deepslate' if x%4==0 else 'polished_andesite','base.lobby.paving')
                self.put(x,base-1,z,M('iron_trapdoor',half='top'),'base.soffit.panels')
                if x%6==0 and z%4==0:self.put(x,base-2,z,'end_rod','lighting.lobby.downlight')
        for x in [58,63,68,73,78,83]:
            self.put(x,g,81,'polished_deepslate','base.access_gate')
            self.put(x,g+1,81,M('iron_trapdoor',half='top'),'base.access_gate.top')
        for x in [60,71,82]:
            self.put(x,g,83,'dark_oak_planks','base.lobby.planter')
            self.put(x,g+1,83,'oak_leaves','base.lobby.plant')
    def floors_and_skin(self):
        start=self.g+self.p['tower_base'];top=max(t['height'] for t in self.p['towers'])+self.g
        floors={start+round(i*self.p['floor_pitch']) for i in range(55)}
        self.floor_ys=sorted(y for y in floors if y<top)
        for y in range(self.g,top):
            active=self.solid[y]
            for z,x in zip(*np.where(active)):
                x,z=int(x),int(z);tid=int(self.tower[y,z,x]);hill=int(self.hill[y,z,x]);owner=f'hills.{hill}' if hill else f'tower.{tid}'
                below=not self.solid[y-1,z,x] if y>0 else True
                above=not self.solid[y+1,z,x]
                # Thin slab floor plates. Tower and hill schedules stay separate.
                local_floor=(y-start)%4==0 if hill else y in floors
                if local_floor or below:self.put(x,y,z,M('smooth_stone_slab',type='top'),owner+'.floor')
                if below:
                    self.put(x,y-1,z,M('iron_trapdoor',half='top'),owner+'.soffit')
                    if hill and (x%5==0 or z%5==0):self.put(x,y-1,z,'polished_deepslate',owner+'.soffit.rib')
                if above:
                    self.put(x,y,z,M('smooth_stone_slab',type='top'),owner+'.roof')
                for side,dx,dz in DIRS:
                    if active[z+dz,x+dx]:continue
                    u=x if dz else z
                    if hill:
                        mat='white_stained_glass_pane' if u%3==0 else self.p['facade']['terrace_glass']
                        if sum(not active[z+ez,x+ex] for _,ex,ez in DIRS)>1:mat='light_blue_stained_glass'
                        self.put(x,y,z,mat,owner+'.glazing.'+side)
                        if (y-start)%4==0 or below or above:
                            self.put(x+dx,y,z+dz,M('smooth_quartz_slab',type='top'),owner+'.horizontal_edge')
                        elif (y-start)%4==2 and u%3==0:
                            self.put(x+dx,y,z+dz,M('iron_trapdoor',half='top'),owner+'.opaque_panel')
                    else:
                        mat='black_stained_glass_pane' if tid==4 else self.p['facade']['glass']
                        # Full glass at convex corners prevents diagonal cracks.
                        if sum(not active[z+ez,x+ex] for _,ex,ez in DIRS)>1:mat='gray_stained_glass'
                        self.put(x,y,z,mat,owner+'.glass.'+side)
                        if y>=start and tid!=4 and u%self.p['facade']['fin_pitch']==0:
                            fin=self.p['facade']['fin']
                            material=M(fin,open=True,facing=OPP[side]) if fin.endswith('trapdoor') else M(fin)
                            self.put(x+dx,y,z+dz,material,owner+'.fins.'+side)
                        if y in floors and not above:
                            self.put(x-dx,y,z-dz,'gray_concrete',owner+'.spandrel_backing')
                        if above:
                            self.put(x,y,z,'gray_concrete',owner+'.roof_edge')
        # Recessed lift enclosure: remains behind the actual gaps, not a fill.
        c=self.p['core'];x0,z0,x1,z1=c['rect']
        for yy in range(self.g,self.g+c['height']):
            for x in [64,75]:
                for z in range(55,67):self.put(x,yy,z,'light_gray_concrete','core.lift_wall')
            for z in [55,66]:
                for x in range(64,76):self.put(x,yy,z,'light_gray_concrete','core.lift_wall')
        # Level-1 portal through front core wall.
        self.box((65,self.g,77),(74,self.g+5,79),'minecraft:air','base.core_portal')
    def terraces(self):
        for row in self.hill_bounds:
            x0,y0,z0,x1,y1,z1=row['box'];own=row['id'];top=y1-1
            # Newly exposed ledges at each retreat; keep the glazed wall intact.
            ledge=[]
            for z in range(z0+1,z1-1):
                for x in range(x0+1,x1-1):
                    if self.solid[y1,z,x]:continue
                    ledge.append((x,z))
                    self.put(x,top,z,'smooth_stone',own+'.terrace.floor')
                    if (x+z)%5==0 and (x-x0<3 or x1-x<4):
                        self.put(x,y1,z,'moss_block',own+'.planter')
                        self.put(x,y1+1,z,'azalea_leaves',own+'.plant')
                    elif x in [x0+1,x1-2] or z in [z0+1,z1-2]:self.put(x,y1,z,'glass_pane',own+'.rail')
            row['exposed_terrace_cells']=len(ledge)
        # Roof crowns have visible open screens and a recessed mechanical well.
        for t in self.p['towers']:
            x0,z0,x1,z1=t['rect'];y=self.g+t['height']-1;own='roof.'+t['id']
            self.box((x0+1,y-5,z0+1),(x1-1,y+1,z1-1),'minecraft:air',own+'.well_void')
            self.box((x0+4,y-4,z0+4),(x1-4,y-3,z1-4),'gray_concrete',own+'.well_floor')
            for x in range(x0+4,x1-3,6):
                for z in range(z0+5,z1-3,8):
                    self.box((x,y-3,z),(x+3,y-1,z+4),'polished_deepslate',own+'.equipment')
                    for xx in range(x,x+3):self.put(xx,y-1,z,M('iron_trapdoor',half='top'),own+'.grille')
            for x in range(x0,x1):
                for z in [z0,z1-1]:
                    for yy in range(y-5,y):
                        self.put(x,yy,z,'iron_bars' if x%3==0 or yy==y-3 else 'minecraft:air',own+'.open_screen')
                    self.put(x,y,z,M('polished_andesite_slab'),own+'.coping')
            for z in range(z0,z1):
                for x in [x0,x1-1]:
                    for yy in range(y-5,y):self.put(x,yy,z,'iron_bars' if z%3==0 or yy==y-3 else 'minecraft:air',own+'.open_screen')
                    self.put(x,y,z,M('polished_andesite_slab'),own+'.coping')
    def interiors(self):
        start=self.g+self.p['tower_base']
        # Representative window-back bays; exposed sky channels remain empty.
        for y in self.floor_ys:
            if y<start or y+4>=self.h:continue
            active=self.solid[y+2]
            for side,dx,dz in DIRS:
                for z,x in zip(*np.where(active)):
                    x,z=int(x),int(z);u=x if dz else z
                    if u%8!=4 or active[z+dz,x+dx]:continue
                    # Roof mechanical wells stay clear of synthetic office bays.
                    if any(t['rect'][0]-1<=x<=t['rect'][2] and t['rect'][1]-1<=z<=t['rect'][3]
                           and y+4>=self.g+t['height']-6 for t in self.p['towers']):continue
                    if self.hill[y+2,z,x] and (y-start)%4!=0:continue
                    tx,tz=dz,-dx
                    # Check every bay corner/depth against the same floorplate.
                    pts=[(x+tx*v-dx*d,z+tz*v-dz*d) for v in [-1,2] for d in [2,6]]
                    if not all(active[zz,xx] for xx,zz in pts):continue
                    if not all(self.solid[y+3,zz,xx] for xx,zz in pts):continue
                    rid=f'room.{side}.{x}.{z}.{y}';style=room_style(self.seed,rid,3,'office')
                    dec=room_lighting(self.seed,str(y),rid,side,self.p['lighting']['activity'],namespace='nanshan-cloud-v1')
                    for du in range(-1,3):
                        for d in range(2,7):
                            xx,zz=x+tx*du-dx*d,z+tz*du-dz*d
                            self.put(xx,y,zz,'smooth_stone','interior.'+rid+'.floor',empty=True)
                        for yy in [y+1,y+2,y+3]:self.put(x+tx*du-dx*6,yy,z+tz*du-dz*6,'gray_concrete','interior.'+rid+'.back',empty=True)
                    for u0,yy,d0,mat in furnishing_cells(style['style'],3):
                        xx,zz=x+tx*(u0-1)-dx*(d0+1),z+tz*(u0-1)-dz*(d0+1)
                        self.put(xx,y+1+yy,zz,mat,'interior.'+rid+'.furniture',empty=True)
                    q=(x-dx*3,y+3,z-dz*3);placed=False
                    if dec['lit']:placed=self.put(*q,style['light'],'lighting.windows.'+rid,empty=True)
                    self.rooms.append({'id':rid,'floor_y':y,'side':side,'style':style,'occupancy':dec,'lamp_position':list(q) if placed else None,'actual_lamp':style['light'] if placed else None,'fidelity':'synthetic office window-back'})
    def lightlines(self):
        # Fixed facade accents are deterministic and independent of room seed.
        start=self.g+self.p['tower_base']
        for band,base in enumerate(self.p['cascades']['bands']):
            y=self.g+base;own=f'lighting.fixed.band{band}'
            for x in range(34,98):
                self.put(x,y-2,104,'glowstone',own+'.front_strip')
                self.put(x,y-2,105,'white_stained_glass',own+'.front_cover')
            for z in range(26,94):
                self.put(108,y-2,z,'glowstone',own+'.right_strip')
                self.put(109,y-2,z,'white_stained_glass',own+'.right_cover')
            # Partial vertical illumination near band ends, as seen in img-022.
            for x in list(range(30,55,8))+list(range(78,103,8)):
                for yy in range(max(start,y-10),y):
                    if self.solid[yy,97,x]:self.put(x,yy,96,'glowstone',own+'.uplight.front')
            for z in list(range(22,49,8))+list(range(74,99,8)):
                for yy in range(max(start,y-10),y):
                    if self.solid[yy,z,101]:self.put(100,yy,z,'glowstone',own+'.uplight.right')
        for t in self.p['towers'][:2]:
            x0,z0,x1,z1=t['rect'];y=self.g+t['height']-2
            for x in range(x0+1,x1-1):self.put(x,y,z1-2,'glowstone','lighting.crown.'+t['id'])
            for z in range(z0+1,z1-1):self.put(x1-2,y,z,'glowstone','lighting.crown.'+t['id'])
    def build(self):
        self.mass_masks();self.site();self.support_and_lobby();self.floors_and_skin();self.terraces();self.interiors();self.lightlines()
        return self

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'params.json');a=ap.parse_args()
    if Path(a.run).name!=a.run:ap.error('simple immutable run name required')
    p=json.loads(a.params.read_text());b=Cloud(p).build()
    out=save_run(CASE,a.run,p,b,__file__,{'route':'image_only','three_dimensional_model_used':False,'floor_schedule':b.floor_ys,'estimate_notice':p['estimates']})
    dump(out/'cascade_components.json',b.hill_bounds)
if __name__=='__main__':main()
