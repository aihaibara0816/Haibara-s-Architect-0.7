const $=id=>document.getElementById(id);
const DIRS={all:['SE','SW','NW','NE'],single:['FR','FL','BL','BR'],elevationAll:['S','E','N','W'],elevationSingle:['F','R','B','L']};
const state={mode:'district',entity:'west',view:'exterior',dir:0,period:'day',floor:0,shot:'upper_street',zoom:1};
const DISTRICTS={west:'西侧主街与林缘院落',school:'学校与文库组团',station:'溪桥会所与车站'};
const SHOTS={mountain:'林中眺望亭与鸟居',river:'河岸砂砾与樱花',yard:'私宅侧后院',upper_street:'上街 · 沿坡路看店面',slope_west:'林中 · 鸟居与下坡',school_court:'学校入口前庭',lower_street:'下街 · 住宅与日常小店',clock_square:'溪桥会所前',station_front:'地方车站门面',bridge_arrival:'桥上看溪谷',side_lane:'连接上下街的侧巷'};
const VIEW_NAMES={exterior:'四向轴测',front:'门面近看',street:'场所近看',elevation:'四面立面',inside:'室内',plan:'平面',section:'剖切',layers:'分层'};
function group(){return state.mode==='single'?state.entity:'Taisho16'}
function building(){return META.buildings.find(b=>b.id===state.entity)}
function availableViews(){return state.mode==='district'?['exterior']:state.mode==='all'?['exterior','street','elevation','plan','section']:['exterior','front','elevation','inside','plan','section','layers']}
function baseKey(){
 if(state.mode==='district')return'district_'+state.entity+'_'+DIRS.all[state.dir];
 if(state.mode==='all')return state.view==='exterior'?'overview_'+DIRS.all[state.dir]:state.view==='street'?state.shot:state.view==='elevation'?'elevation_'+DIRS.elevationAll[state.dir]:state.view==='plan'?'top':'section';
 return state.view==='exterior'?'exterior_'+DIRS.single[state.dir]:state.view==='elevation'?'elevation_'+DIRS.elevationSingle[state.dir]:state.view==='front'?'front':state.view==='inside'?(state.floor===0?'inside':state.entity==='Station'?'platform':'upper_inside'):state.view==='plan'?'plan_'+state.floor:state.view==='layers'?'layer_'+(state.floor===0?'ground':'roof'):'section';
}
function imageKey(){const k=baseKey();return state.period==='night'&&GALLERY[group()][k+'_night']?k+'_night':k}
function button(label,active,fn){const b=document.createElement('button');b.type='button';b.textContent=label;b.className=active?'active':'';b.setAttribute('aria-pressed',String(active));b.onclick=fn;return b}
function setMode(mode){state.mode=mode;state.entity=mode==='single'?META.buildings[0].id:mode==='district'?'west':'Taisho16';state.view='exterior';state.floor=0;state.zoom=1;render()}
function selectBuilding(id){state.mode='single';state.entity=id;state.view='exterior';state.floor=0;state.zoom=1;render();$('viewer').scrollIntoView({behavior:'smooth',block:'start'})}
function shiftBuilding(delta){const ids=META.buildings.map(b=>b.id);let i=ids.indexOf(state.entity);state.entity=ids[(i+delta+ids.length)%ids.length];state.floor=0;state.zoom=1;render()}
function changeView(v){state.view=v;state.floor=0;state.zoom=1;render()}
function zoom(delta){state.zoom=Math.min(3,Math.max(1,Math.round((state.zoom+delta)*100)/100));applyZoom()}
function applyZoom(){const im=$('mainimage'),c=$('canvas'),fit=Math.min(c.clientWidth||1260,(c.clientHeight||900)*1.4);im.style.width=(fit*state.zoom)+'px';im.style.minWidth='0';im.style.maxWidth='none';im.style.marginInline=state.zoom===1?'auto':'0';$('zoomlabel').textContent=Math.round(state.zoom*100)+'%';if(state.zoom===1){$('canvas').scrollLeft=0;$('canvas').scrollTop=0}}
function render(){
 if(!availableViews().includes(state.view))state.view='exterior';
 $('modebuttons').innerHTML='';[['all','整体街区'],['district','片区近看'],['single','单栋建筑']].forEach(([m,n])=>$('modebuttons').append(button(n,state.mode===m,()=>setMode(m))));
 $('entity').innerHTML='';const choices=state.mode==='single'?META.buildings.map(b=>[b.id,b.index.toString().padStart(2,'0')+' · '+b.name]):state.mode==='district'?Object.entries(DISTRICTS):[['Taisho16','18 栋完整街区']];
 choices.forEach(([id,name])=>{const o=document.createElement('option');o.value=id;o.textContent=name;$('entity').append(o)});$('entity').value=state.entity;$('prevbuilding').hidden=state.mode!=='single';$('nextbuilding').hidden=state.mode!=='single';
 $('viewbuttons').innerHTML='';availableViews().forEach(v=>$('viewbuttons').append(button(VIEW_NAMES[v],state.view===v,()=>changeView(v))));
 $('directions').innerHTML='';const directionActive=['exterior','elevation'].includes(state.view);$('directionrow').hidden=!directionActive;
 const dl=state.mode==='single'?(state.view==='elevation'?['正面','右侧','背面','左侧']:['前右','前左','后左','后右']):(state.view==='elevation'?['南面','东面','北面','西面']:['东南','西南','西北','东北']);
 dl.forEach((n,i)=>$('directions').append(button(n,state.dir===i,()=>{state.dir=i;render()})));
 $('shotrow').hidden=!(state.mode==='all'&&state.view==='street');$('shot').innerHTML='';Object.entries(SHOTS).forEach(([id,name])=>{const o=document.createElement('option');o.value=id;o.textContent=name;$('shot').append(o)});$('shot').value=state.shot;
 $('floorbuttons').innerHTML='';let floors=[];
 if(state.mode==='single'){
  if(state.view==='plan')floors=building().floors.map((_,i)=>(i+1)+' 层');
  if(state.view==='inside')floors=state.entity==='Station'?['候车厅','站台']:building().floors.map((_,i)=>(i+1)+' 层');
  if(state.view==='layers')floors=['一层','屋顶'];
 }
 $('floorrow').hidden=!floors.length;floors.forEach((n,i)=>$('floorbuttons').append(button(n,state.floor===i,()=>{state.floor=i;render()})));
 const k=baseKey(),night=!!GALLERY[group()][k+'_night'];$('day').classList.toggle('active',state.period==='day'||!night);$('night').classList.toggle('active',state.period==='night'&&night);$('night').disabled=!night;$('day').setAttribute('aria-pressed',String(state.period==='day'||!night));$('night').setAttribute('aria-pressed',String(state.period==='night'&&night));$('night').title=night?'同方向切换夜景':'此类图纸固定日景';
 const actual=imageKey(),img=GALLERY[group()][actual];if(!img)throw Error('Missing view '+group()+'/'+actual);
 $('mainimage').src=img.src;$('mainimage').alt=img.label;$('caption').textContent=img.label+' · '+(actual.endsWith('_night')?'夜景':'日景');
 $('sceneTitle').textContent=state.mode==='single'?building().name:state.mode==='district'?DISTRICTS[state.entity]:'木漏日溪谷';
 $('sceneDesc').textContent=state.mode==='single'?building().program:state.mode==='district'?'近距离看相邻建筑的大小、进退、屋檐与地形关系。':'保留山体、顺坡小路、河畔广场与 18 栋建筑。';
 $('source').textContent='最终 NBT 离线预览 · '+(state.mode==='single'?'单栋方向以主入口为正面':'场地坐标：北在上、东在右')+' · 非实机截图';
 $('downloadNbt').textContent=state.mode==='single'?'下载本栋 NBT':'下载整街 NBT';applyZoom();
}
function download(name){const value=FILES[name];if(!value)throw Error('Missing download '+name);const bytes=Uint8Array.from(atob(value),c=>c.charCodeAt(0));const u=URL.createObjectURL(new Blob([bytes]));const a=document.createElement('a');a.href=u;a.download=name.endsWith('.nbt')?name.toLowerCase():name;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000)}
$('entity').onchange=()=>{state.entity=$('entity').value;state.floor=0;state.zoom=1;render()};$('shot').onchange=()=>{state.shot=$('shot').value;render()};$('prevbuilding').onclick=()=>shiftBuilding(-1);$('nextbuilding').onclick=()=>shiftBuilding(1);
$('day').onclick=()=>{state.period='day';render()};$('night').onclick=()=>{state.period='night';render()};$('zoomin').onclick=()=>zoom(.25);$('zoomout').onclick=()=>zoom(-.25);$('zoomreset').onclick=()=>{state.zoom=1;applyZoom()};
$('fullscreen').onclick=()=>{$('largeimage').src=GALLERY[group()][imageKey()].src;$('largecaption').textContent=$('caption').textContent;$('lightbox').showModal()};$('closebox').onclick=()=>$('lightbox').close();
$('saveimage').onclick=()=>{const a=document.createElement('a');a.href=GALLERY[group()][imageKey()].src;a.download='Taisho16_'+group()+'_'+imageKey()+'.webp';a.click()};$('downloadNbt').onclick=()=>download(group()+'.nbt');
document.querySelectorAll('[data-building]').forEach(b=>b.onclick=()=>selectBuilding(b.dataset.building));document.querySelectorAll('[data-file]').forEach(b=>b.onclick=()=>download(b.dataset.file));
document.addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(['ArrowLeft','ArrowRight'].includes(e.key)&&['exterior','elevation'].includes(state.view)){state.dir=(state.dir+(e.key==='ArrowRight'?1:3))%4;render();e.preventDefault()}});
document.querySelectorAll('[data-shot]').forEach(b=>b.onclick=()=>{state.mode='all';state.entity='Taisho16';state.view='street';state.shot=b.dataset.shot;state.zoom=1;render();$('viewer').scrollIntoView({behavior:'smooth',block:'start'})});
$('mainimage').onload=applyZoom;if(typeof window!=='undefined')window.addEventListener('resize',applyZoom);
render();
