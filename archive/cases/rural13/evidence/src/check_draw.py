from pathlib import Path
import sys,json,collections,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
R=C/'runs/V4';P=C/'review/previews/V4';b=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000));d=json.loads((R/'params_used.json').read_text());B=b.blocks
font=ImageFont.truetype(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),20)
entries=json.loads((C/'input/entries.json').read_text());fail=[]
for e in entries:
 x,y,z=e['xyz']
 for yy in [y,y+1]:
  if (x,yy,z) in B:fail.append([e['house'],'entry',x,yy,z,B[x,yy,z]])
 if (x,y-1,z) not in B:fail.append([e['house'],'entry_floor'])
crops=[(q,s) for q,s in B.items() if states.family(s)=='crop'];cropbad=[q for q,s in crops if 'farmland' not in B.get((q[0],q[1]-1,q[2]),'')]
report={'source_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'buildings':len(d['buildings']),'types':dict(collections.Counter(t['kind'] for t in d['buildings'])),'non_air':len(B),'entry_failures':fail,'crop_blocks':len(crops),'unsupported_crops':len(cropbad),'preview':'NBT state-box mesh, approximate materials; not game screenshot','game':'server verification pending','player_collision':'pending'}
(R/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
# Same-NBT floor plans, with openings/stair layout visible.
plans=[]
for t in d['buildings']:
 x,z,w,h,n,g=t['x'],t['z'],t['w'],t['d'],t['floors'],t['base'];tid=t['id']
 for f in range(n):
  fy=g+1+6*f;im=Image.new('RGB',((w+8)*16,(h+8)*16+60),'#f4f1e7');dr=ImageDraw.Draw(im)
  dr.text((14,8),f'{tid} · {f+1}F  |  Y={fy+60}',font=font,fill='#283c31')
  for zz in range(z-4,z+h+4):
   for xx in range(x-4,x+w+4):
    ss=next((B[(xx,yy,zz)] for yy in range(fy+2,fy-2,-1) if (xx,yy,zz) in B),None)
    if ss:
     col=states.color(ss);px=(xx-x+4)*16;pz=(zz-z+4)*16+50;dr.rectangle((px,pz,px+15,pz+15),fill=col)
  path=P/f'{tid}_F{f+1:02}.png';im.save(path);plans.append({'house':tid,'floor':f+1,'image':path.name})
# Four accurate elevations of the primary finished house + longitudinal section + exploded floors.
t=d['buildings'][0];x,z,w,h,g=t['x'],t['z'],t['w'],t['d'],t['base'];hi=g+1+t['floors']*6+4
for face in range(4):
 n=w if face%2==0 else h;im=Image.new('RGB',(n*18+60,(hi-g+3)*18+70),'#f4f1e7');dr=ImageDraw.Draw(im)
 dr.text((20,8),['北立面','东立面','南立面','西立面'][face]+' · R01',font=font,fill='#283c31')
 for u in range(n):
  for yy in range(g,hi+1):
   qs=([(x+u,yy,zz) for zz in range(z-2,z+h+2)] if face==0 else [(xx,yy,z+u) for xx in range(x+w+1,x-3,-1)] if face==1 else [(x+w-1-u,yy,zz) for zz in range(z+h+1,z-3,-1)] if face==2 else [(xx,yy,z+h-1-u) for xx in range(x-2,x+w+2)])
   ss=next((B[q] for q in qs if q in B),None)
   if ss:dr.rectangle((30+u*18,50+(hi-yy)*18,47+u*18,67+(hi-yy)*18),fill=states.color(ss))
 im.save(P/f'elevation_{face}.png')
# Section cuts through stair return and floors.
rot=t['rotation'];cutx=x+w-1-4
im=Image.new('RGB',(h*20+60,(hi-g+3)*20+70),'#f4f1e7');dr=ImageDraw.Draw(im);dr.text((20,8),'R01 楼梯剖面 · X='+str(cutx),font=font,fill='#283c31')
for zz in range(z,z+h):
 for yy in range(g,hi+1):
  ss=B.get((cutx,yy,zz))
  if ss:dr.rectangle((30+(zz-z)*20,50+(hi-yy)*20,49+(zz-z)*20,69+(hi-yy)*20),fill=states.color(ss))
im.save(P/'section.png')
# Exploded stack preserves actual X/Z; vertical separation only.
canvas=Image.new('RGB',(800,950),'#f4f1e7');dr=ImageDraw.Draw(canvas);dr.text((30,20),'R01 分层展开 · 同源楼板与家具',font=font,fill='#283c31')
for f in range(t['floors']):
 fy=g+1+f*6;off=720-f*260
 for zz in range(z,z+h):
  for xx in range(x,x+w):
   ss=next((B[(xx,yy,zz)] for yy in range(fy+1,fy-2,-1) if (xx,yy,zz) in B),None)
   if ss:
    u=390+(xx-x-(zz-z))*11;v=off+(xx-x+zz-z)*4
    dr.polygon([(u,v),(u+11,v+4),(u,v+8),(u-11,v+4)],fill=states.color(ss))
 dr.text((40,off+20),f'{f+1}F',font=font,fill='#283c31')
canvas.save(P/'exploded.png');(P/'plans.json').write_text(json.dumps(plans))
assert len(d['buildings'])==13 and not fail and not cropbad
