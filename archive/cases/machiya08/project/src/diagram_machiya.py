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
contract['spatial_spec']['under_stair']=sp.get('under_stair')
contract['facade_spec']=sp.get('frontage',contract['facade_spec'])
(R/'design_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2))
(R/'design_prompts.txt').write_text("""长关键词：原创老式日式街角町屋，二层木构居酒屋兼住家；灰黑主切妻屋顶、一个较小前向山墙、分层瓦口、屋脊和可见椽端。首层店檐按窗台与入口分段，长短深浅有区别。浅色灰泥配深木梁柱，上层书桌窄窗与起居长窗分组，薄格扇、承托窗沿和两端盆栽。营业状态的首层：左侧四格开放窗台，中段三格宽退入入口，右侧客席开窗，侧向短台面；暖帘位于高处，薄板停在柱侧。主入口原木门移除，无打烊闭合机制；其余七樘门保留。店名在左窗上方，菜单挂柱边，入口、窗台、侧面及上层局部有支撑灯；红色候位凳与高低盆组偏置，门口通路留空。首层三席吧台、两组四人桌席、楼道库存和三幅真实原版墙画，后厨两侧工作带及独立卫浴；楼梯下半开放备货角有低柜、侧柜、薄壁架、布巾和灯。楼上两张真床、床头柜、衣柜、书桌、浅色软席、低茶几、薄扶手沙发；后庭木平台、竹株、水钵和小盆。固定交通、门窗、家具和照明，只按稳定分组变化植物种类与竹高。遵守最终 NBT 的坐标和尺寸，非 Freedom 逐格复刻。
短关键词：老式日式町屋，开放临街居酒屋，退入入口，分组木格窗，主切妻与小前山墙，分段深檐，暖帘和局部灯，细柜体、完整床组、低茶席、植物软化。
视图：同机位新旧店口与整栋对照；人物视角保留屋顶与天花；四个45°日夜景，同尺度四立面，垂直分层俯视，X=20向西剖面，门面局部裁切。楼板爆炸仅拉开层距。
边界：上层窗沿不可走，屋面小山墙没有可进入阁楼，座位与杯瓶为原版方块造型，离线图不是实机截图。
""")
print('design contract and exploded diagram written')
