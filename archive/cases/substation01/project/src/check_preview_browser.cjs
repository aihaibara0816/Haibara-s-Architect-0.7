const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert');
const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),doc=fs.readFileSync(path.join(root,'deliverables/Substation01.html'),'utf8');
const executablePath=process.argv[2];if(!executablePath)throw Error('Pass a Chrome Headless Shell executable path.');
const server=http.createServer((req,res)=>{
 res.setHeader('Content-Type','text/html; charset=utf-8');
 res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; frame-src 'self'; sandbox allow-scripts allow-downloads");
 const content=req.url==='/legacy'?doc.replace('modelFrame.srcdoc=new TextDecoder().decode(modelBytes());',"modelFrame.src=URL.createObjectURL(new Blob([modelBytes()],{type:'text/html;charset=utf-8'}));"):doc;
 res.end(content);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({executablePath,headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
 try{
  const page=await browser.newPage({viewport:{width:1400,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{waitUntil:'load'});await page.waitForFunction(()=>window.reportReady);await page.locator('#loadModel').click();
  await page.waitForFunction(()=>['ready','fallback'].includes(window.modelPreviewState),{},{timeout:30000});
  const first=await page.evaluate(()=>({state:window.modelPreviewState,error:window.modelPreviewError}));assert.equal(first.state,'ready',JSON.stringify(first));
  let frame=await page.locator('#modelFrame').elementHandle().then(h=>h.contentFrame());assert.equal(frame.url(),'about:srcdoc');
  await frame.waitForFunction(()=>window.renderCount>0);assert(await page.locator('#modelcover').isHidden());
  await page.locator('[data-facility="T2"]').click();await frame.waitForFunction(()=>window.lastView.id==='T2');
  await page.locator('[data-facility="control"]').click();await frame.waitForFunction(()=>window.lastView.id==='control');
  await frame.locator('#mode').selectOption('floor');await frame.locator('#floor').fill('2');await frame.locator('#floor').dispatchEvent('input');
  await frame.waitForFunction(()=>window.lastView.mode==='floor'&&window.lastView.floor===2);await frame.locator('#night').check();await frame.waitForFunction(()=>window.lastView.night===1);
  const before=await frame.evaluate(()=>window.lastView.eye);const box=await frame.locator('#c').boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2+60,box.y+box.height/2+20,{steps:4});await page.mouse.up();await frame.waitForFunction(old=>JSON.stringify(window.lastView.eye)!==JSON.stringify(old),before);
  assert.equal(await frame.evaluate(()=>gl.getError()),0);assert(!await frame.evaluate(()=>window.modelError));
  fs.mkdirSync(path.join(root,'review/preview_fix_internal'),{recursive:true});await page.locator('#modelFrame').screenshot({path:path.join(root,'review/preview_fix_internal/loaded.png')});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(400);assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));assert(!await frame.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
  const canLose=await frame.evaluate(()=>!!gl.getExtension('WEBGL_lose_context'));
  if(canLose){
   await frame.evaluate(()=>gl.getExtension('WEBGL_lose_context').loseContext());await page.waitForFunction(()=>window.modelPreviewState==='fallback');assert(await page.locator('#modelcover').isVisible());assert(await page.locator('#downloadModel').isVisible());assert(await page.locator('#modelFallback').evaluate(e=>e.naturalWidth>0));
   await page.locator('#loadModel').click();await page.waitForFunction(()=>window.modelPreviewState==='ready',{},{timeout:30000});
  }
  assert.deepEqual(errors,[]);
  const legacy=await browser.newPage({viewport:{width:1100,height:800}}),csp=[];
  legacy.on('console',m=>{if(/violat|refused|framing/i.test(m.text()))csp.push(m.text())});await legacy.goto(base+'/legacy');await legacy.locator('#loadModel').click();await legacy.waitForTimeout(1500);
  const legacyState=await legacy.evaluate(()=>window.modelPreviewState);const reproduced=csp.some(x=>/frame-src|Framing/i.test(x));
  const result={pass:true,browser:await browser.version(),actual_webgl_render:true,iframe:'about:srcdoc',csp_sandbox:'allow-scripts allow-downloads; frame-src self',checks:['initial rendered frame and ready acknowledgement','T2 and control selection','upper floor and night mode','drag rotation','zero WebGL errors','390px responsive layout',...(canLose?['real WebGL context loss retains static image','retry rebuilds the iframe and renders again']:[])],page_errors:errors,legacy_blob_block_reproduced:reproduced,legacy_state:legacyState,legacy_csp_messages:csp,source_nbt_sha256:JSON.parse(fs.readFileSync(path.join(root,'runs/S04/spec.json'),'utf8')).source_nbt_sha256};
  fs.writeFileSync(path.join(root,'runs/S04/browser_preview_fix.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
