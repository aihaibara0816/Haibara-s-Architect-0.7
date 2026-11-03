#!/usr/bin/env python3
import sys,json,argparse,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vendor import render_egl
from vendor.inspect_build import load_build,Build
from detail_lab.mesh import write_mesh

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',default='r01');p.add_argument('--sample');a=p.parse_args()
    out=ROOT/'runs'/a.run;render_egl.ROOT=out
    for c in json.loads((out/'configs_used.json').read_text()):
        if a.sample and c['id']!=a.sample:continue
        views=json.loads((out/'cameras'/(c['id']+'.json')).read_text())
        for v in ['A','B']:
            label=c['id']+'_'+v;root=out/'previews'/label
            nbt=out/'nbt'/(label+'.nbt');decoded=load_build(nbt)
            write_mesh(decoded,nbt,root/'scene')
            ordinary=[q for q in views if 'cutX' not in q and 'cutY' not in q]
            mainviews=root/'ordinary_views.json';mainviews.write_text(json.dumps(ordinary))
            render_egl.main(label,mainviews)
            records=json.loads((root/'render_report.json').read_text())
            for view in views:
                if 'cutX' not in view and 'cutY' not in view:continue
                # Crop decoded cells before meshing so newly exposed surfaces exist.
                # Grid-aligned clipping retains exact per-state shapes at the cut.
                crop={k:view[k] for k in ['cutX','cutY'] if k in view}
                cells={p:s for p,s in decoded.blocks.items() if p[0]<crop.get('cutX',decoded.size[0]) and p[1]<crop.get('cutY',decoded.size[1])}
                cutbuild=Build(decoded.size,cells,decoded.info,decoded.palette)
                tmplabel=label+'__'+view['id'];tmp=out/'previews'/tmplabel
                meta=write_mesh(cutbuild,nbt,tmp/'scene');meta['grid_crop']=crop
                (tmp/'scene/scene.json').write_text(json.dumps(meta))
                cam={k:val for k,val in view.items() if k not in crop};cams=tmp/'view.json';cams.write_text(json.dumps([cam]))
                render_egl.main(tmplabel,cams)
                shutil.copyfile(tmp/(view['id']+'.png'),root/(view['id']+'.png'))
                rec=json.loads((tmp/'render_report.json').read_text())[0];rec['grid_crop']=crop;records.append(rec)
            (root/'render_report.complete.json').write_text(json.dumps(records,indent=2))
            (root/'render_report.complete.json').replace(root/'render_report.json')
