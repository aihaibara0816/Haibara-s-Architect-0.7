"""Image-authored representative Zhujiang Dijing residential group, HAF 0.2.

This is a scoped study, not a surveyed reconstruction of all Shanghuxuan blocks.
Local front is +Z. All roof/plan dimensions are authored image interpretations.
"""
from pathlib import Path
import argparse,collections,json,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder,M,mask_polygon,erode
from hafusion.case_io import save_run,dump
from hafusion.lighting import room_lighting,unit
from hafusion.interiors import room_style,furnishing_cells
CASE=Path(__file__).resolve().parents[1]

def build(p):
    b=Builder(p['size_xyz'],p['seed']);g=p['ground_y'];w,h,d=p['size_xyz'];records={'balconies':[],'supports':[],'entries':[],'furniture':[],'roof_openings':[],'lamps':[]}
    stone=p['facade']['stone'];trim=p['facade']['trim'];glass=p['facade']['glazing'];fy0=p['residential_start_y'];pitch=p['floor_pitch'];roof=p['roof_y']
    def bx(a,c,m,o):b.box(a,c,m,o)
    def border(x0,z0,x1,z1,y0,y1,m,o,t=1):
        bx((x0,y0,z0),(x1,y1,z0+t),m,o);bx((x0,y0,z1-t),(x1,y1,z1),m,o)
        bx((x0,y0,z0+t),(x0+t,y1,z1-t),m,o);bx((x1-t,y0,z0+t),(x1,y1,z1-t),m,o)
    def lamp(x,y,z,o,m='glowstone'):
        b.put(x,y,z,m,o);records['lamps'].append({'xyz':[x,y,z],'owner':o,'material':m,'evidence':'synthetic fixture proposal'})
    # Continuous terrain, retained lake basin and paved circulation.
    bx((0,0,0),(w,g,d),'dirt','site.foundation');bx((0,g,0),(w,g+1,d),'grass_block','site.lawn')
    bx((8,g,8),(224,g+1,20),'stone_bricks','site.rear_lane')
    bx((8,g,77),(224,g+1,89),'smooth_stone','site.front_walk')
    for x in [8,220]:bx((x,g,18),(x+4,g+1,183),'stone_bricks','site.side_walk')
    bx((8,g,178),(224,g+1,184),'stone_bricks','site.front_boundary_walk')
    zz,xx=np.mgrid[0:d,0:w];lake=np.zeros((d,w),bool)
    for x,z,rx,rz in p['garden']['lake_centers']:lake|=((xx-x)/rx)**2+((zz-z)/rz)**2<1
    rim=lake & ~erode(lake,2);inside=erode(lake,2)
    for z,x in zip(*np.where(lake)):
        b.put(x,1,z,'stone_bricks','site.lake.basin');b.put(x,2,z,'stone_bricks' if rim[z,x] else 'water','site.lake.edge' if rim[z,x] else 'site.lake.water')
        b.put(x,3,z,'smooth_stone_slab' if rim[z,x] else 'minecraft:air','site.lake.rim')
    # A continuous winding path follows the lake, without replacing the basin.
    path=((xx-114)/62)**2+((zz-129)/42)**2
    walkway=(path>.91)&(path<1.18)&~lake
    for z,x in zip(*np.where(walkway)):b.put(x,g,z,'stone_bricks','site.lakeside_path')
    for x0,x1 in [(43,53),(107,117),(171,181)]:bx((x0,g,65),(x1,g+1,104),'smooth_stone','site.entry_path')
    for x in [58,171]:bx((x-3,g,157),(x+3,g+1,181),'stone_bricks','site.path_link')

    def room(cx,zglass,y,u,width,rid,side='front'):
        # floor, glazing, backing and furnishings are separate layers.
        f=b.frame(cx,zglass,(0,1) if side=='front' else (0,-1));lo=u-width//2;hi=lo+width
        f.rect(lo,hi,y+1,y+5,-2,1,'minecraft:air',rid+'.opening')
        f.rect(lo,hi,y+1,y+5,-1,0,glass,rid+'.glazing')
        f.rect(lo,hi,y,y+1,-7,-1,'oak_planks',rid+'.floor')
        f.rect(lo,hi,y+1,y+5,-7,-6,stone,rid+'.back')
        for edge in [lo-1,hi]:f.rect(edge,edge+1,y+1,y+5,-7,-1,stone,rid+'.partition')
        f.rect(lo,hi,y+5,y+6,-7,-1,M('smooth_quartz_slab',type='top'),rid+'.ceiling')
        sty=room_style(p['seed'],rid,4,'residential')
        dec=room_lighting(p['seed'],str(y),rid,'residential',p['lighting']['activity'],namespace=p['namespace'])
        lp=tuple(map(int,f.xyz(u,y+4,-4)));placed=[]
        for ux,uy,uz,mat in furnishing_cells(sty['style'],4):
            q=tuple(map(int,f.xyz(lo+ux,y+1+uy,-2-uz)))
            if q==lp or q in b.s.blocks:continue
            support=(q[0],q[1]-1,q[2])
            if support not in b.s.blocks:continue
            b.put(*q,mat,rid+'.furniture');placed.append(q);records['furniture'].append({'xyz':q,'support':support,'room':rid})
        if dec['lit'] and lp not in b.s.blocks:lamp(*lp,rid+'.light',sty['light'])
        else:dec['lit']=False
        b.rooms.append({'id':rid,'floor_y':y,'style':sty,'occupancy':dec,'actual_lamp':sty['light'] if dec['lit'] else None,'lamp_position':lp,'furniture':placed,'fidelity':'synthetic, not real apartment plan'})
        b.windows.append({'id':rid,'opening_anchor':list(f.xyz(u,y+1,-1)),'size':[width,4],'normal_xz':list(f.n),'glass_recess_blocks':1})

    for ti,(cx,cz) in enumerate(p['tower_centers_xz']):
        own=f'residence.unit{ti+1}';x0=cx-27;x1=cx+27;z0=cz-19;zf=cz+19
        bx((x0-2,g+1,z0-1),(x1+2,6,zf+5),'stone_bricks',own+'.foundation')
        bx((x0-2,5,z0-1),(x1+2,6,zf+5),'smooth_stone',own+'.ground_floor')
        # Ground arcade columns land on the complete platform, not thin air.
        for dx in [-25,-16,-7,7,16,25]:
            for z in [zf+2,z0+2]:
                bx((cx+dx-1,6,z-1),(cx+dx+2,13,z+2),stone,own+'.arcade.column')
                bx((cx+dx-2,6,z-2),(cx+dx+3,7,z+3),trim,own+'.arcade.base')
                records['supports'].append({'x0':cx+dx-2,'x1':cx+dx+3,'z0':z-2,'z1':z+3,'base_y':6,'id':own})
        # Closed lobby behind the porch. Actual door opening stays clear.
        bx((cx-25,6,cz-13),(cx+25,13,cz-12),stone,own+'.ground_back')
        bx((cx-25,6,cz-12),(cx-24,13,zf-3),stone,own+'.ground_side');bx((cx+24,6,cz-12),(cx+25,13,zf-3),stone,own+'.ground_side')
        for xa,xb in [(cx-24,cx-4),(cx+5,cx+24)]:bx((xa,6,zf-5),(xb,12,zf-4),glass,own+'.lobby.glazing')
        bx((cx-5,12,zf-6),(cx+6,13,zf+6),trim,own+'.entry.canopy')
        bx((cx-5,11,zf-6),(cx+6,12,zf+6),M('smooth_sandstone_slab',type='top'),own+'.entry.soffit')
        for off in [-3,3]:lamp(cx+off,10,zf-3,own+'.entry.light')
        # Small symbolic plaque instead of disproportionate voxel lettering.
        bx((cx-3,10,zf+5),(cx+4,11,zf+6),stone,own+'.entry.sign')
        for dx in [-2,0,2]:b.put(cx+dx,10,zf+6,'gold_block',own+'.entry.sign.marker')
        # Two low steps join every entrance to the common path.
        bx((cx-6,4,zf+5),(cx+7,5,zf+9),'smooth_stone',own+'.entry.step')
        bx((cx-6,5,zf+5),(cx+7,6,zf+7),'smooth_stone',own+'.entry.step')
        records['entries'].append({'id':own,'center_x':cx,'door_z':zf-5,'floor_y':5,'range_z':[zf-5,zf+9]})
        for k in range(p['residential_floors']):
            y=fy0+k*pitch;fo=f'{own}.floor{k+2:02}'
            bx((x0,y,z0),(x1,y+1,zf),stone,fo+'.slab')
            # The front is a balcony; the sides and rear are residential masonry.
            border(x0,z0,x1,zf-3,y+1,y+6,stone,fo+'.walls')
            for xx0 in [x0,x1-2]:bx((xx0,y+1,z0),(xx0+2,y+6,zf),stone,fo+'.side')
            bx((cx-3,y+1,cz-9),(cx+3,y+6,cz+4),stone,fo+'.core')
            for side in ['front','rear']:
                for u in [-9,0,9]:room(cx,zf-4 if side=='front' else z0,y,u,7,fo+'.'+side+f'.room{u}',side)
            # Side windows: true openings, recessed pane and finite back layer.
            for sign in [-1,1]:
                f=b.frame(cx+sign*27,cz,(sign,0))
                for u in [-12,-4,4,12]:
                    f.rect(u-2,u+2,y+1,y+5,-2,1,'minecraft:air',fo+'.side.window.opening')
                    f.rect(u-2,u+2,y+1,y+5,-1,0,glass,fo+'.side.window.glazing')
                    f.rect(u-2,u+2,y,y+1,-5,0,stone,fo+'.side.window.floor')
                    f.rect(u-2,u+2,y+1,y+5,-5,-4,stone,fo+'.side.window.back')
                    for uu in range(u-2,u+2):f.put(uu,y,0,M('smooth_quartz_slab'),fo+'.side.sill')
                    # Air-conditioning boxes are subordinate to the wall rhythm.
                    if u in [-4,12]:
                        f.put(u+2,y+2,1,'light_gray_concrete',fo+'.ac.unit');f.put(u+2,y+2,2,M('iron_trapdoor',facing='east' if sign>0 else 'west',open=True),fo+'.ac.grille')
            # Continuous shallow bowed balcony deck, thin glass guard and soffit.
            edge={u:zf+3+round(2*(1-(u/15)**2)) for u in range(-15,16)}
            for u,ze in edge.items():
                bx((cx+u,y,zf-3),(cx+u+1,y+1,ze+1),trim,fo+'.balcony.deck')
                b.put(cx+u,y,ze+1,M('smooth_quartz_slab'),fo+'.balcony.edge')
                for yy in [y+1,y+2]:b.put(cx+u,yy,ze,glass,fo+'.balcony.rail')
                # Metal upper rail is a thin trapdoor; no full-block horizontal stripe.
                b.put(cx+u,y+3,ze,M('iron_trapdoor',half='bottom'),fo+'.balcony.handrail')
            for u in [-15,0,15]:bx((cx+u,y+1,zf-1),(cx+u+1,y+6,zf),trim,fo+'.balcony.pier')
            for u in [-12,12]:
                if unit(p['seed'],ti,k,u,'planter',namespace=p['namespace'])<.2:
                    b.put(cx+u,y+1,zf+2,'dark_oak_planks',fo+'.balcony.planter');b.put(cx+u,y+2,zf+2,'azalea_leaves',fo+'.balcony.plant')
            records['balconies'].append({'id':fo,'center':[cx,y,zf],'clear_test':[cx+7,y+2,zf+2],'glazing_test':[cx+7,y+2,zf-5],'rail_test':[cx+7,y+1,edge[7]],'floor_test':[cx+7,y,zf+2],'soffit_y':y+6})
            # Rounded end bays: alternating enclosed bay windows / open balconies.
            for s in [-1,1]:
                bc=cx+s*21;rz=zf-1;r=p['facade']['round_bay_radius']
                cells={(xx0,zz0) for xx0 in range(bc-r,bc+r+1) for zz0 in range(rz-r,rz+r+1) if (xx0-bc)**2+(zz0-rz)**2<=r*r}
                shell={q for q in cells if any((q[0]+dx,q[1]+dz) not in cells for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])}
                for xx0,zz0 in cells:b.put(xx0,y,zz0,trim,fo+'.roundbay.floor')
                for xx0,zz0 in shell:
                    if zz0<rz-1:continue
                    for yy in range(y+1,y+(5 if (k+ti)%3==0 else 3)):
                        b.put(xx0,yy,zz0,glass,fo+'.roundbay.glazing' if (k+ti)%3==0 else fo+'.roundbay.rail')
                    b.put(xx0,y+5,zz0,M('smooth_quartz_slab',type='top'),fo+'.roundbay.soffit')
                bx((bc-4,y+1,rz-2),(bc+5,y+5,rz-1),glass,fo+'.roundbay.back_glazing')
                for xx0 in [bc-5,bc+5]:bx((xx0,y+1,rz-1),(xx0+1,y+6,rz+1),stone,fo+'.roundbay.pier')
            # Thin continuous storey trim on the opaque sides, not giant floor fins.
            border(x0-1,z0-1,x1+1,zf-2,y,y+1,M('smooth_sandstone_slab',type='top'),fo+'.string_course')
        bx((x0,roof,z0),(x1,roof+1,zf),'smooth_stone',own+'.roof.deck')
        border(x0-1,z0-1,x1+1,zf,roof+1,roof+3,trim,own+'.roof.cornice')
        # Open crown canopy (not a solid dome). Two arc ribs plus spaced purlins.
        for u in [-15,15]:
            for z in [zf-6,zf+4]:bx((cx+u-1,roof,z-1),(cx+u+1,roof+6,z+1),trim,own+'.crown.column')
        for z in [zf-6,zf+4]:
            for u in range(-15,16):
                y=roof+5+round(3*math.sqrt(max(0,1-(u/15)**2)))
                b.put(cx+u,y,z,trim,own+'.crown.arch');b.put(cx+u,y+1,z,M('smooth_quartz_slab'),own+'.crown.arch_cap')
        for u in range(-15,16,5):
            y=roof+5+round(3*math.sqrt(max(0,1-(u/15)**2)))
            b.line((cx+u,y,zf-6),(cx+u,y,zf+4),'iron_bars',own+'.crown.purlin')
        for s in [-1,1]:
            bc=cx+s*21
            for y,r in [(roof+1,5),(roof+5,6)]:b.disk(bc,zf-1,r,y,trim,own+'.crown.round_ring',max(0,r-1.3))
            b.disk(bc,zf-1,6,roof+6,M('smooth_quartz_slab'),own+'.crown.round_ring',4.7)
            for dx,dz in [(4,0),(-4,0),(0,4),(0,-4)]:bx((bc+dx,roof+2,zf-1+dz),(bc+dx+1,roof+5,zf+dz),trim,own+'.crown.round_post')
        records['roof_openings'].append([cx,roof+6,zf])
        # Back equipment is deliberately modest and identified as interpretation.
        bx((cx-7,roof+1,cz-9),(cx+8,roof+6,cz+2),stone,own+'.roof.equipment_room')
        bx((cx-8,roof+6,cz-10),(cx+9,roof+7,cz+3),M('smooth_sandstone_slab'),own+'.roof.equipment_cap')
        for dx in [-20,15]:
            bx((cx+dx,roof+1,z0+4),(cx+dx+5,roof+3,z0+8),'light_gray_concrete',own+'.roof.hvac')
        # Recessed connecting stack between facade units, explicitly estimated.
        if ti<2:
            for y in range(6,roof):
                bx((cx+27,y,cz-10),(cx+38,y+1,cz+6),stone if y%6==1 else glass,own+'.connector')

    # Pedestrian bridge: continuous deck with gradual steps, side balustrades.
    bridge_x=p['garden']['bridge_x'];z0=p['garden']['bridge_z0'];z1=p['garden']['bridge_z1']
    for z in range(z0,z1+1):
        y=4+round(3*math.sin(math.pi*(z-z0)/(z1-z0)))
        bx((bridge_x-4,y-1,z),(bridge_x+5,y+1,z+1),'smooth_sandstone','garden.bridge.deck')
        for x in [bridge_x-5,bridge_x+5]:
            b.put(x,y,z,M('smooth_sandstone_slab'),'garden.bridge.base')
            b.put(x,y+3,z,M('smooth_sandstone_slab'),'garden.bridge.rail')
            if z%3==0:
                for yy in [y+1,y+2]:b.put(x,yy,z,'diorite_wall','garden.bridge.baluster')
    for z in [z0,z1]:bx((bridge_x-4,4,z-4),(bridge_x+5,5,z+4),'smooth_stone','garden.bridge.landing')
    # Circular pavilion observed in ref03/ref04; complete column bearings.
    gx,gz=p['garden']['gazebo_center'];gy=7
    for yy in range(1,gy+1):b.disk(gx,gz,12,yy,'stone_bricks' if yy<gy else 'smooth_sandstone','garden.pavilion.foundation')
    for a in np.arange(0,2*math.pi,math.pi/3):
        x=round(gx+8*math.cos(a));z=round(gz+8*math.sin(a));bx((x-1,gy+1,z-1),(x+2,gy+11,z+2),'sandstone','garden.pavilion.column')
        bx((x-2,gy+1,z-2),(x+3,gy+2,z+3),trim,'garden.pavilion.column_base')
        records['supports'].append({'x0':x-2,'x1':x+3,'z0':z-2,'z1':z+3,'base_y':gy+1,'id':'garden.pavilion'})
    for yy in [gy+10,gy+11]:b.disk(gx,gz,11,yy,stone,'garden.pavilion.entablature',8)
    for z in range(gz-11,gz+12):
        for x in range(gx-11,gx+12):
            rr=((x-gx)/11)**2+((z-gz)/11)**2
            if rr<=1:
                y=gy+12+round(6*math.sqrt(1-rr));b.put(x,y,z,'polished_andesite','garden.pavilion.dome');b.put(x,y-1,z,M('smooth_sandstone_slab',type='top'),'garden.pavilion.soffit')
    b.put(gx,gy+19,gz,'sandstone','garden.pavilion.finial');b.put(gx,gy+20,gz,'gold_block','garden.pavilion.finial')
    lamp(gx,gy+11,gz,'garden.pavilion.light')
    # Low planting beds are placed before taller trees, preserving entrances.
    beds=[(28,103,16,8),(201,105,15,10),(41,151,15,14),(194,152,16,11),(65,173,22,5),(145,173,22,5)]
    for i,(cx,cz,rx,rz) in enumerate(beds):
        for z in range(cz-rz,cz+rz+1):
            for x in range(cx-rx,cx+rx+1):
                q=((x-cx)/rx)**2+((z-cz)/rz)**2
                if q<1:
                    b.put(x,4,z,'azalea_leaves' if q>.68 else 'moss_block',f'garden.bed{i}')
                    if q<.65 and (x+3*z)%17==0:b.put(x,5,z,'poppy',f'garden.bed{i}.flowers')
    def palm(x,z,ht):
        for y in range(g+1,g+ht):b.put(x,y,z,'oak_log','garden.palm.trunk')
        for a in np.arange(0,2*math.pi,math.pi/4):
            for t in range(1,9):
                xx0=round(x+math.cos(a)*t);zz0=round(z+math.sin(a)*t);yy=g+ht+round(2*math.sin(t*.4))-t//4
                b.put(xx0,yy,zz0,'oak_leaves','garden.palm.frond',empty=True)
                if t<7:b.put(xx0,yy,zz0+1,'oak_leaves','garden.palm.frond',empty=True)
    for x,z in [(26,91),(73,91),(153,92),(209,92),(24,159),(201,159)]:palm(x,z,18)
    for x,z,ht in [(20,114,18),(211,127,20),(36,170,17),(185,174,17),(40,92,14),(182,93,15)]:b.tree(x,z,g+1,ht,7)
    for x,z in [(34,116),(69,164),(151,174),(185,122),(154,99),(49,92),(176,92)]:
        for y in range(g+1,g+8):b.put(x,y,z,'iron_bars','garden.lamp.post')
        for dx in [-2,2]:
            b.line((x,g+6,z),(x+dx,g+7,z),'iron_bars','garden.lamp.arm');lamp(x+dx,g+8,z,'garden.lamp.fixture')
            b.put(x+dx,g+9,z,M('polished_andesite_slab'),'garden.lamp.cap')
    for x,z in [(50,107),(177,114),(79,169),(165,168)]:
        for dx in range(-3,4):b.put(x+dx,4,z,M('dark_oak_stairs',facing='north'),'garden.bench')
    records['lamp_counts']=dict(collections.Counter(s.split('[')[0] for s in b.s.blocks.values() if any(x in s for x in ['glowstone','sea_lantern'])))
    return b,records

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'research/parameters.json');a=ap.parse_args();p=json.loads(a.params.read_text());b,records=build(p)
    out=save_run(CASE,a.run,p,b,__file__,{'scope':p['scope'],'study_scale_blocks_per_m':2,'scale_surveyed':False,'geometry_route':'image-authored case adapter; no SU','game_status':'pending'})
    dump(out/'construction_records.json',records)
if __name__=='__main__':main()
