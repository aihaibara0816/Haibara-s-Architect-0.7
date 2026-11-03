"""Recheck six existing derivatives against an imported mesh asset."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.model_io import load_asset,read_model,json_write
from architect.model_compare import compare

def main():
    ap=argparse.ArgumentParser();ap.add_argument('asset');ap.add_argument('derivatives');ap.add_argument('output');ap.add_argument('--stem',default='canton');ap.add_argument('--tolerance-m',type=float,default=.001);a=ap.parse_args()
    if Path(a.output).exists():ap.error('Output exists')
    model=load_asset(a.asset);results=[]
    for ext in ('glb','gltf','obj','stl','ply','dae'):
        p=Path(a.derivatives)/(a.stem+'.'+ext)
        other=read_model(p,**({'metres_per_unit':1,'up':'Y'} if ext in ('obj','stl','ply') else {}))
        result={'format':ext,**compare(model,other,a.tolerance_m)};results.append(result);print(ext,result['status'],flush=True)
    json_write(a.output,{'source_sha256':model.document['source']['sha256'],'basis':'Mesh derivatives re-read; not independent authoring-application exports','results':results})
    return 0 if all(r['status']=='pass' for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
