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
entries=['build_qilou_district','qilou_core','qilou_states','audit_qilou_district','verify_qilou_district','render_qilou_district','export_qilou_district_world','report_qilou_district','package_qilou_district','fetch_vanilla_assets']
modules={p.stem:p for p in(ROOT/'src').glob('*.py')};queue=list(entries);seen=set()
while queue:
 name=queue.pop()
 if name in seen or name not in modules:continue
 seen.add(name);p=modules[name];take(p)
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Import):queue.extend(x.name.split('.')[0]for x in n.names)
  if isinstance(n,ast.ImportFrom)and n.module:queue.append(n.module.split('.')[0])
take(ROOT/'src/check_qilou_district_viewer.cjs')
for folder in['support','research']:
 for p in(ROOT/folder).rglob('*'):take(p)
for fn in['vanilla_source.json','render_shader_reference.html','qilou_district_report.html','qilou_district_viewer.js']:take(ROOT/'assets'/fn)
take(ROOT/'input/template_level.dat')
for p in R.glob('*'):
 if p.suffix in['.json','.nbt']:take(p)
for g in['Qilou02']+[b['id']for b in sp['buildings']]:
 folder=ROOT/'review/previews'/(RUN+'_'+g)
 for p in folder.glob('*.png'):take(p)
 for fn in['views_full.json','cameras_full.json','scene/scene.json']:take(folder/fn)
for fn in['Qilou02.html','Qilou02_Preview.png','Qilou02_Spatial.json','Qilou02_World_1.21.1.zip','viewer_check.json']:take(D/fn)
uses=sum(len(x['uses'])for x in a['reports']if x['group']!='Qilou02')
readme=f'''檐下西关 · 四角里 / Qilou02 / {RUN}
12 栋原创广式骑楼、4 处转角、4 条穿巷、1 个共享内院。
这是 HAF 0.4 工作流的骑楼街坊案例；不是现实测绘复原或任意街区生成器。

直接查看
delivery/Qilou02.html 自带全部模型视图、13 份 NBT、空间清单和存档 ZIP，可离线使用。
上方先选街区或单栋，再选类别和视角；昼夜、放大、下载此图可独立控制。
布局图、12 栋建筑卡片和四个转角快捷入口可直接跳转。

直接试玩
解压 delivery/Qilou02_World_1.21.1.zip，把 Qilou02_World 文件夹放入 Java 版 saves，用 1.21.1 打开。
总尺寸 144 × 44 × 144 格，出生点 {' / '.join(map(str,wc['spawn']))}，面向北侧进入南街。
全为原版方块，无必需模组；首次载入由游戏重算光照。用 /time set night 看夜景。
单栋 NBT 与整体 NBT 在 runs/{RUN}。每个单栋统一门面朝南，拼接旋转见 spec.json。
整体 NBT 超过原版结构方块的单次尺寸范围，直接打开附带存档更方便。

内容与衔接
四角：西北邮局、东北书局为两层；东南茶楼、西南客栈为三层。
中段：药铺、粮油、理发、五金、布庄、杂货、诊所、饼铺。药铺和诊所为三层，其余两层。
常规廊道净宽 4 格，斜切转角局部 3 格；穿巷宽 5 格，外街宽 12 格。
8 个中段店屋有服务后门，四条穿巷汇入共享庭院。庭院有长座、清洗工作台和树荫。
8 株街树、2 株庭院树，草花和盆栽按位置成组。
固定设计建筑位置、层数和用途；种子控制百叶、压顶材质、盆栽物种、树冠和树下植物。

本轮检查
{uses} 个单栋功能点、16 段楼梯；拼接后 12 个前门、4 个侧门、8 个后门、3 个院内到达点。
廊道全段连通、遮盖与净空；外街和穿巷净空；门框、床、挂画、花盆、灯具等构件锚点。
12 栋旋转拼接的实际非空气方块与单体 NBT 一致，未被景观覆盖。
同种子 13 份 NBT 字节一致，另一种子改变 {rp['changed_cells']} 处限定细部与植物，布局和动线不变。
世界回读 {wc['checked_cells']:,} 个位置，0 方块差异，{wc['block_entities']} 个方块实体与 {wc['entities']} 个挂画载荷核对一致。
图像来源绑定最终 NBT SHA-256。部分单体与上一轮字节相同，复用对应真实预览，见 render_reuse.json。

已知限制
未启动 Minecraft 客户端。通行是近似 0.6 × 1.8 格身体、开门状态和楼梯采样。
桌椅、沙发是装饰造型；没有坐下功能。光照和碰撞仍待实际游戏体验。
离线预览用官方模型和纹理颜色采样，不是游戏截图；床、招牌等实体细节、植物染色和灯光有近似。
所有布局与店名为原创设定。源码不构成新的通用户型求解器，也未训练模型权重。

复现（Python 3.12，依赖见 requirements.txt；渲染另需 Linux EGL/OpenGL ES）
python src/build_qilou_district.py REBUILD01 311145
python src/fetch_vanilla_assets.py
python src/audit_qilou_district.py REBUILD01
python src/render_qilou_district.py REBUILD01 full
python src/export_qilou_district_world.py REBUILD01 delivery/Qilou02_World_REBUILD01
python src/build_qilou_district.py REBUILD01_REPLAY 311145
python src/build_qilou_district.py REBUILD01_VARIANT 311146
python src/verify_qilou_district.py REBUILD01
python src/audit_qilou_district.py REBUILD01_VARIANT
python src/report_qilou_district.py REBUILD01
node src/check_qilou_district_viewer.cjs delivery/Qilou02.html REBUILD01
python src/package_qilou_district.py REBUILD01
请使用新的运行名，避免已有图像与模型缓存混入。

当前版本关联
Qilou01：3 栋试作。Qilou02：扩展为 12 栋完整街坊。
本轮修复转角共墙、侧廊遮挡、门前座位、灯具、两层转角女儿墙、柜台间隙和院内窗台冲突。
后续可从实际游戏反馈继续研究窄面深进、通风天井、不规则地块及街区外部衔接。

官方游戏资产未打包，获取脚本核对固定版本哈希。
照片与来源署名保留在 research 与 HTML；版权归原作者。非 Mojang 官方作品。
'''
(ROOT/'README_先看这里.txt').write_text(readme,encoding='utf-8');take(ROOT/'README_先看这里.txt')
(ROOT/'requirements.txt').write_text('numpy>=1.26\nPillow>=10\nnbtlib>=2.0\n');take(ROOT/'requirements.txt')
(ROOT/'ASSET_NOTICE.txt').write_text('Minecraft Java 1.21.1 models and textures are not redistributed as source assets. NBT-derived rendered previews and individually attributed reference photographs are included. This is not an official Mojang product.\n');take(ROOT/'ASSET_NOTICE.txt')
manifest=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(files)]
archive=D/'Qilou02_Project.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):z.write(p,'Qilou02_Project/'+str(p.relative_to(ROOT)))
 z.writestr('Qilou02_Project/MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive)as z:assert z.testzip()is None
print(json.dumps({'project_bytes':archive.stat().st_size,'files':len(files),'source_modules':sorted(seen)},ensure_ascii=False))
