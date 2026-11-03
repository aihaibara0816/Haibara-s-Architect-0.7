"""Package B03S2, preserve original connector binaries, and verify final archive."""
from pathlib import Path
import hashlib,json,zipfile,os
P=Path(__file__).resolve().parents[1];D=P/'deliverables/B03S1';R=P/'runs/B03S2'
sha=lambda b:hashlib.sha256(b).hexdigest()
delivery=json.loads((R/'delivery_manifest.json').read_text());spec=json.loads((R/'interface_spec.json').read_text());qa=json.loads((R/'browser_qa.json').read_text());base=json.loads((P/'runs/B03S1/manifest.json').read_text())
for rel,a in delivery.items():
 b=(D/rel).read_bytes();assert len(b)==a['bytes'] and sha(b)==a['sha256'],rel
for a in base['recommended_parts']+base['whole_groups_alternative']:assert sha((D/a['file']).read_bytes())==a['sha256']
assert sha((D/'GuangzhouEast_Print_Guide.html').read_bytes())==qa['guide_sha256']
entries={rel:D/rel for rel in delivery}
source_files=['segment_link_b03.py','plan_triangle_b03.py','deliver_split_b03.py','link_geometry.py','check_split_browser.cjs','package_split_b03.py','annotate_link_interfaces.py','update_print_guide_interfaces.py','check_interface_browser.cjs','package_link_interfaces.py']
for name in source_files:entries['project/src/'+name]=P/'src'/name
for run,names in {'B03':['spec.json','GuangzhouEast_Complete.nbt','GuangzhouEast_LinkOnly.nbt','GuangzhouEast_LinkOnly_owners.json'],
 'B03S1':['manifest.json','validation.json','parts_owner.json','triangle_proposal.json','browser_qa.json','delivery_manifest.json'],
 'B03S2':['interface_spec.json','validation.json','browser_qa.json','delivery_manifest.json','GuangzhouEast_Print_Guide_B03S1.html']}.items():
 for name in names:entries[f'project/runs/{run}/{name}']=P/'runs'/run/name
for name in ['NotoSansCJKsc-Regular.otf','FONT_OFL.txt']:entries['project/research/dongguanxi/'+name]=P/'research/dongguanxi'/name
for p in (P/'deps/nbtlib').rglob('*.py'):entries['project/'+str(p.relative_to(P))]=p
for name in ['LICENSE','METADATA']:entries['project/deps/nbtlib-2.0.4.dist-info/'+name]=P/'deps/nbtlib-2.0.4.dist-info'/name
readme='''广州东联络线 B03S2 — 标准接口与分段打印

先打开 GuangzhouEast_Print_Guide.html 或“标准接法说明.txt”。
print_parts/：原七份联络线分件；whole_groups/：相同联络线的三份整组，两者任选一套。
approach_parts/：本次新增的南侧补接 144＋144＋2 格。已经打印完整 B03 正线时不要重复补接。
原十份 NBT 没有改动；新增三件共9,606个方块，直接取自完整 B03，填补旧独立包未附带的南侧正线。
所有数字以目标轨道方块整数坐标为准。切勿把轨道端点和蓝图外框最小角混用。
P0=(462,33,30)，Q0=(122,7,363)，相对原站最小角。现有末端是第0格。
此包不承诺任意144格模板、任意旋转或任意现场地形可直接替换；标准只针对当前B03与原朝向。

验证：原十份NBT哈希未变；新增三件独立回读与完整B03对应方块一致；南侧连续正线补齐；13个放置定位点、18处模块间普通轨道接缝逐点核对。
离线HTML：13份NBT下载字节一致，多个参考轨道点换算均通过，空值/小数拒绝，手机宽度无页面横向溢出。
尚未进行 Minecraft 导入、蓝图炮打印和列车实机试跑。原三角地用途图仍仅为概念。

复现：Python3.12；需 numpy、scipy、Pillow、fonttools。nbtlib2.0.4及MIT许可已附。
在project/运行：
  python3 src/segment_link_b03.py
  python3 src/plan_triangle_b03.py
  python3 src/deliver_split_b03.py
  python3 src/annotate_link_interfaces.py
  python3 src/update_print_guide_interfaces.py
结果写到project/deliverables/B03S1。runs/B03S1保留上一版记录；runs/B03S2为本版核对结果。
浏览器检查脚本为src/check_interface_browser.cjs；不同环境需调整Playwright模块路径，并传入Chromium可执行文件位置。
本包没有包含浏览器内部测试截图。
Noto Sans CJK ©2014–2021 Adobe，SIL Open Font License1.1，全文见project/research/dongguanxi/FONT_OFL.txt。
'''
dest=D/'GuangzhouEast_Segmented_Print_Pack.zip';tmp=dest.with_suffix('.zip.partial')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for name,p in sorted(entries.items()):z.writestr(name,p.read_bytes())
 z.writestr('先读_标准接法与复现.txt',readme)
with zipfile.ZipFile(tmp)as z:
 assert z.testzip()is None;assert len(z.namelist())==len(set(z.namelist()))
 for name,p in entries.items():assert z.read(name)==p.read_bytes(),name
os.replace(tmp,dest)
report={'name':dest.name,'sha256':sha(dest.read_bytes()),'bytes':dest.stat().st_size,'entries':len(entries)+1,'all_entries_byte_exact':True,'crc_ok':True,'old_10_nbt_unchanged':True,'current_run':'B03S2'}
(R/'package_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
