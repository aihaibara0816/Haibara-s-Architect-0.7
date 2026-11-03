const cv=document.getElementById('c'),gl=cv.getContext('webgl2',{antialias:true,alpha:false,preserveDrawingBuffer:true});
if(!gl)throw Error('此设备没有启用 WebGL2，可使用主页面的固定视图。');
const norm=v=>{let l=Math.hypot(...v);return v.map(x=>x/l)},sub=(a,b)=>a.map((v,i)=>v-b[i]),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function mul(a,b){let r=new Float32Array(16);for(let c=0;c<4;c++)for(let row=0;row<4;row++)for(let k=0;k<4;k++)r[c*4+row]+=a[k*4+row]*b[c*4+k];return r}
function look(eye,target){let z=norm(sub(eye,target)),x=norm(cross(Math.abs(z[1])>.999999?[0,0,-1]:[0,1,0],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1])}
function persp(fov,aspect,near,far){let t=1/Math.tan(fov*Math.PI/360);return new Float32Array([t/aspect,0,0,0,0,t,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0])}
function ortho(l,r,b,t,n,f){return new Float32Array([2/(r-l),0,0,0,0,2/(t-b),0,0,0,0,-2/(f-n),0,-(r+l)/(r-l),-(t+b)/(t-b),-(f+n)/(f-n),1])}
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
function prog(v,f){let p=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,v));gl.attachShader(p,shader(gl.FRAGMENT_SHADER,f));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p}

