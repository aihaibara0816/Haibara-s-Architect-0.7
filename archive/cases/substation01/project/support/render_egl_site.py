"""Headless EGL renderer for exact NBT-derived meshes; no browser required.

Uses the preserved shader with identical cameras for the new Pazhou case. These are
state-box previews and approximate light propagation, not game screenshots.
"""
from pathlib import Path
import ctypes as C, re, json, math, argparse, hashlib, io, os
import numpy as np
from PIL import Image,PngImagePlugin
ROOT=Path(__file__).resolve().parents[1]
E=C.CDLL('libEGL.so.1');E.eglGetProcAddress.argtypes=[C.c_char_p];E.eglGetProcAddress.restype=C.c_void_p

def ep(name,restype,args):
    f=getattr(E,name);f.restype=restype;f.argtypes=args;return f
def gp(name,restype,args):
    p=E.eglGetProcAddress(name.encode())
    if not p:raise RuntimeError(name+' missing')
    return C.CFUNCTYPE(restype,*args)(p)
I=C.c_int;U=C.c_uint;F=C.c_float;P=C.c_void_p
def context():
    get=gp('eglGetPlatformDisplayEXT',P,[U,P,C.POINTER(I)])
    display=get(0x31DD,None,None);a=I();b=I()
    assert ep('eglInitialize',U,[P,C.POINTER(I),C.POINTER(I)])(display,C.byref(a),C.byref(b))
    assert ep('eglBindAPI',U,[U])(0x30A2)
    attrib=(I*15)(0x3033,1,0x3040,8,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3025,24,0x3038)
    config=P();n=I();assert ep('eglChooseConfig',U,[P,C.POINTER(I),C.POINTER(P),I,C.POINTER(I)])(display,attrib,C.byref(config),1,C.byref(n)) and n.value
    surf=ep('eglCreatePbufferSurface',P,[P,P,C.POINTER(I)])(display,config,(I*5)(0x3057,2600,0x3056,3000,0x3038))
    ctx=ep('eglCreateContext',P,[P,P,P,C.POINTER(I)])(display,config,None,(I*5)(0x3098,3,0x30FB,3,0x3038))
    assert ctx and surf and ep('eglMakeCurrent',U,[P,P,P,P])(display,surf,surf,ctx)
    return display,surf,ctx

def glapi():
    signatures={
    'CreateShader':(U,[U]),'ShaderSource':(None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),'CompileShader':(None,[U]),
    'GetShaderiv':(None,[U,U,C.POINTER(I)]),'GetShaderInfoLog':(None,[U,I,C.POINTER(I),P]),
    'CreateProgram':(U,[]),'AttachShader':(None,[U,U]),'LinkProgram':(None,[U]),'GetProgramiv':(None,[U,U,C.POINTER(I)]),'UseProgram':(None,[U]),
    'GenVertexArrays':(None,[I,C.POINTER(U)]),'BindVertexArray':(None,[U]),'GenBuffers':(None,[I,C.POINTER(U)]),'BindBuffer':(None,[U,U]),
    'BufferData':(None,[U,C.c_ssize_t,P,U]),'EnableVertexAttribArray':(None,[U]),'VertexAttribPointer':(None,[U,I,U,U,I,P]),
    'GetUniformLocation':(I,[U,C.c_char_p]),'UniformMatrix4fv':(None,[I,I,U,P]),'Uniform3fv':(None,[I,I,P]),'Uniform1f':(None,[I,F]),'Uniform1i':(None,[I,I]),
    'GenTextures':(None,[I,C.POINTER(U)]),'BindTexture':(None,[U,U]),'TexImage2D':(None,[U,I,I,I,I,I,U,U,P]),'TexImage3D':(None,[U,I,I,I,I,I,I,U,U,P]),'TexParameteri':(None,[U,U,I]),'ActiveTexture':(None,[U]),'PixelStorei':(None,[U,I]),
    'GenFramebuffers':(None,[I,C.POINTER(U)]),'BindFramebuffer':(None,[U,U]),'FramebufferTexture2D':(None,[U,U,U,U,I]),'DrawBuffer':(None,[U]),'ReadBuffer':(None,[U]),'CheckFramebufferStatus':(U,[U]),
    'Viewport':(None,[I,I,I,I]),'ClearColor':(None,[F,F,F,F]),'Clear':(None,[U]),'Enable':(None,[U]),'Disable':(None,[U]),'CullFace':(None,[U]),'DepthFunc':(None,[U]),'DepthMask':(None,[U]),'BlendFunc':(None,[U,U]),
    'DrawArrays':(None,[U,I,I]),'Finish':(None,[]),'ReadPixels':(None,[I,I,I,I,U,U,P]),'GetString':(C.c_char_p,[U]),'GetError':(U,[])}
    return {k:gp('gl'+k,*v) for k,v in signatures.items()}

