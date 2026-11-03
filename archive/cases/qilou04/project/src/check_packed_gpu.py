"""Actual packed vertex/shader readback using Mesa EGL; not a browser/client run."""
from pathlib import Path
import sys,json,re,zlib,base64,ctypes as C,math,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'support'),str(ROOT/'pydeps')]
import numpy as np
from PIL import Image
import render_egl_site as E
R=ROOT/'runs'/sys.argv[1];D=json.loads((R/'interactive_payload.json').read_text());out=ROOT/'review/packed';out.mkdir(exist_ok=True,parents=True)
handles=E.context();gl=E.glapi();I,U,P=E.I,E.U,E.P
call=lambda n,*args:gl[n](*args)
def shader(kind,s):
 s=s.replace('#version 300 es','#version 330 core').replace('precision highp float;','').replace('highp sampler3D','sampler3D');v=call('CreateShader',kind);p=C.c_char_p(s.encode());call('ShaderSource',v,1,C.byref(p),None);call('CompileShader',v);ok=I();call('GetShaderiv',v,0x8B81,C.byref(ok))
 if not ok.value:
  msg=C.create_string_buffer(8192);call('GetShaderInfoLog',v,8192,None,msg);raise RuntimeError(msg.value.decode())
 return v
def prog(v,f):
 p=call('CreateProgram');call('AttachShader',p,shader(0x8B31,v));call('AttachShader',p,shader(0x8B30,f));call('LinkProgram',p);ok=I();call('GetProgramiv',p,0x8B82,C.byref(ok));assert ok.value;return p
text=(ROOT/'assets/interactive_shader_reference.html').read_text();vs=re.search(r'const vs=`(.*?)`;',text,re.S).group(1);fs=re.search(r'const fs=`(.*?)`;',text,re.S).group(1);main=prog(vs,fs)
depth=prog('#version 300 es\nlayout(location=0) in vec3 aPos;uniform mat4 uVP;out vec3 vPos;void main(){vPos=aPos/32.;gl_Position=uVP*vec4(vPos,1.);}', '#version 300 es\nprecision highp float;in vec3 vPos;uniform float uCut;uniform float uMin;void main(){if(vPos.y>uCut||vPos.y<uMin)discard;}')
def gen(kind):x=U();call('Gen'+kind,1,C.byref(x));return x.value
def uni(p,n,v):
 loc=call('GetUniformLocation',p,n.encode())
 if isinstance(v,np.ndarray) and v.shape==(4,4):a=np.ascontiguousarray(v,dtype=np.float32);call('UniformMatrix4fv',loc,1,1,a.ctypes.data)
 elif isinstance(v,(list,tuple,np.ndarray)):a=np.asarray(v,dtype=np.float32);call('Uniform3fv',loc,1,a.ctypes.data)
 else:call('Uniform1f',loc,float(v))
def norm(v):v=np.asarray(v,float);return v/np.linalg.norm(v)
def look(eye,target):
 z=norm(np.array(eye)-target);x=norm(np.cross([0,1,0],z));y=np.cross(z,x);r=np.eye(4);r[:3,:3]=[x,y,z];r[:3,3]=-r[:3,:3]@eye;return r
