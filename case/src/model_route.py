"""Canton-specific reviewed mesh adapter; not installed as a generic Skill."""
import json,math
import numpy as np
from common import ROOT,digest,PALETTE,brace_material

def ellipse_fit(points):
    p=np.asarray(points,float);origin=(p.min(0)+p.max(0))/2
    norm=max(float(np.ptp(p,axis=0).max()),1e-6);q=(p-origin)/norm;x,z=q.T
    a,b,c,d,e=np.linalg.lstsq(np.c_[x*x,x*z,z*z,x,z],np.ones(len(x)),rcond=None)[0]
    Q=np.array([[a,b/2],[b/2,c]]);L=np.array([d,e]);center=-.5*np.linalg.solve(Q,L)
    val=1+center@Q@center;ev,U=np.linalg.eigh(Q)
    if min(ev)<=0 or val<=0:raise ValueError('Non-elliptic source cross section')
    radii=np.sqrt(val/ev)*norm;direction=U[:,0];phi=math.atan2(direction[1],direction[0])
    if phi>math.pi/2:phi-=math.pi
    if phi<-math.pi/2:phi+=math.pi
    return [*(center*norm+origin),*radii,phi]

def section(tri,h):
    pts=[]
    for i,j in [(0,1),(1,2),(2,0)]:
        a,b=tri[:,i],tri[:,j];dy=b[:,1]-a[:,1]
        good=(abs(dy)>1e-9)&(np.minimum(a[:,1],b[:,1])<=h)&(np.maximum(a[:,1],b[:,1])>=h)
        t=(h-a[good,1])/dy[good]
        pts.extend((a[good]+t[:,None]*(b[good]-a[good]))[:,[0,2]].tolist())
    if len(pts)<10:raise ValueError('Insufficient section intersections')
    return np.unique(np.round(pts,6),axis=0)

def sample_triangle(tri,spacing=.20):
    """Dense surface sampling, no flood fill; source interiors stay hollow.

    Slice along the longest AABB dimension; sample every slice segment.
    Sampling is a study rasterizer, not exact triangle/voxel intersection.
    """
    tri=np.asarray(tri,float);axis=int(np.argmax(np.ptp(tri,axis=0)))
    order=np.lexsort((tri[:,2],tri[:,0],tri[:,1],tri[:,axis]));a,b,c=tri[order]
    span=c[axis]-a[axis]
    if span<1e-10:return np.unique(np.floor(tri).astype(int),axis=0)
    result=[]
    for u,v in [(a,b),(b,c)]:
        part=v[axis]-u[axis]
        if part<1e-10:continue
        levels=np.linspace(u[axis],v[axis],max(1,math.ceil(part/spacing))+1)
        pa=a+(levels-a[axis])[:,None]/span*(c-a)
        pb=u+(levels-u[axis])[:,None]/part*(v-u)
        lengths=np.linalg.norm(pb-pa,axis=1)
        n=max(1,math.ceil(float(lengths.max())/spacing))
        for start in range(0,len(levels),256):
            p=pa[start:start+256,None,:]+np.linspace(0,1,n+1)[None,:,None]*(pb-pa)[start:start+256,None,:]
            result.append(np.floor(p.reshape(-1,3)).astype(np.int32))
    result.append(np.floor(tri).astype(np.int32))
    return np.unique(np.concatenate(result),axis=0)

