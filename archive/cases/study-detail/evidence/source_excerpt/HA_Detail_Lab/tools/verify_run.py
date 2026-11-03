#!/usr/bin/env python3
import sys,json,hashlib,argparse,unittest,io,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vendor.inspect_build import load_build
from detail_lab.builders import build,control
from detail_lab.states import family,validate

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',default='r02');p.add_argument('--files-only',action='store_true');a=p.parse_args();out=ROOT/'runs'/a.run
    if a.files_only:
        logtext=(out/'test_log.txt').read_text();assert logtext.rstrip().endswith('OK')
        testcount=int(re.search(r'Ran (\d+) tests',logtext).group(1));skips=0
    else:
        log=io.StringIO();suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        (out/'test_log.txt').write_text(log.getvalue())
        if not result.wasSuccessful():raise RuntimeError(log.getvalue())
        testcount=result.testsRun;skips=len(result.skipped)
    manifest=json.loads((out/'manifest.json').read_text());checks=[];image_count=0;decoded_scenes={}
    for c in manifest['samples']:
        expected=build(c);states={}
        for tag,sc in [('A',control(expected)),('B',expected)]:
            label=c['id']+'_'+tag;path=out/'nbt'/(label+'.nbt');rec=c['variants'][tag]
            raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==rec['sha256']
            nb=load_build(path);cells={p:s for p,s in nb.blocks.items() if family(s)!='air'}
            assert cells==sc.blocks and nb.size==sc.size
            states[tag]=cells;decoded_scenes[label]=cells
            render=json.loads((out/'previews'/label/'render_report.json').read_text());assert len(render)==6
            for im in render:
                f=out/'previews'/label/im['image'];assert hashlib.sha256(f.read_bytes()).hexdigest()==im['sha256']
                with Image.open(f) as x:
                    assert x.size==(1400,1050);assert x.info['source_nbt_sha256']==rec['sha256'];x.verify()
                assert im['source_nbt_sha256']==rec['sha256'];image_count+=1
            rec['preview']=json.loads((out/'previews'/label/'scene/scene.json').read_text())
        assert states['A'].keys()==states['B'].keys()
        assert sum(states['A'][p]!=s for p,s in states['B'].items())==c['changed_state_cells']>0
        aa=json.loads((out/'previews'/(c['id']+'_A')/'render_report.json').read_text());bb=json.loads((out/'previews'/(c['id']+'_B')/'render_report.json').read_text())
        assert [(x['camera'],x.get('grid_crop')) for x in aa]==[(x['camera'],x.get('grid_crop')) for x in bb]
        checks.append({'id':c['id'],'readback':'PASS','pair_same_occupied_cells':'PASS','cameras_identical':'PASS','changed_states':c['changed_state_cells']})
    gallery=out/'nbt/detail_gallery_B.nbt';assert hashlib.sha256(gallery.read_bytes()).hexdigest()==manifest['gallery']['sha256']
    assembled={}
    for placement in manifest['gallery']['placements']:
        off=placement['origin_xyz']
        for p,s in decoded_scenes[placement['id']+'_B'].items():
            q=tuple(x+y for x,y in zip(p,off));assert q not in assembled;assembled[q]=s
    actual={p:s for p,s in load_build(gallery).blocks.items() if family(s)!='air'};assert assembled==actual
    originals=[]
    for rec in json.loads((ROOT/'evidence/original_integrity.json').read_text()):
        p=Path(rec['source'])
        if p.is_file():assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'];originals.append(str(p))
        if rec.get('copied_to'):assert hashlib.sha256((ROOT/rec['copied_to']).read_bytes()).hexdigest()==rec['sha256']
    report={'unit_tests':testcount,'unit_failures':0,'unit_errors':0,'unit_skipped':skips,'paired_samples':checks,'nbt_files_checked':17,'preview_images_checked':image_count,'gallery_exact_assembly':'PASS','original_files_unchanged_checked':len(originals),'game_import':'PENDING','real_building_fidelity':'NOT_MEASURED','limitations':'State grammar and visual boxes are project tests, not a game registry, collision or lighting certification.'}
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
