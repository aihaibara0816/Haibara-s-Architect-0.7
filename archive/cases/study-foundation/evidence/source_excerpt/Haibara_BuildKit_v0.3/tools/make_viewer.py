"""Self-contained offline Canvas viewer; no remote scripts or credentials."""
import json, struct, base64
from pathlib import Path
from voxel_core import build_mesh

def make_viewer(build,title,path,meta):
    mesh=build_mesh(build)
    payload={'size':list(build.size),'mesh_base64':base64.b64encode(struct.pack('<'+str(len(mesh))+'f',*mesh)).decode('ascii'),'meta':meta,'title':title}
    template=(Path(__file__).parent/'viewer_template.html').read_text(encoding='utf8')
    text=template.replace('__BUILD_PAYLOAD__',json.dumps(payload,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c'))
    with Path(path).open('x',encoding='utf8') as f:f.write(text)
    return {'triangles':len(mesh)//30,'path':str(path)}
