"""Distributable case sources and outputs; excludes client/runtime/game assets."""
from pathlib import Path
import ast,sys,json,zipfile,hashlib,os
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs'/sys.argv[1];D=ROOT/'deliverables';s=json.loads((R/'spec.json').read_text());check=json.loads((D/'Qilou04_checks.json').read_text());assert check['offline_geometry']['pass']and check['world_readback']['mismatches']==0 and check['variation']['same_seed_nbt_bytes_identical']and check['control_check']['pass']and check['shader_check']['pass']and check['landscape_and_roofs']['pass']and check['game_capture']['pass']
files=set()
def take(p):
 p=Path(p)
 if p.is_file()and'__pycache__'not in p.parts:files.add(p)
modules={p.stem:p for p in(ROOT/'src').glob('*.py')};queue=['build_district','audit_district','verify_district','render_district','render_interiors','export_world','pack_interactive','check_packed_gpu','report_district','package_district','compile_viewer','fetch_vanilla_assets','record_game_capture','check_report','check_revision','check_activity'];seen=set()
while queue:
 name=queue.pop()
 if name in seen or name not in modules:continue
 seen.add(name);p=modules[name];take(p)
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Import):queue.extend(a.name.split('.')[0]for a in n.names)
  elif isinstance(n,ast.ImportFrom)and n.module:queue.append(n.module.split('.')[0])
for name in ['check_interaction.cjs','check_report.cjs','check_browser.cjs']:take(ROOT/'src'/name)
for folder in['support','hafusion','docs']:
 for p in(ROOT/folder).rglob('*'):take(p)
for name in ['vanilla_source.json','render_shader_reference.html','interactive_shader_reference.html','interactive_app.js','interactive_compiled.js','interactive_shell.html','matrix_math.js']:take(ROOT/'assets'/name)
take(ROOT/'input/template_level.dat')
for p in R.glob('*'):
 if p.suffix in['.json','.nbt']and p.name!='interactive_payload.json':take(p)
for id in ['Qilou04']+[b['id']for b in s['buildings']]:
 d=ROOT/'review/previews'/(R.name+'_'+id)
 for p in d.glob('*.png'):take(p)
 for name in ['cameras_full.json','views_full.json','scene/scene.json']:take(d/name)
for p in(ROOT/'review/game').glob('*'):
 if p.suffix in['.json','.png','.txt']:take(p)
