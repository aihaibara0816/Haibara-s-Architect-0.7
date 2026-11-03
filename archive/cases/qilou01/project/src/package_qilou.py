"""Package the bounded case and provenance, excluding client assets and stale experiments."""
from pathlib import Path
import ast,json,sys,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];D=ROOT/'delivery';R=ROOT/'runs'/RUN
assert (D/'viewer_check.json').exists()
files=set()
def take(path):
 p=Path(path)
 if p.is_file() and '__pycache__' not in p.parts:files.add(p)
entries=['build_qilou','qilou_states','audit_qilou','verify_qilou','render_qilou','export_qilou_world','report_qilou','package_qilou','fetch_vanilla_assets']
modules={p.stem:p for p in (ROOT/'src').glob('*.py')};queue=list(entries);seen=set()
while queue:
 name=queue.pop()
 if name in seen or name not in modules:continue
 seen.add(name);p=modules[name];take(p)
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Import):queue.extend(x.name.split('.')[0]for x in n.names)
  if isinstance(n,ast.ImportFrom) and n.module:queue.append(n.module.split('.')[0])
take(ROOT/'src/check_qilou_viewer.cjs')
for root in ['support','research']:
 for p in (ROOT/root).rglob('*'):take(p)
for fn in ['vanilla_source.json','render_shader_reference.html','qilou_report.html','qilou_viewer.js']:take(ROOT/'assets'/fn)
take(ROOT/'input/template_level.dat')
for p in R.glob('*'):
 if p.suffix in ['.json','.nbt']:take(p)
for g in ['Qilou01','Grocery','Apothecary','Teahouse']:
 folder=ROOT/'review/previews'/(RUN+'_'+g)
 for p in folder.glob('*.png'):take(p)
 for fn in ['views_full.json','cameras_full.json','scene/scene.json']:take(folder/fn)
for fn in ['Qilou01.html','Qilou01_Preview.png','Qilou01_Spatial.json','Qilou01_World_1.21.1.zip','viewer_check.json']:take(D/fn)
readme=f'''檐下西关 · Qilou01 / {RUN}
三栋原创广式骑楼小样，HAF 0.4 工作流案例

1. 先打开 delivery/Qilou01.html。HTML 自带全部图片、三栋与组合 NBT、空间清单、存档 ZIP，可离线使用。
2. 直接试玩：解压 delivery/Qilou01_World_1.21.1.zip，把 Qilou01_World 文件夹放入 Java 版 saves，用 1.21.1 打开。
   出生点 -3 / 65 / 17；试作总尺寸 76 × 40 × 52 格。世界首次载入由游戏重算照明。
3. 单栋 NBT 在 runs/{RUN}；若放入其他地图，先备份地图，再用支持结构 NBT 的导入工具。
   单栋最大 23 × 34 × 33 格；三栋组合更大，直接使用附带存档更方便。

设计内容
和顺杂货：两层，首层经营与备货，楼上生活。
济安药铺：三层，发药咨询 / 库存账房 / 店主住居，带凹阳台。
榕荫茶楼：三层，餐饮后厨 / 茶厅 / 住居，转角双面廊。
常规骑楼廊净宽 4 格，斜切转角局部 3 格。三栋接成连续的廊下步行空间。
三种立面与家具布局分别设计；随机种子仅控制已限定位置的盆栽物种。
参考广州西关骑楼，但不是测绘复原；15 / 17 / 23 格面宽为游戏空间实验。

验证与局限
所有 NBT、图像、存档绑定本轮最终 SHA-256，见 runs/{RUN}/gallery_catalog.json。
46 个功能点、5 段楼梯、3 个主入口及整段廊道经过近似几何检查。
存档回读 245,760 个位置，0 方块差异，方块实体和挂画载荷均核对。
没有启动 Minecraft 客户端。家具坐下、真实碰撞、光照与实际游玩仍待体验。
预览使用 1.21.1 官方模型和纹理颜色采样。床与招牌等实体细节近似；不是游戏截图。
模型单栋与组合的一致性、同种子复现和异种子的变化范围，见 repro_check.json。

源码重建（Python 3.12；numpy、Pillow、nbtlib；预览额外需要 Linux EGL / OpenGL ES）
在项目根目录安装 requirements.txt 中的 Python 依赖，然后使用新的运行名称，例如 REBUILD01。
python src/build_qilou.py REBUILD01
python src/fetch_vanilla_assets.py
python src/audit_qilou.py REBUILD01
python src/render_qilou.py REBUILD01 full
python src/export_qilou_world.py REBUILD01 delivery/Qilou01_World_REBUILD01
重现性报告还需分别生成 REBUILD01_REPLAY（种子 311145）、REBUILD01_VARIANT（种子 311146），随后运行 verify_qilou.py REBUILD01。
report_qilou.py REBUILD01 生成 HTML，node src/check_qilou_viewer.cjs delivery/Qilou01.html 检查交互与内嵌下载，package_qilou.py REBUILD01 打包。
不要使用已有运行名称覆盖实验，避免临时文件或旧预览混入。

官方游戏资产未打包。fetch_vanilla_assets.py 从 Mojang 元数据获取已固定版本，并核对 assets/vanilla_source.json 的哈希。
参考照片与署名保留在 research；照片版权归原作者。不得把本案例的原创房间布置当成真实建筑的平面证据。
本次是 3 栋小样，尚未制作完整街景，也没有训练模型权重或新增通用骑楼生成器。
'''
(ROOT/'README_先看这里.txt').write_text(readme,encoding='utf-8');take(ROOT/'README_先看这里.txt')
(ROOT/'requirements.txt').write_text('numpy>=1.26\nPillow>=10\nnbtlib>=2.0\n');take(ROOT/'requirements.txt')
(ROOT/'ASSET_NOTICE.txt').write_text('Minecraft Java 1.21.1 models and textures are not redistributed as source assets. Rendered previews are derived from the supplied NBT. Reference photographs are attributed individually in the HTML and research records. This project is not affiliated with Mojang.\n');take(ROOT/'ASSET_NOTICE.txt')
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(files)]
archive=D/'Qilou01_Project.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):z.write(p,'Qilou01_Project/'+str(p.relative_to(ROOT)))
 z.writestr('Qilou01_Project/MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive)as z:assert z.testzip() is None
print(json.dumps({'project_bytes':archive.stat().st_size,'files':len(files),'source_modules':sorted(seen)},ensure_ascii=False))