const vs=`#version 300 es
layout(location=0) in vec3 aPos; layout(location=1) in vec3 aNormal;layout(location=2) in vec3 aColor;layout(location=3) in float aEmission;
uniform mat4 uVP;uniform mat4 uLightVP;out vec3 vPos;out vec3 vNormal;out vec3 vColor;out vec4 vShadow;out float vEmission;
void main(){vec3 p=aPos/32.;vPos=p;vNormal=aNormal;vColor=aColor;vEmission=aEmission;vShadow=uLightVP*vec4(p,1.);gl_Position=uVP*vec4(p,1.);}`;
const fs=`#version 300 es
precision highp float;
in vec3 vPos;in vec3 vNormal;in vec3 vColor;in vec4 vShadow;in float vEmission;
uniform sampler2D uShadow;uniform vec3 uSun;uniform vec3 uEye;uniform vec3 uFog;uniform highp sampler3D uBlockLight;uniform vec3 uSize;uniform float uNight;uniform float uGlass;uniform float uGround;uniform float uConcept;
uniform float uCut;uniform float uMin;out vec4 color;
float shadow(){vec3 q=vShadow.xyz/vShadow.w*.5+.5;if(any(lessThan(q,vec3(0.)))||any(greaterThan(q,vec3(1.))))return 1.;float bias=max(.00065,.0010*(1.-dot(vNormal,uSun)));float s=0.;for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++){float d=texture(uShadow,q.xy+vec2(x,y)/2048.).r;s+=q.z-bias>d?.40:1.;}return s/9.;}
void main(){if(vPos.y>uCut||vPos.y<uMin)discard;
vec3 n=normalize(vNormal),view=normalize(uEye-vPos);float ndl=max(dot(n,uSun),0.);float shade=uConcept>.5?1.:shadow();
float ambient=mix(.57,.30,uNight);float direct=mix(.58,.50,uNight);vec3 tint=mix(vec3(1.02,1.01,.99),vec3(.61,.76,1.03),uNight);
vec3 c=vColor*(ambient+direct*ndl*shade)*tint;
// Ground is display context; a very subtle grid makes the voxel scale readable.
if(uGround>.5){float grid=step(.97,fract(vPos.x/10.))+step(.97,fract(vPos.z/10.));c*=1.-min(grid,1.)*.045;}
if(uNight>.5 && uGround<.5){
 float lev=texture(uBlockLight,clamp((vPos+n*.62)/uSize,vec3(.001),vec3(.999))).r*17.;
 c+=vColor*vec3(1.0,.93,.77)*pow(lev,1.7)*.95;
}
if(vEmission>.5)c=vColor;
float alpha=1.;if(uGlass>.5){float fr=pow(1.-abs(dot(n,view)),3.);c=mix(c,mix(vec3(.61,.77,.81),vec3(.20,.33,.48),uNight),.25+.28*fr);alpha=mix(.76,.48,uNight)+.10*fr;}
float fog=1.-exp(-length(uEye-vPos)*mix(.00010,.00018,uNight));c=mix(c,uFog,uConcept>.5?0.:min(fog,.18));
color=vec4(clamp(c,0.,1.),alpha);
}`;
const main=prog(vs,fs),depth=prog(`#version 300 es
layout(location=0) in vec3 aPos;uniform mat4 uVP;uniform float uCut;uniform float uMin;out vec3 vPos;void main(){vPos=aPos/32.;gl_Position=uVP*vec4(vPos,1.);}`,`#version 300 es
precision highp float;in vec3 vPos;uniform float uCut;uniform float uMin;void main(){if(vPos.y>uCut||vPos.y<uMin)discard;}`);
function uni(p,n,type,val){const loc=gl.getUniformLocation(p,n);if(type==='m')gl.uniformMatrix4fv(loc,false,val);if(type==='3')gl.uniform3fv(loc,val);if(type==='1')gl.uniform1f(loc,val);}
function mesh(bytes,kind){const vao=gl.createVertexArray(),buf=gl.createBuffer();gl.bindVertexArray(vao);gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,bytes,gl.STATIC_DRAW);for(const[i,n,t,norm,off]of[[0,3,gl.UNSIGNED_SHORT,false,0],[1,3,gl.BYTE,true,6],[2,3,gl.UNSIGNED_BYTE,true,9],[3,1,gl.UNSIGNED_BYTE,true,12]]){gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,n,t,norm,14,off);}return{vao,buf,count:bytes.byteLength/14,kind};}
function draw(m,gid){gl.bindVertexArray(m.vao);const r=gid?DATA.ranges[m.kind][gid]:[0,m.count];if(r[1])gl.drawArrays(gl.TRIANGLES,r[0],r[1]);}
const shadowSize=2048,shadow=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,shadow);gl.texImage2D(gl.TEXTURE_2D,0,gl.DEPTH_COMPONENT24,shadowSize,shadowSize,0,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);for(const k of[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,k,gl.CLAMP_TO_EDGE);
const fb=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,shadow,0);gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('无法建立阴影缓冲区');gl.bindFramebuffer(gl.FRAMEBUFFER,null);
let opaque,glass,lightTex,ready=false,renderCount=0,shadowKey='',lastView=null,yaw=225,pending=false,rerun=false,focus=null;
const el=id=>document.getElementById(id);
async function inflate(name){const raw=Uint8Array.from(atob(DATA.bins[name]),c=>c.charCodeAt(0));return new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate'))).arrayBuffer());}
async function init(){
 el('status').textContent='解压模型与灯光…';
 for(const kind of['opaque','glass']){const raw=await inflate(kind);if(raw.byteLength!==DATA.stats[kind].raw_bytes)throw Error('模型数据长度不完整');if(kind==='opaque')opaque=mesh(raw,kind);else glass=mesh(raw,kind);}
 let light=await inflate('light');if(light.length!==DATA.size.reduce((a,b)=>a*b,1))throw Error('灯光数据长度错误');let ld=[...DATA.size];const cap=gl.getParameter(gl.MAX_3D_TEXTURE_SIZE),step=Math.ceil(Math.max(...ld)/cap);if(step>1){ld=ld.map(v=>Math.ceil(v/step));const reduced=new Uint8Array(ld[0]*ld[1]*ld[2]);for(let z=0;z<ld[2];z++)for(let y=0;y<ld[1];y++)for(let x=0;x<ld[0];x++){let v=0;for(let dz=0;dz<step;dz++)for(let dy=0;dy<step;dy++)for(let dx=0;dx<step;dx++){const xx=x*step+dx,yy=y*step+dy,zz=z*step+dz;if(xx<DATA.size[0]&&yy<DATA.size[1]&&zz<DATA.size[2])v=Math.max(v,light[(zz*DATA.size[1]+yy)*DATA.size[0]+xx]);}reduced[(z*ld[1]+y)*ld[0]+x]=v;}light=reduced;}lightTex=gl.createTexture();gl.bindTexture(gl.TEXTURE_3D,lightTex);gl.pixelStorei(gl.UNPACK_ALIGNMENT,1);gl.texImage3D(gl.TEXTURE_3D,0,gl.R8,...ld,0,gl.RED,gl.UNSIGNED_BYTE,light);for(const axis of[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T,gl.TEXTURE_WRAP_R])gl.texParameteri(gl.TEXTURE_3D,axis,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_3D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_3D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
 ready=true;window.modelReady=true;delete DATA.bins;update();
}
function options(){
 const width=Math.min(1440,Math.round(cv.clientWidth*Math.min(devicePixelRatio||1,1.3))),height=Math.min(1000,Math.max(280,Math.round((innerHeight-el('controls').offsetHeight)*Math.min(devicePixelRatio||1,1.3))));cv.style.height=(innerHeight-el('controls').offsetHeight)+'px';
 const aspect=width/height,mode=el('mode').value,id=el('building').value,b=DATA.buildings.find(b=>b.id===id);let gid=0,target=focus||[DATA.size[0]/2,0,DATA.size[2]/2],span=Math.max(DATA.size[0]*.82+DATA.size[2]*.74,220*aspect),cut=10000,min=-1;
 let floor=Number(el('floor').value)||1;
 if(b&&['tower','floor'].includes(mode)){
  gid=DATA.buildings.indexOf(b)+1;el('floor').max=b.floors.length;floor=Math.max(1,Math.min(b.floors.length,floor));el('floor').value=floor;let box=b.geometry_bounds;target=[(box[0][0]+box[0][1])/2,(box[1][0]+box[1][1])/2,(box[2][0]+box[2][1])/2];span=Math.max(b.w+b.d+12,(box[1][1]+12)*aspect);
  if(mode==='floor'){min=b.floors[floor-1]-.01;cut=b.floors[floor-1]+3.99;target[1]=min+1.5;span=Math.max(b.w+b.d+8,(Math.max(b.w,b.d)+6)*aspect);}
 }
 if(mode==='garden'){cut=8.99;target=[DATA.size[0]/2,3,DATA.size[2]/2];}
 span/=Number(el('zoom').value);const angle=yaw*Math.PI/180,pitch=Number(el('pitch').value)*Math.PI/180,dist=500;let eye=[target[0]+Math.sin(angle)*Math.cos(pitch)*dist,target[1]+Math.sin(pitch)*dist,target[2]+Math.cos(angle)*Math.cos(pitch)*dist];
 return{width,height,eye,target,spanX:span,spanZ:span/aspect,gid,cut,min,night:el('night').checked?1:0,mode,id,floor};
}
function render(o){
 cv.width=o.width;cv.height=o.height;const sun=norm(o.night?[-.55,.75,-.5]:[.6,.9,.8]),center=DATA.size.map(v=>v/2),le=center.map((v,i)=>v+sun[i]*500),extent=Math.max(290,Math.hypot(...DATA.size)*.6),lv=mul(ortho(-extent,extent,-extent,extent,20,extent*4),look(le,center));
 gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.disable(gl.BLEND);gl.depthMask(true);
 const sk=[o.gid,o.cut,o.min,o.night].join('/');
 if(sk!==shadowKey){gl.bindFramebuffer(gl.FRAMEBUFFER,fb);gl.viewport(0,0,shadowSize,shadowSize);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(depth);uni(depth,'uVP','m',lv);uni(depth,'uCut','1',o.cut);uni(depth,'uMin','1',o.min);draw(opaque,o.gid);gl.bindFramebuffer(gl.FRAMEBUFFER,null);shadowKey=sk;}
 const fog=o.night?[.045,.075,.11]:[.78,.83,.80];gl.viewport(0,0,o.width,o.height);gl.clearColor(...fog,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(main);const vp=mul(ortho(-o.spanX/2,o.spanX/2,-o.spanZ/2,o.spanZ/2,.3,1800),look(o.eye,o.target));
 for(const[n,t,v]of[['uVP','m',vp],['uLightVP','m',lv],['uSun','3',sun],['uEye','3',o.eye],['uFog','3',fog],['uNight','1',o.night],['uGlass','1',0],['uGround','1',0],['uConcept','1',0],['uSize','3',DATA.size],['uCut','1',o.cut],['uMin','1',o.min]])uni(main,n,t,v);
 gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_3D,lightTex);gl.uniform1i(gl.getUniformLocation(main,'uBlockLight'),1);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,shadow);gl.uniform1i(gl.getUniformLocation(main,'uShadow'),0);draw(opaque,o.gid);
 uni(main,'uGlass','1',1);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);draw(glass,o.gid);gl.depthMask(true);gl.disable(gl.BLEND);
 const err=gl.getError();if(err!==gl.NO_ERROR)throw Error('WebGL '+err);renderCount++;window.lastView=o;window.renderCount=renderCount;lastView=o;
 el('status').textContent=(o.id&&o.gid?o.id+' · '+DATA.buildings.find(b=>b.id===o.id).name:DATA.buildings.length+' 组 · 轨道／检修／调度／研发配套')+(o.mode==='floor'?' · '+o.floor+' 段':'')+'　｜　实际 NBT 几何；材质与光照为浏览器近似显示';
}
function update(){if(!ready)return;if(pending){rerun=true;return;}pending=true;requestAnimationFrame(()=>{try{render(options());}catch(e){el('status').textContent='模型显示错误：'+e.message;window.modelError=e.stack;}pending=false;if(rerun){rerun=false;update();}});}
for(const input of document.querySelectorAll('select,input'))input.addEventListener('input',()=>{if(input.id==='building'){el('mode').value=input.value?'tower':'all';el('zoom').value=1;}if(input.id==='mode'&&['tower','floor'].includes(input.value)&&!el('building').value)el('building').value=DATA.buildings[0].id;update();});
for(const b of document.querySelectorAll('[data-yaw]'))b.onclick=()=>{yaw=Number(b.dataset.yaw);update();};
el('top').onclick=()=>{el('pitch').value=Number(el('pitch').value)>85?32:89;update();};el('reset').onclick=()=>{yaw=225;focus=null;el('zoom').value=1;el('pitch').value=32;el('mode').value='all';el('building').value='';update();};el('full').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen().catch(()=>{});};
const pointers=new Map();let drag=null,pinch=0;
cv.addEventListener('pointerdown',e=>{pointers.set(e.pointerId,[e.clientX,e.clientY]);cv.setPointerCapture(e.pointerId);drag=[e.clientX,e.clientY,yaw,Number(el('pitch').value)];if(pointers.size===2){const[a,b]=[...pointers.values()];pinch=Math.hypot(a[0]-b[0],a[1]-b[1]);}});
cv.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===2){const[a,b]=[...pointers.values()],dist=Math.hypot(a[0]-b[0],a[1]-b[1]);if(pinch)el('zoom').value=Math.min(5,Math.max(.55,Number(el('zoom').value)*dist/pinch));pinch=dist;}else if(drag){yaw=(drag[2]+(e.clientX-drag[0])*.45+720)%360;el('pitch').value=Math.max(12,Math.min(89,drag[3]+(e.clientY-drag[1])*.25));}update();});
for(const name of['pointerup','pointercancel'])cv.addEventListener(name,e=>{pointers.delete(e.pointerId);drag=null;pinch=0;});
cv.addEventListener('wheel',e=>{e.preventDefault();el('zoom').value=Math.min(5,Math.max(.55,Number(el('zoom').value)*Math.exp(-e.deltaY*.001)));update();},{passive:false});window.addEventListener('resize',update);
window.addEventListener('message',e=>{if(e.source!==parent||e.data?.type!=='m01_view')return;const b=DATA.buildings.find(b=>b.id===e.data.id);if(!b)return;el('building').value=b.id;el('mode').value='tower';el('zoom').value=1;update();});
window.captureModel=()=>cv.toDataURL('image/png');init().catch(e=>{window.modelError=e.stack;el('status').textContent='旋转查看不可用：'+e.message+'。可使用主页面的固定视图。';});
