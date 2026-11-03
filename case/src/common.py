"""Shared study primitives. No model files are read here."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from voxel_core import Scene,export_structure,parse_state,AIR
import inspect_build

def dump(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

PALETTE={
 'column':('minecraft:white_concrete','#E3E7E4'),
 'ring':('minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]','#B3C0BD'),
 'brace':('minecraft:light_gray_concrete','#C2CDC9'),
 'core':('minecraft:gray_concrete','#778B8D'),
 'glass':('minecraft:cyan_stained_glass','#426B78'),
 'floor':('minecraft:polished_deepslate','#394D54'),
 'mast':('minecraft:iron_block','#DCE2DA'),
 'red':('minecraft:red_concrete','#B84C42'),
 'deck':('minecraft:smooth_stone','#B9C6C0'),
 'paving':('minecraft:stone_bricks','#B8C2B4'),
 'grass':('minecraft:moss_block','#758C64'),
 'light':('minecraft:sea_lantern','#E5F4CD')}
for direction in ['north','south','east','west']:
    PALETTE['brace_'+direction]=(f'minecraft:smooth_quartz_stairs[facing={direction},half=bottom,shape=straight,waterlogged=false]','#C2CDC9')

def brace_material(delta):
    d=np.asarray(delta,float)
    if d[1]<0:d=-d
    direction=('east' if d[0]>=0 else 'west') if abs(d[0])>=abs(d[2]) else ('south' if d[2]>=0 else 'north')
    return 'brace_'+direction

def put(s,p,mat,owner):
    q=tuple(int(math.floor(float(v))) for v in p)
    s.set(q,PALETTE[mat][0],owner)

def line(s,a,b,mat,owner,step=.2):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if mat=='brace':mat=brace_material(b-a)
    n=max(1,math.ceil(float(np.linalg.norm(b-a))/step))
    for t in np.linspace(0,1,n+1):put(s,a+(b-a)*t,mat,owner)

def ellipse_cells(cx,cz,a,b,phi=0,hollow=False):
    co,si=math.cos(phi),math.sin(phi)
    for x in range(max(0,math.floor(cx-max(a,b))),min(56,math.ceil(cx+max(a,b)))):
        for z in range(max(0,math.floor(cz-max(a,b))),min(56,math.ceil(cz+max(a,b)))):
            dx=x+.5-cx;dz=z+.5-cz;xx=dx*co+dz*si;zz=-dx*si+dz*co
            if (xx/a)**2+(zz/b)**2<=1 and (not hollow or (xx/max(.1,a-1))**2+(zz/max(.1,b-1))**2>=1):yield x,z

def photo_profile(h,c):
    f=c['photo_frame'];sc=c['blocks_per_metre'];m=h/sc;w=f['waist_m']
    if m<=w:u=(w-m)/(w-f['foundation_y_m']);diam=f['foundation_diameter_m']
    else:u=(m-w)/(f['top_y_m']-w);diam=f['top_diameter_m']
    a,b=[math.sqrt((r/2)**2+((d/2)**2-(r/2)**2)*u*u)*sc for r,d in zip(f['waist_diameter_m'],diam)]
    t=(m-f['foundation_y_m'])/(f['top_y_m']-f['foundation_y_m'])
    v=(1-t)+.675*t*complex(math.cos(math.radians(f['member_winding_trial_degrees'])),math.sin(math.radians(f['member_winding_trial_degrees'])))
    return 28.,28.,a,b,math.atan2(v.imag,v.real)

def curvepoint(h,theta,profile,shrink=0):
    cx,cz,a,b,phi=profile(h);a=max(.4,a-.5-shrink);b=max(.4,b-.5-shrink)
    dx=a*math.cos(theta);dz=b*math.sin(theta)
    return np.array([cx+dx*math.cos(phi)-dz*math.sin(phi),2+h,cz+dx*math.sin(phi)+dz*math.cos(phi)])

def site(s):
    for y in [0,1]:
        for x,z in ellipse_cells(28,28,25,23):
            mat='paving' if y==1 else 'grass'
            if y==1 and ((x-28)/25)**2+((z-28)/23)**2>.88 and not 25<=x<=30:mat='grass'
            s.set((x,y,z),PALETTE[mat][0],'site')
    for z in range(3,19):
        for x in range(26,30):s.set((x,1,z),PALETTE['deck'][0],'site')
    for x,z in [(16,13),(39,13),(16,42),(39,42)]:s.set((x,1,z),PALETTE['light'][0],'site')

def inner(s,c,profile):
    """Photo-derived common interior treatment; no room layout inferred."""
    for h in range(209):
        cx,cz,a,b,phi=profile(h)
        # Hold the vertical study core fixed in both trials. Envelope/floor clusters
        # may follow the model centre; neither implies surveyed concrete-core offset.
        for x,z in ellipse_cells(28.5,28.5,*c['core_radii_blocks'],hollow=True):
            s.set((x,2+h,z),PALETTE['core'][0],'core')
        band=next((i for i,(lo,hi) in enumerate(c['photo_program_bands_blocks']) if lo<=h<hi),None)
        if band is not None:
            lo,hi=c['photo_program_bands_blocks'][band]
            ra,rb=max(3.7,a-2.5),max(3.2,b-2.5)
            floor=h==lo or h==hi-1 or (h-lo)%5==0
            for x,z in ellipse_cells(cx,cz,ra,rb,phi,hollow=not floor):
                # Reserve a 3x3 vertical shaft within this local core; not a working elevator.
                if x in range(27,30) and z in range(27,30):continue
                s.set((x,2+h,z),PALETTE['floor' if floor else 'glass'][0],f'program.{band:02}')
    # A three-cell-wide entrance through the lower core shell; architectural trial.
    for x in range(27,30):
        for z in range(24,29):
            for y in range(2,5):s.set((x,y,z),AIR,'entry')

def crown(s,c,track):
    """Same 16-capsule grammar for both cases; track geometry is route-specific."""
    pts=np.asarray([track(t) for t in np.linspace(0,2*math.pi,257)])
    center=pts.mean(0)
    # Fit a sloped top deck to the input track; do not fill the entire lattice.
    plane=np.linalg.lstsq(np.c_[pts[:,0],pts[:,2],np.ones(len(pts))],pts[:,1],rcond=None)[0]
    xy=pts[:,[0,2]];cx,cz=xy.mean(0);C=np.cov(xy.T);ev,U=np.linalg.eigh(C);ax=math.sqrt(2*ev[1])-.8;az=math.sqrt(2*ev[0])-.8;phi=math.atan2(U[1,1],U[0,1])
    for x,z in ellipse_cells(cx,cz,ax,az,phi):
        y=int(math.floor(plane@[x+.5,z+.5,1]))-1
        s.set((x,y,z),PALETTE['deck'][0],'crown.deck')
    for a,b in zip(pts,pts[1:]):line(s,a,b,'column','crown.track')
    for j in range(c['capsule_count']):
        p=track(2*math.pi*j/c['capsule_count']);x,y,z=np.floor(p).astype(int)
        for dx in [0,1]:
            for dz in [0,1]:
                for dy in [0,1]:
                    s.set((int(x+dx),int(y+dy+1),int(z+dz)),PALETTE['glass' if dy==0 else 'column'][0],f'crown.capsule.{j:02}')
    return {'center_blocks':center.tolist(),'plane_y_from_xz':plane.tolist(),'capsules':16,'capsule_size_blocks':[2,2,2],'track_source':track.__name__}

def write_nbt(scene,path,c):
    meta=export_structure(scene,path,c['data_version'],include_air=False)
    build=inspect_build.load_build(path)
    assert tuple(build.size)==scene.size and build.blocks==scene.blocks,'NBT readback differs'
    reread=Scene(tuple(build.size),dict(build.blocks),dict(scene.owners))
    assert reread.fingerprint()==scene.fingerprint()
    return meta,build,reread
