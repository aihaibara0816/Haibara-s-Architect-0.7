"""V3a case adapter: evidence-bound program bands, A roof, thin vanilla members.

Extends the frozen V3 adapter. No writes to the source SKP or parent runs.
This is an authored case interpretation, not learned semantic reconstruction.
"""
from common import *
from hybrid_geometry import HybridGeometry, face_path, draw_line

DIRECTIONS={'north':(0,0,-1),'east':(1,0,0),'south':(0,0,1),'west':(-1,0,0)}
WALL='minecraft:diorite_wall'
BARS='minecraft:iron_bars'

def in_shaft(q):
    x,y,z=q
    return 27<=x<30 and 27<=z<30 and 2<=y<211

def member_state(name, connections=()):
    p={d:('low' if d in connections else 'none') if name==WALL else ('true' if d in connections else 'false') for d in DIRECTIONS}
    if name==WALL:p['up']='true'
    p['waterlogged']='false'
    return name+'['+','.join(f'{k}={v}' for k,v in sorted(p.items()))+']'

def register_state(state):
    name,_=parse_state(state)
    if name==WALL:color='#E3E7E4'
    elif name==BARS:color='#C2CDC9'
    else:raise ValueError('Unsupported thin member')
    PALETTE[state]=(state,color)
    return state

def thin_line(scene,a,b,name,owner):
    state=register_state(member_state(name))
    for q in face_path(a,b):scene.set(q,state,owner)

def connect_thin_members(scene):
    """Write explicit vanilla side states; game neighbor updates are not simulated."""
    for q,state in list(scene.blocks.items()):
        name,_=parse_state(state)
        if name not in [WALL,BARS]:continue
        sides=[]
        for d,v in DIRECTIONS.items():
            near=tuple(q[i]+v[i] for i in range(3))
            n=scene.blocks.get(near)
            if n:
                nn,_=parse_state(n)
                # Full cubes and the two member families provide modeled joins.
                if nn in [WALL,BARS] or not any(t in nn for t in ['_slab','_stairs']):sides.append(d)
        scene.set(q,register_state(member_state(name,sides)),scene.owners[q])

def validate_config(p):
    if p.get('schema')!='canton-v3a-0.1':raise ValueError('Unknown V3a schema')
    if p['target_height_blocks']!=280 or p['size_xyz']!=[56,282,56]:raise ValueError('Frozen scale/bounds required')
    if p['crown']['source']!='A_skp_r03_track_plane_and_ellipse' or p['crown']['capsule_count']!=16:raise ValueError('Reviewed A roof and 16 capsules required')
    if p['frame']['column_count']!=24 or p['frame']['ring_count']!=46:raise ValueError('Member counts frozen')
    if p['frame']['column_block']!=WALL or p['frame']['brace_block']!=BARS:raise ValueError('Unsupported member states')
    if p['crown']['preserve_body_until_y']!=204.:raise ValueError('Inherited body blend starts at Y=204')
    if p['frame']['ring_block']!=PALETTE['ring'][0] or p['frame']['wall_post_width_blocks']!=.5 or p['frame']['bar_post_width_blocks']!=.125:raise ValueError('Vanilla-state geometry cannot be resized through these fields')
    if p['core']['center_xz']!=[28.5,28.5] or p['core']['radii_blocks']!=[3.3,2.8] or p['core']['shaft_xz_half_open']!=[[27,30],[27,30]] or p['core']['shaft_y_half_open']!=[2,211]:raise ValueError('Core/shaft changes require a separate geometry revision')
    if p['mast']['top_local_y']!=281:raise ValueError('Frozen antenna tip required')
    if p['enclosure']['floor_spacing_blocks']!=5 or p['enclosure']['inset_blocks']!=3.:raise ValueError('Unsupported floor/envelope grammar')
    last=-1
    ids=[]
    for z in p['enclosure']['zones']:
        lo,hi=z['height_m']
        if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (lo,hi)):raise ValueError('Nonfinite zone')
        if not 0<=lo<hi<=450 or lo<last:raise ValueError('Overlapping/out-of-range zone')
        last=hi;ids.append(z['id'])
    if ids!=list('ABCDE'):raise ValueError('Five named diagram zones required')

