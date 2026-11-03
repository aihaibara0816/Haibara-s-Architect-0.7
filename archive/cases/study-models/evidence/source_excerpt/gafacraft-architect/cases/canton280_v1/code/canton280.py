"""Canton Tower 280-block image experiment, not an automatic recognition model.

Uses the project's deterministic Scene and CPU renderer. Geometry lives in memory;
no NBT, schematic, or block-position file is exported. All render views of a revision
share one fingerprint. Coordinate +Y up; local front -Z is NOT geographic north.
"""
from pathlib import Path
import math, json, argparse, hashlib, time
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, PngImagePlugin
from voxel_core import Scene, quantize, state, block_parts
from renderer import render_view, VIEWS, LABELS, font

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'generation_parameters.json').read_text())
if CONFIG['config_version']!='0.1':raise ValueError('Unsupported case config')
SCALE=CONFIG['total_blocks']/CONFIG['total_metres']
ORIGIN_Y=CONFIG['grade_y']
CX,CZ=CONFIG['center_xz']
SIZE=tuple(CONFIG['size_xyz'])
WAIST_M=CONFIG['waist_m']
WAIST=WAIST_M*SCALE
MAIN_H=CONFIG['body_blocks']
MATERIALS={
 'column':('minecraft:white_concrete','#E3E7E4'),
 'ring':('minecraft:light_gray_concrete','#AEBBBB'),
 'brace':('minecraft:smooth_quartz','#D0D9D7'),
 'core':('minecraft:gray_concrete','#778B8D'),
 'glass':('minecraft:cyan_stained_glass','#426B78'),
 'floor':('minecraft:polished_deepslate','#394D54'),
 'mast':('minecraft:iron_block','#DCE2DA'),
 'red':('minecraft:red_concrete','#B84C42'),
 'deck':('minecraft:smooth_stone','#B9C6C0'),
 'paving':('minecraft:stone_bricks','#C3C4B5'),
 'grass':('minecraft:moss_block','#758C64'),
}
MATERIALS['ring_slab']=('minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]','#9FAFAD')
for direction in ['north','south','east','west']:
    MATERIALS['brace_'+direction]=(state('minecraft:smooth_quartz_stairs',facing=direction,half='bottom',shape='straight',waterlogged='false'),'#C3CFCA')
SPEC={'spec_id':'CANTON TOWER / 280', 'materials':{k:{'block_state':s,'preview_color':c} for k,(s,c) in MATERIALS.items()}}

def section(h):
    """Hyperbolic envelope through reported dimension controls; assumed interpolation.
    The 80 x 60 m control is below grade at -10 m, not the ground silhouette.
    Rotation is a trial member winding; no claim of surveyed member correspondence.
    """
    m=h/SCALE
    if m<=WAIST_M:
        u=(WAIST_M-m)/(WAIST_M-CONFIG['foundation_z_m'])
        a=math.sqrt((CONFIG['waist_diameter_m'][0]/2)**2+((CONFIG['foundation_diameter_m'][0]/2)**2-(CONFIG['waist_diameter_m'][0]/2)**2)*u*u)
        b=math.sqrt((CONFIG['waist_diameter_m'][1]/2)**2+((CONFIG['foundation_diameter_m'][1]/2)**2-(CONFIG['waist_diameter_m'][1]/2)**2)*u*u)
    else:
        u=(m-WAIST_M)/(CONFIG['top_z_m']-WAIST_M)
        a=math.sqrt((CONFIG['waist_diameter_m'][0]/2)**2+((CONFIG['top_diameter_m'][0]/2)**2-(CONFIG['waist_diameter_m'][0]/2)**2)*u*u)
        b=math.sqrt((CONFIG['waist_diameter_m'][1]/2)**2+((CONFIG['top_diameter_m'][1]/2)**2-(CONFIG['waist_diameter_m'][1]/2)**2)*u*u)
    t=(m-CONFIG['foundation_z_m'])/(CONFIG['top_z_m']-CONFIG['foundation_z_m'])
    v=(1-t)+.675*t*complex(math.cos(math.radians(CONFIG['twist_degrees'])),math.sin(math.radians(CONFIG['twist_degrees'])))
    return a*SCALE,b*SCALE,math.atan2(v.imag,v.real)

