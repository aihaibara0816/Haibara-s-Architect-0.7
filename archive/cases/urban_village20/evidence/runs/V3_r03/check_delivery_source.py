"""Verify delivered bytes and inventory actual PNG metadata, without rerendering."""
from pathlib import Path
from html.parser import HTMLParser
import base64
import hashlib
import json
from PIL import Image

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[1]
RUN = CASE / 'runs/V3_r03'
PREVIEW = CASE / 'review/previews/V3_r03'
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text())
nbt = (RUN / 'building.nbt').read_bytes()
source_hash = sha(nbt)
assert (ROOT / 'deliverables/Village.nbt').read_bytes() == nbt

# Earlier batch-render reports may cover only the last batch. Read each actual
# PNG's embedded metadata instead; do not infer a renderer identity.
authored = {c['id']: c for c in read(CASE / 'cameras.json')}
inventory = []
for p in sorted(PREVIEW.glob('*.png')):
    with Image.open(p) as im:
        im.load()
        camera = json.loads(im.info['camera'])
        assert im.info['source_nbt_sha256'] == source_hash, p
        assert camera['id'] == p.stem, p
        assert im.size == (camera['width'], camera['height']), p
        if p.stem in authored:
            for k, v in authored[p.stem].items():
                assert camera[k] == v, (p, k)
        inventory.append({'image': p.name, 'sha256': sha(p.read_bytes()),
                          'source_nbt_sha256': source_hash, 'camera': camera,
                          'emission_policy': im.info['emission_policy']})
assert len(inventory) == 27
assert set(authored).issubset({p['camera']['id'] for p in inventory})
(PREVIEW / 'preview_inventory.json').write_text(json.dumps({
    'provenance': 'Read from actual PNG embedded metadata and file bytes; render_report.json is a partial batch log.',
    'source_nbt_sha256': source_hash, 'images': inventory}, ensure_ascii=False, indent=2))

plans = read(PREVIEW / 'plans/index.json')
assert len(plans) == sum(t['floors'] for t in read(RUN / 'params_used.json')['buildings'])
for entry in plans:
    with Image.open(PREVIEW / 'plans' / entry['file']) as im:
        im.verify()

class DeliveryHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.external = []; self.nbt = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
        for key in ('src', 'href'):
            if tag in ('img', 'script', 'link') and a.get(key, '').startswith(('http:', 'https:', '//')):
                self.external.append(a[key])
        if tag == 'a' and str(a.get('download', '')).endswith('.nbt'):
            self.nbt.append(base64.b64decode(a['href'].split(',', 1)[1]))

html_checks = []
for name in ('Village.html', 'Village_Process.html'):
    p = ROOT / 'deliverables' / name
    parser = DeliveryHTML(); parser.feed(p.read_text())
    assert len(parser.ids) == len(set(parser.ids)), name
    assert not parser.external, name
    if name == 'Village.html':
        assert len(parser.nbt) == 1 and parser.nbt[0] == nbt
    html_checks.append({'file': name, 'sha256': sha(p.read_bytes()),
                        'unique_ids': True, 'external_asset_dependencies': 0,
                        'nbt_downloads': len(parser.nbt)})

validation = read(RUN / 'validation.json')
assert validation['passed'] and len(validation['checks']) == 26
assert all(x['status'] == 'pass' for x in validation['checks'])
assert read(RUN / 'determinism.json')['same_seed_same_output']
assert read(CASE / 'review/browser_qa.json')['passed']
derivation = read(CASE / 'review/previews/V3_r03_exploded/derivation.json')
assert derivation['source_nbt_sha256'] == source_hash and derivation['reversible_exact']
result = {'passed': True, 'source_nbt_sha256': source_hash,
          'preview_inventory_count': len(inventory), 'floor_plans': len(plans),
          'authored_cameras_match_png_metadata': True, 'html': html_checks,
          'offline_checks_passed': len(validation['checks']), 'deterministic_rebuild': True,
          'browser_qa_passed': True, 'exploded_derivation_exact': True,
          'game_test': 'pending', 'user_aesthetic_acceptance': 'pending'}
(CASE / 'review/delivery_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