class ModelRoute:
    def __init__(self,c):
        root=ROOT/'inputs/model';doc=json.loads((root/'model_document.json').read_text());groups=json.loads((root/'model_groups.json').read_text())
        assert doc['source']['sha256']=='26d4ca7237b4d3e870b421ba3260412d8e215d63e335beb559e48a4927c3fa72'
        assert digest(root/'geometry.npz')==doc['geometry_sha256']
        by={nid:g['group_id'] for g in groups['groups'] for nid in g['node_ids']}
        self.meshes=[]
        with np.load(root/'geometry.npz',allow_pickle=False) as Z:
            for node in doc['nodes']:
                for mid in node['mesh_ids']:
                    T=np.array(node['matrix_to_world_m']);v=Z[mid+'_v']@T[:3,:3].T+T[:3,3];f=Z[mid+'_f'];role=by[node['node_id']]
                    self.meshes.append({'node':node['node_id'],'mesh':mid,'role':role,'color':doc['meshes'][mid]['color'],'tri':v[f]})
        column_tri=np.concatenate([m['tri'] for m in self.meshes if m['role']=='model-frame-columns'])
        valid=[m for m in self.meshes if m['role']!='model-background'];allv=np.concatenate([m['tri'].reshape(-1,3) for m in valid])
        ymin=float(allv[:,1].min());ymax=float(allv[:,1].max());base=ellipse_fit(section(column_tri,ymin+5))
        theta=base[4];co,si=math.cos(theta),math.sin(theta)
        R=np.array([[co,0,si],[0,1,0],[-si,0,co]])
        scale=(c['target_height_blocks']-1e-6)/(ymax-ymin)
        origin=np.array([base[0],ymin,base[1]]);offset=np.array([28,2,28]);M=np.eye(4);M[:3,:3]=scale*R;M[:3,3]=offset-scale*R@origin
        def xf(v):return v@M[:3,:3].T+M[:3,3]
        self.transform=xf
        # Read model capsule locations only to fit their shared track. Regenerate 16 cabins.
        cap=xf(np.asarray([x['center_m'] for x in groups['capsule_instances']]))
        fit=ellipse_fit(cap[:,[0,2]]);cx,cz,a,b,phi=fit
        plane=np.linalg.lstsq(np.c_[cap[:,0],cap[:,2],np.ones(len(cap))],cap[:,1]-.7,rcond=None)[0]
        self.crown_fit=fit;self.plane=plane
        # Lowest member endpoints are staggered; a slice at the absolute minimum
        # cuts only a few columns and gives a meaningless fitted ellipse.
        self.rows=[[0.,28.,28.,base[2]*scale,base[3]*scale,0.]]
        for h in np.linspace(4,196,49):
            rawy=ymin+h/scale+.3
            p=section(column_tri,rawy);v=np.c_[p[:,0],np.full(len(p),rawy),p[:,1]];f=ellipse_fit(xf(v)[:,[0,2]])
            self.rows.append([float(h),*f])
        self.rows.append([float(cap[:,1].mean()-2),*fit])
        self.rows=np.asarray(self.rows);self.rows[:,-1]=np.unwrap(self.rows[:,-1],period=math.pi)
        self.report={
            'source_sha256':doc['source']['sha256'],'geometry_sha256':doc['geometry_sha256'],
            'model_ground_assumption_y_m':ymin,'model_tip_y_m':ymax,'model_range_m':ymax-ymin,
            'source_origin_assumption_m':origin.tolist(),'base_principal_axis_radians':theta,
            'matrix_source_metres_to_blocks':M.tolist(),'uniform_blocks_per_source_metre':scale,
            'relative_to_280_over_600':scale/c['blocks_per_metre'],
            'physical_registration':'pending; model floor minimum and fitted base ellipse used as study anchors, not surveyed grade/north',
            'photo_camera_registration':None,'photo_mesh_pixel_registration':False,
            'model_components_used':['frame.columns','frame.rings_braces','antenna','crown.track_fit','envelope.center_and_sections'],
            'excluded':['Google Earth terrain/snapshot','unresolved inner mixed mesh','all 24 original capsule meshes','loose curves'],
            'capsule_revision':{'source_candidates':24,'generated':16,'basis':c['capsule_decision'],'method':'fit source centers into an ellipse/plane then place 16 evenly spaced study cabins'},
            'crown_fit_blocks':fit,'crown_plane':plane.tolist(),'profile_rows_blocks':self.rows.tolist(),
            'rasterization':{'method':'surface samples; no volume fill','sample_spacing_blocks':.2,'approximate':True,'minimum_feature':'occupied block for sampled surface; diagonals may touch only at corners'},
            'repairs':['Ground profile uses the complete base+5m section; lowest endpoint slice is rejected because it intersects only a few staggered column feet.'],
            'classification':'case-specific manually reviewed selectors; ring-vs-brace split uses triangle vertical span <0.7 blocks, heuristic'
        }
        for m in self.meshes:m['tri']=xf(m['tri'])

    def profile(self,h):return tuple(float(np.interp(h,self.rows[:,0],self.rows[:,i])) for i in range(1,6))

    def track(self,t):
        cx,cz,a,b,phi=self.crown_fit;x=cx+a*math.cos(t)*math.cos(phi)-b*math.sin(t)*math.sin(phi);z=cz+a*math.cos(t)*math.sin(phi)+b*math.sin(t)*math.cos(phi)
        return np.array([x,self.plane@[x,z,1],z])

    def frame(self,s):
        counts={};trimmed=0
        # Braces/rings first, main columns last, same ownership priority as photo branch.
        for role in ['model-frame-rings-braces','model-frame-columns']:
            cells={};seen=set();trinum=0
            for m in self.meshes:
                if m['role']!=role:continue
                for tri in m['tri']:
                    key=tuple(sorted(tuple(round(float(a),6) for a in p) for p in tri))
                    if key in seen:continue
                    seen.add(key);trinum+=1
                    mat='column' if role=='model-frame-columns' else ('ring' if np.ptp(tri[:,1])<.7 else brace_material(tri[np.argmax(tri[:,1])]-tri[np.argmin(tri[:,1])]))
                    for p in sample_triangle(tri):
                        p=tuple(map(int,p))
                        if p[1]>math.floor(self.plane@[p[0]+.5,p[2]+.5,1]):trimmed+=1;continue
                        if p[1]<2:raise ValueError('Unexpected below-grade raster')
                        cells[p]=mat
            for p,mat in sorted(cells.items()):s.set(p,PALETTE[mat][0],'frame.columns' if role=='model-frame-columns' else 'frame.rings' if mat=='ring' else 'frame.braces')
            counts[role]={'unique_triangles':trinum,'candidate_cells':len(cells)}
        self.report['frame_surface_counts']=counts;self.report['crown_replacement_trimmed_sample_hits']=trimmed

    def mast(self,s):
        seen=set();cells={}
        for m in self.meshes:
            if m['role']!='model-antenna':continue
            color=m['color'];mat='red' if color[0]>color[1]*1.25 and color[0]<150 else 'mast'
            for tri in m['tri']:
                key=tuple(sorted(tuple(round(float(a),6) for a in p) for p in tri))
                if key in seen:continue
                seen.add(key)
                for p in sample_triangle(tri):cells[tuple(map(int,p))]=mat
        for p,mat in sorted(cells.items()):s.set(p,PALETTE[mat][0],'antenna')
        self.report['antenna_unique_triangles']=len(seen)
