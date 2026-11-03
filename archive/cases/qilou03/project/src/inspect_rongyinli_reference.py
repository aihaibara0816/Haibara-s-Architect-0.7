from pathlib import Path
import sys,zipfile,io,zlib,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps')]
import nbtlib as n
from PIL import Image,ImageDraw
p=next((ROOT.parent/'input').rglob('Rongyinli_V4_Java_1.21.1_World.zip'))
im=Image.new('RGB',(288,216),'#eee9df');pix=im.load();blocks=0
with zipfile.ZipFile(p)as zipf:
 for fn in zipf.namelist():
  if '/region/'not in fn or not fn.endswith('.mca'):continue
  raw=zipf.read(fn)
  for i in range(1024):
   off=int.from_bytes(raw[i*4:i*4+3],'big')*4096
   if not off:continue
   size=int.from_bytes(raw[off:off+4],'big');f=n.File.parse(io.BytesIO(zlib.decompress(raw[off+5:off+4+size])))
   for sec in f['sections']:
    if int(sec['Y'])!=5:continue
    bs=sec['block_states'];pal=[str(q['Name'])for q in bs['palette']];bits=max(4,(len(pal)-1).bit_length());per=64//bits;rawdata=bs.get('data')
    for z in range(16):
     for x in range(16):
      idx=256+z*16+x;val=pal[0]if len(pal)==1 else pal[(int(rawdata[idx//per])%(1<<64)>>(idx%per*bits))&((1<<bits)-1)]
      X=int(f['xPos'])*16+x+144;Z=int(f['zPos'])*16+z+108
      if not(0<=X<288 and 0<=Z<216)or val=='minecraft:air':continue
      color='#73a2a4'if 'glass'in val else'#6a825a'if'leaves'in val else'#956d54';pix[X,Z]=tuple(bytes.fromhex(color[1:]));blocks+=1
im=im.resize((1152,864),Image.Resampling.NEAREST);im.save(ROOT/'research/rongyinli_y81_plan.png')
(ROOT/'research/rongyinli_reference.json').write_text(json.dumps({'source':'Rongyinli_V4_Java_1.21.1_World.zip','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'method':'Actual Anvil section at world Y81; diagram, not gameplay screenshot','inspected_non_air':blocks,'application':'Wide voxel diagonal corner and contrast between arcade street and taller residential back lanes; Qilou03 uses new authored geometry'},ensure_ascii=False,indent=2))