class OpenLatticeGeometry(HybridGeometry):
    def __init__(self,common,config):
        validate_config(config)
        parent=json.loads((ROOT/'inputs/hybrid_parameters.json').read_text())
        super().__init__(common,parent)
        self.config=config
        # Adopt exactly A's ellipse and plane, including direction and offset.
        self.fit=list(self.route.crown_fit)
        self.roof_plane=self.route.plane.copy()
        cx,cz,a,b,phi=self.fit;co,si=math.cos(phi),math.sin(phi)
        self.angles=[]
        for j in range(24):
            top=self.raw(j,206.);dx,dz=top[0]-cx,top[2]-cz
            self.angles.append(math.atan2((-dx*si+dz*co)/b,(dx*co+dz*si)/a))
        self.mast_center=(math.floor(cx)+.5,math.floor(cz)+.5)
        self.zones=[]
        for zone in config['enclosure']['zones']:
            lo,hi=[int(math.floor(x*common['blocks_per_metre']+.5)) for x in zone['height_m']]
            self.zones.append({**zone,'height_blocks_half_open':[lo,hi],'local_y_half_open':[lo+2,hi+2]})

    def track(self,t):return self.route.track(t)

    def deck_y(self,x,z):return math.floor(float(self.roof_plane@[x+.5,z+.5,1]))-1

    def frame(self,s):
        cutoff=self.config['crown']['preserve_body_until_y']
        levels=np.linspace(2,cutoff,46)
        for k,y in enumerate(levels):
            for j in range(24):draw_line(s,self.at(j,y),self.at((j+1)%24,y),'ring',f'frame.ring.{k:02}')
        for k,(y0,y1) in enumerate(zip(levels,levels[1:])):
            for j in range(24):thin_line(s,self.at(j,y0),self.at((j+1)%24,y1),BARS,f'frame.brace.{k:02}.{j:02}')
        for j in range(24):thin_line(s,self.at(j,cutoff),self.end((j+1)%24),BARS,f'crown.connector.{j:02}')
        for j in range(24):
            path=[self.raw(j,2),*[p for p in self.columns[j] if p[1]<=cutoff],self.raw(j,cutoff),self.end(j)]
            for a,b in zip(path,path[1:]):thin_line(s,a,b,WALL,f'frame.column.{j:02}')
            thin_line(s,self.end(j),self.track(self.angles[j]),WALL,f'crown.connection.{j:02}')

    def inner(self,s):
        # Core geometry retained. Interior layout and core shift remain unmeasured.
        for h in range(209):
            for x,z in ellipse_cells(28.5,28.5,*self.c['core_radii_blocks'],hollow=True):
                s.set((x,2+h,z),PALETTE['core'][0],'core')
        for zone in self.zones:
            lo,hi=zone['height_blocks_half_open']
            for h in range(lo,hi):
                cx,cz,a,b,phi=self.route.profile(h)
                a=max(3.7,a-3.);b=max(3.2,b-3.)
                floor=h in [lo,hi-1] or (h-lo)%5==0
                for x,z in ellipse_cells(cx,cz,a,b,phi,hollow=not floor):
                    q=(x,2+h,z)
                    if in_shaft(q):continue
                    if q[1]>=self.deck_y(x,z):continue
                    # Open ranges have no program writes at all, rather than post-hoc erasure.
                    s.set(q,PALETTE['floor' if floor else 'glass'][0],f'program.{zone["id"]}')
        for x in range(27,30):
            for z in range(24,29):
                for y in range(2,5):s.set((x,y,z),AIR,'entry')

    def crown(self,s):
        result=crown(s,self.c,self.track)
        # Separate stepped deck, perimeter track and columns; no full upper volume fill.
        pts=[self.track(t) for t in np.linspace(0,2*math.pi,257)]
        for a,b in zip(pts,pts[1:]):draw_line(s,a,b,'column','crown.track')
        for j in range(24):
            p=self.track(self.angles[j]);q=p.copy()
            q[[0,2]]=q[[0,2]]*.94+np.array(self.fit[:2])*.06;q[1]-=1
            draw_line(s,p,q,'column',f'crown.connection.{j:02}')
        # Keep the pre-existing reserved shaft even where the low edge intersects.
        for q in list(s.blocks):
            if in_shaft(q):s.set(q,AIR,'reserved.shaft')
        result.update(track_source='V2A_model_fitted_plane_and_ellipse',fit_blocks=self.fit,
            tilt_degrees=math.degrees(math.atan(float(np.linalg.norm(self.roof_plane[:2])))),
            tilt_status='source-model fitted value, photo checked qualitatively; not measured from photo',
            deck='stepped voxel approximation of A plane; no auditorium or exact stair reconstruction',
            capsules='16 schematic units; source 24 candidates used only to fit A track, not retained as count')
        return result

    def record(self):
        base=super().record()
        base.update(adapter='canton-v3a-0.1',model_capsule_centers_used_for_crown=True,
            modified_range='upper connections adopt A roof; material section changes throughout frame; diagram-based program bands',
            program_zones=self.zones,roof_plane_y_from_xz=self.roof_plane.tolist(),
            interpretation='human/AI reviewed text-image-model evidence; no automatic semantic segmentation',
            void_rules={'applies_to':'program enclosures and floors',
                'allowed_in_open_ranges':['core','frame','crown connections at upper boundary'],
                'missing_features':['full skywalk/stair path','localized equipment/maintenance decks'],
                'reserved_shaft':'X/Z [27,30), Y [2,211)'})
        return base

def check_voids(blocks,owners,zones):
    allowed_y={y for z in zones for y in range(*z['local_y_half_open'])}
    illegal=[list(q) for q in blocks if owners.get(q,'').startswith('program.') and q[1] not in allowed_y]
    glass_outside=[list(q) for q,state in blocks.items() if 'glass' in state and not owners.get(q,'').startswith('crown.') and q[1] not in allowed_y]
    shaft=[list(q) for q in blocks if in_shaft(q)]
    return {'pass':not(illegal or glass_outside or shaft),'program_cells_in_open_ranges':illegal,
        'glass_cells_in_open_ranges':glass_outside,'reserved_shaft_intrusions':shaft,
        'scope':'open ranges prohibit program infill; frame/core are explicitly allowed, not a universal air-volume solver'}
