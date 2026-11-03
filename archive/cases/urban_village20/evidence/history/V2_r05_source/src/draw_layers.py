"""All floors and an exploded view derived solely from final NBT and ownership."""
from pathlib import Path
import sys,json,gzip,hashlib,argparse,collections
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(C/'src')]
from PIL import Image,ImageDraw,ImageFont
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import export_structure
from hafusion.classical import Builder
from detail_lab import states,mesh
from render_case import grille_boxes
import render_egl_site as egl
def main(run):
 R=C/'runs'/run;P=C/'review/previews'/run;out=P/'plans';out.mkdir(exist_ok=True)
 p=json.loads((R/'params_used.json').read_text());units=json.loads((R/'units.json').read_text());entries={e['id']:e for e in json.loads((R/'entries.json').read_text())};rb=load_build(R/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
 raw=json.loads(gzip.decompress((R/'component_ownership.json.gz').read_bytes()));owners={tuple(q[:3]):raw['owner_names'][q[3]] for q in raw['xyz_owner']};byhouse=collections.defaultdict(dict)
 for q,s in rb.blocks.items():byhouse[owners[q].split('.')[0]][q]=s
 font=lambda n:ImageFont.truetype(str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf'),n)
 index=[]
 for t in p['buildings']:
  x0,z0=t['x']-5,t['z']-5;x1,z1=t['x']+t['w']+5,t['z']+t['d']+5;scale=18;W=(x1-x0)*scale+80;H=(z1-z0)*scale+170
  for f in range(1,t['floors']+1):
   fy=t['base_y']+(f-1)*5;im=Image.new('RGB',(W,H),'#f4f0e7');dr=ImageDraw.Draw(im);dr.text((26,18),f'{t["id"]} · {t["name"]} / {f}F',font=font(22),fill='#293c3c')
   dr.text((26,50),'北 ↑ −Z   东 → +X   ·   最终 NBT 分层回读',font=font(13),fill='#68756b')
   top={}
   for (x,y,z),s in byhouse[t['id']].items():
    if fy-1<=y<=fy+1 and x0<=x<x1 and z0<=z<z1 and y>=top.get((x,z),(-99,''))[0]:top[x,z]=(y,s)
   for (x,z),(y,s) in top.items():
    a,c=40+(x-x0)*scale,90+(z-z0)*scale;col=states.color(s)
    if y==fy-1:col=tuple(min(255,round(v*.75+230*.25)) for v in col)
    dr.rectangle((a,c,a+scale-1,c+scale-1),fill=col)
   floor_units=[u for u in units if u['building']==t['id'] and u['floor']==f]
   start=entries[t['id']]['core_landing'];start=(start[0],start[2]);prev={start:None};todo=collections.deque([start])
   while todo:
    x,z=todo.popleft()
    for v in [(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
     if v in prev or not(x0<=v[0]<x1 and z0<=v[1]<z1):continue
     if (v[0],fy,v[1]) in rb.blocks or (v[0],fy+1,v[1]) in rb.blocks:continue
     support=rb.blocks.get((v[0],fy-1,v[1]));
     if not support or not states.support_cube(support):continue
     prev[v]=(x,z);todo.append(v)
   for u in floor_units:
    q=(u['entry'][0],u['entry'][2]);path=[]
    while q is not None and q in prev:path.append((40+(q[0]-x0+.5)*scale,90+(q[1]-z0+.5)*scale));q=prev[q]
    if len(path)>1:dr.line(path,fill='#287b85',width=3)
    x,z=u['entry'][0],u['entry'][2];a,c=40+(x-x0+.5)*scale,90+(z-z0+.5)*scale;dr.ellipse((a-5,c-5,a+5,c+5),fill='#c96e3e')
   dr.text((26,H-58),'蓝：回读方块净空中的连接路径   橙：入户门洞',font=font(13),fill='#28626a')
   dr.text((26,H-34),'切至完成面上第 2 格；图例覆盖不属于建筑方块。游戏碰撞待测。',font=font(12),fill='#68756b')
   name=t['id']+f'_F{f:02d}.png';im.save(out/name);index.append({'building':t['id'],'floor':f,'file':name,'floor_y':fy})
 (out/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
 # B2/F2 layer extraction. Translation mapping is preserved for reversibility.
 t=next(t for t in p['buildings'] if t['id']=='D5');ox,oz=t['x']-4,t['z']-4;d=C/'review/previews'/(run+'_exploded');d.mkdir(exist_ok=True)
 b=Builder([t['w']+8,23,t['d']+8]);mapping={7:1,8:6,9:7,10:8,11:14,12:20};selected={}
 for (x,y,z),s in byhouse['D5'].items():
  if y in mapping and ox<=x<ox+b.s.size[0] and oz<=z<oz+b.s.size[2]:b.put(x-ox,mapping[y],z-oz,s,'derived.D5.F2');selected[x,y,z]=s
 export_structure(b.s,d/'layers.nbt',include_air=False);rr=load_build(d/'layers.nbt',Limits(cells=4_000_000,nodes=3_000_000));inverse={v:k for k,v in mapping.items()}
 assert {(x+ox,inverse[y],z+oz):s for (x,y,z),s in rr.blocks.items()}==selected
 mesh.boxes=grille_boxes;mesh.write_mesh(rr,d/'layers.nbt',d/'scene')
 cams=[{'id':'exploded','eye':[75,60,83],'target':[b.s.size[0]/2,10,b.s.size[2]/2],'width':1400,'height':1200,'spanX':47,'spanZ':40.3,'ortho':True,'concept':False}]
 cp=d/'cameras.json';cp.write_text(json.dumps(cams));egl.ROOT=C/'review';egl.main(run+'_exploded',cp,emission_policy='material')
 (d/'derivation.json').write_text(json.dumps({'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'building':'D5','floor':2,'vertical_mapping':mapping,'horizontal_offset':[ox,oz],'selected_blocks':len(selected),'reversible_exact':True,'illustration_only':True},indent=2))
 print('floor plans',len(index),'exploded exact',len(selected),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();main(a.run)
