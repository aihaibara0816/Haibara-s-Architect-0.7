from build_case import *
from vendor.inspect_build import load_build,Limits
from detail_lab import states
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
final='v03_r16_ceiling_landscape';old='v03_r13_lighting';paths=[C/'runs'/run/'building.nbt' for run in [old,final]];bs=[load_build(p,Limits(cells=40000000,nodes=16000000)) for p in paths]
row=max(range(84,107),key=lambda z:sum(bs[1].blocks.get((x,12,z)) in ['minecraft:sea_lantern','minecraft:glowstone'] for x in range(15,48)))
fontpath='/workspace/scratch/74fcac1fd17a/civic_work/NotoSansCJKsc-Regular.otf';font=ImageFont.truetype(fontpath,24);sm=ImageFont.truetype(fontpath,18)
im=Image.new('RGB',(1200,650),'#f4f3ef');dr=ImageDraw.Draw(im);dr.text((32,20),'两格层间构造 · 同位置 NBT 实际截面',font=font,fill='#193d41')
for k,b in enumerate(bs):
 ox=92;oy=280+k*265;sc=22;dr.text((32,77+k*265),['R13 · 单层楼板下的凸出灯','R16 · 上层地板＋下层吊顶／灯光'][k],font=font,fill='#193d41')
 for x in range(15,49):
  for y in range(9,17):
   v=b.blocks.get((x,y,row));xx=ox+(x-15)*sc;yy=oy-(y-9)*sc
   if v:
    col=states.color(v)
    if v=='minecraft:sea_lantern':col='#9ddcdb'
    if v=='minecraft:glowstone':col='#eebc6d'
    dr.rectangle((xx,yy-sc,xx+sc,yy),fill=col,outline='#6d7d7c')
 for y,label in [(14,'Y14 上层完成面'),(13,'Y13 上层楼板'),(12,'Y12 吊顶／嵌灯')]:
  yy=oy-(y-9)*sc;dr.text((875,yy-sc+2),label,font=sm,fill='#2d4f59')
 dr.text((95,290+k*265),f'固定截面 Z={row} · 横向 X=15..48 · 青色为海晶灯，橙色为萤石',font=sm,fill='#2d4f59')
dr.text((32,610),'上层完成面不变；普通区增加下层吊顶，净高减少一格。楼梯洞与室外连桥另按原板内嵌。',font=sm,fill='#2d4f59')
sha=hashlib.sha256(paths[1].read_bytes()).hexdigest();info=PngImagePlugin.PngInfo();info.add_text('source_nbt_sha256',sha);out=C/'review/readback/ceiling-section.png';im.save(out,pnginfo=info)
manifest=C/'review/readback/manifest.json';r=json.loads(manifest.read_text());r=[v for v in r if v['file']!=out.name];r.append({'file':out.name,'kind':'two_version_exact_NBT_slice','source_nbt_sha256':sha,'baseline_nbt_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'Z_plane':row});dump(manifest,r);print('ceiling section',row)
