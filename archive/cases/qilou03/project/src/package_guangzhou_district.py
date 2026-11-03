"""Package the final bounded block case, exact renders and reproducible sources."""
from pathlib import Path
import ast,json,sys,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];D=ROOT/'delivery';R=ROOT/'runs'/RUN
read=lambda p:json.loads(p.read_text())
check=read(D/'viewer_check.json');assert check['control_harness']=='pass'and check['embedded_download_bytes']=='exact'
sp=read(R/'spec.json');wc=read(R/'world_check.json');rp=read(R/'repro_check.json');a=read(R/'audit.json')
assert a['pass']and wc['mismatches']==0 and all(rp['identical_replay'].values())and not rp['scope_violations']
files=set()
def take(p):
 p=Path(p)
 if p.is_file()and'__pycache__'not in p.parts:files.add(p)
entries=['build_guangzhou_district','qilou_recipes','qilou_core','qilou_states','audit_guangzhou_district','verify_guangzhou_district','render_guangzhou_district','export_guangzhou_world','report_guangzhou_district','package_guangzhou_district','inspect_rongyinli_reference','fetch_vanilla_assets']
modules={p.stem:p for p in(ROOT/'src').glob('*.py')};queue=list(entries);seen=set()
while queue:
 name=queue.pop()
 if name in seen or name not in modules:continue
 seen.add(name);p=modules[name];take(p)
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Import):queue.extend(x.name.split('.')[0]for x in n.names)
  if isinstance(n,ast.ImportFrom)and n.module:queue.append(n.module.split('.')[0])
take(ROOT/'src/check_guangzhou_viewer.cjs')
for folder in['support','research']:
 for p in(ROOT/folder).rglob('*'):take(p)
for fn in['vanilla_source.json','render_shader_reference.html','guangzhou_report.html','guangzhou_viewer.js']:take(ROOT/'assets'/fn)
take(ROOT/'input/template_level.dat')
for p in R.glob('*'):
 if p.suffix in['.json','.nbt']:take(p)
for g in['Qilou03']+[b['id']for b in sp['buildings']]:
 folder=ROOT/'review/previews'/(RUN+'_'+g)
 for p in folder.glob('*.png'):take(p)
 for fn in['views_full.json','cameras_full.json','scene/scene.json']:take(folder/fn)
