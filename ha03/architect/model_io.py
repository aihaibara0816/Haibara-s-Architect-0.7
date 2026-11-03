"""Read actual model geometry into an evidence asset, never executable BuildingSpec.

Normalized geometry is metres, right-handed Y-up, with original origin retained.
Readers preserve available structure; labels are not architectural classification.
"""
from dataclasses import dataclass, field
from pathlib import Path
import base64, hashlib, io, json, math, re, struct, zipfile
from importlib.metadata import version
import numpy as np
import trimesh

FORMATS = ('skp', 'glb', 'gltf', 'obj', 'dae', 'stl', 'ply')
MAX_BYTES = 256 * 1024 * 1024
MAX_TRIANGLES = 2000000

def sha(raw): return hashlib.sha256(raw).hexdigest()
def ident(prefix, value): return prefix + '-' + sha(value.encode())[:20]
def json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf8')

def matrix(value):
    a = np.asarray(value, dtype=float)
    if a.shape != (4,4) or not np.isfinite(a).all() or not np.allclose(a[3], [0,0,0,1], atol=1e-10):
        raise ValueError('Expected finite affine 4x4 matrix')
    if abs(np.linalg.det(a[:3,:3])) < 1e-15: raise ValueError('Singular transform')
    return a

def coordinates(scale, up):
    if scale is None or not math.isfinite(scale) or scale <= 0: raise ValueError('Explicit positive metres_per_unit required')
    axes = {'Y': [[1,0,0],[0,1,0],[0,0,1]], 'Z': [[1,0,0],[0,0,1],[0,-1,0]], 'X': [[0,-1,0],[1,0,0],[0,0,1]]}
    if up not in axes: raise ValueError('Explicit up axis X/Y/Z required')
    out=np.eye(4);out[:3,:3]=np.asarray(axes[up])*scale
    return out

def points(v, t): return np.asarray(v) @ t[:3,:3].T + t[:3,3]

@dataclass
class ModelAsset:
    document: dict
    meshes: dict = field(default_factory=dict)
    curves: dict = field(default_factory=dict)

def mesh(asset, mid, vertices, faces, color=(180,195,190,255), metadata=None):
    v=np.asarray(vertices, dtype=float).reshape((-1,3));raw=np.asarray(faces)
    if raw.size and (not np.issubdtype(raw.dtype,np.integer) or raw.size%3):raise ValueError('Triangle indices must be integers')
    f=raw.astype(np.int64).reshape((-1,3))
    if not len(v) or not len(f):raise ValueError('Empty triangle mesh')
    if not np.isfinite(v).all() or f.min()<0 or f.max()>=len(v):raise ValueError('Invalid mesh coordinates/indices')
    if mid in asset.meshes:raise ValueError('Duplicate mesh identity')
    if len(f)+sum(len(x['faces']) for x in asset.meshes.values())>MAX_TRIANGLES:raise ValueError('Triangle budget exceeded')
    asset.meshes[mid]={'vertices':v,'faces':f,'color':list(color),'metadata':metadata or {}}
    return mid

def node(asset, key, name, parent, local, mesh_ids=(), **extra):
    n={'node_id':key,'name':name,'parent_id':parent,'matrix_to_parent_m':matrix(local).tolist(),'mesh_ids':list(mesh_ids),'curve_ids':[],**extra}
    asset.document['nodes'].append(n);return n

def local_resource(path, key):
    from urllib.parse import unquote
    key=unquote(str(key))
    if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',key) or key.startswith(('/', '\\')):
        raise ValueError('External/absolute resource is not allowed: '+key)
    p=(path.parent/key.replace('\\','/')).resolve()
    if not p.is_relative_to(path.parent.resolve()):raise ValueError('Resource leaves model directory')
    if not p.is_file():raise ValueError('Missing model resource: '+key)
    if p.stat().st_size>MAX_BYTES:raise ValueError('Resource exceeds byte budget')
    return p

class LocalResolver(trimesh.resolvers.Resolver):
    def __init__(self,path,records):self.path=Path(path);self.records=records
    def get(self,key):
        p=local_resource(self.path,key);raw=p.read_bytes()
        self.records[str(p.relative_to(self.path.parent))]=sha(raw);return raw
    def __getitem__(self,key):return self.get(key)
    def namespaced(self,namespace):return LocalResolver(self.path.parent/str(namespace)/self.path.name,self.records)
    def keys(self):return []
    def write(self,name,data):raise ValueError('Read-only resolver')

