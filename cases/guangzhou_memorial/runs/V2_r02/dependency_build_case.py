"""Guangzhou Memorial Hall V1: image-authored HAF case, not automatic reconstruction.

Axes: front +Z, right +X. Roof profiles are explicit estimates from ref01/03/07/10.
The 2 blocks/m uniform scale uses the municipal 48.63 x 63.32 x 72.65 m envelope.
"""
from pathlib import Path
import argparse,json,math,sys,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder,M,mask_polygon,erode
from hafusion.case_io import save_run,dump
CASE=Path(__file__).resolve().parents[1]

def build(p):
    b=Builder(p['size_xyz'],p['seed']);cx,cz=p['center_xz'];g=p['ground_y'];floor=p['floor_y']
    roof_records=[];light_records=[]
    def put(x,y,z,mat,own):b.put(cx+x,y,cz+z,mat,own)
    def box(a,c,mat,own):b.box((cx+a[0],a[1],cz+a[2]),(cx+c[0],c[1],cz+c[2]),mat,own)
    def line(a,c,mat,own):b.line((cx+a[0],a[1],cz+a[2]),(cx+c[0],c[1],cz+c[2]),mat,own)
    def lamp(x,y,z,mat,zone):
        put(x,y,z,mat,'lighting.'+zone)
        light_records.append({'xyz':[cx+x,y,cz+z],'material':mat,'zone':zone})
    def oct_points(r):
        k=r*(math.sqrt(2)-1)
        return [(cx+x,cz+z) for x,z in [(-k,-r),(k,-r),(r,-k),(r,k),(k,r),(-k,r),(-r,k),(-r,-k)]]
    shape=(p['size_xyz'][0],p['size_xyz'][2])
    # Bounded site: front forecourt and a slice of the south garden, not all 6 ha.
    b.box((0,0,0),(shape[0],g,shape[1]),'dirt','site.substrate')
    b.box((0,g,0),(shape[0],g+1,shape[1]),'grass_block','site.lawn')
    b.box((cx-83,g,cz-88),(cx+84,g+1,cz+158),'smooth_stone','site.paving')
    for z in range(cz-84,cz+155,12):
        b.box((cx-83,g,z),(cx+84,g+1,z+1),'polished_andesite','site.paving.joints')
    for x in range(cx-78,cx+83,12):b.box((x,g,cz-88),(x+1,g+1,cz+158),'polished_andesite','site.paving.joints')
    # Auditorium footprint + four connected wings. Front wall is recessed behind columns.
    mask=mask_polygon(shape,oct_points(p['body_radius'])).copy()
    for x0,z0,x1,z1 in p['wing_wall_rects']:
        mask[cz+z0:cz+z1+1,cx+x0:cx+x1+1]=True
    base=np.asarray(__import__('PIL').Image.fromarray(mask.astype('uint8')*255).filter(__import__('PIL').ImageFilter.MaxFilter(9)))>0
    for y in range(g+1,floor):b.surface(base,y,'stone_bricks' if y<floor-1 else 'smooth_stone','base.platform')
    b.surface(mask,floor,'smooth_sandstone','hall.floor')
    shell=mask & ~erode(mask,2)
    for y in range(floor+1,35):b.surface(shell,y,'smooth_sandstone','hall.envelope')
    # Front platform staircase, 0.5-block treads with a broad landing.
    for i in range(floor-g):
        box((-41,g+1+i,66),(42,g+2+i,79-i),'smooth_stone','entry.stair.mass')
        for x in range(-41,42):put(x,g+1+i,78-i,M('smooth_stone_slab'),'entry.stair.tread')
    # Four facades: actual openings, red lattice, rear closure and warm interior light.
    faces=[('front',0,54,(0,1),range(-36,37,12)),('rear',0,-73,(0,-1),range(-30,31,12)),
           ('east',62,0,(1,0),range(-24,25,12)),('west',-62,0,(-1,0),range(-24,25,12))]
    for name,x,z,n,us in faces:
        f=b.frame(cx+x,cz+z,n)
        for u in us:
            for yy,hh in [(floor+2,9),(23,9)]:
                own=f'facade.{name}.bay{u}.level{yy}'
                f.rect(u-4,u+5,yy-1,yy+hh+1,-3,1,'red_terracotta',own+'.surround')
                f.rect(u-3,u+4,yy,yy+hh,-3,1,'minecraft:air',own+'.opening')
                f.rect(u-3,u+4,yy,yy+hh,-2,-1,'gray_stained_glass_pane',own+'.glass')
                for uu in [u-2,u,u+2]:f.rect(uu,uu+1,yy,yy+hh,-1,0,'red_concrete',own+'.lattice')
                f.rect(u-3,u+4,yy+hh//2,yy+hh//2+1,-1,0,'red_concrete',own+'.transom')
                b.windows.append({'id':own,'center':f.xyz(u,yy+hh/2,0),'image':'ref01/ref03/ref06','type':'red lattice approximation'})
                q=f.xyz(u,yy+hh-1,-4);b.put(*q,'glowstone','lighting.'+name+'.windows');light_records.append({'xyz':list(q),'zone':name+'.windows','material':'glowstone'})
        # Rear/side lower door openings, front five double-height entry openings.
        for u in ([-24,-12,0,12,24] if name=='front' else [0]):
            f.rect(u-3,u+4,floor+1,floor+9,-4,2,'minecraft:air','entry.'+name+'.open')
            f.rect(u-3,u+4,floor+9,floor+10,-2,1,'red_concrete','entry.'+name+'.lintel')
    # Red entrance columns and exposed bracket/soffit stack. Eight columns are an estimate.
    for u in p['entrance_columns_x']:
        box((u-1,floor+1,63),(u+2,35,66),'red_terracotta','entry.column.shaft')
        box((u-2,floor+1,62),(u+3,floor+3,67),'smooth_stone','entry.column.base')
        for y,spread in [(32,2),(33,3),(34,4)]:box((u-spread,y,62),(u+spread+1,y+1,67),'oxidized_copper','entry.bracket')
        for d in [-3,3]:put(u+d,33,66,'gold_block','entry.bracket.gold')
        lamp(u,32,61,'glowstone','entry.soffit')
    box((-45,34,63),(46,36,66),'lapis_block','entry.beam')
    for x in range(-44,45,3):put(x,35,66,'oxidized_copper','entry.beam.pattern')

    def roof_hip(ident,axis,uc,vc,hw,hd,eave,rise,upper=False):
        """Curved roof surface, with shortened ridge and gable caps for 歇山."""
        def xyz(u,v):return (u,v) if axis=='z' else (v,u)
        ridge_half=hw-hd*.64
        def h(u,v):
            q=max(abs(v-vc)/hd,max(0,abs(u-uc)-ridge_half)/(hw-ridge_half))
            corner=(abs(u-uc)/hw)**8*(abs(v-vc)/hd)**7*2.5
            return eave+rise*(max(0,1-q)**1.55)+corner
        for u in range(round(uc-hw),round(uc+hw)+1):
            for v in range(round(vc-hd),round(vc+hd)+1):
                x,z=xyz(u,v);yy=round(h(u,v));edge=abs(u-uc)>=hw-1 or abs(v-vc)>=hd-1
                put(x,yy,z,'lapis_block','roof.'+ident+'.tiles')
                put(x,yy-1,z,'dark_oak_planks','roof.'+ident+'.underside')
                if edge:put(x,yy-1,z,'smooth_quartz','roof.'+ident+'.fascia')
                if edge and (round(u+v)%7==0):lamp(x,yy-2,z,'sea_lantern','roof.'+ident+'.eave')
                if abs(v-vc)<.5:put(x,yy+1,z,'lapis_block','roof.'+ident+'.ridge')
        # Upper gable-on-hip: short triangular gable above the hip ends.
        if upper:
            for sign in [-1,1]:
                u=uc+sign*int(ridge_half)
                for dv in range(-int(hd*.62),int(hd*.62)+1):
                    x,z=xyz(u,vc+dv);top=round(eave+rise*(1-abs(dv)/hd)**1.55)
                    for yy in range(eave+4,top+1):put(x,yy,z,'smooth_sandstone','roof.'+ident+'.gable')
                    put(x,top+1,z,'lapis_block','roof.'+ident+'.gable_rim')
        # Restrained abstract 博古 end ornaments, not generic pagoda animals.
        for sign in [-1,1]:
            x,z=xyz(uc+sign*ridge_half,vc)
            for dy in range(1,4):put(x,eave+rise+dy,z,'lapis_block','roof.'+ident+'.bogu_proxy')
        roof_records.append({'id':ident,'type':'curved_xieshan_proxy' if upper else 'curved_hip','axis':axis,'center_uv':[uc,vc],'half':[hw,hd],'eave_y':eave,'rise':rise})
    for r in p['wing_roofs']:
        # Fill roof-supporting clerestory only at the vertical strip between the two tiers.
        if r['upper']:
            axis=r['axis'];u0=-r['hw']+4;u1=r['hw']-3;v=r['vc']+ (r['hd']-3 if r['vc']>0 else -r['hd']+3)
            x,z=(0,v) if axis=='z' else (v,0);n=(0,1 if v>0 else -1) if axis=='z' else (1 if v>0 else -1,0)
            f=b.frame(cx+x,cz+z,n)
            f.rect(u0,u1,43,r['eave'],-2,0,'smooth_sandstone','clerestory.'+r['ident'])
            for u in range(u0+2,u1-2,5):
                f.rect(u,u+2,45,r['eave']-1,-2,0,'red_terracotta','clerestory.'+r['ident']+'.panel')
        roof_hip(**r)
    # Central eight-faced clerestory and curved, eight-segment pyramidal roof.
    r=p['central_roof']['radius'];k=r*(math.sqrt(2)-1);e=p['central_roof']['eave_y'];peak=p['central_roof']['peak_y']
    pts=[(-k,-r),(k,-r),(r,-k),(r,k),(k,r),(-k,r),(-r,k),(-r,-k)]
    inner=[(x*(r-4)/r,z*(r-4)/r) for x,z in pts]
    for i,(a,c) in enumerate(zip(inner,inner[1:]+inner[:1])):
        length=math.dist(a,c);steps=round(length)
        for t in range(steps+1):
            q=t/steps;x=a[0]+(c[0]-a[0])*q;z=a[1]+(c[1]-a[1])*q
            for yy in range(61,e):
                mat='smooth_sandstone' if yy in [61,62,e-2,e-1] or t%8 in [0,1] else 'red_terracotta' if t%8==4 or yy in [65,70] else 'gray_stained_glass'
                put(x,yy,z,mat,'central.clerestory.face'+str(i))
            if t%8==4:lamp(x*.96,e-4,z*.96,'glowstone','central.clerestory')
        # Perimeter supports do not invade the central auditorium clear span.
        x,z=a
        line((x,35,z),(x,62,z),'smooth_sandstone','central.perimeter_support')
    roofmask=mask_polygon(shape,oct_points(r))
    rim=roofmask & ~erode(roofmask,1)
    for zz,xx in zip(*np.where(roofmask)):
        x,z=int(xx-cx),int(zz-cz)
        q=max(abs(x)/r,abs(z)/r,(abs(x)+abs(z))/(r+k))
        corner=max(0,(q-.86)/.14)**2*1.5
        yy=round(e+(peak-e)*max(0,1-q)**1.7+corner)
        put(x,yy,z,'lapis_block','roof.central.tiles');put(x,yy-1,z,'dark_oak_planks','roof.central.underside')
        if rim[zz,xx]:
            put(x,yy-1,z,'smooth_quartz','roof.central.fascia')
            put(x,yy-2,z,'oxidized_copper','roof.central.brackets')
            if (x+z)%5==0:lamp(x,yy-3,z,'sea_lantern','roof.central.eave')
    for x,z in pts:
        for t in np.linspace(0,1,100):
            yy=round(e+(peak-e)*(1-t)**1.7+max(0,(t-.86)/.14)**2*1.5)
            put(x*t,yy+1,z*t,'lapis_block','roof.central.hip_rib')
        put(x,e+3,z,'lapis_block','roof.central.corner_ornament')
    for yy in range(peak+1,peak+4):put(0,yy,0,'gold_block','roof.central.finial')
    roof_records.append({'id':'central','type':'curved_octagonal_pyramid','radius':r,'eave_y':e,'peak_y':peak})
    # Actual Chinese plaque represented by reproducible glyph mask (resolution limited).
    box((-20,42,60),(21,52,62),'lapis_block','entry.plaque.back')
    for x in range(-21,22):
        for y in [41,52]:put(x,y,62,'gold_block','entry.plaque.frame')
    for zrow,row in enumerate(p['plaque_bitmap']):
        for x,v in enumerate(row):
            if v=='1':put(x-len(row)//2,50-zrow,62,'gold_block','entry.plaque.glyph')
    # Close the inter-roof support spandrels; a gap in a photograph is not an open hall.
    for side in [-1,1]:
        for x in range(42,51):
            for z in range(36,44):
                # Stay below the actual lower roof: never create a white cube above tiles.
                q=max(abs(z-49)/23,max(0,x-(55-23*.64))/(23*.64))
                top=round(37+10*max(0,1-q)**1.55)-1
                for y in range(35,top):put(side*x,y,z,'smooth_sandstone','roof.junction.front_support')
    # Exposed, sheltered warm fixtures between the columns, plus pillar uplights.
    # Placed late so no later roof/facade pass silently overwrites them.
    for x in range(-36,37,12):
        lamp(x,33,64,'glowstone','entry.soffit_visible')
        put(x,32,64,'white_stained_glass','entry.fixture.diffuser')
        for y in [16,30]:
            for dx in [-2,2]:
                lamp(x+dx,y,53,'glowstone','entry.window_visible')
                put(x+dx,y,54,'white_stained_glass','entry.window_diffuser')
    for x in p['entrance_columns_x']:
        lamp(x+3,floor+1,67,'glowstone','entry.column_uplight')
        put(x+3,floor+2,67,'white_stained_glass','entry.uplight_diffuser')
    # Eight clerestory faces: bright inset panels beside (not behind) the opaque mullions.
    for a,c in zip(inner,inner[1:]+inner[:1]):
        for t in [.24,.52,.78]:
            x=a[0]+(c[0]-a[0])*t;z=a[1]+(c[1]-a[1])*t
            lamp(x*.98,68,z*.98,'glowstone','central.window_visible')
    # Approximate the cool roof floodlights with small real lamps on the upper edge.
    # Vanilla lighting has no RGB filtering; glass is an appearance cue only.
    for a,c in zip(pts,pts[1:]+pts[:1]):
        for t in [.25,.5,.75]:
            x=a[0]+(c[0]-a[0])*t;z=a[1]+(c[1]-a[1])*t
            lamp(x,74,z,'sea_lantern','roof.central.uplight')
            put(x,75,z,'light_blue_stained_glass','roof.central.light_cover')
    # Column-free lower auditorium, stage, curved two-tier galleries and real aisles.
    for z in range(-17,38,4):
        limit=min(36,round(math.sqrt(max(0,43**2-z*z))))
        for x in range(-limit,limit+1,3):
            if abs(x)<3 or 15<=abs(x)<=18:continue
            put(x,floor+1,z,'red_terracotta','interior.main.seat_base')
            put(x,floor+2,z+1,M('dark_oak_stairs',facing='north'),'interior.main.seat_back')
    box((-23,floor+1,-46),(24,floor+4,-26),'oak_planks','interior.stage')
    box((-24,floor+4,-48),(25,31,-46),'black_concrete','interior.stage.backdrop')
    for x in [-26,25]:box((x,floor+4,-47),(x+2,33,-25),'red_terracotta','interior.stage.curtain')
    box((-26,31,-47),(27,34,-25),'smooth_sandstone','interior.stage.proscenium')
    for level,fy,r0,r1 in [(1,20,39,50),(2,31,43,52)]:
        for x in range(-54,55):
            for z in range(-40,53):
                rr=math.hypot(x,z)
                if r0<=rr<=r1 and z>-27:
                    put(x,fy,z,'smooth_sandstone',f'interior.gallery{level}.floor')
                    if rr<r0+1.3:
                        put(x,fy+1,z,'oxidized_copper',f'interior.gallery{level}.balustrade')
                        put(x,fy+2,z,M('smooth_sandstone_slab'),f'interior.gallery{level}.rail')
                    elif x%3==0 and z%4==0:put(x,fy+1,z,M('dark_oak_stairs',facing='north'),f'interior.gallery{level}.seat')
                    if x%10==0 and z%10==0:lamp(x,fy-1,z,'glowstone','interior.gallery'+str(level))
    # Gallery access stairs in side aisles; practical approximation, not surveyed routing.
    for side in [-1,1]:
        for i in range(23):
            box((side*36-2,floor+1,-20+i),(side*36+3,floor+2+i,-19+i),'smooth_sandstone','interior.gallery_stair')
    # Luminous ceiling circle and coffer grid. No visible pillar in the middle.
    for x in range(-39,40):
        for z in range(-39,40):
            rr=math.hypot(x,z)
            if rr<39:
                mat='smooth_sandstone' if x%8==0 or z%8==0 or rr>34 else 'white_stained_glass'
                put(x,58,z,mat,'interior.ceiling.coffer')
                if 16<rr<18:lamp(x,57,z,'sea_lantern','interior.ceiling_ring')
                if (x%10==0 and z%10==0 and rr>20):lamp(x,57,z,'glowstone','interior.ceiling_coffers')
    b.rooms.append({'id':'auditorium','fidelity':'stage + horseshoe galleries + column-free central seating, approximate seat count and circulation','sources':['ref05','ref10']})
    # South forecourt statue: deliberately coarse bronze figure and cane, not a portrait.
    sx,sz=p['statue_xz'];sy=g+1
    for y,hw in [(sy,12),(sy+1,10),(sy+2,8),(sy+3,6)]:box((sx-hw,y,sz-hw),(sx+hw+1,y+1,sz+hw+1),'smooth_stone','site.statue.steps')
    box((sx-4,sy+4,sz-4),(sx+5,sy+12,sz+5),'smooth_sandstone','site.statue.plinth')
    for x in [-2,1]:box((sx+x,sy+12,sz-1),(sx+x+2,sy+17,sz+2),'oxidized_copper','site.statue.legs')
    box((sx-2,sy+17,sz-2),(sx+3,sy+23,sz+2),'oxidized_copper','site.statue.body')
    box((sx-1,sy+23,sz-1),(sx+2,sy+26,sz+2),'oxidized_copper','site.statue.head')
    line((sx+3,sy+21,sz),(sx+5,sy+18,sz+1),'oxidized_copper','site.statue.arm')
    line((sx+5,sy+12,sz+1),(sx+5,sy+18,sz+1),'iron_bars','site.statue.cane')
    for x in [-11,11]:lamp(x,g+1,sz+12,'glowstone','site.statue_uplight')
    # Symmetric planting beds and conical hedges from aerial reference; garden extents estimated.
    for side in [-1,1]:
        for xx in [20,28,36,44]:
            x=side*xx;z=sz
            b.disk(cx+x,cz+z,4.5,g+1,'moss_block','site.hedge.bed')
            for y in range(12):b.disk(cx+x,cz+z,max(.9,3.8-y*.27),g+2+y,'oak_leaves','site.hedge.cone')
        for x,z,r in [(side*66,94,8),(side*45,75,6)]:
            b.disk(cx+x,cz+z,r,g+1,'smooth_quartz','site.flowerbed.border')
            b.disk(cx+x,cz+z,r-1,g+1,'moss_block','site.flowerbed.soil')
            for xx in range(x-r+2,x+r-1,2):
                for zz in range(z-r+2,z+r-1,2):
                    if (xx-x)**2+(zz-z)**2<(r-2)**2:put(xx,g+2,zz,'poppy','site.flowerbed.flowers')
        # Front lawn panels beyond statue; not the entire historical garden.
        box((side*48-28,g,139),(side*48+29,g+1,173),'grass_block','site.front_lawn')
    for side in [-1,1]:
        for j,z in enumerate(range(-76,149,26)):
            b.tree(cx+side*(93+(j%2)*5),cz+z,g+1,h=17+(j%3)*2,r=8)
        for z in [-63,5,79,139]:b.lamp(cx+side*79,cz+z,g+1)
    # Audit physical light survivors only after all geometry is assembled.
    surviving=[]
    for row in light_records:
        if b.s.blocks.get(tuple(map(int,row['xyz'])))==M(row['material']):surviving.append(row)
    b.memorial_metadata={'roof_components':roof_records,'placed_light_records':surviving,
        'light_zones':dict(collections.Counter(x['zone'] for x in surviving)),
        'envelope_blocks':[127,97,145],'source_dimensions_m':[63.32,48.63,72.65]}
    return b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'research/parameters.json');a=ap.parse_args()
    p=json.loads(a.params.read_text());b=build(p)
    out=save_run(CASE,a.run,p,b,Path(__file__),{'scale_blocks_per_m':2,'route':'image_only','scope':'hall, forecourt, statue, partial garden','fidelity_status':'awaiting user review','height_basis':'48.63m municipal record; 52m competing source retained'})
    dump(out/'case_geometry.json',b.memorial_metadata)
if __name__=='__main__':main()
