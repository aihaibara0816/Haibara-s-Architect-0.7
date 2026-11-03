from pathlib import Path
import base64,json,hashlib,re
R=Path(__file__).resolve().parent
source=R.parent/'upload/InteriorDetail05.html'
s=source.read_text()
assert 'id="plants"' not in s
s=s.replace('</style>',(R/'plant-style.css').read_text()+'</style>',1)
pos=s.index('<section id="styles">')
s=s[:pos]+(R/'plant-section.html').read_text()+s[pos:]
s=s.replace('<a href="#problem">问题</a>','<a href="#problem">问题</a><a href="#plants">植物 / 柔和感</a>',1)
s=s.replace('内饰规则 0.4.2','内饰规则 0.4.3',1).replace('<span class="tag">2026.10.29</span>','<span class="tag">植物增补 2026.10.30</span>',1)
s=s.replace('整理本轮 8 条新参考、回看旧教程，并用 4 个固定展间检验构件组合。','保留 10.29 的 8 条参考与 4 个家具展间；10.30 增补植物、盆器与软装组合，增加可切换种子的平面研究。',1)
s=s.replace('规则版本升级为 <b>0.4.2</b>','家具规则 0.4.2 基础上增补植物组景，当前版本为 <b>0.4.3</b>',1)
s=s.replace('<li>新增家具精细度与生活场景规则。</li>','<li>新增家具精细度与生活场景规则。</li><li>10.30 增补植物与软装同步设计、盆器/株形、按组随机与整株避让规则。</li>',1)
s=s.replace('先补看 soujju 客厅 0:12','同时试窗边落地盆栽、边几小盆、地毯与灯位，不把植被推迟到最后填空。先补看 soujju 客厅 0:12',1)
s=s.replace('下列文件可独立导出。NBT 为','下列文件可独立导出。两份 NBT 保留 10.29 家具试验原样，未写入本次新增植物方案。NBT 为',1)
research=json.loads((R.parent/'interior_detail05/research.json').read_text())
research['planting_addendum']={'date':'2026-10-30','rule_version':'0.4.3','user_feedback':'植被也是尝试的一部分；纯室内太干太硬，需花盆与随机植物带来软感','sources':['UIMG1','UIMG2','S01 old frame 01:49'],'new_video_review':False,'artifact':'seeded SVG planting plan','status':'schematic_only','nbt_changed':False,'game_checked':False,'aesthetic':'pending','next':'同一起居角同时精修家具、植物、软装，再做同机位近看与实机测试'}
def uri(v):return 'data:application/json;base64,'+base64.b64encode(json.dumps(v,ensure_ascii=False,indent=2).encode()).decode()
s=re.sub(r'(<a class="button" download="research.json" href=")[^"]+("[^>]*>)',lambda m:m[1]+uri(research)+m[2],s,count=1)
source_bundle={n:(R/n).read_text() for n in ['plant-section.html','plant-style.css','plant-study.js','update_report.py']}
s=s.replace('</div><details style="margin-top:20px"><summary>查看技术边界</summary>','<a class="button" download="InteriorDetail05-plant-study-source.json" href="'+uri(source_bundle)+'">植物平面试验源码 JSON</a></div><details style="margin-top:20px"><summary>查看技术边界</summary>',1)
s=s.replace('</body>','<script>'+(R/'plant-study.js').read_text()+'</script></body>',1)
(R/'InteriorDetail05.html').write_text(s)
(R/'research.json').write_text(json.dumps(research,ensure_ascii=False,indent=2))
print(json.dumps({'path':str(R/'InteriorDetail05.html'),'bytes':len(s.encode()),'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},ensure_ascii=False))