def point(h,theta,shrink=0):
    a,b,phi=section(h)
    # Centers inset 0.5 block to keep cube exterior near the dimensional envelope.
    a=max(.3,a-.5-shrink);b=max(.3,b-.5-shrink)
    dx=a*math.cos(theta); dz=b*math.sin(theta)
    return np.array([CX+dx*math.cos(phi)-dz*math.sin(phi), ORIGIN_Y+h, CZ+dx*math.sin(phi)+dz*math.cos(phi)])

def put(scene,p,mat,owner):
    q=tuple(int(math.floor(float(v))) for v in p)
    if any(q[i]<0 or q[i]>=SIZE[i] for i in range(3)):
        raise ValueError(f'Clipped geometry forbidden: {q} ({owner})')
    scene.set(q,MATERIALS[mat][0],owner)

def line(scene,a,b,mat,owner):
    a=np.asarray(a);b=np.asarray(b)
    n=max(1,math.ceil(float(np.linalg.norm(b-a))*5))
    for t in np.linspace(0,1,n+1):put(scene,a+(b-a)*t,mat,owner)

def ellipse(scene,h,mat,owner,shrink=0,tilt=False):
    pts=[]
    for theta in np.linspace(0,2*math.pi,241):
        p=point(h,theta,shrink)
        if tilt:p[1]+=1+math.cos(theta)
        pts.append(p)
    for a,b in zip(pts,pts[1:]):line(scene,a,b,mat,owner)

def filled_ellipse(scene,y,a,b,mat,owner,phi=0,cx=CX,cz=CZ,hollow=False):
    for x in range(max(0,math.floor(cx-max(a,b))),min(SIZE[0],math.ceil(cx+max(a,b)))):
        for z in range(max(0,math.floor(cz-max(a,b))),min(SIZE[2],math.ceil(cz+max(a,b)))):
            dx=x+.5-cx;dz=z+.5-cz
            xx=dx*math.cos(phi)+dz*math.sin(phi);zz=-dx*math.sin(phi)+dz*math.cos(phi)
            r=(xx/a)**2+(zz/b)**2
            inner=(xx/max(.1,a-1))**2+(zz/max(.1,b-1))**2
            if r<=1 and (not hollow or inner>=1):scene.set((x,y,z),MATERIALS[mat][0],owner)

