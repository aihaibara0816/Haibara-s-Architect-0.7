"""Canton-specific component fusion in continuous block coordinates, before NBT.

Model columns supply paths; photo study supplies member grammar and crown style.
This is a reviewed case adapter, not automatic image/model registration.
"""
from common import *
from model_route import ModelRoute, ellipse_fit


def split_columns(triangles):
    """Connected triangle islands, invariant to triangle/vertex ordering."""
    tri = np.asarray(triangles, float)
    parent = list(range(len(tri)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    vertices = {}
    for i, t in enumerate(tri):
        for v in t:
            key = tuple(np.round(v, 5))
            if key in vertices:
                a, b = find(i), find(vertices[key])
                parent[a] = b
            else:
                vertices[key] = i
    islands = {}
    for i in range(len(tri)):
        islands.setdefault(find(i), []).append(i)
    return [tri[idx] for idx in islands.values()]


def section_center(tri, y):
    pts = []
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        a, b = tri[:, i], tri[:, j]
        dy = b[:, 1] - a[:, 1]
        ok = (abs(dy) > 1e-9) & (np.minimum(a[:, 1], b[:, 1]) <= y) & (np.maximum(a[:, 1], b[:, 1]) >= y)
        t = (y - a[ok, 1]) / dy[ok]
        pts.extend(a[ok] + t[:, None] * (b[ok] - a[ok]))
    if not pts:
        raise ValueError(f'No section at y={y}')
    p = np.unique(np.round(pts, 7), axis=0)
    # AABB midpoint avoids triangulation-density bias. It is an approximation to
    # a tapered member's medial axis; no engineering centroid is claimed.
    return (p.min(0) + p.max(0)) / 2


def face_path(a, b):
    """Grid traversal with face-neighbor steps, including exact corner crossings.

    At a tie cross X then Y then Z. The tie bridges are intentionally explicit;
    connectivity of occupied cells still says nothing about stair collision.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    q, end = np.floor(a).astype(int), np.floor(b).astype(int)
    delta = b - a
    sign = np.sign(delta).astype(int)
    result = [tuple(map(int, q))]
    for _ in range(int(np.abs(end-q).sum()) + 1):
        if np.array_equal(q, end):
            return result
        choices = []
        for axis in range(3):
            if q[axis] == end[axis]:
                continue
            boundary = q[axis] + (1 if sign[axis] > 0 else 0)
            choices.append(((boundary-a[axis])/delta[axis], axis))
        _, axis = min(choices)
        q[axis] += sign[axis]
        result.append(tuple(map(int, q)))
    raise AssertionError('Grid traversal did not reach endpoint')


def draw_line(scene, a, b, material, component):
    if material == 'brace':
        material = brace_material(np.asarray(b)-a)
    for p in face_path(a, b):
        scene.set(p, PALETTE[material][0], component)


def validate_parameters(p):
    if p.get('schema') != 'canton-hybrid-0.1':
        raise ValueError('Unsupported parameter schema')
    if p['size_xyz'] != [56,282,56] or p['target_height_blocks'] != 280:
        raise ValueError('V3 comparison keeps the original scale and bounds')
    f, e, c = p['frame'], p['enclosure'], p['crown']
    if f['column_count'] != 24 or c['capsule_count'] != 16:
        raise ValueError('Counts require a separate evidence review')
    if type(f['ring_count']) is not int or not 36 <= f['ring_count'] <= 52:
        raise ValueError('ring_count must be an integer from 36 to 52')
    if f['brace_step'] != 1 or f['column_material'] != 'column' or f['ring_material'] != 'ring' or f['brace_material'] != 'brace':
        raise ValueError('Unsupported member grammar')
    for value, lo, hi in [(f['sample_step_blocks'],.1,.5),(f['body_preserved_until_y'],200,205),
                          (e['inset_blocks'],2.5,3.5),(c['track_center_y'],212,214),
                          (c['tilt_amplitude_blocks'],0,1.5),(c['radius_adjust_blocks'],-.5,.5)]:
        if type(value) not in (int,float) or not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'Parameter outside reviewed bounds: {value}')
    if c['interface_fit_y'] != 206. or type(c['terrace_enabled']) is not bool:
        raise ValueError('Invalid crown interface')
    if e['minimum_radii'] != [3.7,3.2] or e['bands_from'] != 'inputs/common.json':
        raise ValueError('Unsupported enclosure source')
    if p['mast'] != {'source':'B_photo_stepped','center':'snap_to_crown_center_cell','height_end_exclusive':282}:
        raise ValueError('Unsupported mast recipe')


class HybridGeometry:
    def __init__(self, common, params):
        validate_parameters(params)
        self.c, self.p = common, params
        self.route = ModelRoute(common)
        tri = np.concatenate([m['tri'] for m in self.route.meshes if m['role']=='model-frame-columns'])
        islands = split_columns(tri)
        if len(islands) != 24:
            raise ValueError(f'Expected 24 source column islands, got {len(islands)}')
        islands.sort(key=lambda t: math.atan2(section_center(t,6)[2]-28, section_center(t,6)[0]-28))
        self.columns = []
        self.source_records = []
        step = params['frame']['sample_step_blocks']
        for j, t in enumerate(islands):
            y0 = max(2.5,float(t[:,:,1].min())+.2)
            y1 = min(208.,float(t[:,:,1].max())-.2)
            levels = np.unique(np.r_[np.arange(y0,y1,step),y1])
            path = np.asarray([section_center(t,y) for y in levels])
            self.columns.append(path)
            self.source_records.append({'component_id':f'frame.column.{j:02}', 'source_triangles':len(t),
                'source_member_minmax_y':[float(t[:,:,1].min()),float(t[:,:,1].max())],
                'sampled_y_range':[float(y0),float(y1)],'ground_extension_blocks':float(y0-2),
                'identity':'angle of member section at local Y=6; stable for this frozen source'})
        top = np.asarray([self.raw(j,params['crown']['interface_fit_y']) for j in range(24)])
        self.fit = ellipse_fit(top[:,[0,2]])
        self.fit[2] += params['crown']['radius_adjust_blocks']
        self.fit[3] += params['crown']['radius_adjust_blocks']
        cx,cz,a,b,phi = self.fit
        co,si=math.cos(phi),math.sin(phi)
        self.angles=[]
        for p in top:
            dx,dz=p[0]-cx,p[2]-cz
            self.angles.append(math.atan2((-dx*si+dz*co)/b,(dx*co+dz*si)/a))
        self.mast_center=(math.floor(cx)+.5,math.floor(cz)+.5)

    def raw(self,j,y):
        path=self.columns[j]
        if y<path[0,1]:
            return path[0]+(y-path[0,1])/(path[1,1]-path[0,1])*(path[1]-path[0])
        return np.array([np.interp(y,path[:,1],path[:,i]) for i in range(3)])

    def track(self,t):
        cx,cz,a,b,phi=self.fit
        return np.array([cx+a*math.cos(t)*math.cos(phi)-b*math.sin(t)*math.sin(phi),
            self.p['crown']['track_center_y']+self.p['crown']['tilt_amplitude_blocks']*math.cos(t),
            cz+a*math.cos(t)*math.sin(phi)+b*math.sin(t)*math.cos(phi)])

    def end(self,j):
        p=self.track(self.angles[j]);p[1]-=1
        return p

    def at(self,j,y):
        cutoff=self.p['frame']['body_preserved_until_y']
        if y<=cutoff:return self.raw(j,y)
        end=self.end(j);t=(y-cutoff)/(end[1]-cutoff)
        return self.raw(j,cutoff)*(1-t)+end*t

    def frame(self,s):
        cutoff=self.p['frame']['body_preserved_until_y']
        levels=np.linspace(2,cutoff,self.p['frame']['ring_count'])
        for k,y in enumerate(levels):
            for j in range(24):
                draw_line(s,self.at(j,y),self.at((j+1)%24,y),'ring',f'frame.ring.{k:02}')
        for k,(y0,y1) in enumerate(zip(levels,levels[1:])):
            for j in range(24):
                draw_line(s,self.at(j,y0),self.at((j+1)%24,y1),'brace',f'frame.brace.{k:02}.{j:02}')
        # Last connectors deliberately use the crown interface, not raw SKP caps.
        for j in range(24):
            draw_line(s,self.at(j,cutoff),self.end((j+1)%24),'brace',f'crown.connector.{j:02}')
        for j in range(24):
            path=[self.raw(j,2),*[p for p in self.columns[j] if p[1]<=cutoff],self.raw(j,cutoff),self.end(j)]
            for a,b in zip(path,path[1:]):draw_line(s,a,b,'column',f'frame.column.{j:02}')
            draw_line(s,self.end(j),self.track(self.angles[j]),'column',f'crown.connection.{j:02}')

    def inner(self,s):
        # Reuse the V2 interior grammar unchanged; adjust only the envelope inset.
        # Passing a smaller profile affects envelope radii, not the fixed core.
        delta=self.p['enclosure']['inset_blocks']-2.5
        def inset_profile(h):
            cx,cz,a,b,phi=self.route.profile(h)
            return cx,cz,a-delta,b-delta,phi
        inner(s,self.c,inset_profile)

    def crown(self,s):
        # Photo B's low-tilt deck, track and cabin grammar, registered to the
        # tower's upper column envelope rather than its original fixed centre.
        result=crown(s,self.c,self.track)
        cx,cz,a,b,phi=self.fit
        if self.p['crown']['terrace_enabled']:
            # One restrained step near the mast, informed by R12; not measured stairs.
            for x,z in ellipse_cells(cx,cz,a*.50,b*.50,phi):
                s.set((x,int(math.floor(self.p['crown']['track_center_y'])),z),PALETTE['deck'][0],'crown.terrace')
        # Use face-connected track segments and radial deck joints; preserve cabin owners.
        pts=[self.track(t) for t in np.linspace(0,2*math.pi,257)]
        for a,b in zip(pts,pts[1:]):draw_line(s,a,b,'column','crown.track')
        for j in range(24):
            p=self.track(self.angles[j]);q=p.copy()
            q[[0,2]]=q[[0,2]]*.94+np.array([cx,cz])*.06;q[1]-=1
            draw_line(s,p,q,'column',f'crown.connection.{j:02}')
        result.update(track_source='B_photo_grammar_on_A_column_interface',fit_blocks=self.fit,
            tilt_status='1-block amplitude study assumption; not photogrammetric measurement',
            source_capsules_used=False,terrace='single schematic raised deck, not full staircase')
        return result

    def mast(self,s):
        p=self.c['photo_mast'];cx,cz=self.mast_center
        for k,(lo,hi) in enumerate(zip(p['transitions_blocks'],p['transitions_blocks'][1:])):
            r=p['radii_blocks'][k]
            for h in range(lo,hi):
                mat='red' if h>=251 and (h-251)//4%2 else 'mast'
                for x,z in ellipse_cells(cx,cz,r,r):s.set((x,h+2,z),PALETTE[mat][0],f'antenna.tier.{k:02}')
            if lo in p['platform_levels_blocks']:
                for x,z in ellipse_cells(cx,cz,r+1.1,r+1.1):s.set((x,lo+2,z),PALETTE['deck'][0],f'antenna.platform.{lo}')

    def record(self):
        return {'adapter':'canton-hybrid-0.1','coordinate_space':'continuous blocks, X/Y/Z; grade Y=2',
            'source_model_transform':self.route.report['matrix_source_metres_to_blocks'],
            'source_column_records':self.source_records,'source_centerlines':{f'frame.column.{j:02}':p.tolist() for j,p in enumerate(self.columns)},
            'crown_fit_blocks':self.fit,'column_interface_endpoints':[self.end(j).tolist() for j in range(24)],
            'mast_center_xz':list(self.mast_center),'photo_registration':None,
            'preserved_range':'source section centre paths through local Y=204; feet extrapolated to Y=2',
            'modified_range':'above local Y=204 interpolate to photo-style crown plane; thickness quantized independently',
            'model_capsule_centers_used_for_crown':False,
            'not_implemented':['automatic photo pose','pixel depth','generic semantic fusion','safe incremental in-world edits']}
