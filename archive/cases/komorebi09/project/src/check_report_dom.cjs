const fs=require('fs'),vm=require('vm'),assert=require('assert');
const dir=process.argv[2],report=process.argv[3],raw=JSON.parse(fs.readFileSync(dir+'/dom.json','utf8')),buildings=JSON.parse(fs.readFileSync(dir+'/buildings.json','utf8'));
const els={},all=[];
function el(a){
 const classes=new Set((a.class||'').split(/\s+/));
 const o={...a,dataset:{},listeners:{},textContent:a.textContent||'',classList:{toggle(c,on){if(on)classes.add(c);else classes.delete(c);},contains(c){return classes.has(c);}}};
 for(const[k,v]of Object.entries(a))if(k.startsWith('data-'))o.dataset[k.slice(5)]=v;
 o.addEventListener=(name,fn)=>o.listeners[name]=fn;
 o.matches=q=>q==='img.zoom'?a.tag==='img'&&classes.has('zoom'):q.startsWith('[data-')?o.dataset[q.slice(6,-1)]!==undefined:false;
 o.closest=q=>o.matches(q)?o:null;o.showModal=()=>o.open=true;o.close=()=>o.open=false;
 return o;
}
for(const a of raw){const o=el(a);all.push(o);if(o.id)els[o.id]=o;}
const listeners={},document={getElementById:id=>els[id],querySelectorAll:q=>{
 if(q==='img[data-img]')return all.filter(x=>x.tag==='img'&&x.dataset.img);
 if(q==='[data-building]')return all.filter(x=>x.dataset.building);
 const m=q.match(/^#([\w-]+) button$/);if(m)return all.filter(x=>x.tag==='button'&&x.parents.includes(m[1]));
 throw Error('Unhandled selector '+q);
},addEventListener:(n,f)=>listeners[n]=f};
vm.runInNewContext(fs.readFileSync(dir+'/script.js','utf8'),{document});
const modes=all.filter(x=>x.dataset.mode);let switches=0,keyboards=0;
for(const b of buildings){
 const lot=all.find(x=>x.tag==='g'&&x.dataset.building===b.id);assert(lot);
 listeners.click({target:lot});assert.equal(els['building-title'].textContent,b.name);
 const [x,y,z]=b.entry;assert.equal(els['tp-command'].textContent,'/tp @s '+(x-82)+' '+(y+62)+' '+(z-56+(b.rotation===180?-3:3))+' '+(b.rotation===180?0:180)+' 0');
 for(const m of modes){
  els['building-views'].listeners.click({target:m});
  const key=b.id+'_'+(m.dataset.mode==='extra'?(b.floors===2?'upper':'detail'):m.dataset.mode);
  assert.equal(els['building-img'].dataset.img,key);assert(els['building-img'].src.startsWith('data:image/webp;base64,'));
  assert.equal(els['download-view'].href,els['building-img'].src);assert.equal(els['download-view'].download,key+'.webp');
  assert.equal(modes.filter(x=>x.classList.contains('active')).length,1);switches++;
 }
 let prevented=false;els['site-map'].listeners.keydown({key:'Enter',target:lot,preventDefault(){prevented=true;}});assert(prevented);keyboards++;
}
const familyCounts={all:18,machiya:4,compact:6,single:8};
for(const [value,count]of Object.entries(familyCounts)){els['building-filter'].listeners.change({target:{value}});assert.equal(document.querySelectorAll('#building-list button').filter(x=>!x.hidden).length,count);}
let hero=0;for(const b of all.filter(x=>x.dataset.view)){els['hero-controls'].listeners.click({target:b});assert.equal(els['hero-img'].dataset.img,b.dataset.view);assert(els['hero-img'].src.startsWith('data:image/webp;'));hero++;}
listeners.click({target:els['building-img']});assert(els.viewer.open&&els['viewer-img'].src===els['building-img'].src);els['viewer-close'].listeners.click();assert(!els.viewer.open);
const r=JSON.parse(fs.readFileSync(report,'utf8'));Object.assign(r,{building_view_switches:switches,map_keyboard_checks:keyboards,family_filter_checks:4,hero_view_switches:hero,modal_open_close:true,full_browser_test:false});fs.writeFileSync(report,JSON.stringify(r,null,2));process.stdout.write(JSON.stringify(r)+'\n');
