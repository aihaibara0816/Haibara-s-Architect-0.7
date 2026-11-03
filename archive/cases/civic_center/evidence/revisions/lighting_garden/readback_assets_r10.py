from build_case import *
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import Scene,export_structure
from detail_lab import states
FINAL='v03_r10_public';d=C/'runs'/FINAL;out=C/'review/readback';out.mkdir(parents=True,exist_ok=True)
b=load_build(d/'building.nbt',Limits(cells=40000000,nodes=16000000));sha=hashlib.sha256((d/'building.nbt').read_bytes()).hexdigest();records=[]
font=ImageFont.truetype(str(C/'review/font_assets/NotoSC-Case.otf'),24)
small=ImageFont.truetype(str(C/'review/font_assets/NotoSC-Case.otf'),16)
def save(im,name,kind,extra):
 info=PngImagePlugin.PngInfo();info.add_text('source_nbt_sha256',sha);p=out/name;im.save(p,pnginfo=info);records.append({'file':name,'kind':kind,'source_nbt_sha256':sha,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**extra})
for fi,f in enumerate(S['floors']):
 fy=yr(f['elevation']);im=Image.new('RGB',(1008,900),'#f4f5ef');dr=ImageDraw.Draw(im);dr.text((35,18),f"{fi+1}F · {f['title']} · NBT 回读平面",font=font,fill='#233c44');sc=6;ox=72;oz=100
 for z in range(b.size[2]):
  for x in range(b.size[0]):
   q=next(((x,y,z) for y in range(fy+3,fy-2,-1) if (x,y,z) in b.blocks),None)
   if q:
    col=states.color(b.blocks[q]);dr.rectangle((ox+x*sc,oz+z*sc,ox+(x+1)*sc,oz+(z+1)*sc),fill=col)
 dr.text((72,805),'木色：休息／共享  米色：公共／活动  深灰：成组工区  白色柱：分区骨架',font=small,fill='#284451')
 # Path overlay taken from unchanged handoff; do not claim automatic navigation.
 for route in f['routes']:
  pts=[(ox+(12+Q(x))*sc,oz+(12+Q(48-z))*sc) for x,z in route['points']];col={'public':'#d77e2f','staff':'#386c9d','park':'#4b986e'}[route['type']]
  dr.line(pts,fill=col,width=3)
 dr.text((72,836),'橙：公共路线  蓝：办公路线  绿：公园路线（设计路径叠加，非游戏寻路结果）',font=small,fill='#284451')
 dr.text((72,864),f"切至本层完成面以上 2m · 完成面 Y={fy} 格 · 上北(-Z) / 右东(+X)",font=small,fill='#284451')
 save(im,f'plan-{fi+1}.png','NBT_slice_plan',{'floor':fi+1,'slice_range':[fy-1,fy+3]})
for id,zm in [('AA',32),('BB',40)]:
 plane=12+Q(48-zm);sc=8;ox=60;oy=720;im=Image.new('RGB',(1280,820),'#f4f5ef');dr=ImageDraw.Draw(im)
 dr.text((45,18),f'{id} 剖面 · 设计 z={zm}m · NBT Z={plane}格截面',font=font,fill='#233c44')
 for (x,y,z),v in b.blocks.items():
  if z!=plane:continue
  for X,Y,Z,XX,YY,ZZ in states.boxes(v):
   if Z<=.5<=ZZ:dr.rectangle((ox+(x+X)*sc,oy-(y+YY)*sc,ox+(x+XX)*sc,oy-(y+Y)*sc),fill=states.color(v))
 for fy in [4,14,23,32,40,48,56,64]:
  yy=oy-fy*sc;dr.line((55,yy,1210,yy),fill='#c3ccca',width=1);dr.text((8,yy-10),f'{(fy-4)/2:g}',font=small,fill='#49646b')
 dr.text((60,765),'左侧标高为量化后的设计米；直接截取方块状态盒，不补造剖面实体。',font=small,fill='#284451')
 save(im,f'section-{id}.png','NBT_state_box_cross_section',{'Z_plane':plane+.5,'design_z_m':zm})
# Independently verified, cropped samples extracted only from FINAL NBT.
sm=C/'samples/final';sm.mkdir(parents=True,exist_ok=True);samples=[]
for name,lo,size in [('Facade',(53,10,44),(14,56,44)),('Windows',(11,22,9),(55,39,10)),('Bridge',(94,2,19),(27,23,24)),('Stairs',(15,2,71),(19,24,19)),('Public',(59,22,32),(43,10,42)),('Work',(13,31,82),(29,9,26))]:
 ss=Scene(size)
 for q,v in b.blocks.items():
  qq=tuple(q[k]-lo[k] for k in range(3))
  if all(0<=qq[k]<size[k] for k in range(3)):ss.set(qq,v,'final_crop')
 p=sm/(name+'.nbt')
 if p.exists():raise ValueError('sample immutable')
 meta=export_structure(ss,p,include_air=False);rb=load_build(p,Limits(cells=1000000,nodes=2000000));assert rb.blocks==ss.blocks
 samples.append({'file':name+'.nbt','origin_in_whole':lo,'size':size,'blocks':len(ss.blocks),'source_nbt_sha256':sha,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'readback_exact':True})
dump(out/'manifest.json',records);dump(sm/'manifest.json',samples)
print('7 floor slices, 2 sections, 6 final samples')
