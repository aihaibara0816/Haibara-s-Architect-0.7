"""Verify retained originals without fetching pages or changing source records."""
import argparse,json,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('original_directory');a=ap.parse_args()
r=Path(a.original_directory);pool=json.loads((Path(__file__).parent/'evidence_pool.json').read_text())
results=[{'id':x['id'],'match':hashlib.sha256((r/x['file']).read_bytes()).hexdigest()==x['sha256']} for x in pool]
print(json.dumps(results));raise SystemExit(not all(x['match'] for x in results))
