"""Memorial Hall V2 repairs over the preserved V1 adapter, on HAF 0.2.

Case-specific geometry. A future HAF 0.3 release requires cross-building evidence.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import build_case as v1
from hafusion.classical import M,mask_polygon,erode
from hafusion.case_io import save_run,dump
CASE=Path(__file__).resolve().parents[1]

def roof_height(r,x,z):
    u,v=(x,z) if r['axis']=='z' else (z,x)
    if abs(u-r['uc'])>r['hw'] or abs(v-r['vc'])>r['hd']:return None
    ridge=r['hw']-r['hd']*.64
    q=max(abs(v-r['vc'])/r['hd'],max(0,abs(u-r['uc'])-ridge)/(r['hw']-ridge))
    curl=(abs(u-r['uc'])/r['hw'])**8*(abs(v-r['vc'])/r['hd'])**7*2.5
    return round(r['eave']+r['rise']*max(0,1-q)**1.55+curl)

def repair(b,p):
    cx,cz=p['center_xz'];s=b.s;g=p['ground_y'];fy=p['floor_y'];cfg=p['v2_repairs'];audit={}
    def put(x,y,z,mat,own):b.put(cx+x,y,cz+z,mat,own)
    def box(lo,hi,mat,own):b.box((cx+lo[0],lo[1],cz+lo[2]),(cx+hi[0],hi[1],cz+hi[2]),mat,own)
    # Remove only the former sign, not the surrounding building or lower roof.
    sign_cells=[q for q,o in s.owners.items() if o.startswith('entry.plaque.')]
    for q in sign_cells:s.set(q,'minecraft:air','repair.plaque.clear')
    sign=cfg['plaque'];hw=sign['half_width'];yy=sign['base_y'];zz=sign['z']
    box((-hw,yy,zz),(hw+1,yy+3,zz+1),'lapis_block','entry.plaque.back')
    for x in sign['symbol_x']:put(x,yy+1,zz+1,'gold_block','entry.plaque.symbol')
    audit['plaque']={'old_cells_removed':len(sign_cells),'width':2*hw+1,'height':3,'symbol_blocks':len(sign['symbol_x']),'text_rendering':False}
    # Continuous bearing platform below every column and across the route to the hall.
    x0,z0,x1,z1=cfg['portico']['platform_rect']
    box((x0,g+1,z0),(x1+1,fy,z1+1),'stone_bricks','entry.platform.foundation')
    box((x0,fy,z0),(x1+1,fy+1,z1+1),'smooth_stone','entry.platform.walk_surface')
    # Recessed ceiling, connected to the beam. Leave open column bays and doorways.
    sy=cfg['portico']['soffit_y']
    for x in range(-44,45):
        for z in range(55,66):
            q=(cx+x,sy,cz+z)
            if q not in s.blocks:put(x,sy,z,M('smooth_quartz_slab',type='top'),'entry.soffit.panel')
    for x in p['entrance_columns_x']:
        for z in range(55,64):put(x,sy-1,z,'oxidized_copper','entry.soffit.crossbeam')
    audit['platform']={'rect':cfg['portico']['platform_rect'],'floor_y':fy,'foundation_to_ground':True,'soffit_y':sy}
    # Join the outside L-shaped re-entrant gaps of adjacent upper roof surfaces.
    roofs={r['ident']:r for r in p['wing_roofs']};patches=[]
    for sx in [-1,1]:
        side=roofs['east_upper' if sx>0 else 'west_upper']
        for sz in [-1,1]:
            front=roofs['front_upper' if sz>0 else 'back_upper']
            xa=front['hw'];xb=abs(side['vc'])+side['hd'];za=side['hw'];zb=abs(front['vc'])+front['hd']
            ident=('east' if sx>0 else 'west')+'_'+('front' if sz>0 else 'rear')
            cells=0
            for ax in range(xa,xb+1):
                for az in range(za,zb+1):
                    t=(ax-xa)/(xb-xa)+(az-za)/(zb-za)
                    if t>1:continue
                    x,z=sx*ax,sz*az
                    h1=roof_height(front,sx*xa,z);h2=roof_height(side,x,sz*za)
                    dx=ax-xa;dz=az-za
                    yy=round((h1*dz+h2*dx)/(dx+dz)) if dx+dz else max(h1,h2)
                    put(x,yy,z,'lapis_block','junction.roof.'+ident+'.tiles')
                    put(x,yy-1,z,'dark_oak_planks','junction.roof.'+ident+'.underside');cells+=1
                    if t>.87:put(x,yy-1,z,'smooth_quartz','junction.roof.'+ident+'.fascia')
                    # Recessed diagonal closure beneath the joining roof, terminating on lower tiles.
                    if .62<=t<=.78:
                        below=[roof_height(r,x,z) for r in p['wing_roofs'] if not r['upper']]
                        lower=max([h for h in below if h is not None],default=35)
                        for y in range(lower+1,yy-1):
                            mat='red_terracotta' if (ax+az)%7==0 and lower+2<y<yy-3 else 'smooth_sandstone'
                            put(x,y,z,mat,'junction.roof.'+ident+'.recessed_closure')
            patches.append({'id':ident,'rectangle_xz_abs':[xa,za,xb,zb],'roof_surface_cells':cells,'basis':'case-authoring estimate from existing aerials; not a measured valley detail'})
    audit['roof_connections']=patches
    # Eight-sided continuous wall apron below the clerestory, resting on the roof envelope.
    r=p['central_roof']['radius']-4;k=r*(math.sqrt(2)-1)
    points=[(-k,-r),(k,-r),(r,-k),(r,k),(k,r),(-k,r),(-r,k),(-r,-k)]
    shape=(s.size[0],s.size[2]);mask=mask_polygon(shape,[(cx+x,cz+z) for x,z in points]);rim=mask & ~erode(mask,2)
    # The V1 face-line rasterizer rounds differently from polygon filling on diagonals.
    # Include the ACTUAL bottom cells, rather than trusting an idealized polygon alone.
    for (gx,gy,gz),owner in s.owners.items():
        if gy==61 and owner.startswith('central.clerestory.face'):rim[gz,gx]=True
    cells=0
    for gz,gx in zip(*np.where(rim)):
        x,z=int(gx-cx),int(gz-cz)
        local=[roof_height(rf,x,z) for rf in p['wing_roofs'] if rf['upper']]
        bottom=max([h for h in local if h is not None],default=52)
        for y in range(bottom,61):
            q=(int(gx),y,int(gz));owner=s.owners.get(q,'')
            if owner.startswith(('roof.','junction.roof.')):continue
            mat='oxidized_copper' if y==60 else 'smooth_sandstone'
            put(x,y,z,mat,'junction.central.apron');cells+=1
    audit['central_apron']={'cells_placed':cells,'top_y':60,'bottom_rule':'upper roof envelope, with top-band underside at 61','thickness_blocks':2}
    # Recompute light inventory after final geometry. Preserve warm/cool design decisions.
    lights=[]
    for q,st in s.blocks.items():
        if st not in [M('glowstone'),M('sea_lantern')]:continue
        o=s.owners[q];zone=o.removeprefix('lighting.')
        lights.append({'xyz':list(q),'material':st.removeprefix('minecraft:'),'zone':zone})
    b.memorial_metadata['placed_light_records']=lights
    b.memorial_metadata['light_zones']=dict(collections.Counter(x['zone'] for x in lights))
    b.memorial_metadata['v2_repairs']=audit
    return b

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'research/parameters_v2.json');a=ap.parse_args()
    p=json.loads(a.params.read_text());b=repair(v1.build(p),p)
    out=save_run(CASE,a.run,p,b,Path(__file__),{'scale_blocks_per_m':2,'route':'image_only','baseline_run':'V1_r03','scope':'plaque, portico continuity, clerestory apron and four roof junctions','fidelity_status':'awaiting user review','future_engine_release':'HAF 0.3 planned after additional independent building cases'})
    dump(out/'case_geometry.json',b.memorial_metadata)
    dependencies={}
    for f in [Path(v1.__file__),Path(__file__)]:
        target=out/('dependency_'+f.name);target.write_bytes(f.read_bytes());dependencies[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    dump(out/'adapter_dependencies.json',dependencies)
if __name__=='__main__':main()