for name in ['Qilou04.html','Qilou04_Model.html','Qilou04_Plan.svg','Qilou04_Preview.png','Qilou04_Game_Preview.png','Qilou04_checks.json','Qilou04_World_1.21.1.zip','report_check.json']:take(D/name)
readme=f'''榕灰里 · 骑楼与里巷 / Qilou04 / HAF 0.4
44栋 = 12栋骑楼 + 32栋城中村住宅、店住楼。
原创组合街区；不是北京路、一德路的测绘复原，也不是通用城市规划器。

观看
打开 deliverables/Qilou04.html。旋转模型按按钮加载，支持拖动、缩放、四向、昼夜、单栋和逐层内饰。
近景为实际Minecraft Java 1.21.1客户端的F2截图，1920×1080原始PNG，原版材质、无外部光影。
总览、单栋外观、剖面与爆炸图是NBT离线渲染，材质采样和光照近似；页面分别标注。
近景可查看/下载原图。44栋卡片均可下载单栋NBT。完整NBT和世界ZIP已内嵌，离线可用。

地图
解压 Qilou04_World_1.21.1.zip，将Qilou04文件夹放进Java版saves目录，用1.21.1载入。
范围356×84×250格；出生点22,65,-4。原版方块，无必需模组。
/time set night 看夜景。独立NBT位于runs/{R.name}。
完整街区及部分独栋超过原版结构方块单次尺寸，需支持大结构的导入工具；附带存档可以直接打开。
方向X东、Y上、Z南。placement为各独栋在整区的位置与旋转。

本次变化 · R19
沿街住宅补商业界面：19栋商业首层，22处直接面街店面。独立住宅入口与楼梯保留。
随机夜景按住户状态分组，主路有挑臂灯、巷口低灯、檐下店灯；这是静态夜景快照，并非自动开关电路。
以下R18已认可的体量、色彩、屋顶与景观继续沿用：
主街两侧保持连续骑楼，后面及过街以生活住宅为主，十字路口西北角让出榕树广场。
32栋住宅有{check["variation"]["unique_residential_width_depth_height"]}种宽深层数组合，2至12层；包含深窄、横长、前切角、后切角、组合凹口。
骑楼保留灰白，并穿插米黄、暖黄、浅粉与砖红；住宅另有淡青绿。逐栋主色、修补程度分别变化。
三栋大骑楼分别38、46、51格宽，穿插在普通店铺之间；混合平顶、露台、双坡和四坡顶。
A3为11层，E2为12层；两栋高楼错位设置，其余住宅2—8层。
重做{len(s["trees"])}株景观树，包含分枝主榕、阔叶树和少量棕榈意象；树下连续绿地、灌木与蕨草。
绿地共{s["landscape"]["planted_ground_cells"]}格，保护主街、巷路与入口；灰石铺装按片区修补变化。

随机性
主街骨架与地块关系为本案编排，始终保留公共道路。
不同种子独立调整住宅宽深、退距、楼高、住户亮灯与细节；限制在各自地块范围内。
基准种子311148；对照种子311149。{check["variation"]["changed_massing"]}栋住宅体量改变，{check["variation"]["changed_setbacks"]}栋退距改变；两个版本均通过离线通行检查。
同种子{check["variation"]["replay_files"]}份NBT字节完全一致。不是逐块随机撒材质，也没有训练模型权重。

检查与限度
源NBT SHA256: {s['source_nbt_sha256']}
{check['world_readback']['checked_cells']:,}格世界回读0差异，方块实体与绘画实体载荷一致。
单栋拼接后{check["variation"]["preserved_module_blocks_checked"]}个地面以上源方块保留；只允许{check["variation"]["allowed_join_connection_updates"]}处邻接连接属性更新，无建筑被景观覆盖。
离线检查{len(s["entries"])}处外部入口、{sum(b["levels"] for b in s["buildings"])}层对应空间、门框、楼梯、床组及家具前方通行。
JavaScript控件、数据范围及Mesa EGL实际着色器已检查；所有44栋、{sum(b["levels"] for b in s["buildings"])}层选择可执行。
实际Chrome浏览器通过桌面与手机尺寸检查：模型加载、拖动、选楼、切层、昼夜、实机近景与内嵌模型选择。
另已启动原版1.21.1客户端载入世界并取景；截图以review/game中的原始PNG为准。
未逐户实测每一张床、每个容器及全部楼梯交互，也未做游戏帧率基准。桌椅与沙发为方块造型，无坐下功能。

代码复现
Python3.12，numpy、Pillow、nbtlib；渲染使用Linux EGL。
python src/build_district.py NewRun 311148
python src/fetch_vanilla_assets.py
python src/audit_district.py NewRun
python src/render_district.py NewRun full
python src/render_interiors.py NewRun
python src/pack_interactive.py NewRun
python src/check_packed_gpu.py NewRun
node src/check_interaction.cjs . NewRun
python src/export_world.py NewRun world/NewWorld
原始Minecraft客户端、Java运行时、模型纹理资源不打包。获取资源脚本核对Java1.21.1固定哈希。
完整报告生成另需世界ZIP、变体/回放报告和实机截图；交付版都已包含。
本工程仅记录本案例；没有自动修改用户技能。
'''
(ROOT/'README_先看这里.txt').write_text(readme);take(ROOT/'README_先看这里.txt');(ROOT/'requirements.txt').write_text('numpy>=1.26\nPillow>=10\nnbtlib>=2.0\n');take(ROOT/'requirements.txt')
(ROOT/'ASSET_NOTICE.txt').write_text('Unofficial Minecraft building study. Mojang client/runtime/original texture assets are not redistributed. Includes original case sources, NBT/world data, rendered previews, and game screenshots. Research links and attribution are in Qilou04.html.\n');take(ROOT/'ASSET_NOTICE.txt')
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(files)]
with zipfile.ZipFile(D/'Qilou04_Project.zip.partial','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):z.write(p,'Qilou04_Project/'+str(p.relative_to(ROOT)))
 z.writestr('Qilou04_Project/MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with (D/'Qilou04_Project.zip.partial').open('rb')as f:os.fsync(f.fileno())
os.replace(D/'Qilou04_Project.zip.partial',D/'Qilou04_Project.zip')
with zipfile.ZipFile(D/'Qilou04_Project.zip')as z:assert z.testzip()is None
with zipfile.ZipFile(D/'Qilou04_Game_Screenshots.zip.partial','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted((ROOT/'review/game').glob('*')):
  if p.suffix in['.png','.json','.txt']:z.write(p,'Qilou04_Game_Screenshots/'+p.name)
with (D/'Qilou04_Game_Screenshots.zip.partial').open('rb')as f:os.fsync(f.fileno())
os.replace(D/'Qilou04_Game_Screenshots.zip.partial',D/'Qilou04_Game_Screenshots.zip')
with zipfile.ZipFile(D/'Qilou04_Game_Screenshots.zip')as z:assert z.testzip()is None
print(json.dumps({'files':len(files),'source_modules':sorted(seen),'project_bytes':(D/'Qilou04_Project.zip').stat().st_size,'screenshot_zip_bytes':(D/'Qilou04_Game_Screenshots.zip').stat().st_size}))
