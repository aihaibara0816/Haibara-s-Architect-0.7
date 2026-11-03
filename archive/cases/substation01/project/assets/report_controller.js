for(const im of document.querySelectorAll('[data-img]'))im.src=IMAGES[im.dataset.img];
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>{
 document.getElementById('heroImage').src=IMAGES[b.dataset.view];
 document.getElementById('viewcaption').textContent=LABELS[b.dataset.view];
 document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b));
};
const modelFrame=document.getElementById('modelFrame'),modelCover=document.getElementById('modelcover'),modelBox=modelFrame.parentElement;
const modelButton=document.getElementById('loadModel'),modelMessage=document.getElementById('modelMessage');
let modelStarted=false,modelReady=false,pendingFacility=null,modelTimer=null;
const modelBytes=()=>Uint8Array.from(atob(MODEL),c=>c.charCodeAt(0));
function modelFailure(reason){
 clearTimeout(modelTimer);modelStarted=false;modelReady=false;modelCover.hidden=false;
 modelButton.disabled=false;modelButton.textContent='重新打开三维';
 modelMessage.textContent='三维暂未打开，先显示全站预览。可以重试，或下载独立预览页打开。';
 modelMessage.title=reason||'';document.getElementById('downloadModel').hidden=false;
 window.modelPreviewState='fallback';window.modelPreviewError=reason||'';
}
function sendFacility(){if(modelReady&&pendingFacility){modelFrame.contentWindow.postMessage({type:'m01_view',id:pendingFacility},'*');pendingFacility=null;}}
function loadModel(id){
 if(id)pendingFacility=id;
 if(modelReady){sendFacility();return;}
 if(modelStarted)return;
 modelStarted=true;window.modelPreviewState='loading';window.modelPreviewError=null;
 modelBox.classList.add('is-loading');modelCover.hidden=false;modelFrame.hidden=false;
 modelButton.disabled=true;modelButton.textContent='正在打开三维…';
 modelMessage.textContent='正在读取模型，画面出现后即可旋转查看。';
 document.getElementById('downloadModel').hidden=true;
 clearTimeout(modelTimer);modelTimer=setTimeout(()=>modelFailure('模型未在 20 秒内报告首次绘制成功。'),20000);
 // Direct inline document: no temporary blob-page navigation in the preview host.
 modelFrame.srcdoc=new TextDecoder().decode(modelBytes());
}
window.addEventListener('message',e=>{
 if(e.source!==modelFrame.contentWindow||e.data?.type!=='substation_model_state')return;
 if(e.data.state==='ready'){
  clearTimeout(modelTimer);modelStarted=true;modelReady=true;modelCover.hidden=true;
  modelBox.classList.remove('is-loading');window.modelPreviewState='ready';window.modelPreviewError=null;sendFacility();
 }else if(e.data.state==='error')modelFailure(String(e.data.message||'三维未能启动。'));
});
modelButton.onclick=()=>loadModel();
for(const b of document.querySelectorAll('[data-facility]'))b.onclick=()=>{
 loadModel(b.dataset.facility);document.getElementById('model').scrollIntoView({behavior:'smooth'});
};
function downloadBytes(bytes,name){
 const url=URL.createObjectURL(new Blob([bytes],{type:name.endsWith('.html')?'text/html;charset=utf-8':'application/octet-stream'})),a=document.createElement('a');
 a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
document.getElementById('downloadModel').onclick=()=>downloadBytes(modelBytes(),'Substation01_Model.html');
for(const b of document.querySelectorAll('[data-download]'))b.onclick=()=>{
 const name=b.dataset.download;downloadBytes(Uint8Array.from(atob(DOWNLOADS[name]),c=>c.charCodeAt(0)),name);
};
window.reportReady=true;window.modelPreviewState='idle';