def ortho(l,r,b,t,n,f):return np.array([[2/(r-l),0,0,-(r+l)/(r-l)],[0,2/(t-b),0,-(t+b)/(t-b)],[0,0,-2/(f-n),-(f+n)/(f-n)],[0,0,0,1.]])
meshes={}
for k in ['opaque','glass']:
 raw=zlib.decompress(base64.b64decode(D['bins'][k]));assert hashlib.sha256(raw).hexdigest()==D['stats'][k]['sha256'];arr=np.frombuffer(raw,np.uint8);vao=gen('VertexArrays');buf=gen('Buffers');call('BindVertexArray',vao);call('BindBuffer',0x8892,buf);call('BufferData',0x8892,len(raw),arr.ctypes.data,0x88E4)
 for i,size,typ,normed,off in [(0,3,0x1403,0,0),(1,3,0x1400,1,6),(2,3,0x1401,1,9),(3,1,0x1401,1,12)]:call('EnableVertexAttribArray',i);call('VertexAttribPointer',i,size,typ,normed,14,off)
 meshes[k]=(vao,len(raw)//14)
def draw(k,gid):
 vao,total=meshes[k];start,count=D['ranges'][k][gid]if gid else[0,total];assert start+count<=total;call('BindVertexArray',vao);call('DrawArrays',4,start,count)
tex=gen('Textures');call('BindTexture',0x0DE1,tex);call('TexImage2D',0x0DE1,0,0x81A6,2048,2048,0,0x1902,0x1405,None)
for k,v in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:call('TexParameteri',0x0DE1,k,v)
fb=gen('Framebuffers');call('BindFramebuffer',0x8D40,fb);call('FramebufferTexture2D',0x8D40,0x8D00,0x0DE1,tex,0);call('DrawBuffer',0);call('ReadBuffer',0);assert call('CheckFramebufferStatus',0x8D40)==0x8CD5;call('BindFramebuffer',0x8D40,0)
lt=gen('Textures');light=np.frombuffer(zlib.decompress(base64.b64decode(D['bins']['light'])),np.uint8);call('BindTexture',0x806F,lt);call('PixelStorei',0x0CF5,1);call('TexImage3D',0x806F,0,0x8229,*D['size'],0,0x1903,0x1401,light.ctypes.data)
for k,v in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F),(0x8072,0x812F)]:call('TexParameteri',0x806F,k,v)
reports=[]
for name,id,floor,night in [('whole','',0,0),('whole_night','',0,1),('A2','A2',0,0),('N08_floor1','N08',1,0),('E6_floor8','E6',8,0)]:
 width,height=1200,820;gid=0;target=[D['size'][0]/2,18,D['size'][2]/2];span=480;cut=10000;miny=-1
 if id:
  b=next(b for b in D['buildings']if b['id']==id);gid=D['buildings'].index(b)+1;box=b['geometry_bounds'];target=[sum(v)/2 for v in box];span=max(b['w']+b['d']+12,(box[1][1]+12)*width/height)
  if floor:miny=b['floors'][floor-1]-.01;cut=miny+4;target[1]=miny+1.5
 pitch=math.radians(55 if floor else 39);eye=np.asarray(target)+np.array([math.cos(pitch)/math.sqrt(2),math.sin(pitch),math.cos(pitch)/math.sqrt(2)])*500
 sun=norm([-.55,.75,-.5]if night else[.6,.9,.8]);center=np.array(D['size'])/2;lv=ortho(-290,290,-290,290,20,1100)@look(center+sun*500,center)
 call('Enable',0x0B71);call('DepthFunc',0x0203);call('Enable',0x0B44);call('CullFace',0x0405);call('Disable',0x0BE2);call('DepthMask',1);call('BindFramebuffer',0x8D40,fb);call('Viewport',0,0,2048,2048);call('Clear',0x0100);call('UseProgram',depth)
 for n,v in [('uVP',lv),('uCut',cut),('uMin',miny)]:uni(depth,n,v)
 draw('opaque',gid);call('BindFramebuffer',0x8D40,0);fog=[.045,.075,.11]if night else[.78,.83,.80];call('Viewport',0,0,width,height);call('ClearColor',*fog,1);call('Clear',0x4000|0x0100);call('UseProgram',main)
 for n,v in [('uVP',ortho(-span/2,span/2,-span*height/width/2,span*height/width/2,.3,1800)@look(eye,target)),('uLightVP',lv),('uSun',sun),('uEye',eye),('uFog',fog),('uNight',night),('uGlass',0),('uGround',0),('uConcept',0),('uSize',D['size']),('uCut',cut),('uMin',miny)]:uni(main,n,v)
 call('ActiveTexture',0x84C1);call('BindTexture',0x806F,lt);call('Uniform1i',call('GetUniformLocation',main,b'uBlockLight'),1);call('ActiveTexture',0x84C0);call('BindTexture',0x0DE1,tex);call('Uniform1i',call('GetUniformLocation',main,b'uShadow'),0);draw('opaque',gid);uni(main,'uGlass',1);call('Enable',0x0BE2);call('BlendFunc',0x0302,0x0303);call('DepthMask',0);draw('glass',gid);call('DepthMask',1);call('Disable',0x0BE2);call('Finish');pixels=np.empty((height,width,4),np.uint8);call('ReadPixels',0,0,width,height,0x1908,0x1401,pixels.ctypes.data);err=call('GetError');assert err==0,hex(err);assert pixels[:,:,:3].std()>10;Image.fromarray(pixels[::-1,:,:3]).save(out/(name+'.png'));reports.append({'name':name,'gid':gid,'floor':floor,'night':night,'gl_error':err,'color_std':float(pixels[:,:,:3].std())});print('GPU',name,flush=True)
report={'pass':True,'scope':'Mesa EGL actual packed attributes, draw ranges, GLSL shaders and pixel readback; browser interaction covered separately; no Minecraft client run','renderer':call('GetString',0x1F01).decode(),'source_nbt_sha256':D['source_nbt_sha256'],'views':reports};(R/'packed_gpu_check.json').write_text(json.dumps(report,indent=2));E.ep('eglTerminate',U,[P])(handles[0])
