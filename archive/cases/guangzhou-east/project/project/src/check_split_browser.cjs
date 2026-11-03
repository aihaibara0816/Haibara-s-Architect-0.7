const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'deliverables/B03S1'),run=path.join(root,'runs/B03S1');
const html=fs.readFileSync(path.join(dir,'GuangzhouEast_Print_Guide.html'));
const manifest=JSON.parse(fs.readFileSync(path.join(run,'manifest.json')));
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; sandbox allow-scripts allow-downloads");res.end(html);});
async function main(){await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:process.argv[2],headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try {const page=await browser.newPage({viewport:{width:1440,height:1080}}),errors=[],downloads=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/');await page.waitForFunction(()=>window.guideReady);await page.evaluate(()=>document.fonts.ready);
 assert.equal(await page.locator('.partbtn').count(),7);
 async function checkDownload(selector,file){console.log('checking download '+file);await page.waitForTimeout(400);const wait=page.waitForEvent('download',{timeout:10000});await page.locator(selector).first().click();const dl=await wait;assert.equal(dl.suggestedFilename(),path.basename(file));const tmp=path.join(run,'qa_download.tmp');await dl.saveAs(tmp);assert(fs.readFileSync(tmp).equals(fs.readFileSync(path.join(dir,file))),'different download: '+file);fs.unlinkSync(tmp);downloads.push(file);}
 for(const [mode,items] of [['parts',manifest.recommended_parts],['groups',manifest.whole_groups_alternative]]){await page.locator('[data-mode="'+mode+'"]').click();assert.equal(await page.locator('.partbtn').count(),items.length);
 for(const item of items){await page.locator('[data-id="'+item.id+'"]').click();assert(await page.locator('#selectionBox').isVisible());const box=await page.locator('#selectionBox').evaluate(e=>['x','y','width','height'].map(k=>Number(e.getAttribute(k))));assert.deepEqual(box,[item.origin_station_xyz[0],item.origin_station_xyz[2],item.size_xyz[0],item.size_xyz[2]]);await checkDownload('#detail [data-download="'+item.id+'"]',item.file);}
 }
 await page.locator('[data-mode="parts"]').click();
 for(const [id,v]of [['wx','1000'],['wy','64'],['wz','2000']])await page.locator('#'+id).fill(v);
 const checkedCoords={};
 for(const [ref,origin]of Object.entries(manifest.reference_origins_station_xyz)){await page.locator('#reference').selectOption(ref);const expected=manifest.recommended_parts[0].origin_station_xyz.map((v,i)=>v+[1000,64,2000][i]-origin[i]);const text=await page.locator('[data-row="E01"] .coords').textContent();assert.equal(text,'('+expected.join(', ')+')');checkedCoords[ref]=expected;}
 await page.locator('[data-mode="land"]').click();assert.equal(await page.locator('.partbtn').count(),0);assert.equal(await page.locator('#zoneCards .card').count(),6);assert(await page.locator('.landuse-layer').first().isVisible());assert(!await page.locator('#partlabels').isVisible());
 for(const [id,file]of [['csv','放置坐标.csv'],['partsPNG','GuangzhouEast_Print_Parts.png'],['landPNG','GuangzhouEast_Triangle_Proposal.png']])await checkDownload('#'+id,file);
 await page.locator('[data-mode="parts"]').click();await page.locator('[data-id="M02"]').click();await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(run,'qa_guide_desktop.png')});
 await page.setViewportSize({width:390,height:844});for(const mode of ['parts','groups','land']){await page.locator('[data-mode="'+mode+'"]').click();assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),'horizontal overflow '+mode);}
 await page.screenshot({path:path.join(run,'qa_guide_mobile.png')});
 assert.deepEqual(errors,[]);
 const report={browser:await browser.version(),guide_sha256:crypto.createHash('sha256').update(html).digest('hex'),strict_csp:true,all_downloads_byte_exact:downloads,selection_bounds:true,coordinate_calculator:checkedCoords,land_plan:true,mobile_no_overflow:true,page_errors:errors};
 fs.writeFileSync(path.join(run,'browser_qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();server.close();}
}
main().catch(e=>{console.error(e);server.close();process.exitCode=1;});
