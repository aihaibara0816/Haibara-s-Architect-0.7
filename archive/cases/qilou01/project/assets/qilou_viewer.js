const DATA=JSON.parse(document.getElementById('data').textContent);
const G=DATA.gallery, FILES=DATA.files;
const $=id=>document.getElementById(id);
let group='Qilou01',kind='exterior',shot='exterior_FR',night=false,zoom=1;
const cats={exterior:'四向轴测',elevation:'四面立面',detail:'街边 / 室内近景',plan:'逐层平面',section:'剖面',layer:'独立楼层',exploded:'分层展开',top:'屋顶俯视'};
const isNight=k=>k.endsWith('_night');
function category(k){if(k.startsWith('exterior_'))return'exterior';if(k.startsWith('elevation_'))return'elevation';if(k.startsWith('plan_')||k==='ground_plan')return'plan';if(k.startsWith('layer_'))return'layer';return ['section','top','exploded'].includes(k)?k:'detail'}
function keys(){return Object.keys(G[group]).filter(k=>!isNight(k))}
function option(value,label){const e=document.createElement('option');e.value=value;e.textContent=label;return e}
function selectOptions(el,items,value){el.replaceChildren(...items.map(x=>option(...x)));el.value=value}
function sync(){
 const all=keys(),available=Object.keys(cats).filter(c=>all.some(k=>category(k)===c));
 if(!available.includes(kind))kind='exterior';
 const shots=all.filter(k=>category(k)===kind);if(!shots.includes(shot))shot=shots[0];
 selectOptions($('subject'),Object.entries(DATA.names),group);
 selectOptions($('kind'),available.map(c=>[c,cats[c]]),kind);
 selectOptions($('shot'),shots.map(k=>[k,G[group][k].label]),shot);
 const hasNight=!!G[group][shot+'_night'];if(!hasNight)night=false;
 $('night').disabled=!hasNight;$('night').textContent=night?'☀ 切到白天':'☾ 切到夜晚';
 $('night').setAttribute('aria-pressed',String(night));
 const rec=G[group][shot+(night?'_night':'')];
 $('mainimg').src=rec.src;$('mainimg').alt=DATA.names[group]+' · '+rec.label+(night?' · 夜景':' · 日景');
 $('caption').textContent=$('mainimg').alt;
 $('viewnote').textContent=kind==='exploded'?'展开示意：各层竖向移开 6 格，家具与平面位置不变。':kind==='plan'||kind==='section'||kind==='layer'?'去顶 / 剖切示意；移除部分遮挡只用于观察内部。':'由实际 NBT 回读生成的离线预览；灯光与部分实体外观为近似。';
 $('currentNBT').textContent='下载'+(group==='Qilou01'?'组合':'此栋')+' NBT';
 $('hash').textContent=rec.source_nbt_sha256;
 $('program').textContent=DATA.programs[group];
 zoom=1;applyZoom();
}
function applyZoom(){$('mainimg').style.width=(zoom*100)+'%';$('mainimg').style.height=(zoom*100)+'%';$('zoomValue').textContent=Math.round(zoom*100)+'%'}
function changeGroup(g){group=g;kind='exterior';shot='exterior_FR';sync()}
function download(name){const raw=atob(FILES[name]),a=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)a[i]=raw.charCodeAt(i);saveBlob(new Blob([a],{type:'application/octet-stream'}),name)}
function saveBlob(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500)}
$('subject').onchange=e=>{group=e.target.value;sync()};
$('kind').onchange=e=>{kind=e.target.value;sync()};
$('shot').onchange=e=>{shot=e.target.value;sync()};
$('night').onclick=()=>{night=!night;sync()};
$('zoomIn').onclick=()=>{zoom=Math.min(3,zoom+.25);applyZoom()};
$('zoomOut').onclick=()=>{zoom=Math.max(1,zoom-.25);applyZoom()};
$('reset').onclick=()=>{zoom=1;applyZoom();$('viewport').scrollTo(0,0)};
$('full').onclick=async()=>{if(document.fullscreenElement)await document.exitFullscreen();else if($('viewer').requestFullscreen)await $('viewer').requestFullscreen();else window.open($('mainimg').src,'_blank')};
$('currentNBT').onclick=()=>download(group+'.nbt');
$('downloadImage').onclick=()=>{const a=document.createElement('a');a.href=$('mainimg').src;a.download=group+'_'+shot+(night?'_night':'')+'.webp';a.click()};
document.querySelectorAll('[data-building]').forEach(b=>b.onclick=()=>{changeGroup(b.dataset.building);$('viewer').scrollIntoView({behavior:'smooth',block:'start'})});
document.querySelectorAll('[data-file]').forEach(b=>b.onclick=()=>download(b.dataset.file));
$('tourArcade').onclick=()=>{group='Qilou01';kind='detail';shot='arcade';sync();$('viewer').scrollIntoView({behavior:'smooth'})};
document.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key)||['SELECT','INPUT','TEXTAREA'].includes(e.target.tagName))return;const list=keys().filter(k=>category(k)===kind);shot=list[(list.indexOf(shot)+(e.key==='ArrowRight'?1:list.length-1))%list.length];sync()});
sync();