def _skp(path, asset):
    from openskp import SkpFile
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if sum(x.file_size for x in z.infolist())>MAX_BYTES*4:raise ValueError('Expanded SKP exceeds budget')
    parsed=SkpFile.open(str(path)).parse()
    s=SkpFile.open(str(path)).build_instanced_scene()
    defs=[parsed.root,*parsed.definitions.values()]
    hidden={i.guid:i.hidden for d in defs for i in d.instances if i.guid}
    resources={}
    for r in s.mesh_resources:
        ids=[]
        for i,p in enumerate(r.primitives):
            mat=s.gltf_materials[p.material_index] if 0<=p.material_index<len(s.gltf_materials) else {}
            rgba=mat.get('pbrMetallicRoughness',{}).get('baseColorFactor',[.7,.76,.74,1])
            ids.append(mesh(asset,ident('mesh',r.id+'/'+str(i)),p.positions,p.indices,np.clip(np.asarray(rgba)*255,0,255).astype(int).tolist(),{'source_definition_id':str(r.definition_id),'source_definition_name':r.definition_name,'material_index':p.material_index}))
        resources[r.id]=ids
    cr={}
    for r in s.curve_resources:
        ids=[]
        for i,c in enumerate(r.curves):
            cid=ident('curve',r.id+'/'+str(i));v=np.asarray(c.points_m,dtype=float)
            if not np.isfinite(v).all():raise ValueError('Nonfinite curve')
            asset.curves[cid]={'points':v,'closed':bool(c.closed),'layer':c.layer};ids.append(cid)
        cr[r.id]=ids
    def walk(n,parent=None,path_key='root',parent_hidden=False):
        key=ident('node',path_key);is_hidden=parent_hidden or hidden.get(n.guid,False) or s.layer_hidden.get(n.layer,False)
        row=node(asset,key,n.name,parent,np.asarray(n.matrix).reshape((4,4),order='F'),resources.get(n.mesh_resource_id,[]),source_guid=n.guid or None,definition_name=n.definition_name,layer=n.layer,name_is_generated=n.name_is_generated,hidden=is_hidden,identity_basis='ancestor_guid_path' if n.guid else 'source_path_fallback')
        row['curve_ids']=cr.get(n.curve_resource_id,[])
        for i,c in enumerate(n.children):walk(c,key,path_key+'/'+(c.guid or str(i)),is_hidden)
    walk(s.scene_hierarchy)
    asset.document['source_coordinates']={'metres_per_unit':.0254,'up_axis':'Z','basis':'SKP internal inches; display units do not change geometry','display_units':parsed.units}
    asset.document['source_to_normalized_matrix']=coordinates(.0254,'Z').tolist()
    asset.document['reader']={'name':'openskp','version':version('openskp'),'format_version':parsed.version}
    asset.document['source_structure']={'definitions':len(parsed.definitions),'layers':[{'name':l.name,'hidden':l.hidden} for l in parsed.layers],'materials':len(parsed.materials),'placed_nodes':len(asset.document['nodes']),'hidden_faces':sum(getattr(f,'hidden',False) for d in defs for f in d.faces.values()),'definitions_summary':[{'id':str(d.id),'name':d.name,'vertices':len(d.vertices),'faces':len(d.faces),'instances':len(d.instances)} for d in defs]}
    asset.document['textures']=[{'index':i,'bytes':len(t.data),'sha256':sha(t.data),'mime_type':t.mime_type} for i,t in enumerate(s.textures)]
    asset.document['warnings']+=['SKP reader is third-party; parsing is not an independent SketchUp SDK fidelity check.','All stored mesh geometry is retained. Hidden-face rendering and saved-scene visibility are not reproduced.','Textures remain in original SKP; previews/exports below use base colours, not photographic textures.']

