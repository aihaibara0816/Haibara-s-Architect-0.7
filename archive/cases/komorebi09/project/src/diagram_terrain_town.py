"""Precise terrain/placement diagrams from the adopted heightfields and final scene metadata."""
from pathlib import Path
import sys,json,numpy as np,html
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs'/sys.argv[1];D=ROOT/'review/previews'/R.name;D.mkdir(parents=True,exist_ok=True)
s=json.loads((R/'spec.json').read_text());H=np.load(R/'terrain_final.npy');B=np.load(R/'terrain_original.npy');W,Y,Z=s['size_xyz']
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Z}"><title>实际地形与建筑导航</title>']
for x in range(W):
 for z in range(Z):
  h=int(H[x,z]);c=(max(55,151-h*2),max(75,185-h*2),max(52,113-h));parts.append(f'<rect x="{x}" y="{z}" width="1" height="1" fill="rgb{c}"/>')
for x,z,h in s['water_levels']:parts.append(f'<rect x="{x}" y="{z}" width="1" height="1" fill="#80bdc7"/>')
for x,z,h in s['route_heights']:parts.append(f'<rect x="{x}" y="{z}" width="1" height="1" fill="#c6bca7"/>')
for t in s['trees']:
 if t['kind']=='cherry':parts.append(f'<circle cx="{t["x"]}" cy="{t["z"]}" r="3" fill="#e8b6c5" opacity=".75"/>')
for p in s['public_nodes']:
 x,y,z=p['pos'];parts.append(f'<rect x="{x-3}" y="{z-3}" width="6" height="6" fill="#efe1ad" stroke="#6d633f" stroke-width=".5"/><text x="{x}" y="{z+1}" font-size="2.3" text-anchor="middle">{p["id"]}</text>')
for b in s['buildings']:
 x,y,z,X,Y1,Z1=b['bounds'];parts.append(f'<g class="lot" data-building="{b["id"]}" tabindex="0" role="button" aria-label="{b["id"]} {html.escape(b["name"])}"><rect x="{x}" y="{z}" width="{X-x}" height="{Z1-z}" fill="#e4c9a0" stroke="#5c4a31" stroke-width=".6"/><text x="{(X+x)/2}" y="{(Z1+z)/2}" font-size="3.5" text-anchor="middle" fill="#372d1e">{b["id"]}</text></g>')
parts.append('<text x="7" y="10" font-size="4" fill="#fff">北 ↑ · 西北山体</text></svg>');(D/'terrain_map.svg').write_text(''.join(parts))
# West-to-east section through the mountain peak; one shared horizontal/vertical scale.
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 470"><rect width="1160" height="470" fill="#f5f1e8"/><style>text{font-family:system-ui,sans-serif;fill:#314733}</style><text x="40" y="45" font-size="25">西北山体与北侧台地 · z=30 剖面</text><text x="40" y="75" font-size="15">原始地形虚线 / 建设后地面实线；同一比例。建筑轮廓只画实际被剖到的部分。</text>']
y0=350;scale=4.65
for yy in range(0,51,10):parts.append(f'<path d="M40 {y0-yy*scale} H1100" stroke="#d6d9ca"/><text x="12" y="{y0-yy*scale+5}" font-size="13">{yy}</text>')
pts=lambda A:' '.join(f'{40+x*scale:.1f},{y0-int(A[x,30])*scale:.1f}'for x in range(W))
parts.append(f'<polygon points="40,{y0} '+pts(H)+f' {40+(W-1)*scale},{y0}" fill="#b4c69c"/><polyline points="'+pts(H)+'" fill="none" stroke="#466240" stroke-width="2"/><polyline points="'+pts(B)+'" fill="none" stroke="#a77552" stroke-width="2" stroke-dasharray="7 4"/>')
for b in s['buildings']:
 x,y,z,X,Y1,Z1=b['bounds']
 if z<=30<Z1:
  h=b['floor_y'];bh=b['floors']*5;parts.append(f'<rect x="{40+x*scale}" y="{y0-(h+bh)*scale}" width="{(X-x)*scale}" height="{bh*scale}" fill="#d5b58a" stroke="#66513b"/><text x="{40+(x+X)/2*scale}" y="{y0-(h+bh+2)*scale}" text-anchor="middle" font-size="15">{b["id"]}</text>')
parts.append('<text x="40" y="405" font-size="16">峰顶 y=36 / 街区基准 y=6 → 相对高差 30 格。房屋首层 y=6…21。</text><text x="40" y="434" font-size="14">坐标为结构内部坐标，进入世界时整体加世界偏移；不是实测地理高程。</text></svg>');(D/'terrain_section.svg').write_text(''.join(parts))
# Layered floor-footprint diagram, explicitly a spatial diagram rather than exact room-floor occupancy.
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1030"><rect width="1200" height="1030" fill="#f5f1e8"/><style>text{font-family:system-ui,sans-serif;fill:#334b38}</style><text x="35" y="45" font-size="26">台地与楼层分层示意</text><text x="35" y="76" font-size="15">地块范围沿原坐标投影；二层上移展示。示意省略家具、楼梯洞与实际木楼板边界。</text>']
for layer in[0,1]:
 def pr(x,y,z):return[600+(x-W/2-z+Z/2)*2.2,700-layer*350+(x-W/2+z-Z/2)*1.0-y*2.2]
 for b in s['buildings']:
  if layer and b['floors']==1:continue
  x,y,z,X,Y1,Z1=b['bounds'];fy=b['floor_y']+layer*5;pts=[pr(xx,fy,zz)for xx,zz in[(x,z),(X,z),(X,Z1),(x,Z1)]];parts.append('<polygon points="'+' '.join(f'{a},{c}'for a,c in pts)+'" fill="'+('#c5a47b'if layer==0 else'#e2d0b2')+'" stroke="#6c6c54"/>');tx,ty=pr((x+X)/2,fy,(z+Z1)/2);parts.append(f'<text x="{tx}" y="{ty}" font-size="12" text-anchor="middle">{b["id"]}</text>')
 parts.append(f'<text x="35" y="{650-layer*350}" font-size="21">'+('首层 · 18 栋'if not layer else'二层 · 10 栋')+'</text>')
parts.append('</svg>');(D/'terrace_exploded.svg').write_text(''.join(parts))
diff=[{'x':x,'z':z,'before':int(B[x,z]),'after':int(H[x,z])}for x in range(W)for z in range(Z)if B[x,z]!=H[x,z]]
contract={'case_id':'Komorebi09','run':R.name,'route':'authored terrain first, bounded neighborhood adapter','source_terrain':{'file':'Terrain_Input.nbt','sha256':s['terrain_input_sha256'],'kind':'generated terrain, not imported user NBT'},'final_nbt_sha256':s['source_nbt_sha256'],'coordinates':s['coordinates'],'size_xyz':s['size_xyz'],'components':s['buildings'],'public_nodes':s['public_nodes'],'connections':s['roads'],'adopted_route_heights':s['route_heights'],'water_protected':s['water_levels'],'planting':{'trees':s['trees'],'bamboo':s['bamboo'],'groundcover':s['groundcover']},'earthworks':s['earthworks'],'earthwork_columns':diff,'randomness':s['randomness'],'status':{'case_generator':'implemented','terrain_input_export':'implemented','arbitrary_user_NBT_site_detection':'pending','arbitrary_site_placement_solver':'pending','game':'pending'}}
(R/'spatial_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2));print('terrain diagrams and contract written')