def main(label,viewfile,emission_policy='material'):
    handles=context();gl=glapi()
    def call(k,*a):return gl[k](*a)
    def shader(kind,txt):
        txt=txt.replace('#version 300 es','#version 330 core').replace('precision highp float;','').replace('highp sampler3D','sampler3D')
        s=call('CreateShader',kind);text=C.c_char_p(txt.encode());call('ShaderSource',s,1,C.byref(text),None);call('CompileShader',s)
        ok=I();call('GetShaderiv',s,0x8B81,C.byref(ok))
        if not ok.value:
            msg=C.create_string_buffer(8192);call('GetShaderInfoLog',s,8192,None,msg);raise RuntimeError(msg.value.decode())
        return s
    def program(v,f):
        p=call('CreateProgram');call('AttachShader',p,shader(0x8B31,v));call('AttachShader',p,shader(0x8B30,f));call('LinkProgram',p)
        ok=I();call('GetProgramiv',p,0x8B82,C.byref(ok));assert ok.value;return p
    shader_file=ROOT/'assets/render_shader_reference.html'
    if not shader_file.exists():shader_file=ROOT.parent/'assets/render_shader_reference.html'
    html=shader_file.read_text()
    vs=re.search(r'const vs=`(.*?)`;',html,re.S).group(1);fs=re.search(r'const fs=`(.*?)`;',html,re.S).group(1)
    from detail_lab.shading import emission_shader
    fs=emission_shader(fs,emission_policy)
    mainp=program(vs,fs)
    depth=program('#version 330 core\nlayout(location=0) in vec3 aPos;uniform mat4 uVP;void main(){gl_Position=uVP*vec4(aPos,1.);}', '#version 330 core\nvoid main(){}')
    def uni(p,n,v):
        loc=call('GetUniformLocation',p,n.encode())
        if isinstance(v,np.ndarray) and v.shape==(4,4):
            a=np.ascontiguousarray(v,dtype=np.float32);call('UniformMatrix4fv',loc,1,1,a.ctypes.data)
        elif isinstance(v,(list,tuple,np.ndarray)):
            a=np.asarray(v,dtype=np.float32);call('Uniform3fv',loc,1,a.ctypes.data)
        else:call('Uniform1f',loc,float(v))
    def gen(name):
        x=U();call('Gen'+name,1,C.byref(x));return x.value
    def mesh(a):
        a=np.ascontiguousarray(a,dtype=np.float32);vao=gen('VertexArrays');buf=gen('Buffers');call('BindVertexArray',vao);call('BindBuffer',0x8892,buf);call('BufferData',0x8892,a.nbytes,a.ctypes.data,0x88E4)
        for i,size,off in [(0,3,0),(1,3,12),(2,3,24),(3,1,36)]:call('EnableVertexAttribArray',i);call('VertexAttribPointer',i,size,0x1406,0,40,off)
        return vao,a.shape[0]
    def draw(m):call('BindVertexArray',m[0]);call('DrawArrays',4,0,m[1])
    def norm(v):v=np.asarray(v,float);return v/np.linalg.norm(v)
    def look(eye,target):
        z=norm(np.asarray(eye)-target);x=norm(np.cross([0,0,-1] if abs(z[1])>.99999 else [0,1,0],z));y=np.cross(z,x)
        r=np.eye(4);r[:3,:3]=[x,y,z];r[:3,3]=-r[:3,:3]@eye;return r
    def ortho(l,r,b,t,n,f):
        return np.array([[2/(r-l),0,0,-(r+l)/(r-l)],[0,2/(t-b),0,-(t+b)/(t-b)],[0,0,-2/(f-n),-(f+n)/(f-n)],[0,0,0,1.]])
    def persp(fov,aspect,n=.3,f=1600):
        t=1/math.tan(math.radians(fov)/2);return np.array([[t/aspect,0,0,0],[0,t,0,0],[0,0,(f+n)/(n-f),2*f*n/(n-f)],[0,0,-1,0]])
    root=ROOT/'previews'/label;meta=json.loads((root/'scene/scene.json').read_text());arrays={n:np.fromfile(root/'scene'/f'{n}.bin',dtype='<f4').reshape(-1,10) for n in ['opaque','glass']}
    for name,a in arrays.items():
        assert a.size==meta['triangles'][name]*3*10,(name,a.size,meta['triangles'][name])
    light=np.fromfile(root/'scene/blocklight.bin',np.uint8)
    tex=gen('Textures');call('BindTexture',0x0DE1,tex);call('TexImage2D',0x0DE1,0,0x81A6,4096,4096,0,0x1902,0x1405,None)
    for k,v in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:call('TexParameteri',0x0DE1,k,v)
    fb=gen('Framebuffers');call('BindFramebuffer',0x8D40,fb);call('FramebufferTexture2D',0x8D40,0x8D00,0x0DE1,tex,0);call('DrawBuffer',0);call('ReadBuffer',0);assert call('CheckFramebufferStatus',0x8D40)==0x8CD5;call('BindFramebuffer',0x8D40,0)
    lt=gen('Textures');call('BindTexture',0x806F,lt);call('PixelStorei',0x0CF5,1);call('TexImage3D',0x806F,0,0x8229,*meta['size_xyz'],0,0x1903,0x1401,light.ctypes.data)
    for k,v in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F),(0x8072,0x812F)]:call('TexParameteri',0x806F,k,v)
    ground=mesh(np.array([[*p,0,1,0,.71,.75,.72,0] for p in [[-1000,-.03,-1000],[-1000,-.03,1000],[1000,-.03,1000],[-1000,-.03,-1000],[1000,-.03,1000],[1000,-.03,-1000]]]))
    records=[]
    for v in json.loads(Path(viewfile).read_text()):
        ms={}
        for key,a in arrays.items():
            tri=a.reshape(-1,3,10);mask=np.ones(len(tri),bool)
            if 'cutY' in v:mask&=(tri[:,:,1]<=v['cutY']).all(axis=1)
            if 'minY' in v:mask&=(tri[:,:,1]>=v['minY']).all(axis=1)
            if 'cutX' in v:mask&=(tri[:,:,0]<=v['cutX']).all(axis=1)
            if 'bounds' in v:
                x0,z0,x1,z1=v['bounds'];mask&=((tri[:,:,0]>=x0)&(tri[:,:,0]<=x1)&(tri[:,:,2]>=z0)&(tri[:,:,2]<=z1)).all(axis=1)
            aa=tri[mask]
            if 'explode_floors' in v:
                aa=aa.copy()
                levels=np.searchsorted(v['explode_floors'],aa[:,:,1].mean(axis=1)+.001,side='right')-1
                aa[:,:,1]+=np.maximum(0,levels)[:,None]*v.get('explode_gap',6)
            if key=='glass':
                direction=norm(np.array(v['target'])-v['eye']);d=aa[:,:,:3].mean(axis=1)@direction;aa=aa[np.argsort(-d,kind='stable')]
            ms[key]=mesh(aa.reshape(-1,10))
        w,h=v['width'],v['height'];night=1 if v.get('night') else 0
        # Optional, recorded case lighting; unchanged defaults replay older views.
        sun_input=v.get('sun_night' if night else 'sun_day',[-.55,.75,-.5] if night else [-.6,.9,-.8])
        if len(sun_input)!=3 or not np.isfinite(sun_input).all() or np.linalg.norm(sun_input)<1e-8:
            raise ValueError('sun direction must be a finite nonzero 3-vector')
        sun=norm(sun_input);center=np.array(meta['size_xyz'])/2;extent=max(230,float(np.linalg.norm(meta['size_xyz']))*.6);lv=ortho(-extent,extent,-extent,extent,20,extent*4)@look(center+sun*(extent*2),center)
        call('Enable',0x0B71);call('DepthFunc',0x0203);call('Enable',0x0B44);call('CullFace',0x0405);call('Disable',0x0BE2);call('DepthMask',1)
        call('BindFramebuffer',0x8D40,fb);call('Viewport',0,0,4096,4096);call('Clear',0x0100);call('UseProgram',depth);uni(depth,'uVP',lv);draw(ms['opaque']);call('BindFramebuffer',0x8D40,0)
        fog=[.075,.13,.18] if night else [.84,.89,.89];call('Viewport',0,0,w,h);call('ClearColor',*fog,1);call('Clear',0x4000|0x0100);call('UseProgram',mainp)
        projection=ortho(-v['spanX']/2,v['spanX']/2,-v['spanZ']/2,v['spanZ']/2,.3,1600) if v.get('ortho') else persp(v['fov'],w/h)
        for n,value in [('uVP',projection@look(v['eye'],v['target'])),('uLightVP',lv),('uSun',sun),('uEye',v['eye']),('uFog',fog),('uNight',night),('uGlass',0),('uGround',0),('uConcept',1 if v.get('concept') else 0),('uSize',meta['size_xyz'])]:uni(mainp,n,value)
        call('ActiveTexture',0x84C1);call('BindTexture',0x806F,lt);call('Uniform1i',call('GetUniformLocation',mainp,b'uBlockLight'),1)
        call('ActiveTexture',0x84C0);call('BindTexture',0x0DE1,tex);call('Uniform1i',call('GetUniformLocation',mainp,b'uShadow'),0)
        draw(ms['opaque']);uni(mainp,'uGround',1);draw(ground);uni(mainp,'uGround',0);uni(mainp,'uGlass',1);call('Enable',0x0BE2);call('BlendFunc',0x0302,0x0303);call('DepthMask',0);draw(ms['glass']);call('DepthMask',1);call('Disable',0x0BE2);call('Finish')
        pixels=np.empty((h,w,4),np.uint8);call('ReadPixels',0,0,w,h,0x1908,0x1401,pixels.ctypes.data);err=call('GetError');assert err==0,hex(err)
        path=root/(v['id']+'.png');info=PngImagePlugin.PngInfo();info.add_text('source_nbt_sha256',meta['source_nbt_sha256']);info.add_text('camera',json.dumps(v));info.add_text('emission_policy',emission_policy)
        buffer=io.BytesIO();Image.fromarray(pixels[::-1,:,:3]).save(buffer,format='PNG',pnginfo=info)
        temp=path.with_suffix('.png.tmp')
        with temp.open('wb') as stream:
            stream.write(buffer.getvalue());stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
        records.append({'image':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_nbt_sha256':meta['source_nbt_sha256'],'camera':v,'emission_policy':emission_policy,'renderer':call('GetString',0x1F01).decode()});print(label,v['id'],flush=True)
    (root/'render_report.json').write_text(json.dumps(records,indent=2));ep('eglTerminate',U,[P])(handles[0])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('views');a=p.parse_args();main(a.label,a.views)
