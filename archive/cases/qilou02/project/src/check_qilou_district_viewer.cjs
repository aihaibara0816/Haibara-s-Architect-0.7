// Offline control/download checks with a minimal DOM harness; not a browser-layout test.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),crypto=require('crypto'),path=require('path');
const htmlfile=process.argv[2],doc=fs.readFileSync(htmlfile,'utf8');
const match=doc.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/);assert(match);
const data=JSON.parse(match[1]),code=doc.match(/<script>([\s\S]*?)<\/script>/)[1];
const els=new Map(),created=[],clicks=[];
function el(id){if(!els.has(id))els.set(id,{id,style:{},value:'',textContent:'',dataset:{},options:[],replaceChildren(...x){this.options=x},setAttribute(k,v){this[k]=v},scrollTo(){},scrollIntoView(){},requestFullscreen:async()=>{document.fullscreenElement=els.get(id)}});return els.get(id)}
const byBuilding=[...doc.matchAll(/data-building="([^"]+)"/g)].map(m=>({dataset:{building:m[1]}}));
const byView=[...doc.matchAll(/data-view="([^"]+)"/g)].map(m=>({dataset:{view:m[1]}}));
const byFile=[...doc.matchAll(/data-file="([^"]+)"/g)].map(m=>({dataset:{file:m[1]}}));
const document={getElementById:el,querySelectorAll:q=>q==='[data-building]'?byBuilding:q==='[data-view]'?byView:byFile,createElement:tag=>{let e={tag,click(){clicks.push(this)}};created.push(e);return e},addEventListener(){},fullscreenElement:null,exitFullscreen:async()=>{document.fullscreenElement=null}};
el('data').textContent=match[1];
const context={document,window:{open(){}},console,Blob,Uint8Array,atob,URL:{createObjectURL:()=> 'blob:local',revokeObjectURL(){}},setTimeout:fn=>fn()};
vm.createContext(context);vm.runInContext(code,context);
let views=0,nightPairs=0;
for(const g of Object.keys(data.names)){
 el('subject').onchange({target:{value:g}});
 const categories=el('kind').options.map(o=>o.value);
 for(const cat of categories){
  el('kind').onchange({target:{value:cat}});
  const shots=el('shot').options.map(o=>o.value);
  assert(shots.length);
  for(const shot of shots){
   el('shot').onchange({target:{value:shot}});
   if(el('night')['aria-pressed']==='true')el('night').onclick();
   assert.equal(el('mainimg').src,data.gallery[g][shot].src);
   assert(el('mainimg').alt.includes(data.names[g]));views++;
   if(data.gallery[g][shot+'_night']){assert(!el('night').disabled);el('night').onclick();assert.equal(el('mainimg').src,data.gallery[g][shot+'_night'].src);el('night').onclick();nightPairs++}
   else assert(el('night').disabled);
  }
 }
 el('currentNBT').onclick();assert.equal(clicks.at(-1).download,g+'.nbt');
}
for(const b of byBuilding){b.onclick();assert(el('mainimg').alt.includes(data.names[b.dataset.building]))}
for(const b of byView){b.onclick();assert.equal(el('shot').value,b.dataset.view);assert.equal(el('mainimg').src,data.gallery.Qilou02[b.dataset.view].src)}
for(const b of byFile){assert(data.files[b.dataset.file]);b.onclick();assert.equal(clicks.at(-1).download,b.dataset.file)}
el('tourArcade').onclick();assert.equal(el('shot').value,'arcade');
el('zoomIn').onclick();assert.equal(el('mainimg').style.width,'125%');assert.equal(el('mainimg').style.height,'125%');el('reset').onclick();assert.equal(el('mainimg').style.width,'100%');
assert(!doc.includes('@@'));
for(const [k,b] of Object.entries(data.files)){const disk=k.endsWith('.nbt')?path.join(path.dirname(htmlfile),'../runs',process.argv[3],k):path.join(path.dirname(htmlfile),k);assert(Buffer.from(b,'base64').equals(fs.readFileSync(disk)),k+' embedded bytes differ')}
assert(doc.includes('data-view="turn"'));assert.equal(Object.keys(data.names).length,13);
const downloadHashes=Object.fromEntries(Object.entries(data.files).map(([k,b])=>[k,crypto.createHash('sha256').update(Buffer.from(b,'base64')).digest('hex')]));
const out={control_harness:'pass',day_views:views,night_pairs:nightPairs,total_views:views+nightPairs,subjects:Object.keys(data.names).length,map_card_links:byBuilding.length,quick_views:byView.length,embedded_download_bytes:'exact',downloads:downloadHashes,browser_layout:'not executed: Chromium is not installed',game:'not executed'};
const dest=path.join(path.dirname(htmlfile),'viewer_check.json');fs.writeFileSync(dest,JSON.stringify(out,null,2));console.log(JSON.stringify(out));
