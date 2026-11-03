"""Review or guard a revision; all outputs are new files, never overwrite."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.spec_loader import load_spec,read_json
from architect.reference_review import validate_review
from architect.revision import guard_revision

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='action',required=True)
    p=sub.add_parser('review');p.add_argument('spec');p.add_argument('review');p.add_argument('run');p.add_argument('output')
    p=sub.add_parser('revision');p.add_argument('before');p.add_argument('after');p.add_argument('request');p.add_argument('output')
    a=ap.parse_args()
    if a.action=='review':result=validate_review(read_json(a.review),load_spec(a.spec),a.run)
    else:result=guard_revision(load_spec(a.before),load_spec(a.after),read_json(a.request))
    with Path(a.output).open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
