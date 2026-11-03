from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import room_states
from vendor.inspect_build import load_build,Limits
R=ROOT/'runs'/sys.argv[1];b=load_build(R/'Machiya08.nbt',Limits(cells=2_000_000,nodes=6_000_000));sp=json.loads((R/'spec.json').read_text());D=ROOT/'review/previews'/R.name;D.mkdir(parents=True,exist_ok=True)
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 850" role="img" aria-label="日和小食同源楼层爆炸图"><rect width="880" height="850" fill="#f4f0e6"/><style>text{font-family:system-ui,sans-serif;fill:#453b30}.cap{font-size:24px;font-weight:700}.small{font-size:14px}</style><text x="30" y="40" class="cap">日和小食 · 楼层叠合</text><text x="30" y="68" class="small">水平坐标一致，仅拉开显示层距。楼板占用与楼梯洞口来自最终 NBT。</text>']
for idx,f in enumerate([2,7,12]):
 base=710-idx*220
 def proj(x,z):return (470+(x-15.5-z+15)*17,base+(x-15.5+z-15)*7)
 for x,z in sorted([(x,z)for x in range(7,24)for z in range(7,23)if b.blocks.get((x,f,z),'minecraft:air')!='minecraft:air'],key=lambda q:sum(q)):
  pts=[proj(a,c)for a,c in [(x,z),(x+1,z),(x+1,z+1),(x,z+1)]];col=['#b39774','#dec8a0','#a7aea7'][idx]
  parts.append('<polygon points="'+' '.join(f'{a:.1f},{c:.1f}'for a,c in pts)+f'" fill="{col}" stroke="#706553" stroke-width=".4"/>')
 title=['1F · 居酒屋 / 后厨 / 卫浴','2F · 卧室 / 茶席 / 书桌','木顶与屋架基面'][idx]
 parts.append(f'<text x="28" y="{base-90}" class="cap">{title}</text><text x="28" y="{base-65}" class="small">源标高 y = {f} · 图中省略家具</text>')
 if idx<2:
  for xx,zz,t in [(10,13,'楼梯'),(18,10,'厨房 / 卫浴'if idx==0 else'卧室'),(18,19,'吧台 / 餐位'if idx==0 else'茶席 / 沙发')]:
   xx,zz=proj(xx,zz);parts.append(f'<text x="{xx}" y="{zz}" text-anchor="middle" class="small">{t}</text>')
parts.append('<text x="28" y="822" class="small">上层图表示木顶和屋架基面，不是屋顶全形；坡屋面见四向立面与主视。</text></svg>');(D/'exploded.svg').write_text(''.join(parts))
contract={'design_brief':sp['design_brief'],'spatial_spec':{'floors':sp['floor_blocks'],'rooms':sp['rooms'],'doors':sp['doors'],'stairs':sp['stairs'],'plants':sp['plants'],'lights':sp['lights'],'activity_points':sp['use_points']},'facade_spec':{'main_roof':'simple east-west ridge, half-step slopes, 2–3-block eaves','secondary_eave':'south shop canopy turning onto east facade','walls':'spruce timber frame, warm pale plaster, dark thin shutters','storefront':'sign above, blue noren beside clear door, lanterns under supported beams, plants left, menu right','garden':'rear north, compact planted corner with basin and wood platform'},'seed':sp['seed'],'randomness':sp['randomness'],'source_nbt_sha256':sp['source_nbt_sha256']}
contract['spatial_spec']['paintings']=sp.get('paintings',[]);contract['spatial_spec']['refit_groups']=sp.get('refit_groups',[])
(R/'design_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2))
(R/'design_prompts.txt').write_text('长关键词：原创老式日式街角町屋，二层木构居酒屋兼住家；简单灰黑切妻屋顶，深檐、分层瓦口、可见椽端、主檐与店前小檐区分；浅色灰泥与深木梁柱、退进格窗和薄木格扇。入口与门框同平面，店名在上，蓝暖帘避开门前，左右悬灯、左侧高低盆栽和低凳、右侧菜单台。首层三席吧台、两组四人桌席、楼道木桶和三幅原版墙画、后厨两侧工作带与独立卫浴，楼上真床、床头柜、衣柜、书桌、浅色软席、低茶几和薄扶手沙发；后侧小庭院木平台、竹株、水钵、灯与小盆。全部功能空间有支点灯具；固定交通、门窗和家具，只按组变化植物种类与株高，不做破洞旧化。遵守最终 NBT 的坐标与尺寸，非 Freedom 逐格复刻。\n短关键词：老式日式町屋，灰瓦深檐、木格窗、蓝暖帘，楼下居酒屋楼上起居，细柜体、床组、低茶席、盆栽和小庭院。\n视图：四个45°日夜景，同尺度四立面，垂直分层俯视，X=20向西剖面；人物视角保留屋顶和天花；爆炸只拉开层距。\n')
print('design contract and exploded diagram written')
