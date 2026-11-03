const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),run=process.argv[2]||'O09',h=fs.readFileSync(path.join(root,'delivery/Taisho15.html'),'utf8');
class El{constructor(){this.children=[];this.dataset={};this.style={};this.value='';this.clientWidth=1260;this.clientHeight=780;this.classList={toggle(){}};this.modal=false;}set innerHTML(x){this.children=[];this._html=x;}get innerHTML(){return this._html;}append(...x){this.children.push(...x);}setAttribute(k,v){this[k]=v;}showModal(){this.modal=true;}close(){this.modal=false;}click(){}scrollIntoView(){}}
const els={},downloaded=[],ctx=vm.createContext({document:{getElementById:id=>els[id]??=new El(),createElement:()=>new El(),querySelectorAll:()=>[],addEventListener(){}},console,Uint8Array,Blob,atob,URL:{createObjectURL:b=>{downloaded.push(b);return'blob:sample'},revokeObjectURL(){}},setTimeout:f=>f()});
const scripts=[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);scripts.forEach(s=>vm.runInContext(s,ctx));
const g=vm.runInContext('GALLERY',ctx),files=vm.runInContext('FILES',ctx),meta=vm.runInContext('META',ctx);let combinations=0;
function execute(code){return vm.runInContext(code,ctx)}
function check(){execute('render()');const gr=execute('group()'),k=execute('imageKey()');if(!g[gr][k]||els.mainimage.src!==g[gr][k].src)throw Error('missing view');combinations++;}
for(const mode of ['all','district','single']){
 execute(`setMode(${JSON.stringify(mode)})`);
 const entities=mode==='all'?['Taisho15']:mode==='district'?['west','school','station']:meta.buildings.map(b=>b.id);
 for(const e of entities){execute(`state.entity=${JSON.stringify(e)}`);for(const v of execute('availableViews()')){
  execute(`changeView(${JSON.stringify(v)})`);let floors=1;if(mode==='single'&&['inside','plan'].includes(v))floors=v==='inside'&&e==='Station'?2:meta.buildings.find(b=>b.id===e).floors.length;if(v==='layers')floors=2;
  const shots=v==='street'?Object.keys(execute('SHOTS')):['upper_street'];for(const shot of shots)for(let f=0;f<floors;f++)for(let dir=0;dir<4;dir++)for(const period of ['day','night']){execute(`state.floor=${f};state.dir=${dir};state.period=${JSON.stringify(period)};state.shot=${JSON.stringify(shot)}`);check();}
 }}
}
execute("selectBuilding('School');state.dir=3;state.period='day';render()");els.night.onclick();if(execute('state.entity')!=='School'||execute('state.dir')!==3||!execute('imageKey()').endsWith('_night'))throw Error('night loses context');
execute('shiftBuilding(1)');if(execute('state.entity')!=='Library')throw Error('next building');execute('shiftBuilding(-1)');if(execute('state.entity')!=='School')throw Error('previous building');
els.zoomin.onclick();if(execute('state.zoom')!==1.25)throw Error('zoom');els.zoomreset.onclick();if(execute('state.zoom')!==1)throw Error('reset');els.fullscreen.onclick();if(!els.lightbox.modal)throw Error('modal');els.closebox.onclick();if(els.lightbox.modal)throw Error('close');
// Responsive fit calculations: the image must fit both width and height at 100%.
for(const [w,ht]of[[1260,780],[350,260],[900,600]]){els.canvas.clientWidth=w;els.canvas.clientHeight=ht;execute('applyZoom()');const width=parseFloat(els.mainimage.style.width);if(width>w+.01||width/1.4>ht+.01)throw Error('fit');}
for(const [name,data]of Object.entries(files)){
 const target=name.endsWith('.nbt')?'runs/'+run+'/'+name:name==='Taisho15_Spatial.json'?'runs/'+run+'/spec.json':name==='Presentation_Standard_v1.json'?'research/presentation_standard_v1.json':name==='Material_Recipes.json'?'research/recipe_catalog_15.json':'delivery/'+name;
 if(!Buffer.from(data,'base64').equals(fs.readFileSync(path.join(root,target))))throw Error('download payload '+name);execute(`download(${JSON.stringify(name)})`);
}
const ids=[...h.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);if(new Set(ids).size!==ids.length)throw Error('duplicate IDs');if(/@@[A-Z]+@@/.test(h)||/<script\s+src=/.test(h))throw Error('unresolved or external');
const report={view_combinations_checked:combinations,views:Object.values(g).reduce((n,x)=>n+Object.keys(x).length,0),building_choices:meta.buildings.length,preserves_direction_on_day_night:true,previous_next_building:true,fit_width_height_cases:3,zoom_and_fullscreen:true,embedded_downloads_exact:downloaded.length,test_method:'JavaScript execution with DOM stubs; not a real browser rendering test',game:'not run'};
fs.writeFileSync(path.join(root,'runs',run,'html_check.json'),JSON.stringify(report,null,2));console.log(report);
