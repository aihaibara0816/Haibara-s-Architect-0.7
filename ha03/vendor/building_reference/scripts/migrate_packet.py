"""Explicit migration preserving source IDs and the original four-slot record."""
import argparse,json
from pathlib import Path
from reference_set import migrate
from validate_packet import validate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');a=ap.parse_args()
    src=Path(a.input);p=json.loads(src.read_text());r=validate(p,'template',src.parent)
    if r['status']=='FAIL':raise ValueError(r['errors'])
    out=Path(a.output)
    # Local paths are relative to the packet; do not silently relocate assets.
    if any(i.get('local_file') for i in p['images']) and out.resolve().parent!=src.resolve().parent:raise ValueError('Keep local-evidence packet beside its assets')
    migrated=migrate(p);r=validate(migrated,'template',src.parent)
    if r['status']=='FAIL':raise ValueError(r['errors'])
    with out.open('x',encoding='utf8') as f:json.dump(migrated,f,ensure_ascii=False,indent=2)
    print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
