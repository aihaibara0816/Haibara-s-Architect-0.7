"""Package the verified P4 case, retaining NBT history and omitting mesh caches."""
from pathlib import Path
import sys,json,hashlib,zipfile,shutil
C=Path(__file__).resolve().parents[1];PROJECT=C.parents[2]
run=sys.argv[1];world=Path(sys.argv[2]);out=Path(sys.argv[3]);R=C/'runs'/run
qa=json.loads((R/'checks.json').read_text());land=json.loads((R/'landscape_check.json').read_text());wc=json.loads((R/'world_check.json').read_text())
assert not qa['uncontained_water'] and qa['unhydrated_crop_count']==0 and land['primary_water_components']==1 and not land['new_path_blockers']
assert wc['source_nbt_sha256']==qa['source_nbt_sha256'] and not wc['blockstate_mismatches'] and not wc['unexpected_blocks_in_air']
shutil.copy2(R/'building.nbt',PROJECT/'Tiangengli18.nbt')
text=f'''田埂里 · P4 田园深化版 · 最终 {run}
日期：2026-10-29

最终结果：RuralHAF/cases/tiangengli/runs/{run}/
最终结构：Tiangengli18.nbt（与该run的building.nbt逐字节相同）
世界存档另见 Tiangengli18_World_1.21.1.zip，解压后把Tiangengli18放入.minecraft/saves。
使用Minecraft Java 1.21.1；出生点(-15,64,-9)，创造模式、允许指令。

本次修改
- 原有32片田地内侧下沉一格，村路和田埂保留；其中8片改为浅水田，24片为下沉旱田/休耕田。
- 浅水田用原版水面、湿土种植条、小麦幼苗表达；并非原生水稻，无需模组。
- 外围主渠、支渠、田边集水沟与灌溉塘连通，路下保留涵洞；旱田配下田踏步。
- 3处小菜园、13棵新增疏密不同的小树、竹丛、农具棚、柴棚、草垛、禽舍围栏、泵棚、农机陈设。
- 原18栋房屋、6座农业棚保留；房屋源构件{land['protected_house_blocks']:,}格逐一比较未改动。
- 原161个灯方块完整保留，新增12个灯方块，合计173；住人层保持灯位，田间较暗。
- 位置、苗龄、树高和树冠按固定随机种子生成；本版种子20261029。

验证
checks.json：单一路网、18户门口净空、34个使用楼层灯位、{qa['crop_count']:,}格作物承托与灌溉检查通过，水体底部/侧边未发现缺口。
landscape_check.json：{land['primary_water_cells']:,}格下沉水体连成1个网络；32块田与主渠连接；新小路{land['new_path_cells']}格的两格净空通过。
world_check.json：360个区块，4,423,680个位置从写出MCA重新读取，方块状态与空气位置均与最终NBT吻合。
四向等尺度昼夜图、正俯视图和局部近景均从最终NBT读回生成；共19个视角，另有41张逐层切片。
本版没有运行Minecraft客户端或服务端。水体更新、实际光照、玩家完整碰撞和交互仍待游戏内验收。
isLightOn=0，首次进世界由游戏重算光照。默认冻结昼夜、天气和随机生长以保留展示状态。
/time set night 或 /time set day 切换；/gamerule randomTickSpeed 3 恢复随机生长。

真实性与边界
这是已有P3案例的局部深化，并非任意建筑自动复原引擎。
预览使用简化方块形状、材质和离线照明，不是游戏截图；原版光源不提供真正冷暖彩色光传播。
禽舍和农机是静态场景构件，未新增动物、可驾驶车辆或产物系统；树冠为果树意向，没有原生果实系统。
水渠连通仅为水方块的几何拓扑，不是水力流量模拟或游戏液体更新实测。
场地320×288格，NBT大小320×48×288，世界平移(-160,60,-144)。
NBT是稀疏结构，导入其他世界时不会自动清除未列出的空气；整片体验优先使用附带世界。

修订记录
P3_B1—P3_B4：前版房屋、田地与灯光建造，原README保存在README_P3_B4.txt。
P4_B1：首轮景观；检查发现部分菜园灌溉不足和旧支渠未连通。
P4_B2：补通旧渠和菜园灌溉；修渠时碰到菜园侧边，结果保留作诊断。
P4_B3：水体、灌溉及原道路检查通过；扩展检查发现新小路与老树、灯柱、农机相交。
{run}：新小路绕行，灯位移至路侧，修剪低枝；最终几何与存档检查通过。

复跑（Python 3.12，依赖requirements.txt，离线预览需要Mesa libEGL.so.1）
在工程根目录执行，以未使用的新run名替换P4_REBUILD：
python3 RuralHAF/cases/tiangengli/src/revise_landscape.py P4_REBUILD
python3 RuralHAF/cases/tiangengli/src/verify_build.py P4_REBUILD
python3 RuralHAF/cases/tiangengli/src/verify_landscape.py P4_REBUILD
python3 RuralHAF/tools/render_building_case.py --case tiangengli --run P4_REBUILD
解压WorldTemplate_Java_1.21.1.zip至template后：
python3 RuralHAF/cases/tiangengli/src/write_world.py P4_REBUILD template/Tiangengli_13_1_21_1 output_world
python3 RuralHAF/cases/tiangengli/src/make_report_p4.py P4_REBUILD output_report RuralHAF/cases/tiangengli/input/source_plan_P3.png
原P3_B4 NBT及构件归属为本次直接输入，均随包附带；无需旧工作目录。中间网格可重建，不放入归档。

最终NBT SHA-256：{qa['source_nbt_sha256']}
本次查看前版建成俯视/近景接续修改，没有重新观看早期参考视频。源房型记录见README_P3_B4.txt。
许可见ATTRIBUTION.md及support/fonts/OFL.txt。
'''
(PROJECT/'README.txt').write_text(text)
def include(f):
 rel=f.relative_to(PROJECT)
 if any(p.startswith('.') or p in ('__pycache__','scene') for p in rel.parts) or f.suffix=='.pyc':return False
 if 'previews' in rel.parts and not any(p in ('P3_B4',run) for p in rel.parts):return False
 return f.is_file() and f.name!='FILE_MANIFEST.json'
files=sorted(f for f in PROJECT.rglob('*') if include(f))
manifest=[{'path':str(f.relative_to(PROJECT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
(PROJECT/'FILE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out/'Tiangengli18_Project.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for f in files+[PROJECT/'FILE_MANIFEST.json']:z.write(f,Path('Tiangengli18_Project')/f.relative_to(PROJECT))
with zipfile.ZipFile(out/'Tiangengli18_World_1.21.1.zip','w',zipfile.ZIP_DEFLATED,6) as z:
 for f in sorted(world.rglob('*')):
  if f.is_file() and f.name not in ('session.lock',):z.write(f,Path('Tiangengli18')/f.relative_to(world))
for f in out.glob('*.zip'):
 with zipfile.ZipFile(f) as z:assert z.testzip() is None
print(json.dumps({'run':run,'project_files':len(files)+1,'deliverables':[{ 'name':f.name,'bytes':f.stat().st_size} for f in sorted(out.iterdir()) if f.is_file()]},ensure_ascii=False))