for fn in['Qilou03.html','Qilou03_Preview.png','Qilou03_Spatial.json','Qilou03_World_1.21.1.zip','viewer_check.json']:take(D/fn)
uses=sum(len(x['uses'])for x in a['reports']if x['group']!='Qilou03')
readme=f'''檐下榕里 · 广州街巷 / Qilou03 / {RUN}
28 栋：12 栋骑楼 + 16 栋城中村楼；6 处宽斜切转角。
原创组合，以 HAF 0.4 工作流组织；不是现实测绘复原或任意街区生成器。

查看
打开 delivery/Qilou03.html。默认先看主街，再切换单栋、四向、昼夜、近景、逐层平面、剖面与分层展开。
地图和建筑卡片可直接跳转；HTML 自带 29 份 NBT、空间用途清单和试玩 ZIP，离线可用。

试玩
解压 delivery/Qilou03_World_1.21.1.zip，将 Qilou03_World 文件夹放进 Java 版 saves，用 1.21.1 打开。
总尺寸 244 × 58 × 216 格，出生点 {' / '.join(map(str,wc['spawn']))}，主街向东。
原版方块，无必需模组。首次载入由游戏重算光照；/time set night 查看夜景。
单栋及整体 NBT：runs/{RUN}。整体超过原版结构方块单次尺寸，附带存档可直接打开。
坐标 X 向东、Y 向上、Z 向南。单栋门面统一朝南，由 placement.turn 按 90 度旋转拼接。

街区组织
主街 12 格；贯通南北支路 10 格；东侧丁字支路 9 格；后街约 6 格，纵巷约 4～8 格。
12 栋骑楼两至三层，城中村四至六层，面宽 15 / 17 / 19 / 23 格组合。
四个骑楼角的斜切约 6 格，冰室和面馆另有斜切体量。道路从街区边缘延伸出去，公共路网贯通。
含营业区、后勤、楼梯、住宅起居、餐厨、盥洗、床组、沙发、植物。屋顶水箱、晾晒架与设备为装饰，未提供上屋顶楼梯。
28 株阔冠树、树池草花、口袋绿地、长座、候车棚、小后院；树冠保护室内和阳台空间。

随机性
街网、地块、建筑形体、层数和用途为本案编排，种子不改变这些内容。
不同种子控制百叶、压顶材质、盆栽物种、树冠和树下植物。不是逐块随机撒噪点，也未宣称通用城市生成。

验证
{uses} 个单栋功能点；{sum(len(x['stairs'])for x in a['reports']if x['group']!='Qilou03')} 段楼梯；28 栋主入口、侧向或居住入口和后门接入公共步行网络。
门框、床、花盆、挂画、灯具锚点；廊道遮盖、道路和巷道净空。
旋转拼接后逐块核对各栋建筑，景观未覆盖建筑。
同种子 29 份 NBT 字节一致；另一种子变动 {rp['changed_cells']} 处已声明细部和植物，布局、用途与动线相同。
世界回读 {wc['checked_cells']:,} 个位置，0 差异；{wc['block_entities']} 个方块实体和 {wc['entities']} 个挂画载荷一致。
所有图像绑定最终 NBT 哈希。HTML 控件和内嵌下载已做脚本检查，未运行真实浏览器布局检查。

限制
未启动 Minecraft 客户端。通行是近似 0.6 × 1.8 格身体、开门状态及楼梯采样；实际碰撞、尺度、夜景需试玩。
桌椅与沙发是装饰造型，无坐下功能。离线预览使用官方模型与纹理颜色采样；实体外观、植物染色和灯光有近似，并非游戏截图。
源码为案例适配器，不是通用户型或地块求解器，也没有训练模型权重。

版本
Qilou01：3 栋骑楼小样。
Qilou02：12 栋围合街坊。
Qilou03：28 栋骑楼与城中村混合街区，重新组织主街、支路、后巷和宽斜切转角。
榕荫里 V4 仅用于读取旧存档平面、参考斜切体量；本轮城中村几何重新制作。
research 中保留参考照片、署名、切片图和来源哈希。部分旧研究文件来自父案例，当前设计以 design_brief_qilou03.json 为准。

复现（Python 3.12；依赖 requirements.txt；渲染另需 Linux EGL/OpenGL ES）
python src/build_guangzhou_district.py REBUILD01 311145
python src/fetch_vanilla_assets.py
python src/audit_guangzhou_district.py REBUILD01
python src/render_guangzhou_district.py REBUILD01 full
python src/export_guangzhou_world.py REBUILD01 delivery/Qilou03_World_REBUILD01
python src/build_guangzhou_district.py REBUILD01_REPLAY 311145
python src/build_guangzhou_district.py REBUILD01_VARIANT 311146
python src/verify_guangzhou_district.py REBUILD01
python src/audit_guangzhou_district.py REBUILD01_VARIANT
python src/report_guangzhou_district.py REBUILD01
node src/check_guangzhou_viewer.cjs delivery/Qilou03.html REBUILD01
python src/package_guangzhou_district.py REBUILD01
使用新运行名，避免旧图像缓存混入。
官方游戏资产未打包；获取脚本核对固定版本哈希。照片版权归原作者，非 Mojang 官方作品。
'''
(ROOT/'README_先看这里.txt').write_text(readme,encoding='utf-8');take(ROOT/'README_先看这里.txt')
(ROOT/'requirements.txt').write_text('numpy>=1.26\nPillow>=10\nnbtlib>=2.0\n');take(ROOT/'requirements.txt')
(ROOT/'ASSET_NOTICE.txt').write_text('Minecraft Java 1.21.1 models and textures are not redistributed as source assets. NBT-derived rendered previews and individually attributed reference photographs are included. This is not an official Mojang product.\n');take(ROOT/'ASSET_NOTICE.txt')
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(files)]
archive=D/'Qilou03_Project.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):z.write(p,'Qilou03_Project/'+str(p.relative_to(ROOT)))
 z.writestr('Qilou03_Project/MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive)as z:assert z.testzip()is None
print(json.dumps({'project_bytes':archive.stat().st_size,'files':len(files),'source_modules':sorted(seen)},ensure_ascii=False))