def _dae(path, asset, scale, up):
    from defusedxml.ElementTree import fromstring
    fromstring(path.read_bytes())
    import collada
    c=collada.Collada(str(path),ignore=None)
    if c.scene is None:raise ValueError('COLLADA has no active scene')
    unit=c.assetInfo.unitmeter if c.assetInfo.unitmeter is not None else 1.0
    axis=str(c.assetInfo.upaxis or 'Y_UP')[0]
    if scale is not None and not np.isclose(unit,scale):raise ValueError('Explicit unit contradicts COLLADA metadata')
    if up is not None and up!=axis:raise ValueError('Explicit axis contradicts COLLADA metadata')
    C=coordinates(unit,axis);root=node(asset,'node-root','COLLADA',None,C)
    def walk(n,parent,pth,depth=0):
        if depth>100:raise ValueError('COLLADA graph too deep/cyclic')
        key=ident('node',pth)
        if isinstance(n,collada.scene.Node):
            node(asset,key,n.id or 'Unnamed node',parent,n.matrix,identity_basis='source_id_path')
            for i,ch in enumerate(n.children):walk(ch,key,pth+'/'+str(getattr(ch,'id',i))+'/'+str(i),depth+1)
        elif isinstance(n,collada.scene.GeometryNode):
            ids=[]
            for i,prim in enumerate(n.geometry.primitives):
                if isinstance(prim,collada.polylist.Polylist):
                    # pycollada fan triangulation is unsafe for arbitrary concave/holey polygons.
                    if not np.all(prim.vcounts==3):raise ValueError('COLLADA non-triangle polygons require triangulated export')
                    prim=prim.triangleset()
                if not isinstance(prim,collada.triangleset.TriangleSet):raise ValueError('Unsupported COLLADA primitive; export triangles')
                ids.append(mesh(asset,ident('mesh',pth+'/'+str(i)),prim.vertex,prim.vertex_index,metadata={'source_geometry_id':n.geometry.id}))
            node(asset,key,n.geometry.name or n.geometry.id,parent,np.eye(4),ids,identity_basis='source_geometry_path')
        elif isinstance(n,(collada.scene.CameraNode,collada.scene.LightNode)):
            asset.document['warnings'].append('Camera/light omitted: research uses geometry only')
        else:raise ValueError('Unsupported COLLADA node '+type(n).__name__)
    for i,n in enumerate(c.scene.nodes):walk(n,root['node_id'],str(n.id)+'/'+str(i))
    asset.document['source_coordinates']={'metres_per_unit':unit,'up_axis':axis,'basis':'COLLADA asset metadata/defaults'}
    asset.document['source_to_normalized_matrix']=C.tolist()
    asset.document['reader']={'name':'pycollada','version':version('pycollada')}
    asset.document['warnings'].append('COLLADA transforms and hierarchy retained; texture/material fidelity not supported by this adapter.')

def _gltf_preflight(path, records):
    raw=path.read_bytes()
    if path.suffix.lower()=='.glb':
        if len(raw)<20 or raw[:4]!=b'glTF' or struct.unpack_from('<I',raw,4)[0]!=2 or struct.unpack_from('<I',raw,8)[0]!=len(raw):raise ValueError('Invalid GLB header/length')
        length,kind=struct.unpack_from('<II',raw,12)
        if kind!=0x4e4f534a or length+20>len(raw):raise ValueError('Invalid GLB JSON chunk')
        data=json.loads(raw[20:20+length])
    else:data=json.loads(raw)
    if data.get('asset',{}).get('version')!='2.0':raise ValueError('Only glTF 2.0 is supported')
    if data.get('skins') or data.get('animations') or any(p.get('targets') for m in data.get('meshes',[]) for p in m.get('primitives',[])):
        raise ValueError('Animated/skinned/morph models need an explicit baked static export')
    if data.get('extensionsRequired'):raise ValueError('Required glTF extensions need a dedicated tested decoder')
    for m in data.get('meshes',[]):
        for p in m.get('primitives',[]):
            if p.get('mode',4)!=4:raise ValueError('Only glTF triangle primitives are supported')
    for item in data.get('buffers',[])+data.get('images',[]):
        uri=item.get('uri')
        if uri and not uri.startswith('data:'):
            p=local_resource(path,uri);records[str(p.relative_to(path.parent))]=sha(p.read_bytes())
        elif uri and len(uri)>MAX_BYTES*1.4:raise ValueError('Embedded resource too large')
    return data

