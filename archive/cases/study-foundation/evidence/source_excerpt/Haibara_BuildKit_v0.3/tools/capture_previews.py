"""Optional: headless Chromium captures the actual offline CPU Canvas/NBT viewer.
Requires playwright Python package and Chromium. Not required to build or view HTML.
"""
from pathlib import Path
import argparse,json,shutil,time

def capture(run,browser=None):
    from playwright.sync_api import sync_playwright
    out=run/'previews';out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        exe=browser or shutil.which('chromium') or shutil.which('google-chrome')
        if not exe:raise RuntimeError('Chromium not found; pass --browser PATH or open review.html manually')
        b=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1536,'height':1024},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content((run/'review.html').read_text(encoding='utf8'),wait_until='load',timeout=30000)
        page.wait_for_function('window.__READY===true',timeout=30000)
        records=[]
        for v in ('iso','corridor','front','side','top','under'):
            page.evaluate('(v)=>window.setView(v)',v);page.wait_for_timeout(150)
            page.locator('article').screenshot(path=str(out/f'{v}.png'))
            records.append({'view':v,'file':f'previews/{v}.png','camera':page.evaluate('window.getCamera()'),'renderer_stats':page.evaluate('window.getRendererStats()'),'source':page.evaluate('window.buildMetadata')})
        page.evaluate("window.setView('iso')");page.screenshot(path=str(out/'viewer_full.png'))
        # Verify Y control is active; preserve a diagnostic frame.
        page.evaluate("document.getElementById('layer').value=9;document.getElementById('layer').oninput()")
        page.locator('article').screenshot(path=str(out/'layer09.png'))
        errors.extend(page.evaluate('window.__ERRORS'))
        # CPU Canvas draw succeeded without driver errors.
        err=0
        if err:errors.append(f'CPU Canvas error {err}')
        b.close()
    report={'renderer':'offline CPU Canvas + headless Chromium','game_screenshot':False,'texture_mode':'procedural_schematic_palette','views':records,'browser_errors':errors,'result':'pass' if not errors else 'fail'}
    (out/'render_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    if errors:raise RuntimeError(str(errors))
    print('Rendered',len(records),'views:',out)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path);ap.add_argument('--browser');a=ap.parse_args();capture(a.run,a.browser)
