"""Actual multi-format model intake; every output is new and explicit."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.model_io import read_model,save_asset,load_asset,export_mesh,attach_candidate,json_write
from architect.model_preview import preview
from architect.spec_loader import read_json

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='action',required=True)
    p=sub.add_parser('import');p.add_argument('input');p.add_argument('--out',required=True);p.add_argument('--model-id',default='model-import');p.add_argument('--metres-per-unit',type=float);p.add_argument('--up',choices=['X','Y','Z']);p.add_argument('--preview',action='store_true')
    p=sub.add_parser('export');p.add_argument('asset');p.add_argument('output');p.add_argument('--root',action='append')
    p=sub.add_parser('preview');p.add_argument('asset');p.add_argument('output');p.add_argument('--root',action='append')
    p=sub.add_parser('attach');p.add_argument('asset');p.add_argument('spec');p.add_argument('output')
    a=ap.parse_args()
    if a.action=='import':
        if Path(a.out).exists():ap.error('Output directory already exists')
        model=read_model(a.input,model_id=a.model_id,metres_per_unit=a.metres_per_unit,up=a.up);save_asset(model,a.out)
        if a.preview:preview(model,Path(a.out)/'preview.png')
        print(json.dumps(model.document['statistics'],ensure_ascii=False))
    else:
        model=load_asset(a.asset)
        if Path(a.output).exists():ap.error('Output already exists')
        if a.action=='export':json_write(a.output+'.meta.json',export_mesh(model,a.output,a.root))
        elif a.action=='preview':preview(model,a.output,a.root)
        else:json_write(a.output,attach_candidate(read_json(a.spec),model))
if __name__=='__main__':main()