def _generic(path,asset,scale,up):
    ext=path.suffix.lower()[1:];records={}
    if ext in ('glb','gltf'):
        _gltf_preflight(path,records)
        if scale is not None and scale!=1:raise ValueError('glTF uses metres; conflicting scale rejected')
        if up is not None and up!='Y':raise ValueError('glTF is Y-up')
        scale,up=1.0,'Y';basis='glTF 2.0 metres/Y-up'
    else:
        if scale is None or up is None:raise ValueError(ext.upper()+' has no reliable units/axis: provide --metres-per-unit and --up')
        basis='Explicit caller declaration; not inferred from building name or dimensions'
    C=coordinates(scale,up)
    s=trimesh.load_scene(str(path),file_type=ext,process=False,maintain_order=True,group_material=False,resolver=LocalResolver(path,records))
    if not s.geometry:raise ValueError('No mesh geometry read')
    resources={}
    for name,g in s.geometry.items():
        if not isinstance(g,trimesh.Trimesh):raise ValueError('Non-triangle geometry needs dedicated adapter')
        mid=ident('mesh',str(name));color=[180,195,190,255]
        if getattr(g.visual,'kind',None):
            try:color=np.asarray(g.visual.main_color,dtype=int).tolist()
            except (AttributeError,ValueError):pass
        resources[name]=mesh(asset,mid,g.vertices,g.faces,color,{'source_geometry_name':str(name)})
    base=str(s.graph.base_frame);node(asset,ident('node',base),base,None,C,identity_basis='reader_source_node_name')
    edges=s.graph.to_edgelist();pending=list(edges);known={base}
    while pending:
        count=len(pending)
        for edge in list(pending):
            parent,child,data=edge
            if str(parent) not in known:continue
            g=data.get('geometry');ids=[resources[g]] if g in resources else []
            node(asset,ident('node',str(child)),str(child),ident('node',str(parent)),data.get('matrix',np.eye(4)),ids,identity_basis='reader_source_node_name')
            known.add(str(child));pending.remove(edge)
        if len(pending)==count:raise ValueError('Disconnected/cyclic scene graph')
    asset.document['source_coordinates']={'metres_per_unit':scale,'up_axis':up,'basis':basis}
    asset.document['source_to_normalized_matrix']=C.tolist()
    asset.document['reader']={'name':'trimesh','version':version('trimesh')}
    asset.document['sidecars']=[{'file':k,'sha256':v} for k,v in sorted(records.items())]
    asset.document['warnings']+=['Material colour is a preview approximation; textures/normals are not retained in the research mesh.','Node identities are deterministic for this input/reader; cross-export or reordered-node identity requires explicit matching.']
    if ext in ('obj','stl','ply'):asset.document['warnings'].append('Original architectural hierarchy may be absent or flattened in this format.')

