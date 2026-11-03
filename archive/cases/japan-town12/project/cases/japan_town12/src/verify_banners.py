"""Read the saved structure and region files independently to compare banner BEs."""
from pathlib import Path
import sys,io,zlib,json
import nbtlib as n
C=Path(__file__).resolve().parents[1];R=C/'runs'/sys.argv[1];world=Path(sys.argv[2]);src=n.load(R/'building.nbt');wc=json.loads((R/'world_check.json').read_text());off=wc['world_offset'];expected={}
for b in src['blocks']:
 st=src['palette'][int(b['state'])]
 if '_wall_banner' in str(st['Name']):
  assert str(b['nbt']['id'])=='minecraft:banner'
  assert len(b['nbt']['patterns'])==0
  expected[tuple(int(v)+o for v,o in zip(b['pos'],off))]=str(st['Name'])
found={}
for p in (world/'region').glob('*.mca'):
 raw=p.read_bytes()
 for i in range(1024):
  pos=int.from_bytes(raw[i*4:i*4+3],'big')*4096
  if not pos:continue
  length=int.from_bytes(raw[pos:pos+4],'big');chunk=n.File.parse(io.BytesIO(zlib.decompress(raw[pos+5:pos+4+length])))
  for be in chunk['block_entities']:
   assert str(be['id'])=='minecraft:banner'
   q=tuple(int(be[k]) for k in ['x','y','z']);assert q not in found;assert len(be['patterns'])==0;found[q]=True
assert set(found)==set(expected)
out=dict(source_banner_count=len(expected),world_banner_count=len(found),positions_exact=True,pure_color_patterns=True,game_display='pending')
(R/'banner_check.json').write_text(json.dumps(out,indent=2));print(out)
