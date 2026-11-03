"""Fetch explicitly identified public reference images; never infer image URLs."""
from pathlib import Path
import concurrent.futures, hashlib, io, json, urllib.request
from PIL import Image

CASE = Path(__file__).resolve().parents[1]
OUT = CASE / 'research/v2'

def fetch(item):
    record = dict(item)
    p = OUT / 'images' / (item['image_id'] + '.jpg')
    try:
        if p.exists():
            data = p.read_bytes()
        else:
            req = urllib.request.Request(item['direct_image_url'], headers={'User-Agent':'HAF-Architect-Research/0.2 (public architectural reference study)'})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = response.read(30_000_001)
            if len(data) > 30_000_000:
                raise ValueError('Image exceeds bounded reference download')
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            record['actual_pixels'] = list(image.size)
            record['format'] = image.format
        p.write_bytes(data)
        record.update(local_path=str(p.relative_to(CASE)), sha256=hashlib.sha256(data).hexdigest(), download_status='ok', viewed_v2=False)
    except Exception as exc:
        record.update(download_status='failed', error=str(exc), viewed_v2=False)
    print(record['image_id'], record['download_status'], record.get('actual_pixels',record.get('error')), flush=True)
    return record

def main():
    (OUT/'images').mkdir(parents=True, exist_ok=True)
    packet = json.loads((CASE/'research/original_packet.json').read_text())
    items=packet['images']
    extra=OUT/'additional_candidates.json'
    if extra.exists(): items += json.loads(extra.read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(fetch,items))
    (OUT/'downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__': main()