def analyze(asset):
    nodes=asset.document['nodes'];known={};total=0;world_points=[];curve_points=[]
    for n in nodes:
        if n['node_id'] in known:raise ValueError('Duplicate node ID')
        parent=n['parent_id']
        if parent is not None and parent not in known:raise ValueError('Node parent must precede child')
        t=matrix(n['matrix_to_parent_m']);world=known[parent][1]@t if parent else t
        n['matrix_to_world_m']=world.tolist();known[n['node_id']]=(n,world)
        singular=np.linalg.svd(t[:3,:3],compute_uv=False)
        n['local_nonuniform_or_shear']=bool(not np.allclose(singular,singular[0],rtol=1e-6,atol=1e-10))
        pts=[];n['triangles']=0
        for mid in n['mesh_ids']:
            m=asset.meshes[mid];v=points(m['vertices'][np.unique(m['faces'])],world);pts.append(v);n['triangles']+=len(m['faces'])
        for cid in n['curve_ids']:curve_points.append(points(asset.curves[cid]['points'],world))
        if pts:
            v=np.vstack(pts);n['own_bounds_m']=[v.min(0).tolist(),v.max(0).tolist()];world_points.append(v)
        else:n['own_bounds_m']=None
        total+=n['triangles']
        n['subtree_bounds_m']=n['own_bounds_m'];n['subtree_triangles']=n['triangles']
    for n in reversed(nodes):
        if n['parent_id']:
            p=known[n['parent_id']][0];p['subtree_triangles']+=n['subtree_triangles']
            if n['subtree_bounds_m'] is not None:
                b=n['subtree_bounds_m'];a=p['subtree_bounds_m']
                p['subtree_bounds_m']=b if a is None else [np.minimum(a[0],b[0]).tolist(),np.maximum(a[1],b[1]).tolist()]
    if not world_points:raise ValueError('No placed triangle geometry')
    if total>MAX_TRIANGLES:raise ValueError('Placed triangle budget exceeded')
    v=np.vstack(world_points);bounds=[v.min(0).tolist(),v.max(0).tolist()]
    degenerate=0
    for m in asset.meshes.values():
        t=m['vertices'][m['faces']];degenerate+=int((np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)<1e-12).sum())
    asset.document['statistics']={'nodes':len(nodes),'mesh_resources':len(asset.meshes),'unique_triangles':sum(len(m['faces']) for m in asset.meshes.values()),'placed_triangles':total,'bounds_m':bounds,'size_m':(v.max(0)-v.min(0)).tolist(),'degenerate_resource_triangles':degenerate,'curve_resources':len(asset.curves),'curve_points_placed':sum(len(c) for c in curve_points)}
    asset.document['checks']={'finite_geometry':True,'valid_triangle_indices':True,'valid_parent_graph':True,'physical_accuracy':'unverified','geographic_orientation':'unverified','component_semantics':'unclassified','minecraft_generation':False}
    if degenerate:asset.document['warnings'].append(str(degenerate)+' degenerate resource triangles retained; no silent repair.')
    asset.document['statistics']['nodes_with_nonuniform_local_transform']=sum(n['local_nonuniform_or_shear'] for n in nodes)
    asset.document['warnings']=list(dict.fromkeys(asset.document['warnings']))
    return asset

def read_model(path, *, model_id='model-import', metres_per_unit=None, up=None):
    path=Path(path).resolve()
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_.-]*',model_id):raise ValueError('Invalid model ID')
    ext=path.suffix.lower()[1:]
    if ext not in FORMATS:raise ValueError('Unsupported format '+ext+'; supported: '+', '.join(FORMATS))
    if not path.is_file() or path.stat().st_size>MAX_BYTES:raise ValueError('Missing/oversized model')
    raw=path.read_bytes()
    doc={'schema_version':'model-evidence-0.1','model_id':model_id,'source':{'file':path.name,'bytes':len(raw),'sha256':sha(raw),'format':ext,'license_status':'unknown'},'normalized_coordinates':{'unit':'metre','up_axis':'Y','handedness':'right','origin':'original retained','heading':'not registered to building/front/geographic north'},'nodes':[],'warnings':[],'sidecars':[]}
    a=ModelAsset(doc)
    if ext=='skp':
        if (metres_per_unit is not None and metres_per_unit!=.0254) or (up is not None and up!='Z'):raise ValueError('SKP internal coordinates are inches/Z-up')
        _skp(path,a)
    elif ext=='dae':_dae(path,a,metres_per_unit,up)
    else:_generic(path,a,metres_per_unit,up)
    return analyze(a)

