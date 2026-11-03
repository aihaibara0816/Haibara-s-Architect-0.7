const fs=require('fs'),vm=require('vm'),assert=require('assert');
const dom=JSON.parse(fs.readFileSync(process.argv[2]+'/dom.json','utf8'));const els={},imgs=[],buttons=[];
function el(a={}){let o={...a,dataset:{},listeners:{},textContent:'',classList:{toggle(){}}};for(const [k,v]of Object.entries(a))if(k.startsWith('data-'))o.dataset[k.slice(5)]=v;o.addEventListener=(name,fn)=>o.listeners[name]=fn;o.closest=()=>o;o.matches=q=>q==='img.zoom'&&o.class?.includes('zoom');o.showModal=()=>o.open=true;o.close=()=>o.open=false;return o;}
for(const id of dom.ids)els[id]=el({id});
for(const a of dom.images){let o=el(a);imgs.push(o);if(a.id)els[a.id]=o;}
for(const a of dom.buttons){let o=el(a);buttons.push(o);if(a.id)els[a.id]=o;}
const listeners={};const document={getElementById:id=>els[id],querySelectorAll:q=>q==='img[data-img]'?imgs.filter(i=>i.dataset.img):buttons.filter(b=>b.parent===q.slice(1).split(' ')[0]),addEventListener:(name,fn)=>listeners[name]=fn};
vm.runInNewContext(fs.readFileSync(process.argv[2]+'/script.js','utf8'),{document,window:{open(){}}});let checks=0;
for(const [control,attr,target]of [['hero-controls','view','hero-img'],['room-controls','room','room-img'],['plan-controls','plan','plan-img']])for(const b of buttons.filter(b=>b.dataset[attr])){els[control].listeners.click({target:b});assert(els[target].src?.startsWith('data:image/'));checks++;}
listeners.click({target:els['room-img']});assert(els.viewer.open&&els['viewer-img'].src);els['close-viewer'].listeners.click();assert(!els.viewer.open);checks+=2;
let p=process.argv[3],r=JSON.parse(fs.readFileSync(p));r.javascript_dom_harness_checks=checks;r.full_browser_test=false;fs.writeFileSync(p,JSON.stringify(r,null,2));process.stdout.write(JSON.stringify(r)+'\n');
