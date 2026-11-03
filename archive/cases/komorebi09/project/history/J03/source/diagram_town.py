from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import town_states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];sp=json.loads((R/'spec.json').read_text());b=load_build(R/'Komorebi09.nbt',Limits(cells=1000000,nodes=8000000));D=ROOT/'review/previews'/R.name;D.mkdir(parents=True,exist_ok=True)
# Technical occupancy diagram: only actual wooden floors, including their stair openings.
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 1000"><rect width="1100" height="1000" fill="#f4f1e8"/><style>text{font-family:system-ui,sans-serif;fill:#344139}</style><text x="36" y="46" font-size="27" font-weight="700">木漏日町 · 楼板叠合</text><text x="36" y="75" font-size="16">同源 NBT 占用；只拉开显示层距。省略墙、屋面和家具。</text>']
for layer,f in enumerate([2,7]):
 base=610-layer*330
 def proj(x,z):return[510+(x-82-z+56)*3.5,base+(x-82+z-56)*1.5]
 cells=[]
 for bd in sp['buildings']:
  if f==7 and bd['floors']!=2:continue
  x0,_,z0,x1,_,z1=bd['bounds']
  for x in range(x0,x1):
   for z in range(z0,z1):
    if b.blocks.get((x,f,z))in ['minecraft:oak_planks','minecraft:spruce_planks']:cells.append((x,z))
  xx,zz=proj((x0+x1)/2,(z0+z1)/2)
  parts.append(f'<text x="{xx}" y="{zz-5}" font-size="13" text-anchor="middle">{bd["id"]}</text>')
 polys=[]
 for x,z in sorted(cells,key=lambda q:sum(q)):
  pts=[proj(xx,zz)for xx,zz in [(x,z),(x+1,z),(x+1,z+1),(x,z+1)]];polys.append('<polygon points="'+' '.join(f'{xx:.1f},{zz:.1f}'for xx,zz in pts)+'" fill="'+('#bd9870'if layer==0 else'#ddc7a4')+'" stroke="#7e7667" stroke-width=".12"/>')
 parts.extend(polys);parts.append(f'<text x="36" y="{base-120}" font-size="22">'+('首层 · 18 栋'if f==2 else'二层 · 10 栋')+'</text>')
parts.append('<text x="36" y="954" font-size="15">单层小店不虚构二层；每栋楼板开口以最终几何为准。北为 -Z。</text></svg>');(D/'exploded.svg').write_text(''.join(parts))
contract={'design_brief':sp['design_brief'],'coordinates':sp['coordinates'],'size_xyz':sp['size_xyz'],'spatial_spec':{'buildings':sp['buildings'],'main_street':[2,38,138,45],'quiet_lane':[2,73,138,80],'creek':sp['water_cells'],'bridges':sp['bridges'],'trees':sp['trees'],'groundcover':sp['groundcover']},'facade_spec':{'shopfront':'open trading bays or framed residential entry; curtains, signs and planted thresholds','upper':'private living windows, ledges and shutters','roofs':'mixed single/two-storey gables; four large shop-houses retain the M08 front cross-gable','variation':'family/lot design choices; no per-cell damaged masonry'},'randomness':sp['randomness'],'seed':sp['seed'],'source_nbt_sha256':sp['source_nbt_sha256']}
(R/'design_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2))
(R/'design_prompts.txt').write_text('长关键词：18栋老式日式小街区，四栋大町屋、六栋紧凑两层住商楼、八栋单层专门店与公共小楼；街屋有厨卫、床组、柜体、软席与用途陈列。主商店街为窄沥青路，侧巷与安静街采用石铺；建筑正面退距、屋脊方向、高度与檐深不同。首层临街开口、退入入口、暖帘、菜单、候位凳、薄格扇；白灰泥与深浅木构、灰黑瓦。东侧微弯小溪、低石岸与草坡边缘，石桥和木桥接上两岸步道；溪边树荫、草花、墙根小簇植物、花盆、局部灌木与坐凳。草地有低草和少量高草，花按组分布，避免均匀撒点。保护门口、床侧、楼梯、连续街道和桥面；仅植物组随固定种子变化。普通室内与完整顶棚人物视角一起验收，不凭缩略图判断内饰。\n短关键词：老式日式18栋街坊，混合住商小楼，层次木构瓦檐，开放店口，完整可进内饰，侧边小溪与两桥，树荫、成簇草花和门前盆栽，安静日漫街景。\n边界：原创有界案例；参考既有Freedom局部观察，未重新观看视频或复制完整教程。离线NBT材质图，不是实机截图；家具部分为装饰；生成器固定18个地块，不代表任意城镇自动规划。\n')
print('diagram/contract/keywords written')