def save_asset(asset,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    arrays={};meta={}
    for k,m in asset.meshes.items():
        arrays[k+'_v']=m['vertices'];arrays[k+'_f']=m['faces'];meta[k]={x:v for x,v in m.items() if x not in ('vertices','faces')}
    curve_meta={}
    for k,c in asset.curves.items():arrays[k+'_p']=c['points'];curve_meta[k]={x:v for x,v in c.items() if x!='points'}
    np.savez_compressed(out/'geometry.npz',**arrays)
    d=dict(asset.document);d['meshes']=meta;d['curves']=curve_meta;d['geometry_sha256']=sha((out/'geometry.npz').read_bytes())
    json_write(out/'model_document.json',d)
    return out

def load_asset(out):
    out=Path(out);d=json.loads((out/'model_document.json').read_text());raw=(out/'geometry.npz').read_bytes()
    if d.get('schema_version')!='model-evidence-0.1':raise ValueError('Unsupported model evidence schema')
    if sha(raw)!=d['geometry_sha256']:raise ValueError('Geometry asset hash mismatch')
    a=ModelAsset(d)
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        for k,m in d['meshes'].items():mesh(a,k,z[k+'_v'],z[k+'_f'],m['color'],m['metadata'])
        for k,c in d['curves'].items():a.curves[k]={'points':z[k+'_p'],**c}
    analyze(a);return a

def selected_nodes(asset,root_ids=None):
    allids={n['node_id'] for n in asset.document['nodes']}
    if root_ids is None:return asset.document['nodes']
    if not root_ids or not set(root_ids)<=allids:raise ValueError('Unknown/empty selection')
    selected=set(root_ids)
    for n in asset.document['nodes']:
        if n['parent_id'] in selected:selected.add(n['node_id'])
    return [n for n in asset.document['nodes'] if n['node_id'] in selected]

def world_meshes(asset,root_ids=None):
    for n in selected_nodes(asset,root_ids):
        t=np.asarray(n['matrix_to_world_m'])
        for mid in n['mesh_ids']:
            m=asset.meshes[mid];f=m['faces'].copy()
            if np.linalg.det(t[:3,:3])<0:f=f[:,::-1]
            yield n,m,points(m['vertices'],t),f

def export_mesh(asset,path,root_ids=None):
    path=Path(path)
    if path.exists():raise ValueError('Export path exists')
    ext=path.suffix.lower()[1:]
    if ext not in ('glb','gltf','obj','stl','ply','dae'):raise ValueError('Unsupported export')
    parts=[];scene=trimesh.Scene(base_frame='world')
    # GLB/glTF preserve selected hierarchy and resource sharing. Other exports bake transforms.
    selected=selected_nodes(asset,root_ids);ids={n['node_id'] for n in selected}
    for n in selected:
        parent=n['parent_id'] if n['parent_id'] in ids else 'world'
        t=n['matrix_to_parent_m'] if n['parent_id'] in ids else n['matrix_to_world_m']
        scene.graph.update(frame_to=n['node_id'],frame_from=parent,matrix=t)
        for mid in n['mesh_ids']:
            m=asset.meshes[mid]
            if mid not in scene.geometry:
                scene.geometry[mid]=trimesh.Trimesh(m['vertices'],m['faces'],process=False,face_colors=m['color'])
            scene.graph.update(frame_to=n['node_id']+'-'+mid,frame_from=n['node_id'],matrix=np.eye(4),geometry=mid)
    for n,m,v,f in world_meshes(asset,root_ids):parts.append(trimesh.Trimesh(v,f,process=False,face_colors=m['color']))
    if not parts:raise ValueError('Selection has no faces')
    if ext=='glb':data=scene.export(file_type='glb')
    elif ext=='gltf':
        data=scene.export(file_type='gltf',merge_buffers=True,embed_buffers=True)
        if set(data)!= {'model.gltf'}:raise ValueError('Unexpected external glTF buffers')
        data=data['model.gltf']
    elif ext=='dae':
        from trimesh.exchange.dae import export_collada
        data=export_collada(parts)
    elif ext=='obj':data=trimesh.util.concatenate(parts).export(file_type=ext,include_texture=False)
    else:data=trimesh.util.concatenate(parts).export(file_type=ext)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data,str) else data)
    return {'file':path.name,'sha256':sha(path.read_bytes()),'unit':'metre','up_axis':'Y','source_sha256':asset.document['source']['sha256'],'selected_roots':root_ids,'hierarchy_preserved':ext in ('glb','gltf'),'curves_exported':False,'textures_exported':False,'scope':'Triangle mesh derivative; original model/asset retains omitted curves and source metadata'}

def candidate_record(asset):
    d=asset.document
    return {'model_id':d['model_id'],'sha256':d['source']['sha256'],'format':d['source']['format'],'source_id':None,'license_status':d['source']['license_status'],'version':d['reader'].get('format_version'),'status':'candidate','transform':None}

def attach_candidate(spec,asset):
    import copy
    from .spec_loader import validate_spec
    s=copy.deepcopy(spec)
    if s.get('schema_version')!='0.2':raise ValueError('Upgrade BuildingSpec to 0.2 first')
    record=candidate_record(asset)
    if any(m['model_id']==record['model_id'] for m in s['research']['models']):raise ValueError('Model ID already present')
    s['research']['models'].append(record);s['research']['model_status']='available'
    s['unresolved'].append('Imported model '+record['model_id']+' is a candidate; source accuracy, anchors and component matching require review.')
    validate_spec(s);return s