def generate(revision='v1'):
    scene=Scene(SIZE)
    # Small contextual pad only: not a reconstruction of the riverfront landscape.
    for y in range(ORIGIN_Y):filled_ellipse(scene,y,25,23,'grass' if y==0 else 'paving','site')
    # Estimated inner core and program zones, explicitly lower confidence than envelope.
    for h in range(209):
        filled_ellipse(scene,ORIGIN_Y+h,*CONFIG['core_radius_blocks'],'core','inner_core',cx=CX+CONFIG['core_offset_x'])
        if any(a<=h<b for a,b in CONFIG['glazed_ranges_blocks']):
            a,b,phi=section(h)
            filled_ellipse(scene,ORIGIN_Y+h,max(3.5,a-2.2),max(3.1,b-2.2),
                           'floor' if h%4==0 else 'glass','internal_program',phi=phi,hollow=True)
    stage_inner=scene.snapshot()
    ring_heights=np.linspace(0,MAIN_H-1,CONFIG['ring_count'])
    # Revision is applied only after review. v1 keeps all structural classes full cubes.
    for k,h in enumerate(ring_heights):
        ellipse(scene,float(h),'ring',f'ring_{k:02}',tilt=(k==CONFIG['ring_count']-1))
    for k in range(CONFIG['ring_count']-1):
        h0,h1=ring_heights[k:k+2]
        for j in range(CONFIG['columns']):
            a=point(float(h0),2*math.pi*j/CONFIG['columns'])
            b=point(float(h1),2*math.pi*(j+1)/CONFIG['columns'])
            line(scene,a,b,'brace',f'brace_{k:02}_{j:02}')
    for j in range(CONFIG['columns']):
        theta=2*math.pi*j/CONFIG['columns']
        pts=[point(float(h),theta) for h in np.linspace(0,MAIN_H-1,MAIN_H*3)]
        pts[-1][1]+=1+math.cos(theta)
        for a,b in zip(pts,pts[1:]):line(scene,a,b,'column',f'column_{j:02}')
    stage_frame=scene.snapshot()
    # Tilted rooftop plane at nominal 450 m, stepped 0..2 blocks (454 m high point).
    a,b,phi=section(210)
    for h in [208,209]:filled_ellipse(scene,ORIGIN_Y+h,a-.4,b-.4,'deck','crown_deck',phi=phi)
    ellipse(scene,210,'column','crown_track',shrink=.5,tilt=True)
    for j in range(CONFIG['capsules']):
        th=2*math.pi*j/CONFIG['capsules']
        p=point(210,th,shrink=.7);p[1]+=1+math.cos(th)
        x,y,z=map(lambda v:int(math.floor(v)),p)
        for dx in [0,1]:
            for dz in [0,1]:
                for dy in [0,1]:
                    scene.set((x+dx,y+dy,z+dz),MATERIALS['glass' if dy==0 else 'column'][0],f'capsule_{j:02}')
    # Antenna envelope: visible stepped widths are estimates from current photos.
    for h in range(210,280):
        if h<CONFIG['antenna_transitions'][0]:r=CONFIG['antenna_radii_blocks'][0];mat='mast'
        elif h<CONFIG['antenna_transitions'][1]:r=CONFIG['antenna_radii_blocks'][1];mat='mast'
        else:r=CONFIG['antenna_radii_blocks'][2];mat='red' if ((h-247)//4)%2 else 'mast'
        # Align thin mast to a voxel center, ensuring a continuous 280th block.
        filled_ellipse(scene,ORIGIN_Y+h,r,r,mat,'antenna',cx=CX+.5,cz=CZ+.5)
        if h in [230,245]:filled_ellipse(scene,ORIGIN_Y+h,r+1.5,r+1.5,'deck','antenna_platform')
    if revision=='v2':
        # Local patch: block states only, unchanged coordinates and component ownership.
        for p,owner in list(scene.owners.items()):
            if owner.startswith('ring_'):
                scene.set(p,MATERIALS['ring_slab'][0],owner)
            elif owner.startswith('brace_'):
                _,k,j=owner.split('_');k=int(k);j=int(j)
                d=point(float(ring_heights[k+1]),2*math.pi*(j+1)/CONFIG['columns'])-point(float(ring_heights[k]),2*math.pi*j/CONFIG['columns'])
                direction=('east' if d[0]>0 else 'west') if abs(d[0])>=abs(d[2]) else ('south' if d[2]>0 else 'north')
                scene.set(p,MATERIALS['brace_'+direction][0],owner)
    return scene,{'inner':stage_inner,'frame':stage_frame},ring_heights

def overview_diagram(path):
    im=Image.new('RGB',(1500,1050),'#F1F3EF');d=ImageDraw.Draw(im)
    d.rectangle((0,0,1500,112),fill='#183B39')
    d.text((48,27),'01 / EVIDENCE TO GEOMETRY',font=font(36),fill='white')
    d.text((48,77),'CANTON TOWER  |  total height includes antenna',font=font(20),fill='#BED3CA')
    x0=370; y0=950; scale=2.65
    # Exact explanatory diagram, not a generated photograph.
    left=[];right=[]
    for h in np.linspace(0,210,422):
        a,b,phi=section(float(h));left.append((x0-a*scale,y0-h*scale));right.append((x0+a*scale,y0-h*scale))
    d.polygon(left+right[::-1],fill='#B8CBC4',outline='#38675C')
    d.rectangle((x0-3,y0-280*scale,x0+3,y0-210*scale),fill='#38675C')
    for h,label in [(0,'GROUND'),(130.1067,'WAIST / 130.1'),(210,'MAIN BODY / 210'),(280,'TOTAL / 280')]:
        yy=y0-h*scale; d.line((170,yy,560,yy),fill='#7B9A8E',width=2)
        d.text((24,yy-24),label,font=font(17),fill='#274F46')
    rows=[('ONE SCALE','280 / 600 = 0.466667 blocks per metre'),('MAIN + ANTENNA','450 m -> 210 blocks / 150 m -> 70 blocks'),('WAIST HEIGHT','278.8 m -> 130.11 blocks above grade'),('WAIST SECTION','27.5 x 20.65 m -> 12.83 x 9.64 blocks'),('TOP CONTROL','54 x 40.5 m -> 25.2 x 18.9 blocks'),('FOUNDATION CONTROL','80 x 60 m at -10 m; not ground width'),('UNRESOLVED','Exact member nodes, ring levels, core offset'),('TRIAL DECISIONS','Hyperbolic interpolation, material and rounding')]
    for i,(a,b) in enumerate(rows):
        yy=176+i*95;d.text((665,yy),a,font=font(18),fill='#367665');d.text((665,yy+30),b,font=font(20),fill='#183B39')
    im.save(path)

def metrics(scene,rings,revision):
    p=[p for p in scene.blocks if scene.owners[p]!='site'];ys=[v[1] for v in p]
    owners=Counter(o.split('_')[0] for o in scene.owners.values())
    layers=[]
    for h in [0,50,100,129,130,131,150,180,209,210,279]:
        pts=[p for p in scene.blocks if p[1]==ORIGIN_Y+h and scene.owners[p]!='site']
        a,b,phi=section(min(h,210))
        layers.append({'height_from_grade':h,'occupied_xz_bounds':([min(p[0] for p in pts),min(p[2] for p in pts),max(p[0] for p in pts),max(p[2] for p in pts)] if pts else None),'analytic_principal_diameter_xz':[2*a,2*b] if h<=210 else None})
    return {'revision':revision,'size_xyz':list(scene.size),'non_air_blocks':len(scene.blocks),'tower_height_blocks':max(ys)-min(ys)+1,'tower_y_min':min(ys),'tower_y_max':max(ys),'origin_y':ORIGIN_Y,'geometry_sha256':scene.fingerprint(),'component_counts':dict(owners),'design_longitudinal_members':24,'design_rings':len(rings),'design_capsules':16,'ring_levels_approximate':list(map(float,rings)),'layers':layers,'source':'generated_voxel_data','exported_blueprint':False}

def test_geometry(scene,rings):
    checks=[]
    def check(name,condition,detail):
        checks.append({'name':name,'status':'PASS' if condition else 'FAIL','detail':detail})
    m=metrics(scene,rings,'test')
    check('280_blocks_above_grade',m['tower_height_blocks']==280 and m['tower_y_min']==2 and m['tower_y_max']==281,m['tower_height_blocks'])
    check('bounds',all(all(0<=p[i]<SIZE[i] for i in range(3)) for p in scene.blocks),str(SIZE))
    check('single_scale',abs(450*SCALE-210)<1e-8 and abs(150*SCALE-70)<1e-8,'600m -> 280; 450m ->210; 150m ->70')
    check('waist_principal_dimensions',np.allclose(np.array(section(WAIST)[:2])*2,[27.5*SCALE,20.65*SCALE]),'continuous envelope; occupied voxel silhouette separately reported')
    heights=np.linspace(0,210,2101);mins=heights[np.argmin([section(h)[0] for h in heights])]
    check('waist_position',abs(mins-WAIST)<.11,{'measured':float(mins),'target':WAIST})
    check('46_distinct_ring_levels',len(set(math.floor(h) for h in rings))==46,'levels approximate, no quantization collapse')
    check('24_members_survive',len({o for o in scene.owners.values() if o.startswith('column_')})==24,'member ownership exists; individual geometry may merge at joints')
    check('16_capsules_survive',len({o for o in scene.owners.values() if o.startswith('capsule_')})==16,'coarse 2 x 2 x 2 representation')
    check('every_height_occupied',all(any(p[1]==y and scene.owners[p]!='site' for p in scene.blocks) for y in range(2,282)),'no empty tower height layer')
    check('ownership_complete',set(scene.blocks)==set(scene.owners),'every voxel has a component id')
    check('no_exported_building_files',not any(ROOT.rglob('*.nbt')) and not any(ROOT.rglob('*.schem')),'picture-only experiment')
    return checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='v1');ap.add_argument('--views',default='front,iso45');ap.add_argument('--diagrams',action='store_true');a=ap.parse_args()
    out=ROOT/'output'/a.revision;out.mkdir(exist_ok=True,parents=True)
    scene,stages,rings=generate(a.revision)
    info=metrics(scene,rings,a.revision);info['tests']=test_geometry(scene,rings)
    (out/'metrics.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
    if a.diagrams:overview_diagram(ROOT/'output'/'01_scale_decisions.png')
    results=[]
    for view in a.views.split(','):
        if not view:continue
        st=time.time()
        result=render_view(scene,SPEC,view,out/f'{view}.png',a.revision,scene.fingerprint())
        results.append(result);print(f'{a.revision} {view}: {time.time()-st:.1f}s {len(scene.blocks)} blocks',flush=True)
    (out/'render_report.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'revision':a.revision,'geometry_sha':scene.fingerprint(),'blocks':len(scene.blocks),'tests':Counter(c['status'] for c in info['tests'])}),flush=True)

if __name__=='__main__':main()
