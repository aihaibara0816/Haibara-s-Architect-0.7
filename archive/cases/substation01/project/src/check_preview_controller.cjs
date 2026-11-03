// Regression check for parent-page loading/visibility. Does not simulate WebGL or a browser renderer.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..'),doc=fs.readFileSync(path.join(root,'deliverables/Substation01.html'),'utf8');
const script=doc.match(/<script>([\s\S]*?)<\/script>/)[1];
function scenario(){
 const elements=[],events={},timers=new Map(),messages=[],downloads=[];let timerId=0,urlCount=0;
 class Element{
  constructor(tag,a){Object.assign(this,{tag,attrs:a,id:a.id||'',hidden:'hidden'in a,disabled:false,dataset:{},style:{},textContent:'',srcdoc:'',srcdocWrites:0});for(const[k,v]of Object.entries(a))if(k.startsWith('data-'))this.dataset[k.slice(5)]=v;const classes=new Set((a.class||'').split(' '));this.classList={add:x=>classes.add(x),remove:x=>classes.delete(x),toggle:(x,v)=>v?classes.add(x):classes.delete(x)};}
  scrollIntoView(){}click(){downloads.push(this.download);if(this.onclick)this.onclick();}
 }
 for(const m of doc.matchAll(/<(button|img|iframe|div|p|section)\b([^>]*)>/g)){
  const a={};for(const q of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))a[q[1]]=q[2]||'';elements.push(new Element(m[1],a));
 }
 const byId=Object.fromEntries(elements.filter(x=>x.id).map(x=>[x.id,x]));
 const frame=byId.modelFrame;frame.parentElement=elements.find(x=>x.attrs.class==='modelbox');frame.contentWindow={postMessage:(...x)=>messages.push(x)};
 const window={addEventListener:(name,fn)=>(events[name]??=[]).push(fn)};
 const context={window,document:{getElementById:id=>byId[id],querySelectorAll:selector=>elements.filter(x=>selector.slice(1,-1)in x.attrs),createElement:tag=>new Element(tag,{})},setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId;},clearTimeout:id=>timers.delete(id),atob:s=>Buffer.from(s,'base64').toString('binary'),Uint8Array,TextDecoder,Blob,URL:{createObjectURL:()=>{urlCount++;return'blob:test';},revokeObjectURL:()=>{}}};
 vm.runInNewContext(script,context,{timeout:5000});
 return{byId,frame,window,messages,downloads,timers,elements,urlCount:()=>urlCount,message:(source,state,message='')=>events.message.forEach(fn=>fn({source,data:{type:'substation_model_state',state,message}}))};
}
const a=scenario();assert.equal(a.window.modelPreviewState,'idle');assert(a.byId.modelFallback.src.startsWith('data:image/'));assert(a.frame.hidden);
a.elements.find(x=>x.dataset.facility==='T2').onclick();
assert.equal(a.window.modelPreviewState,'loading');assert.equal(a.urlCount(),0);assert(!a.frame.hidden);assert(!a.byId.modelcover.hidden);assert(a.frame.srcdoc.startsWith('<!doctype html>'));assert(a.frame.srcdoc.includes('新港枢纽变电站'));
a.message({},'ready');assert(!a.byId.modelcover.hidden,'untrusted frame must not hide the loading cover');
a.message(a.frame.contentWindow,'ready');assert.equal(a.window.modelPreviewState,'ready');assert(a.byId.modelcover.hidden);assert.equal(a.messages[0][0].id,'T2');
a.elements.find(x=>x.dataset.facility==='control').onclick();assert.equal(a.messages[1][0].id,'control');
a.message(a.frame.contentWindow,'error','GPU context unavailable');assert.equal(a.window.modelPreviewState,'fallback');assert(!a.byId.modelcover.hidden);assert(!a.byId.downloadModel.hidden);assert(!a.byId.loadModel.disabled);
a.byId.downloadModel.onclick();assert.equal(a.downloads[0],'Substation01_Model.html');
a.byId.loadModel.onclick();assert.equal(a.window.modelPreviewState,'loading');a.message(a.frame.contentWindow,'ready');assert.equal(a.window.modelPreviewState,'ready');
const b=scenario();b.byId.loadModel.onclick();[...b.timers.values()].find(t=>t.ms===20000).fn();assert.equal(b.window.modelPreviewState,'fallback');assert(!b.byId.modelcover.hidden);assert(!b.byId.downloadModel.hidden);assert(b.byId.modelFallback.src.startsWith('data:image/'));
const out={pass:true,scope:'parent controller regression; actual WebGL/browser rendering is separate',checks:['srcdoc embeds the complete UTF-8 model without blob page navigation','static preview stays visible until first rendered-frame acknowledgement','facility choice queued until model readiness','unrelated message sources ignored','load error and timeout retain image, enable retry and standalone download','retry can return to ready state'],source_nbt_sha256:JSON.parse(fs.readFileSync(path.join(root,'runs/S04/spec.json'),'utf8')).source_nbt_sha256};
fs.writeFileSync(path.join(root,'runs/S04/preview_fix_check.json'),JSON.stringify(out,null,2));console.log(JSON.stringify(out));
